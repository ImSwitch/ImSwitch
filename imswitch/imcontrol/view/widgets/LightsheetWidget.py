import numpy as np
import pyqtgraph as pg
from qtpy import QtCore, QtWidgets

from imswitch.imcontrol.view import guitools
from .basewidgets import NapariHybridWidget


class LightsheetWidget(NapariHybridWidget):
    """ Widget containing lightsheet interface. """
    sigSliderIlluValueChanged = QtCore.Signal(float)  # (value)
    
    def __post_init__(self):
        #super().__init__(*args, **kwargs)

        self.grid = QtWidgets.QGridLayout()
        self.setLayout(self.grid)

        # Pull-down menu for the illumination source
        self.illuminationSourceComboBox = QtWidgets.QComboBox()
        self.illuminationSourceLabel = QtWidgets.QLabel("Illumination Source:")
        self.illuminationSourceComboBox.addItems(["Laser 1", "Laser 2", "LED"])
        self.grid.addWidget(self.illuminationSourceComboBox, 2, 1, 1, 1)

        # Slider for setting the value for the illumination source
        self.illuminationSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.illuminationSlider.setMinimum(0)
        self.illuminationSlider.setMaximum(100)
        self.illuminationSlider.valueChanged.connect(
            lambda value: self.sigSliderIlluValueChanged.emit(value)
        )
        
        self.grid.addWidget(self.illuminationSlider, 3, 1, 1, 1)

        # Pull-down menu for the stage axis
        self.stageAxisComboBox = QtWidgets.QComboBox()
        self.stageAxisLabel = QtWidgets.QLabel("Stage Axis:")
        self.stageAxisComboBox.addItems(["X", "Y", "Z", "A"])
        self.grid.addWidget(self.stageAxisLabel, 4, 0, 1, 1)
        self.grid.addWidget(self.stageAxisComboBox, 4, 1, 1, 1)

        # Text fields for minimum and maximum position
        self.minPositionLineEdit = QtWidgets.QLineEdit("-1000")
        self.maxPositionLineEdit = QtWidgets.QLineEdit("1000")
        self.grid.addWidget(QtWidgets.QLabel("Min Position:"), 5, 0, 1, 1)
        self.grid.addWidget(self.minPositionLineEdit, 5, 1, 1, 1)
        self.grid.addWidget(QtWidgets.QLabel("Max Position:"), 6, 0, 1, 1)
        self.grid.addWidget(self.maxPositionLineEdit, 6, 1, 1, 1)

        # Start and Stop buttons
        self.startButton = QtWidgets.QPushButton('Start')
        self.stopButton = QtWidgets.QPushButton('Stop')
        self.speedLabel = QtWidgets.QLabel("Speed:")
        self.speedTextedit = QtWidgets.QLineEdit("1000")
        self.grid.addWidget(self.startButton, 7, 0, 1, 1)
        self.grid.addWidget(self.stopButton, 7, 1, 1, 1)
        self.grid.addWidget(self.speedLabel, 8, 0, 1, 1)
        self.grid.addWidget(self.speedTextedit, 8, 1, 1, 1)
        
        self.layer = None
        
    def setAvailableIlluSources(self, sources):
        self.illuminationSourceComboBox.clear()
        self.illuminationSourceComboBox.addItems(sources)
    
    def setAvailableStageAxes(self, axes):
        self.stageAxisComboBox.clear()
        self.stageAxisComboBox.addItems(axes)
        
    def getSpeed(self):
        return np.float32(self.speedTextedit.text())
    
    def getIlluminationSource(self):
        return self.illuminationSourceComboBox.currentText()
    
    def getStageAxis(self):
        return self.stageAxisComboBox.currentText()
    
    def getMinPosition(self):
        return np.float32(self.minPositionLineEdit.text())
    
    def getMaxPosition(self):
        return np.float32(self.maxPositionLineEdit.text())
    
    
        
    def setImage(self, im, colormap="gray", name="", pixelsize=(1,1,1), translation=(0,0,0)):
        if len(im.shape) == 2:
            translation = (translation[0], translation[1])
        if self.layer is None or name not in self.viewer.layers:
            self.layer = self.viewer.add_image(im, rgb=False, colormap=colormap, 
                                               scale=pixelsize,translate=translation,
                                               name=name, blending='additive')
        self.layer.data = im
        
        
        
