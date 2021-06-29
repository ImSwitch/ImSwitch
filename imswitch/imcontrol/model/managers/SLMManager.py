import os
import glob
import enum
import math

from lantz import Q_
from PIL import Image
import numpy as np

from scipy import signal as sg

class SLMManager:
    def __init__(self, slmInfo, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if slmInfo is None:
            return

        self.__slm = getSLMObj(slmInfo.monitorIdx)
        self.__slmInfo = slmInfo
        self.__wavelength = self.__slmInfo.wavelength
        self.__pixelsize = self.__slmInfo.pixelSize
        self.__angleMount = self.__slmInfo.angleMount
        self.__slmSize = (self.__slmInfo.width, self.__slmInfo.height)
        self.__correctionPatternsDir = self.__slmInfo.correctionPatternsDir
        #print(self.__slmSize)
        self.__maskLeft = Mask(self.__slmSize[1], int(self.__slmSize[0]/2), self.__wavelength)
        self.__maskRight = Mask(self.__slmSize[1], int(self.__slmSize[0]/2), self.__wavelength)
        self.__masks = [self.__maskLeft, self.__maskRight]

        self.initCorrectionMask()
        self.initTiltMask()
        self.initAberrationMask()

        self.__masksAber = [self.__maskAberLeft, self.__maskAberRight]
        self.__masksTilt = [self.__maskTiltLeft, self.__maskTiltRight]

        self.updateSLMDisplay()

    def saveState(self, state_general, state_pos, state_aber):
        self.state_general = state_general
        self.state_pos = state_pos
        self.state_aber = state_aber

    def initCorrectionMask(self):
        # Add correction mask with correction pattern
        self.__maskCorrection = Mask(self.__slmSize[1], int(self.__slmSize[0]), self.__wavelength)
        bmpsCorrection = glob.glob(self.__correctionPatternsDir + "\*.bmp")

        if len(bmpsCorrection) < 1:
            print('No BMP files found in correction patterns directory, cannot initialize'
                  ' correction mask.')
            return

        wavelengthCorrection = [int(x[-9: -6]) for x in bmpsCorrection]
        # Find the closest correction pattern within the list of patterns available
        wavelengthCorrectionLoad = min(wavelengthCorrection, key=lambda x: abs(x - self.__wavelength))
        self.__maskCorrection.loadBMP("CAL_LSH0701153_" + str(wavelengthCorrectionLoad) + "nm", self.__correctionPatternsDir)

    def initTiltMask(self):
        # Add blazed grating tilting mask
        self.__maskTiltLeft = Mask(self.__slmSize[1], int(self.__slmSize[0]/2), self.__wavelength)
        self.__maskTiltLeft.setTilt(self.__angleMount, self.__pixelsize)
        self.__maskTiltRight = Mask(self.__slmSize[1], int(self.__slmSize[0]/2), self.__wavelength)
        self.__maskTiltRight.setTilt(-self.__angleMount, self.__pixelsize)

    def initAberrationMask(self):
        # Add blazed grating tilting mask
        self.__maskAberLeft = Mask(self.__slmSize[1], int(self.__slmSize[0]/2), self.__wavelength)
        self.__maskAberLeft.setBlack()
        self.__maskAberRight = Mask(self.__slmSize[1], int(self.__slmSize[0]/2), self.__wavelength)
        self.__maskAberRight.setBlack()

    def setMask(self, mask, angle, sigma, maskMode):
        if self.__masks[mask].mask_type == MaskMode.Black and maskMode != MaskMode.Black:
            self.__masksTilt[mask].setTilt(self.__angleMount, self.__pixelsize)
        if maskMode == maskMode.Donut:
            self.__masks[mask].setDonut()
        elif maskMode == maskMode.Tophat:
            self.__masks[mask].setTophat(sigma)
        elif maskMode == maskMode.Half:
            self.__masks[mask].setHalf(angle)
        elif maskMode == maskMode.Gauss:
            self.__masks[mask].setGauss()
        elif maskMode == maskMode.Hex:
            self.__masks[mask].setHex(angle)
        elif maskMode == maskMode.Quad:
            self.__masks[mask].setQuad(angle)
        elif maskMode == maskMode.Split:
            self.__masks[mask].setSplit(angle)
        elif maskMode == maskMode.Black:
            self.__masks[mask].setBlack()
            self.__masksTilt[mask].setBlack()

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
        self.__masksAber[mask].moveCenter(move_v)

    def setAberrations(self, aber_info):
        dAberFactors = aber_info["left"]
        tAberFactors = aber_info["right"]
        self.__masksAber[0].setAberrations(dAberFactors)
        self.__masksAber[1].setAberrations(tAberFactors)
        #print(f'Set aberrations on both phase mask.')

    def updateSLMDisplay(self):
        """Update the SLM monitor with the left and right mask, with correction masks added on."""
        self.maskDouble = self.__masks[0].concat(self.__masks[1])
        self.maskTilt = self.__masksTilt[0].concat(self.__masksTilt[1])
        self.maskAber = self.__masksAber[0].concat(self.__masksAber[1])
        self.maskCombined = self.maskDouble + self.maskAber + self.maskTilt + self.__maskCorrection
        self.__slm.updateArray(self.maskCombined)

    def getCenters(self):
        centerCoords = {"left": self.__masks[0].getCenter(),
                        "right": self.__masks[1].getCenter()}
        return centerCoords
    
    def setCenters(self, centerCoords):
        for idx, (mask, masktilt, maskaber) in enumerate(zip(self.__masks, self.__masksTilt, self.__masksAber)):
            if idx == 0:
                center = (centerCoords["left"]["centerx"],centerCoords["left"]["centery"])
            elif idx == 1:
                center = (centerCoords["right"]["centerx"],centerCoords["right"]["centery"])
            mask.setCenter(center)
            masktilt.setCenter(center)
            maskaber.setCenter(center)

    def setGeneral(self, general_info):
        radius = general_info["radius"]
        sigma = general_info["sigma"]
        self.setRadius(radius)
        self.setSigma(sigma)

    def setRadius(self, radius):
        for mask, masktilt, maskaber in zip(self.__masks, self.__masksTilt, self.__masksAber):
            mask.setRadius(radius)
            masktilt.setRadius(radius)
            maskaber.setRadius(radius)

    def setSigma(self, sigma):
        for mask in self.__masks:
            mask.setSigma(sigma)

    def update(self):
        self.updateSLMDisplay()
        returnmask = self.maskDouble + self.maskAber
        return returnmask.image()


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
        self.centerx = self.height // 2
        self.centery = self.width // 2
        self.radius = 100
        self.sigma = 35
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
        #print(np.max(np.max(self.img)))
        self.img *= self.value_max / (2 * math.pi)
        self.img = np.round(self.img).astype(np.uint8)
        #print(np.max(np.max(self.img)))

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
        self.pixelSize = pixelsize
        angle *= math.pi / 180  # conversion to radians, JA comment: but it is already in radians no?
        wavelength = self.wavelength * 10**-6  # conversion to mm
        mask = np.indices((self.height, self.width), dtype="float")[1, :, :]
        #d_spat = wavelength / np.sin(angle)
        #f_spat = 1 / d_spat
        #f_spat_px = round(f_spat / pixelsize)
        #np.round(wavelength / (pixelsize * np.sin(angle)))
        # Round spatial frequency to avoid aliasing
        f_spat = np.round(wavelength / (pixelsize * np.sin(angle)))
        #f_spat = 10
        if np.absolute(f_spat) < 3:
            print("spatial frequency:", f_spat, "pixels")
        period = 2 * math.pi / f_spat  # period
        mask *= period  # getting a mask that is time along x-axis with a certain period
        tilt = sg.sawtooth(mask) + 1  # creating the blazed grating
        tilt *= self.value_max / 2  # normalizing it to range of [0 value_max]
        tilt = np.round(tilt).astype(np.uint8)  # getting it in np.uint8 type
        self.img = tilt
        self.mask_type = MaskMode.Tilt

    def setAberrations(self, aber_params_info):
        self.aber_params_info = aber_params_info
        fTilt = aber_params_info["tilt"]
        fTip = aber_params_info["tip"]
        fDefoc = aber_params_info["defocus"]
        fSph = aber_params_info["spherical"]
        fVertComa = aber_params_info["verticalComa"]
        fHozComa = aber_params_info["horizontalComa"]
        fVertAst = aber_params_info["verticalAstigmatism"]
        fOblAst = aber_params_info["obliqueAstigmatism"]
        
        tiltMask = np.fromfunction(lambda i, j: fTilt * 2 * np.sqrt(((i - self.centerx) / self.radius)**2 + ((j - self.centery) / self.radius)**2) * np.sin(np.arctan2(((j - self.centery) / self.radius), ((i - self.centerx) / self.radius))), (self.height, self.width), dtype="float")
        tipMask = np.fromfunction(lambda i, j: fTip * 2 * np.sqrt(((i - self.centerx) / self.radius)**2 + ((j - self.centery) / self.radius)**2) * np.cos(np.arctan2(((j - self.centery) / self.radius), ((i - self.centerx) / self.radius))), (self.height, self.width), dtype="float")
        defocMask = np.fromfunction(lambda i, j: fDefoc * np.sqrt(3) * (2 * (((i - self.centerx) / self.radius)**2 + ((j - self.centery) / self.radius)**2) - 1), (self.height, self.width), dtype="float")
        sphMask = np.fromfunction(lambda i, j: fSph * np.sqrt(5) * (6 * (((i - self.centerx) / self.radius)**2 + ((j - self.centery) / self.radius)**2)**4 - 6 * (((i - self.centerx) / self.radius)**2 + ((j - self.centery) / self.radius)**2) + 1), (self.height, self.width), dtype="float")
        vertComaMask = np.fromfunction(lambda i, j: fVertComa * np.sqrt(8) * np.sin(np.arctan2(((j - self.centery) / self.radius), ((i - self.centerx) / self.radius))) * (3 * (np.sqrt(((i - self.centerx) / self.radius)**2 + ((j - self.centery) / self.radius)**2))**3 - 2 * np.sqrt(((i - self.centerx) / self.radius)**2 + ((j - self.centery) / self.radius)**2)), (self.height, self.width), dtype="float")
        hozComaMask = np.fromfunction(lambda i, j: fHozComa * np.sqrt(8) * np.cos(np.arctan2(((j - self.centery) / self.radius), ((i - self.centerx) / self.radius))) * (3 * (np.sqrt(((i - self.centerx) / self.radius)**2 + ((j - self.centery) / self.radius)**2))**3 - 2 * np.sqrt(((i - self.centerx) / self.radius)**2 + ((j - self.centery) / self.radius)**2)), (self.height, self.width), dtype="float")
        vertAstMask = np.fromfunction(lambda i, j: fVertAst * np.sqrt(6) * np.cos(2 * np.arctan2(((j - self.centery) / self.radius), ((i - self.centerx) / self.radius))) * ((np.sqrt(((i - self.centerx) / self.radius)**2 + ((j - self.centery) / self.radius)**2))**2), (self.height, self.width), dtype="float")
        oblAstMask = np.fromfunction(lambda i, j: fOblAst * np.sqrt(6) * np.sin(2 * np.arctan2(((j - self.centery) / self.radius), ((i - self.centerx) / self.radius))) * ((np.sqrt(((i - self.centerx) / self.radius)**2 + ((j - self.centery) / self.radius)**2))**2), (self.height, self.width), dtype="float")

        mask = tiltMask + tipMask + defocMask + sphMask + vertComaMask + hozComaMask + vertAstMask + oblAstMask + math.pi
        mask %= 2 * math.pi
        self.img = mask
        self.pi2uint8()
        self.mask_type = MaskMode.Aber

    def getCenter(self):
        return (self.centerx, self.centery)

    def setCenter(self, setCoords):
        self.centerx, self.centery = setCoords

    def setRadius(self, radius):
        self.radius = radius

    def setSigma(self, sigma):
        self.sigma = sigma

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
            mask = np.ones((self.height, self.width), dtype="float") * (2 * np.pi) - mask

        self.img = mask
        self.pi2uint8()
        self.mask_type = MaskMode.Donut

    def setTophat(self, sigma=35):
        """This function generates a tophat mask with a mid-radius defined by sigma, and with the center defined in the mask object."""
        self.sigma = sigma
        mask = np.zeros((self.height, self.width), dtype="float")
        x, y = np.ogrid[-self.centerx: self.height - self.centerx, -self.centery: self.width - self.centery]
        d = x**2 + y**2

        mid_radius = sigma * np.sqrt(2 * np.log(2 / (1 + np.exp(-self.radius**2 / (2 * sigma**2)))))
        tophat_bool = (d > mid_radius**2)
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
            self.setTophat(self.sigma)
        elif self.mask_type == MaskMode.Half:
            self.setHalf(self.angle_rotation)
        elif self.mask_type == MaskMode.Quad:
            self.setQuad(self.angle_rotation)
        elif self.mask_type == MaskMode.Hex:
            self.setHex(self.angle_rotation)
        elif self.mask_type == MaskMode.Split:
            self.setSplit(self.angle_rotation)
        elif self.mask_type == MaskMode.Tilt:
            self.setTilt(self.angle_tilt, self.pixelSize)
        elif self.mask_type == MaskMode.Aber:
            self.setAberrations(self.aber_params_info)

    def __str__(self):
        return "image of the mask"

    def __add__(self, other):
        if self.height == other.height and self.width == other.width:
            out = Mask(self.height, self.width, self.wavelength)
            out.load(((self.image() + other.image()) % (self.value_max + 1)).astype(np.uint8))
            return out
        else:
            raise TypeError("Cannot add two masks with different shapes")


def getSLMObj(slmIdx):
    try:
        from ..interfaces.SLM import SLMdisplay
        print('Trying to display SLM in monitor', slmIdx)
        slm = SLMdisplay(slmIdx)
        return slm
    except OSError:
        print('Failed to load SLM')
    #    print('Initializing Mock SLM')
    #    from model.interfaces import MockSLM
    #    return MockSLM()


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


class Direction(enum.Enum):
    Up = 1
    Down = 2
    Left = 3
    Right = 4


class MaskChoice(enum.Enum):
    Left = 0
    Right = 1


# Copyright (C) 2020, 2021 TestaLab
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
