import numpy as np
import NanoImagingPack as nip

from imswitch.imcommon.framework import Signal, Thread, Worker, Mutex
from imswitch.imcontrol.view import guitools
from imswitch.imcommon.model import initLogger
from ..basecontrollers import LiveUpdatedController


class HoloController(LiveUpdatedController):
    """ Linked to HoloWidget."""

    sigImageReceived = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.updateRate = 10
        self.it = 0
        self.init = False
        self.showPos = False

        # reconstruction related settings
        #TODO: Make parameters adaptable from Plugin
        self.valueRangeMin=0
        self.valueRangeMax=0
        self.pixelsize = 3.45*1e-6   
        self.mWavelength = 488*1e-9
        self.NA=.3
        self.k0 = 2*np.pi/(self.mWavelength)

        self.PSFpara = nip.PSF_PARAMS()
        self.PSFpara.wavelength = self.mWavelength
        self.PSFpara.NA=self.NA
        self.PSFpara.pixelsize = self.pixelsize

        self.dz = 40*1e-3

        # Prepare image computation worker
        self.imageComputationWorker = self.HoloImageComputationWorker()
        self.imageComputationWorker.set_pixelsize(self.pixelsize)
        self.imageComputationWorker.set_dz(self.dz)
        self.imageComputationWorker.set_PSFpara(self.PSFpara)
        self.imageComputationWorker.sigHoloImageComputed.connect(self.displayImage)
   
        self.imageComputationThread = Thread()
        self.imageComputationWorker.moveToThread(self.imageComputationThread)
        self.sigImageReceived.connect(self.imageComputationWorker.computeHoloImage)
        self.imageComputationThread.start()

        # Connect CommunicationChannel signals
        self._commChannel.sigUpdateImage.connect(self.update)

        # Connect HoloWidget signals
        self._widget.sigShowToggled.connect(self.setShowHolo)
        self._widget.sigUpdateRateChanged.connect(self.changeRate)
        self._widget.sigSliderValueChanged.connect(self.valueChanged)

        self.changeRate(self._widget.getUpdateRate())
        self.setShowHolo(self._widget.getShowHoloChecked())

    def valueChanged(self, magnitude):
        """ Change magnitude. """
        self.dz = magnitude*1e-3
        self.imageComputationWorker.set_dz(self.dz)

    def __del__(self):
        self.imageComputationThread.quit()
        self.imageComputationThread.wait()
        if hasattr(super(), '__del__'):
            super().__del__()

    def setShowHolo(self, enabled):
        """ Show or hide Holo. """
        self.pixelsize = self._widget.getPixelSize()
        self.mWavelength = self._widget.getWvl()
        self.NA = self._widget.getNA()
        self.k0 = 2 * np.pi / (self.mWavelength)
        self.active = enabled
        self.init = False

    def update(self, detectorName, im, init, isCurrentDetector):
        """ Update with new detector frame. """
        if not isCurrentDetector or not self.active:
            return

        if self.it == self.updateRate:
            self.it = 0
            self.imageComputationWorker.prepareForNewImage(im)
            self.sigImageReceived.emit()
        else:
            self.it += 1

    def displayImage(self, im):
        """ Displays the image in the view. """
        self._widget.setImage(im)

    def changeRate(self, updateRate):
        """ Change update rate. """
        self.updateRate = updateRate
        self.it = 0

    class HoloImageComputationWorker(Worker):
        sigHoloImageComputed = Signal(np.ndarray)

        def __init__(self):
            super().__init__()
            
            self._logger = initLogger(self, tryInheritParent=False)
            self._numQueuedImages = 0
            self._numQueuedImagesMutex = Mutex()
            self.PSFpara = None
            self.pixelsize = 1
            self.dz = 1


        def reconholo(self, image, PSFpara, N_subroi=1024, pixelsize=1e-3, dz=50e-3):
            mimage = nip.image(np.sqrt(image))
            mimage = nip.extract(mimage, [N_subroi,N_subroi])
            mimage.pixelsize=(pixelsize, pixelsize)
            mpupil = nip.ft(mimage)         
            #nip.__make_propagator__(mpupil, PSFpara, doDampPupil=True, shape=mpupil.shape, distZ=dz)
            cos_alpha, sin_alpha = nip.cosSinAlpha(mimage, PSFpara)
            defocus = self.dz #  defocus factor
            PhaseMap = nip.defocusPhase(cos_alpha, defocus, PSFpara)
            propagated = nip.ft2d((np.exp(1j * PhaseMap))*mpupil)
            return np.squeeze(propagated)

        def computeHoloImage(self):
            """ Compute Holo of an image. """
            try:
                if self._numQueuedImages > 1:
                    return  # Skip this frame in order to catch up
                holorecon = np.flip(np.abs(self.reconholo(self._image, PSFpara=self.PSFpara, N_subroi=1024, pixelsize=self.pixelsize, dz=self.dz)),1)
                
                self.sigHoloImageComputed.emit(np.array(holorecon))
            finally:
                self._numQueuedImagesMutex.lock()
                self._numQueuedImages -= 1
                self._numQueuedImagesMutex.unlock()

        def prepareForNewImage(self, image):
            """ Must always be called before the worker receives a new image. """
            self._image = image
            self._numQueuedImagesMutex.lock()
            self._numQueuedImages += 1
            self._numQueuedImagesMutex.unlock()

        def set_dz(self, dz):
            self.dz = dz
        
        def set_PSFpara(self, PSFpara):
            self.PSFpara = PSFpara

        def set_pixelsize(self, pixelsize):
            self.pixelsize = pixelsize


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
