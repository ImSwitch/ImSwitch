import numpy as np

try:
    import NanoImagingPack as nip
    isNIP = True
except:
    isNIP = False
    
from imswitch.imcommon.framework import Signal, Thread, Worker, Mutex
from imswitch.imcontrol.view import guitools
from imswitch.imcommon.model import initLogger
from ..basecontrollers import LiveUpdatedController
import threading
import time 
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
        self.lastProcessedTime = time.time()

        if not isNIP:
            return
        self.PSFpara = nip.PSF_PARAMS()
        self.PSFpara.wavelength = self.mWavelength
        self.PSFpara.NA=self.NA
        self.PSFpara.pixelsize = self.pixelsize
        self.availableReconstructionModes = ["off", "inline", "offaxis"]
        self.reconstructionMode = self.availableReconstructionModes[0]
        self.dz = 40*1e-3
        # Prepare image computation worker
        self.imageComputationWorker = self.HoloImageComputationWorker()
        self.imageComputationWorker.set_pixelsize(self.pixelsize)
        self.imageComputationWorker.set_dz(self.dz)
        self.imageComputationWorker.set_PSFpara(self.PSFpara)
        self.imageComputationWorker.sigHoloImageComputed.connect(self.displayImage)
   
        self.imageComputationThread = Thread()
        self.imageComputationWorker.moveToThread(self.imageComputationThread)
        #self.sigImageReceived.connect(self.imageComputationWorker.computeHoloImage)
        self.imageComputationThread.start()

        # Connect CommunicationChannel signals
        self._commChannel.sigUpdateImage.connect(self.update)

        # Connect HoloWidget signals 
        self._widget.sigShowInLineToggled.connect(self.setShowInLineHolo)
        self._widget.sigShowOffAxisToggled.connect(self.setShowOffAxisHolo)
        self._widget.sigUpdateRateChanged.connect(self.changeRate)
        self._widget.sigInLineSliderValueChanged.connect(self.inLineValueChanged)
        self._widget.sigOffAxisSliderValueChanged.connect(self.offAxisValueChanged)
        self._widget.btnSelectCCCenter.clicked.connect(self.selectCCCenter)
        self.changeRate(self._widget.getUpdateRate())
        self.setShowInLineHolo(self._widget.getShowInLineHoloChecked())
        self.setShowOffAxisHolo(self._widget.getShowOffAxisHoloChecked())

    def selectCCCenter(self):
        # get the center of the cross correlation
        self.CCCenter = self._widget.getCCCenterFromNapari()
        self.CCRadius = self._widget.getCCRadius()
        if self.CCRadius is None or self.CCRadius<50:
            self.CCRadius = 100
        self.imageComputationWorker.set_CCCenter(self.CCCenter)
        self.imageComputationWorker.set_CCRadius(self.CCRadius)

    def offAxisValueChanged(self, magnitude):
        self.dz = magnitude*1e-3
        self.imageComputationWorker.set_dz(self.dz)
    
    def inLineValueChanged(self, magnitude):
        """ Change magnitude. """
        self.dz = magnitude*1e-3
        self.imageComputationWorker.set_dz(self.dz)

    def __del__(self):
        self.imageComputationThread.quit()
        self.imageComputationThread.wait()
        if hasattr(super(), '__del__'):
            super().__del__()

    def setShowInLineHolo(self, enabled):
        """ Show or hide Holo. """
        self.pixelsize = self._widget.getPixelSize()
        self.mWavelength = self._widget.getWvl()
        self.NA = self._widget.getNA()
        self.k0 = 2 * np.pi / (self.mWavelength)
        self.active = enabled
        self.init = False
        self.reconstructionMode = self.availableReconstructionModes[1]
        self.imageComputationWorker.setReconstructionMode(self.reconstructionMode)
        self.imageComputationWorker.setActive(enabled)
        
    def setShowOffAxisHolo(self, enabled):
        """ Show or hide Holo. """
        self.pixelsize = self._widget.getPixelSize()
        self.mWavelength = self._widget.getWvl()
        self.NA = self._widget.getNA()
        self.k0 = 2 * np.pi / (self.mWavelength)
        self.active = enabled
        self.init = False
        self.reconstructionMode = self.availableReconstructionModes[2]
        self.imageComputationWorker.setReconstructionMode(self.reconstructionMode)
        self.imageComputationWorker.setActive(enabled)
        self._widget.createPointsLayer()
        #detectorName, image, init, scale, detectorName==self._currentDetectorName
   
    def update(self, detectorName, im, init, scale, isCurrentDetector):
        """ Update with new detector frame. """
        
        if  not self.active or not isNIP:# or not isCurrentDetector:
            return

        if time.time()-self.lastProcessedTime<1/self.updateRate:
            return
        if self.it == self.updateRate:
            self.it = 0
            self.imageComputationWorker.prepareForNewImage(im)
            self.sigImageReceived.emit()
            self.lastProcessedTime = time.time()
        else:
            self.it += 1

    def displayImage(self, im, name):
        """ Displays the image in the view. """
        if im.dtype=="complex":
            self._widget.setImage(np.abs(im), name+"_abs")
            self._widget.setImage(np.angle(im), name+"_angle")
        else:
            self._widget.setImage(np.abs(im), name)

    def changeRate(self, updateRate):
        """ Change update rate. """
        if updateRate == "":
            return
        if updateRate <= 0:
            updateRate = 1
        self.updateRate = updateRate
        self.it = 0

    class HoloImageComputationWorker(Worker):
        sigHoloImageComputed = Signal(np.ndarray, str)

        def __init__(self):
            super().__init__()
            
            self._logger = initLogger(self, tryInheritParent=False)
            self.PSFpara = None
            self.pixelsize = 1
            self.dz = 1
            self.reconstructionMode = "off"
            self.active = False
            self.CCCenter = None
            self.CCRadius = 100
            self.isBusy = False
            
        def set_CCCenter(self, CCCenter):
            self.CCCenter = CCCenter
            
        def set_CCRadius(self, CCRadius):
            self.CCRadius = CCRadius
            
        def setActive(self, active):
            self.active = active
            
        def setReconstructionMode(self, mode):
            self.reconstructionMode = mode

        def reconholo(self, image, PSFpara, N_subroi=1024, pixelsize=1e-3, dz=50e-3):
            if self.reconstructionMode == "inline":
                mimage = nip.image(np.sqrt(image.copy()))
                mimage = nip.extract(mimage, [N_subroi,N_subroi])
                mimage.pixelsize=(pixelsize, pixelsize)
                mpupil = nip.ft(mimage)         
                #nip.__make_propagator__(mpupil, PSFpara, doDampPupil=True, shape=mpupil.shape, distZ=dz)
                cos_alpha, sin_alpha = nip.cosSinAlpha(mimage, PSFpara)
                defocus = self.dz #  defocus factor
                PhaseMap = nip.defocusPhase(cos_alpha, defocus, PSFpara)
                propagated = nip.ft2d((np.exp(1j * PhaseMap))*mpupil)
                return np.squeeze(propagated)
            elif self.reconstructionMode == "offaxis" and self.CCCenter is not None:
                mimage = np.sqrt(nip.image(image.copy()))  # get e-field
                mpupil = nip.ft(mimage)             # bring to FT space
                mpupil = nip.extract(mpupil, (int(self.CCCenter[0]), int(self.CCCenter[1])), (int(self.CCRadius),int(self.CCRadius)), checkComplex=False) # cut out CC-term
                mimage = nip.ift(mpupil)            # bring back to image space
                return np.squeeze(mimage)           # this is still complex
            else:
                return np.zeros_like(image)
                
        def computeHoloImage(self, mHologram):
            """ Compute Holo of an image. """
            self.isBusy = True
            try:
                holorecon = np.flip(self.reconholo(mHologram, PSFpara=self.PSFpara, N_subroi=1024, pixelsize=self.pixelsize, dz=self.dz),1)
                
                self.sigHoloImageComputed.emit(np.array(holorecon), "Hologram")
                if self.reconstructionMode == "offaxis":
                    mFT = nip.ft2d(mHologram)
                    self.sigHoloImageComputed.emit(np.array(np.log(1+mFT)), "FFT")
            except Exception as e:
                self._logger.error(f"Error in computeHoloImage: {e}")
            self.isBusy = False
                
        def prepareForNewImage(self, image):
            """ Must always be called before the worker receives a new image. """
            self._image = image
            if self.active and not self.isBusy:
                self.isBusy = True
                mThread = threading.Thread(target=self.computeHoloImage, args=(self._image,))
                mThread.start()
                

        def set_dz(self, dz):
            self.dz = dz
        
        def set_PSFpara(self, PSFpara):
            self.PSFpara = PSFpara

        def set_pixelsize(self, pixelsize):
            self.pixelsize = pixelsize


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
