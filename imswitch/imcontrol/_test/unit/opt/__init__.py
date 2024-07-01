from imswitch.imcontrol.model import DetectorInfo
from imswitch.imcontrol.view import ViewSetupInfo


detectorInfosNonSquare = {
    'CAM': DetectorInfo(
        analogChannel=None,
        digitalLine=3,
        managerName='HamamatsuManager',
        managerProperties={
            'cameraListIndex': 'mock',
            'hamamatsu': {
                'readout_speed': 3,
                'trigger_global_exposure': 5,
                'trigger_active': 2,
                'trigger_polarity': 2,
                'exposure_time': 0.01,
                'trigger_source': 1,
                'subarray_hpos': 0,
                'subarray_vpos': 0,
                'subarray_hsize': 1024,
                'subarray_vsize': 761,
                'image_width': 1024,
                'image_height': 761
            }
        },
        forAcquisition=True
    )
}

rotator = {
    "ArduinoStepper": {
        'managerName': 'TelemetrixRotatorManager',
        'managerProperties': {
            "startSpeed": 400,
            "stepsPerTurn": 3200,
            "maximumSpeed": 900,
            "acceleration": 200,
            "interface": "StepperDriver",
            "pinConfig": {
                "pin1": 2,
                "pin2": 3
            }
        }
    }
}

setupInfoOPTBasic = ViewSetupInfo.from_json("""
{
    "detectors": {
        "DMK": {
            "analogChannel": null,
            "digitalLine": null,
            "managerName": "TIS4Manager",
            "managerProperties": {
                "cameraListIndex": 0,  
                "tis": {
                    "pixel_format": "12bit",
                    "exposure": 1000,
                    "gain": 0,
                    "image_width": 2048,
                    "image_height": 1536,
                    "rotate_frame": "90"
                }
            },
            "forAcquisition": true,
            "forOpt": true
        }
    },
    "rotators": {
        "ArduinoStepper": {
            "managerName": "TelemetrixRotatorManager",
            "managerProperties": {
                "startSpeed": 400,
                "stepsPerTurn": 3200,
                "maximumSpeed": 900,
                "acceleration": 200,
                "interface": "StepperDriver",
                "pinConfig" : {
                    "pin1": 2,
                    "pin2": 3
                }
            }
        }
    },
    "optInfo": {
        "detectors": ["DMK"],
        "rotator": "ArduinoStepper"
    },
    "rois": {
      "Full chip": {
        "x": 0,
        "y": 0,
        "w": 2048,
        "h": 1536
      }
    },
    "availableWidgets": [
        "Settings",
        "View",
        "Recording",
        "Image",
        "Rotator",
        "Opt"
    ]
}
""", infer_missing=True)
