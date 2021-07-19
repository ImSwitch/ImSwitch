*******************************
Adding support for more devices
*******************************

There are three main device types that ImSwitch supports:
**detectors**, **lasers** and **positioners**.
In order to add support for a new detector, laser or positioner,
a corresponding device manager class must be implemented in ImSwitch's code.

Detector support is implemented in device manager classes derived from the abstract base class ``DetectorManager``.
The corresponding parent class for lasers is ``LaserManager``,
and for positioners it is ``PositionerManager``.
These derived classes are placed in the ``detectors``, ``lasers`` and ``positioners`` sub-modules respectively in the ``imswitch.imcontrol.model.managers`` module.

The required constructor signature for the device managers is ``__init__(deviceInfo, name, **lowLevelManagers)``.
``deviceInfo`` is the ``DetectorInfo``, ``LaserInfo`` or ``PositionerInfo`` object which represents the device's entry in the setup file
(see :doc:`the hardware control setup page <imcontrol-setups>` for further information).
Inside it, the ``managerProperties`` dict field may contain manager-specific properties.
``name`` is a unique name that is used to identify the device,
which is defined by the key of the device's entry in the setup file.
``lowLevelManagers`` is a dict containing objects that facilitate low-level device interaction,
which are documented :doc:`here <low-level-managers>`.
Note that ``super().__init__`` has a different signature, depending on which base class is used.

When creating a new device manager,
you will need to implement all the abstract methods and properties defined in the base class.
You should avoid overriding non-abstract properties.
Overriding non-abstract methods is generally fine,
but you should make sure that they continue to work as expected.
The device manager class must be placed in a .py file with the same name as the class,
in the appropriate location as outlined above.
No other action is required for the device manager to be available to use.

You can find a simple example of a positioner manager implementation `here <https://github.com/kasasxav/ImSwitch/blob/master/imswitch/imcontrol/model/managers/positioners/NidaqPositionerManager.py>`_.


Base class documentation
========================

DetectorManager
---------------

.. autoclass:: imswitch.imcontrol.model.managers.detectors.DetectorManager.DetectorManager
   :members:
   :special-members: __init__

.. autoclass:: imswitch.imcontrol.model.managers.detectors.DetectorManager.DetectorAction
   :members:
   :inherited-members:

.. autoclass:: imswitch.imcontrol.model.managers.detectors.DetectorManager.DetectorParameter

.. autoclass:: imswitch.imcontrol.model.managers.detectors.DetectorManager.DetectorNumberParameter
   :members:
   :inherited-members:
   :show-inheritance:

.. autoclass:: imswitch.imcontrol.model.managers.detectors.DetectorManager.DetectorListParameter
   :members:
   :inherited-members:
   :show-inheritance:


LaserManager
------------

.. autoclass:: imswitch.imcontrol.model.managers.lasers.LaserManager.LaserManager
   :members:
   :special-members: __init__


PositionerManager
-----------------

.. autoclass:: imswitch.imcontrol.model.managers.positioners.PositionerManager.PositionerManager
   :members:
   :special-members: __init__
