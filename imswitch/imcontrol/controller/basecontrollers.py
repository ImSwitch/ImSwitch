import functools
import os

from abc import abstractmethod

from imswitch.imcommon.controller import WidgetController, WidgetControllerFactory
from imswitch.imcontrol.model import InvalidChildClassError
from imswitch.imcommon.model import APIExport, dirtools, initLogger
from imswitch.imcontrol.view import guitools


class ImConWidgetControllerFactory(WidgetControllerFactory):
    """ Factory class for creating a ImConWidgetController object. """

    def __init__(self, setupInfo, master, commChannel, moduleCommChannel):
        super().__init__(setupInfo=setupInfo, master=master, commChannel=commChannel,
                         moduleCommChannel=moduleCommChannel)


class ImConWidgetController(WidgetController):
    """ Superclass for all ImConWidgetController.
    All WidgetControllers should have access to the setup information,
    MasterController, CommunicationChannel and the linked Widget. """

    def __init__(self, setupInfo, commChannel, master, *args, **kwargs):
        # Protected attributes, which should only be accessed from controller and its subclasses
        self._setupInfo = setupInfo
        self._commChannel = commChannel
        self._master = master

        # Init superclass
        super().__init__(*args, **kwargs)


class LiveUpdatedController(ImConWidgetController):
    """ Superclass for those controllers that will update the widgets with an
    upcoming frame from the camera.  Should be either active or not, and have
    an update function. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.active = False

    def update(self, detectorName, im, init, isCurrentDetector):
        raise NotImplementedError


class SuperScanController(ImConWidgetController):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make non-overwritable functions
        self.isValidScanController = self.__isValidScanController
        self.isValidChild = self.isValidScanController

        self._logger = initLogger(self)

        self.settingAttr = False
        self.settingParameters = False

        self._analogParameterDict = {}
        self._digitalParameterDict = {}
        self.signalDict = None
        self.scanInfoDict = None
        self.isRunning = False
        self.doingNonFinalPartOfSequence = False

        self.positioners = {
            pName: pManager for pName, pManager in self._setupInfo.positioners.items()
            if pManager.forScanning
        }
        self.TTLDevices = self._setupInfo.getTTLDevices()

        self.scanDir = os.path.join(dirtools.UserFileDirs.Root, 'imcontrol_scans')
        if not os.path.exists(self.scanDir):
            os.makedirs(self.scanDir)

        # Connect NidaqManager signals
        self._master.nidaqManager.sigScanBuilt.connect(
            lambda _, __, deviceList: self.emitScanSignal(self._commChannel.sigScanBuilt, deviceList)
        )
        self._master.nidaqManager.sigScanStarted.connect(
            lambda: self.emitScanSignal(self._commChannel.sigScanStarted)
        )
        self._master.nidaqManager.sigScanDone.connect(self.scanDone)
        self._master.nidaqManager.sigScanBuildFailed.connect(self.scanFailed)

        # Connect CommunicationChannel signals
        self._commChannel.sigRunScan.connect(self.runScanExternal)
        self._commChannel.sigAbortScan.connect(self.abortScan)
        self._commChannel.sharedAttrs.sigAttributeSet.connect(self.attrChanged)
        self._commChannel.sigToggleBlockScanWidget.connect(lambda block: self.toggleBlockWidget(block))
        self._commChannel.sigRequestScanParameters.connect(self.sendScanParameters)
        self._commChannel.sigSetAxisCenters.connect(lambda devices, centers: self.setCenterParameters(devices, centers))

        # Connect ScanWidget signals
        self._widget.sigSaveScanClicked.connect(self.saveScan)
        self._widget.sigLoadScanClicked.connect(self.loadScan)
        self._widget.sigRunScanClicked.connect(self.runScan)
        self._widget.sigSeqTimeParChanged.connect(self.updateScanTTLAttrs)
        self._widget.sigStageParChanged.connect(self.updatePixels)
        self._widget.sigStageParChanged.connect(self.updateScanStageAttrs)
        self._widget.sigSignalParChanged.connect(self.updateScanTTLAttrs)

    @property
    def parameterDict(self):
        return None

    def __isValidScanController(self):
        if self.parameterDict is None:
            raise InvalidChildClassError('ScanController needs to return a valid parameterDict')
        else:
            return True

    def runScanExternal(self, recalculateSignals, isNonFinalPartOfSequence):
        """ Run scan from external non-scan-widget trigger. """
        self._widget.setScanMode()
        self._widget.setRepeatEnabled(False)
        self.runScanAdvanced(recalculateSignals=recalculateSignals,
                             isNonFinalPartOfSequence=isNonFinalPartOfSequence,
                             sigScanStartingEmitted=True)
    
    @abstractmethod
    def setParameters(self):
        """ Set scan parameters from analog and digital parameter dictionaries. """
        pass

    @abstractmethod
    def getParameters(self):
        """ Get scan parameters from widget GUI fields. """
        pass

    @abstractmethod
    def updatePixels(self):
        """ Update number of pixels field in GUI. """
        pass

    @abstractmethod
    def emitScanSignal(self, signal, *args):
        """ Emit general scan signal. """
        pass

    @abstractmethod
    def runScanAdvanced(self, *, recalculateSignals=True, isNonFinalPartOfSequence=False,
                        sigScanStartingEmitted):
        """ Run a scan with the set scanning parameters. """
        pass

    @abstractmethod
    def scanDone(self):
        """ Called when scan is done, clean up and toggle GUI. """
        pass

    @APIExport(runOnUIThread=True)
    @abstractmethod
    def saveScanParamsToFile(self, filePath: str) -> None:
        """ Saves the set scanning parameters to the specified file. """
        pass

    @APIExport(runOnUIThread=True)
    @abstractmethod
    def loadScanParamsFromFile(self, filePath: str) -> None:
        """ Loads scanning parameters from the specified file. """
        pass

    def getNumScanPositions(self):
        """ Returns the number of scan positions for the configured scan. """
        _, positions, _ = self._master.scanManager.getScanSignalsDict(self._analogParameterDict)
        numPositions = functools.reduce(lambda x, y: x * y, positions)
        return numPositions

    def saveScan(self):
        """ Save scan parameters template. """
        fileName = guitools.askForFilePath(self._widget, 'Save scan', self.scanDir, isSaving=True)
        if not fileName:
            return
        self.saveScanParamsToFile(fileName)

    def loadScan(self):
        """ Load scan parameters template. """
        fileName = guitools.askForFilePath(self._widget, 'Load scan', self.scanDir)
        if not fileName:
            return
        self.loadScanParamsFromFile(fileName)

    def abortScan(self):
        """ Abort scan. """
        self.doingNonFinalPartOfSequence = False  # So that sigScanEnded is emitted
        if not self.isRunning:
            self.scanFailed()

    def scanFailed(self):
        """ Called when scan failed. """
        self._logger.error('Scan failed')
        self.isRunning = False
        self.doingNonFinalPartOfSequence = False
        self._widget.setScanButtonChecked(False)
        self.emitScanSignal(self._commChannel.sigScanEnded)

    def setCenterParameters(self, devices, centers):
        """ Set center parameter for all axes. """
        for centerpos, scannerSet in zip(centers, devices):
            # for every incoming device, listed in order of scanAxes
            for scannerAxis in self.positioners:
                # for every device, listed in order as device list
                if scannerSet == scannerAxis:
                    self._widget.setScanCenterPos(scannerSet, centerpos)

    def attrChanged(self, key, value):
        if self.settingAttr or len(key) != 2:
            return

        if key[0] == _attrCategoryStage:
            self._analogParameterDict[key[1]] = value
            self.setParameters()
        elif key[0] == _attrCategoryTTL:
            self._digitalParameterDict[key[1]] = value
            self.setParameters()
            
    def toggleBlockWidget(self, block):
        """ Blocks/unblocks scan widget if scans are run from elsewhere. """
        self._widget.setEnabled(block)

    def setSharedAttr(self, category, attr, value):
        self.settingAttr = True
        try:
            self._commChannel.sharedAttrs[(category, attr)] = value
        finally:
            self.settingAttr = False

    def updateScanStageAttrs(self):
        self.getParameters()

        for key, value in self._analogParameterDict.items():
            self.setSharedAttr(_attrCategoryStage, key, value)

        positiveDirections = []
        for i in range(len(self.positioners)):
            positionerName = self._analogParameterDict['target_device'][i]
            if positionerName != 'None':
                positiveDirection = self._setupInfo.positioners[positionerName].isPositiveDirection
                positiveDirections.append(positiveDirection)

        self.setSharedAttr(_attrCategoryStage, 'positive_direction', positiveDirections)

    def updateScanTTLAttrs(self):
        self.getParameters()

        for key, value in self._digitalParameterDict.items():
            self.setSharedAttr(_attrCategoryTTL, key, value)

    def getNumCamTTL(self):
        camTTL = self._master.scanManager.getTTLCycleSignalsDict(self._digitalParameterDict)['Green'].tolist()
        numCamTTL = len ([i for i in range(len(camTTL)-1) if camTTL[i+1]-camTTL[i] == 1]) #counting for first True in list
        return numCamTTL


    @APIExport(runOnUIThread=True)
    def runScan(self) -> None:
        """ Runs a scan with the set scanning parameters. """
        self.runScanAdvanced(sigScanStartingEmitted=False)
        
    def sendScanParameters(self):
        self.getParameters()
        self._commChannel.sigSendScanParameters.emit(self._analogParameterDict, self._digitalParameterDict, self._positionersScan)

_attrCategoryStage = 'ScanStage'
_attrCategoryTTL = 'ScanTTL'


# Copyright (C) 2020-2021 ImSwitch developers
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
