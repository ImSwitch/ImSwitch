************************************************************
Setup configuration JSON and hardware control configurations
************************************************************

The hardware control module of ImSwitch is designed to be flexible and usable in a wide variety of microscopy setups.
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
Behind the scenes, they are automatically translated to Python class instances of the corresponding classes
as defined in ``imcontrol\model\SetupInfo`` when loaded into the software.
Each object in the JSON configuration needs to correspond to a Python class with the same name.

A central concept in ImSwitch is that of device managers.
Device managers define what kind of device you have, and how ImSwitch communicates with it.
For example, if you have a Hamamatsu camera that you would like to control,
you would define a new detector object in the ``detectors`` object that uses the ``HamamatsuManager`` in the hardware setup file and set its appropriate properties (``managerProperties``), e.g. the ``cameraListIndex``.
The list of available managers and their properties can be found :ref:`here <Available managers>`.
Each device must have a unique name, which is represented by its object key in the JSON.

See below for examples of how to implement new objects in the configuration setup info, examplified by a new laser, a new serial command communication channel, as well as a new widget requiring user-defined information. 

Signal designers, which are relevant for users who use the scan functionality, are similar and in the hardware configuration ``scan`` object you define which signal designer to use.
Microscopy scans can be set up in different ways; in a point-scanning setup, for instance,
you might want to set your scan settings to use the ``PointScanTTLCycleDesigner`` to generate the appropriate TTL signals.
They are documented :ref:`here <Available signal designers>`.

Example of hardware configuration for the implementation of a new laser
=======================================================================

As a very simple example,
a hardware configuration file that allows you to control a single Cobolt 06-01 (non-DPL)
laser connected to COM port 11 can look like this:

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

Note that the ``digitalPorts`` property is specific to ``Cobolt0601LaserManager``, as other LaserManagers might not use digital ports for communication.

Example of configuration for the implementation of a new RS232 communication object
===================================================================================

RS232 communication channels also need to be defined in the setup configuration, under the object ``rs232devices``.
Each object created here will define a new communication channel, using the parameters defined under its ``managerProperties``.
These created rs232 objects can be used by other devices that require serial command communication. 

As an example, a new laser controller requiring serial command communication would need both an rs232 object under ``rs232devices``,
see the example below where all the serial port specifications are defined,
but also an object under ``lasers``, where under its ``managerProperties`` the rs232device object should be referenced.

.. code-block:: json

   {
   "rs232devices": {
      "newLaser": {
         "managerName": "RS232Manager",
         "managerProperties": {
            "port": "ASRL4::INSTR",
            "encoding": "ascii",
            "recv_termination": "\n",
            "send_termination": "\r \n",
            "baudrate": 57600,
            "bytesize": 8,
            "parity": "none",
            "stopbits": 1,
            "rtscts": "false",
            "dsrdtr": "false",
            "xonxoff": "false"
         }
      }
   }


Example of configuration for a new device or widget requiring user-defined information
======================================================================================

As an example, implementing the SLM widget required some user-defined information regarding the SLM,
such as the size of the SLM, the wavelength to be used, the pixel size, and a local directory containing the flatness correction information.
For this, a new object in the setup configuration was implemented, called ``slm``, with the following information:

.. code-block:: json

   {
   "slm": {
      "monitorIdx": 2,
      "width": 792,
      "height": 600,
      "wavelength": 775,
      "pixelSize": 0.02,
      "correctionPatternsDir": "C:\\Local\\Directory"
      }
   }

Additionally, a new class needs to be defined in SetupInfo, here named ``SLMInfo``, where all of these parameters are defined with the expected data types.

.. code-block:: python

   @dataclass(frozen=True)
   class SLMInfo:
      monitorIdx: int
      """ Index of the monitor in the system list of monitors (indexing starts at
      0). """

      width: int
      """ Width of SLM, in pixels. """

      height: int
      """ Height of SLM, in pixels. """

      wavelength: int
      """ Wavelength of the laser line used with the SLM. """

      pixelSize: float
      """ Pixel size or pixel pitch of the SLM, in millimetres. """

      angleMount: float
      """ The angle of incidence and reflection of the laser line that is shaped
      by the SLM, in radians. For adding a blazed grating to create off-axis
      holography. """

      correctionPatternsDir: str
      """ Directory of .bmp images provided by Hamamatsu for flatness correction
      at various wavelengths. A combination will be chosen based on the
      wavelength. """

Finally, the expected ``slm`` setup configuration object needs to be connected to the SLMInfo class, which takes place in the SetupInfo class where a new field is added.
Here, the ``Optional`` tag defines that this does not generally have to be configured in the setup configuration JSON file, only if you want to use an SLM it needs to be defined, which should be the standard way of implementing a new SetupInfo field.
Instead, ``detectors``, ``lasers``, ``positioners``, and ``rs232devices`` are all required SetupInfo fields, however they can in the configuration file be left empty if no such devices are used in that configuration.

.. code-block:: python

    slm: Optional[SLMInfo] = field(default_factory=lambda: None)
    """ SLM settings. Required to be defined to use SLM functionality. """


Configuration file specification
================================

.. autoclassconheader:: imswitch.imcontrol.view.guitools.ViewSetupInfo.ViewSetupInfo
   :members:
   :inherited-members:

.. autoclassconheader:: imswitch.imcontrol.model.SetupInfo.SetupInfo
   :members:
   :inherited-members:


Example of implemented item types that may be included
======================================================

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
