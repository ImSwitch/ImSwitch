from imcommon.framework import Signal, SignalInterface


class CommunicationChannel(SignalInterface):
    """
    Communication Channel is a class that handles the communication between Master Controller
    and Widgets, or between Widgets.
    """

    sigDataFolderChanged = Signal(object)  # (dataFolderPath)

    sigSaveFolderChanged = Signal(object)  # (saveFolderPath)

    sigCurrentDataChanged = Signal(object)  # (dataObj)

    sigScanParamsUpdated = Signal(object)  # (scanParDict)

    sigPatternUpdated = Signal(object)  # (pattern)

    sigPatternVisibilityChanged = Signal(bool)  # (visible)
