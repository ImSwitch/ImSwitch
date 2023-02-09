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
        cmd = '71002'
        print(self._rs232Manager.query(cmd))  # print serial no of dmi stand

    def move(self, value, *args):
        if not int(value) == 0:
            cmd = '71024 ' + str(int(value))
            if int(value) > 132:
                print('Warning: Step bigger than 500nm.')
            self._rs232Manager.write(cmd)

        self._position = self._position + value
        return self._position

    def setPosition(self, value, *args):
        cmd = '71022 ' + str(int(value))
        self._rs232Manager.write(cmd)

        self._position = value
        return self._position

    def returnMod(self, reply):
        return reply[6:]

    def position(self, *args):
        cmd = '71023'
        return self.returnMod(self._rs232Manager.send(cmd))

    def motCorrPos(self, value):
        """ Absolute mot_corr position movement. """
        movetopos = int(round(value*93.83))
        cmd = '47022 -1 ' + str(movetopos)
        self._rs232Manager.write(cmd)

    # the serial command automatically sleeps until a reply is gotten, which it gets after flip is finished
    def setFLUO(self, *args):
        cmd = '70029 10 x'
        self._rs232Manager.query(cmd)

    # the serial command automatically sleeps until a reply is gotten, which it gets after flip is finished
    def setCS(self, *args):
        cmd = '70029 14 x'
        self._rs232Manager.query(cmd)

    def setILshutter(self, value):
        cmd = '77032 1 ' + str(value)
        self._rs232Manager.query(cmd)