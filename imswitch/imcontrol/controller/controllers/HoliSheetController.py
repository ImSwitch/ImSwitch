import numpy as np
import NanoImagingPack as nip
import time
import threading
import pyqtgraph.ptime as ptime

from imswitch.imcommon.framework import Signal, Thread, Worker, Mutex
from imswitch.imcontrol.view import guitools
from imswitch.imcommon.model import initLogger
from ..basecontrollers import LiveUpdatedController


class HoliSheetController(LiveUpdatedController):
    """ Linked to HoliSheetWidget."""

    sigImageReceived = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._logger = initLogger(self, tryInheritParent=False)
        
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
        
        # Parameters for monitoring the pressure
        self.T_measure = 0.1 # sampling rate of measure pressure
        self.is_measure = True
        self.pressure = 0
        self.buffer = 40
        self.currPoint = 0
        self.setPointData = np.zeros(self.buffer)
        self.timeData = np.zeros(self.buffer)
        self.startTime = ptime.time()
        
        # Motor properties
        self.speedPump = .01 # steps/s
        self.speedRotation = .01 # steps/s
        self.stepsPerRotation = 200*32 # for microstepping
        self.tRoundtripRotation = self.stepsPerRotation/self.speedRotation

        # Prepare image computation worker
        self.imageComputationWorker = self.HoliSheetImageComputationWorker()
        self.imageComputationWorker.set_pixelsize(self.pixelsize)
        self.imageComputationWorker.set_dz(self.dz)
        self.imageComputationWorker.set_PSFpara(self.PSFpara)
        self.imageComputationWorker.sigHoliSheetImageComputed.connect(self.displayImage)
   
        self.imageComputationThread = Thread()
        self.imageComputationWorker.moveToThread(self.imageComputationThread)
        self.sigImageReceived.connect(self.imageComputationWorker.computeHoliSheetImage)
        self.imageComputationThread.start()

        # Connect CommunicationChannel signals
        self._commChannel.sigUpdateImage.connect(self.update)

        # Connect HoliSheetWidget signals
        self._widget.sigShowToggled.connect(self.setShowHoliSheet)
        self._widget.sigUpdateRateChanged.connect(self.changeRate)
        self._widget.sigSliderFocusValueChanged.connect(self.valueFocusChanged)
        self._widget.sigSliderPumpSpeedValueChanged.connect(self.valuePumpSpeedChanged)
        self._widget.sigSliderRotationSpeedValueChanged.connect(self.valueRotationSpeedChanged)

        self.changeRate(self._widget.getUpdateRate())
        self.setShowHoliSheet(self._widget.getShowHoliSheetChecked())
        
        # select detectors
        allDetectorNames = self._master.detectorsManager.getAllDeviceNames()
        
        try:
            if allDetectorNames[0].lower().find("light"):
                self.detectorLightsheetName = allDetectorNames[0]
                self.detectorHoloName = allDetectorNames[1]
            else:
                self.detectorLightsheetName = allDetectorNames[1]
                self.detectorHoloName = allDetectorNames[0]
        except Exception as e:
            self._logger.debug("No camera found - in debug mode?")   
        
        # connect camera and stage
        #self.camera = self._setupInfo.autofocus.camera
        #self._master.detectorsManager[self.camera].startAcquisition()
        self.positionerName = self._master.positionersManager.getAllDeviceNames()[0]
        self.positioner = self._master.positionersManager[self.positionerName]

        # Connect buttons
        self._widget.snapRotationButton.clicked.connect(self.captureFullRotation)
        # start measurment thread (pressure)
        self.start_measurement_thread()
        
    def valueFocusChanged(self, magnitude):
        """ Change magnitude. """
        self.dz = magnitude*1e-3
        self.imageComputationWorker.set_dz(self.dz)

    def valuePumpSpeedChanged(self, value):
        """ Change magnitude. """
        self.speedPump = int(value)
        self._widget.updatePumpPressure(self.speedPump)
        self.positioner.moveForever(speed=(self.speedPump,self.speedRotation,0),is_stop=False)

    def valueRotationSpeedChanged(self, value):
        """ Change magnitude. """
        self.speedRotation = int(value)
        self._widget.updateRotationSpeed(self.speedPump)
        self.tRoundtripRotation = self.stepsPerRotation/(0.001+self.speedRotation) # in s        
        self.positioner.moveForever(speed=(self.speedPump,self.speedRotation,0),is_stop=False)

    def __del__(self):
        self.imageComputationThread.quit()
        self.imageComputationThread.wait()        
        if hasattr(super(), '__del__'):
            super().__del__()

    def setShowHoliSheet(self, enabled):
        """ Show or hide HoliSheet. """
        self.pixelsize = self._widget.getPixelSize()
        self.mWavelength = self._widget.getWvl()
        self.NA = self._widget.getNA()
        self.k0 = 2 * np.pi / (self.mWavelength)
        self.active = enabled
        self.init = False
        
    def captureFullRotation(self):
        # TODO: Here we want to capture frames and display that in Napari?
        # TODO: better do recording not single frame acquisition?
        tstart = time.time()
        self.framesRoundtrip = []
        camera = self._master.detectorsManager[self.detectorLightsheetName]
        while((time.time()-tstart)<self.tRoundtripRotation):
            self.framesRoundtrip.append(camera.getLatestFrame())
        return self.framesRoundtrip # after that comes image procesing - how?

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
        
    def updateSetPointData(self):
        if self.currPoint < self.buffer:
            self.setPointData[self.currPoint] = self.pressure
            self.timeData[self.currPoint] = ptime.time() - self.startTime
        else:
            self.setPointData[:-1] = self.setPointData[1:]
            self.setPointData[-1] = self.pressure
            self.timeData[:-1] = self.timeData[1:]
            self.timeData[-1] = ptime.time() - self.startTime
        self.currPoint += 1
    
    def measurement_grabber(self):
        while(self.is_measure):
            try:
                self.pressure = self.positioner.measure(sensorID=0)
                #self._logger.debug("Pressure is: "+str(self.pressure))
                self._widget.updatePumpPressure(self.pressure)
            except Exception as e:
                self._logger.error(e)
            time.sleep(self.T_measure)
            
            
            # update plot
            self.updateSetPointData()
            if self.currPoint < self.buffer:
                self._widget.pressurePlotCurve.setData(self.timeData[1:self.currPoint],
                                                self.setPointData[1:self.currPoint])
            else:
                self._widget.pressurePlotCurve.setData(self.timeData, self.setPointData)


    def start_measurement_thread(self):
        self.measurement_thread = threading.Thread(target=self.measurement_grabber, args=())
        self.measurement_thread.start()
            
            
    class HoliSheetImageComputationWorker(Worker):
        sigHoliSheetImageComputed = Signal(np.ndarray)

        def __init__(self):
            super().__init__()
            
            self._logger = initLogger(self, tryInheritParent=False)
            self._numQueuedImages = 0
            self._numQueuedImagesMutex = Mutex()
            self.PSFpara = None
            self.pixelsize = 1
            self.dz = 1


        def reconHoliSheet(self, image, PSFpara, N_subroi=1024, pixelsize=1e-3, dz=50e-3):
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

        def computeHoliSheetImage(self):
            """ Compute HoliSheet of an image. """
            try:
                if self._numQueuedImages > 1:
                    return  # Skip this frame in order to catch up
                HoliSheetrecon = np.flip(np.abs(self.reconHoliSheet(self._image, PSFpara=self.PSFpara, N_subroi=1024, pixelsize=self.pixelsize, dz=self.dz)),1)
                
                self.sigHoliSheetImageComputed.emit(np.array(HoliSheetrecon))
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
