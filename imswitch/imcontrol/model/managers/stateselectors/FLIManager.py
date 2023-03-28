import serial
from imswitch.imcommon.model import initLogger
from .StateSelectorManager import StateSelectorManager

position_dict = {
    0 : "-0",
    1 : "1",
    2 : "2",
    3 : "3",
    4 : "4",
    5 : "5",
    6 : "6",
    7 : "7",
    8 : "8",
    9 : "9"
}

class FLIManager(StateSelectorManager):
    """ StatesSelectorManager for FLI Filter wheel.

    Manager properties:

    None
    """

    def __init__(self, stateselectorInfo, name, **lowLevelManagers):
        self.__logger = initLogger(self, instanceName=name)
        self.__logger.debug('Initializing')
        self._serial = serial.Serial(port="COM4", baudrate=9600, bytesize=8,
                                                  timeout=2, stopbits=serial.STOPBITS_ONE,parity=serial.PARITY_NONE)

        super().__init__(stateselectorInfo, name)

    def move(self, cmd):
        cmd = int(cmd)
        data = "{0}\r\n".format(position_dict[cmd])
        self._serial.write(bytes(data, encoding="utf-8"))

    def finalize(self) -> None:
        self._serial.close()
