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


import numpy as np
try:
    import microEye
    isMicroEye = True
except:
    isMicroEye = False

if isMicroEye:
    from microEye.Filters import BandpassFilter
    from microEye.fitting.fit import CV_BlobDetector
    from microEye.fitting.results import FittingMethod
    from microEye.fitting.fit import localize_frame


class STORMReconController(LiveUpdatedController):
    """ Linked to STORMReconWidget."""

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
        self.imageComputationWorker = self.STORMReconImageComputationWorker()
        self.imageComputationWorker.set_pixelsize(self.pixelsize)
        self.imageComputationWorker.set_dz(self.dz)
        self.imageComputationWorker.set_PSFpara(self.PSFpara)
        self.imageComputationWorker.sigSTORMReconImageComputed.connect(self.displayImage)
        if isMicroEye:
            self.imageComputationThread = Thread()
            self.imageComputationWorker.moveToThread(self.imageComputationThread)
            self.sigImageReceived.connect(self.imageComputationWorker.computeSTORMReconImage)
            self.imageComputationThread.start()

            # Connect CommunicationChannel signals
            self._commChannel.sigUpdateImage.connect(self.update)

            # Connect STORMReconWidget signals
            self._widget.sigShowToggled.connect(self.setShowSTORMRecon)
            self._widget.sigUpdateRateChanged.connect(self.changeRate)
            self._widget.sigSliderValueChanged.connect(self.valueChanged)

            self.changeRate(self._widget.getUpdateRate())
            self.setShowSTORMRecon(self._widget.getShowSTORMReconChecked())
            
            # setup reconstructor
            self.peakDetector = CV_BlobDetector()
            self.preFilter = BandpassFilter()
            
            self.imageComputationWorker.set_peakDetector(self.peakDetector)
            self.imageComputationWorker.set_preFilter(self.preFilter)

    def valueChanged(self, magnitude):
        """ Change magnitude. """
        self.dz = magnitude*1e-3
        self.imageComputationWorker.set_dz(self.dz)

    def __del__(self):
        self.imageComputationThread.quit()
        self.imageComputationThread.wait()
        if hasattr(super(), '__del__'):
            super().__del__()

    def setShowSTORMRecon(self, enabled):
        """ Show or hide STORMRecon. """
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

    class STORMReconImageComputationWorker(Worker):
        sigSTORMReconImageComputed = Signal(np.ndarray)

        def __init__(self):
            super().__init__()
            
            self._logger = initLogger(self, tryInheritParent=False)
            self._numQueuedImages = 0
            self._numQueuedImagesMutex = Mutex()
            self.PSFpara = None
            self.pixelsize = 1
            self.dz = 1


        def reconSTORMFrame(self, frame):
            # tune parameters
            
            index = 1
            filtered = None # nip.gaussf(frame, 1.5)
            varim = None


            # localize  frame 
            # params = > x,y,background, max(0, intensity), magnitudeX / magnitudeY
            frames, params, crlbs, loglike = localize_frame(
                        index,
                        frame,
                        filtered,
                        varim,
                        self.preFilter,
                        self.peakDetector,
                        rel_threshold=0.4,
                        PSFparam=np.array([1.5]),
                        roiSize=13,
                        method=FittingMethod._2D_Phasor_CPU)

            # create a simple render
            frameLocalized = np.zeros(frame.shape)
            try:
                allX = np.int(params[0])
                allY = np.int(params[1])
                frameLocalized[allY, allX] = 1
            except:
                pass


            return frameLocalized

        def computeSTORMReconImage(self):
            """ Compute STORMRecon of an image. """
            try:
                if self._numQueuedImages > 1:
                    return  # Skip this frame in order to catch up
                #STORMReconrecon = self.reconSTORMFrame(self._image)
                #self.sigSTORMReconImageComputed.emit(np.array(STORMReconrecon))
            finally:
                self._numQueuedImagesMutex.lock()
                self._numQueuedImages -= 1
                self._numQueuedImagesMutex.unlock()

        def prepareForNewImage(self, image):
            """ Must always be called before the worker receives a new image. """
            self._image = image
            self.STORMReconrecon = self.reconSTORMFrame(self._image)
            self._numQueuedImagesMutex.lock()
            self._numQueuedImages += 1
            self._numQueuedImagesMutex.unlock()

        def set_dz(self, dz):
            self.dz = dz
        
        def set_PSFpara(self, PSFpara):
            self.PSFpara = PSFpara

        def set_pixelsize(self, pixelsize):
            self.pixelsize = pixelsize
            
        def set_preFilter(self, preFilter):
            self.preFilter = preFilter
            
        def set_peakDetector(self, peakDetector):
            self.peakDetector = peakDetector


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
