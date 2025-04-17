import time

import numpy as np

from imswitch.imcommon.framework import Thread, Worker, Signal
from ..basecontrollers import ImConWidgetController
from skimage.transform import rescale
from tifffile import imsave,imread
from imswitch.imcontrol.view import guitools
import  matplotlib.pyplot as plt 
from skimage import io, measure, morphology
from scipy.signal import find_peaks
import cv2

class BeadRecController(ImConWidgetController):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.recIm = None
        self.im_display = None
        self.running = False
        self.roiAdded = False
        self.newScan = False
        self.parametersChanged = False
        self.dims = None
        self.stepSizes = None

        self.beadWorker = BeadWorker(self)
        self.beadWorker.sigNewChunk.connect(self.update)
        self.thread = Thread()
        self.beadWorker.moveToThread(self.thread)
        self.thread.started.connect(self.beadWorker.run)

        # Connect BeadRecWidget signals
        self._widget.sigROIToggled.connect(self.roiToggled)
        self._widget.sigRunClicked.connect(self.run)
        self._widget.sigScaleClicked.connect(self.updateScaling)
        self._widget.saveRecBtn.clicked.connect(self.saveRec)
        self._widget.loadImgBtn.clicked.connect(self.loadImg)
        self._widget.donutsAnalysisBtn.clicked.connect(self.donutsAnalysis)

        # Connect comm channel signals
        self._commChannel.sigScanStarted.connect(self.updateParameters)
        self._commChannel.sigScanStarted.connect(self.setNewScanStatus)

    def __del__(self):
        self.thread.quit()
        self.thread.wait()
        if hasattr(super(), '__del__'):
            super().__del__()

    def donutsAnalysis(self):
        run_donut_analysis(self.im_display)

    def loadImg(self):
        path = guitools.askForFilePath(self._widget, 'Choose a tiff image',defaultFolder='C:',isSaving=False,
                                       nameFilter= "TIFF Files (*.tif *.tiff)")
        if path is None:
            return
        
        self.im_display = imread(path)
        self._widget.updateImage(self.im_display)

    def saveRec(self):
        if self.recIm is None:
            return
        path = guitools.askForFilePath(self._widget, '',defaultFolder='D:',isSaving=True)
        im_display = np.resize(self.recIm, (self.dims[1] + 1,self.dims[0] + 1))
        if self._widget.scaleButton.isChecked():
            im_display = self.rescale(im_display)
        
        if path.split('.')[-1] not in ['tif', 'tiff']:
            path = path + ".tiff"
        
        imsave(path,im_display)
        

    def roiToggled(self, enabled):
        """ Show or hide ROI."""
        if enabled:
            self.addROI()

            ROIsize = (64, 64)
            ROIcenter = self._commChannel.getCenterViewbox()

            ROIpos = (ROIcenter[0] - 0.5 * ROIsize[0],
                      ROIcenter[1] - 0.5 * ROIsize[1])

            self._widget.showROI(ROIpos, ROIsize)
        else:
            self._widget.hideROI()

    def addROI(self):
        """ Adds the ROI to ImageWidget viewbox through the CommunicationChannel. """
        if not self.roiAdded:
            self._commChannel.sigAddItemToVb.emit(self._widget.getROIGraphicsItem())
            self.roiAdded = True

    def run(self):
        if not self.running:
            self.updateParameters()
            self.running = True
            self._master.detectorsManager.execOnAll(lambda c: c.flushBuffers())
            self.thread.start()
        else:
            self.running = False
            self.thread.quit()
            self.thread.wait()

    def setNewScanStatus(self):
        self.newScan = True

    def updateParameters(self):
        prior_dims = self.dims
        prior_stepSizes = self.stepSizes
        self.dims = np.array(self._commChannel.getDimsScan()).astype(int)
        self.stepSizes = np.array(self._commChannel.getScanStepSizes(),dtype=float)[self.dims!=0]
        self.dims = self.dims[self.dims != 0]
        if len(self.dims)>2:
            self.dims = self.dims[:2]
            self._logger.warning("Using only first 2 dimensions of 3d scan")
        
        if prior_dims is not None and prior_stepSizes is not None:
            if len(prior_dims) != len(self.dims) or (prior_dims != self.dims).any() or \
                len(prior_stepSizes) != len(self.stepSizes) or (prior_stepSizes != self.stepSizes).any():
                
                self.parametersChanged = True


    def updateScaling(self):
        if not self._commChannel.isScanRunning():
            self.update()

    def rescale(self,im):
        """
        Rescale imRec if not isotropic scan. Uses scikit rescale function, without interpolation.
        """
        px_y = self.stepSizes[1] # (y,x) in recIm, so inversed to the scan XY.
        px_x = self.stepSizes[0]
        if px_y - px_x == 0:
            return im
        scale_x = px_x / min(px_x, px_y)
        scale_y = px_y / min(px_x, px_y)
        rescaled_im = rescale(im, (scale_y, scale_x), anti_aliasing=False, mode='reflect', preserve_range=True)  
        # imsave(r"C:\Users\MonaLisa\Documents\rescaled.tiff",rescaled_im) #to debug scaling
        return rescaled_im
    
    def update(self):
        self.im_display = np.resize(self.recIm, (self.dims[1] + 1,self.dims[0] + 1))
        if self._widget.scaleButton.isChecked():
            self.im_display = self.rescale(self.im_display)
        self._widget.updateImage(self.im_display)


