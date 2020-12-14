import numpy as np


class ReconObj:
    def __init__(self, name, scanningParDict, r_l_text, u_d_text, b_f_text, timepoints_text, p_text, n_text, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.r_l_text = r_l_text
        self.u_d_text = u_d_text
        self.b_f_text = b_f_text
        self.timepoints_text = timepoints_text
        self.p_text = p_text
        self.n_tetx = n_text

        self.name = name
        self.coeffs = None
        self.reconstructed = None
        self.scanningParDict = scanningParDict.copy()

        self.disp_levels = None

    def setDispLevels(self, levels):
        self.disp_levels = levels

    def getDispLevels(self):
        return self.disp_levels

    def getReconstruction(self):
        return self.reconstructed

    def getCoeffs(self):
        return self.coeffs

    def addCoeffsTP(self, in_coeffs):
        if self.coeffs is None:
#            print('In if, shape is: ', np.shape(in_coeffs))
#            print('coeffs are: ', in_coeffs)
            self.coeffs = np.array([in_coeffs])
        else:
#            print('In else, shape self.data is: ', np.shape(in_coeffs))
#            print('In else, shape in_coeffs is: ', np.shape(in_coeffs))
            print('Max in coeffs = ', in_coeffs.max())
            in_coeffs = np.expand_dims(in_coeffs, 0)
            self.coeffs = np.vstack((self.coeffs, in_coeffs))

    def updateScanningPars(self, scanningParDict):
        self.scanningParDict = scanningParDict

    def update_images(self):
        """Updates the variable self.reconstructed which contains the final
        reconstructed and reassigned images of ALL the bases given to the
        reconstructor"""
        if not self.coeffs is None:
            datasets = np.shape(self.coeffs)[0]
            bases = np.shape(self.coeffs)[1]
            self.reconstructed = np.array([[self.coeffs_to_image(self.coeffs[ds][b], self.scanningParDict) for b in range(0, bases)] for ds in range(0, datasets)])
            print('shape of reconstructed is : ', np.shape(self.reconstructed))
        else:
            print('Cannot update images without coefficients')

    def add_grid_of_coeffs(self, im, coeffs, t, s, r0, c0, pr, pc):
#        print('Timepoint: ', t)
#        print('shape if im: ', im.shape)
#        print('shape if coeffts[i]: ', coeffs.shape)
#        print('r0: ', r0)
#        print('c0: ', c0)
#        print('pr: ', pr)
#        print('pc: ', pc)
        im[t, s, r0::pr, c0::pc] = coeffs

    def coeffs_to_image(self, coeffs, scanningParDict):
        """Takes the 4d matrix of coefficients from the signal extraction and
        reshapes into images according to given parameters"""
        frames = np.shape(coeffs)[0]
        dim0_side = int(scanningParDict['steps'][0])
        dim1_side = int(scanningParDict['steps'][1])
        dim2_side = int(scanningParDict['steps'][2])
        dim3_side = int(scanningParDict['steps'][3]) #Always timepoints
        if not frames == dim0_side*dim1_side*dim2_side*dim3_side:
            print('ERROR: Wrong dimensional data')
            pass

        timepoints = int(scanningParDict['steps'][scanningParDict['dimensions'].index(self.timepoints_text)])
        slices = int(scanningParDict['steps'][scanningParDict['dimensions'].index(self.b_f_text)])
        sq_rows = int(scanningParDict['steps'][scanningParDict['dimensions'].index(self.u_d_text)])
        sq_cols = int(scanningParDict['steps'][scanningParDict['dimensions'].index(self.r_l_text)])

        im = np.zeros([timepoints, slices, sq_rows*np.shape(coeffs)[1], sq_cols*np.shape(coeffs)[2]], dtype=np.float32)
        for i in np.arange(np.shape(coeffs)[0]):

            t = int(np.floor(i/(frames/dim3_side)))

            slow = int(np.mod(i, frames/timepoints) / (dim0_side*dim1_side))
            mid = int(np.mod(i, dim0_side*dim1_side) / dim0_side)
            fast = np.mod(i, dim0_side)

            if not scanningParDict['unidirectional']:
                odd_mid_step = np.mod(mid, 2)
                fast = (1-odd_mid_step)*fast + odd_mid_step*(dim1_side - 1 - fast)

            neg = (int(scanningParDict['directions'][0] == 'neg'),
                   int(scanningParDict['directions'][1] == 'neg'),
                   int(scanningParDict['directions'][2] == 'neg'))

            """Adjust for positive or negative direction"""
            fast = (1-neg[0])*fast + neg[0]*(dim0_side - 1 - fast)
            mid = (1-neg[1])*mid + neg[1]*(dim1_side - 1 - mid)
            slow = (1-neg[2])*slow + neg[2]*(dim2_side - 1 - slow)

            """Place dimensions in correct row/col/slice"""
            if scanningParDict['dimensions'][0] == self.r_l_text:
                if scanningParDict['dimensions'][1] == self.u_d_text:
                    c = fast
                    pc = dim0_side
                    r = mid
                    pr = dim1_side
                    s = slow
                else:
                    c = fast
                    pc = dim0_side
                    r = slow
                    pr = dim2_side
                    s = mid
            elif scanningParDict['dimensions'][0] == self.u_d_text:
                if scanningParDict['dimensions'][1] == self.r_l_text:
                    c = mid
                    pc = dim1_side
                    r = fast
                    pr = dim0_side
                    s = slow
                else:
                    c = slow
                    pc = dim2_side
                    r = fast
                    pr = dim0_side
                    s = mid
            else:
                if scanningParDict['dimensions'][1] == self.r_l_text:
                    c = mid
                    pc = dim1_side
                    r = slow
                    pr = dim2_side
                    s = fast
                else:
                    c = slow
                    pc = dim2_side
                    r = mid
                    pr = dim1_side
                    s = fast

            self.add_grid_of_coeffs(im, coeffs[i], t, s, r, c, pr, pc)

        return im
