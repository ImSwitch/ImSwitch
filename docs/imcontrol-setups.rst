******************************
Hardware Control Configuration
******************************

Hardware control configurations are to be placed in the ``imcontrol_setups`` directory,
which is created automatically inside your user directory for ImSwitch the first time the hardware control module starts.
The user directory is located at ``<your user's documents folder>\ImSwitch`` on Windows and ``~/ImSwitch`` on macOS/Linux.

The ``imcontrol_setups`` directory contains some pre-made configuration files by default.


Detector managers
=================

.. autoclassdocstr:: imswitch.imcontrol.model.managers.detectors.APDManager.APDManager

.. autoclassdocstr:: imswitch.imcontrol.model.managers.detectors.HamamatsuManager.HamamatsuManager

.. autoclassdocstr:: imswitch.imcontrol.model.managers.detectors.PhotometricsManager.PhotometricsManager

.. autoclassdocstr:: imswitch.imcontrol.model.managers.detectors.TISManager.TISManager


Laser managers
==============

.. autoclassdocstr:: imswitch.imcontrol.model.managers.lasers.AAAOTFLaserManager.AAAOTFLaserManager

.. autoclassdocstr:: imswitch.imcontrol.model.managers.lasers.CoboltLaserManager.CoboltLaserManager

.. autoclassdocstr:: imswitch.imcontrol.model.managers.lasers.CoolLEDLaserManager.CoolLEDLaserManager

.. autoclassdocstr:: imswitch.imcontrol.model.managers.lasers.NidaqLaserManager.NidaqLaserManager


Positioner managers
===================

.. autoclassdocstr:: imswitch.imcontrol.model.managers.positioners.MHXYStageManager.MHXYStageManager

.. autoclassdocstr:: imswitch.imcontrol.model.managers.positioners.NidaqPositionerManager.NidaqPositionerManager

.. autoclassdocstr:: imswitch.imcontrol.model.managers.positioners.PiezoconceptZManager.PiezoconceptZManager


RS232 manager
=============

A general-purpose RS232 manager that together with a general-purpose RS232Driver interface can handle an arbitrary RS232 communication channel,
with all the standard serial communication protocol parameters as defined in the hardware control configuration. 

Available manager properties:

- ``port``
- ``encoding``
- ``recv_termination``
- ``send_termination``
- ``baudrate``
- ``bytesize``
- ``parity``
- ``stopbits``
- ``rtscts``
- ``dsrdtr``
- ``xonxoff``


Misc. managers
==============

SLMManager
----------

A manager for that deals with a Hamamatsu SLM, connected with a video input connector.

Available manager properties:

- ``monitorIdx`` -- index of the monitor in the system list of monitors (indexing starts at 0)
- ``width`` -- width, in pixels, of SLM
- ``height`` -- height, in pixels, of SLM
- ``wavelength`` -- wavelength of the laser line used with the SLM
- ``pixelSize`` -- pixel size/pixel pitch, in mm, of the SLM
- ``angleMount`` -- the angle of incidence and reflection, in radians, of the laser line that is shaped by the SLM, for adding a blazed grating to create off-axis holography
- ``correctionPatternsDir`` -- directory of .bmp images provided by Hamamatsu for flatness correction at various wavelengths, a combination will be chosen based on the wavelength


Available widgets
=================

The following values are possible to include in the available widgets field (note: case sensitive):

- ``Settings`` (detector settings widget)
- ``View`` (image controls widget)
- ``Recording`` (recording widget)
- ``Image`` (image display widget)
- ``FocusLock`` (focus lock widget)
- ``SLM`` (SLM widget)
- ``Laser`` (laser control widget)
- ``Positioner`` (positioners widget)
- ``Scan`` (scan widget)
- ``BeadRec`` (bead reconstruction widget)
- ``AlignAverage`` (axial alignment tool widget)
- ``AlignXY`` (rotation alignment tool widget)
- ``AlignmentLine`` (line alignment tool widget)
- ``uLenses`` (uLenses tool widget)
- ``FFT`` (FFT tool widget)
- ``Console`` (Python console widget)