class BeadWorker(Worker):
    sigNewChunk = Signal()

    def __init__(self, controller):
        super().__init__()
        self.__controller = controller
    
    def init1DArray(self):
        dims = np.array(self.__controller.dims)
        N = (dims[0] + 1) * (dims[1] + 1)
        self.__controller.recIm = np.zeros(N)
        return N

    def run(self):
        N = self.init1DArray()
        i = 0

        while self.__controller.running:

            if self.__controller.newScan:
                self.__controller.newScan = False
                i = 0
            
            if self.__controller.parametersChanged:
                self.__controller.parametersChanged = False
                N = self.init1DArray()

            if self.__controller._commChannel.isScanRunning():
                newImages = self.__controller._master.detectorsManager.execOnCurrent(
                    lambda c: c.getChunk()
                )
                n = len(newImages)
                if n > 0:
                    roiItem = self.__controller._widget.getROIGraphicsItem()
                    x0, y0, x1, y1 = roiItem.bounds

                    for j in range(0, n):
                        img = newImages[j]
                        img = img[y0:y1, x0:x1]
                        mean = np.mean(img)
                        self.__controller.recIm[i] = mean
                        i = i + 1
                        if i == N:
                            i = 0
                    self.sigNewChunk.emit()

            time.sleep(0.0001)  # Prevents freezing

