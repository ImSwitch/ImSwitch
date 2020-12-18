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
        self.__maskLeft = Mask(self.__slmSize[1],int(self.__slmSize[0]/2),self.__wavelength)
        self.__maskRight = Mask(self.__slmSize[1],int(self.__slmSize[0]/2),self.__wavelength)
        self.__masks = [self.__maskLeft, self.__maskRight]
        
        # Add correction mask with correction pattern
        self.__maskCorrection = Mask(self.__slmSize[1],int(self.__slmSize[0]),self.__wavelength)
        bmpsCorrection = glob.glob(self.__correctionPatternsDir + "\*.bmp")
        wavelengthCorrection = [int(x[-9: -6]) for x in bmpsCorrection]
        # Find the closest correction pattern within the list of patterns available
        wavelengthCorrectionLoad = min(wavelengthCorrection, key=lambda x: abs(x - self.__wavelength))
        self.__maskCorrection.loadBMP("CAL_LSH0701153_" + str(wavelengthCorrectionLoad) + "nm", self.__correctionPatternsDir)

        # Add blazed grating tilting mask
        angle = 0.15  # read this from parameter tree later
        maskTiltLeft = Mask(self.__slmSize[1],int(self.__slmSize[0]/2),self.__wavelength)
        maskTiltLeft.setTilt(angle, self.__pixelsize)
        maskTiltLeft.setCircular()
        maskTiltRight = Mask(self.__slmSize[1],int(self.__slmSize[0]/2),self.__wavelength)
        maskTiltRight.setTilt(-angle, self.__pixelsize)
        maskTiltRight.setCircular()
        self.__maskTilt = maskTiltLeft.concat(maskTiltRight)
        
        #print(self.__doubleMask)
        #print(np.shape(self.__doubleMask))
        self.updateSLMDisplay(self.__maskLeft, self.__maskRight)

    def setMask(self, mask, angle, maskMode):
        if maskMode == maskMode.Donut:
            print(f'Set {mask} phase mask to a Donut.')
        elif maskMode == maskMode.Tophat:
            print(f'Set {mask} phase mask to a Tophat.')
        elif maskMode == maskMode.Half:
            print(f'Set {mask} phase mask to half pattern, rotated {angle} rad.')
        elif maskMode == maskMode.Gauss:
            self.__masks[mask].setGauss()
            print(f'Set {mask} phase mask to a Gaussian.')
        elif maskMode == maskMode.Hex:
            print(f'Set {mask} phase mask to hex pattern, rotated {angle} rad.')
        elif maskMode == maskMode.Quad:
            print(f'Set {mask} phase mask to quad pattern, rotated {angle} rad.')
        elif maskMode == maskMode.Split:
            print(f'Set {mask} phase mask to split pattern, rotated {angle} rad.')
        elif maskMode == maskMode.Black:
            self.__masks[mask].setBlack()
            print(f'Set {mask} phase mask to black.')
        self.updateSLMDisplay(self.__maskLeft, self.__maskRight)
        return self.maskDouble.image()

    def setAberrations(self, mask):
        print(f'Set aberrations on {mask} phase mask.')
        
    def updateSLMDisplay(self, maskLeft, maskRight):
        """Update the SLM monitor with the supplied left and right mask.
        Note that the array is not the same size as the SLM resolution,
        the image will be deformed to fit the screen."""
        maskLeft.setCircular()
        maskRight.setCircular()
        self.maskDouble = maskLeft.concat(maskRight)
        maskCombined = self.maskDouble + self.__maskCorrection + self.__maskTilt
        self.__slm.updateArray(maskCombined)


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
        maskCombined = Mask(self.height, self.width*2, self.wavelength)
        imgCombined = np.concatenate((self.img, maskOther.img), axis=1)
        maskCombined.loadArray(imgCombined)
        return maskCombined

    def loadArray(self, mask):
        self.img = mask

    def __str__(self):
        plt.figure()
        plt.imshow(self.img)
        return "image of the mask"

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
        print("twoPiToUInt8 called")
        self.img *= self.value_max / (2 * math.pi)
        print("twoPiToUInt8 almost finished")
        self.img = np.round(self.img).astype(np.uint8)
        print("twoPiToUInt8 finished")

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

    def setCircular(self):#, x=-1, y=-1):
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
        # Necessary inversion because going through 4f-system (for right mask)
        #angle = -1 * angle  # angle in degrees
        angle *= math.pi / 180  # conversion in radians
        wavelength = self.wavelength * 10**-6  # conversion in mm
        mask = np.indices((self.height, self.width), dtype="float")[1, :, :]
        # Round spatial frequency to avoid aliasing
        f_spat = np.round(wavelength / (pixelsize * np.sin(angle)))
        #f_spat = 5
        if np.absolute(f_spat) < 3:
            print("spatial frequency:", f_spat, "pixels")
        period = 2 * math.pi / f_spat
        mask *= period
        tilt = sg.sawtooth(mask) + 1
        tilt *= self.value_max / 2
        tilt = np.round(tilt).astype(np.uint8)
        self.img = tilt    

    def setBlack(self):
        self.img = np.zeros((self.height, self.width), dtype=np.uint8)

    def setGauss(self):
        self.img = np.ones((self.height, self.width), dtype=np.uint8)

    def __add__(self, other):
        if self.height == other.height and self.width == other.width:
            out = Mask(self.height, self.width, self.wavelength)
            out.load(((self.image() + other.image()) % (self.value_max + 1)).astype(np.uint8))
            return out
        else:
            raise TypeError("Cannot add two arrays with different shapes")


class MaskMode(enum.Enum):
    Donut = 1
    Tophat = 2
    Black = 3
    Gauss = 4
    Half = 5
    Hex = 6
    Quad = 7
    Split = 8

    
class MaskChoice(enum.Enum):
    Left = 0
    Right = 1