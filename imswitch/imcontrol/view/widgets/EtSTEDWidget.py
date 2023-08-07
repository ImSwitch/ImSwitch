from pathlib import Path
from inspect import signature
from imswitch.imcommon.model import initLogger

import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore

from imswitch.imcommon.model import dirtools
from imswitch.imcontrol.view import guitools
from imswitch.imcommon.view.guitools import naparitools
from .basewidgets import Widget, NapariHybridWidget

_etstedDir: Path = dirtools.UserConfigFileDirs.Root / 'imcontrol_etsted'


class EtSTEDWidget(Widget):
    """ Widget for controlling the etSTED implementation. """

    def __init__(self, *args, **kwargs):
        self.__logger = initLogger(self, instanceName='EtSTEDWidget')
        super().__init__(*args, **kwargs)

        self.analysisDir = _etstedDir / 'analysis_pipelines'
        self.transformDir = _etstedDir / 'transform_pipelines'

        if not self.analysisDir.exists():
            self.analysisDir.mkdir(parents=True)

        if not self.transformDir.exists():
            self.transformDir.mkdir(parents=True)

        # add scatterplot to napari imageviewer to plot the detected coordinates
        self.eventScatterPlot = naparitools.VispyScatterVisual(color='red', symbol='x')
        self.eventScatterPlot.hide()

        # add all available analysis pipelines to the dropdown list
        self.analysisPipelines = list()
        self.analysisPipelinePar = QtGui.QComboBox()
        for pipeline in self.analysisDir.iterdir():
            if (self.analysisDir / pipeline).is_file():
                pipeline = str(pipeline).split('.')[0]
                self.analysisPipelines.append(pipeline)

        self.analysisPipelinePar.addItems(self.analysisPipelines)
        self.analysisPipelinePar.setCurrentIndex(0)

        self.__paramsExclude = ['img', 'prev_frames', 'binary_mask', 'exinfo', 'testmode']

        #TODO: add way to save current coordinate transform as a file that can be loaded from the list
        # add all available coordinate transformations to the dropdown list
        self.transformPipelines = list()
        self.transformPipelinePar = QtGui.QComboBox()
        for transform in self.transformDir.iterdir():
            if (self.transformDir / transform).is_file():
                transform = str(transform).split('.')[0]
                self.transformPipelines.append(transform)

        self.transformPipelinePar.addItems(self.transformPipelines)
        self.transformPipelinePar.setCurrentIndex(0)

        # add all forAcquisition detectors in a dropdown list, for being the fastImgDetector (widefield)
        self.fastImgDetectors = list()
        self.fastImgDetectorsPar = QtGui.QComboBox()
        self.fastImgDetectorsPar_label = QtGui.QLabel('Fast detector')
        self.fastImgDetectorsPar_label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom)
        # add all lasers in a dropdown list, for being the fastImgLaser (widefield)
        self.fastImgLasers = list()
        self.fastImgLasersPar = QtGui.QComboBox()
        self.fastImgLasersPar_label = QtGui.QLabel('Fast laser')
        self.fastImgLasersPar_label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom)
        # add all experiment modes in a dropdown list
        self.experimentModes = ['Experiment','TestVisualize','TestValidate']
        self.experimentModesPar = QtGui.QComboBox()
        self.experimentModesPar_label = QtGui.QLabel('Experiment mode')
        self.experimentModesPar_label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignCenter)
        self.experimentModesPar.addItems(self.experimentModes)
        self.experimentModesPar.setCurrentIndex(0)
        # add dropdown list for the type of recording I want to perform (pure scanWidget or recordingManager for timelapses with defined frequency)
        self.scanInitiation = list()
        self.scanInitiationPar = QtGui.QComboBox()
        self.scanInitiationPar_label = QtGui.QLabel('Scan type')
        self.scanInitiationPar_label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom)

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

        self.bin_thresh_label = QtGui.QLabel('Bin. threshold')
        self.bin_thresh_label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom)
        self.bin_thresh_edit = QtGui.QLineEdit(str(10))
        self.bin_smooth_label = QtGui.QLabel('Bin. smooth (px)')
        self.bin_smooth_label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom)
        self.bin_smooth_edit = QtGui.QLineEdit(str(2))
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

        self.grid.addWidget(self.initiateButton, currentRow, 0)
        self.grid.addWidget(self.endlessScanCheck, currentRow, 1)
        self.grid.addWidget(self.experimentModesPar_label, currentRow, 2)
        self.grid.addWidget(self.experimentModesPar, currentRow, 3)

        currentRow += 1

        self.grid.addWidget(self.bin_smooth_label, currentRow, 0)
        self.grid.addWidget(self.bin_smooth_edit, currentRow, 1)
        self.grid.addWidget(self.bin_thresh_label, currentRow,2)
        self.grid.addWidget(self.bin_thresh_edit, currentRow, 3)

        currentRow += 1

        self.grid.addWidget(self.loadPipelineButton, currentRow, 0)
        self.grid.addWidget(self.analysisPipelinePar, currentRow, 1)
        self.grid.addWidget(self.transformPipelinePar, currentRow, 2)
        self.grid.addWidget(self.coordTransfCalibButton, currentRow, 3)

        currentRow += 1

        self.grid.addWidget(self.update_period_label, currentRow, 2)
        self.grid.addWidget(self.update_period_edit, currentRow, 3)

        currentRow += 1

        self.grid.addWidget(self.setUpdatePeriodButton, currentRow, 2)
        self.grid.addWidget(self.recordBinaryMaskButton, currentRow, 3)

        currentRow +=1

        self.grid.addWidget(self.fastImgDetectorsPar_label, currentRow, 2)
        self.grid.addWidget(self.fastImgDetectorsPar, currentRow, 3)

        currentRow += 1

        self.grid.addWidget(self.fastImgLasersPar_label, currentRow, 2)
        self.grid.addWidget(self.fastImgLasersPar, currentRow, 3)

        currentRow +=1

        self.grid.addWidget(self.scanInitiationPar_label, currentRow, 2)
        self.grid.addWidget(self.scanInitiationPar, currentRow, 3)

        currentRow +=1

        self.grid.addWidget(self.loadScanParametersButton, currentRow, 2)
        self.grid.addWidget(self.setBusyFalseButton, currentRow, 3)


    def initParamFields(self, parameters: dict):
        """ Initialized etSTED widget parameter fields. """
        # remove previous parameter fields for the previously loaded pipeline
        for param in self.param_names:
            self.grid.removeWidget(param)
            param.deleteLater()
        for param in self.param_edits:
            self.grid.removeWidget(param)
            param.deleteLater()

        # initiate parameter fields for all the parameters in the pipeline chosen
        currentRow = 4

        self.param_names = list()
        self.param_edits = list()
        for pipeline_param_name, pipeline_param_val in parameters.items():
            if pipeline_param_name not in self.__paramsExclude:
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

    def setFastDetectorList(self, detectorNames):
        """ Set combobox with available detectors to use for the fast method. """
        for detectorName, _ in detectorNames.items():
            self.fastImgDetectors.append(detectorName)
        self.fastImgDetectorsPar.addItems(self.fastImgDetectors)
        self.fastImgDetectorsPar.setCurrentIndex(0)

    def setFastLaserList(self, laserNames):
        """ Set combobox with available lasers to use for the fast method. """
        for laserName, _ in laserNames.items():
            self.fastImgLasers.append(laserName)
        self.fastImgLasersPar.addItems(self.fastImgLasers)
        self.fastImgLasersPar.setCurrentIndex(0)

    def setScanInitiationList(self, initiationTypes):
        """ Set combobox with types of scan initiation to use for the scan method. """
        for initiationType in initiationTypes:
            self.scanInitiation.append(initiationType)
        self.scanInitiationPar.addItems(self.scanInitiation)
        self.scanInitiationPar.setCurrentIndex(0)

    def setEventScatterData(self, x, y):
        """ Updates scatter plot of detected coordinates with new data. """
        self.eventScatterPlot.setData(x=x, y=y)

    def setEventScatterVisible(self, visible):
        """ Updates visibility of scatter plot. """
        pass
        #self.eventScatterPlot.setVisible(visible)

    def getEventScatterPlot(self):
        return self.eventScatterPlot

    def launchHelpWidget(self, widget, init=True):
        """ Launch the help widget. """
        if init:
            widget.show()
        else:
            widget.hide()


