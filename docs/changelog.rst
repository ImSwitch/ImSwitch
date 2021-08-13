*********
Changelog
*********


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
