import os
import time
from typing import Optional, Union, List
import numpy as np
import datetime
from fastapi.responses import StreamingResponse
from fastapi import FastAPI, Response, HTTPException
import cv2
from PIL import Image
import io
import imswitch 
from imswitch.imcommon.framework import Timer
from imswitch.imcommon.model import ostools, APIExport, initLogger, dirtools
from imswitch.imcontrol.model import RecMode, SaveMode, SaveFormat
from ..basecontrollers import ImConWidgetController


class RecordingController(ImConWidgetController):
    """ Linked to RecordingWidget. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__logger = initLogger(self)
        
        
        # Define a dictionary to store variables accessible to the function
        self.shared_variables: dict[str, any] = {}

        self.settingAttr = False
        self.recording = False
        self.doneScan = False
        self.endedRecording = False
        self.lapseCurrent = -1
        self.lapseTotal = 0
        
        self.streamstarted = False

        # Connect CommunicationChannel signals
        self._commChannel.sigRecordingStarted.connect(self.recordingStarted)
        self._commChannel.sigRecordingEnded.connect(self.recordingEnded)
        self._commChannel.sigScanDone.connect(self.scanDone)
        self._commChannel.sigUpdateRecFrameNum.connect(self.updateRecFrameNum)
        self._commChannel.sigUpdateRecTime.connect(self.updateRecTime)
        self._commChannel.sharedAttrs.sigAttributeSet.connect(self.attrChanged, check_nargs=False)
        self._commChannel.sigSnapImg.connect(self.snap)
        self._commChannel.sigSnapImgPrev.connect(self.snapImagePrev)
        self._commChannel.sigStartRecordingExternal.connect(self.startRecording)
        self._commChannel.sigRequestScanFreq.connect(self.sendScanFreq)
        

        if imswitch.IS_HEADLESS: return
        
        self.untilStop()
        
        # ADD GUI elements just in case
        self._widget.setDetectorList(
            self._master.detectorsManager.execOnAll(lambda c: c.model,
                                                    condition=lambda c: c.forAcquisition)
        )
        self._widget.setsaveFormat(SaveFormat.HDF5.value)
        self._widget.setSnapSaveMode(SaveMode.Disk.value)
        self._widget.setSnapSaveModeVisible(self._setupInfo.hasWidget('Image'))

        self._widget.setRecSaveMode(SaveMode.Disk.value)
        self._widget.setRecSaveModeVisible(
            self._moduleCommChannel.isModuleRegistered('imreconstruct')
        )


        # Connect RecordingWidget signals
        self._widget.sigDetectorModeChanged.connect(self.detectorChanged)
        self._widget.sigDetectorSpecificChanged.connect(self.detectorChanged)
        self._widget.sigOpenRecFolderClicked.connect(self.openFolder)
        self._widget.sigSpecFileToggled.connect(self._widget.setCustomFilenameEnabled)

        self._widget.sigSnapSaveModeChanged.connect(self.snapSaveModeChanged)

        self._widget.sigSpecFramesPicked.connect(self.specFrames)
        self._widget.sigSpecTimePicked.connect(self.specTime)
        self._widget.sigScanOncePicked.connect(self.recScanOnce)
        self._widget.sigScanLapsePicked.connect(self.recScanLapse)
        self._widget.sigUntilStopPicked.connect(self.untilStop)

        self._widget.sigSnapRequested.connect(self.snap)
        self._widget.sigRecToggled.connect(self.toggleREC)

    def openFolder(self):
        """ Opens current folder in File Explorer. """
        folder = self._widget.getRecFolder()
        if not os.path.exists(folder):
            os.makedirs(folder)
        ostools.openFolderInOS(folder)

    def snapSaveModeChanged(self):
        saveMode = SaveMode(self._widget.getSnapSaveMode())
        self._widget.setsaveFormatEnabled(saveMode != SaveMode.RAM)
        if saveMode == SaveMode.RAM:
            self._widget.setsaveFormat(SaveFormat.TIFF.value)

    def snap(self, name=None, mSaveFormat=None):
        """ Take a snap and save it to a file. """
        self.updateRecAttrs(isSnapping=True)

        # by default save as it's noted in the widget
        if mSaveFormat is None:
            if imswitch.IS_HEADLESS:
                mSaveFormat = SaveFormat(self._widget.getSnapSaveMode())
            else:
                mSaveFormat = 1 # TIFF

        if imswitch.IS_HEADLESS:
            folder = self._widget.getRecFolder()
        else:
            timeStamp = datetime.datetime.now().strftime("%Y_%m_%d-%I-%M-%S_%p")
            folder = os.path.join(dirtools.UserFileDirs.Root, 'recordings', timeStamp)
        if not os.path.exists(folder):
            os.makedirs(folder)
        time.sleep(0.01)

        detectorNames = self.getDetectorNamesToCapture()
        if name is None:
            name = '_snap'
        savename = os.path.join(folder, self.getFileName()) + name

        attrs = {detectorName: self._commChannel.sharedAttrs.getHDF5Attributes()
                 for detectorName in detectorNames}

        self._master.recordingManager.snap(detectorNames,
                                           savename,
                                           SaveMode(self._widget.getSnapSaveMode()),
                                           mSaveFormat,
                                           attrs)

    def snapNumpy(self):
        self.updateRecAttrs(isSnapping=True)
        detectorNames = self.getDetectorNamesToCapture()
        attrs = {detectorName: self._commChannel.sharedAttrs.getHDF5Attributes()
                 for detectorName in detectorNames}

        return self._master.recordingManager.snap(detectorNames,
                                           "",
                                           SaveMode(4), # for Numpy
                                           "",
                                           attrs)



    def snapImagePrev(self, *args):
        """ Snap an already taken image and save it to a file. """
        self.updateRecAttrs(isSnapping=True)

        args = list(args)
        detectorName = (args[0])
        image = args[1]
        suffix = args[2]

        folder = self._widget.getRecFolder()
        if not os.path.exists(folder):
            os.makedirs(folder)
        time.sleep(0.01)

        savename = os.path.join(folder, self.getFileName()) + '_snap_' + suffix
        attrs = {detectorName: self._commChannel.sharedAttrs.getHDF5Attributes()}

        self._master.recordingManager.snapImagePrev(detectorName,
                                                    savename,
                                                    SaveFormat(self._widget.getSnapSaveFormat()),
                                                    image,
                                                    attrs)

    def toggleREC(self, checked):
        """ Start or end recording. """
        if checked and not self.recording:
            self.updateRecAttrs(isSnapping=False)

            folder = self._widget.getRecFolder()
            if not os.path.exists(folder):
                os.makedirs(folder)
            time.sleep(0.01)
            self.savename = os.path.join(folder, self.getFileName()) + '_rec'

            if self.recMode == RecMode.ScanOnce:
                self._commChannel.sigScanStarting.emit()  # To get correct values from sharedAttrs

            detectorsBeingCaptured = self.getDetectorNamesToCapture()

            self.recordingArgs = {
                'detectorNames': detectorsBeingCaptured,
                'recMode': self.recMode,
                'savename': self.savename,
                'saveMode': SaveMode(self._widget.getRecSaveMode()),
                'saveFormat': SaveFormat(self._widget.getsaveFormat()),
                'attrs': {detectorName: self._commChannel.sharedAttrs.getHDF5Attributes()
                          for detectorName in detectorsBeingCaptured},
                'singleMultiDetectorFile': (len(detectorsBeingCaptured) > 1 and
                                            self._widget.getMultiDetectorSingleFile())
            }

            if self.recMode == RecMode.SpecFrames:
                self.recordingArgs['recFrames'] = self._widget.getNumExpositions()
                self._master.recordingManager.startRecording(**self.recordingArgs)
            elif self.recMode == RecMode.SpecTime:
                self.recordingArgs['recTime'] = self._widget.getTimeToRec()
                self._master.recordingManager.startRecording(**self.recordingArgs)
            elif self.recMode == RecMode.ScanOnce:
                self.recordingArgs['recFrames'] = self._commChannel.getNumScanPositions()
                self._master.recordingManager.startRecording(**self.recordingArgs)
                time.sleep(0.3)
                self._commChannel.sigRunScan.emit(True, False)
            elif self.recMode == RecMode.ScanLapse:
                self.recordingArgs['singleLapseFile'] = self._widget.getTimelapseSingleFile()
                self.lapseTotal = self._widget.getTimelapseTime()
                self.lapseCurrent = 0
                self.nextLapse()
            else:
                self._master.recordingManager.startRecording(**self.recordingArgs)

            self.recording = True
            self.endedRecording = False
        else:
            if self.recMode == RecMode.ScanLapse and self.lapseCurrent != -1:
                self._commChannel.sigAbortScan.emit()
            self._master.recordingManager.endRecording()

    def nextLapse(self):
        self.endedRecording = False
        self.doneScan = False

        isFirstLapse = self.lapseCurrent == 0
        isFinalLapse = self.lapseCurrent + 1 == self.lapseTotal

        if not self.recordingArgs['singleLapseFile']:
            lapseCurrentStr = str(self.lapseCurrent).zfill(len(str(self.lapseTotal)))
            self.recordingArgs['savename'] = f'{self.savename}_scan{lapseCurrentStr}'

        if isFirstLapse:
            self._commChannel.sigScanStarting.emit()  # To get updated values from sharedAttrs
            self.recordingArgs['attrs'] = {  # Update
                detectorName: self._commChannel.sharedAttrs.getHDF5Attributes()
                for detectorName in self.recordingArgs['detectorNames']
            }
            self.recordingArgs['recFrames'] = self._commChannel.getNumScanPositions()  # Update

        self._master.recordingManager.startRecording(**self.recordingArgs)
        time.sleep(0.3)

        self._commChannel.sigRunScan.emit(isFirstLapse, not isFinalLapse)

    def recordingStarted(self):
        self._widget.setFieldsEnabled(False)

    def recordingCycleEnded(self):
        if (self._widget.isRecButtonChecked() and self.recMode == RecMode.ScanLapse and
                0 < self.lapseCurrent + 1 < self.lapseTotal):
            self.lapseCurrent += 1
            self._widget.updateRecLapseNum(self.lapseCurrent)
            self.timer = Timer(singleShot=True)
            self.timer.timeout.connect(self.nextLapse)
            self.timer.start(int(self._widget.getTimelapseFreq() * 1000))
        else:
            self.recording = False
            self.lapseCurrent = -1
            self._widget.updateRecFrameNum(0)
            self._widget.updateRecTime(0)
            self._widget.updateRecLapseNum(0)
            self._widget.setRecButtonChecked(False)
            self._widget.setFieldsEnabled(True)

    def scanDone(self):
        self.doneScan = True
        if not self.endedRecording and (self.recMode == RecMode.ScanLapse or
                                    self.recMode == RecMode.ScanOnce):
            self.recordingCycleEnded()

    def recordingEnded(self):
        self.endedRecording = True
        if not self.doneScan or not (self.recMode == RecMode.ScanLapse or
                                 self.recMode == RecMode.ScanOnce):
            self.recordingCycleEnded()

    def updateRecFrameNum(self, recFrameNum):
        if self.recMode == RecMode.SpecFrames:
            self._widget.updateRecFrameNum(recFrameNum)

    def updateRecTime(self, recTime):
        if self.recMode == RecMode.SpecTime:
            self._widget.updateRecTime(recTime)

    def specFrames(self):
        self._widget.checkSpecFrames()
        self._widget.setEnabledParams(specFrames=True)
        self.recMode = RecMode.SpecFrames

    def specTime(self):
        self._widget.checkSpecTime()
        self._widget.setEnabledParams(specTime=True)
        self.recMode = RecMode.SpecTime

    def recScanOnce(self):
        self._widget.checkScanOnce()
        self._widget.setEnabledParams()
        self.recMode = RecMode.ScanOnce

    def recScanLapse(self):
        self._widget.checkScanLapse()
        self._widget.setEnabledParams(scanLapse=True)
        self.recMode = RecMode.ScanLapse

    def untilStop(self):
        self._widget.checkUntilStop()
        self._widget.setEnabledParams()
        self.recMode = RecMode.UntilStop

    def setRecMode(self, recMode):
        if recMode == RecMode.SpecFrames:
            self.specFrames()
        elif recMode == RecMode.SpecTime:
            self.specTime()
        elif recMode == RecMode.ScanOnce:
            self.recScanOnce()
        elif recMode == RecMode.ScanLapse:
            self.recScanLapse()
        elif recMode == RecMode.UntilStop:
            self.untilStop()
        else:
            raise ValueError(f'Invalid RecMode {recMode} specified')

    def detectorChanged(self):
        detectorMode = self._widget.getDetectorMode()
        self._widget.setSpecificDetectorListVisible(detectorMode == -3)
        self._widget.setMultiDetectorSingleFileVisible(detectorMode in [-2, -3])

    def getDetectorNamesToCapture(self):
        """ Returns a list of which detectors the user has selected to be captured. """
        detectorMode = self._widget.getDetectorMode()
        if detectorMode == -1:  # Current detector at start
            return [self._master.detectorsManager.getCurrentDetectorName()]
        elif detectorMode == -2:  # All acquisition detectors
            return list(
                self._master.detectorsManager.execOnAll(
                    lambda c: c.name,
                    condition=lambda c: c.forAcquisition
                ).values()
            )
        elif detectorMode == -3:  # A specific detector
            return self._widget.getSelectedSpecificDetectors()

    def getFileName(self):
        """ Gets the filename of the data to save. """
        filename = self._widget.getCustomFilename()
        if filename is None:
            filename = time.strftime('%Hh%Mm%Ss')
        return filename

    def attrChanged(self, key, value):
        if self.settingAttr or len(key) != 2 or key[0] != _attrCategory or value == 'null':
            return

        if key[1] == _recModeAttr:
            if value == 'Snap':
                return
            self.setRecMode(RecMode[value])
        elif key[1] == _framesAttr:
            self._widget.setNumExpositions(value)
        elif key[1] == _timeAttr:
            self._widget.setTimeToRec(value)
        elif key[1] == _lapseTimeAttr:
            self._widget.setTimelapseTime(value)
        elif key[1] == _freqAttr:
            self._widget.setTimelapseFreq(value)

    def setSharedAttr(self, attr, value):
        self.settingAttr = True
        try:
            self._commChannel.sharedAttrs[(_attrCategory, attr)] = value
        finally:
            self.settingAttr = False

    def updateRecAttrs(self, *, isSnapping):
        self.setSharedAttr(_framesAttr, 'null')
        self.setSharedAttr(_timeAttr, 'null')
        self.setSharedAttr(_lapseTimeAttr, 'null')
        self.setSharedAttr(_freqAttr, 'null')

        if isSnapping:
            self.setSharedAttr(_recModeAttr, 'Snap')
        else:
            self.setSharedAttr(_recModeAttr, self.recMode.name)
            if self.recMode == RecMode.SpecFrames:
                self.setSharedAttr(_framesAttr, self._widget.getNumExpositions())
            elif self.recMode == RecMode.SpecTime:
                self.setSharedAttr(_timeAttr, self._widget.getTimeToRec())
            elif self.recMode == RecMode.ScanLapse:
                self.setSharedAttr(_lapseTimeAttr, self._widget.getTimelapseTime())
                self.setSharedAttr(_freqAttr, self._widget.getTimelapseFreq())

    def sendScanFreq(self):
        freq = self.getTimelapseFreq()
        self._commChannel.sigSendScanFreq.emit(freq)

    def getTimelapseFreq(self):
        return self._widget.getTimelapseFreq()


    def stop_stream(self):
        self.streamRunning = False
        self.streamstarted = False
        self.manager = None
        
    def start_stream(self):
        '''
        return a generator that converts frames into jpeg's reads to stream
        '''
        detectorManager = self._master.detectorsManager
        detectorNum1Name = detectorManager.getAllDeviceNames()[0]
        detectorNum1 = detectorManager[detectorNum1Name]
        detectorNum1.startAcquisition()
        
        self.fx = self.fy = .1
        
        try:
            while self.streamRunning:
                output_frame = detectorNum1.getLatestFrame()
                if output_frame is None:
                    continue
                try:
                    output_frame = cv2.resize(output_frame, dsize=None, fx=self.fx,fy=self.fx)
                except: 
                    output_frame = np.zeros((640,460))
                (flag, encodedImage) = cv2.imencode(".jpg", output_frame)
                if not flag:
                    continue
                self.manager.put(encodedImage)
        except:
            self.streamRunning = False
                
    def streamer(self):
        from multiprocessing import Queue
        if not self.streamstarted:
            import threading
            self.manager = Queue(maxsize=10)
            self.streamRunning = True
            threading.Thread(target=self.start_stream).start()
        try:

            while self.manager:
                yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' +
                    bytearray(self.manager.get()) + b'\r\n')
        except GeneratorExit:
            self.__logger.debug("cancelled")


    @APIExport(runOnUIThread=False)
    def video_feeder(self, startStream: bool = True) -> StreamingResponse:
        '''
        return a generator that converts frames into jpeg's reads to stream
        '''
        if startStream:
            return StreamingResponse(self.streamer(), media_type="multipart/x-mixed-replace;boundary=frame")
        else:
            self.stop_stream()
            return "stream stopped"





    #@app.post("/execute-function/")
    @APIExport(runOnUIThread=False)
    def executeFunction(self, code: str):
        try:
            # Create a new dictionary for local variables
            local_variables = {'self': self}
            global_variables = {'self': self}

            # Execute the provided code within the context of the current FastAPI runtime
            exec(code, globals(), local_variables)

            # Add the local variables to the shared dictionary
            self.shared_variables.update(local_variables)

            return {"message": "Function executed successfully", "result": local_variables}
        except Exception as e:
            self._logger.error(e)
            return HTTPException(detail=str(e), status_code=400)

    @APIExport(runOnUIThread=False)
    #@app.get("/get-variable/{variable_name}")
    def getVariable(self, variable_name: str):
        if variable_name in self.shared_variables:
            return {"variable_value": self.shared_variables[variable_name]}
        else:
            return HTTPException(detail="Variable not found", status_code=404)

    @APIExport(runOnUIThread=True)
    def snapImageToPath(self, fileName: str = "."):
        """ Take a snap and save it to a .tiff file at the given fileName. """
        self.snap(name = fileName, mSaveFormat=SaveFormat.TIFF)
    
    @APIExport(runOnUIThread=False)
    def snapImage(self, output: bool = False, toList: bool = True) -> Union[None, list]:
        """ 
        Take a snap and save it to a .tiff file at the set file path. 
        output: if True, return the numpy array of the image as a list if toList is True, or as a numpy array if toList is False
        toList: if True, return the numpy array of the image as a list, otherwise return it as a numpy array
        """
        if output:
            numpy_array_list = self.snapNumpy()
            mDetector = list(numpy_array_list.keys())[0]
            numpy_array = numpy_array_list[mDetector]
            if toList:
                return numpy_array.tolist()  # Convert the numpy array to a list
            else:
                return np.array(numpy_array)
        else:
            self.snap()

    @APIExport(runOnUIThread=False)
    def snapNumpyToFastAPI(self, detectorName: str=None, resizeFactor: float=1) -> Response:
        '''
        Taking a snap and return it as a FastAPI Response object.
        detectorName: the name of the detector to take the snap from. If None, take the snap from the first detector.
        resizeFactor: the factor by which to resize the image. If <1, the image will be downscaled, if >1, nothing will happen.
        '''
        # Create a 2D NumPy array representing the image
        images = self.snapNumpy()

        # get the image from the first detector if detectorName is not specified
        if detectorName is None:
            detectorName = self.getDetectorNamesToCapture()[0]

        # get the image from the specified detector    
        image = images[detectorName]

        if resizeFactor <1:
            image = self.resizeImage(image, resizeFactor)
                
        # eventually resize image to save bandwidth
        resizeFactor
        
        # using an in-memory image
        im = Image.fromarray(image)
        
        # save image to an in-memory bytes buffer
        # save image to an in-memory bytes buffer
        with io.BytesIO() as buf:
            im = im.convert('L')  # convert image to 'L' mode
            im.save(buf, format='PNG')
            im_bytes = buf.getvalue()
            
        headers = {'Content-Disposition': 'inline; filename="test.png"'}
        return Response(im_bytes, headers=headers, media_type='image/png')

    @APIExport(runOnUIThread=True)
    def startRecording(self) -> None:
        """ Starts recording with the set settings to the set file path. """
        self._widget.setRecButtonChecked(True)

    @APIExport(runOnUIThread=True)
    def stopRecording(self) -> None:
        """ Stops recording. """
        self._widget.setRecButtonChecked(False)

    @APIExport(runOnUIThread=True)
    def setRecModeSpecFrames(self, numFrames: int) -> None:
        """ Sets the recording mode to record a specific number of frames. """
        self.specFrames()
        self._widget.setNumExpositions(numFrames)

    @APIExport(runOnUIThread=True)
    def setRecModeSpecTime(self, secondsToRec: Union[int, float]) -> None:
        """ Sets the recording mode to record for a specific amount of time.
        """
        self.specTime()
        self._widget.setTimeToRec(secondsToRec)

    @APIExport(runOnUIThread=True)
    def setRecModeScanOnce(self) -> None:
        """ Sets the recording mode to record a single scan. """
        self.recScanOnce()

    @APIExport(runOnUIThread=True)
    def setRecModeScanTimelapse(self, lapsesToRec: int, freqSeconds: float,
                                timelapseSingleFile: bool = False) -> None:
        """ Sets the recording mode to record a timelapse of scans. """
        self.recScanLapse()
        self._widget.setTimelapseTime(lapsesToRec)
        self._widget.setTimelapseFreq(freqSeconds)
        self._widget.setTimelapseSingleFile(timelapseSingleFile)

    @APIExport(runOnUIThread=True)
    def setRecModeUntilStop(self) -> None:
        """ Sets the recording mode to record until recording is manually
        stopped. """
        self.untilStop()

    @APIExport(runOnUIThread=True)
    def setDetectorToRecord(self, detectorName: Union[List[str], str, int],
                            multiDetectorSingleFile: bool = False) -> None:
        """ Sets which detectors to record. One can also pass -1 as the
        argument to record the current detector, or -2 to record all detectors.
        """
        if isinstance(detectorName, int):
            self._widget.setDetectorMode(detectorName)
        else:
            if isinstance(detectorName, str):
                detectorName = [detectorName]
            self._widget.setDetectorMode(-3)
            self._widget.setSelectedSpecificDetectors(detectorName)
            self._widget.setMultiDetectorSingleFile(multiDetectorSingleFile)

    @APIExport(runOnUIThread=True)
    def setRecFilename(self, filename: Optional[str]) -> None:
        """ Sets the name of the file to record to. This only sets the name of
        the file, not the full path. One can also pass None as the argument to
        use a default time-based filename. """
        if filename is not None:
            self._widget.setCustomFilename(filename)
        else:
            self._widget.setCustomFilenameEnabled(False)

    @APIExport(runOnUIThread=True)
    def setRecFolder(self, folderPath: str) -> None:
        """ Sets the folder to save recordings into. """
        self._widget.setRecFolder(folderPath)

    def resizeImage(self, image, scale_factor):
        """
        Resize the input image by a given scale factor using nearest neighbor interpolation.

        Parameters:
            image (numpy.ndarray): The input image. For RGB, shape should be (height, width, 3),
                                for monochrome/grayscale, shape should be (height, width).
            scale_factor (float): The scaling factor by which to resize the image.

        Returns:
            numpy.ndarray: The resized image.
        """
        if len(image.shape) == 3 and image.shape[2] == 3:  # RGB image
            height, width, _ = image.shape
        elif len(image.shape) == 2:  # Monochrome/grayscale image
            height, width = image.shape
        else:
            raise ValueError("Invalid image shape. Supported shapes are (height, width, 3) for RGB and (height, width) for monochrome.")

        new_height, new_width = int(height * scale_factor), int(width * scale_factor)

        # Use OpenCV's resize function with nearest neighbor interpolation
        resized_image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_NEAREST)

        return resized_image



_attrCategory = 'Rec'
_recModeAttr = 'Mode'
_framesAttr = 'Frames'
_timeAttr = 'Time'
_lapseTimeAttr = 'LapseTime'
_freqAttr = 'LapseFreq'


# Copyright (C) 2020-2023 ImSwitch developers
# This file is part of ImSwitch.
#
# ImSwitch is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ImSwitch is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
