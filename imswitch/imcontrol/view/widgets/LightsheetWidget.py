import numpy as np
import pyqtgraph as pg
from qtpy.QtCore import Signal
# PyQt5 imports
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication
import numpy as np
import pyqtgraph.opengl as gl


from imswitch.imcontrol.view import guitools
from .basewidgets import NapariHybridWidget


class LightsheetWidget(NapariHybridWidget):
    """ Widget containing lightsheet interface. """
    sigSliderIlluValueChanged = Signal(float)  # (value)
    
    def __post_init__(self):
        #super().__init__(*args, **kwargs)

        self.grid = QtWidgets.QGridLayout()
        self.setLayout(self.grid)

        # Initialize tab widget and add it to the main layout
        self.tabWidget = QtWidgets.QTabWidget()
        self.grid.addWidget(self.tabWidget, 0, 0, 1, 2)  # Adjust grid coordinates as needed

        # Create the first tab for existing controls
        self.controlsTab = QtWidgets.QWidget()
        self.controlsLayout = QtWidgets.QGridLayout(self.controlsTab)

        # Pull-down menu for the illumination source
        self.illuminationSourceComboBox = QtWidgets.QComboBox()
        self.illuminationSourceLabel = QtWidgets.QLabel("Illumination Source:")
        self.illuminationSourceComboBox.addItems(["Laser 1", "Laser 2", "LED"])
        self.controlsLayout.addWidget(self.illuminationSourceComboBox, 2, 1, 1, 1)

        # Slider for setting the value for the illumination source
        self.illuminationSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.illuminationSlider.setMinimum(0)
        self.illuminationSlider.setMaximum(100)
        self.illuminationSlider.valueChanged.connect(
            lambda value: self.sigSliderIlluValueChanged.emit(value)
        )
        
        self.controlsLayout.addWidget(self.illuminationSlider, 3, 1, 1, 1)

        # Pull-down menu for the stage axis
        self.stageAxisComboBox = QtWidgets.QComboBox()
        self.stageAxisLabel = QtWidgets.QLabel("Stage Axis:")
        self.stageAxisComboBox.addItems(["X", "Y", "Z", "A"])
        self.controlsLayout.addWidget(self.stageAxisLabel, 4, 0, 1, 1)
        self.controlsLayout.addWidget(self.stageAxisComboBox, 4, 1, 1, 1)

        # Text fields for minimum and maximum position
        self.minPositionLineEdit = QtWidgets.QLineEdit("-1000")
        self.maxPositionLineEdit = QtWidgets.QLineEdit("1000")
        self.controlsLayout.addWidget(QtWidgets.QLabel("Min Position:"), 5, 0, 1, 1)
        self.controlsLayout.addWidget(self.minPositionLineEdit, 5, 1, 1, 1)
        self.controlsLayout.addWidget(QtWidgets.QLabel("Max Position:"), 6, 0, 1, 1)
        self.controlsLayout.addWidget(self.maxPositionLineEdit, 6, 1, 1, 1)

        # Start and Stop buttons
        self.startButton = QtWidgets.QPushButton('Start')
        self.stopButton = QtWidgets.QPushButton('Stop')
        self.speedLabel = QtWidgets.QLabel("Speed:")
        self.speedTextedit = QtWidgets.QLineEdit("1000")
        self.controlsLayout.addWidget(self.startButton, 7, 0, 1, 1)
        self.controlsLayout.addWidget(self.stopButton, 7, 1, 1, 1)
        self.controlsLayout.addWidget(self.speedLabel, 8, 0, 1, 1)
        self.controlsLayout.addWidget(self.speedTextedit, 8, 1, 1, 1)
        
        self.layer = None
        
        
        # Create the second tab for the 3D viewer
        self.viewerTab = QtWidgets.QWidget()
        self.viewerLayout = QtWidgets.QVBoxLayout(self.viewerTab)
        self.tabWidget.addTab(self.controlsTab, "Controls")
        self.tabWidget.addTab(self.viewerTab, "3D Viewer")

        # Initialize GLViewWidget and add it to the viewer layout
        self.glWidget = gl.GLViewWidget()
        nPixelDimViewer = 5000
        #self.glWidget.setRange(xRange=(-nPixelDimViewer, nPixelDimViewer), 
        #                       yRange=(-nPixelDimViewer, nPixelDimViewer), 
        #                       zRange=(-nPixelDimViewer, nPixelDimViewer))
        mPos = QtGui.QVector3D(0.0, 0.0, 0.0)
        self.glWidget.setCameraPosition(pos=mPos, distance=nPixelDimViewer*2, elevation=30, azimuth=45)

        # Add a grid to help visualize the space
        grid = gl.GLGridItem()
        grid.setSize(x=nPixelDimViewer, y=nPixelDimViewer, z=0)  # Grid size, with z=0 for a flat grid
        grid.setSpacing(x=100, y=100, z=100)  # Spacing between grid lines
        self.glWidget.addItem(grid)

        xLabel = gl.GLTextItem(pos=(nPixelDimViewer, 0, 0), text='X', color=(1, 0, 0, 1))
        yLabel = gl.GLTextItem(pos=(0, nPixelDimViewer, 0), text='Y', color=(0, 1, 0, 1))
        zLabel = gl.GLTextItem(pos=(0, 0, nPixelDimViewer), text='Z', color=(0, 0, 1, 1))
        self.glWidget.addItem(xLabel)
        self.glWidget.addItem(yLabel)
        self.glWidget.addItem(zLabel)
        
        # add a label to the viewer layout and describe what we see
        self.viewerLayout.addWidget(QtWidgets.QLabel("Sample position in XYZ space"))
        self.viewerLayout.addWidget(self.glWidget)
        

        # Now, add your 3D viewer setup code here, working with self.glWidget
        w = gl.GLGridItem()
        self.glWidget.addItem(w)

        # draw position of stage    
        self.ScatterPlotItems = {}
        self.updatePosition((0,0,0))

    def updatePosition(self, positions=(0,0,0)):
        mPoint = np.array([positions])  # Convert the position to a numpy array
        if not hasattr(self, 'scatterPlotItem'):  # If the scatter plot item doesn't exist, create it
            self.scatterPlotItem = gl.GLScatterPlotItem(pos=mPoint, size=50, color=(1, 0, 0, .5))
            self.glWidget.addItem(self.scatterPlotItem)
        else:  # If it already exists, just update the data
            self.scatterPlotItem.setData(pos=mPoint)
            
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
        #self.layer.contrast_limits_range = (range_min, range_max)
        self.layer.contrast_limits = (np.min(im), np.max(im))
        
        
        

