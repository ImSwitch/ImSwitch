from imswitch.imcommon.framework import SignalInterface
from imswitch.imcommon.model import initLogger


class TriggerScopeManager(SignalInterface):
    """ For interaction with TriggerScope hardware interfaces. """

    def __init__(self, setupInfo):
        super().__init__()
        self.__setupInfo = setupInfo
        self.__logger = initLogger(self)

    def test(self):
        self.__logger.debug("Test")

    def run(self):
        self.__logger.debug("Run")

