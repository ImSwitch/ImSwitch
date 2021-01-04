# -*- coding: utf-8 -*-
"""
Created on Wed Dec 16 16:37:00 2020

@author: jonatanalvelid
"""

import os
import glob
import enum
import math

from lantz import Q_
from PIL import Image
import numpy as np

from scipy import signal as sg

class SLMHelper:
    def __init__(self, slmInfo, slm, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__slm = slm
        self.__slmInfo = slmInfo
        self.__wavelength = self.__slmInfo.wavelength
        self.__pixelsize = self.__slmInfo.pixelsize
        self.__slmSize = (self.__slmInfo.width, self.__slmInfo.height)
        self.__correctionPatternsDir = self.__slmInfo.correctionPatternsDir
        #print(self.__slmSize)
        self.__maskLeft = Mask(self.__slmSize[1], int(self.__slmSize[0]/2), self.__wavelength)
        self.__maskRight = Mask(self.__slmSize[1], int(self.__slmSize[0]/2), self.__wavelength)
        self.__masks = [self.__maskLeft, self.__maskRight]

        self.setCorrectionMask()
        self.setTiltMask()

        self.__masksTilt = [self.__maskTiltLeft, self.__maskTiltRight]

        self.updateSLMDisplay()

    def setMask(self, mask, angle, maskMode):
        if maskMode == maskMode.Donut:
            self.__masks[mask].setDonut()
            print(f'Set {mask} phase mask to a Donut.')
        elif maskMode == maskMode.Tophat:
            self.__masks[mask].setTophat()
            print(f'Set {mask} phase mask to a Tophat.')
        elif maskMode == maskMode.Half:
            self.__masks[mask].setHalf(angle)
            #print(f'Set {mask} phase mask to half pattern, rotated {angle} rad.')
        elif maskMode == maskMode.Gauss:
            self.__masks[mask].setGauss()
            #print(f'Set {mask} phase mask to a Gaussian.')
        elif maskMode == maskMode.Hex:
            self.__masks[mask].setHex(angle)
            #print(f'Set {mask} phase mask to hex pattern, rotated {angle} rad.')
        elif maskMode == maskMode.Quad:
            self.__masks[mask].setQuad(angle)
            #print(f'Set {mask} phase mask to quad pattern, rotated {angle} rad.')
        elif maskMode == maskMode.Split:
            self.__masks[mask].setSplit(angle)
            #print(f'Set {mask} phase mask to split pattern, rotated {angle} rad.')
        elif maskMode == maskMode.Black:
            self.__masks[mask].setBlack()
            #print(f'Set {mask} phase mask to black.')
        self.updateSLMDisplay()
        return self.maskDouble.image()

    def moveMask(self, mask, direction, amount):
        if direction == direction.Up:
            move_v = np.array([-1,0])*amount
        elif direction == direction.Down:
            move_v = np.array([1,0])*amount
        elif direction == direction.Left:
            move_v = np.array([0,-1])*amount
        elif direction == direction.Right:
            move_v = np.array([0,1])*amount

        self.__masks[mask].moveCenter(move_v)
        self.__masksTilt[mask].moveCenter(move_v)
        self.updateSLMDisplay()
        return self.maskDouble.image()

    def setAberrations(self, mask):
        print(f'Set aberrations on {mask} phase mask.')

    def setCorrectionMask(self):
        # Add correction mask with correction pattern
        self.__maskCorrection = Mask(self.__slmSize[1], int(self.__slmSize[0]), self.__wavelength)
        bmpsCorrection = glob.glob(self.__correctionPatternsDir + "\*.bmp")
        wavelengthCorrection = [int(x[-9: -6]) for x in bmpsCorrection]
        # Find the closest correction pattern within the list of patterns available
        wavelengthCorrectionLoad = min(wavelengthCorrection, key=lambda x: abs(x - self.__wavelength))
        self.__maskCorrection.loadBMP("CAL_LSH0701153_" + str(wavelengthCorrectionLoad) + "nm", self.__correctionPatternsDir)

    def setTiltMask(self):
        # Add blazed grating tilting mask
        angle = 0.15  # read this from parameter tree later
        self.__maskTiltLeft = Mask(self.__slmSize[1], int(self.__slmSize[0]/2), self.__wavelength)
        self.__maskTiltLeft.setTilt(angle, self.__pixelsize)
        self.__maskTiltRight = Mask(self.__slmSize[1], int(self.__slmSize[0]/2), self.__wavelength)
        self.__maskTiltRight.setTilt(-angle, self.__pixelsize)
        
    def updateSLMDisplay(self):
        """Update the SLM monitor with the left and right mask, with correction masks added on."""
        self.maskDouble = self.__masks[0].concat(self.__masks[1])
        self.maskTilt = self.__masksTilt[0].concat(self.__masksTilt[1])
        #self.maskCombined = self.maskDouble + self.__maskCorrection + self.maskTilt
        self.maskCombined = self.maskDouble + self.maskTilt
        self.__slm.updateArray(self.maskCombined)


class Mask(object):
    """Class creating a mask to be displayed by the SLM."""
    def __init__(self, height: int, width: int, wavelength: int):
        """initiates the mask as an empty array
        n,m corresponds to the width,height of the created image
        wavelength is the illumination wavelength in nm"""
        self.img = np.zeros((height, width), dtype=np.uint8)
        self.height = height
        self.width = width
        self.value_max = 255
        self.centery = self.width // 2
        self.centerx = self.height // 2
        self.radius = 100
        self.wavelength = wavelength
        self.mask_type = MaskMode.Black
        self.angle_rotation = 0
        self.angle_tilt = 0
        if wavelength == 561:
            self.value_max = 148
        elif wavelength == 491:
            self.value_max = 129
        elif wavelength < 780 and wavelength > 800:
            # Here we infer the value of the maximum with a linear approximation from the ones provided by the manufacturer
            # Better ask them in case you need another wavelength
            self.value_max = int(wavelength * 0.45 - 105)
            print("Caution: a linear approximation has been made")

    def concat(self, maskOther):
        for mask in [self, maskOther]:
            mask.updateImage()
            mask.setCircular()
        maskCombined = Mask(self.height, self.width*2, self.wavelength)
        imgCombined = np.concatenate((self.img, maskOther.img), axis=1)
        maskCombined.loadArray(imgCombined)
        return maskCombined

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
        """Method converting a phase image (values from 0 to 2Pi) into a uint8 image"""
        print(np.max(np.max(self.img)))
        self.img *= self.value_max / (2 * math.pi)
        self.img = np.round(self.img).astype(np.uint8)
        print(np.max(np.max(self.img)))

    def load(self, img):
        """Initiates the mask with an existing image."""
        tp = img.dtype
        if tp != np.uint8:
            max_val = np.max(img)
            print("input image is not of format uint8")
            if max_val != 0:
                img = self.value_max * img.astype('float64') / np.max(img)
            img = img.astype('uint8')
        self.img = img
        return

    def setCircular(self):
        """This method sets to 0 all the values within Mask except the ones included
        in a circle centered in (x,y) with a radius r"""
        #self.centerx = np.max(x, self.height // 2)
        #self.centery = np.max(y, self.width // 2)
        x, y = np.ogrid[-self.centerx: self.height - self.centerx, -self.centery: self.width - self.centery]
        mask_bin = x * x + y * y <= self.radius * self.radius
        result = np.zeros((self.height, self.width))
        result[mask_bin] = self.img[mask_bin]
        self.img = result

    def setTilt(self, angle, pixelsize):
        """Creates a tilt mask, blazed grating, for off-axis holography."""
        """GO BACK AND CHECK HOW THIS WORKS LATER, BUT THE CALCULATIONS DOES NOT SEEM TO MAKE ANY SENSE"""
        # Necessary inversion because going through 4f-system (for right mask)
        #angle = -1 * angle  # angle in degrees
        self.angle_tilt = angle
        self.pixelsize = pixelsize
        angle *= math.pi / 180  # conversion to radians, JA comment: but it is already in radians no?
        wavelength = self.wavelength * 10**-6  # conversion to mm
        mask = np.indices((self.height, self.width), dtype="float")[1, :, :]
        # Round spatial frequency to avoid aliasing
        #d_spat = wavelength / np.sin(angle)
        #f_spat = 1 / d_spat
        #f_spat_px = round(f_spat / pixelsize)
        #np.round(wavelength / (pixelsize * np.sin(angle)))
        f_spat = np.round(wavelength / (pixelsize * np.sin(angle)))
        #f_spat = 10
        #if np.absolute(f_spat) < 3:
        print("spatial frequency:", f_spat, "pixels")
        period = 2 * math.pi / f_spat  # period
        mask *= period  # getting a mask that is time along x-axis with a certain period
        tilt = sg.sawtooth(mask) + 1  # creating the blazed grating
        tilt *= self.value_max / 2  # normalizing it to range of [0 value_max]
        tilt = np.round(tilt).astype(np.uint8)  # getting it in np.uint8 type
        self.img = tilt
        self.mask_type = MaskMode.Tilt

    def setCenter(self, setCoords):
        self.centerx, self.centery = setCoords

    def moveCenter(self, move_v):
        self.centerx = self.centerx + move_v[0]
        self.centery = self.centery + move_v[1]

    def setBlack(self):
        self.img = np.zeros((self.height, self.width), dtype=np.uint8)
        self.mask_type = MaskMode.Black

    def setGauss(self):
        self.img = np.ones((self.height, self.width), dtype=np.uint8) * self.value_max // 2
        self.mask_type = MaskMode.Gauss

    def setDonut(self, rotation=True):
        """This function generates a donut mask, with the center defined in the mask object."""
        mask = np.zeros((self.height, self.width), dtype="float")
        x, y = np.ogrid[-self.centerx: self.height - self.centerx, -self.centery: self.width - self.centery]
        theta = np.arctan2(x, y)

        mask = theta % (2 * np.pi)
        if rotation:
            mask2 = np.ones((self.height, self.width), dtype="float") * (2 * np.pi)
            mask = mask2 - mask

        self.img = mask
        self.pi2uint8()
        self.mask_type = MaskMode.Donut

    def setTophat(self, sigma=0.5):
        """This function generates a tophat mask with a mid-radius defined by sigma, and with the center defined in the mask object."""
        mask = np.zeros((self.height, self.width), dtype="float")
        x, y = np.ogrid[-self.centerx: self.height - self.centerx, -self.centery: self.width - self.centery]

        mid_radius = sigma * np.sqrt(2 * np.log(2 / (1 + np.exp(-self.radius**2 / (2 * sigma**2)))))
        y, x = np.ogrid[(-sizex // 2 - u): (sizex // 2 - u), (-sizey // 2 - v): (sizey // 2 - v)]
        d2 = x**2 + y**2
        tophat_bool = (d2 > mid_radius**2)
        mask[tophat_bool] = np.pi

        self.img = mask
        self.pi2uint8()   
        self.mask_type = MaskMode.Tophat  

    def setHalf(self, angle):
        """Sets the current masks to half masks, with the same center,
        for accurate center position determination."""
        mask = np.zeros((self.height, self.width), dtype="float")
        x, y = np.ogrid[-self.centerx: self.height - self.centerx, -self.centery: self.width - self.centery]
        theta = np.arctan2(x, y) + angle

        half_bool = (abs(theta) < np.pi / 2)
        mask[half_bool] = np.pi

        self.img = mask
        self.pi2uint8()
        self.mask_type = MaskMode.Half
        self.angle_rotation = angle

    def setQuad(self, angle):
        """Transforms the current mask in a quadrant pattern mask for testing
        aberrations."""
        mask = np.zeros((self.height, self.width), dtype="float")
        x, y = np.ogrid[-self.centerx: self.height - self.centerx, -self.centery: self.width - self.centery]
        theta = np.arctan2(x, y) + angle

        quad_bool = (theta < np.pi)*(theta > np.pi / 2) + (theta < 0 )*(theta > -np.pi / 2)
        mask[quad_bool] = np.pi

        self.img = mask
        self.pi2uint8()
        self.mask_type = MaskMode.Quad
        self.angle_rotation = angle

    def setHex(self, angle):
        """Transforms the current mask in a hex pattern mask for testing
        aberrations."""
        mask = np.zeros((self.height, self.width), dtype="float")
        x, y = np.ogrid[-self.centerx: self.height - self.centerx, -self.centery: self.width - self.centery]
        theta = np.arctan2(x, y) + angle

        hex_bool = (theta < np.pi / 3)*(theta > 0) + (theta > -2 * np.pi / 3)*(theta < -np.pi / 3) + (theta > 2 * np.pi / 3)*(theta < np.pi)
        mask[hex_bool] = np.pi

        self.img = mask
        self.pi2uint8()
        self.mask_type = MaskMode.Hex
        self.angle_rotation = angle

    def setSplit(self, angle):
        """Transforms the current mask in a split bullseye pattern mask for testing
        aberrations."""
        mask = np.zeros((self.height, self.width), dtype="float")
        mask1 = np.zeros((self.height, self.width), dtype="float")
        mask2 = np.zeros((self.height, self.width), dtype="float")
        x, y = np.ogrid[-self.centerx: self.height - self.centerx, -self.centery: self.width - self.centery]
        theta = np.arctan2(x, y) + angle

        radius_factor = 0.6
        mid_radius = radius_factor * self.radius
        d = x**2 + y**2
        ring = (d > mid_radius**2)
        mask1[ring] = np.pi
        midLine = (abs(theta) < np.pi / 2)
        mask2[midLine] = np.pi
        mask = (mask1 + mask2) % (2 * np.pi)

        self.img = mask
        self.pi2uint8()
        self.mask_type = MaskMode.Split
        self.angle_rotation = angle

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
            self.setHalf(self.angle_rotation)
        elif self.mask_type == MaskMode.Quad:
            self.setQuad(self.angle_rotation)
        elif self.mask_type == MaskMode.Hex:
            self.setHex(self.angle_rotation)
        elif self.mask_type == MaskMode.Split:
            self.setSplit(self.angle_rotation)
        elif self.mask_type == MaskMode.Tilt:
            print('SetTilt started')
            self.setTilt(self.angle_tilt, self.pixelsize)
            print('SetTilt finished')

    def __str__(self):
        plt.figure()
        plt.imshow(self.img)
        return "image of the mask"

    def __add__(self, other):
        if self.height == other.height and self.width == other.width:
            out = Mask(self.height, self.width, self.wavelength)
            out.load(((self.image() + other.image()) % (self.value_max + 1)).astype(np.uint8))
            return out
        else:
            raise TypeError("Cannot add two masks with different shapes")


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


class Direction(enum.Enum):
    Up = 1
    Down = 2
    Left = 3
    Right = 4


class MaskChoice(enum.Enum):
    Left = 0
    Right = 1