from typing import Mapping

import numpy as np
from imswitch.imcommon.framework import Signal, SignalInterface
from imswitch.imcommon.model import pythontools, APIExport, SharedAttributes
from imswitch.imcommon.model import initLogger


class CommunicationChannel(SignalInterface):
    """
    Communication Channel is a class that handles the communication between Master Controller
    and Widgets, or between Widgets.
    """

    sigUpdateImage = Signal(str, np.ndarray, bool, list, bool)

    sigAcquisitionStarted = Signal()

    sigAcquisitionStopped = Signal()

    sigScriptExecutionFinished = Signal()

    sigAdjustFrame = Signal(object)  # (shape)

    sigDetectorSwitched = Signal(str, str)  # (newDetectorName, oldDetectorName)

    sigGridToggled = Signal(bool)  # (enabled)

    sigCrosshairToggled = Signal(bool)  # (enabled)

    sigAddItemToVb = Signal(object)  # (item)

    sigRemoveItemFromVb = Signal(object)  # (item)

    sigRecordingStarted = Signal()

    sigRecordingEnded = Signal()

    sigUpdateRecFrameNum = Signal(int)  # (frameNumber)

    sigUpdateRecTime = Signal(int)  # (recTime)

    sigMemorySnapAvailable = Signal(
        str, np.ndarray, object, bool
    )  # (name, image, filePath, savedToDisk)

    sigRunScan = Signal(bool, bool)  # (recalculateSignals, isNonFinalPartOfSequence)

    sigAbortScan = Signal()

    sigScanStarting = Signal()

    sigScanBuilt = Signal(object)  # (deviceList)

    sigScanStarted = Signal()

    sigScanDone = Signal()

    sigScanEnded = Signal()

    sigSLMMaskUpdated = Signal(object)  # (mask)

    sigToggleBlockScanWidget = Signal(bool)

    sigSnapImg = Signal()

    sigSnapImgPrev = Signal(str, np.ndarray, str)  # (detector, image, nameSuffix)

    sigRequestScanParameters = Signal()

    sigSendScanParameters = Signal(dict, dict, object)  # (analogParams, digitalParams, scannerList)

    sigSetAxisCenters = Signal(object, object)  # (axisDeviceList, axisCenterList)

    sigStartRecordingExternal = Signal()

    sigRequestScanFreq = Signal()
    
    sigSendScanFreq = Signal(float)  # (scanPeriod)

    #sigRequestScannersInScan = Signal()

    #sigSendScannersInScan = Signal(object)  # (scannerList)

    sigSaveFocus = Signal()

    sigScanFrameFinished = Signal()  # TODO: emit this signal when a scanning frame finished, maybe in scanController if possible? Otherwise in APDManager for now, even if that is not general if you want to do camera-based experiments. Could also create a signal specifically for this from the scan curve generator perhaps, specifically for the rotation experiments, would that be smarter?
    
    sigUpdateRotatorPosition = Signal(str)  # (rotatorName)

    sigSetSyncInMovementSettings = Signal(str, float)  # (rotatorName, position)

    sigNewFrame = Signal()

    # useq-schema related signals
    sigSetXYPosition = Signal(float, float)
    sigSetZPosition = Signal(float)
    sigSetExposure = Signal(float)
    sigSetSpeed = Signal(float)

    @property
    def sharedAttrs(self):
        return self.__sharedAttrs

    def __init__(self, main, setupInfo):
        super().__init__()
        self.__main = main
        self.__sharedAttrs = SharedAttributes()
        self.__logger = initLogger(self)
        self._scriptExecution = False
        self.__main._moduleCommChannel.sigExecutionFinished.connect(self.executionFinished)

    def getCenterViewbox(self):
        """ Returns the center point of the viewbox, as an (x, y) tuple. """
        if 'Image' in self.__main.controllers:
            return self.__main.controllers['Image'].getCenterViewbox()
        else:
            raise RuntimeError('Required image widget not available')

    def getDimsScan(self):
        if 'Scan' in self.__main.controllers:
            return self.__main.controllers['Scan'].getDimsScan()
        else:
            raise RuntimeError('Required scan widget not available')

    def getNumScanPositions(self):
        if 'Scan' in self.__main.controllers:
            return self.__main.controllers['Scan'].getNumScanPositions()
        else:
            raise RuntimeError('Required scan widget not available')

    def get_image(self, detectorName=None):
        return self.__main.controllers['View'].get_image(detectorName)

    @APIExport(runOnUIThread=True)
    def acquireImage(self) -> None:
        image = self.get_image()
        self.output.append(image)

    def runScript(self, text):
        self.output = []
        self._scriptExecution = True
        self.__main._moduleCommChannel.sigRunScript.emit(text)

    def executionFinished(self):
        self.sigScriptExecutionFinished.emit()
        self._scriptExecution = False

    def isExecuting(self):
        return self._scriptExecution

    @APIExport()
    def signals(self) -> Mapping[str, Signal]:
        """ Returns signals that can be used with e.g. the getWaitForSignal
        action. Currently available signals are:

         - acquisitionStarted
         - acquisitionStopped
         - recordingStarted
         - recordingEnded
         - scanEnded

        They can be accessed like this: api.imcontrol.signals().scanEnded
        """

        return pythontools.dictToROClass({
            'acquisitionStarted': self.sigAcquisitionStarted,
            'acquisitionStopped': self.sigAcquisitionStopped,
            'recordingStarted': self.sigRecordingStarted,
            'recordingEnded': self.sigRecordingEnded,
            'scanEnded': self.sigScanEnded,
            'saveFocus': self.sigSaveFocus
        })


# Copyright (C) 2020-2022 ImSwitch developers
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
