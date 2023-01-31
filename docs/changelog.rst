*********
Changelog
*********

2.0.0
=====

Highlights:

- Added support for Pulse Streamer and other devices, and improve low lever managers: https://github.com/kasasxav/ImSwitch/pull/1
- Server-client support with fastAPI and Pyro5: https://github.com/kasasxav/ImSwitch/tree/master/imswitch/imcontrol/controller/server
- Added features for open microscopy hardware (OpenUC2, SQUID, ESP32) more on beniroquai's fork
- Support for event triggered sted (https://www.nature.com/articles/s41592-022-01588-y)
- Improvements in scanning curve design
- Implementation of file watcher (see also https://github.com/kasasxav/napari-file-watcher/)
- Fix bugs (most reported in Issues).

A list of all code changes is available on GitHub: https://github.com/kasasxav/ImSwitch/compare/v1.2.1...v2.0.0

1.2.1
=====

Highlights:

- Snaps can now be saved to the image viewer (#64)
- Snaps can now be saved as tiff files (#75)
- Resolved the issue of not being able to run scans with only one positioner or only one laser
- Fixed the step up/down buttons not working properly for multi-axis positioners
- Fixed the api.imcontrol.setDetectorToRecord method not working

A list of all code changes is available on GitHub: https://github.com/kasasxav/ImSwitch/compare/v1.2.0...v1.2.1


1.2.0
=====

Highlights:

- Saving multi-detector and timelapse recordings in a single file is now supported (#53)
- Selecting specific detectors to record is now supported (#52)
- It is now possible to edit values/on-off-state of non-involved lasers during scanning (#51)
- The image reconstruction module now allows reconstructing all loaded data files (e.g. multi-file timelapses) into a single reconstruction (#34)
- The documentation has been improved (#61, #63)
- Fixed the SLM widget causing crashes on macOS (#57)
- Fixed the module picker being empty in standalone Windows bundles (#55)

A list of all code changes is available on GitHub: https://github.com/kasasxav/ImSwitch/compare/v1.1.0...v1.2.0


1.1.0
=====

Highlights:

- ImSwitch is now available to install from PyPI, and standalone Windows bundles are also available to download from the releases page on GitHub. (#38)
- User configuration files are now saved to an appropriate user directory. On Windows, this is the documents directory, and on other operating systems it's the user's home directory. (#40)
- Added a Tools menu item for setting active modules. (#27)
- Added an image shifting tool to the hardware control module. (#30)
- Added support for presets to laser widget. (#25)
- The laser widget is now a vertical list instead of a horizontal one. (#24)
- Resolved the issue of timelapse recordings sometimes containing too few frames. (#33)

A list of all code changes is available on GitHub: https://github.com/kasasxav/ImSwitch/compare/v1.0.0...v1.1.0


1.0.0
=====

Initial release.
