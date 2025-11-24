import numpy as np
from scipy.interpolate import interp1d

from .LaserManager import LaserManager
from imswitch.imcommon.model import initLogger
from imswitch.imcontrol.controller import CommunicationChannel

class NidaqLaserManager(LaserManager):
    """ LaserManager for analog-value NI-DAQ-controlled lasers.

    Manager properties: None
    """

    def __init__(self, laserInfo, name, **lowLevelManagers):

        self._nidaqManager = lowLevelManagers['nidaqManager']
        self.__logger = initLogger(self, tryInheritParent=True)

        self._lut = None
        self._value_units = 'V'
        try:
            calib_csv_path = laserInfo.managerProperties["calibCsvPath"]
            self.create_lut_from_calib(calib_csv_path)
            self._value_units = '%'

        except AttributeError:
            pass # Calib file not specified, managerProperties doesnt exist
        except KeyError:
            pass  # Calib file not specified, managerProperties does exist but calib is missing
        except Exception as e:
            print(f"creating lut for {laserInfo} from calib failed due to: {e}")


        super().__init__(laserInfo, name, isBinary=laserInfo.getAnalogChannel() is None,
                         valueUnits=self._value_units, valueDecimals=2)

    def setEnabled(self, enabled):
        try:
            self._nidaqManager.setDigital(self.name, enabled)
        except:
            self.__logger.error("Error trying to enable laser.")

    def setValue(self, val, enabled=True, for_scanning=False):
        if self.isBinary:
            return
        if self._lut is not None:
            voltage = self._lut(val)
        else:
            voltage = val
        if for_scanning and not enabled:
            voltage = 0
        try:
            self._nidaqManager.setAnalog(
                target=self.name, voltage=voltage,
                min_val=self.valueRangeMin, max_val=self.valueRangeMax
            )
        except Exception as e:
            self.__logger.error(e, "Error trying to set value to laser.")

    def setScanModeActive(self, active, enabled=True):
        if active:
            self.setEnabled(False)
        # if laser was enable before the scan, it is enabled again. Value set to 0 first so that it does not get enabled
        # before laser preset is applied
        elif enabled:
            self.setValue(0, True)
            self.setEnabled(True)

    def create_lut_from_calib(self, calib_csv_path):
        data = np.loadtxt(calib_csv_path)
        data[:, 1] -= data[:, 1].min()
        data[:, 1] /= data[:, 1].max() * 0.01 # convert to %
        self._lut = interp1d(data[:, 1], data[:, 0], bounds_error=False)

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
