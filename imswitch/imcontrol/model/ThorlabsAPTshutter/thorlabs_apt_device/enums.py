# Copyright 2021 Patrick C. Tapping
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Enumerated values for the ThorLabs APT protocol.
"""

__all__ = ["EndPoint", "LEDMode"]

from enum import IntEnum

class EndPoint(IntEnum):
    """
    Numerical codes representing sources and destinations of messages.
    """
    HOST = 0x01
    RACK = 0x11
    BAY0 = 0x21
    BAY1 = 0x22
    BAY2 = 0x23
    BAY3 = 0x24
    BAY4 = 0x25
    BAY5 = 0x26
    BAY6 = 0x27
    BAY7 = 0x28
    BAY8 = 0x29
    BAY9 = 0x2A
    USB = 0x50

    @property
    def description(self):
        """
        Return a string describing the representation of the endpoint value.
        """
        return {
            EndPoint.HOST : "Host controller (control PC)",
            EndPoint.RACK : "Rack controller, motherboard in a card slot system or comms router board",
            EndPoint.BAY0 : "Bay 0 in a card slot system",
            EndPoint.BAY1 : "Bay 1 in a card slot system",
            EndPoint.BAY2 : "Bay 2 in a card slot system",
            EndPoint.BAY3 : "Bay 3 in a card slot system",
            EndPoint.BAY4 : "Bay 4 in a card slot system",
            EndPoint.BAY5 : "Bay 5 in a card slot system",
            EndPoint.BAY6 : "Bay 6 in a card slot system",
            EndPoint.BAY7 : "Bay 7 in a card slot system",
            EndPoint.BAY8 : "Bay 8 in a card slot system",
            EndPoint.BAY9 : "Bay 9 in a card slot system",
            EndPoint.USB  : "Generic USB hardware unit"
        }[self.value]


class LEDMode(IntEnum):
    """
    Numerical values corresponding to bit fields for device LED behaviour modes.

    These values represent bits in the bit field and can be combined with bitwise logic.
    For example, ``LEDMode.IDENT | LEDMode.MOVING`` would set the LED to flash when the identify
    message is sent, and also when the motor is moving.
    """
    IDENT = 1
    LIMITSWITCH = 2
    MOVING = 8

    @property
    def description(self):
        """
        Return a string describing the representation of the endpoint value.
        """
        return {
            LEDMode.IDENT : "LED will flash when the 'Identify' message is sent",
            LEDMode.LIMITSWITCH : "LED will flash when the motor reaches a forward or reverse limit switch",
            LEDMode.MOVING : "LED is lit when the motor is moving"
        }[self.value]
