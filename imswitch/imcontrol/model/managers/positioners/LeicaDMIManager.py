import numpy as np
from scipy.interpolate import interp1d

from imswitch.imcommon.model import initLogger
from imswitch.imcontrol.model.managers.positioners.PositionerManager import PositionerManager


class LeicaDMIManager(PositionerManager):
    def __init__(self, positionerInfo, name, *args, **lowLevelManagers):
        self.__logger = initLogger(self)
        try:
            self._rs232Manager = lowLevelManagers['rs232sManager'][positionerInfo.managerProperties['rs232device']]
        except:
            self.__logger.error(f'Failed to access Leica DMI stand RS232 connection with name {positionerInfo.managerProperties["rs232device"]}, define it in your setup .json. Loading mocker.')
            from imswitch.imcontrol.model.interfaces.RS232Driver_mock import MockRS232Driver
            self._rs232Manager = MockRS232Driver(name=positionerInfo.managerProperties['rs232device'], settings={'port': 'Mock'})

        self._lut_du_to_nm = None
        self._lut_nm_to_du = None
        self._value_units = 'arb'

        try:
            calib_csv_path = positionerInfo.managerProperties["calibCsvPath"]
            self.create_lut_from_calib(calib_csv_path)
            self._value_units = 'nm'
        except AttributeError:
            pass  # Calib file not specified, managerProperties doesnt exist
        except KeyError:
            pass  # Calib file not specified, managerProperties does exist but calib is missing
        except Exception as e:
            print(f"creating lut for {positionerInfo} from calib failed due to: {e}")

        cmd = '71003'
        print(self._rs232Manager.query(cmd))  # print serial no of dmi stand

    @property
    def resetOnClose(self):
        return False

    def move(self, value, *args):
        """
        Legacy: Move by in device units
        """
        if not int(value) == 0:
            cmd = '71024 ' + str(int(value))
            if int(value) > 132:
                print('Warning: Step bigger than 500nm.')
            self._rs232Manager.write(cmd)

        self._position = self._position + value
        return self._position


    def setPosition(self, value, *args):
        """
        Legacy: Move to in device units
        """
        cmd = '71022 ' + str(int(value))
        self._rs232Manager.write(cmd)

        self._position = value
        return self._position

    def get_pos_nm(self):
        """
        get absolute position in nm
        """
        cmd = '71023'
        pos_du = self._rs232Manager.query(cmd)
        self.__logger.debug(f"objective pos: {self._lut_du_to_nm(pos_du)}")

    def set_pos_nm(self, pos_nm):
        """
            set absolute position in nm
        """
        pos_du = int(self._lut_nm_to_du(pos_nm))
        cmd = '71022' + str(pos_du)
        self._rs232Manager.write(cmd)
        self._position = pos_du

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

    def setTLshutter(self, value):
        # turn TL lamp on or off, 0 = off, 1 = on
        if value == True:
            cmd_sfx = '1'
        else:
            cmd_sfx = '0'
        cmd = '77032 0 ' + cmd_sfx
        self._rs232Manager.query(cmd)

    def create_lut_from_calib(self, calib_csv_path):
        data = np.loadtxt(calib_csv_path)
        data[:, 1] *= 1E6 # convert to nm
        self._lut_nm_to_du = interp1d(data[:, 1], data[:, 0], bounds_error=False)
        self._lut_du_to_nm = interp1d(data[:, 0], data[:, 1], bounds_error=False)
