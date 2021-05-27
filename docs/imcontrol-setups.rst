******************************
Hardware Control Configuration
******************************

Hardware control configurations are to be placed in the /config/imcontrol_setups/ directory. You
can also find some pre-made configuration files there.


Detector managers
=================

APDManager
----------------

DetectorManager that deals with an avalanche photodiode connected to a counter input on a Nidaq card.

Available manager properties:

- ``terminal`` -- the physical input terminal on the Nidaq to which the APD is connected
- ``ctrInputLine`` -- the counter that the physical input terminal is connected to


HamamatsuManager
----------------

DetectorManager that deals with the Hamamatsu parameters and frame extraction for a Hamamatsu
camera.

Available manager properties:

- ``cameraListIndex`` -- the camera's index in the Hamamatsu camera list (list indexing starts at 0); set this to an invalid value, e.g. the string "mock" to load a mocker
- ``hamamatsu`` -- dictionary of DCAM API properties


TISManager
----------------

DetectorManager that deals with TheImagingSource cameras and the parameters for frame extraction from them.

Available manager properties:

- ``cameraListIndex`` -- the camera's index in the TIS camera list (list indexing starts at 0); set this string to an invalid value to load a mocker
- ``tis`` -- dictionary of TIS camera properties


Laser managers
==============

AAAOTFLaserManager
-------------------

LaserManager for controlling one channel of an AA Opto-Electronic acousto-optic modulator/tunable filter through RS232 communication.

Available manager properties:

- ``rs232device`` -- name of the defined rs232 communication channel through which the communication should take place
- ``channel`` -- index of the channel in the acousto-optic device that should be controlled (indexing starts at 1)


CoboltLaserManager
------------------
LaserManager for Cobolt lasers that are fully digitally controlled
using drivers available through Lantz. Uses digital modulation mode when
scanning.

Available manager properties: Same as LantzLaserManager.


CoolLEDLaserManager
---------------------

LaserManager for controlling coolLED though RS232 communication.

Available manager properties:

- rs232device -- name of the defined rs232 communication channel through which the communication should take place
- channel_index -- laser channel (A to H)


KatanaLaserManager
-------------------

LaserManager for controlling a OneFive Katana pulsed laser (NKT Photonics).

Available manager properties:

- ``rs232device`` -- name of the defined rs232 communication channel through which the communication should take place


LantzLaserManager
-----------------

Base LaserManager for lasers that are fully digitally controlled using
drivers available through Lantz.

Available manager properties:

- ``digitalDriver`` -- a string containing a Lantz driver name, e.g. "cobolt.cobolt0601.Cobolt0601"
- ``digitalPorts`` -- a string array containing the COM ports to connect to, e.g. ["COM4"]


NidaqAOLaserManager
-------------------

LaserManager for analog NI-DAQ-controlled lasers.

Available manager properties: None


Positioner managers
===================

NidaqPositionerManager
------------------------

PositionerManager for analog NI-DAQ-controlled positioners.

Available manager properties:

- ``conversionFactor`` -- float
- ``minVolt`` -- minimum voltage
- ``maxVolt`` -- maximum voltage


PiezoconceptZManager
------------------------

PositionerManager for control of a Piezoconcept Z-piezo through RS232-communication.

Available manager properties:

- ``rs232device`` -- name of the defined rs232 communication channel through which the communication should take place 


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

- ``monitorIdx`` -- index of the monitor in a list of monitors from wxPython (indexing starts at 0)
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
