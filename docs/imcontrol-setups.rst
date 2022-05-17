*******************************
Hardware control configurations
*******************************

ImSwitch's hardware control module is designed to be flexible and be usable in a wide variety of microscopy setups.
In order to provide this flexibility,
hardware configurations are defined in .json files that are loaded when the hardware control module starts.

Hardware configuration files are loaded from the ``imcontrol_setups`` directory,
which is automatically created inside your user directory for ImSwitch the first time the hardware control module starts.
It contains some pre-made configuration files by default.
The user directory is located at ``%USERPROFILE%\Documents\ImSwitch`` on Windows and ``~/ImSwitch`` on macOS/Linux.

The first time you start the hardware control module,
you will be prompted to select a setup file to load.
If you want to switch to another hardware configuration later,
select "Tools" -> "Pick hardware setup…" in the hardware control module's menu bar.


How configurations are defined
==============================

Hardware configurations are defined in JSON format.
Behind the scenes,
they are automatically translated to Python class instances when loaded into the software.

A central concept in ImSwitch is that of device managers.
Device managers define what kind of device you have, and how ImSwitch communicates with it.
For example, if you have a Hamamatsu camera that you would like to control,
you would define a detector that uses the ``HamamatsuManager`` in the hardware setup file and set its appropriate properties.
The list of available managers and their properties can be found :ref:`here <Available managers>`.
Each device must have a unique name, which is represented by its object key in the JSON.

Signal designers, which are relevant for users who use the scan functionality, are similar.
Microscopy scans can be set up in different ways; in a point-scanning setup, for instance,
you might want to set your scan settings to use the ``PointScanTTLCycleDesigner`` to generate the appropriate TTL signals.
They are documented :ref:`here <Available signal designers>`.

As a very simple example,
a hardware configuration file that allows you to control a single Cobolt 06-01 (non-DPL) laser connected to COM port 11 can look like this:

.. code-block:: json

   {
       "lasers": {
           "Cobolt405nm": {
               "managerName": "Cobolt0601LaserManager",
               "managerProperties": {
                   "digitalPorts": ["COM11"]
               },
               "valueRangeMin": 0,
               "valueRangeMax": 200,
               "wavelength": 405
           }
       },
       "availableWidgets": [
           "Laser"
       ]
   }

Note that the ``digitalPorts`` property is specific to ``Cobolt0601LaserManager``.


Configuration file specification
================================

.. autoclassconheader:: imswitch.imcontrol.view.guitools.ViewSetupInfo.ViewSetupInfo
   :members:
   :inherited-members:


Item types that may be included
===============================

.. autoclassconheader:: imswitch.imcontrol.model.SetupInfo.DetectorInfo
   :members:
   :inherited-members:

.. autoclassconheader:: imswitch.imcontrol.model.SetupInfo.LaserInfo
   :members:
   :inherited-members:

.. autoclassconheader:: imswitch.imcontrol.model.SetupInfo.PositionerInfo
   :members:
   :inherited-members:

.. autoclassconheader:: imswitch.imcontrol.model.SetupInfo.RS232Info
   :members:
   :inherited-members:

.. autoclassconheader:: imswitch.imcontrol.model.SetupInfo.SLMInfo
   :members:
   :inherited-members:

.. autoclassconheader:: imswitch.imcontrol.model.SetupInfo.FocusLockInfo
   :members:
   :inherited-members:

.. autoclassconheader:: imswitch.imcontrol.model.SetupInfo.ScanInfo
   :members:
   :inherited-members:

.. autoclassconheader:: imswitch.imcontrol.model.SetupInfo.NidaqInfo
   :members:
   :inherited-members:

.. autoclassconheader:: imswitch.imcontrol.view.guitools.ViewSetupInfo.ROIInfo
   :members:
   :inherited-members:

.. autoclassconheader:: imswitch.imcontrol.view.guitools.ViewSetupInfo.LaserPresetInfo
   :members:
   :inherited-members:

.. autoclassconheader:: imswitch.imcontrol.model.SetupInfo.EtSTEDInfo
   :members:
   :inherited-members:


Available managers
==================

Detector managers
-----------------

.. autoclassconheader:: imswitch.imcontrol.model.managers.detectors.APDManager.APDManager

.. autoclassconheader:: imswitch.imcontrol.model.managers.detectors.HamamatsuManager.HamamatsuManager

.. autoclassconheader:: imswitch.imcontrol.model.managers.detectors.PhotometricsManager.PhotometricsManager

.. autoclassconheader:: imswitch.imcontrol.model.managers.detectors.TISManager.TISManager


Laser managers
--------------

.. autoclassconheader:: imswitch.imcontrol.model.managers.lasers.AAAOTFLaserManager.AAAOTFLaserManager

.. autoclassconheader:: imswitch.imcontrol.model.managers.lasers.Cobolt0601LaserManager.Cobolt0601LaserManager

.. autoclassconheader:: imswitch.imcontrol.model.managers.lasers.CoolLEDLaserManager.CoolLEDLaserManager

.. autoclassconheader:: imswitch.imcontrol.model.managers.lasers.NidaqLaserManager.NidaqLaserManager


Positioner managers
-------------------

.. autoclassconheader:: imswitch.imcontrol.model.managers.positioners.MHXYStageManager.MHXYStageManager

.. autoclassconheader:: imswitch.imcontrol.model.managers.positioners.NidaqPositionerManager.NidaqPositionerManager

.. autoclassconheader:: imswitch.imcontrol.model.managers.positioners.PiezoconceptZManager.PiezoconceptZManager


RS232 managers
--------------

.. autoclassconheader:: imswitch.imcontrol.model.managers.rs232.RS232Manager.RS232Manager


Available signal designers
==========================

Scan designers
--------------

.. autoclassconheader:: imswitch.imcontrol.model.signaldesigners.BetaScanDesigner.BetaScanDesigner

.. autoclassconheader:: imswitch.imcontrol.model.signaldesigners.GalvoScanDesigner.GalvoScanDesigner


TTL cycle designers
-------------------

.. autoclassconheader:: imswitch.imcontrol.model.signaldesigners.BetaTTLCycleDesigner.BetaTTLCycleDesigner

.. autoclassconheader:: imswitch.imcontrol.model.signaldesigners.PointScanTTLCycleDesigner.PointScanTTLCycleDesigner
