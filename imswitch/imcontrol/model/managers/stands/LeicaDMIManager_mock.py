from imswitch.imcommon.model import initLogger


class MockLeicaDMIManager:
    def __init__(self, deviceInfo, *args, **kwargs):
        self.__logger = initLogger(self)
        try:
            self._rs232Manager = kwargs['rs232sManager']._subManagers[deviceInfo.rs232device]
        except:
            self.__logger.error(f'Failed to access Leica DMI stand RS232 connection with name {deviceInfo.rs232device}, define it in your setup .json. Loading mocker.')
            from imswitch.imcontrol.model.interfaces.RS232Driver_mock import MockRS232Driver
            self._rs232Manager = MockRS232Driver(name=deviceInfo.rs232device, settings={'port': 'Mock'})

    def move(self, value, *args):
        if not int(value) == 0:
            cmd = str(int(value))
            self._rs232Manager.write(cmd)

        self._position = self._position + value
        return self._position

    def setPosition(self, value, *args):
        cmd = str(int(value))
        self._rs232Manager.write(cmd)

        self._position = value
        return self._position

    def returnMod(self, reply):
        return reply

    def position(self, *args):
        cmd = '000'
        return self.returnMod(self._rs232Manager.send(cmd))

    def motCorrPos(self, value):
        """ Absolute mot_corr position movement. """
        movetopos = int(round(value))
        cmd = str(movetopos)
        self._rs232Manager.write(cmd)

    # the serial command automatically sleeps until a reply is gotten, which it gets after flip is finished
    def setFLUO(self, *args):
        cmd = '000'
        self._rs232Manager.query(cmd)

    # the serial command automatically sleeps until a reply is gotten, which it gets after flip is finished
    def setCS(self, *args):
        cmd = '000'
        self._rs232Manager.query(cmd)

    def setILshutter(self, value):
        cmd = str(value)
        self._rs232Manager.query(cmd)
        
    def setTLshutter(self, value):
        cmd = str(value)
        self._rs232Manager.query(cmd)