def run_donut_analysis(im:np.ndarray,params:dict = None):

    """ Zero analysis of donuts function"""
    if params is None:
        params = {}
    else:
        assert isinstance(params,dict), "params should be a dictionnary"
    
    # retrieve parameters, default values set if not found
    min_area = params.get("min_area",50)
    max_area = params.get("max_area",1000)
    bead_margin_px = params.get("bead_margin_px",3)
    tol_peaks_pos = params.get("tol_peaks_pos",10)
    thresh_coeff = params.get("thresh_coeff",0.2)

    # Pad image
    im_pad = np.pad(im, pad_width=3, mode='constant', constant_values=np.min(im))

    # Thresholding
    range_val = np.max(im) - np.min(im)
    thresh = thresh_coeff * range_val + np.min(im)
    im_bw1 = im_pad > thresh

    # Connected components
    labels = measure.label(im_bw1)
    props = measure.regionprops_table(labels, properties=('centroid', 'area'))
    areas = np.array(props['area'])
    sorted_idx = np.argsort(areas)[::-1]  # descending

    rejected_peaks = False
    rejected_binarization = False
    # Blob detection
    if len(areas) > 0 and min_area < areas[sorted_idx[0]] < max_area:
        mask = labels == (sorted_idx[0] + 1)
        im_bw2 = morphology.binary_closing(mask, morphology.disk(5))

        # Diameter and erosion
        props2 = measure.regionprops(im_bw2.astype(int))
        blob_diameter = props2[0].equivalent_diameter
        radius = max(round(blob_diameter * 0.3), 1)
        im_bw3 = morphology.erosion(im_bw2, morphology.disk(radius))

        # Background estimation
        im_bw_bg = morphology.dilation(im_bw1[3:-3, 3:-3], morphology.disk(3))
        im_bg = im[~im_bw_bg]
        bg = np.mean(im_bg[im_bg != 0])

        # Find local minimum
        im2 = im.copy()
        im3_crop = im_bw3[3:-3, 3:-3]
        im2[~im3_crop] = 1e3
        im2[im2 < bg + 0.1 * range_val] = 1e3
        min_val = np.min(im2)
        miny, minx = np.unravel_index(np.argmin(im2), im2.shape)
        
        linex = im[miny, :]
        liney = im[:, minx]
        
        try:
            # Line profile X
            xlocs, xpks_props = find_peaks(linex)
            xpks = linex[xlocs]  # Get the peak values at those indices
            valid_peaks_x = np.where(np.abs(xlocs - minx) <= tol_peaks_pos)[0]

            filtered_peaks_x = xlocs[valid_peaks_x]
            filtered_vals_x = linex[filtered_peaks_x]
            order_x = np.argsort(filtered_vals_x)[::-1]

            maxX1 = filtered_vals_x[order_x[0]]
            x1 = filtered_peaks_x[order_x[0]]
            maxX2 = filtered_vals_x[order_x[1]]
            x2 = filtered_peaks_x[order_x[1]]
            maxX = 0.5 * (maxX1 + maxX2)
            fillX = (min_val - bg) / (maxX - bg)

            # Line profile Y
            ylocs, ypks_props = find_peaks(liney)
            ypks = liney[ylocs]
            valid_peaks_y = np.where(np.abs(ylocs - miny) <= tol_peaks_pos)[0]


            filtered_peaks_y = ylocs[valid_peaks_y]
            filtered_vals_y = liney[filtered_peaks_y]
            order_y = np.argsort(filtered_vals_y)[::-1]

            maxY1 = filtered_vals_y[order_y[0]]
            y1 = filtered_peaks_y[order_y[0]]
            maxY2 = filtered_vals_y[order_y[1]]
            y2 = filtered_peaks_y[order_y[1]]
            maxY = 0.5 * (maxY1 + maxY2)
            fillY = (min_val - bg) / (maxY - bg)

        except Exception as e:
            fillX = 0
            fillY = 0
            rejected_peaks = True

    else:
        rejected_binarization = True

    # Final plotting
    if rejected_binarization:
        fig, axes = plt.subplots(1, 2, figsize=(8, 4))
        fig.suptitle('Rejected after binarization. Check parameters.', fontsize=16)
        axes[0][0].imshow(im, cmap='gray')
        axes[0][0].set_title("Donut")
        axes[0][1].imshow(im_bw1, cmap='gray')
        axes[0][1].set_title("Binarized")

    elif rejected_peaks:
        fig, axes = plt.subplots(1, 4, figsize=(16, 4))
        fig.suptitle('Rejected because peaks localization failed.', fontsize=16)
        axes[0][0].imshow(im, cmap='gray')
        axes[0][0].set_title("Donut + zero localization")
        axes[0][0].axvline(x=minx, color='red')   # vertical line
        axes[0][0].axhline(y=miny, color='green') # horizontal line

        axes[0][1].imshow(im_bw1, cmap='gray')
        axes[0][1].set_title("Binarized")

        axes[1][2].plot(linex, 'g')
        axes[1][2].set_title("X profile")

        axes[1][3].plot(liney, 'r')
        axes[1][3].set_title("fillY")


    else:
        # Display processing steps
        fig, axes = plt.subplots(2, 4, figsize=(16, 8))
        fig.suptitle('Donuts analysis results', fontsize=16)

        axes[0][0].imshow(im, cmap='gray')
        axes[0][0].set_title("Donut")
        axes[0][1].imshow(im_bw1, cmap='gray')
        axes[0][1].set_title("Binarized")
        axes[0][2].imshow(im_bw2, cmap='gray')
        axes[0][2].set_title("After closing")
        axes[0][3].imshow(im_bw3, cmap='gray')
        axes[0][3].set_title("After erosion (zero search area)")

        # Subplot 1: original image with cross lines
        axes[1][0].imshow(im, cmap='gray')
        axes[1][0].axis('image')
        axes[1][0].axvline(x=minx, color='red')   # vertical line
        axes[1][0].axhline(y=miny, color='green') # horizontal line
        axes[1][0].set_title("Zero location")

        # Subplot 2: background mask
        axes[1][1].imshow(im_bw_bg, cmap='gray')
        axes[1][1].axis('image')
        axes[1][1].set_title("Bkg estim")

        # Subplot 3: X profile
        axes[1][2].plot(linex, 'g')
        axes[1][2].plot([x1, x2], [maxX1, maxX2], 'xk')
        axes[1][2].text(minx - 3, min_val - 1, f"{fillX:.2f}")
        axes[1][2].set_title("fillX")

        # Subplot 4: Y profile
        axes[1][3].plot(liney, 'r')
        axes[1][3].plot([y1, y2], [maxY1, maxY2], 'xk')
        axes[1][3].text(miny - 5, min_val - 3, f"{fillY:.2f}")
        axes[1][3].set_title("fillY")


        for idx in range(2):
            for ax in axes[idx]:
                ax.axis('off')
        # plt.tight_layout()
        plt.show()





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
