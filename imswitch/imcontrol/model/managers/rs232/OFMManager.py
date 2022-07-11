import openflexure_microscope_client as ofm_client # pip install UC2-REST

from imswitch.imcommon.model import initLogger
from imswitch.imcommon.model import APIExport

class OFMManager:
    """ A low-level wrapper for TCP-IP communication (OFM REST API)
    """

    def __init__(self, rs232Info, name, **_lowLevelManagers):
        self.__logger = initLogger(self, instanceName=name)
        self._settings = rs232Info.managerProperties
        self._name = name
        
        self.host = self._settings['host']
        self.__logger.debug(f"Attempting to connect to '{self.host}'")

        if self.host is None:
            self._OFM = ofm_client.find_first_microscope()
        else:        
            try:
                self._OFM = ofm_client.MicroscopeClient(self.host) 
            except:
                self.__logger.debug(f"Attempting to connect to '{self.host}' failed, looking for other HOST")
                self._OFM = ofm_client.find_first_microscope()    
    

    def finalize(self):
        pass


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
