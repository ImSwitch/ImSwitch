from imswitch.imcontrol.model import DetectorInfo


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
