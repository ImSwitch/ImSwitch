import time

import numpy as np
import scipy.ndimage as ndi
import threading

from imswitch.imcommon.model import initLogger, APIExport
from ..basecontrollers import ImConWidgetController
from skimage.filters import gaussian, median
from imswitch.imcommon.framework import Signal, Thread, Worker, Mutex, Timer
import cv2

try:
    import NanoImagingPack as nip
    isNIP=True
except:
    isNIP = False


# global axis for Z-positioning - should be Z
gAxis = "Z"
T_DEBOUNCE = .2


class AutofocusController(ImConWidgetController):
    """Linked to AutofocusWidget."""


    sigImageReceived = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__logger = initLogger(self)

        if self._setupInfo.autofocus is None:
            return

        self.isAutofusRunning = False

        self.camera = self._setupInfo.autofocus.camera
        self.positioner = self._setupInfo.autofocus.positioner
        # self._master.detectorsManager[self.camera].crop(*self.cropFrame)

        # Connect AutofocusWidget buttons
        self._widget.focusButton.clicked.connect(self.focusButton)
        self._commChannel.sigAutoFocus.connect(self.autoFocus)

        # select stage
        self.stages = self._master.positionersManager[self._master.positionersManager.getAllDeviceNames()[0]]

        # for display on Napari
        self.imageToDisplayName = ""
        self.imageToDisplay = None
        self.sigImageReceived.connect(self.displayImage)

    def __del__(self):
        self._AutofocusThead.quit()
        self._AutofocusThead.wait()
        if hasattr(super(), '__del__'):
            super().__del__()

    def focusButton(self):
        if not self.isAutofusRunning:
            rangez = float(self._widget.zStepRangeEdit.text())
            resolutionz = float(self._widget.zStepSizeEdit.text())
            defocusz = float(self._widget.zBackgroundDefocusEdit.text())
            self._widget.focusButton.setText('Stop')
            self.autoFocus(rangez, resolutionz, defocusz)
        else:
            self.isAutofusRunning = False

    @APIExport(runOnUIThread=True)
    # Update focus lock
    def autoFocus(self, rangez=100, resolutionz=10, defocusz=0):

        '''
        The stage moves from -rangez...+rangez with a resolution of resolutionz
        For every stage-position a camera frame is captured and a contrast curve is determined

        '''
        # determine optimal focus position by stepping through all z-positions and cacluate the focus metric
        self.isAutofusRunning = True
        self._AutofocusThead = threading.Thread(target=self.doAutofocusBackground, args=(rangez, resolutionz, defocusz),
                                                daemon=True)
        self._AutofocusThead.start()

    def grabCameraFrame(self):
        detectorManager = self._master.detectorsManager[self.camera]
        return detectorManager.getLatestFrame()

    def displayImage(self):
        # a bit weird, but we cannot update outside the main thread
        name = self.imageToDisplayName
        self._widget.setImageNapari(np.uint16(self.imageToDisplay), colormap="gray", name=name, pixelsize=(1,1), translation=(0,0))

    def recordFlatfield(self, nFrames=10, nGauss=16, defocusPosition = 200, defocusAxis="Z"):
        '''
        This method defocusses the sample and records a series of images to produce a flatfield image
        '''
        flatfield = []
        posStart = self.stages.getPosition()[defocusAxis]
        time.sleep(1) # debounce
        self.stages.move(value=defocusPosition, axis=defocusAxis, is_absolute=False, is_blocking=True)
        for iFrame in range(nFrames):
            mFrame = self.grabCameraFrame()
            flatfield.append(mFrame)
        flatfield = np.mean(np.array(flatfield),0)
        # normalize and smooth using scikit image
        flatfield = gaussian(flatfield, sigma=nGauss)
        #flatfield = median(flatfield, selem=np.ones((nMedian, nMedian)))
        self.stages.move(value=-defocusPosition, axis=defocusAxis, is_absolute=False, is_blocking=True)

        time.sleep(1)  #debounce
        return flatfield

    def doAutofocusBackground(self, rangez=100, resolutionz=10, defocusz=0):
        self._commChannel.sigAutoFocusRunning.emit(True)  # inidicate that we are running the autofocus
        bestzpos_rel = None
        mProcessor = FrameProcessor()
        # record a flatfield Image and display
        if defocusz !=0:
            flatfieldImage = self.recordFlatfield(defocusPosition=defocusz)
            self.imageToDisplay = flatfieldImage
            mProcessor.setFlatfieldFrame(flatfieldImage)
            self.imageToDisplayName = "FlatFieldImage"
        #self.sigImageReceived.emit()

        initialPosition = self.stages.getPosition()["Z"]

        Nz = int(2 * rangez // resolutionz)
        allfocusvals = np.zeros(Nz)
        relative_positions = np.int32(np.linspace(-abs(rangez), abs(rangez), Nz))

        # Move to the initial relative position
        self.stages.move(value=relative_positions[0], axis="Z", is_absolute=False, is_blocking=True)
        mAllImages = []

        for iz in range(Nz):
            if not self.isAutofusRunning:
                break

            # Move to the next relative position
            if iz != 0:
                self.stages.move(value=relative_positions[iz] - relative_positions[iz-1], axis="Z", is_absolute=False, is_blocking=True)

            mImg = self.grabCameraFrame()
            mProcessor.add_frame(mImg, iz)
            mAllImages.append(mImg)

        allfocusvalsList = mProcessor.getFocusValueList(nFrameExpected=Nz)
        mProcessor.stop()

        if 0: # only for debugging
            allProcessedFrames = mProcessor.getAllProcessedSlices()
            self.imageToDisplay = allProcessedFrames
            self.imageToDisplayName = "ProcessedStack"
            self.sigImageReceived.emit()
            import tifffile as tif
            tif.imsave("autofocus_rawimages.tif", mAllImages)
            tif.imsave("autofocus_processed.tif", allProcessedFrames)
            self.imageToDisplay = mAllImages
            self.imageToDisplayName = "RAWImages"
            self.sigImageReceived.emit()

        if self.isAutofusRunning:
            oordinate = relative_positions + initialPosition
            self._widget.focusPlotCurve.setData(oordinate[:len(allfocusvalsList)], np.array(allfocusvalsList))

            allfocusvals = np.array(allfocusvalsList)
            zindex = np.where(np.max(allfocusvals) == allfocusvals)[0]
            bestzpos_rel = relative_positions[np.squeeze(zindex)]
            if type(bestzpos_rel)==np.ndarray and bestzpos_rel.shape>1:
                bestzpos_rel =bestzpos_rel[0]
            # Move back to the initial position
            self.stages.move(value=-2*rangez, axis="Z", is_absolute=False, is_blocking=True)
            self.stages.move(value= rangez+bestzpos_rel, axis="Z", is_absolute=False, is_blocking=True)


        else:
            # Return to the initial absolute position
            self.stages.move(value=initialPosition, axis="Z", is_absolute=True, is_blocking=True)

        # We are done!
        self._commChannel.sigAutoFocusRunning.emit(False)  # inidicate that we are running the autofocus
        self.isAutofusRunning = False

        self._widget.focusButton.setText('Autofocus')
        return bestzpos_rel + initialPosition



import threading
import queue

class FrameProcessor:
    def __init__(self, nGauss=7, nCropsize=2048):
        self.frame_queue = queue.Queue()
        self.allfocusimages = []
        self.allfocusvals = []
        self.worker_thread = threading.Thread(target=self.process_frames, daemon=True)
        self.worker_thread.start()
        self.flatFieldFrame = None
        self.allLaplace = []
        self.nGauss = nGauss
        self.nCropsize = nCropsize
        self.isRunning = True


    def setFlatfieldFrame(self, flatfieldFrame):
        self.flatFieldFrame = flatfieldFrame

    def add_frame(self, img, iz):
        """ Add frames to the queue """
        self.frame_queue.put((img, iz))

    def process_frames(self):
        """ Continuously process frames from the queue """
        while self.isRunning:
            img, iz = self.frame_queue.get()
            self.process_frame(img, iz)

    def process_frame(self, img, iz):
        # crop frame, only take inner 40%

        if self.flatFieldFrame is not None:
            img = img/self.flatFieldFrame
        # crop region
        img = self.extract(img, self.nCropsize)

        if 0:
            # Gaussian filter the image, to remove noise
            imagearraygf = ndi.filters.gaussian_filter(img, self.nGauss)

            # compute focus metric
            mLaplace = ndi.filters.laplace(imagearraygf)
            self.allLaplace.append(mLaplace)
            focusquality = np.std(mLaplace)
        else:

            # Encode the NumPy array to JPEG format with 80% quality
            if len(img.shape)>3:
                img = np.mean(img,-1)
            imagearraygf = ndi.filters.gaussian_filter(img, self.nGauss)
            is_success, buffer = cv2.imencode(".jpg", imagearraygf, [int(cv2.IMWRITE_JPEG_QUALITY), 80])

            # Check if encoding was successful
            if is_success:
                # Get the size of the JPEG image
                focusquality = len(buffer)
            else:
                focusquality = 0
        self.allfocusvals.append(focusquality)

    def stop(self):
        self.isRunning = False

    @staticmethod
    def extract(marray, crop_size):
        center_x, center_y = marray.shape[1] // 2, marray.shape[0] // 2

        # Calculate the starting and ending indices for cropping
        x_start = center_x - crop_size // 2
        x_end = x_start + crop_size
        y_start = center_y - crop_size // 2
        y_end = y_start + crop_size

        # Crop the center region
        return marray[y_start:y_end, x_start:x_end]

    def getFocusValueList(self, nFrameExpected, timeout=5):
        t0=time.time() # in case something goes wrong
        while len(self.allfocusvals)<(nFrameExpected):
            time.sleep(.01)
            if time.time()-t0>timeout:
                break
        return self.allfocusvals

    def getAllProcessedSlices(self):
        return np.array(self.allLaplace)

# Copyright (C) 2020-2023 ImSwitch developers
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
