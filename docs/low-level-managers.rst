******************
Low level managers
******************

What is a low level manager?
============================

In contrast with the ImSwitch ``Manager`` concept, low level managers represent 
a direct connection to an hardware object that does not represent a specific type of device.
Low level managers can interface with different managers at the same time, providing access points to .

Relevant examples of low level managers are:

- the `RS232Manager <https://github.com/ImSwitch/ImSwitch/blob/master/imswitch/imcontrol/model/managers/rs232/RS232Manager.py>`_;
  
  - it represents an RS232 interface over a specific port, which can be used by different managers at the same time to read/write over that same port;

- the `NidaqManager <https://github.com/kasasxav/ImSwitch/blob/master/imswitch/imcontrol/model/managers/NidaqManager.py>`_;
  
  - it represents an interface to a National Instrument Data AcQuisition (DAQ) card, exposing the functions of the `nidaqmx <https://nidaqmx-python.readthedocs.io/en/latest/>`_ package.

Every device manager constructor provides a dictionary parameter ``**lowLevelManagers``, which contains all the currently available low level managers instantiated in the `MasterController <https://github.com/ImSwitch/ImSwitch/blob/master/imswitch/imcontrol/controller/MasterController.py>`_.
A device manager can then access the functionalities of the low level manager directly, implementing a type of control specific to that class.

Low level manager use case
^^^^^^^^^^^^^^^^^^^^^^^^^^
An example of how to use a low level manager to control different types of devices via the same hardware interface is presented in the `NidaqLaserManager <https://github.com/kasasxav/ImSwitch/blob/master/imswitch/imcontrol/model/managers/lasers/NidaqLaserManager.py>`_ and the `NidaqPositionerManager <https://github.com/kasasxav/ImSwitch/blob/master/imswitch/imcontrol/model/managers/positioners/NidaqPositionerManager.py>`_:

- the first is an implementation of a ``LaserManager`` device;

- the second is an implementation of a ``PositionerManager`` device.

How to implement a new low level manager
========================================

These are the steps to integrate a new low level manager in your application:

- define your low level manager class in the folder ``imswitch\imcontrol\model\managers``;

  - there is currently no specific interface for a low level manager; relevant functions should be exposed depending on the implementation so that different classes of devices can make use of the manager functionalities;

- in ``imswitch\imcontrol\controller\MasterController.py``, create an instance of your low level manager and add a key-value couple in the ``lowLevelManagers`` dictionary, with:
  
  - the key being a ``str`` identifying your low level manager;
  - the value being the created instance of the low level manager itself.

- define type-specific classes to use your low level manager;

  - the constructor function signature should look like ``__init__(deviceInfo, name, **lowLevelManagers)``
