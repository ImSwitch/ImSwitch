import numpy as np
import tifffile as tif
import os
from datetime import datetime

from imswitch.imcommon.framework import Signal, Thread, Worker, Mutex
from imswitch.imcontrol.view import guitools
from imswitch.imcommon.model import initLogger, dirtools
from ..basecontrollers import LiveUpdatedController


import numpy as np
try:
    import microEye
    isMicroEye = True         
    from microEye.Filters import BandpassFilter
    from microEye.fitting.fit import CV_BlobDetector
    from microEye.fitting.results import FittingMethod
    from microEye.fitting.fit import localize_frame
  
except:
    isMicroEye = False


class STORMReconController(LiveUpdatedController):
    """ Linked to STORMReconWidget."""

    sigImageReceived = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.updateRate = 0
        self.it = 0
        self.showPos = False

        # reconstruction related settings
        #TODO: Make parameters adaptable from Plugin
        # Prepare image computation worker
        self.imageComputationWorker = self.STORMReconImageComputationWorker()
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

            self.changeRate(self.updateRate)
            self.setShowSTORMRecon(self._widget.getShowSTORMReconChecked())
            
            # setup reconstructor
            self.peakDetector = CV_BlobDetector()
            self.preFilter = BandpassFilter()

            self.imageComputationWorker.setDetector(self.peakDetector)
            self.imageComputationWorker.setFilter(self.preFilter)

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
        
        # read parameters from GUI for reconstruction the data on the fly
        filter = self._widget.image_filter.currentData().filter
        tempEnabled = self._widget.tempMedianFilter.enabled.isChecked()
        detector = self._widget.detection_method.currentData().detector

        # write parameters to worker
        self.imageComputationWorker.setFilter(filter)
        self.imageComputationWorker.setTempEnabled(tempEnabled)
        self.imageComputationWorker.setDetector(detector)
        
        # this will activate/deactivate the live reconstruction
        self.active = enabled
        
        # if it will be deactivated, trigger an image-save operation
        if not self.active:
            self.imageComputationWorker.saveImage()

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
            
            self.sumReconstruction = None


        def reconSTORMFrame(self, frame, preFilter, peakDetector,
                            rel_threshold=0.4, PSFparam=np.array([1.5]), 
                            roiSize=13, method=FittingMethod._2D_Phasor_CPU):
            # tune parameters
            
            # parameters are read only once the SMLM reconstruction is initiated
            # cannot be altered during recroding
            
            index = 1
            filtered = filtered = frame.copy() # nip.gaussf(frame, 1.5)
            varim = None

            # localize  frame 
            # params = > x,y,background, max(0, intensity), magnitudeX / magnitudeY
            frames, params, crlbs, loglike = localize_frame(
                        index,
                        frame,
                        filtered,
                        varim,
                        preFilter,
                        peakDetector,
                        rel_threshold,
                        PSFparam,
                        roiSize,
                        method)

            # create a simple render
            frameLocalized = np.zeros(frame.shape)
            try:
                allX = np.int32(params[:,0])
                allY = np.int32(params[:,1])
                frameLocalized[(allY, allX)] = 1
            except Exception as e:
                pass

            return frameLocalized

        def computeSTORMReconImage(self):
            """ Compute STORMRecon of an image. """
            try:
                if self._numQueuedImages > 1:
                    return  # Skip this frame in order to catch up
                STORMReconrecon = self.reconSTORMFrame(self._image, self.preFilter, self.peakDetector)
                if self.sumReconstruction is None:
                    self.sumReconstruction = STORMReconrecon
                else:
                    self.sumReconstruction += STORMReconrecon
                #self.sigSTORMReconImageComputed.emit(np.array(STORMReconrecon))
                self.sigSTORMReconImageComputed.emit(np.array(self.sumReconstruction))
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

        def setFilter(self, filter):
            self.preFilter = filter
        
        def setTempEnabled(self, tempEnabled):
            self.tempEnabled = tempEnabled
            
        def setDetector(self, detector):
            self.peakDetector = detector
            
        def saveImage(self, filename="STORMRecon", fileExtension="tif"):
            if self.sumReconstruction is None:
                return
            time = datetime.now().strftime("%Y_%m_%d-%I-%M-%S_%p")            
            filePath = self.getSaveFilePath(date=time, 
                                timestamp=0,
                                filename=filename, 
                                extension=fileExtension)
            
            # self.switchOffIllumination()
            self._logger.debug(filePath)
            tif.imwrite(filePath, self.sumReconstruction, append=False)
            self.sumReconstruction = None
            
        def getSaveFilePath(self, date, timestamp, filename, extension):
            mFilename =  f"{date}_{filename}.{extension}"
            dirPath  = os.path.join(dirtools.UserFileDirs.Root, 'recordings', date, "t"+str(timestamp))

            newPath = os.path.join(dirPath,mFilename)

            if not os.path.exists(dirPath):
                os.makedirs(dirPath)

            return newPath

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
