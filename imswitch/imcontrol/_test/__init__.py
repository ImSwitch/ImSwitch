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
        },
        "473": {
            "analogChannel": 3,
            "digitalLine": 2,
            "managerName": "NidaqLaserManager",
            "managerProperties": {},
            "wavelength": 473,
            "valueRangeMin": 0,
            "valueRangeMax": 5
        }
    },
    "positioners": {
        "X": {
            "analogChannel": 0,
            "digitalLine": null,
            "managerName": "NidaqPositionerManager",
            "managerProperties": {
                "conversionFactor": 1.587,
                "minVolt": -10,
                "maxVolt": 10
            },
            "axes": ["X"],
            "forScanning": true,
            "forPositioning": true
        },
        "Y": {
            "analogChannel": 1,
            "digitalLine": null,
            "managerName": "NidaqPositionerManager",
            "managerProperties": {
                "conversionFactor": 1.587,
                "minVolt": -10,
                "maxVolt": 10
            },
            "axes": ["Y"],
            "forScanning": true,
            "forPositioning": true
        },
        "Z": {
            "analogChannel": 2,
            "digitalLine": null,
            "managerName": "NidaqPositionerManager",
            "managerProperties": {
                "conversionFactor": 10.0,
                "minVolt": 0,
                "maxVolt": 10
            },
            "axes": ["Z"],
            "forScanning": true,
            "forPositioning": true
        }
    },
    "scan": {
        "scanWidgetType": "Base",
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
    "availableWidgets": [
        "Settings",
        "View",
        "Recording",
        "Console",
        "Image",
        "Laser",
        "Positioner",
        "Scan",
        "AlignXY",
        "AlignAverage",
        "AlignmentLine",
        "BeadRec",
        "FFT",
        "ULenses"
    ]
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
        },
        "473": {
            "analogChannel": 3,
            "digitalLine": 2,
            "managerName": "NidaqLaserManager",
            "managerProperties": {},
            "wavelength": 473,
            "valueRangeMin": 0,
            "valueRangeMax": 5
        }
    },
    "positioners": {
        "X": {
            "analogChannel": 0,
            "digitalLine": null,
            "managerName": "NidaqPositionerManager",
            "managerProperties": {
                "conversionFactor": 1.587,
                "minVolt": -10,
                "maxVolt": 10
            },
            "axes": ["X"],
            "forScanning": true,
            "forPositioning": true
        },
        "Y": {
            "analogChannel": 1,
            "digitalLine": null,
            "managerName": "NidaqPositionerManager",
            "managerProperties": {
                "conversionFactor": 1.587,
                "minVolt": -10,
                "maxVolt": 10
            },
            "axes": ["Y"],
            "forScanning": true,
            "forPositioning": true
        },
        "Z": {
            "analogChannel": 2,
            "digitalLine": null,
            "managerName": "NidaqPositionerManager",
            "managerProperties": {
                "conversionFactor": 10.0,
                "minVolt": 0,
                "maxVolt": 10
            },
            "axes": ["Z"],
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
