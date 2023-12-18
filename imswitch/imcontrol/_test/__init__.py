from imswitch.imcontrol.model import Options
from imswitch.imcontrol.view import ViewSetupInfo

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
    "StageX": {
      "managerName": "ESP32StageManager",
      "managerProperties": {
        "rs232device": "ESP32",
        "enableauto": 1,
        "isEnable": 1
      },
      "axes": ["X"],
      "forScanning": true,
      "forPositioning": true
    },
    "StageY": {
      "managerName": "ESP32StageManager",
      "managerProperties": {
        "rs232device": "ESP32",
        "enableauto": 1,
        "isEnable": 1
      },
      "axes": ["Y"],
      "forScanning": true,
      "forPositioning": true
    },
    "StageZ": {
      "managerName": "ESP32StageManager",
      "managerProperties": {
        "rs232device": "ESP32",
        "enableauto": 1,
        "isEnable": 1
      },
      "axes": ["Z"],
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
        "serialport": "/dev/cu.usbserial-A50285BI"
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
        "channel_index": 2,
        "filter_change": false,
        "laser_despeckle_period": 10,
        "laser_despeckle_amplitude": 0
      },
      "wavelength": 488,
      "valueRangeMin": 0,
      "valueRangeMax": 1024
    },
    "635 Laser": {
      "analogChannel": null,
      "digitalLine": null,
      "managerName": "ESP32LEDLaserManager",
      "managerProperties": {
        "rs232device": "ESP32",
        "channel_index": 1,
        "filter_change": false,
        "laser_despeckle_period": 10,
        "laser_despeckle_amplitude": 0
      },
      "wavelength": 635,
      "valueRangeMin": 0,
      "valueRangeMax": 1024
    },
    "LED": {
      "analogChannel": null,
      "digitalLine": null,
      "managerName": "ESP32LEDLaserManager",
      "managerProperties": {
        "rs232device": "ESP32",
        "channel_index": "3",
        "filter_change": false,
        "filter_axis": 3,
        "filter_position": 32000,
        "filter_position_init": -0
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
    },
    "ESP32Cam": {
      "ExtPackage": "imswitch_det_webcam",
      "analogChannel": null,
      "digitalLine": null,
      "managerName": "ESP32SerialCamManager",
      "managerProperties": {
        "cameraListIndex": 1,
        "gxipycam": {
          "exposure": 20,
          "gain": 0,
          "blacklevel": 10,
          "image_width": 1000,
          "image_height": 1000
        }
      },
      "forAcquisition": true,
      "forFocusLock": true
    }
  },
  "nidaq": {
    "timerCounterChannel": "Dev1/ctr2",
    "startTrigger": true
  },
  "rois": {
    "Full chip": {
      "x": 600,
      "y": 600,
      "w": 1200,
      "h": 1200
    }
  },
  "HistoScan": {
    "PreviewCamera": "ESP32Cam"
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
    "angleMount": 0
  },
  "dpc": {
    "wavelength": 0.53,
    "pixelsize": 0.2,
    "NA": 0.3,
    "NAi": 0.3,
    "n": 1.0,
    "rotations": [0, 180, 90, 270]
  },
  "webrtc": {},
  "PixelCalibration": {},
  "focusLock": {
    "camera": "ESP32Cam",
    "port": "COM5",
    "positioner": "ESP32StageManager",
    "updateFreq": 4,
    "frameCropx": 0,
    "frameCropy": 0,
    "frameCropw": 0,
    "frameCroph": 0
  },
  "availableWidgets": [
    "Settings",
    "Positioner",
    "View",
    "Recording",
    "Image",
    "Laser",
    "UC2Config",
    "Joystick",
    "Lightsheet",
    "ROIScan",
    "Scan"
  ],
  "scan": {
    "scanWidgetType": "PointScan",
    "scanDesigner": "GalvoScanDesigner",
    "scanDesignerParams": {},
    "TTLCycleDesigner": "PointScanTTLCycleDesigner",
    "TTLCycleDesignerParams": {},
    "sampleRate": 100000,
    "lineClockLine": "Dev1/port0/line5",
    "frameClockLine": "Dev1/port0/line6"
  }
}
""", infer_missing=True)

setupInfoWithoutWidgets = ViewSetupInfo.from_json("""
{
    "detectors": {
        "CAM": {
            "analogChannel": null,
            "digitalLine": 3,
            "managerName": "HamamatsuManager",
            "managerProperties": {
                "cameraListIndex": 0,
                "hamamatsu": {
                    "readout_speed": 3,
                    "trigger_global_exposure": 5,
                    "trigger_active": 2,
                    "trigger_polarity": 2,
                    "exposure_time": 0.01,
                    "trigger_source": 1,
                    "subarray_hpos": 0,
                    "subarray_vpos": 0,
                    "subarray_hsize": 2304,
                    "subarray_vsize": 2304
                }
            },
            "forAcquisition": true
        }
    },
    "lasers": {
        "405": {
            "analogChannel": null,
            "digitalLine": 0,
            "managerName": "Cobolt0601LaserManager",
            "managerProperties": {
                "digitalPorts": [
                    "COM9"
                ]
            },
            "wavelength": 405,
            "valueRangeMin": 0,
            "valueRangeMax": 200
        },
        "488": {
            "analogChannel": null,
            "digitalLine": 1,
            "managerName": "Cobolt0601LaserManager",
            "managerProperties": {
                "digitalPorts": [
                    "COM4",
                    "COM14"
                ]
            },
            "wavelength": 488,
            "valueRangeMin": 0,
            "valueRangeMax": 200
        }
    },
      "rs232devices": {
    "ESP32": {
      "managerName": "ESP32Manager",
      "managerProperties": {
        "host_": "192.168.43.129",
        "serialport_": "COM3",
        "serialport": "/dev/cu.usbserial-A50285BI"
      }
    }
  },
      "nidaq": {
    "timerCounterChannel": "Dev1/ctr2",
    "startTrigger": true
    },
  "positioners": {
    "ESP32Stage": {
      "managerName": "ESP32StageManager",
      "managerProperties": {
        "rs232device": "ESP32",
        "enableauto": 1,
        "isEnable": 1
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
    "scan": {
        "scanDesigner": "BetaScanDesigner",
        "scanDesignerParams": {
            "return_time": 0.01
        },
        "TTLCycleDesigner": "BetaTTLCycleDesigner",
        "TTLCycleDesignerParams": {},
        "sampleRate": 100000
    },
    "rois": {
        "Imaging": {
            "x": 520,
            "y": 292,
            "w": 1308,
            "h": 1308
        },
        "Test 2": {
            "x": 256,
            "y": 256,
            "w": 256,
            "h": 256
        },
        "imaging_20201215": {
            "x": 589,
            "y": 444,
            "w": 1308,
            "h": 1308
        },
        "beadscan_centre": {
            "x": 577,
            "y": 539,
            "w": 1345,
            "h": 1345
        },
        "Imaging-20212101": {
            "x": 616,
            "y": 572,
            "w": 1304,
            "h": 1304
        },
        "image-210121": {
            "x": 560,
            "y": 588,
            "w": 1308,
            "h": 1308
        }
    },
    "availableWidgets": []
}
""", infer_missing=True)


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
