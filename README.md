# ImSwitch

[![DOI](https://joss.theoj.org/papers/10.21105/joss.03394/status.svg)](https://doi.org/10.21105/joss.03394)

``ImSwitch`` is a software solution in Python that aims at generalizing microscope control by using an architecture based on the model-view-presenter (MVP) to provide a solution for flexible control of multiple microscope modalities.

## Statement of need

The constant development of novel microscopy methods with an increased number of dedicated
hardware devices poses significant challenges to software development. 
ImSwitch is designed to be compatible with many different microscope modalities and customizable to the
specific design of individual custom-built microscopes, all while using the same software. We
would like to involve the community in further developing ImSwitch in this direction, believing
that it is possible to integrate current state-of-the-art solutions into one unified software.

## Installation

### Option A: Standalone bundles for Windows

Windows users can download ImSwitch in standalone format from the [releases page on GitHub](https://github.com/kasasxav/ImSwitch/releases). Further information is available there. An existing Python installation is *not* required.

### Option B: Install using pip

ImSwitch is also published on PyPI and can be installed using pip. Python 3.7 or later is required. Additionally, certain components (the image reconstruction module and support for TIS cameras) require the software to be running on Windows, but most of the functionality is available on other operating systems as well.

To install ImSwitch from PyPI, run the following command:

```
pip install ImSwitch
```

(Developers installing ImSwitch from the source repository should run `pip install -r requirements-dev.txt` instead.)

You will then be able to start ImSwitch with this command:

```
imswitch
```

### Option C: Install from Github (UC2 version) 

**Installation**
```
cd ~/Downloads
git clone https://github.com/beniroquai/ImSwitch/
conda create -n imswitch python=3.8
conda activate imswitch
pip install -r requirements.txt --user 
pip install -e ./
```

**Start the imswitch**

```
cd imswitch
python __main__.py
```

**Add UC2 configuration**

in the folder ``, please add the following json file and name it `UC2_setup.py`. It gives you all what you need to start with:
* GRBL-controlled stage connected through USB 
* VIMBA camera connected through USB3 
* Laser/LED driver connected through Wifi/REST API

In order to get it work properly, you have to change the PORT (i.e. `COMX`, `/dev/ttyUSBX`, where `X` is a placeholder relating to your device number). The same holds true for the REST-API based device. Make sure the ESP32 is in the same Network as your computer. Make sure you can access it by entering the ESP32's ip in the browser e.g. `http://192.168.43.133/identify` (it will automatically connect to `SSID: Blynk`, `Password: 12345678`)

```json
{
  "positioners": {
    "GRBLStage": {
        "managerName": "GRBLStageManager",
        "managerProperties": {
          "rs232device_mac": "/dev/cu.wchusbserial14330",
          "rs232device": "COM14"
        },
        "axes": ["X", "Y", "Z"],
        "forScanning": true,
        "forPositioning": true
    }
},
"lasers": {
  "635 Laser": {
    "analogChannel": null,
    "digitalLine": null,
    "managerName": "ESP32LEDLaserManager",
    "managerProperties": {
        "host": "192.168.137.222",
        "channel_index": "R"
    },
    "wavelength": 635,
    "valueRangeMin": 0,
    "valueRangeMax": 32768
},
  "LED Array": {
    "analogChannel": null,
    "digitalLine": null,
    "managerName": "ESP32LEDMatrixManager",
    "managerProperties": {
        "host": "192.168.137.222"
    },
    "wavelength": 1000,
    "valueRangeMin": 0,
    "valueRangeMax": 255
  }
},
"detectors": {
  "WidefieldCamera": {
    "analogChannel": null,
    "digitalLine": null,
    "managerName": "AVManager",
    "managerProperties": {
      "cameraListIndex": 1,
      "avcam": {
        "exposure": 0,
        "gain": 0,
        "blacklevel": 100,
        "image_width": 1000,
        "image_height": 1000
      }
    },
    "forAcquisition": true
  }
},
  "rois": {
    "Full chip": {
      "x": 0,
      "y": 0,
      "w": 1000,
      "h": 2048
    }
  },
  "availableWidgets": [
    "Settings",
    "View",
    "Recording",
    "Image",
    "Laser",
    "Positioner"
  ]
}
```



## Documentation

Further documentation is available at [imswitch.readthedocs.io](https://imswitch.readthedocs.io).

## Testing

ImSwitch has automated testing through GitHub Actions, including UI and unit tests. It is also possible to manually inspect and test the software without any device since it contains mockers that are automatically initialized if the instrumentation specified in the config file is not detected.

## Contributing

Read the [contributing section](https://imswitch.readthedocs.io/en/latest/contributing.html) in the documentation if you want to help us improve and further develop ImSwitch!
