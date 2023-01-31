from imswitch.imcommon.framework import Signal, SignalInterface


class CommunicationChannel(SignalInterface):
    """
    Communication Channel is a class that handles the communication between Master Controller
    and Widgets, or between Widgets.
    """

    sigDataFolderChanged = Signal(object)  # (dataFolderPath)

    sigSaveFolderChanged = Signal(object)  # (saveFolderPath)

    sigCurrentDataChanged = Signal(object)  # (dataObj)

    sigScanParamsUpdated = Signal(object, bool)  # (scanParDict, applyOnCurrentRecon)

    sigPatternUpdated = Signal(object)  # (pattern)

    sigPatternVisibilityChanged = Signal(bool)  # (visible)

    sigAddToMultiData = Signal(str, str)  # (path, datasetName)

    sigReconstruct = Signal(object, bool)

    sigExecutionFinished = Signal(object)


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
