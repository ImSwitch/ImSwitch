import numpy as np

from imswitch.imcommon.model import initLogger


class ReconObj:
    def __init__(self, name, scanParDict, r_l_text, u_d_text, b_f_text,
                 timepoints_text, p_text, n_text, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__logger = initLogger(self, instanceName=name)

        self.r_l_text = r_l_text
        self.u_d_text = u_d_text
        self.b_f_text = b_f_text
        self.timepoints_text = timepoints_text
        self.p_text = p_text
        self.n_tetx = n_text

        self.name = name
        self.coeffs = None
        self.reconstructed = None
        self.scanParDict = scanParDict.copy()

        self.dispLevels = None

    def setDispLevels(self, levels):
        self.dispLevels = levels

    def getDispLevels(self):
        return self.dispLevels

    def getReconstruction(self):
        return self.reconstructed

    def getCoeffs(self):
        return self.coeffs

    def getScanParams(self):
        return self.scanParDict

    def addCoeffsTP(self, inCoeffs):
        """ Adds a set of coefficients to the existing set of coefficients. """
        if self.coeffs is None:
            # self.__logger.debug(f'In if, shape is: {np.shape(inCoeffs)}')
            # self.__logger.debug(f'Coeffs are: {inCoeffs}')
            self.coeffs = np.array([inCoeffs])
        else:
            # self.__logger.debug(f'In else, shape self.data is: {np.shape(inCoeffs)}')
            # self.__logger.debug(f'In else, shape inCoeffs is: {np.shape(inCoeffs)}')
            self.__logger.debug(f'Max in coeffs: {inCoeffs.max()}')
            inCoeffs = np.expand_dims(inCoeffs, 0)
            self.coeffs = np.vstack((self.coeffs, inCoeffs))

    def updateScanParams(self, scanParDict):
        self.scanParDict = scanParDict

    def updateImages(self):
        """Updates the variable self.reconstructed which contains the final
        reconstructed and reassigned images of ALL the bases given to the
        reconstructor"""
        if self.coeffs is not None:
            datasets = np.shape(self.coeffs)[0]
            bases = np.shape(self.coeffs)[1]
            self.reconstructed = np.array([
                [self.coeffsToImage(self.coeffs[ds][b], self.scanParDict) for b in range(0, bases)]
                for ds in range(0, datasets)
            ])
            self.__logger.debug(f'Shape of reconstructed: {np.shape(self.reconstructed)}')
        else:
            self.__logger.error('Cannot update images without coefficients')
    
    def updateReconstructed(self,new_img):
        self.reconstructed = new_img

    def addGridOfCoeffs(self, im, coeffs, t, s, r0, c0, pr, pc):
        # self.__logger.debug(f'Timepoint: {t}')
        # self.__logger.debug(f'shape if im: {im.shape}')
        # self.__logger.debug(f'shape if coeffts[i]: {coeffs.shape}')
        # self.__logger.debug(f'r0: {r0}')
        # self.__logger.debug(f'c0: {c0}')
        # self.__logger.debug(f'pr: {pr}')
        # self.__logger.debug(f'pc: {pc}')
        im[t, s, r0::pr, c0::pc] = coeffs

    def coeffsToImage(self, coeffs, scanParDict):
        """Takes the 4d matrix of coefficients from the signal extraction and
        reshapes into images according to given parameters"""
        frames = np.shape(coeffs)[0]
        dim0Side = int(scanParDict['steps'][0])
        dim1Side = int(scanParDict['steps'][1])
        dim2Side = int(scanParDict['steps'][2])
        dim3Side = int(scanParDict['steps'][3])  # Always timepoints
        if not frames == dim0Side * dim1Side * dim2Side * dim3Side:
            self.__logger.error('Wrong dimensional data')
            pass

        timepoints = int(
            scanParDict['steps'][scanParDict['dimensions'].index(self.timepoints_text)]
        )
        slices = int(scanParDict['steps'][scanParDict['dimensions'].index(self.b_f_text)])
        sqRows = int(scanParDict['steps'][scanParDict['dimensions'].index(self.u_d_text)])
        sqCols = int(scanParDict['steps'][scanParDict['dimensions'].index(self.r_l_text)])

        im = np.zeros(
            [timepoints, slices, sqRows * np.shape(coeffs)[1], sqCols * np.shape(coeffs)[2]],
            dtype=np.float32
        )
        for i in np.arange(np.shape(coeffs)[0]):

            t = int(np.floor(i / (frames / dim3Side)))

            slow = int(np.mod(i, frames / timepoints) / (dim0Side * dim1Side))
            mid = int(np.mod(i, dim0Side * dim1Side) / dim0Side)
            fast = np.mod(i, dim0Side)

            if not scanParDict['unidirectional']:
                oddMidStep = np.mod(mid, 2)
                fast = (1 - oddMidStep) * fast + oddMidStep * (dim1Side - 1 - fast)

            neg = (int(scanParDict['directions'][0] == 'neg'),
                   int(scanParDict['directions'][1] == 'neg'),
                   int(scanParDict['directions'][2] == 'neg'))

            """Adjust for positive or negative direction"""
            fast = (1 - neg[0]) * fast + neg[0] * (dim0Side - 1 - fast)
            mid = (1 - neg[1]) * mid + neg[1] * (dim1Side - 1 - mid)
            slow = (1 - neg[2]) * slow + neg[2] * (dim2Side - 1 - slow)

            """Place dimensions in correct row/col/slice"""
            if scanParDict['dimensions'][0] == self.r_l_text:
                if scanParDict['dimensions'][1] == self.u_d_text:
                    c = fast
                    pc = dim0Side
                    r = mid
                    pr = dim1Side
                    s = slow
                else:
                    c = fast
                    pc = dim0Side
                    r = slow
                    pr = dim2Side
                    s = mid
            elif scanParDict['dimensions'][0] == self.u_d_text:
                if scanParDict['dimensions'][1] == self.r_l_text:
                    c = mid
                    pc = dim1Side
                    r = fast
                    pr = dim0Side
                    s = slow
                else:
                    c = slow
                    pc = dim2Side
                    r = fast
                    pr = dim0Side
                    s = mid
            else:
                if scanParDict['dimensions'][1] == self.r_l_text:
                    c = mid
                    pc = dim1Side
                    r = slow
                    pr = dim2Side
                    s = fast
                else:
                    c = slow
                    pc = dim2Side
                    r = mid
                    pr = dim1Side
                    s = fast

            self.addGridOfCoeffs(im, coeffs[i], t, s, r, c, pr, pc)

        return im


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
