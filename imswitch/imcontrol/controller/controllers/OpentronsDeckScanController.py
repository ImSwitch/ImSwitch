import os
import time

try:
    from opentrons.types import Point
    from opentrons.protocol_api.labware import Labware, Well
    from opentrons.simulate import get_protocol_api
    from opentrons.util.entrypoint_util import labware_from_paths
    from opentrons_shared_data.deck import load
    from locai.utils.utils import strfdelta
    IS_LOCAI = True
except:
    IS_LOCAI = False

from typing import Dict, List
from functools import partial
from qtpy import QtCore, QtWidgets
import json
import threading
from datetime import datetime
import numpy as np
import tifffile as tif
from queue import Queue


from imswitch.imcommon.model import APIExport
from ..basecontrollers import ImConWidgetController, LiveUpdatedController
from imswitch.imcontrol.view import guitools as guitools
from imswitch.imcommon.model import initLogger, APIExport, ostools, dirtools
from imswitch.imcontrol.controller.controllers.PositionerController import PositionerController
from imswitch.imcommon.framework import Signal, Thread, Worker, Mutex, Timer

_attrCategory = 'Positioner'
_positionAttr = 'Position'
_speedAttr = "Speed"
_objectiveRadius = 21.8 / 2
_objectiveRadius = 29.0 / 2 # Olympus

