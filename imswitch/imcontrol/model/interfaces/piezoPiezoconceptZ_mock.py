from lantz import Action, Feat, Driver


class MockPCZPiezo(Driver):
    """Mock driver for the PiezoConcept Z-piezo."""

    def __init__(self):
        super().__init__()

    @Feat(read_once=True)
    def idn(self):
        """Get information of device"""
        #        return self.query('INFOS')
        dummyquery = 'dummy zpiezo answer'
        return dummyquery

    def initialize(self):
        pass

    # Z-MOVEMENT

    @Feat()
    def absZ(self):
        """ Absolute Z position. """
        return 2.0

    @absZ.setter
    def absZ(self, value):
        """ Absolute Z position movement, in um. """
        print(f"Mock PCZ: setting Z position to {value} um")

    def relZ(self, value):
        """ Relative Z position movement, in um. """
        print(f"Mock PCZ: moving Z position {value} um")
        pass
        if abs(float(value)) > 0.5:
            print('Warning: Step bigger than 500 nm')

    @Action()
    def move_relZ(self, value):
        """ Relative Z position movement, in um. """
        print(f"Mock PCZ: moving Z position {value} um")
        pass
        if abs(float(value)) > 0.5:
            print('Warning: Step bigger than 500 nm')

    @Action(limits=(100,))
    def move_absZ(self, value):
        """ Absolute Z position movement, in um. """
        print(f"Mock PCZ: setting Z position to {value} um")

    # CONTROL/STATUS

    @Feat()
    def timeStep(self):
        """ Get the time between each points sent by the RAM of the USB
        interface to the nanopositioner. """
        return 1

    @timeStep.setter
    def timeStep(self, value):
        """ Set the time between each points sent by the RAM of the USB
        interface to the nanopositioner, in ms. """
        pass

    def close(self):
        pass


# Copyright (C) 2020, 2021 TestaLab
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
