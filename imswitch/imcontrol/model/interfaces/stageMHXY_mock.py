from lantz import Action, Feat, Driver

from imswitch.imcommon.model import initLogger


class MockMHXYStage(Driver):

    def __init__(self, SerialDriver=0):
        super().__init__()
        self.__logger = initLogger(self, tryInheritParent=True)
        self.__logger.debug('Simulated Marzhauser XY-stage')

    @Feat(read_once=True)
    def idn(self):
        """Get information of device"""
        return 'Marzhauser XY-stage mock'

    # XY-POSITION READING AND MOVEMENT

    @Feat()
    def absX(self):
        """ Read absolute X position, in um. """
        self.__logger.debug("Mock MHXY: Absolute position, X.")

    @Feat()
    def absY(self):
        """ Read absolute Y position, in um. """
        self.__logger.debug("Absolute position, Y.")

    @Action()
    def move_relX(self, value):
        """ Relative X position movement, in um. """
        self.__logger.debug(f"Move relative, X: {value} um.")

    @Action()
    def move_relY(self, value):
        """ Relative Y position movement, in um. """
        self.__logger.debug(f"Move relative, Y: {value} um.")

    @Action(limits=(100,))
    def move_absX(self, value):
        """ Absolute X position movement, in um. """
        self.__logger.debug(f"Set position, X: {value} um.")

    @Action(limits=(100,))
    def move_absY(self, value):
        """ Absolute Y position movement, in um. """
        self.__logger.debug(f"Set position, Y: {value} um.")

    # CONTROL/STATUS/LIMITS

    @Feat()
    def circLimit(self):
        """ Circular limits, in terms of X,Y center and radius. """
        self.__logger.debug("Ask circular limits.")

    @circLimit.setter
    def circLimit(self, xpos, ypos, radius):
        """ Set circular limits, in terms of X,Y center and radius. """
        self.__logger.debug(f"Ask circular limits, X: {xpos}, Y: {ypos}, radius: {radius}.")

    @Action()
    def function_press(self):
        """ Check function button presses. """
        self.__logger.debug("Check button presses.")

    def close(self):
        self.finalize()


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
