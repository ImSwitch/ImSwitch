from typing import List, Union

import os
import sys
import ctypes
import importlib
import enum
import h5py

from collections import deque
from datetime import datetime
from inspect import signature
from wsgiref import validate
from scipy.optimize import least_squares
import scipy.ndimage as ndi
import pyqtgraph as pg
import numpy as np
from tkinter.filedialog import askopenfilename

from imswitch.imcommon.model import APIExport
from imswitch.imcontrol.model import configfiletools
from imswitch.imcommon.model import dirtools
from imswitch.imcontrol.view import guitools
from ..basecontrollers import ImConWidgetController
from imswitch.imcommon.model import initLogger

_logsDir = os.path.join(dirtools.UserFileDirs.Root, 'recordings', 'logs_etsted')


# HIGH-RES TIMING FUNCTIONS FROM https://stackoverflow.com/questions/38319606/how-can-i-get-millisecond-and-microsecond-resolution-timestamps-in-python/38319607#38319607
def micros():
    "return a timestamp in microseconds (us)"
    tics = ctypes.c_int64()
    freq = ctypes.c_int64()

    #get ticks on the internal ~2MHz QPC clock
    ctypes.windll.Kernel32.QueryPerformanceCounter(ctypes.byref(tics)) 
    #get the actual freq. of the internal ~2MHz QPC clock
    ctypes.windll.Kernel32.QueryPerformanceFrequency(ctypes.byref(freq))  
    
    t_us = tics.value*1e6/freq.value
    return t_us
    
def millis():
    "return a timestamp in milliseconds (ms)"
    tics = ctypes.c_int64()
    freq = ctypes.c_int64()

    #get ticks on the internal ~2MHz QPC clock
    ctypes.windll.Kernel32.QueryPerformanceCounter(ctypes.byref(tics)) 
    #get the actual freq. of the internal ~2MHz QPC clock 
    ctypes.windll.Kernel32.QueryPerformanceFrequency(ctypes.byref(freq)) 
    
    t_ms = tics.value*1e3/freq.value
    return t_ms


