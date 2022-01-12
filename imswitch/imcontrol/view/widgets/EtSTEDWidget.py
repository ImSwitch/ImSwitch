import os
from inspect import signature

import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore

from imswitch.imcommon.model import dirtools
from imswitch.imcontrol.view import guitools
from .basewidgets import Widget

_etstedDir = os.path.join(dirtools.UserFileDirs.Root, 'imcontrol_etsted')


class EtSTEDWidget(Widget):
    """ Widget for controlling the etSTED implementation. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.analysisDir = os.path.join(_etstedDir, 'analysis_pipelines')
        self.transformDir = os.path.join(_etstedDir, 'transform_pipelines')
        
        if not os.path.exists(self.analysisDir):
            os.makedirs(self.analysisDir)

        if not os.path.exists(self.transformDir):
            os.makedirs(self.transformDir)
        
        # add all available analysis pipelines to the dropdown list
        self.analysisPipelines = list()
        self.analysisPipelinePar = QtGui.QComboBox()
        for pipeline in os.listdir(self.analysisDir):
            if os.path.isfile(os.path.join(self.analysisDir, pipeline)):
                pipeline = pipeline.split('.')[0]
                self.analysisPipelines.append(pipeline)
        
        self.analysisPipelinePar.addItems(self.analysisPipelines)
        self.analysisPipelinePar.setCurrentIndex(0)
        
        #TODO: add way to save current coordinate transform as a file that can be loaded from the list
        # add all available coordinate transformations to the dropdown list
        self.transformPipelines = list()
        self.transformPipelinePar = QtGui.QComboBox()
        for transform in os.listdir(self.transformDir):
            if os.path.isfile(os.path.join(self.transformDir, transform)):
                transform = transform.split('.')[0]
                self.transformPipelines.append(transform)
        
        self.transformPipelinePar.addItems(self.transformPipelines)
        self.transformPipelinePar.setCurrentIndex(0)

        self.param_names = list()
        self.param_edits = list()

        self.initiateButton = guitools.BetterPushButton('Initiate etSTED')
        self.initiateButton.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Expanding)
        self.loadPipelineButton = guitools.BetterPushButton('Load pipeline')
        
        self.coordTransfCalibButton = guitools.BetterPushButton('Transform calibration')
        self.recordBinaryMaskButton = guitools.BetterPushButton('Record binary mask')
        self.loadScanParametersButton = guitools.BetterPushButton('Load scan parameters')
        self.setUpdatePeriodButton = guitools.BetterPushButton('Set update period')
        self.setBusyFalseButton = guitools.BetterPushButton('Unlock softlock')

        self.endlessScanCheck = QtGui.QCheckBox('Endless')
        self.visualizeCheck = QtGui.QCheckBox('Visualize')
        self.validateCheck = QtGui.QCheckBox('Validate')
        self.timelapseScanCheck = QtGui.QCheckBox('Timelapse scan')

        self.bin_thresh_label = QtGui.QLabel('Bin. threshold')
        self.bin_thresh_label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom)
        self.bin_thresh_edit = QtGui.QLineEdit(str(9))
        self.bin_smooth_label = QtGui.QLabel('Bin. smooth (px)')
        self.bin_smooth_label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom)
        self.bin_smooth_edit = QtGui.QLineEdit(str(2))
        self.timelapse_reps_label = QtGui.QLabel('Timelapse frames')
        self.timelapse_reps_label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom)
        self.timelapse_reps_edit = QtGui.QLineEdit(str(1))
        self.throw_delay_label = QtGui.QLabel('Throw delay (us)')
        self.throw_delay_label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom)
        self.throw_delay_edit = QtGui.QLineEdit(str(30))
        self.update_period_label = QtGui.QLabel('Update period (ms)')
        self.update_period_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignBottom)
        self.update_period_edit = QtGui.QLineEdit(str(100))

        # help widget for coordinate transform
        self.coordTransformWidget = CoordTransformWidget(*args, **kwargs)

        # help widget for showing images from the analysis pipelines, i.e. binary masks or analysed images in live
        self.analysisHelpWidget = AnalysisWidget(*args, **kwargs)

        self.grid = QtGui.QGridLayout()
        self.setLayout(self.grid)
    

        # initialize widget controls
        currentRow = 0

        # add general buttons to grid
        self.grid.addWidget(self.initiateButton, currentRow, 0)
        self.grid.addWidget(self.endlessScanCheck, currentRow, 1)
        self.grid.addWidget(self.visualizeCheck, currentRow, 2)
        self.grid.addWidget(self.validateCheck, currentRow, 3)
        self.grid.addWidget(self.loadScanParametersButton, currentRow, 4)
        self.grid.addWidget(self.recordBinaryMaskButton, currentRow, 5)
        self.grid.addWidget(self.setBusyFalseButton, currentRow, 6)
        
        currentRow += 2

        # add image and pixel size parameters to grid
        # add param name and param to grid
        self.grid.addWidget(self.throw_delay_label, currentRow-1, 1)
        self.grid.addWidget(self.timelapseScanCheck, currentRow-1, 2)
        self.grid.addWidget(self.timelapse_reps_label, currentRow-1, 3)
        self.grid.addWidget(self.bin_thresh_label, currentRow-1, 4)
        self.grid.addWidget(self.bin_smooth_label, currentRow-1, 5)
        self.grid.addWidget(self.throw_delay_edit, currentRow, 1)
        self.grid.addWidget(self.timelapse_reps_edit, currentRow, 3)
        self.grid.addWidget(self.bin_thresh_edit, currentRow, 4)
        self.grid.addWidget(self.bin_smooth_edit, currentRow, 5)

        currentRow += 1

        self.grid.addWidget(self.loadPipelineButton, currentRow, 0)
        self.grid.addWidget(self.analysisPipelinePar, currentRow, 1)
        self.grid.addWidget(self.transformPipelinePar, currentRow, 2)
        self.grid.addWidget(self.coordTransfCalibButton, currentRow, 3)
        self.grid.addWidget(self.setUpdatePeriodButton, currentRow, 5)
        self.grid.addWidget(self.update_period_label, currentRow+1, 4)
        self.grid.addWidget(self.update_period_edit, currentRow+1, 5)


    def initParamFields(self, parameters: dict):
        """ Initialized etSTED widget parameter fields. """
        # remove previous parameter fields for the previously loaded pipeline
        for param in self.param_names:
            self.grid.removeWidget(param)
        for param in self.param_edits:
            self.grid.removeWidget(param)

        # initiate parameter fields for all the parameters in the pipeline chosen
        currentRow = 4
        
        self.param_names = list()
        self.param_edits = list()
        for pipeline_param_name, pipeline_param_val in parameters.items():
            if pipeline_param_name != 'img' and pipeline_param_name != 'bkg' and pipeline_param_name != 'binary_mask' and pipeline_param_name != 'testmode':
                # create param for input
                param_name = QtGui.QLabel('{}'.format(pipeline_param_name))
                param_value = pipeline_param_val.default if pipeline_param_val.default is not pipeline_param_val.empty else 0
                param_edit = QtGui.QLineEdit(str(param_value))
                # add param name and param to grid
                self.grid.addWidget(param_name, currentRow, 0)
                self.grid.addWidget(param_edit, currentRow, 1)
                # add param name and param to object list of temp widgets
                self.param_names.append(param_name)
                self.param_edits.append(param_edit)

                currentRow += 1

    def launchHelpWidget(self, widget, init=True):
        """ Launch the help widget. """
        if init:
            widget.show()
        else:
            widget.hide()


class AnalysisWidget(Widget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.imgVbWidget = pg.GraphicsLayoutWidget()
        self.imgVb = self.imgVbWidget.addViewBox(row=1, col=1)

        self.img = pg.ImageItem(axisOrder = 'row-major')
        self.img.translate(-0.5, -0.5)

        self.imgVb.addItem(self.img)
        self.imgVb.setAspectLocked(True)

        self.info_label = QtGui.QLabel('<image info>')
        
        self.grid = QtGui.QGridLayout()
        self.setLayout(self.grid)
        self.grid.addWidget(self.info_label, 0, 0)
        self.grid.addWidget(self.imgVbWidget, 1, 0)



class CoordTransformWidget(Widget):
    """ Pop-up widget for the coordinate transform between the two etSTED modalities. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.loadLoResButton = guitools.BetterPushButton('Load low-res calibration image')
        self.loadHiResButton = guitools.BetterPushButton('Load high-res calibration image')
        self.saveCalibButton = guitools.BetterPushButton('Save calibration')
        self.resetCoordsButton = guitools.BetterPushButton('Reset coordinates')

        self.loResVbWidget = pg.GraphicsLayoutWidget()
        self.hiResVbWidget = pg.GraphicsLayoutWidget()
        self.loResVb = self.loResVbWidget.addViewBox(row=1, col=1)
        self.hiResVb = self.hiResVbWidget.addViewBox(row=1, col=1)

        self.loResImg = pg.ImageItem(axisOrder = 'row-major')
        self.hiResImg = pg.ImageItem(axisOrder = 'row-major')
        self.loResImg.translate(-0.5, -0.5)
        self.hiResImg.translate(-0.5, -0.5)

        self.loResVb.addItem(self.loResImg)
        self.hiResVb.addItem(self.hiResImg)
        self.loResVb.setAspectLocked(True)
        self.hiResVb.setAspectLocked(True)

        self.loResScatterPlot = pg.ScatterPlotItem()
        self.hiResScatterPlot = pg.ScatterPlotItem()
        self.transformScatterPlot = pg.ScatterPlotItem()
        self.loResScatterPlot.setData
        self.hiResScatterPlot.setData
        self.transformScatterPlot.setData
        self.loResVb.addItem(self.loResScatterPlot)
        self.hiResVb.addItem(self.hiResScatterPlot)
        self.hiResVb.addItem(self.transformScatterPlot)

        self.grid = QtGui.QGridLayout()
        self.setLayout(self.grid)
    
        # initialize the controls for the coordinate transform help widget
        currentRow = 0
        self.grid.addWidget(self.loadLoResButton, currentRow, 0)
        self.grid.addWidget(self.loadHiResButton, currentRow, 1)
        
        currentRow += 1
        self.grid.addWidget(self.loResVbWidget, currentRow, 0)
        self.grid.addWidget(self.hiResVbWidget, currentRow, 1)

        currentRow += 1
        self.grid.addWidget(self.saveCalibButton, currentRow, 0)
        self.grid.addWidget(self.resetCoordsButton, currentRow, 1)

