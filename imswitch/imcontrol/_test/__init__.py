from imswitch.imcontrol.model import Options
from imswitch.imcontrol.view import ViewSetupInfo
import json
optionsBasic = Options.from_json("""
{
    "setupFileName": "",
    "recording": {
        "outputFolder": "D:\\\\Data\\\\",
        "includeDateInOutputFolder": true
    }
}
""")

setupInfoBasic = ViewSetupInfo.from_json("""
{
    "positioners": {
        "VirtualStage": {
          "managerNameGRBL": "GRBLStageManager",
          "managerName": "VirtualStageManager",
          "managerProperties": {
            "rs232device": "VirtualMicroscope",
            "isEnable": true, 
            "enableauto": false,
            "isDualaxis": 0,
            "stepsizeX": 1,
            "stepsizeY": 1,
            "stepsizeZ": 1,
            "stepsizeA": 1,
            "homeSpeedX": 15000,
            "homeSpeedY": 15000,
            "homeSpeedZ": 15000,
            "homeSpeedA": 15000,
            "homeDirectionX": 1,
            "homeDirectionY": 1,
            "homeDirectionZ": -1,
            "initialSpeed": {"X": 15000, "Y":  15000,"Z": 15000, "A": 15000}
          },
          "axes": [
            "X",
            "Y",
            "Z", 
            "A"
          ],
          "forScanning": true,
          "forPositioning": true
        }
      },
    "rs232devices": {
    "VirtualMicroscope": {
      "managerName": "VirtualMicroscopeManager",
      "managerProperties": {
      }
    }
  },
 "lasers": {
    "LED": {
      "analogChannel": null,
      "digitalLine": null,
      "managerName": "VirtualLaserManager",
      "managerProperties": {
        "rs232device": "VirtualMicroscope",
        "channel_index": 1
      },
      "wavelength": 635,
      "valueRangeMin": 0,
      "valueRangeMax": 1023
    }
  },
  "detectors": {
    "WidefieldCamera": {
        "analogChannel": null,
        "digitalLine": null,
        "managerName": "VirtualCameraManager",
        "managerProperties": {
            "isRGB": 0,
            "cameraListIndex": 0,
            "cameraEffPixelsize": 0.2257,
            "virtcam": {
                "exposure": 0,
                "gain": 0,
                "blacklevel": 100,
                "image_width": 1000,
                "image_height": 1000
            }
        },
        "forAcquisition": true,
        "forFocusLock": true
    }
    },
  "rois": {
    "Full chip": {
      "x": 600,
      "y": 600,
      "w": 1200,
      "h": 1200
    }
  },
  "fovLock": {
    "camera": "WidefieldCamera",
    "positioner": "VirtualStage",
    "updateFreq": 1, 
    "piKp":1, 
    "piKi":1
    },
    "sim": {
      "monitorIdx": 2,
      "width": 1080,
      "height": 1920,
      "wavelength": 0,
      "pixelSize": 0,
      "angleMount": 0,
      "patternsDir": "/users/bene/ImSwitchConfig/imcontrol_sim/488"
    },
    "dpc": {
      "wavelength": 0.53,
      "pixelsize": 0.2,
      "NA": 0.3,
      "NAi": 0.3,
      "n": 1.0,
      "rotations": [0, 180, 90, 270]
    },
  "PixelCalibration": {},
  "availableWidgets": [
    "Settings",
    "View",
    "Recording",
    "Image",
    "Laser",
    "Positioner",
    "Autofocus",
    "MCT",
    "ROIScan",
    "HistoScan",
    "Hypha" 
  ],
  "nonAvailableWidgets":[
    "FocusLock",
    "SIM", 
    "DPC",
    "FOVLock",
    "Temperature", 
    "HistoScan",
    "PixelCalibration", 
    "Lightsheet", 
    "WebRTC", 
    "Flatfield", 
    "STORMRecon",
    "DPC",    
    "ImSwitchServer",
    "PixelCalibration",
    "FocusLock"]
}
""", infer_missing=True)