class OpentronsDeckScanController(LiveUpdatedController):
    """ Linked to OpentronsDeckScanWidget."""
    sigImageReceived = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__logger = initLogger(self, instanceName="OpentronsScanController")

        if not IS_LOCAI:
            self.__logger.warning("Locai not installed, cannot use OpentronsScanController")
            return
        # Init desk and labware
        self.load_deck(self._setupInfo.deck["OpentronsDeck"])
        self.load_labwares(self._setupInfo.deck["OpentronsDeck"].labwares)
        # Has control over positioner and scanner
        self.initialize_positioners()
        self.scanner = LabwareScanner(self.positioner, self.deck, self.labwares, _objectiveRadius)
        # Has control over detector/camera
        self.initialize_detectors()
        # Has control over TLUP LED
        self.initialize_leds()
        # Current position to scan -> row from table
        self.current_scanning_position = (None, None, (None, None))
        # Time to settle image (stage vibrations)
        self.tUnshake = 1
        #From MCT:
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

    # Scan Logic
    def setAutoFocusIsRunning(self, isRunning):
        # this is set by the AutofocusController once the AF is finished/initiated
        self.isAutofocusRunning = isRunning
    def displayImage(self):
        # a bit weird, but we cannot update outside the main thread
        name = "tilescanning"
        self._widget.setImage(self.detector.getLatestFrame(), colormap="gray", name=name, pixelsize=(1, 1), translation=(0, 0))
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
                x,y,z = self.positioner.get_position()
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
                        timestamp_ = str(self.nRounds) + strfdelta(datetime.now()- self.timeStart, "_d{days}h{hours}m{minutes}s{seconds}")
                        self.z_focus = float(autofocusParams["valueInitial"])
                        self.takeImageIllu(illuMode="Brightfield", intensity=self.LEDValue, timestamp=timestamp_)
                    self.nRounds += 1
                    self._widget.setNImages(self.nRounds)
                    self.LastStackLEDArrayLast = np.array(self.LastStackLED)
                    self._widget.ScanShowLastButton.setEnabled(True)

                except Exception as e:
                    self._logger.error(f"Thread closes with Error: {e}")
                    x, y, z = self.positioner.get_position()
                    self.positioner.move(dist=- z, axis="Z", is_blocking=True)
                    raise e
                    # close the controller ina nice way
                    pass
            x, y, z = self.positioner.get_position()
            self.positioner.move(dist=- z, axis="Z", is_blocking=True)
            # pause to not overwhelm the CPU
            time.sleep(0.1)
    def switchOnIllumination(self, intensity):
        self.__logger.info(f"Turning on Leds: {intensity} A")
        self.leds[0].setValue(intensity)
        self.leds[0].setEnabled(True)
    def switchOffIllumination(self):
        # switch off all illu sources
        self.__logger.info(f"Turning off Leds")
        if len(self.leds) > 0:
            self.leds[0].setEnabled(False)
            self.leds[0].setValue(0)
            # self.illu.setAll((0,0,0))
    def get_first_position(self):
        slot = self._widget.scan_list.item(0, 0).text()
        well = self._widget.scan_list.item(0, 1).text()
        first_position_offset = self._widget.scan_list.item(0, 2).text()
        first_position_offset = tuple(map(float, first_position_offset.strip('()').split(',')))
        return slot, well, first_position_offset
    def doAutofocus(self, params):
        self._logger.info("Autofocusing at first position...")
        self._widget.setNImages("Autofocusing...")
        slot, well, offset = self.get_first_position()
        self.scanner.moveToWell(well=well, slot=slot, is_blocking=True)
        self.scanner.shiftXY(xy_shift=offset, is_blocking=True)
        self._commChannel.sigAutoFocus.emit(float(params["valueRange"]), float(params["valueSteps"]), float(params["valueInitial"]))
        self.isAutofocusRunning = True
        while self.isAutofocusRunning:
            time.sleep(0.1)
            if not self.isAutofocusRunning:
                self._logger.info("Autofocusing done.")
                _, _, z_focus = self.positioner.get_position() # Once done, update focal point
                self.z_focus = z_focus
                return
            # # For Mock AutoFocus I need to break somehow:
            # for i in range(10000):
            #     pass
            # return
    def get_current_scan_position(self):
        queue_item = self.scan_queue.get()
        if queue_item is None:
            self.__logger.debug(f"Queue is empty upon scanning")
            raise ValueError("Queue is empty upon scanning.")
        elif None not in queue_item:
            self.current_scanning_position = queue_item
            self.current_scanning_position[2] = tuple(map(float, queue_item[2].strip('()').split(',')))
            return self.current_scanning_position
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
            self.__logger.info(f"Currently scanning position: {self.current_scanning_position}")
            slot,well,offset = self.get_current_scan_position()
            # TODO: Avoid this double movement call: should be an absolute movement...
            self.scanner.moveToWell(well=well, slot=slot, is_blocking=True)
            self.scanner.shiftXY(xy_shift=offset, is_blocking=True)
            x, y, z = self.positioner.get_position()
            self.positioner.move(dist=self.z_focus-z, axis="Z", is_blocking=True) #, is_absolute=False
            if self.zStackEnabled:
                self.__logger.info(f"zStackEnabled")
                # perform a z-stack from z_focus
                self.zStackDepth = self.zStackMax - self.zStackMin
                stepsCounter = 0
                time.sleep(self.tUnshake)  # unshake
                # for zn, iZ in enumerate(np.arange(self.zStackMin, self.zStackMax, self.zStackStep)):
                # Array of displacements from center point (z_focus) -/+ z_depth/2
                for zn, iZ in enumerate(np.linspace(-self.zStackDepth/2 + self.z_focus, self.zStackDepth/2 + self.z_focus, int(self.zStackStep))):
                    self.__logger.info(f"Z-stack : {iZ}")
                    # move to each position
                    x, y, z = self.positioner.get_position()
                    self.positioner.move(dist=iZ - z, axis="Z", is_blocking=True)  # , is_absolute=False
                    stepsCounter += self.zStackStep
                    self.switchOnIllumination(intensity)
                    time.sleep(self.tUnshake*5)  # unshake + Light

                    self.__logger.info(f"Taking image at Z:{iZ:.3f}.")
                    filename_str = f'{self.ScanFilename}_s{f"0{slot}" if int(slot) < 10 else slot}{well}_p{pos_row}_Z{zn}_i{imageIndex}'
                    filePath = self.getSaveFilePath(date=self.ScanDate,timestamp=timestamp,
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
                self.positioner.move(dist=self.z_focus-z, axis="Z", is_blocking=True) # , is_absolute=True
            else:
                # single file timelapse
                self.switchOnIllumination(intensity)
                time.sleep(self.tUnshake*2)  # unshake + Light
                self.__logger.info(f"Taking image.")
                x, y, z = self.positioner.get_position()
                filename_str = f'{self.ScanFilename}_s{f"0{slot}" if int(slot) < 10 else slot}{well}_Z{z:.3f}_i{imageIndex}'.replace(
                    ".", "mm")
                filePath = self.getSaveFilePath(date=self.ScanDate,timestamp=timestamp,
                                                filename=filename_str,extension=fileExtension)
                lastFrame = self.detector.getLatestFrame()
                self._logger.debug(filePath)
                tif.imwrite(filePath, lastFrame)
                imageIndex += 1
                # store frames for displaying
                if illuMode == "Brightfield":
                    self.LastStackLED = (lastFrame.copy())
            self.sigImageReceived.emit()  # => displays image
            time.sleep(1) # Time to see image
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
        self.positioner.move(dist=- z, axis="Z", is_blocking=True)
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
    # Deck and Labware Logic
    def load_labwares(self, labwares):
        labwares_dict = {}
        if "custom" in labwares.keys():
            if labwares["custom"] is None:
                protocol = get_protocol_api("2.12")
            else:
                # Load custom/extra labware
                # c_labw = [os.sep.join([labwares["custom_labwares_path"],labw+".json"]) for labw in labwares["custom"].values()]
                self._custom_labware = labware_from_paths([labwares["custom_labwares_path"]])
                protocol = get_protocol_api("2.12", extra_labware=self._custom_labware)
                for slot, labware_file in labwares["custom"].items():
                    labwares_dict[slot] = protocol.load_labware(labware_file, slot)
        else:
            protocol = get_protocol_api("2.12")
        # Load standard labware
        for slot, labware_file in labwares["standard"].items():
            labwares_dict[slot] = protocol.load_labware(labware_file, slot)
        self.labwares = labwares_dict
        return

    def load_deck(self, deck):
        if hasattr(deck, "deck_file"):
            deck_def_dict = json.load(open(deck.deck_file))
        elif hasattr(deck, "deck_name"):  # Default for OT2: "ot2_standard"
            deck_def_dict = load(name=deck.deck_name, version=3)
        else:
            path = os.sep.join([deck.deck_path, deck.deck_name + ".json"])
            deck_def_dict = json.load(open(path))
        self.deck = deck_def_dict
        self.ordered_slots = {slot["id"]: slot for i, slot in enumerate(self.deck["locations"]["orderedSlots"])}
        self.corner_offset = [abs(i) for i in self.deck["cornerOffsetFromOrigin"]]
        return

    # Detectors Logic
    def initialize_detectors(self):
        # select detectors
        self.detector_names = self._master.detectorsManager.getAllDeviceNames()
        self.detector = self._master.detectorsManager[self.detector_names[0]]
        self.detector.startAcquisition()
    # LED Logic
    def initialize_leds(self):
        self.led_names = self._master.LEDsManager.getAllDeviceNames()
        self.leds = []
        for led_name in self.led_names:
            self.leds.append(self._master.LEDsManager[led_name])
        self.LEDValueOld = 0
        self.LEDValue = 0
        self._widget.sigSliderLEDValueChanged.connect(self.valueLEDChanged)
        if len(self.leds) >= 1:
            self._widget.sliderLED.setMaximum(self.leds[0].valueRangeMax)
        if len(self.leds) >= 1:
            self._widget.autofocusLED1Checkbox.setText(self.led_names[0])
            self._widget.autofocusLED1Checkbox.setCheckState(True)
    def valueLEDChanged(self, value):
        self.LEDValue = value
        self._widget.LabelLED.setText('Intensity (LED):' + str(value))
        if len(self.leds) and not self.leds[0].enabled: self.leds[0].setEnabled(1)
        if len(self.leds): self.leds[0].setValue(self.LEDValue)

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
    # Positioners Logic:
    def moveToWell(self, well, slot=None):
        if isinstance(well, Well):
            slot = well.parent.parent
            well = well.well_name
        self.__logger.debug(f"Move to {well}")
        self.scanner.moveToWell(well=well, slot=slot if slot is not None else self.current_scanning_position[0])
        [self.updatePosition(self.positioner_name, axis) for axis in self.positioner.axes]
    def move(self, positionerName, axis, dist):
        """ Moves positioner by dist micrometers in the specified axis. """
        if positionerName is None:
            positionerName = self._master.positionersManager.getAllDeviceNames()[0]
        self._master.positionersManager[positionerName].move(dist, axis)
        self.updatePosition(positionerName, axis)

class LabwareScanner():
    def __init__(self, positioner, deck, labwares, objective_radius):
        self.__logger = initLogger(self, instanceName="DeckSlotScanner")

        self.positioner = positioner
        self.deck = deck
        self.slots_list = self.deck["locations"]["orderedSlots"]
        self.corner_offset = [abs(i) for i in self.deck["cornerOffsetFromOrigin"]]
        self.labwares = labwares
        self.objective_radius = objective_radius
        self.default_positions_in_well = {"center": (0, 0), "left": (-0.01, 0),
                                          "right": (0.01, 0), "up": (0, 0.01), "down": (0, -0.01)}

    def get_slot(self, loc=None):
        """
        :param loc: Absolute position
        :return: Slot number
        """
        if loc is None:
            xo, yo, _ = self.positioner.get_position()
        elif isinstance(loc, Point):
            xo, yo, _ = loc
        else:
            raise TypeError

        for slot in self.slots_list:
            slot_origin = [a + b for a, b in zip(slot["position"], self.corner_offset)]
            slot_size = [v for v in slot["boundingBox"].values()]
            x1, y1, _ = slot_origin
            x2, y2, _ = [a + b for a, b in zip(slot_origin, slot_size)]
            if x1 < xo < x2 and y1 < yo < y2:
                # self.__logger.debug(f"Currently in slot {slot['id']}.")
                return slot['id']
        return None

    def shiftXY(self, xy_shift, x_shift=None, y_shift=None, is_blocking = False):
        if xy_shift is not None and x_shift is None and y_shift is None:
            if isinstance(xy_shift, str):
                raise TypeError("Received string. Expected tuple of floats.")
            x_shift = xy_shift[0]
            y_shift = xy_shift[1]
        else:
            raise ValueError
        x, y, z = self.positioner.get_position()
        new_pos = (x + x_shift, y + y_shift)
        if self.objective_collision_avoidance(axis="XY",new_pos=(x_shift + x, y_shift + y)):
            self.__logger.debug(f"Shifting on {x_shift, y_shift}. Abs. Pos.: {new_pos[0],new_pos[1]}")
            self.moveToXY(new_pos[0], new_pos[1], is_blocking = is_blocking)
        else:
            self.__logger.info(f"Avoiding objective collision.")

    def moveToWell(self, well, slot, is_blocking = False):
        if not isinstance(well, Well):
            well = self.labwares[slot].wells_by_name()[well]
        x, y, _ = well.geometry.position
        x_offset, y_offset, _ = self.corner_offset
        new_pos = (x + abs(x_offset), y + abs(y_offset))
        if self.objective_collision_avoidance(axis="XY",new_pos=new_pos, slot=slot):
            self.__logger.debug(f"Moving to well: {well} in slot: {slot}. Abs. Pos.: {new_pos[0],new_pos[1]}")
            self.moveToXY(new_pos[0],new_pos[1], is_blocking = is_blocking)
        else:
            self.__logger.info(f"Avoiding objective collision.")

    def check_position_in_well(self, well, pos):
        if (abs(pos[0]) < well.diameter / 2) and (abs(pos[1]) < well.diameter / 2):
            return
        else:
            raise ValueError("Position outside well.")

    def objective_collision_avoidance(self, axis, new_pos=None, slot=None, shift=None):
        xo, yo, z = self.positioner.get_position()
        if axis == "Z":
            if slot is not None:
                if slot == self.get_slot():  # Moving objective within a slot
                    return True
                else:  # Apply collision avoidance
                    return False
            else:
                if self.get_slot() is not None:
                    return True
                else:
                    return False
        else:
            # Define XY shift
            if axis == "X":
                new_x = new_pos if shift is None else xo + shift
                new_y = yo
            elif axis == "Y":
                new_x = xo
                new_y = new_pos if shift is None else yo + shift
            elif axis == "XY":
                new_x = new_pos[0] if shift is None else xo + shift[0]
                new_y = new_pos[1] if shift is None else yo + shift[1]
            else:
                raise ValueError
            # Called with positioner arrows within one slot -> avoid collision and check borders
            if slot is None and self.get_slot() is not None:
                slot_dict = self.slots_list[int(self.get_slot()) - 1]

                slot_origin = [a + b for a, b in zip(slot_dict["position"], self.corner_offset)]
                slot_size = [v for v in slot_dict["boundingBox"].values()]

                x1, y1, _ = slot_origin
                x2, y2, _ = [a + b for a, b in zip(slot_origin, slot_size)]

                if not x1 + self.objective_radius < new_x < x2 - self.objective_radius \
                        or not y1 + self.objective_radius < new_y < y2 - self.objective_radius:
                    return False
                else:
                    return True
            # Called with moveToWell, knows slot -> keep z and check borders
            elif slot is not None and slot == self.get_slot():
                slot_dict = self.slots_list[int(self.get_slot()) - 1]

                slot_origin = [a + b for a, b in zip(slot_dict["position"], self.corner_offset)]
                slot_size = [v for v in slot_dict["boundingBox"].values()]

                x1, y1, _ = slot_origin
                x2, y2, _ = [a + b for a, b in zip(slot_origin, slot_size)]

                if not x1 + self.objective_radius < new_x < x2 - self.objective_radius \
                        or not y1 + self.objective_radius < new_y < y2 - self.objective_radius:
                    return False
                else:
                    return True
            # Called with moveToWell, knows slot -> avoid collision and check borders
            elif slot is not None and slot != self.get_slot():
                slot_dict = self.slots_list[int(slot) - 1]

                slot_origin = [a + b for a, b in zip(slot_dict["position"], self.corner_offset)]
                slot_size = [v for v in slot_dict["boundingBox"].values()]

                x1, y1, _ = slot_origin
                x2, y2, _ = [a + b for a, b in zip(slot_origin, slot_size)]

                if not x1 + self.objective_radius < new_x < x2 - self.objective_radius \
                        or not y1 + self.objective_radius < new_y < y2 - self.objective_radius:
                    return False
                else:
                    if z > 1:
                        self.__logger.debug("Avoiding objective collision.")
                        self.positioner.move(axis="XYZ", dist=(0, 0, -z), is_blocking=True)
                    return True
            else:
                raise ValueError

    def moveToXY(self, pos_X, pos_Y, is_blocking = False):
        x, y, z = self.positioner.get_position()
        self.positioner.move(axis="XY", dist=(pos_X - x, pos_Y - y), is_blocking = is_blocking)

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