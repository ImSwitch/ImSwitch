# -*- coding: utf-8 -*-
"""
Created on Fri Mar 20 15:16:06 2020

@author: _Xavi
"""
import os

import constants
from model import config, instruments


class TempestaModel:
    def __init__(self):
        configFilesDir = os.path.join(constants.rootFolderPath, 'config_files')
        with open(os.path.join(configFilesDir, 'setup.json')) as setupFile:
            self.setupInfo = config.SetupInfo.from_json(setupFile.read(), infer_missing=True)

        self.cameras = instruments.Cameras(0)

        self.lasers = {}
        for laserId, laserInfo in self.setupInfo.lasers.items():
            if (laserInfo.digitalDriver is None or laserInfo.digitalPorts is None
                    or len(laserInfo.digitalPorts) < 1):
                continue

            if len(laserInfo.digitalPorts) == 1:
                laser = instruments.Laser(laserInfo.digitalDriver, laserInfo.digitalPorts[0])
            else:
                laser = instruments.LinkedLaserCheck(laserInfo.digitalDriver, laserInfo.digitalPorts)

            self.initLaser(laser)
            self.lasers[laserId] = laser

    def initLaser(self, laser):
        print(laser.idn)
        laser.digital_mod = False
        laser.enabled = False
        laser.digital_mod = True
        laser.autostart = False
        laser.autostart = False