class EtSTEDController(ImConWidgetController):
    """ Linked to EtSTEDWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if self._setupInfo.etSTED is None:
            return

        self._widget.setFastDetectorList(
            self._master.detectorsManager.execOnAll(lambda c: c.name,
                                                    condition=lambda c: c.forAcquisition)
        )

        self._widget.setFastLaserList(
            self._master.lasersManager.execOnAll(lambda c: c.name)
        )

        self.scanInitiationList = ['ScanWidget','RecordingWidget']
        self._widget.setScanInitiationList(self.scanInitiationList)

        self.__logger = initLogger(self)
        self.__logger.debug('Initializing')

        sys.path.append(self._widget.analysisDir)
        sys.path.append(self._widget.transformDir)

        # create a helper controller for the coordinate transform pop-out widget
        self.__coordTransformHelper = EtSTEDCoordTransformHelper(self, self._widget.coordTransformWidget, _logsDir)

        # Initiate coordinate transform coeffs
        self.__transformCoeffs = np.ones(20)

        # Connect EtSTEDWidget and communication channel signals
        self._widget.initiateButton.clicked.connect(self.initiate)
        self._widget.loadPipelineButton.clicked.connect(self.loadPipeline)
        self._widget.recordBinaryMaskButton.clicked.connect(self.initiateBinaryMask)
        self._widget.loadScanParametersButton.clicked.connect(self.getScanParameters)
        self._widget.setUpdatePeriodButton.clicked.connect(self.setUpdatePeriod)
        self._widget.setBusyFalseButton.clicked.connect(self.setBusyFalse)
        self._commChannel.sigSendScanParameters.connect(lambda analogParams, digitalParams, positionersScan: self.assignScanParameters(analogParams, digitalParams, positionersScan))
        self._commChannel.sigSendScanFreq.connect(lambda scanFreq: self.logScanFreq(scanFreq))

        # initiate log for each detected event
        self.resetDetLog()

        # initiate flags and params
        self.__runMode = RunMode.Experiment
        self.__running = False
        self.__validating = False
        self.__busy = False
        self.__bkg = None
        self.__prevFrames = deque(maxlen=10)
        self.__prevAnaFrames = deque(maxlen=10)
        self.__binary_mask = None
        self.__binary_stack = None
        self.__binary_frames = 10
        self.__init_frames = 5
        self.__validationFrames = 0
        self.__frame = 0
        self.t_call = 0
        self.__maxAnaImgVal = 0


    def initiate(self):
        """ Initiate or stop an etSTED experiment. """
        if not self.__running:
            detectorFastIdx = self._widget.fastImgDetectorsPar.currentIndex()
            self.detectorFast = self._widget.fastImgDetectors[detectorFastIdx]
            laserFastIdx = self._widget.fastImgLasersPar.currentIndex()
            self.laserFast = self._widget.fastImgLasers[laserFastIdx]
            scanInitiationTypeIdx = self._widget.scanInitiationPar.currentIndex()
            scanInitiationType = self._widget.scanInitiation[scanInitiationTypeIdx]
            if scanInitiationType == self.scanInitiationList[0]:
                self.scanInitiationMode = ScanInitiationMode.ScanWidget
            elif scanInitiationType == self.scanInitiationList[1]:
                self.scanInitiationMode = ScanInitiationMode.RecordingWidget

            self.__param_vals = self.readParams()
            # Reset parameter for extra information that pipelines can input and output
            self.__exinfo = None
            
            # Check if visualization mode, in case launch help widget
            experimentModeIdx = self._widget.experimentModesPar.currentIndex()
            self.experimentMode = self._widget.experimentModes[experimentModeIdx]
            if self.experimentMode == 'TestVisualize':
                self.__runMode = RunMode.Visualize
            elif self.experimentMode == 'TestValidate':
                self.__runMode = RunMode.Validate
            else:
                self.__runMode = RunMode.Experiment
            # check if visualization or validation mode
            if self.__runMode == RunMode.Validate or self.__runMode == RunMode.Visualize:
                self.launchHelpWidget()
            # load selected coordinate transform
            self.loadTransform()
            self.__transformCoeffs = self.__coordTransformHelper.getTransformCoeffs()
            # connect communication channel signals and turn on wf laser
            self._commChannel.sigUpdateImage.connect(self.runPipeline)
            if self.scanInitiationMode == ScanInitiationMode.ScanWidget:
                self._commChannel.sigToggleBlockScanWidget.emit(False)
                self._commChannel.sigScanEnded.connect(self.scanEnded)
            elif self.scanInitiationMode == ScanInitiationMode.RecordingWidget:
                self._commChannel.sigRecordingEnded.connect(self.scanEnded)
            self._master.lasersManager.execOn(self.laserFast, lambda l: l.setEnabled(True))

            #self._widget.setEventScatterVisible(True)
            self._widget.initiateButton.setText('Stop')
            self.__running = True
        else:
            # disconnect communication channel signals and turn off wf laser
            self._commChannel.sigUpdateImage.disconnect(self.runPipeline)
            if self.scanInitiationMode == ScanInitiationMode.ScanWidget:
                self._commChannel.sigToggleBlockScanWidget.emit(True)
                self._commChannel.sigScanEnded.disconnect(self.scanEnded)
            elif self.scanInitiationMode == ScanInitiationMode.RecordingWidget:
                self._commChannel.sigRecordingEnded.disconnect(self.scanEnded)
            self._master.lasersManager.execOn(self.laserFast, lambda l: l.setEnabled(False))

            #self._widget.setEventScatterVisible(False)
            self._widget.initiateButton.setText('Initiate')
            self.resetParamVals()
            self.resetRunParams()

    def scanEnded(self):
        """ End an etSTED slow method scan. """
        self.setDetLogLine("scan_end",datetime.now().strftime('%Ss%fus'))
        if self.scanInitiationMode == ScanInitiationMode.ScanWidget:
            self._commChannel.sigSnapImg.emit()
            frame_period = self.scanInfoDict['scan_samples_frame'] * 10e-6  # length (s) of total scan signal
            self.setDetLogLine("frame_period", frame_period)
        self.endRecording()
        self.continueFastModality()
        self.__frame = 0

    def setDetLogLine(self, key, val, *args):
        if args:
            self.__detLog[f"{key}{args[0]}"] = val
        else:
            self.__detLog[key] = val

    def runSlowScan(self):
        """ Run a scan of the slow method (STED). """
        self.__detLog[f"scan_start"] = datetime.now().strftime('%Ss%fus')
        if self.scanInitiationMode == ScanInitiationMode.ScanWidget:
            # Run scan in nidaqManager
            self._master.nidaqManager.runScan(self.signalDic, self.scanInfoDict)
        elif self.scanInitiationMode == ScanInitiationMode.RecordingWidget:
            # Run recording from RecWidget
            self.triggerRecordingWidgetScan()

    def endRecording(self):
        """ Save an etSTED slow method scan. """
        self.setDetLogLine("pipeline", self.getPipelineName())
        self.logPipelineParamVals()
        # save log file with temporal info of trigger event
        filename = datetime.utcnow().strftime('%Hh%Mm%Ss%fus')
        name = os.path.join(_logsDir, filename) + '_log'
        log = [f'{key}: {self.__detLog[key]}' for key in self.__detLog]
        with open(f'{name}.txt', 'w') as f:
            [f.write(f'{st}\n') for st in log]
        self.resetDetLog()

    def getTransformName(self):
        """ Get the name of the pipeline currently used. """
        transformidx = self._widget.transformPipelinePar.currentIndex()
        transformname = self._widget.transformPipelines[transformidx]
        return transformname

    def getPipelineName(self):
        """ Get the name of the pipeline currently used. """
        pipelineidx = self._widget.analysisPipelinePar.currentIndex()
        pipelinename = self._widget.analysisPipelines[pipelineidx]
        return pipelinename

    def logPipelineParamVals(self):
        """ Put analysis pipeline parameter values in the log file. """
        params_ignore = ['img','bkg','binary_mask','testmode','exinfo']
        param_names = list()
        for pipeline_param_name, _ in self.__pipeline_params.items():
            if pipeline_param_name not in params_ignore:
                param_names.append(pipeline_param_name)
        for key, val in zip(param_names, self.__param_vals):
            self.setDetLogLine(key, val)

    def continueFastModality(self):
        """ Continue the fast method, after an event scan has been performed. """
        if self._widget.endlessScanCheck.isChecked() and not self.__running:
            # connect communication channel signals
            self._commChannel.sigUpdateImage.connect(self.runPipeline)
            self._master.lasersManager.execOn(self.laserFast, lambda l: l.setEnabled(True))
            
            #self._widget.setEventScatterVisible(True)
            self._widget.initiateButton.setText('Stop')
            self.__running = True
        elif not self._widget.endlessScanCheck.isChecked():
            self._widget.initiateButton.setText('Initiate')
            if self.scanInitiationMode == ScanInitiationMode.ScanWidget:
                self._commChannel.sigToggleBlockScanWidget.emit(True)
                self._commChannel.sigScanEnded.disconnect(self.scanEnded)
            elif self.scanInitiationMode == ScanInitiationMode.RecordingWidget:
                self._commChannel.sigRecordingEnded.disconnect(self.scanEnded)
            self.__running = False
            self.resetParamVals()

    def loadTransform(self):
        """ Load a previously saved coordinate transform. """
        transformname = self.getTransformName()
        self.transform = getattr(importlib.import_module(f'{transformname}'), f'{transformname}')

    def loadPipeline(self):
        """ Load the selected analysis pipeline, and its parameters into the GUI. """
        self.__pipelinename = self.getPipelineName()
        self.pipeline = getattr(importlib.import_module(f'{self.__pipelinename}'), f'{self.__pipelinename}')
        self.__pipeline_params = signature(self.pipeline).parameters
        self._widget.initParamFields(self.__pipeline_params)

    def initiateBinaryMask(self):
        """ Initiate the process of calculating a binary mask of the region of interest. """
        self.__binary_stack = None
        laserFastIdx = self._widget.fastImgLasersPar.currentIndex()
        self.laserFast = self._widget.fastImgLasers[laserFastIdx]
        detectorFastIdx = self._widget.fastImgDetectorsPar.currentIndex()
        self.detectorFast = self._widget.fastImgDetectors[detectorFastIdx]
        self._master.lasersManager.execOn(self.laserFast, lambda l: l.setEnabled(True))
        self._commChannel.sigUpdateImage.connect(self.addImgBinStack)
        self._widget.recordBinaryMaskButton.setText('Recording...')

    def addImgBinStack(self, detectorName, img, init, scale, isCurrentDetector):
        """ Add image to the stack of images used to calculate a binary mask of the region of interest. """
        if detectorName == self.detectorFast:
            if self.__binary_stack is None:
                self.__binary_stack = img
            elif len(self.__binary_stack) == self.__binary_frames:
                self._commChannel.sigUpdateImage.disconnect(self.addImgBinStack)
                self._master.lasersManager.execOn(self.laserFast, lambda l: l.setEnabled(False))
                self.calculateBinaryMask(self.__binary_stack)
            else:
                if np.ndim(self.__binary_stack) == 2:
                    self.__binary_stack = np.stack((self.__binary_stack, img))
                else:
                    #self.__logger.debug(np.shape(img))
                    #self.__logger.debug(np.shape(self.__binary_stack))
                    self.__binary_stack = np.concatenate((self.__binary_stack,  [img]), axis=0)

    def calculateBinaryMask(self, img_stack):
        """ Calculate the binary mask of the region of interest. """
        img_mean = np.mean(img_stack, 0)
        img_bin = ndi.filters.gaussian_filter(img_mean, np.float(self._widget.bin_smooth_edit.text()))
        self.__binary_mask = np.array(img_bin > np.float(self._widget.bin_thresh_edit.text()))
        self._widget.recordBinaryMaskButton.setText('Record binary mask')
        self.setAnalysisHelpImg(self.__binary_mask)
        self.launchHelpWidget()

    def setAnalysisHelpImg(self, img_ana, exinfo=None):
        """ Set the preprocessed image in the analysis help widget. """
        #self._widget.analysisHelpWidget.img.setOnlyRenderVisible(True, render=False)
        if np.max(img_ana) > self.__maxAnaImgVal:
            self.__maxAnaImgVal = np.max(img_ana)
            autolevels = True
        else:
            autolevels = False
        #self.__logger.debug(autolevels)
        if img_ana.ndim == 3:
            img_ana = img_ana[0,:,:]
        #self.__logger.debug(type(img_ana))
        #self.__logger.debug(np.shape(img_ana))
        #self.__logger.debug(img_ana.dtype)
        self._widget.analysisHelpWidget.img.setImage(img_ana, autoLevels=autolevels)
        infotext = f'Min: {np.min(img_ana)}, max: {np.max(img_ana)}'
        self._widget.analysisHelpWidget.info_label.setText(infotext)

        # scatter plot exinfo if there is something (cdvesprox or dynamin)
        if exinfo is not None:
            if 'cd_vesicle_prox' in self.__pipelinename or 'dynamin' in self.__pipelinename:
                self._widget.analysisHelpWidget.scatter.setData(x=np.array(exinfo['y']), y=np.array(exinfo['x']), pen=pg.mkPen(None), brush='g', symbol='x', size=15)
            #else:
            #    self._widget.analysisHelpWidget.scatter.setData(x=[], y=[])

        #self._widget.analysisHelpWidget.img.render()

    def getScanParameters(self):
        """ Load STED scan parameters from the scanning widget. """
        self._commChannel.sigRequestScanParameters.emit()

    def setUpdatePeriod(self):
        """ Set the update period for the fast method. """
        self.__updatePeriod = int(self._widget.update_period_edit.text())
        self._master.detectorsManager.setUpdatePeriod(self.__updatePeriod)

    def setBusyFalse(self):
        self.__busy = False

    def assignScanParameters(self, analogParams, digitalParams, positionersScan):
        """ Assign scan parameters from the scanning widget. """
        self._analogParameterDict = analogParams
        self._digitalParameterDict = digitalParams
        self._positionersScan = positionersScan

    def readParams(self):
        """ Read user-provided analysis pipeline parameter values. """
        param_vals = list()
        for item in self._widget.param_edits:
            param_vals.append(np.float(item.text()))
        return param_vals

    def launchHelpWidget(self):
        """ Launch help widget that shows the preprocessed images in real-time. """
        self._widget.launchHelpWidget(self._widget.analysisHelpWidget, init=True)

    def resetDetLog(self):
        """ Reset the event log file. """
        self.__detLog = dict()
        self.__detLog = {
            "pipeline": "",
            "pipeline_start": "",
            "pipeline_end": "",
            "coord_transf_start": "",
            "fastscan_x_center": 0,
            "fastscan_y_center": 0,
            "slowscan_x_center": 0,
            "slowscan_y_center": 0
        }

    def resetParamVals(self):
        self.__param_vals = list()

    def resetRunParams(self):
        self.__running = False
        self.__validating = False
        self.__frame = 0
        self.__maxAnaImgVal = 0

    def runPipeline(self, detectorName, img, init, scale, isCurrentDetector):
        """ If detector is detectorFast: run the analyis pipeline, called after every fast method frame. """
        if detectorName == self.detectorFast:
            if not self.__busy:
                t_sincelastcall = millis() - self.t_call
                self.t_call = millis()
                self.setDetLogLine("pipeline_rep_period", str(t_sincelastcall))
                self.setDetLogLine("pipeline_start", datetime.now().strftime('%Ss%fus'))
                self.__busy = True
                t_pre = millis()
                if self.__runMode == RunMode.Visualize or self.__runMode == RunMode.Validate:
                    coords_detected, self.__exinfo, img_ana = self.pipeline(img, self.__prevFrames, self.__binary_mask, (self.__runMode==RunMode.Visualize or self.__runMode==RunMode.Validate), self.__exinfo, *self.__param_vals)
                else:
                    coords_detected, self.__exinfo = self.pipeline(img, self.__prevFrames, self.__binary_mask, self.__runMode==RunMode.Visualize, self.__exinfo, *self.__param_vals)
                t_post = millis()
                self.setDetLogLine("pipeline_end", datetime.now().strftime('%Ss%fus'))
                #self.__logger.debug(f'Pipeline time: {t_post-t_pre} ms')
                #self.__logger.debug(coords_detected)

                if self.__frame > self.__init_frames:
                    # run if the initial frames have passed
                    #self.__logger.debug(self.__runMode)
                    if self.__runMode == RunMode.Visualize:
                        self.updateScatter(coords_detected, clear=True)
                        self.setAnalysisHelpImg(img_ana, self.__exinfo)
                    elif self.__runMode == RunMode.Validate:
                        self.updateScatter(coords_detected, clear=True)
                        self.setAnalysisHelpImg(img_ana)
                        if self.__validating:
                            if self.__validationFrames > 5:
                                self.saveValidationImages(prev=True, prev_ana=True)
                                self.pauseFastModality()
                                self.endRecording()
                                self.continueFastModality()
                                self.__frame = 0
                                self.__validating = False
                            self.__validationFrames += 1
                        elif coords_detected.size != 0:
                            # if some events where detected
                            if np.size(coords_detected) > 2:
                                coords_scan = coords_detected[0,:]
                            else:
                                coords_scan = coords_detected[0]
                            # log detected center coordinate
                            self.setDetLogLine("fastscan_x_center", coords_scan[0])
                            self.setDetLogLine("fastscan_y_center", coords_scan[1])
                            # log all detected coordinates
                            if np.size(coords_detected) > 2:
                                for i in range(np.size(coords_detected,0)):
                                    self.setDetLogLine("det_coord_x_", coords_detected[i,0], i)
                                    self.setDetLogLine("det_coord_y_", coords_detected[i,1], i)
                            self.__validating = True
                            self.__validationFrames = 0
                    elif coords_detected.size != 0:
                        # if some events were detected
                        if np.size(coords_detected) > 2:
                            coords_scan = np.copy(coords_detected[0,:])
                        else:
                            coords_scan = np.copy(coords_detected[0])
                        self.setDetLogLine("prepause", datetime.now().strftime('%Ss%fus'))
                        coords_scan = np.flip(np.copy(coords_scan))
                        self.setDetLogLine("fastscan_x_center", coords_scan[0])
                        self.setDetLogLine("fastscan_y_center", coords_scan[1])
                        coords_scan[1] = np.shape(img)[0] - coords_scan[1]
                        self.pauseFastModality()
                        self.setDetLogLine("coord_transf_start", datetime.now().strftime('%Ss%fus'))
                        coords_center_scan = self.transform(coords_scan, self.__transformCoeffs)
                        self.setDetLogLine("slowscan_x_center", coords_center_scan[0])
                        self.setDetLogLine("slowscan_y_center", coords_center_scan[1])
                        self.setDetLogLine("scan_initiate", datetime.now().strftime('%Ss%fus'))
                        # save all detected coordinates in the log
                        if np.size(coords_detected) > 2:
                            for i in range(np.size(coords_detected,0)):
                                self.setDetLogLine("det_coord_x_", coords_scan[0], i)
                                self.setDetLogLine("det_coord_y_", coords_scan[1], i)
                        
                        #self.__logger.debug(coords_scan)
                        #self.__logger.debug(coords_center_scan)
                        self.initiateSlowScan(position=coords_center_scan)
                        self.runSlowScan()

                        # update scatter plot of event coordinates in the shown fast method image
                        self.updateScatter(np.flip(np.copy(coords_detected)), clear=True)

                        self.__prevFrames.append(img)
                        self.saveValidationImages(prev=True, prev_ana=False)
                        self.__exinfo = None
                        self.__busy = False
                        return
                self.__bkg = img
                self.__prevFrames.append(img)
                if self.__runMode == RunMode.Validate:
                    self.__prevAnaFrames.append(img_ana)
                self.__frame += 1
                self.setBusyFalse()

    def initiateSlowScan(self, position=[0.0,0.0,0.0]):
        """ Initiate a STED scan. """
        dt = datetime.now()
        time_curr_before = round(dt.microsecond/1000)
        self.setCenterScanParameter(position)
        dt = datetime.now()
        time_curr_mid = round(dt.microsecond/1000)
        if self.scanInitiationMode == ScanInitiationMode.ScanWidget:
            self.__logger.debug('Initiating scan with ScanWidget')
            try:
                self.signalDic, self.scanInfoDict = self._master.scanManager.makeFullScan(
                    self._analogParameterDict, self._digitalParameterDict, staticPositioner=False
                )
            except:
                self.__logger.debug('Error when initiating ScanWidget scan')
                return
        elif self.scanInitiationMode == ScanInitiationMode.RecordingWidget:
            self.__logger.debug('Initiating scan with RecordingWidget')
            self._commChannel.sigRequestScanFreq.emit()
            # Set scan axis centers in scanwidget
            self.setCentersScanWidget()
        #self.scanInfoDict['phase_delay'] = np.float(self._widget.phase_delay_edit.text())
        dt = datetime.now()
        time_curr_after = round(dt.microsecond/1000)
        print(f'Time for curve parameters: {time_curr_mid-time_curr_before} ms')
        print(f'Time for signal curve generation: {time_curr_after-time_curr_mid}')

    def setCenterScanParameter(self, position):
        """ Set the scanning center from the detected event coordinates. """
        self.__logger.debug(self._analogParameterDict)
        if self._analogParameterDict:
            for index, positionerName in enumerate(self._analogParameterDict['target_device']):
                #self.__logger.debug(positionerName)
                if positionerName != 'None':
                    if positionerName == 'ND-GalvoX':
                        center = position[0]
                        center = self.addFastAxisShift(center)
                        self._analogParameterDict['axis_centerpos'][index] = center
                    elif positionerName == 'ND-GalvoY':
                        center = position[1]
                        self._analogParameterDict['axis_centerpos'][index] = center
        self.__logger.debug(self._analogParameterDict)
        # set actual positions of scanners not in scan from centerpos (usually done in ScanController.runScanAdvanced())
        for index, positionerName in enumerate(self._analogParameterDict['target_device']):
            if positionerName not in self._positionersScan:
                position = self._analogParameterDict['axis_centerpos'][index]
                self._master.positionersManager[positionerName].setPosition(position, 0)
                self.__logger.debug(f'set {positionerName} center to {position} before scan')

    def logScanFreq(self, scanFreq):
        self.setDetLogLine("scan_period", scanFreq)

    def addFastAxisShift(self, center):
        """ Add a scanning-method and microscope-specific shift to the fast axis scanning. 
        Based on second-degree curved surface fit to 2D-sampling of dwell time and pixel size induced shifts. """
        dwell_time = float(self._analogParameterDict['sequence_time'])
        px_size = float(self._analogParameterDict['axis_step_size'][0])
        C = np.array([-5.06873628, -80.6978355, 104.06976744, -7.12113356, 8.0065076, 0.68227188])  # second order plane fit
        params = np.array([px_size**2, dwell_time**2, px_size*dwell_time, px_size, dwell_time, 1])  # for use with second order plane fit
        shift_compensation = np.sum(params*C)
        center -= shift_compensation
        return(center)

    def setCentersScanWidget(self):
        devices = []
        centers = []
        for device,center in zip(self._analogParameterDict['target_device'], self._analogParameterDict['axis_centerpos']):
            devices.append(device)
            centers.append(center)
        self._commChannel.sigSetAxisCenters.emit(devices, centers)

    def triggerRecordingWidgetScan(self):
        self._commChannel.sigStartRecordingExternal.emit()

    def updateScatter(self, coords, clear=True):
        """ Update the scatter plot of detected event coordinates. """
        if np.size(coords) > 0:
            self._widget.setEventScatterData(x=coords[:,1],y=coords[:,0])
            # possibly not the below more than one time. Maybe it is enough to then update it, if the reference to the same object is kept throughout all function calls
            self._commChannel.sigAddItemToVb.emit(self._widget.getEventScatterPlot())

    def saveValidationImages(self, prev=True, prev_ana=True):
        """ Save the widefield validation images of an event detection. """
        if prev:
            img = np.array(list(self.__prevFrames))
            self._commChannel.sigSnapImgPrev.emit(self.detectorFast, img, 'raw')
            self.__prevFrames.clear()
        if prev_ana:
            img = np.array(list(self.__prevAnaFrames))
            self._commChannel.sigSnapImgPrev.emit(self.detectorFast, img, 'ana')
            self.__prevAnaFrames.clear()

    def pauseFastModality(self):
        """ Pause the fast method, when an event has been detected. """
        if self.__running:
            self._commChannel.sigUpdateImage.disconnect(self.runPipeline)
            self._master.lasersManager.execOn(self.laserFast, lambda l: l.setEnabled(False))
            self.__running = False

    def closeEvent(self):
        pass


class EtSTEDCoordTransformHelper():
    """ Coordinate transform help widget controller. """
    def __init__(self, etSTEDController, coordTransformWidget, saveFolder, *args, **kwargs):
        
        self.__logger = initLogger(self)
        self.__logger.debug('Initializing')

        self.etSTEDController = etSTEDController
        self._widget = coordTransformWidget
        self.__saveFolder = saveFolder

        # initiate coordinate transform parameters
        self.__transformCoeffs = np.ones(20)
        self.__loResCoords = list()
        self.__hiResCoords = list()
        self.__loResCoordsPx = list()
        self.__hiResCoordsPx = list()
        self.__hiResPxSize = 1
        self.__loResPxSize = 1
        self.__hiResSize = 1

        # connect signals from widget
        etSTEDController._widget.coordTransfCalibButton.clicked.connect(self.calibrationLaunch)
        self._widget.saveCalibButton.clicked.connect(self.calibrationFinish)
        self._widget.resetCoordsButton.clicked.connect(self.resetCalibrationCoords)
        self._widget.loadLoResButton.clicked.connect(lambda: self.loadCalibImage('lo'))
        self._widget.loadHiResButton.clicked.connect(lambda: self.loadCalibImage('hi'))

    def getTransformCoeffs(self):
        """ Get transformation coefficients. """
        return self.__transformCoeffs

    def calibrationLaunch(self):
        """ Launch calibration. """
        self.etSTEDController._widget.launchHelpWidget(self.etSTEDController._widget.coordTransformWidget, init=True)

    def calibrationFinish(self):
        """ Finish calibration. """
        # get annotated coordinates in both images and translate to real space coordinates
        self.__loResCoordsPx = self._widget.pointsLayerLo.data
        for pos_px in self.__loResCoordsPx:
            #pos = (np.around(pos_px[0]*self.__loResPxSize, 3), np.around(pos_px[1]*self.__loResPxSize, 3))
            pos = (np.around(pos_px[0], 3), np.around(pos_px[1], 3))
            self.__loResCoords.append(pos)
        self.__hiResCoordsPx = self._widget.pointsLayerHi.data
        for pos_px in self.__hiResCoordsPx:
            pos = (np.around(pos_px[0]*self.__hiResPxSize - self.__hiResSize/2, 3), -1 * np.around(pos_px[1]*self.__hiResPxSize - self.__hiResSize/2, 3))
            self.__hiResCoords.append(pos)
        # calibrate coordinate transform
        self.coordinateTransformCalibrate()
        #self.__logger.debug(self.__loResCoords)
        #self.__logger.debug(self.__hiResCoords)
        #self.__logger.debug(f'Transformation coeffs: {self.__transformCoeffs}')
        name = datetime.utcnow().strftime('%Hh%Mm%Ss%fus')
        filename = os.path.join(self.__saveFolder, name) + '_transformCoeffs.txt'
        np.savetxt(fname=filename, X=self.__transformCoeffs)

        # plot the resulting transformed low-res coordinates on the hi-res image
        coords_transf = []
        for i in range(0,len(self.__loResCoords)):
            pos = self.poly_thirdorder_transform(self.__transformCoeffs, self.__loResCoords[i])
            pos_px = (np.around((pos[0] + self.__hiResSize/2)/self.__hiResPxSize, 0), np.around((-1 * pos[1] + self.__hiResSize/2)/self.__hiResPxSize, 0))
            coords_transf.append(pos_px)
        coords_transf = np.array(coords_transf)
        self._widget.pointsLayerTransf.data = coords_transf

    def resetCalibrationCoords(self):
        """ Reset all selected coordinates. """
        self.__loResCoords = list()
        self.__loResCoordsPx = list()
        self.__hiResCoords = list()
        self.__hiResCoordsPx = list()
        self._widget.pointsLayerLo.data = []
        self._widget.pointsLayerHi.data = []
        self._widget.pointsLayerTransf.data = []

    def loadCalibImage(self, modality):
        """ Load low or high resolution calibration image. """
        # open gui to choose file
        img_filename = self.openFolder()
        # load img data from file
        with h5py.File(img_filename, "r") as f:
            img_key = list(f.keys())[0]
            pixelsize = f[img_key].attrs['element_size_um'][1]
            img_data = np.array(f[img_key])
            imgsize = pixelsize*np.size(img_data,0)
        # view data in corresponding viewbox
        self.updateCalibImage(img_data, modality)
        if modality == 'hi':
            self.__hiResCoords = list()
            self.__hiResPxSize = pixelsize
            self.__hiResSize = imgsize
        elif modality == 'lo':
            self.__loResCoords = list()
            self.__loResPxSize = pixelsize

    def openFolder(self):
        """ Opens current folder in File Explorer and returns chosen filename. """
        filename = askopenfilename()
        return filename

    def updateCalibImage(self, img_data, modality):
        """ Update new image in the viewbox. """
        if modality == 'hi':
            viewer = self._widget.napariViewerHi
        elif modality == 'lo':
            viewer = self._widget.napariViewerLo
        viewer.add_image(img_data)
        viewer.layers.unselect_all()
        viewer.layers.move_selected(len(viewer.layers)-1,0)

    def coordinateTransformCalibrate(self):
        """ Third-order polynomial fitting with least-squares Levenberg-Marquart algorithm. """
        # prepare data and init guess
        c_init = np.hstack([np.zeros(10), np.zeros(10)])
        xdata = np.array([*self.__loResCoords]).astype(np.float32)
        ydata = np.array([*self.__hiResCoords]).astype(np.float32)
        initguess = c_init.astype(np.float32)
        # fit
        res_lsq = least_squares(self.poly_thirdorder, initguess, args=(xdata, ydata), method='lm')
        transformCoeffs = res_lsq.x
        self.__transformCoeffs = transformCoeffs

    def poly_thirdorder(self, a, x, y):
        """ Polynomial function that will be fit in the least-squares fit. """
        res = []
        for i in range(0, len(x)):
            c1 = x[i,0]
            c2 = x[i,1]
            x_i1 = a[0]*c1**3 + a[1]*c2**3 + a[2]*c2*c1**2 + a[3]*c1*c2**2 + a[4]*c1**2 + a[5]*c2**2 + a[6]*c1*c2 + a[7]*c1 + a[8]*c2 + a[9]
            x_i2 = a[10]*c1**3 + a[11]*c2**3 + a[12]*c2*c1**2 + a[13]*c1*c2**2 + a[14]*c1**2 + a[15]*c2**2 + a[16]*c1*c2 + a[17]*c1 + a[18]*c2 + a[19]
            res.append(x_i1 - y[i,0])
            res.append(x_i2 - y[i,1])
        return res
    
    def poly_thirdorder_transform(self, a, x):
        """ Use for plotting the least-squares fit results. """
        c1 = x[0]
        c2 = x[1]
        x_i1 = a[0]*c1**3 + a[1]*c2**3 + a[2]*c2*c1**2 + a[3]*c1*c2**2 + a[4]*c1**2 + a[5]*c2**2 + a[6]*c1*c2 + a[7]*c1 + a[8]*c2 + a[9]
        x_i2 = a[10]*c1**3 + a[11]*c2**3 + a[12]*c2*c1**2 + a[13]*c1*c2**2 + a[14]*c1**2 + a[15]*c2**2 + a[16]*c1*c2 + a[17]*c1 + a[18]*c2 + a[19]
        return (x_i1, x_i2)



class RunMode(enum.Enum):
    Experiment = 1
    Visualize = 2
    Validate = 3

class ScanInitiationMode(enum.Enum):
    ScanWidget = 1
    RecordingWidget = 2


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