class AnalysisWidget(Widget):
    """ Pop-up widget for the live analysis images or binary masks. """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.imgVbWidget = pg.GraphicsLayoutWidget()
        self.imgVb = self.imgVbWidget.addViewBox(row=1, col=1)

        self.img = pg.ImageItem(axisOrder = 'row-major')
        self.img.translate(-0.5, -0.5)

        self.scatter = pg.ScatterPlotItem()

        self.imgVb.addItem(self.img)
        self.imgVb.setAspectLocked(True)
        self.imgVb.addItem(self.scatter)

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

        self.napariViewerLo = naparitools.EmbeddedNapari()
        self.napariViewerHi = naparitools.EmbeddedNapari()

        # add points layers to the viewer
        self.pointsLayerLo = self.napariViewerLo.add_points(name="lo_points", symbol='ring', size=20, face_color='green', edge_color='green')
        self.pointsLayerTransf = self.napariViewerHi.add_points(name="transf_points", symbol='cross', size=20, face_color='red', edge_color='red')
        self.pointsLayerHi = self.napariViewerHi.add_points(name="hi_points", symbol='ring', size=20, face_color='green', edge_color='green')

        self.grid = QtGui.QGridLayout()
        self.setLayout(self.grid)

        # initialize the controls for the coordinate transform help widget
        currentRow = 0
        self.grid.addWidget(self.loadLoResButton, currentRow, 0)
        self.grid.addWidget(self.loadHiResButton, currentRow, 1)

        currentRow += 1
        self.grid.addWidget(self.napariViewerLo.get_widget(), currentRow, 0)
        self.grid.addWidget(self.napariViewerHi.get_widget(), currentRow, 1)

        currentRow += 1
        self.grid.addWidget(self.saveCalibButton, currentRow, 0)
        self.grid.addWidget(self.resetCoordsButton, currentRow, 1)
