import time

import numpy as np
import scipy.ndimage as ndi
import threading

from imswitch.imcommon.framework import Thread, Timer
from imswitch.imcommon.model import initLogger, APIExport
from ..basecontrollers import ImConWidgetController

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

    def __del__(self):
        self._AutofocusThead.quit()
        self._AutofocusThead.wait()
        if hasattr(super(), '__del__'):
            super().__del__()

    def focusButton(self):
        if not self.isAutofusRunning:
            rangez = float(self._widget.zStepRangeEdit.text())
            resolutionz = float(self._widget.zStepSizeEdit.text())
            self._widget.focusButton.setText('Stop')
            self.autoFocus(rangez, resolutionz)
        else:
            self.isAutofusRunning = False

    @APIExport(runOnUIThread=True)
    # Update focus lock
    def autoFocus(self, rangez=100, resolutionz=10):

        '''
        The stage moves from -rangez...+rangez with a resolution of resolutionz
        For every stage-position a camera frame is captured and a contrast curve is determined

        '''
        # determine optimal focus position by stepping through all z-positions and cacluate the focus metric
        self.isAutofusRunning = True
        self._AutofocusThead = threading.Thread(target=self.doAutofocusBackground, args=(rangez, resolutionz),
                                                daemon=True)
        self._AutofocusThead.start()

    def grabCameraFrame(self):
        detectorManager = self._master.detectorsManager[self.camera]
        return detectorManager.getLatestFrame()

    def doAutofocusBackground(self, rangez=100, resolutionz=10):
        self._commChannel.sigAutoFocusRunning.emit(True)  # inidicate that we are running the autofocus

        # get current position
        initialPosition = self.stages.getPosition()["Z"]

        # precompute values for Z-scan
        Nz = int(2 * rangez // resolutionz)
        allfocusvals = np.zeros(Nz)
        allfocuspositions = np.int32(np.linspace(-abs(rangez), abs(rangez), Nz) + initialPosition)

        # 0 move focus to initial position
        self.stages.move(value=allfocuspositions[0], axis="Z", is_absolute=True, is_blocking=True)

        # Example usage
        mProcessor = FrameProcessor()

        # 1 compute focus for every z position
        for iz in range(Nz):

            # exit autofocus if necessary
            if not self.isAutofusRunning:
                break
            # 0 Move stage to the predefined position - remember: stage moves in relative coordinates
            self.stages.move(value=allfocuspositions[iz], axis="Z", is_absolute=True, is_blocking=True)
            self._logger.debug(f'Moving focus to {allfocuspositions[iz]}')

            # 1 Grab camera frame
            self._logger.debug("Grabbing Frame")
            mImg = self.grabCameraFrame()
            mProcessor.add_frame(mImg, iz)

        # collect all values once done
        allfocusvalsList = mProcessor.getFocusValueList(nFrameExpected=Nz)
       
        if self.isAutofusRunning:
            # display the curve
            self._widget.focusPlotCurve.setData(allfocuspositions, np.array(allfocusvalsList))

            # 4 find maximum focus value and move stage to this position
            allfocusvals = np.array(allfocusvalsList)
            zindex = np.where(np.max(allfocusvals) == allfocusvals)[0]
            bestzpos = allfocuspositions[np.squeeze(zindex)]

            # 5 move focus back to initial position (reduce backlash)
            self.stages.move(value=allfocuspositions[0], axis="Z", is_absolute=True, is_blocking=True)

            # 6 Move stage to the position with max focus value
            self._logger.debug(f'Moving focus to {zindex * resolutionz}')
            self.stages.move(value=bestzpos, axis="Z", is_absolute=True, is_blocking=True)

            if False:
                allfocusimages = np.array(allfocusimages)
                np.save('allfocusimages.npy', allfocusimages)
                import tifffile as tif
                tif.imsave("llfocusimages.tif", allfocusimages)
                np.save('allfocuspositions.npy', allfocuspositions)
                np.save('allfocusvals.npy', allfocusvals)

        else:
            self.stages.move(value=initialPosition, axis="Z", is_absolute=True, is_blocking=True)

        # DEBUG

        # We are done!
        self._commChannel.sigAutoFocusRunning.emit(False)  # inidicate that we are running the autofocus
        self.isAutofusRunning = False

        self._widget.focusButton.setText('Autofocus')
        return bestzpos



import threading
import queue

class FrameProcessor:
    def __init__(self):
        self.frame_queue = queue.Queue()
        self.allfocusimages = []
        self.allfocusvals = []
        self.worker_thread = threading.Thread(target=self.process_frames, daemon=True)
        self.worker_thread.start()

    def add_frame(self, img, iz, isNIP=True):
        """ Add frames to the queue """
        print("Add frame: "+str(iz))
        self.frame_queue.put((img, iz, isNIP))

    def process_frames(self):
        """ Continuously process frames from the queue """
        while True:
            img, iz, isNIP = self.frame_queue.get()
            self.process_frame(img, iz, isNIP)

    def process_frame(self, img, iz, gSigma=3, cropRegion=512, isNIP=False):
        # crop frame, only take inner 40%
        if isNIP:
            img = self.extract(img, (cropRegion,cropRegion))

        print("processing frame : "+str(iz))
        # Gaussian filter the image, to remove noise
        imagearraygf = ndi.filters.gaussian_filter(img, gSigma)

        # compute focus metric
        focusquality = np.mean(ndi.filters.laplace(imagearraygf))
        self.allfocusvals.append(focusquality)

    @staticmethod
    def extract(img, size):
        """ A dummy nip.extract function """
        # Replace with actual NIP extraction logic if needed
        return img[:size[0], :size[1]]

    def getFocusValueList(self, nFrameExpected):
        t0=time.time() # in case something goes wrong
        while not(len(self.allfocusvals)==nFrameExpected) or not time.time()-t0>5:
            time.sleep(.01)
        return self.allfocusvals

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