setupInfoWithoutWidgets = ViewSetupInfo.from_json("""
{
  "positioners": {
    "ESP32Stage": {
      "managerName": "ESP32StageManager",
      "managerProperties": {
        "rs232device": "ESP32",
        "enableauto": 0,
        "isEnable": 1,
        "homeXenabled": true, 
        "homeStepsX":10000, 
        "homeOnStartX": true,
        "homeEndposReleaseX":5000,
        "homeYenabled": true, 
        "homeStepsY":10000, 
        "homeOnStartY": true,
        "homeEndposReleaseY":5000,
        "homeAenabled": true, 
        "homeStepsA":10000, 
        "homeOnStarta": true,
        "homeEndposReleaseA":5000,
        "stepsizeX": -0.3125,
        "stepsizeY": -0.3125,
        "stepsizeZ": 0.3125
      },
      "axes": [
        "X",
        "Y",
        "Z",
        "A"
      ],
      "forScanning": true,
      "forPositioning": true
    }
  },
  "rs232devices": {
    "ESP32": {
      "managerName": "ESP32Manager",
      "managerProperties": {
        "host_": "192.168.43.129",
        "serialport_": "COM3",
        "serialport": "COM3",
        "baudrate":500000, 
        "debug":1
       }
    }
  },
  "lasers": {
    "488 Laser": {
      "analogChannel": null,
      "digitalLine": null,
      "managerName": "ESP32LEDLaserManager",
      "managerProperties": {
        "rs232device": "ESP32",
        "channel_index":1,
        "filter_change": false,
        "laser_despeckle_period": 10,
        "laser_despeckle_amplitude": 0
      },
      "wavelength": 488,
      "valueRangeMin": 0,
      "valueRangeMax": 512
    },
    "LED Matrix": {
      "analogChannel": null,
      "digitalLine": null,
      "managerName": "ESP32LEDLaserManager",
      "managerProperties": {
        "rs232device": "ESP32",
        "channel_index": "LED",
        "filter_change": false,
        "filter_axis": 3,
        "filter_position": 32000,
        "filter_position_init": -0
      },
      "wavelength": 635,
      "valueRangeMin": 0,
      "valueRangeMax": 255
    }
  },
  "detectors": {
    "WidefieldCamera": {
        "analogChannel": null,
        "digitalLine": null,
        "managerName": "HikCamManager",
        "managerProperties": {
            "isRGB": 0,
            "cameraListIndex": 0,
            "cameraEffPixelsize": 0.2257,
            "hikcam": {
                "exposure": 0,
                "gain": 0,
                "blacklevel": 100,
                "image_width": 1000,
                "image_height": 1000
            }
        },
        "forAcquisition": true,
        "forFocusLock": true
    }
    },
  "rois": {
    "Full chip": {
      "x": 600,
      "y": 600,
      "w": 1200,
      "h": 1200
    }
  },
  "LEDMatrixs": {
    "ESP32 LEDMatrix": {
      "analogChannel": null,
      "digitalLine": null,
      "managerName": "ESP32LEDMatrixManager",
      "managerProperties": {
        "rs232device": "ESP32",
        "Nx": 4,
        "Ny": 4
      },
      "wavelength": 488,
      "valueRangeMin": 0,
      "valueRangeMax": 32768
    }
  },
  "autofocus": {
    "camera": "WidefieldCamera",
    "positioner": "ESP32Stage",
    "updateFreq": 10,
    "frameCropx": 780,
    "frameCropy": 400,
    "frameCropw": 500,
    "frameCroph": 100
  },
  "uc2Config": {
    "defaultConfig": "pindefWemos.json",
    "defaultConfig2": "pindefUC2Standalon2.json",
    "defaultConfig1": "pindefUC2Standalon.json"
  },
  "mct": {
    "monitorIdx": 2,
    "width": 1080,
    "height": 1920,
    "wavelength": 0,
    "pixelSize": 0,
    "angleMount": 0,
    "patternsDir": "/users/bene/ImSwitchConfig/imcontrol_sim/488"
  },
  "availableWidgets": [
    ]
}
""", infer_missing=True)

if __name__ == '__main__':
    print(setupInfoBasic)
    print(setupInfoWithoutWidgets)
    print(optionsBasic)

# Copyright (C) 2020-2023 ImSwitch developers
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
