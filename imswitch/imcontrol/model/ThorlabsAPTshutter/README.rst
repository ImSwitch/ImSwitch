thorlabs_apt_device
===================

This is a python interface to Thorlabs equipment which communicates using the APT protocol.
Because there are a large variety of these devices, such as translation and rotation stages,
flip mounts and laser diode drivers, this package has been kept as general as possible.
A hierarchical class structure is designed such that basic functionality is handled transparently 
at low levels, allowing a minimal amount of code to be used to implement device-specific features.

In its current state, this package should be able to perform device discovery, communications and
message encoding/decoding for every APT-compatible device.
Classes for a small number of specific motion controllers are provided which give essentially
feature complete functionality for these particular devices.
To use a new, unsupported device, a subclass can be created which describes the specifics of
the device control and implement its new functionality.
If the device is very similar to something already implemented, then the amount of coding required
can be very small.
For example, the ``TDC001`` is a relatively simple DC motor driven
motion controller, and the class to implement it is only a few lines of code since it is able to
be derived from the ``APTDevice_Motor`` class.

The code has no dependence on the Thorlabs software or libraries, and so is platform-agnostic.
It has been tested on Linux and Windows, but should work on all other operating systems supported
by the pyserial library.

Support
-------

Documentation can be found online at `<https://thorlabs-apt-device.readthedocs.io/en/latest/>`_.

Bug reports, feature requests and suggestions can be submitted to the `issue tracker <https://gitlab.com/ptapping/thorlabs-apt-device/-/issues>`_.


License
-------

All original work is free and open source, licensed under the GNU Public License.
See the `LICENSE <https://gitlab.com/ptapping/thorlabs-apt-device/-/blob/main/LICENSE>`__ for details.

A fork of the `thorlabs-apt-protocol <https://gitlab.com/yaq/thorlabs-apt-protocol>`__ library is
included under the ``protocol`` directory, which remains under an MIT license.
See `LICENSE <https://gitlab.com/ptapping/thorlabs-apt-device/protocol/-/blob/main/LICENSE>`_ for details.