'''
# GLViewWidget setup
w = gl.GLViewWidget()
w.show()

# Create and add a GLGridItem
g = gl.GLGridItem()
w.addItem(g)


# Define the vertices of the box
vertices = np.array([
    [10, 10, 10],    # Vertex 0
    [10, -10, 10],   # Vertex 1
    [-10, -10, 10],  # Vertex 2
    [-10, 10, 10],   # Vertex 3
    [10, 10, -10],   # Vertex 4
    [10, -10, -10],  # Vertex 5
    [-10, -10, -10], # Vertex 6
    [-10, 10, -10]   # Vertex 7
])+(0,0,10)

# Define the edges of the box using the vertices
edges = np.array([
    [0, 1], [1, 2], [2, 3], [3, 0],  # Top edges
    [4, 5], [5, 6], [6, 7], [7, 4],  # Bottom edges
    [0, 4], [1, 5], [2, 6], [3, 7]   # Side edges connecting top and bottom
])

# Use GLLinePlotItem to draw each edge
for edge in edges:
    line = np.array([vertices[edge[0]], vertices[edge[1]]])
    line_item = gl.GLLinePlotItem(pos=line, color=(1, 1, 1, 1), width=2)  # White color, adjust width as needed
    w.addItem(line_item)

# Scatter plot setup
pos = np.random.randint(-10, 10, size=(100, 10, 3))
pos[:, :, 2] = np.abs(pos[:, :, 2])
ScatterPlotItems = {}
for point in np.arange(10):
    ScatterPlotItems[point] = gl.GLScatterPlotItem(pos=pos[:, point, :])
    w.addItem(ScatterPlotItems[point])

# Generate random points
pos = np.random.randint(-10, 10, size=(100, 10, 3))
pos[:, :, 2] = np.abs(pos[:, :, 2])

# Initialize color
color = np.zeros((pos.shape[0], 10, 4), dtype=np.float32)
color[:, :, 0] = 1  # Red
color[:, :, 1] = 0  # Green
color[:, :, 2] = 0.5  # Blue
color[0:5, :, 3] = np.tile(np.arange(1, 6) / 5., (10, 1)).T  # Alpha

# Update function
def update():
    global color
    # Update scatter plot item colors
    for point in np.arange(10):
        ScatterPlotItems[point].setData(color=color[:, point, :])
    # Rotate colors
    color = np.roll(color, 1, axis=0)


input()
'''