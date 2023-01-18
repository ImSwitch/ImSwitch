from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union

from imswitch.imcontrol.model import SetupInfo


@dataclass(frozen=True)
class ROIInfo:
    x: int
    """ Starting X position of ROI, in pixels. """

    y: int
    """ Starting Y position of ROI, in pixels. """

    w: int
    """ Width of ROI, in pixels. """

    h: int
    """ Height of ROI, in pixels. """


@dataclass(frozen=True)
class LaserPresetInfo:
    value: float
    """ Laser value. """

@dataclass(frozen=True)
class LEDPresetInfo:
    value: float
    """ LED value. """

# TODO: implement presets for OpentronsDeck
@dataclass(frozen=True)
class OpentronsDeckPresetInfo:
    value: float
    """ Laser value. """


@dataclass
class ViewSetupInfo(SetupInfo):
    """ This is the object represented by the hardware configuration JSON file.
    All fields are optional, unless explicitly otherwise specified. """

    # Quotes around type hints seem to be required for proper linking in the hardware control docs

    rois: Dict[str, 'ROIInfo'] = field(default_factory=dict)
    """ Additional ROIs available to select in detector settings. """
    # TODO: implement presets for OpentronsDeck
    OpentronsDeckPreset: Dict[str, Dict[str, 'OpentronsDeckPresetInfo']] = field(default_factory=dict)
    """ LED presets available to select (map preset name -> LED name ->
    LEDPresetInfo). """

    ledPresets: Dict[str, Dict[str, 'LEDPresetInfo']] = field(default_factory=dict)
    """ LED presets available to select (map preset name -> LED name ->
    LEDPresetInfo). """

    defaultLEDPresetForScan: Optional[str] = field(default_factory=lambda: None)
    """ Default LED preset for scanning. """

    laserPresets: Dict[str, Dict[str, 'LaserPresetInfo']] = field(default_factory=dict)
    """ Laser presets available to select (map preset name -> laser name ->
    LaserPresetInfo). """

    defaultLaserPresetForScan: Optional[str] = field(default_factory=lambda: None)
    """ Default laser preset for scanning. """

    availableWidgets: Union[List[str], bool] = field(default_factory=list)
    """ Which widgets to load. The following values are possible to include
    (case sensitive):

    - ``Settings`` (detector settings widget)
    - ``View`` (image controls widget)
    - ``Recording`` (recording widget)
    - ``Image`` (image display widget)
    - ``FocusLock`` (focus lock widget; requires ``focusLock`` field to be
      defined)
    - ``Autofocus`` (autofocus widget; requires ``focusLock`` field to be
      defined)      
    - ``SLM`` (SLM widget; requires ``slm`` field to be defined)
    - ``SIM`` (SIM widget; requires ``sim`` field to be defined)    
    - ``Laser`` (laser control widget)
    - ``LED`` (LED control widget)
    - ``Deck`` (Deck control widget)
    - ``OpentronsDeck`` (OpentronsDeck control widget)
    - ``Positioner`` (positioners widget)
    - ``StandaPositioner`` (Standa positioners widget)
    - ``StandaStage`` (Standa Stage widget)
    - ``Scan`` (scan widget; requires ``scan`` field to be defined)
    - ``BeadRec`` (bead reconstruction widget)
    - ``AlignAverage`` (axial alignment tool widget)
    - ``AlignXY`` (rotation alignment tool widget)
    - ``AlignmentLine`` (line alignment tool widget)
    - ``uLenses`` (uLenses tool widget; requires ``Image`` widget)
    - ``FFT`` (FFT tool widget)
    - ``Console`` (Python console widget)
    - ``EtSTED`` (etSTED widget; requires ``etSTED`` field to be defined)

    You can also set this to ``true`` to enable all widgets, or ``false`` to
    disable all widgets.

    This field is required.
    """

    def setROI(self, name, x, y, width, height):
        """ :meta private: """
        self.rois[name] = ROIInfo(x=x, y=y, w=width, h=height)

    def removeROI(self, name):
        """ :meta private: """
        try:
            del self.rois[name]
        except KeyError:
            pass

    def setLEDPreset(self, name, laserPresetInfos):
        """ :meta private: """
        self.laserPresets[name] = laserPresetInfos

    def removeLEDPreset(self, name):
        """ :meta private: """
        try:
            del self.laserPresets[name]
            if self.defaultLEDPresetForScan == name:
                self.setDefaultLEDPresetForScan(None)
        except KeyError:
            pass

    def setDefaultLEDPresetForScan(self, presetNameOrNone):
        """ :meta private: """
        self.defaultLEDPresetForScan = presetNameOrNone

    def setLaserPreset(self, name, laserPresetInfos):
        """ :meta private: """
        self.laserPresets[name] = laserPresetInfos

    def removeLaserPreset(self, name):
        """ :meta private: """
        try:
            del self.laserPresets[name]
            if self.defaultLaserPresetForScan == name:
                self.setDefaultLaserPresetForScan(None)
        except KeyError:
            pass

    def setDefaultLaserPresetForScan(self, presetNameOrNone):
        """ :meta private: """
        self.defaultLaserPresetForScan = presetNameOrNone

    def hasWidget(self, widget):
        """ :meta private: """
        return self.availableWidgets is True or (
            isinstance(self.availableWidgets, list) and widget in self.availableWidgets
        )


# Copyright (C) 2020-2021 ImSwitch developers
# This file is part of ImSwitch.
#
# ImSwitch is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ImSwitch is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
