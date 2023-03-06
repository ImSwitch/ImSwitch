import json
import os
import threading
import time
from datetime import datetime
from queue import Queue

import numpy as np
import tifffile as tif
from imswitch.imcommon.framework import Signal
from imswitch.imcommon.model import dirtools
from imswitch.imcommon.model import initLogger

from locai.deck.deck_config import DeckConfig
from locai.utils.utils import strfdelta
from ..basecontrollers import LiveUpdatedController
from ...model.SetupInfo import OpentronsDeckInfo
from opentrons.types import Point

_attrCategory = 'Positioner'
_positionAttr = 'Position'
_speedAttr = "Speed"
_objectiveRadius = 21.8 / 2
_objectiveRadius = 29.0 / 2  # Olympus


class DeckScanController(LiveUpdatedController):
    """ Linked to OpentronsDeckScanWidget."""
    sigImageReceived = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__logger = initLogger(self, instanceName="DeckScanController")
        self.objective_radius = _objectiveRadius
        ot_info: OpentronsDeckInfo = self._setupInfo.deck["OpentronsDeck"]
        deck_layout = json.load(open(ot_info.deck_file, "r"))
        self.deck_definition = DeckConfig(deck_layout, ot_info.labwares)
        self.translate_units = self._setupInfo.deck["OpentronsDeck"].translate_units

        # Init desk and labware
        self.initialize_positioners()
        # Has control over detector/camera
        self.initialize_detectors()
        # Has control over TLUP LED
        self.initialize_leds()
        # Current position to scan -> row from table
        self.current_scanning_row = (None, None, (None, None), None, (None, None, None))
        # Time to settle image (stage vibrations)
        self.tUnshake = 0.2
        # From MCT:
        # mct parameters
        self.nRounds = 0
        self.timePeriod = 60  # seconds
        self.zStackEnabled = False
        self.zStackMin = 0
        self.zStackMax = 0
        self.zStackStep = 0
        self.MCTFilename = ""
        self.pixelsize = (10, 1, 1)  # zxy
        # Connect MCTWidget signals
        self._widget.ScanStartButton.clicked.connect(self.startScan)
        self._widget.ScanStopButton.clicked.connect(self.stopScan)
        self._widget.ScanShowLastButton.clicked.connect(self.showLast)
        # connect XY Stagescanning live update  https://github.com/napari/napari/issues/1110
        self.sigImageReceived.connect(self.displayImage)
        # autofocus related
        self.isAutofocusRunning = False
        self._commChannel.sigAutoFocusRunning.connect(self.setAutoFocusIsRunning)
        self.isScanrunning = False
        self._widget.ScanShowLastButton.setEnabled(False)
        self._widget.scan_list.sigGoToTableClicked.connect(self.gototable)

    def gototable(self, absolute_position):
        self.move(new_position=Point(*absolute_position))

    # Scan Logic
    def setAutoFocusIsRunning(self, isRunning):
        # this is set by the AutofocusController once the AF is finished/initiated
        self.isAutofocusRunning = isRunning

    def displayImage(self):
        # a bit weird, but we cannot update outside the main thread
        name = "tilescanning"
        self._widget.setImage(self.detector.getLatestFrame(), colormap="gray", name=name, pixelsize=(1, 1),
                              translation=(0, 0))

    def displayStack(self, im):
        """ Displays the image in the view. """
        self._widget.setImage(im)

    def cleanStack(self, input):
        try:
            import NanoImagingPack as nip
            mBackground = nip.gaussf(np.mean(input, 0), 10)
            moutput = input / mBackground
            mFluctuations = np.mean(moutput, (1, 2))
            moutput /= np.expand_dims(np.expand_dims(mFluctuations, -1), -1)
            return np.uint8(moutput)
        except:
            return np.uint8(input)

    def showLast(self):
        isCleanStack = True
        try:
            if isCleanStack:
                LastStackLEDArrayLast = self.cleanStack(self.LastStackLEDArrayLast)
            else:
                LastStackLEDArrayLast = self.LastStackLEDArrayLast
            self._widget.setImage(LastStackLEDArrayLast, colormap="gray", name="Brightfield", pixelsize=self.pixelsize)
        except  Exception as e:
            self._logger.error(e)

    def get_scan_list_queue(self):
        queue = Queue(maxsize=self._widget.scan_list_items)
        for row in range(self._widget.scan_list.rowCount()):
            rowdata = []
            for column in range(self._widget.scan_list.columnCount()):
                item = self._widget.scan_list.item(row, column)
                if item is not None:
                    rowdata.append(
                        item.text())
                else:
                    rowdata.append('')
            queue.put(rowdata)
        return queue

    def startScan(self):
        # initilaze setup
        # this is not a thread!
        self._widget.ScanStartButton.setEnabled(False)
        # start the timelapse
        if not self.isScanrunning and self.LEDValue > 0:
            self.nRounds = 0
            self._widget.setNImages("Starting timelapse...")
            self.switchOffIllumination()
            # get parameters from GUI
            self.zStackMin, self.zStackMax, self.zStackStep, self.zStackEnabled = self._widget.getZStackValues()
            # self.xScanMin, self.xScanMax, self.xScanStep, self.yScanMin, self.yScanMax, self.yScanStep, self.xyScanEnabled = self._widget.getXYScanValues()
            self.timePeriod, self.nDuration = self._widget.getTimelapseValues()
            self.ScanFilename = self._widget.getFilename()
            self.ScanDate = datetime.now().strftime("%Y%m%d_%H%M%S")
            # store old values for later
            if len(self.leds) > 0:
                self.LEDValueOld = self.leds[0].getValue()
            # reserve space for the stack
            self._widget.ScanShowLastButton.setEnabled(False)
            # TODO: freeze scan_list -> edit shouldn´t be available while running.
            # start the timelapse - otherwise we have to wait for the first run after timePeriod to take place..
            self.takeTimelapse(self.timePeriod)
        else:
            self.isScanrunning = False
            if self.LEDValue == 0:
                self.__logger.debug("LED intensity needs to be set before starting scan.")
            self._widget.ScanStartButton.setEnabled(True)

    def takeTimelapse(self, tperiod):
        # this is called periodically by the timer
        if not self.isScanrunning:
            try:
                # make sure there is no exisiting thread
                del self.ScanThread
            except:
                pass
            # this should decouple the hardware-related actions from the GUI
            self.isScanrunning = True
            self.ScanThread = threading.Thread(target=self.takeTimelapseThread, args=(tperiod,), daemon=True)
            self.ScanThread.start()

    def takeTimelapseThread(self, tperiod=1):
        # this wil run i nthe background
        self.timeLast = 0
        self.timeStart = datetime.now()
        # run as long as the Scan is active
        while (self.isScanrunning):
            # stop measurement once done
            if self.nDuration <= self.nRounds:
                self.isScanrunning = False
                self._logger.debug("Done with timelapse")
                self._widget.ScanStartButton.setEnabled(True)
                break
            # initialize a run
            if time.time() - self.timeLast >= tperiod:
                # TODO: include estimation of one run (Autofocus * Z-Stack * Positions * Speed)
                # run an event
                self.timeLast = time.time()  # makes sure that the period is measured from launch to launch
                self._logger.debug("Take image")
                # reserve and free space for displayed stacks
                self.LastStackLED = []
                # get current position
                x, y, z = self.positioner.get_position()
                self.initialPosition = (x, y)
                self.initialPosiionZ = z
                # Get positions to observe:
                # Scan queue
                self.scan_queue = self.get_scan_list_queue()
                try:
                    # want to do autofocus?
                    autofocusParams = self._widget.getAutofocusValues()
                    if self._widget.isAutofocus() and np.mod(self.nRounds, int(autofocusParams['valuePeriod'])) == 0:
                        self._widget.setNImages("Autofocusing...")
                        if self.nRounds == 0:
                            self.z_focus = float(autofocusParams["valueInitial"])
                        else:
                            autofocusParams["valueInitial"] = self.z_focus
                        self.doAutofocus(autofocusParams)
                    if self.LEDValue > 0:
                        timestamp_ = str(self.nRounds) + strfdelta(datetime.now() - self.timeStart,
                                                                   "_d{days}h{hours}m{minutes}s{seconds}")
                        self.z_focus = float(autofocusParams["valueInitial"])
                        self.takeImageIllu(illuMode="Brightfield", intensity=self.LEDValue, timestamp=timestamp_)
                    self.nRounds += 1
                    self._widget.setNImages(self.nRounds)
                    self.LastStackLEDArrayLast = np.array(self.LastStackLED)
                    self._widget.ScanShowLastButton.setEnabled(True)

                except Exception as e:
                    self._logger.error(f"Thread closes with Error: {e}")
                    x, y, z = self.positioner.get_position()
                    self.positioner.move(value=- z, axis="Z", is_blocking=True)
                    raise e
                    # close the controller ina nice way
                    pass
            x, y, z = self.positioner.get_position()
            self.positioner.move(value=- z, axis="Z", is_blocking=True)
            # pause to not overwhelm the CPU
            time.sleep(0.1)

    def switchOnIllumination(self, intensity):
        self.__logger.info(f"Turning on Leds: {intensity} A")
        if self.leds:
            self.leds[0].setValue(intensity)
            self.leds[0].setEnabled(True)
        elif self.led_matrixs:
            self.led_matrixs[0].setAll(state=(1, 1, 1))
            [self.ledMatrix.setLEDSingle(indexled=int(LEDid), state=(0, 0, 0)) for LEDid in [12, 13, 14, 15]]

    def switchOffIllumination(self):
        # switch off all illu sources
        self.__logger.info(f"Turning off Leds")
        if len(self.leds) > 0:
            self.leds[0].setEnabled(False)
            self.leds[0].setValue(0)
            # self.illu.setAll((0,0,0))
        elif self.led_matrixs:
            self.led_matrixs[0].setAll(state=(0, 0, 0))

    def get_first_row(self):
        slot = self._widget.scan_list.item(0, 0).text()
        well = self._widget.scan_list.item(0, 1).text()
        first_position_offset = self._widget.scan_list.item(0, 2).text()
        abs_pos = self._widget.scan_list.item(0, 4).text()
        first_position_offset = tuple(map(float, first_position_offset.strip('()').split(',')))
        abs_pos = tuple(map(float, abs_pos.strip('()').split(',')))
        return slot, well, first_position_offset, abs_pos

    def doAutofocus(self, params):
        self._logger.info("Autofocusing at first position...")
        self._widget.setNImages("Autofocusing...")
        slot, well, first_position_offset, first_pos = self.get_first_row()
        self.positioner.move(value=first_pos, axis="XYZ", is_absolute=True, is_blocking=True)
        self._commChannel.sigAutoFocus.emit(float(params["valueRange"]), float(params["valueSteps"]),
                                            float(params["valueInitial"]))
        self.isAutofocusRunning = True
        while self.isAutofocusRunning:
            time.sleep(0.1)
            if not self.isAutofocusRunning:
                self._logger.info("Autofocusing done.")
                _, _, z_focus = self.positioner.get_position()  # Once done, update focal point
                self.z_focus = z_focus
                return
            # # For Mock AutoFocus I need to break somehow:
            # for i in range(10000):
            #     pass
            # return

    def get_current_scan_row(self):
        queue_item = self.scan_queue.get()
        if queue_item is None:
            self.__logger.debug(f"Queue is empty upon scanning")
            raise ValueError("Queue is empty upon scanning.")
        elif None not in queue_item:
            self.current_scanning_row = queue_item
            self.current_scanning_row[2] = tuple(map(float, queue_item[2].strip('()').split(',')))
            self.current_scanning_row[4] = tuple(map(float, queue_item[4].strip('()').split(',')))
            return self.current_scanning_row
        else:
            raise ValueError("Get rid of None values in the list before scanning.")

    def takeImageIllu(self, illuMode, intensity, timestamp=0):
        self._logger.debug("Take image: " + illuMode + " - " + str(intensity) + " A")
        fileExtension = 'tif'
        imageIndex = 0
        self._widget.gridLayer = None
        # iterate over all xy coordinates iteratively
        self.__logger.info(f"Starting scan")
        for pos_i, pos_row in enumerate(range(self._widget.scan_list.rowCount())):
            self.__logger.info(f"Total positions {self._widget.scan_list.rowCount()}. pos_i{pos_i} - pos_row{pos_row}")
            # Get position to scan
            # TODO: inform current status through front-end.
            slot, well, offset, z_focus, current_pos = self.get_current_scan_row()
            self.__logger.info(f"Currently scanning row: {self.current_scanning_row}")
            # TODO: Avoid this double movement call: should be an absolute movement...
            time.sleep(self.tUnshake*5)
            self.move(current_pos)
            time.sleep(self.tUnshake*5)
            x, y, z = self.positioner.get_position()
            self.positioner.move(value=self.z_focus - z, axis="Z", is_blocking=True)  # , is_absolute=False
            if self.zStackEnabled:
                self.__logger.info(f"zStackEnabled")
                # perform a z-stack from z_focus
                self.zStackDepth = self.zStackMax - self.zStackMin
                stepsCounter = 0
                time.sleep(self.tUnshake)  # unshake
                # for zn, iZ in enumerate(np.arange(self.zStackMin, self.zStackMax, self.zStackStep)):
                # Array of displacements from center point (z_focus) -/+ z_depth/2
                for zn, iZ in enumerate(
                        np.linspace(-self.zStackDepth / 2 + self.z_focus, self.zStackDepth / 2 + self.z_focus,
                                    int(self.zStackStep))):
                    self.__logger.info(f"Z-stack : {iZ}")
                    # move to each position
                    x, y, z = self.positioner.get_position()
                    self.positioner.move(value=iZ - z, axis="Z", is_blocking=True)  # , is_absolute=False
                    stepsCounter += self.zStackStep
                    self.switchOnIllumination(intensity)
                    time.sleep(self.tUnshake)  # unshake + Light

                    self.__logger.info(f"Taking image at Z:{iZ:.3f}.")
                    filename_str = f'{self.ScanFilename}_s{f"0{slot}" if int(slot) < 10 else slot}{well}_p{pos_row}_Z{zn}_i{imageIndex}'
                    filePath = self.getSaveFilePath(date=self.ScanDate, timestamp=timestamp,
                                                    filename=filename_str, extension=fileExtension)
                    lastFrame = self.detector.getLatestFrame()
                    self.switchOffIllumination()
                    self._logger.debug(filePath)
                    tif.imwrite(filePath, lastFrame, append=True)
                    imageIndex += 1
                    # store frames for displaying
                    if illuMode == "Brightfield":
                        self.LastStackLED.append(lastFrame.copy())
                # self.scanner.positioner.setEnabled(is_enabled=False)
                x, y, z = self.positioner.get_position()
                self.positioner.move(value=self.z_focus - z, axis="Z", is_blocking=True)  # , is_absolute=True
            else:
                # single file timelapse
                self.switchOnIllumination(intensity)
                time.sleep(self.tUnshake)  # unshake + Light
                self.__logger.info(f"Taking image.")
                x, y, z = self.positioner.get_position()
                filename_str = f'{self.ScanFilename}_s{f"0{slot}" if int(slot) < 10 else slot}{well}_Z{z:.3f}_i{imageIndex}'.replace(
                    ".", "mm")
                filePath = self.getSaveFilePath(date=self.ScanDate, timestamp=timestamp,
                                                filename=filename_str, extension=fileExtension)
                lastFrame = self.detector.getLatestFrame()
                self._logger.debug(filePath)
                tif.imwrite(filePath, lastFrame)
                imageIndex += 1
                # store frames for displaying
                if illuMode == "Brightfield":
                    self.LastStackLED = (lastFrame.copy())
            self.sigImageReceived.emit()  # => displays image
            time.sleep(1)  # Time to see image
            self.switchOffIllumination()

    def stopScan(self):
        self.isScanrunning = False
        self._widget.setNImages("Stopping timelapse...")
        self._widget.ScanStartButton.setEnabled(True)
        # # delete any existing timer
        # try:
        #     del self.timer
        # except:
        #     pass
        # delete any existing thread
        try:
            del self.ScanThread
        except:
            pass
        self._widget.setNImages("Done wit timelapse...")
        x, y, z = self.positioner.get_position()
        self.positioner.move(value=- z, axis="Z", is_blocking=True)
        # store old values for later
        if len(self.leds) > 0:
            self.leds[0].setValue(self.LEDValueOld)

    def getSaveFilePath(self, date, timestamp, filename, extension):
        mFilename = f"{filename}.{extension}"
        dirPath = os.path.join(dirtools.UserFileDirs.Root, 'recordings', date, "t" + str(timestamp))
        newPath = os.path.join(dirPath, mFilename)
        if not os.path.exists(dirPath):
            os.makedirs(dirPath)
        return newPath

    # Detectors Logic
    def initialize_detectors(self):
        # select detectors
        self.detector_names = self._master.detectorsManager.getAllDeviceNames()
        self.detector = self._master.detectorsManager[self.detector_names[0]]
        self.detector.startAcquisition()

    # LED Logic
    def initialize_leds(self):
        self.led_names = self._master.LEDsManager.getAllDeviceNames()
        self.ledMatrix_names = self._master.LEDMatrixsManager.getAllDeviceNames()

        self.leds = []
        self.led_matrixs = []
        for led_name in self.led_names:
            self.leds.append(self._master.LEDsManager[led_name])
        for led_matrix_name in self.ledMatrix_names:
            self.led_matrixs.append(self._master.LEDMatrixsManager[led_matrix_name])
        self.LEDValueOld = 0
        self.LEDValue = 0
        self._widget.sigSliderLEDValueChanged.connect(self.valueLEDChanged)
        if len(self.leds) >= 1:
            self._widget.sliderLED.setMaximum(self.leds[0].valueRangeMax)
        elif len(self.led_matrixs) >= 1:
            #        self._widget.sliderLED.setMaximum(self.led_matrixs[0].valueRangeMax)
            self._widget.sliderLED.setMaximum(100)  # TODO: Implement in LEDMatrix
        if len(self.leds) >= 1:
            self._widget.autofocusLED1Checkbox.setText(self.led_names[0])
            self._widget.autofocusLED1Checkbox.setCheckState(True)
        elif len(self.led_matrixs) >= 1:
            self._widget.autofocusLED1Checkbox.setText(self.ledMatrix_names[0])
            self._widget.autofocusLED1Checkbox.setCheckState(True)

    def valueLEDChanged(self, value):
        self.LEDValue = value
        self._widget.LabelLED.setText('Intensity (LED):' + str(value))
        try:
            if len(self.leds) and not self.leds[0].enabled:
                self.leds[0].setEnabled(1)
        except Exception as e:
            raise e
        if len(self.leds):
            try:
                self.leds[0].setValue(self.LEDValue)
            except Exception as e:
                self.leds[0].setIntensity(self.LEDValue)

    # Positioner Logic
    def initialize_positioners(self):
        # Has control over positioner
        self.positioner_name = self._master.positionersManager.getAllDeviceNames()[0]
        self.positioner = self._master.positionersManager[self.positioner_name]
        # Set up positioners
        for pName, pManager in self._master.positionersManager:
            if not pManager.forPositioning:
                continue
            hasSpeed = hasattr(pManager, 'speed')
            # self._widget.addPositioner(pName, pManager.axes, hasSpeed, pManager.position, pManager.speed)
            for axis in pManager.axes:
                self.setSharedAttr(pName, axis, _positionAttr, pManager.position[axis])
                if hasSpeed:
                    self.setSharedAttr(pName, axis, _speedAttr, pManager.speed[axis])
        # Connect CommunicationChannel signals
        self._commChannel.sharedAttrs.sigAttributeSet.connect(self.attrChanged)

        self.positioner.doHome("X")
        time.sleep(0.1)
        self.positioner.doHome("Y")

    def setPositioner(self, positionerName: str, axis: str, position: float) -> None:
        """ Moves the specified positioner axis to the specified position. """
        self.setPos(positionerName, axis, position)

    def setPos(self, positionerName, axis, position):
        """ Moves the positioner to the specified position in the specified axis. """
        self._master.positionersManager[positionerName].setPosition(position, axis)
        self.updatePosition(positionerName, axis)

    def updatePosition(self, positionerName, axis):
        newPos = self._master.positionersManager[positionerName].position[axis]
        self.setSharedAttr(positionerName, axis, _positionAttr, newPos)

    def attrChanged(self, key, value):
        if self.settingAttr or len(key) != 4 or key[0] != _attrCategory:
            return
        positionerName = key[1]
        axis = key[2]
        if key[3] == _positionAttr:
            self.setPositioner(positionerName, axis, value)

    def setSharedAttr(self, positionerName, axis, attr, value):
        self.settingAttr = True
        try:
            self._commChannel.sharedAttrs[(_attrCategory, positionerName, axis, attr)] = value
        finally:
            self.settingAttr = False

    def move(self, new_position):
        """ Moves positioner to absolute position. """
        self.positioner.move(new_position, "XYZ", is_absolute=True, is_blocking=True)
        [self.updatePosition(self.positioner_name, axis) for axis in self.positioner.axes]


class mTimer(object):
    def __init__(self, waittime, mFunc) -> None:
        self.waittime = waittime
        self.starttime = time.time()
        self.running = False
        self.isStop = False
        self.mFunc = mFunc

    def start(self):
        self.starttime = time.time()
        self.running = True

        ticker = threading.Event(daemon=True)
        self.waittimeLoop = 0  # make sure first run runs immediately
        while not ticker.wait(self.waittimeLoop) and self.isStop == False:
            self.waittimeLoop = self.waittime
            self.mFunc()
        self.running = False

    def stop(self):
        self.running = False
        self.isStop = True
