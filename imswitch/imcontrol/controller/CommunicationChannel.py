from typing import Mapping

import numpy as np
import Pyro5.server

from imswitch.imcommon.framework import Signal, SignalInterface, Thread, Worker
from imswitch.imcommon.model import pythontools, APIExport, SharedAttributes, initLogger
from .ImSwitchServer import ImSwitchServer


class CommunicationChannel(SignalInterface):
    """
    Communication Channel is a class that handles the communication between Master Controller
    and Widgets, or between Widgets.
    """

    sigUpdateImage = Signal(
        str, np.ndarray, bool, bool
    )  # (detectorName, image, init, isCurrentDetector)

    sigAcquisitionStarted = Signal()

    sigAcquisitionStopped = Signal()

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

    @property
    def sharedAttrs(self):
        return self.__sharedAttrs

    def __init__(self, main, setupInfo):
        super().__init__()
        self.__main = main
        self.__sharedAttrs = SharedAttributes()
        self._serverWorker = ServerWorker(self, setupInfo)
        self._thread = Thread()
        self._serverWorker.moveToThread(self._thread)
        self._thread.started.connect(self._serverWorker.run)
        self._thread.finished.connect(self._serverWorker.stop)
        self._thread.start()

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
            'scanEnded': self.sigScanEnded
        })


class ServerWorker(Worker):
    def __init__(self, channel, setupInfo):
        super().__init__()
        self.__logger = initLogger(self, tryInheritParent=True)
        self._server = ImSwitchServer(channel)
        self._channel = channel
        self._name = setupInfo.pyroServerInfo.name
        self._host = setupInfo.pyroServerInfo.host
        self._port = setupInfo.pyroServerInfo.port

    def run(self):
        self.__logger.debug("Started server with URI -> PYRO:" + self._name + "@" + self._host + ":" + str(self._port))
        Pyro5.server.serve(
            {self._server: self._name},
            use_ns=False,
            host=self._host,
            port=self._port,
        )
        self.__logger.debug("Loop Finished")

    def stop(self):
        self._daemon.shutdown()

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
