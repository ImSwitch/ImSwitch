# -*- coding: utf-8 -*-
"""
Created on Fri Mar 20 15:16:06 2020

@author: _Xavi
"""
import os

import constants
from model import config, instruments


class MainModel:
    def __init__(self):
        configFilesDir = os.path.join(constants.rootFolderPath, 'config_files')

        with open(os.path.join(configFilesDir, 'options.json')) as optionsFile:
            self.options = config.Options.from_json(optionsFile.read(), infer_missing=True)

        with open(os.path.join(configFilesDir, self.options.setupFileName)) as setupFile:
            self.setupInfo = config.SetupInfo.from_json(setupFile.read(), infer_missing=True)

        self.cameras = {}
        for cameraName, cameraInfo in self.setupInfo.cameras.items():
            camera = instruments.Camera(cameraInfo.id)
            self.initCamera(camera, cameraInfo)
            self.cameras[cameraName] = camera

        self.lasers = {}
        for laserName, laserInfo in self.setupInfo.lasers.items():
            if (laserInfo.digitalDriver is None or laserInfo.digitalPorts is None
                    or len(laserInfo.digitalPorts) < 1):
                continue

            laser = instruments.FullDigitalLaser(laserInfo.digitalDriver, laserInfo.digitalPorts)

            self.initLaser(laser)
            self.lasers[laserName] = laser

    def initCamera(self, camera, cameraInfo):
        for propertyName, propertyValue in cameraInfo.properties.items():
            camera.setPropertyValue(propertyName, propertyValue)

    def initLaser(self, laser):
        print(laser.idn)
        laser.digital_mod = False
        laser.enabled = False
        laser.digital_mod = True
        laser.autostart = False
        laser.autostart = False
