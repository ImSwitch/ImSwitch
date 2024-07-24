""" This is a modifacation of the code of J. Alvelid to enable SLM into the MoNaLisa set up 
author: G. Lecarme
date: 31/05/2024
__version__ = 0.1.0
"""

import os
import glob
import enum
import numpy as np
from PIL import Image
import math
from scipy import signal as sg
from pathlib import Path
import matplotlib.pyplot as plt

from imswitch.imcommon.framework import Signal, SignalInterface
from imswitch.imcommon.model import initLogger

class SLMmlManager(SignalInterface):
    sigSLMMaskUpdated = Signal(object)  # (maskCombined)
    
    def __init__(self, slm_info, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__logger = initLogger(self)
        
        if slm_info is None:
            return

        self.__slmInfo = slm_info
        self.__wavelength = self.__slmInfo.wavelength
        self.__serial_number = self.__slmInfo.serial_number
        self.__pixelsize = self.__slmInfo.pixelSize
        self.__slmSize = (self.__slmInfo.width, self.__slmInfo.height)
        self.__correctionPatternsDir = self.__slmInfo.correctionPatternsDir
        self.__mask = Mask(self.__slmSize[1], self.__slmSize[0], self.__wavelength)
        self.applyMFA = False

        self.initFresnelLensMask()
        self.initCorrectionMask()
        self.initTiltMask()
        self.initAberrationMask()
        self.initMFAMask()

        self.update(maskChange=True, tiltChange=True, aberChange=True, focalChange=True)
        
    def saveState(self, state_general=None, state_pos=None, state_aber=None):
        if state_general is not None:
            self.state_general = state_general
        if state_pos is not None:
            self.state_pos = state_pos
        if state_aber is not None:
            self.state_aber = state_aber
            
    def initCorrectionMask(self):
        # Add correction mask with correction pattern
        self.__maskCorrection = Mask(self.__slmSize[1], int(self.__slmSize[0]), self.__wavelength)
        bmpsCorrection = glob.glob(os.path.join(self.__correctionPatternsDir, "*.bmp"))

        if len(bmpsCorrection) < 1:
            self.__logger.error(
                'No BMP files found in correction patterns directory, cannot initialize correction'
                ' mask.'
            )
            return

        try:
            self.__maskCorrection.loadBMP(f'CAL_{self.__serial_number}_{self.__wavelength}nm',
                                        self.__correctionPatternsDir)
        except:
            self.__logger.error(
                'No correction file found in correction patterns directory for this wavelength,'
                ' cannot initialize correction mask.'
            )
            return
        
        
    def initTiltMask(self):
        # Add blazed grating tilting mask
        self.__maskTilt = Mask(self.__slmSize[1], self.__slmSize[0], self.__wavelength)
        self.__maskTilt.setTilt(self.__pixelsize)
        
    def initAberrationMask(self):
        self.__maskAber = Mask(self.__slmSize[1], self.__slmSize[0], self.__wavelength)
        self.__maskAber.setBlack()
        
    def initFresnelLensMask(self):
        self.__maskLens = Mask(self.__slmSize[1], self.__slmSize[0], self.__wavelength)
        self.__maskLens.setFresnelLens(self.__pixelsize)
        
    def initMFAMask(self):
        self.__maskMFA = Mask(self.__slmSize[1], self.__slmSize[0], self.__wavelength)
        self.__maskMFA.setBlack()
    
    def setMask(self, maskMode):
        if self.__mask.mask_type == MaskMode.Black and maskMode != MaskMode.Black:
            self.__maskTilt.setTilt(self.__pixelsize)
        if maskMode == maskMode.Donut:
            self.__mask.setDonut()
        elif maskMode == maskMode.Tophat:
            self.__mask.setTophat()
        elif maskMode == maskMode.Half:
            self.__mask.setHalf()
        elif maskMode == maskMode.Gauss:
            self.__mask.setGauss()
        elif maskMode == maskMode.Hex:
            self.__mask.setHex()
        elif maskMode == maskMode.Quad:
            self.__mask.setQuad()
        elif maskMode == maskMode.Split:
            self.__mask.setSplit()
        elif maskMode == maskMode.Black:
            self.__mask.setBlack()
            self.__maskTilt.setBlack()
            self.__maskAber.setBlack()
            
    def moveMask(self, direction, amount):
        if direction == direction.Up:
            move_v = np.array([-1, 0]) * amount
        elif direction == direction.Down:
            move_v = np.array([1, 0]) * amount
        elif direction == direction.Left:
            move_v = np.array([0, -1]) * amount
        elif direction == direction.Right:
            move_v = np.array([0, 1]) * amount

        self.__mask.moveCenter(move_v)
        self.__maskTilt.moveCenter(move_v)
        self.__maskAber.moveCenter(move_v)
        
    def getCenter(self):
        centerCoords = {"mask": self.__mask.getCenter()}
        return centerCoords

    def setCenter(self, centerCoords):
        center = (centerCoords["mask"]["xcenter"], centerCoords["mask"]["ycenter"])
        self.__mask.setCenter(center)
        self.__maskTilt.setCenter(center)
        self.__maskAber.setCenter(center)
        
    def setGeneral(self, general_info):
        self.setRadius(general_info["radius"])
        self.setFocal(general_info["focal"])
        self.setSigma(general_info["sigma"])
        self.setRotationAngle(general_info["rotationAngle"])
        self.setTiltAngle(general_info["tiltAngle"])
        
    def setRadius(self, radius):
        self.__mask.setRadius(radius)
        self.__maskTilt.setRadius(radius)
        self.__maskAber.setRadius(radius)
        self.__maskLens.setRadius(radius)
    
    def setFocal(self, focal):
        self.__maskLens.setFocal(focal)
        
    def setSigma(self, sigma):
        self.__mask.setSigma(sigma)
        
    def setRotationAngle(self, rotation_angle):
        self.__mask.setRotationAngle(rotation_angle)

    def setTiltAngle(self, tilt_angle):
        self.__maskTilt.setTiltAngle(tilt_angle)
        
    def setAberrationFactors(self, aber_info):
        AberFactors = aber_info["mask"]
        self.__maskAber.setAberrationFactors(AberFactors)
        
    def setAberrations(self, aber_info):  
        AberFactors = aber_info["mask"]
        self.__maskAber.setAberrationFactors(AberFactors)
        self.__maskAber.setAberrations()
    
    def updateMFApath(self,path):
        self.__maskMFA.MFApath = path

    def update(self, maskChange=False, tiltChange=False, aberChange=False, focalChange=False):
        if maskChange:
            self.__mask.updateImage()
            self.mask = self.__mask
        if tiltChange:
            self.__maskTilt.updateImage()
            self.maskTilt = self.__maskTilt
        if aberChange:
            self.__maskAber.updateImage()
            self.maskAber = self.__maskAber
        if focalChange:
            self.__maskLens.updateImage()
            self.__maskLens.setCircular()
            self.maskLens = self.__maskLens
        
        #MFA
        if self.applyMFA:
            self.__maskMFA.mask_type = MaskMode.MFA
        else:
            self.__maskMFA.mask_type = MaskMode.Black
        self.__maskMFA.updateImage()
        self.maskMFA = self.__maskMFA
        
        self.maskCombined = self.mask + self.maskAber + self.maskTilt + self.maskLens \
                                               + self.maskMFA + self.__maskCorrection
        self.sigSLMMaskUpdated.emit(self.maskCombined)
        returnmask = self.mask + self.maskAber + self.maskTilt + self.maskMFA
        returnmask.img[:, 0:10] = 255
        return returnmask.image()
            
            
class Mask:
    """Class creating a mask to be displayed by the SLM."""

    def __init__(self, height: int, width: int, wavelength: int):
        """initiates the mask as an zeros array
        n,m corresponds to the width,height of the created image
        wavelength is the illumination wavelength in nm"""
        self.__logger = initLogger(self, tryInheritParent=True)
        self.zeroimg = np.zeros((height, width), dtype=np.uint8)
        self.img = np.zeros((height, width), dtype=np.uint8)
        self.height = height
        self.width = width
        self.value_max = 255
        self.centerx = self.height // 2
        self.centery = self.width // 2
        self.radius = 500
        self.sigma = 200
        self.focal = 343
        self.MFApath = None
        self.wavelength = wavelength
        self.mask_type = MaskMode.Black
        self.angle_rotation = 0
        self.angle_tilt = 0
        self.pixelSize = 0
        if wavelength == 488:
            self.value_max = 139
        elif wavelength == 690:
            self.value_max = 221
        else:
            # Here we infer the value of the maximum with a linear approximation from the ones
            # provided by the manufacturer
            # Better ask them in case you need another wavelength
            self.value_max = int(wavelength * (221-139)/(690-488) + 139 - 488*(221-139)/(690-488))
            self.__logger.warning("Caution: a linear approximation has been made")
            
    def loadArray(self, mask):
        self.img = mask

    def image(self):
        return self.img


    def loadBMP(self, filename, path):
        """Loads a .bmp image as the img of the mask."""
        with Image.open(os.path.join(path, filename + ".bmp")) as data:
            imgLoad = np.array(data)
        heightLoad, widthLoad = imgLoad.shape
        if heightLoad > self.height:
            diff = heightLoad - self.height
            imgLoad = imgLoad[(diff // 2): (self.height + diff // 2), :]
        if widthLoad > self.width:
            diff = widthLoad - self.width
            imgLoad = imgLoad[:, diff // 2: self.width + diff // 2]

        if heightLoad <= self.height and widthLoad <= self.width:
            result = np.zeros((self.height, self.width))
            diffx = (self.width - widthLoad) // 2
            diffy = (self.height - heightLoad) // 2
            result[diffy: heightLoad + diffy, diffx: widthLoad + diffx] = imgLoad
            imgLoad = result

        self.height, self.width = imgLoad.shape
        self.img[:, :] = imgLoad[:, :]
        self.scaleToLut()

    def scaleToLut(self):
        """Scales the values of the pixels according to the LUT"""
        self.img = self.img.astype("float")
        self.img *= self.value_max / np.max(self.img)
        self.img = self.img.astype("uint8")

    def pi2uint8(self):
        """Method converting a phase image (values from 0 to 2Pi) into a uint8
        image"""
        self.img *= self.value_max / (2 * np.pi)
        self.img = np.round(self.img).astype(np.uint8)
        
    def load(self, img):
        """Initiates the mask with an existing image."""
        tp = img.dtype
        if tp != np.uint8:
            max_val = np.max(img)
            self.__logger.warning("Input image is not of format uint8")
            if max_val != 0:
                img = self.value_max * img.astype('float64') / np.max(img)
            img = img.astype('uint8')
        self.img = img
        return
    
    def getCenter(self):
        return (self.centerx, self.centery)

    def setCenter(self, setCoords):
        self.centerx, self.centery = setCoords

    def moveCenter(self, move_v):
        self.centerx = self.centerx + move_v[0]
        self.centery = self.centery + move_v[1]
        
    def setAberrationFactors(self, aber_params_info):
        self.aber_params_info = aber_params_info
        
    def setRotationAngle(self, rotation_angle):
        self.angle_rotation = rotation_angle

    def setTiltAngle(self, tilt_angle):
        self.angle_tilt = tilt_angle * math.pi / 180
        
    def setRadius(self, radius):
        self.radius = radius
        
    def setFocal(self, focal):
        self.focal = focal
        
    def setSigma(self, sigma):
        self.sigma = sigma
    
    def setTilt(self, pixelsize=None):
        """Creates a tilt mask, blazed grating, for off-axis holography."""
        if pixelsize:
            self.pixelSize = pixelsize
        wavelength = self.wavelength * 10 ** -6  # conversion to mm
        mask = np.indices((self.height, self.width), dtype="float")[1, :, :]
        # Spatial frequency, round to avoid aliasing
        f_spat = np.round(wavelength / (self.pixelSize * np.sin(self.angle_tilt)))
        if np.absolute(f_spat) < 3:
            self.__logger.debug(f"Spatial frequency: {f_spat} pixels")
        period = 2 * math.pi / f_spat  # period
        mask *= period  # getting a mask that is time along x-axis with a certain period
        tilt = sg.sawtooth(mask) + 1  # creating the blazed grating
        tilt *= self.value_max / 2  # normalizing it to range of [0 value_max]
        tilt = np.round(tilt).astype(np.uint8)  # getting it in np.uint8 type
        self.img = tilt
        self.mask_type = MaskMode.Tilt

    def setAberrations(self):
        fTilt = self.aber_params_info["tilt"]
        fTip = self.aber_params_info["tip"]
        fDefoc = self.aber_params_info["defocus"]
        fSph = self.aber_params_info["spherical"]
        fVertComa = self.aber_params_info["verticalComa"]
        fHozComa = self.aber_params_info["horizontalComa"]
        fVertAst = self.aber_params_info["verticalAstigmatism"]
        fOblAst = self.aber_params_info["obliqueAstigmatism"]

        mask = np.fromfunction(lambda i, j: fTilt * 2 * np.sqrt(((i - self.centerx) / self.radius)**2 + ((j - self.centery) / self.radius)**2) * np.sin(np.arctan2(((j - self.centery) / self.radius), ((i - self.centerx) / self.radius))), (self.height, self.width), dtype="float")
        mask += np.fromfunction(lambda i, j: fTip * 2 * np.sqrt(((i - self.centerx) / self.radius)**2 + ((j - self.centery) / self.radius)**2) * np.cos(np.arctan2(((j - self.centery) / self.radius), ((i - self.centerx) / self.radius))), (self.height, self.width), dtype="float")
        mask += np.fromfunction(lambda i, j: fDefoc * np.sqrt(3) * (2 * (((i - self.centerx) / self.radius)**2 + ((j - self.centery) / self.radius)**2) - 1), (self.height, self.width), dtype="float")
        mask += np.fromfunction(lambda i, j: fSph * np.sqrt(5) * (6 * (((i - self.centerx) / self.radius)**2 + ((j - self.centery) / self.radius)**2)**4 - 6 * (((i - self.centerx) / self.radius)**2 + ((j - self.centery) / self.radius)**2) + 1), (self.height, self.width), dtype="float")
        mask += np.fromfunction(lambda i, j: fVertComa * np.sqrt(8) * np.sin(np.arctan2(((j - self.centery) / self.radius), ((i - self.centerx) / self.radius))) * (3 * (np.sqrt(((i - self.centerx) / self.radius)**2 + ((j - self.centery) / self.radius)**2))**3 - 2 * np.sqrt(((i - self.centerx) / self.radius)**2 + ((j - self.centery) / self.radius)**2)), (self.height, self.width), dtype="float")
        mask += np.fromfunction(lambda i, j: fHozComa * np.sqrt(8) * np.cos(np.arctan2(((j - self.centery) / self.radius), ((i - self.centerx) / self.radius))) * (3 * (np.sqrt(((i - self.centerx) / self.radius)**2 + ((j - self.centery) / self.radius)**2))**3 - 2 * np.sqrt(((i - self.centerx) / self.radius)**2 + ((j - self.centery) / self.radius)**2)), (self.height, self.width), dtype="float")
        mask += np.fromfunction(lambda i, j: fVertAst * np.sqrt(6) * np.cos(2 * np.arctan2(((j - self.centery) / self.radius), ((i - self.centerx) / self.radius))) * ((np.sqrt(((i - self.centerx) / self.radius)**2 + ((j - self.centery) / self.radius)**2))**2), (self.height, self.width), dtype="float")
        mask += np.fromfunction(lambda i, j: fOblAst * np.sqrt(6) * np.sin(2 * np.arctan2(((j - self.centery) / self.radius), ((i - self.centerx) / self.radius))) * ((np.sqrt(((i - self.centerx) / self.radius)**2 + ((j - self.centery) / self.radius)**2))**2), (self.height, self.width), dtype="float")

        mask %= 2 * math.pi
        self.img = mask
        self.pi2uint8()
        self.mask_type = MaskMode.Aber
        
    def loadMFA(self):
        if self.MFApath is not None:
            filename = (Path(self.MFApath).name).split('.')[:-1]
            filename = ''.join(filename)
            path = Path(self.MFApath).parent
            try:
                self.loadBMP(filename,path)
                self.mask_type = MaskMode.MFA
            except FileNotFoundError as e:
                self.__logger.error(f"Could not load MFA '{filename}' - got error: {e}")


    def setFresnelLens(self, pixelsize=None):
        if pixelsize:
            self.pixelSize = pixelsize
        focal = self.focal/10**3
        pp = self.pixelSize/10**3
        wavelength = self.wavelength/10**9
        R = self.radius
        
        PI = math.pi
    
        d = np.zeros((self.height, self.width), dtype=float)
        x = np.linspace((-self.centery + 1/2)*pp, (self.width - self.centery + 1/2)*pp, self.width, endpoint=False, dtype=float)
        y = np.linspace((-self.centerx + 1/2)*pp, (self.height - self.centerx + 1/2)*pp, self.height, endpoint=False)
    
        X, Y = np.meshgrid(x, y)
    
        wavefront = np.sqrt(focal**2 - (X**2 + Y**2)) - focal # surface equation
        d[X**2 + Y**2 < R**2] = np.abs(wavefront[X**2 + Y**2 < R**2]) + wavelength*1e-9 # distance to the slm plane z=0
        phase = -d*2*PI/wavelength
        self.img = phase%(2*PI) # 2*PI modulation at maximum wrap the phase image
        self.pi2uint8()
        self.mask_type = MaskMode.Lens

    def setBlack(self):
        self.img = np.zeros((self.height, self.width), dtype=np.uint8)
        self.mask_type = MaskMode.Black

    def setGauss(self):
        self.img = np.ones((self.height, self.width), dtype=np.uint8) * self.value_max // 2
        self.mask_type = MaskMode.Gauss

    def setDonut(self, rotation=True):
        """This function generates a donut mask, with the center defined in the
        mask object."""
        mask = np.zeros((self.height, self.width), dtype="float")
        x, y = np.ogrid[-self.centerx: self.height - self.centerx,
                        -self.centery: self.width - self.centery]
        theta = np.arctan2(x, y)

        mask = theta % (2 * np.pi)
        if rotation:
            mask = np.ones((self.height, self.width), dtype="float") * (2 * np.pi) - mask

        self.img = mask
        self.pi2uint8()
        self.mask_type = MaskMode.Donut
        print(self.getCenter())

    def setTophat(self):
        """This function generates a tophat mask with a mid-radius defined by
        sigma, and with the center defined in the mask object."""
        mask = np.zeros((self.height, self.width), dtype="float")
        x, y = np.ogrid[-self.centerx: self.height - self.centerx,
                        -self.centery: self.width - self.centery]
        d = x ** 2 + y ** 2

        mid_radius = self.sigma * np.sqrt(
            2 * np.log(2 / (1 + np.exp(-self.radius ** 2 / (2 * self.sigma ** 2))))
        )
        tophat_bool = (d > mid_radius ** 2)
        mask[tophat_bool] = np.pi

        self.img = mask
        self.pi2uint8()
        self.mask_type = MaskMode.Tophat
        
    def setHalf(self):
        """Sets the current masks to half masks, with the same center,
        for accurate center position determination."""
        mask = np.zeros((self.height, self.width), dtype="float")
        x, y = np.ogrid[-self.centerx: self.height - self.centerx,
                        -self.centery: self.width - self.centery]
        theta = np.arctan2(x, y) + self.angle_rotation

        half_bool = (abs(theta) < np.pi / 2)
        mask[half_bool] = np.pi

        self.img = mask
        self.pi2uint8()
        self.mask_type = MaskMode.Half

    def setQuad(self):
        """Transforms the current mask in a quadrant pattern mask for testing
        aberrations."""
        mask = np.zeros((self.height, self.width), dtype="float")
        x, y = np.ogrid[-self.centerx: self.height - self.centerx,
                        -self.centery: self.width - self.centery]
        theta = np.arctan2(x, y) + self.angle_rotation

        quad_bool = (theta < np.pi) * (theta > np.pi / 2) + (theta < 0) * (theta > -np.pi / 2)
        mask[quad_bool] = np.pi

        self.img = mask
        self.pi2uint8()
        self.mask_type = MaskMode.Quad

    def setHex(self):
        """Transforms the current mask in a hex pattern mask for testing
        aberrations."""
        mask = np.zeros((self.height, self.width), dtype="float")
        x, y = np.ogrid[-self.centerx: self.height - self.centerx,
                        -self.centery: self.width - self.centery]
        theta = np.arctan2(x, y) + self.angle_rotation

        hex_bool = ((theta < np.pi / 3) * (theta > 0) +
                    (theta > -2 * np.pi / 3) * (theta < -np.pi / 3) +
                    (theta > 2 * np.pi / 3) * (theta < np.pi))
        mask[hex_bool] = np.pi

        self.img = mask
        self.pi2uint8()
        self.mask_type = MaskMode.Hex

    def setSplit(self):
        """Transforms the current mask in a split bullseye pattern mask for
        testing aberrations."""
        mask = np.zeros((self.height, self.width), dtype="float")
        mask1 = np.zeros((self.height, self.width), dtype="float")
        mask2 = np.zeros((self.height, self.width), dtype="float")
        x, y = np.ogrid[-self.centerx: self.height - self.centerx,
                        -self.centery: self.width - self.centery]
        theta = np.arctan2(x, y) + self.angle_rotation

        radius_factor = 0.6
        mid_radius = radius_factor * self.radius
        d = x ** 2 + y ** 2
        ring = (d > mid_radius ** 2)
        mask1[ring] = np.pi
        midLine = (abs(theta) < np.pi / 2)
        mask2[midLine] = np.pi
        mask = (mask1 + mask2) % (2 * np.pi)

        self.img = mask
        self.pi2uint8()
        self.mask_type = MaskMode.Split
        
    def updateImage(self):
        if self.mask_type == MaskMode.Black:
            self.setBlack()
        elif self.mask_type == MaskMode.Gauss:
            self.setGauss()
        elif self.mask_type == MaskMode.Donut:
            self.setDonut()
        elif self.mask_type == MaskMode.Tophat:
            self.setTophat()
        elif self.mask_type == MaskMode.Half:
            self.setHalf()
        elif self.mask_type == MaskMode.Quad:
            self.setQuad()
        elif self.mask_type == MaskMode.Hex:
            self.setHex()
        elif self.mask_type == MaskMode.Split:
            self.setSplit()
        elif self.mask_type == MaskMode.Tilt:
            self.setTilt()
        elif self.mask_type == MaskMode.Aber:
            self.setAberrations()
        elif self.mask_type == MaskMode.Lens:
            self.setFresnelLens()
        elif self.mask_type == MaskMode.MFA:
            self.loadMFA()
            
    def setCircular(self):
        """This method sets to 0 all the values within Mask except the ones
        included in a circle centered in (centerx,centery) with a radius r"""
        x, y = np.ogrid[-self.centerx: self.height - self.centerx,
                        -self.centery: self.width - self.centery]
        mask_bin = x * x + y * y <= self.radius * self.radius
        result = np.zeros((self.height, self.width))
        result[mask_bin] = self.img[mask_bin]
        self.img = result
        
    def __add__(self, other):
        if self.height == other.height and self.width == other.width:
            out = Mask(self.height, self.width, self.wavelength)
            out.load(((self.image().astype("float32") + other.image().astype("float32")) 
                      % (self.value_max + 1)).astype(np.uint8)) # if type is uint8 the operator __add__ wraps the values around 256
            return out
        else:
            raise TypeError("Cannot add two masks with different shapes")
        
    def image(self):
        return self.img
        
class MaskMode(enum.Enum):
    Donut = 1
    Tophat = 2
    Black = 3
    Gauss = 4
    Half = 5
    Hex = 6
    Quad = 7
    Split = 8
    Tilt = 9
    Aber = 10
    Lens = 11
    MFA = 12

class Direction(enum.Enum):
    Up = 1
    Down = 2
    Left = 3
    Right = 4
            
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