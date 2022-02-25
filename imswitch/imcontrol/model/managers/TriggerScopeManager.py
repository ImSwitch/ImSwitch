from imswitch.imcommon.framework import SignalInterface
from imswitch.imcommon.model import initLogger


class TriggerScopeManager(SignalInterface):
    """ For interaction with TriggerScope hardware interfaces. """

    def __init__(self, daqInfo, **lowLevelManagers):
        super().__init__()
        self._rs232manager = lowLevelManagers['rs232sManager'][
            daqInfo.managerProperties['rs232device']
        ]
        self.__logger = initLogger(self)

    def send(self, command, recieve):
        self.__logger.debug("Send command to RS232 device: " + command)
    
        if recieve:
            return self._rs232manager.send(command)
        else:
            self._rs232manager.send(command)
        
    def sendAnalog(self, dacLine, value):
        self.send("DAC" + str(dacLine) + "," + str(((value+5)/10)*65535), 0)

    def sendTTL(self, ttlLine, value):
        self.send("TTL" + str(ttlLine) + "," + str(value), 0)
        
    def run_wave(self, dacArray, ttlArray, params):
        command = "PROG_WAVE," + str(params["analogLine"]) + "," + str(params["digitalLine"]) + "," + str(params["length"]) + "," + str(params["trigMode"]) + "," + str(params["delay"]) + "," + str(params["reps"])
        self.send(command, 0)
        
        for x in range(params["length"]):
            command = str(((dacArray[x]+5)/10)*65535) + "," + str(ttlArray[x])
            self.send(command, 1)
            self.__logger.debug("Send: " + str(x))
            
        self.send("STARTWAVE", 0)

