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
Utility methods for conversion of units to encoder counts.

The interfaces to the controllers have been left in their native "encoder counts", since
there are many different devices with different conversions between encoder counts (or stepper
motor microsteps etc) to position or angle.
Furthermore, real usage of motion devices will often involve a calibration routine, for example to 
convert linear translation stage motion to an optical delay path.
In this case it's more straightforward to convert time to encoder pulses directly, instead of
converting through a position intermediate (which may itself need to be calibrated properly).

This choice does make code a little more verbose, however with these utilities and some tricks
of python, that extra coding effort can be reduced.
For a particular combination of controller and motion device, it's recommended to use the python
`partial <https://docs.python.org/3/library/functools.html>`_ to build device-specific conversions.
For example, the documentation for the TDC001 controller lists a time unit of
:math:`2048/6 \\times 10^6` and with a MTS50-Z8 translation stage encoder counts per mm of 34304.
Custom conversion methods can be built: 

.. code-block:: python

    from functools import partial

    # Build our custom coversions using mm, mm/s and mm/s/s
    from_mm = partial(from_pos, factor=34304)
    from_mmps = partial(from_vel, factor=34304, t=2048/6e6)
    from_mmpsps = partial(from_acc, factor=34304, t=2048/6e6)
    to_mm = partial(from_pos, factor=1/34304)
    to_mmps = partial(from_vel, factor=1/34304, t=2048/6e6)
    to_mmpsps = partial(from_acc, factor=1/34304, t=2048/6e6)

    # ...

    # Perform moves in mm instead of encoder counts
    stage.move_relative(from_mm(12.34))

    # Check position in mm
    print(to_mm(stage.status["position"]))

Similar functions can be built for other units, for example where position is angle in degrees.

"""

def from_pos(pos, factor):
    """
    Convert from position in real units to encoder counts.

    The ``factor`` is the number of encoder counts per real unit, taken from the documentation for
    the device.
    For example, there are 20000 encoder counts per mm on the DDS600 translation stage, so using
    ``factor=20000`` would convert millimetres to encoder counts.

    :param factor: Conversion factor, encoder counts per unit.
    :returns: Number of encoder counts corresponding to ``pos``.
    """
    return int(factor*pos)

def from_vel(vel, factor, t):
    """
    Convert from velocity in real units to encoder counts per unit time.

    The ``factor`` parameter is the number of encoder counts per real unit, taken from the
    documentation for the device and is the same as for :meth:`from_pos`.
    The `t` is the time unit, again taken from the documentation for the controller.
    For example, the BBD201 controller has ``t=102.4e-6``.

    :param factor: Conversion factor, encoder counts per unit.
    :param t: Time unit for the controller.
    :returns: Number of encoder counts per unit time corresponding to ``vel``.
    """
    return int(factor*t*65536*vel)

def from_acc(acc, factor, t):
    """
    Convert from acceleration in real units to encoder counts per unit time squared.

    The ``factor`` parameter is the number of encoder counts per real unit, taken from the
    documentation for the device and is the same as for :meth:`from_pos`.
    The `t` is the time unit, again taken from the documentation for the controller, and is the
    same as for :meth:`from_vel`.

    :param factor: Conversion factor, encoder counts per unit.
    :param t: Time unit for the controller.
    :returns: Number of encoder counts per unit time squared corresponding to ``acc``.
    """
    return int(factor*t*t*65536*acc)

def to_pos(count, factor):
    """
    Convert to position in real units from encoder counts.

    The ``factor`` is the number of encoder counts per real unit, taken from the documentation for
    the device.
    For example, there are 20000 encoder counts per mm on the DDS600 translation stage, so using
    ``factor=20000`` would convert encoder counts to millimetres.

    :param factor: Conversion factor, encoder counts per unit.
    :returns: Position in real units corresponding to ``count``.
    """
    return(count/factor)

def to_vel(count, factor, t):
    """
    Convert to velocity in real units from encoder counts per unit time.

    The ``factor`` parameter is the number of encoder counts per real unit, taken from the
    documentation for the device and is the same as for :meth:`from_pos`.
    The `t` is the time unit, again taken from the documentation for the controller.
    For example, the BBD201 controller has ``t=102.4e-6``.

    :param factor: Conversion factor, encoder counts per unit.
    :param t: Time unit for the controller.
    :returns: Velocity in real units corresponding to ``count``.
    """
    return (count/(factor*t*65536))

def to_acc(count, factor, t):
    """
    Convert to acceleration in real units from encoder counts per unit time squared.

    The ``factor`` parameter is the number of encoder counts per real unit, taken from the
    documentation for the device and is the same as for :meth:`from_pos`.
    The `t` is the time unit, again taken from the documentation for the controller, and is the
    same as for :meth:`from_vel`.

    :param factor: Conversion factor, encoder counts per unit.
    :param t: Time unit for the controller.
    :returns: Acceleration in real units corresponding to ``count``.
    """
    return (count/(factor*t*t*65536))