******************************
Hardware Control Configuration
******************************

Hardware control configurations are to be placed in the /config/imcontrol_setups/ directory. You
can also find some pre-made configuration files there.


Detector managers
=================

HamamatsuManager
----------------

DetectorManager that deals with the Hamamatsu parameters and frame extraction for a Hamamatsu
camera.

Available manager properties:

- cameraListIndex -- the camera's index in the Hamamatsu camera list (list indexing starts at 0); set this to an invalid value, e.g. the string "mock" to load a mocker
- hamamatsu -- dictionary of DCAM API properties


Laser managers
==============

LantzLaserManager
-----------------------

LaserManager for lasers that are fully digitally controlled using
drivers available through Lantz.

Available manager properties:
- digitalDriver -- a string containing a Lantz driver name, e.g. "cobolt.cobolt0601.Cobolt0601"
- digitalPorts -- a string array containing the COM ports to connect to, e.g. ["COM4"]


NidaqAOLaserManager
-------------------

LaserManager for analog NI-DAQ-controlled lasers.

Available manager properties: None


Positioner managers
===================

NidaqAOPositionerManager
------------------------

PositionerManager for analog NI-DAQ-controlled positioners.

Available manager properties:
- conversionFactor -- float
- minVolt -- minimum voltage
- maxVolt -- maximum voltage
