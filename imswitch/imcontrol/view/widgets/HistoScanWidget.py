import numpy as np
import pyqtgraph as pg
import cv2
import copy
from qtpy import QtCore, QtWidgets, QtGui, QtWidgets
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import QTimer, Qt, pyqtSignal, QPoint, QRect
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen, QColor
import imswitch

from PyQt5 import QtGui, QtWidgets
import PyQt5
from imswitch.imcommon.model import initLogger
from imswitch.imcontrol.view import guitools
from .basewidgets import NapariHybridWidget
import os

class ScanParameters(object):
    def __init__(self, name="Wellplate", physDimX=164, physDimY=109, physOffsetX=0, physOffsetY=0, imagePath="imswitch/_data/images/WellplateAdapter3Slides.png"):
        self.name = name
        self.physDimX = physDimX*1e3 # mm
        self.physDimY = physDimY*1e3 # mm
        self.physOffsetX = physOffsetX
        self.physOffsetY =  physOffsetY
        self.imagePath = imagePath



class HistoScanWidget(NapariHybridWidget):
    """ Widget containing HistoScan interface. """
    sigSliderIlluValueChanged = QtCore.Signal(float)  # (value)
    sigGoToPosition = QtCore.Signal(float, float)  # (posX, posY)
    sigCurrentOffset = QtCore.Signal(float, float)
    sigStageMappingComplete = QtCore.Signal(np.ndarray, np.ndarray, bool)  # (xy mapping matrix, backlash, isCalibrated)

    def __post_init__(self):
        #super().__init__(*args, **kwargs)
        self._logger = initLogger(self)
        
        self.tabWidget = QtWidgets.QTabWidget(self)
        mainWidget = QtWidgets.QWidget()  # Create a widget for the first tab
        self.grid = QtWidgets.QGridLayout(mainWidget)  # Use this widget in your grid

        # Pull-down menu for the illumination source
        self.illuminationSourceComboBox = QtWidgets.QComboBox()
        self.illuminationSourceLabel = QtWidgets.QLabel("Illumination Source:")
        self.illuminationSourceComboBox.addItems(["Laser 1", "Laser 2", "LED"])


        # Slider for setting the value for the illumination source
        self.illuminationSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.illuminationSlider.setMinimum(0)
        self.illuminationSlider.setMaximum(255)
        self.illuminationSlider.valueChanged.connect(
            lambda value: self.sigSliderIlluValueChanged.emit(value)
        )

        self.samplePicker = QtWidgets.QComboBox()


        # Pull-down menu for the stage axis
        self.stageAxisComboBox = QtWidgets.QComboBox()
        self.stageAxisLabel = QtWidgets.QLabel("Stage Axis:")
        self.stageAxisComboBox.addItems(["X", "Y", "Z", "A"])
        self.grid.addWidget(self.illuminationSourceComboBox, 3, 0, 1, 1)
        self.grid.addWidget(self.illuminationSlider, 3, 1, 1, 1)
        #self.grid.addWidget(self.stageAxisLabel, 4, 0, 1, 1)
        #self.grid.addWidget(self.stageAxisComboBox, 4, 1, 1, 1)
        self.buttonSelectPath = guitools.BetterPushButton('Select Path')
        self.buttonSelectPath.clicked.connect(self.handleSelectPath)
        self.lineeditSelectPath = QtWidgets.QLineEdit("Default Path")

        self.timeIntervalField = QtWidgets.QLineEdit()
        self.timeIntervalField.setPlaceholderText("Time Interval (s)")
        self.numberOfScansField = QtWidgets.QLineEdit()
        self.numberOfScansField.setPlaceholderText("Number of Scans")


        # Text fields for minimum and maximum position for X
        self.minPositionXLineEdit = QtWidgets.QLineEdit("-1000")
        self.maxPositionXLineEdit = QtWidgets.QLineEdit("1000")
        self.grid.addWidget(QtWidgets.QLabel("Min Position (X):"), 5, 0, 1, 1)
        self.grid.addWidget(self.minPositionXLineEdit, 5, 1, 1, 1)
        self.grid.addWidget(QtWidgets.QLabel("Max Position (X):"), 6, 0, 1, 1)
        self.grid.addWidget(self.maxPositionXLineEdit, 6, 1, 1, 1)


        # Text fields for minimum and maximum position for Y
        self.minPositionYLineEdit = QtWidgets.QLineEdit("-1000")
        self.maxPositionYLineEdit = QtWidgets.QLineEdit("1000")
        self.grid.addWidget(QtWidgets.QLabel("Min Position (Y):"), 7, 0, 1, 1)
        self.grid.addWidget(self.minPositionYLineEdit, 7, 1, 1, 1)
        self.grid.addWidget(QtWidgets.QLabel("Max Position (Y):"), 8, 0, 1, 1)
        self.grid.addWidget(self.maxPositionYLineEdit, 8, 1, 1, 1)
        '''
        1st Widget: Layout-based tiling
        '''
        
        # Start and Stop buttons
        self.startButton = QtWidgets.QPushButton('Start')
        self.stopButton = QtWidgets.QPushButton('Stop')
        self.speedLabel = QtWidgets.QLabel("Speed:")
        self.calibrationButton =  QtWidgets.QPushButton('Calibrate Position')
        self.calibrationButton.setCheckable(True)
        self.speedTextedit = QtWidgets.QLineEdit("1000")
        #self.grid.addWidget(self.speedLabel, 10, 0, 1, 1)
        #self.grid.addWidget(self.speedTextedit, 10, 1, 1, 1)

        self.grid.addWidget(self.buttonSelectPath,9, 0, 1, 1)
        self.grid.addWidget(self.lineeditSelectPath,9, 1, 1, 1)
        self.grid.addWidget(self.timeIntervalField,10, 0, 1, 1)
        self.grid.addWidget(self.numberOfScansField,10, 1, 1, 1)
        self.grid.addWidget(self.calibrationButton, 11, 0, 1, 1)
        self.grid.addWidget(self.samplePicker, 11, 1, 1, 1)
        self.grid.addWidget(self.startButton, 14, 0, 1, 1)
        self.grid.addWidget(self.stopButton, 14, 1, 1, 1)

        # define scan parameter per sample
        self.allScanParameters = []
        mFWD = os.path.dirname(os.path.realpath(__file__)).split("imswitch")[0]
        self.allScanParameters.append(ScanParameters("6 Wellplate", 126, 86, 0, 0, mFWD+"imswitch/_data/images/Wellplate6.png"))
        self.allScanParameters.append(ScanParameters("24 Wellplate", 126, 86, 0, 0, mFWD+"imswitch/_data/images/Wellplate24.png"))
        self.allScanParameters.append(ScanParameters("3-Slide Wellplateadapter", 164, 109, 0, 0, mFWD+"imswitch/_data/images/WellplateAdapter3Slides.png"))

        # load sample layout
        self.ScanSelectViewWidget = None
        self.loadSampleLayout(0)
        self.grid.addWidget(self.ScanSelectViewWidget, 12, 0, 2, 2)


        # set combobox with all samples
        self.setSampleLayouts(self.allScanParameters)
        self.samplePicker.currentIndexChanged.connect(self.loadSampleLayout)

        # Add the first tab
        self.tabWidget.addTab(mainWidget, "Figure-based Scan")

        '''
        2nd Widget: Manual tiling
        '''
        
        # Create a new widget for the second tab
        secondTabWidget = QtWidgets.QWidget()
        secondTabLayout = QtWidgets.QGridLayout(secondTabWidget)

        # Add input fields and buttons for second tab
        self.numTilesXLineEdit = QtWidgets.QLineEdit("10")
        self.numTilesYLineEdit = QtWidgets.QLineEdit("10")
        self.stepSizeXLineEdit = QtWidgets.QLineEdit("1.0")
        self.stepSizeYLineEdit = QtWidgets.QLineEdit("1.0")

        secondTabLayout.addWidget(QtWidgets.QLabel("Number of Tiles X:"), 0, 0)
        secondTabLayout.addWidget(self.numTilesXLineEdit, 0, 1)
        secondTabLayout.addWidget(QtWidgets.QLabel("Number of Tiles Y:"), 1, 0)
        secondTabLayout.addWidget(self.numTilesYLineEdit, 1, 1)
        secondTabLayout.addWidget(QtWidgets.QLabel("Step Size X:"), 2, 0)
        secondTabLayout.addWidget(self.stepSizeXLineEdit, 2, 1)
        secondTabLayout.addWidget(QtWidgets.QLabel("Step Size Y:"), 3, 0)
        secondTabLayout.addWidget(self.stepSizeYLineEdit, 3, 1)
        self.startButton2 = QtWidgets.QPushButton("Start")
        self.stopButton2 = QtWidgets.QPushButton("Stop")

        secondTabLayout.addWidget(self.startButton2, 4, 0)
        secondTabLayout.addWidget(self.stopButton2, 4, 1)

        # Add the second tab
        self.tabWidget.addTab(secondTabWidget, "Tile-based Scan")

        '''
        3rd Widget: Camera-based tile-scanning
        '''
        
        # Create a new widget for the thirdtab
        thirdTabWidget = QtWidgets.QWidget()
        thirdTabLayout = QtWidgets.QGridLayout(thirdTabWidget)

        self.getCameraScanCoordinatesButton = QtWidgets.QPushButton("Retreive Coordinates from Area")
        self.resetScanCoordinatesButton = QtWidgets.QPushButton("Reset Coordinates")
        self.nTilesXLabel = QtWidgets.QLabel("Number of Tiles X:")
        self.nTilesYLabel = QtWidgets.QLabel("Number of Tiles Y:")
        self.posXminLabel = QtWidgets.QLabel("Min Position X:")
        self.posXmaxLabel = QtWidgets.QLabel("Max Position X:")
        self.posYminLabel = QtWidgets.QLabel("Min Position Y:")
        self.posYmaxLabel = QtWidgets.QLabel("Max Position Y:")
        self.startButton3 = QtWidgets.QPushButton("Start")
        self.stopButton3 = QtWidgets.QPushButton("Stop")


        # illu settings
        self.buttonTurnOnLED = QtWidgets.QPushButton("LED On")
        self.buttonTurnOffLED = QtWidgets.QPushButton("LED OFF")    
        self.buttonTurnOnLEDArray = QtWidgets.QPushButton("Array On")
        self.buttonTurnOffLEDArray = QtWidgets.QPushButton("Array Off")

        self.imageLabel = ImageLabel()
        # Create a container widget for the ImageLabel
        imageLabelContainer = QtWidgets.QWidget()
        imageLabelLayout = QtWidgets.QHBoxLayout(imageLabelContainer)
        imageLabelLayout.addWidget(self.imageLabel)
        imageLabelLayout.setAlignment(QtCore.Qt.AlignCenter)  # Align the imageLabel to the center

        thirdTabLayout.addWidget(self.getCameraScanCoordinatesButton, 0, 0)
        thirdTabLayout.addWidget(self.resetScanCoordinatesButton, 0, 1)
        thirdTabLayout.addWidget(self.nTilesXLabel, 1, 0)
        thirdTabLayout.addWidget(self.nTilesYLabel, 1, 1)
        thirdTabLayout.addWidget(self.posXminLabel, 2, 0)
        thirdTabLayout.addWidget(self.posXmaxLabel, 2, 1)
        thirdTabLayout.addWidget(self.posYminLabel, 3, 0)
        thirdTabLayout.addWidget(self.posYmaxLabel, 3, 1)
        thirdTabLayout.addWidget(self.startButton3, 4, 0)
        thirdTabLayout.addWidget(self.stopButton3, 4, 1)
        
        thirdTabLayout.addWidget(self.buttonTurnOnLED, 5, 0)
        thirdTabLayout.addWidget(self.buttonTurnOffLED, 5, 1)
        thirdTabLayout.addWidget(self.buttonTurnOnLEDArray, 5, 2)
        thirdTabLayout.addWidget(self.buttonTurnOffLEDArray, 5, 3)

        thirdTabLayout.addWidget(imageLabelContainer, 6, 0, 4, 2)

        # Optional: Add stretch to rows and columns to ensure centering
        thirdTabLayout.setRowStretch(4, 1)  # Add stretch above the image container
        thirdTabLayout.setRowStretch(9, 1)  # Add stretch below the image container
        thirdTabLayout.setColumnStretch(0, 1)  # Add stretch to the sides of the image container
        thirdTabLayout.setColumnStretch(1, 1)
        # Add the third tab
        self.tabWidget.addTab(thirdTabWidget, "Camera-based Scan")
        
        
        # 4th Calibration:
        fourthTabWidget = QtWidgets.QWidget()
        fourthLayout = QtWidgets.QGridLayout(fourthTabWidget)

        self.startCalibrationButton = QtWidgets.QPushButton("Start Calibration")
        self.stopCalibrationButton = QtWidgets.QPushButton("Stop Calibration")
        calibrationLabel = QtWidgets.QLabel("""This uses the output from :func:.calibrate_backlash_1d, run at least 
                                    twice with orthogonal (or at least different) `direction` parameters. 
                                    The resulting 2x2 transformation matrix should map from image 
                                    to stage coordinates.  Currently, the backlash estimate given 
                                    by this function is only really trustworthy if you've supplied 
                                    two orthogonal calibrations - that will usually be the case.""")

        calibrationLabelScroll = QtWidgets.QScrollArea()  # Scrollbereich erstellen
        calibrationLabelScroll.setWidget(calibrationLabel)  # QLabel zum Scrollbereich hinzufügen
        calibrationLabelScroll.setWidgetResizable(True)  # Erlaubt das QLabel, sich auf die Größe des Scrollbereichs auszudehnen
                                                    
        self.calibrationLabelResult = QtWidgets.QLabel("Result:")
        self.calibrationLabelResultTable = QtWidgets.QTableWidget()
        fourthLayout.addWidget(self.startCalibrationButton, 0, 0)
        fourthLayout.addWidget(self.stopCalibrationButton, 0, 1)
        fourthLayout.addWidget(calibrationLabelScroll, 1, 0, 1, 2)
        fourthLayout.addWidget(self.calibrationLabelResult, 2, 1)
        fourthLayout.addWidget(self.calibrationLabelResultTable, 3, 0, 1, 2)
    
        fourthLayout.setRowStretch(4, 1)  # Add stretch above the image container
        fourthLayout.setRowStretch(9, 1)  # Add stretch below the image container
        fourthLayout.setColumnStretch(0, 1)  # Add stretch to the sides of the image container
        fourthLayout.setColumnStretch(1, 1)
        
        self.sigStageMappingComplete.connect(self.setStageMappingInfo)
        # Add the fourth tab
        self.tabWidget.addTab(fourthTabWidget, "Stage Mapping")
    
        # Add the self.tabWidget to the main layout of the widget
        mainLayout = QtWidgets.QVBoxLayout(self)
        mainLayout.addWidget(self.tabWidget)
        self.setLayout(mainLayout)

        # Initialize Layers
        self.imageLayer = None
        self.shapeLayer = None
        
    def setCameraScanParameters(self, nTilesX, nTilesY, minPosX, maxPosX, minPosY, maxPosY):
        self.nTilesXLabel.setText("Number of Tiles X: " + str(nTilesX))
        self.nTilesYLabel.setText("Number of Tiles Y: " + str(nTilesY))
        self.posXminLabel.setText("Min Position X: " + str(minPosX))
        self.posXmaxLabel.setText("Max Position X: " + str(maxPosX))
        self.posYminLabel.setText("Min Position Y: " + str(minPosY))
        self.posYmaxLabel.setText("Max Position Y: " + str(maxPosY))
        
    def setStageMappingInfo(self, xy_mapping_matrix, backlash, isCalibrated):
        if isCalibrated:
            self.calibrationLabelResult.setText("Result: Stage Mapping complete")
            rows, cols = 6,3
            self.calibrationLabelResultTable.setRowCount(rows)
            self.calibrationLabelResultTable.setColumnCount(cols)
            # set first two rows with xy_mapping_matrix
            for i in range(2):
                for j in range(2):
                    self.calibrationLabelResultTable.setItem(i, j, QtWidgets.QTableWidgetItem(str(xy_mapping_matrix[i, j])))
            # set 3rd row with backlash
            for j in range(cols):
                self.calibrationLabelResultTable.setItem(3, j, QtWidgets.QTableWidgetItem(str(backlash[j])))
        else:
            self.calibrationLabelResult.setText("Result: Stage Mapping failed")
            # reset table
            self.calibrationLabelResultTable.setRowCount(0)
            
    def getNumberTiles(self):
        return int(self.numTilesXLineEdit.text()), int(self.numTilesYLineEdit.text())
    
    def getStepSize(self):
        return float(self.stepSizeXLineEdit.text()), float(self.stepSizeYLineEdit.text())
    
    def setTilebasedScanParameters(self, scanParameters):
        self.stepSizeXLineEdit.setText(str(scanParameters[0]))
        self.stepSizeYLineEdit.setText(str(scanParameters[1]))
        
    def getTilebasedScanParameters(self):
        return float(self.stepSizeXLineEdit.text()), float(self.stepSizeYLineEdit.text())

    def getNTimesScan(self):
        try:
            return int(self.numberOfScansField.text())
        except:
            return 1

    def getTPeriodScan(self):
        try:
            return int(self.timeIntervalField.text())
        except:
            return 0

    def setDefaultSavePath(self, path):
        self.savePath = path
        self.lineeditSelectPath.setText(path)

    def getDefaulSavePath(self):
        return self.savePath

    def handleSelectPath(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(
            self, 'Select Folder', '')
        # check if string is a valid path
        if os.path.isdir(path):
            self.setDefaultSavePath(os.path.join(path, "histoScan"))
            os.makedirs(os.path.join(path, "histoScan"), exist_ok=True)

    def loadSampleLayout(self, index):
        if self.ScanSelectViewWidget is None:
            self.ScanSelectViewWidget = ScanSelectView(self, self.allScanParameters[index])
        else:
            self.ScanSelectViewWidget.updateParams(self.allScanParameters[index])
        self.ScanSelectViewWidget.setPixmap(QtGui.QPixmap(self.allScanParameters[index].imagePath))


    def setSampleLayouts(self, sampleLayoutList):
        self.samplePicker.clear()
        for sample in sampleLayoutList:
            self.samplePicker.addItem(sample.name)


    def setOffset(self, offsetX, offsetY):
        self.ScanSelectViewWidget.setOffset(offsetX, offsetY)

    def setScanMinMax(self, posXmin, posYmin, posXmax, posYmax):
        self.minPositionXLineEdit.setText(str(np.int64(posXmin)))
        self.maxPositionXLineEdit.setText(str(np.int64(posXmax)))
        self.minPositionYLineEdit.setText(str(np.int64(posYmin)))
        self.maxPositionYLineEdit.setText(str(np.int64(posYmax)))
        self._logger.debug("Setting scan min/max")

    def goToPosition(self, posX, posY):
        self._logger.debug("Moving to position")
        self.sigGoToPosition.emit(posX, posY)

    def setAvailableIlluSources(self, sources):
        self.illuminationSourceComboBox.clear()
        self.illuminationSourceComboBox.addItems(sources)

    def getSpeed(self):
        return np.float32(self.speedTextedit.text())

    def getIlluminationSource(self):
        return self.illuminationSourceComboBox.currentText()

    def getMinPositionX(self):
        return np.float32(self.minPositionXLineEdit.text())

    def getMaxPositionX(self):
        return np.float32(self.maxPositionXLineEdit.text())

    def getMinPositionY(self):
        return np.float32(self.minPositionYLineEdit.text())

    def getMaxPositionY(self):
        return np.float32(self.maxPositionYLineEdit.text())

    def initShapeLayerNapari(self):
        self.shapeLayer = self.viewer.add_shapes(shape_type='rectangle', edge_width=2,
                                               edge_color='red', face_color='transparent',
                                               name="ROI", blending='additive')
    
    def getCoordinatesShapeLayerNapari(self):
        return self.shapeLayer.data
    
    def setShapeLayerNapari(self, shape, name=""):
        if self.shapeLayer is None or name not in self.viewer.layers:
            self.shapeLayer = self.viewer.add_shapes(shape, shape_type='rectangle', edge_width=2,
                                               edge_color='red', face_color='transparent',
                                               name=name, blending='additive')
        self.shapeLayer.data = shape
        
    def resetShapeLayerNapari(self):
        self.shapeLayer.data = []
        self.shapeLayer.refresh()
        

    def setImageNapari(self, im, colormap="gray", isRGB = False, name="", pixelsize=(1,1), translation=(0,0)):
        if len(im.shape) == 2:
            translation = (translation[0], translation[1])
        if self.imageLayer is None or name not in self.viewer.layers:
            self.imageLayer = self.viewer.add_image(np.squeeze(im), rgb=isRGB, colormap=colormap,
                                               scale=pixelsize,translate=translation,
                                               name=name, blending='additive')
        else:
            self.imageLayer.data = np.squeeze(im)

    def removeImageNapari(self, name=""):
        if self.imageLayer is None or name not in self.viewer.layers:
            return
        self.viewer.layers.remove(self.imageLayer)
        
    def updatePartialImageNapari(self, im, coords, name=""):
        ''' update a sub roi of the already existing napari layer '''
        if self.imageLayer is None or name not in self.viewer.layers:
            return
        try:
            # coords are x,y,w,h
            self.imageLayer.data[coords[1]-coords[3]:coords[1], coords[0]:coords[0]+coords[2]] = im
            self.imageLayer.refresh()
        except Exception as e:
            self._logger.error(e)
            return

    def isAutofocus(self):
        if self.autofocusCheckbox.isChecked():
            return True
        else:
            return False

    def getAutofocusValues(self):
        autofocusParams = {}
        autofocusParams["valueRange"] = self.autofocusRange.text()
        autofocusParams["valueSteps"] = self.autofocusSteps.text()
        autofocusParams["valuePeriod"] = self.autofocusPeriod.text()
        autofocusParams["illuMethod"] = 'LED'
        return autofocusParams


    def setupSliderGui(self, label, valueDecimals, valueRange, tickInterval, singleStep):
        HistoScanLabel  = QtWidgets.QLabel(label)
        valueRangeMin, valueRangeMax = valueRange
        slider = guitools.FloatSlider(QtCore.Qt.Horizontal, self, allowScrollChanges=False,
                                        decimals=valueDecimals)
        slider.setFocusPolicy(QtCore.Qt.NoFocus)
        slider.setMinimum(valueRangeMin)
        slider.setMaximum(valueRangeMax)
        slider.setTickInterval(tickInterval)
        slider.setSingleStep(singleStep)
        slider.setValue(0)
        return slider, HistoScanLabel

    def getImage(self):
        if self.imageLayer is not None:
            return self.img.image

    def setImage(self, im, colormap="gray", name="", pixelsizeZ=1):
        if self.imageLayer is None or name not in self.viewer.layers:
            self.imageLayer = self.viewer.add_image(im, rgb=False, colormap=colormap,
                                               scale=(1, 1, pixelsizeZ),
                                               name=name, blending='additive')
        self.imageLayer.data = im

    def getCoordinateList(self):
        return self.canvas.getCoordinateList()

    def resetCoodinateList(self):
        self.canvas.resetCoordinateList()

    def getZStackValues(self):
        valueZmin = -abs(float(self.HistoScanValueZmin.text()))
        valueZmax = float(self.HistoScanValueZmax.text())
        valueZsteps = float(self.HistoScanValueZsteps.text())
        valueZenabled = bool(self.HistoScanDoZStack.isChecked())

        return valueZmin, valueZmax, valueZsteps, valueZenabled


    def getFilename(self):
        HistoScanEditFileName = self.HistoScanEditFileName.text()
        return HistoScanEditFileName

    def setInformationLabel(self, information):
        self.HistoScanLabelInfo.setText(information)

    def updateBoxPosition(self, posX, posY):
        if imswitch.IS_HEADLESS:
            return
        self.ScanSelectViewWidget.drawRectCurrentPoint(posX, posY)




class QPaletteButton(QtWidgets.QPushButton):

    def __init__(self, color):
        super().__init__()
        self.setFixedSize(QtCore.QSize(24,24))
        self.color = color
        self.setStyleSheet("background-color: %s;" % color)

COLORS = ['#000000', '#ffffff']


class ScanSelectView(QtWidgets.QGraphicsView):
    def __init__(self, parent, scanParameters):
        super().__init__(parent)
        scene = QtWidgets.QGraphicsScene(self)
        self._logger = initLogger(self)
        self.setScene(scene)

        self._pixmap_item = QtWidgets.QGraphicsPixmapItem()
        scene.addItem(self.pixmap_item)

        self.selection_rect = None
        self.start_point = None
        self.parent = parent

        # real-world coordinates for the scan region that is represented by the image
        self.physDimX = scanParameters.physDimX
        self.physDimY = scanParameters.physDimY
        self.physOffsetX = scanParameters.physOffsetX
        self.physOffsetY = scanParameters.physOffsetY
        self.clickedCoordinates = (0,0)
        self._logger = initLogger(self)
        
    def updateParams(self, scanParameters):
        # real-world coordinates for the scan region that is represented by the image
        self.physDimX = scanParameters.physDimX
        self.physDimY = scanParameters.physDimY
        self.physOffsetX = scanParameters.physOffsetX
        self.physOffsetY = scanParameters.physOffsetY

    def setOffset(self, offsetX, offsetY):
        self.physOffsetX = offsetX
        self.physOffsetY = offsetY

    @property
    def pixmap_item(self):
        return self._pixmap_item

    def setPixmap(self, pixmap):
        self.pixmap_item.setPixmap(pixmap)

    def resizeEvent(self, event):
        self.fitInView(self.pixmap_item, PyQt5.QtCore.Qt.KeepAspectRatio)
        super().resizeEvent(event)

    def mousePressEvent(self, event):
        sp = self.mapToScene(event.pos())
        lp = self.pixmap_item.mapFromScene(sp).toPoint()

        if event.button() == PyQt5.QtCore.Qt.LeftButton:
            self.start_point = lp
            if self.selection_rect:
                self.scene().removeItem(self.selection_rect)
            self.selection_rect = QtWidgets.QGraphicsRectItem(PyQt5.QtCore.QRectF(self.start_point, lp))
            self.selection_rect.setPen(QtGui.QPen(QtGui.QColor(255, 0, 0)))
            self.scene().addItem(self.selection_rect)

    def mouseMoveEvent(self, event):
        if self.start_point:
            sp = self.mapToScene(event.pos())
            lp = self.pixmap_item.mapFromScene(sp).toPoint()
            rect = PyQt5.QtCore.QRectF(self.start_point, lp)
            self.selection_rect.setRect(rect.normalized())

    def drawRectCurrentPoint(self, posX, posY):
        '''
        draw the current coordinates in the map converted from real-world coordinates into pixelmaps
        '''
        try: self.scene().removeItem(self.selection_rect_current)
        except: pass

        left = ((posX - self.physOffsetX)/self.physDimX)*self.pixmap_item.pixmap().width()
        top = -((posY - self.physOffsetY)/+self.physDimY*self.pixmap_item.pixmap().height()-self.pixmap_item.pixmap().height())

        self.selection_rect_current = QtWidgets.QGraphicsRectItem(PyQt5.QtCore.QRectF(left-5, top-5, 5, 5))
        self.selection_rect_current.setPen(QtGui.QPen(QtGui.QColor(0, 255, 0)))
        self.scene().addItem(self.selection_rect_current)

    def mouseReleaseEvent(self, event):
        if event.button() == PyQt5.QtCore.Qt.LeftButton and self.start_point:
            self.start_point = None
            # Calculate the selected coordinates here based on self.selection_rect.rect()
            selected_rect = self.selection_rect.rect()
            left = selected_rect.left()
            top = selected_rect.top()
            right = selected_rect.right()
            bottom = selected_rect.bottom()
            #self._logger.debug("Selected coordinates:", left, top, right, bottom)


            # differentiate between single point and rectangle
            if np.abs(left-right)<5 and np.abs(top-bottom)<5:
                # single
                self.scene().removeItem(self.selection_rect)
                self.selection_rect = QtWidgets.QGraphicsRectItem(PyQt5.QtCore.QRectF(left-5, top-5, 5, 5))
                self.selection_rect.setPen(QtGui.QPen(QtGui.QColor(255, 0, 0)))
                self.scene().addItem(self.selection_rect)
                # calculate real-world coordinates
                if self.parent.calibrationButton.isChecked():
                    self.physOffsetX, self.physOffsetY = 0,0 # reset offset because we estimate a new one
                posX = left/self.pixmap_item.pixmap().width()*self.physDimX+self.physOffsetX
                posY = (self.pixmap_item.pixmap().height()-top)/self.pixmap_item.pixmap().height()*self.physDimY+self.physOffsetY

                if self.parent.calibrationButton.isChecked():
                    self.clickedCoordinates = (posX,posY)
                    self.parent.sigCurrentOffset.emit(posX, posY)
                else:
                    self.parent.goToPosition(posX, posY)
                    self.drawRectCurrentPoint(posX, posY)
            else:
                # rectangle => send min/max X/Y position to parent
                # calculate real-world coordinates
                posXmin = left/self.pixmap_item.pixmap().width()*self.physDimX+self.physOffsetX
                posXmax = right/self.pixmap_item.pixmap().width()*self.physDimX+self.physOffsetX
                posYmin = (self.pixmap_item.pixmap().height()-bottom)/self.pixmap_item.pixmap().height()*self.physDimY+self.physOffsetY
                posYmax = (self.pixmap_item.pixmap().height()-top)/self.pixmap_item.pixmap().height()*self.physDimY+self.physOffsetY

                self.parent.setScanMinMax(posXmin, posYmin, posXmax, posYmax)


# Webcam View
class ImageLabel(QLabel):
    doubleClicked = pyqtSignal()
    dragPosition = pyqtSignal(QPoint, QPoint)

    def __init__(self):
        super().__init__()
        self.originalPixmap = None
        self.dragStartPos = None
        self.currentRect = None
        self.doubleClickPos = None

    def setOriginalPixmap(self, pixmap):
        self.originalPixmap = pixmap
        self.aspectRatio = pixmap.width() / pixmap.height()
        self.updatePixmap()

    def updatePixmap(self):
        if self.originalPixmap:
            fixedWidth = 500
            height = fixedWidth / self.aspectRatio

            scaledPixmap = self.originalPixmap.scaled(fixedWidth, height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.setAlignment(Qt.AlignCenter)  # Align the pixmap to the center of the label
            self.setPixmap(scaledPixmap)

    def mouseDoubleClickEvent(self, event):
        self.currentRect = None
        self.doubleClickPos = event.pos()
        self.doubleClicked.emit()
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragStartPos = event.pos()

    def mouseMoveEvent(self, event):
        if not self.dragStartPos:
            return
        self.currentRect = QRect(self.dragStartPos, event.pos())
        self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.dragStartPos:
            self.dragPosition.emit(self.dragStartPos, event.pos())
            self.dragStartPos = None

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self.currentRect:
            return
        painter = QPainter(self)
        painter.drawPixmap(self.rect(), self.originalPixmap)
        pen = QPen(QColor(255, 0, 0), 2)
        painter.setPen(pen)
        painter.drawRect(self.currentRect)


    def getCurrentImageSize(self):
        currentPixmap = self.pixmap()
        if currentPixmap:
            return currentPixmap.size()
        return None


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
