import numpy as np
import pyqtgraph as pg
from qtpy.QtCore import Signal
# PyQt5 imports
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QGroupBox, QLabel, QSpinBox, QDoubleSpinBox, QHBoxLayout, QVBoxLayout, QGridLayout, QPushButton, QSizePolicy
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import QSize, QRect
import numpy as np
import pyqtgraph.opengl as gl


from imswitch.imcontrol.view import guitools
from .basewidgets import NapariHybridWidget

class SquareButton(QPushButton):
    def __init__(self, text):
        super().__init__(text)
        size_policy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        size_policy.setHeightForWidth(True)
        self.setSizePolicy(size_policy)

    def heightForWidth(self, width):
        return width  # Dies macht den Button quadratisch

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
        
        # add mesospim tab
        self.mesoSPIMWidget = self.createMesoSPIMTab()
        self.mesoSPIMTab = QtWidgets.QWidget()
        self.mesoSPIMTab.setLayout(self.mesoSPIMWidget)
        
        # Create the second tab for the 3D viewer
        self.viewerTab = QtWidgets.QWidget()
        self.viewerLayout = QtWidgets.QVBoxLayout(self.viewerTab)
        self.tabWidget.addTab(self.controlsTab, "Controls")
        self.tabWidget.addTab(self.viewerTab, "3D Viewer")
        self.tabWidget.addTab(self.mesoSPIMTab, "MesoSPIM")

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

    def createMesoSPIMTab(self):
        # Group box for XYZ controls
        # Create group boxes
        main_layout = QVBoxLayout(self) 
        xyz_groupbox = self.createGroupbox('Sample Translation XY', 14)
        focus_groupbox = self.createGroupbox('Focus \& Sample Z', 14)
        rotation_groupbox = self.createGroupbox('Rotation', 14)
        scan_groupbox = self.createGroupbox('Scan Parameters', 14)

        # Set layouts for each groupbox
        xyz_layout = self.createGridLayout(xyz_groupbox)
        focus_layout = self.createGridLayout(focus_groupbox)
        rotation_layout = self.createGridLayout(rotation_groupbox)

        # Adding widgets to XYZ group box
        self.buttonXY_up = SquareButton('^')
        self.buttonXY_down = SquareButton('v')
        self.buttonXY_left = SquareButton('<')
        self.buttonXY_right = SquareButton('>')
        self.buttonXY_zero = SquareButton('ZERO\nXY')
        self.spinXY_increment = self.createSpinBox(1000, ' µm')
        scan_overlap_layout, self.scan_overlap = self.createLabeledSpinbox('overlap', 10, ' %')
        
        xyz_layout.addWidget(self.buttonXY_up, 0, 1)  # Y plus button
        xyz_layout.addWidget(self.buttonXY_right, 1, 2)  # X plus button
        xyz_layout.addWidget(self.buttonXY_left, 1, 0)  # X minus button
        xyz_layout.addWidget(self.buttonXY_down, 2, 1)  # Y minus button
        xyz_layout.addWidget(self.buttonXY_zero, 1, 1)  # XY zero button
        xyz_layout.addWidget(QLabel('Increment'), 3, 0)  # Increment label
        xyz_layout.addWidget(self.spinXY_increment, 3, 1)  # Increment spin box
        xyz_layout.addWidget(QLabel('Overlap'), 4, 0)  # Overlap label
        xyz_layout.addWidget(self.scan_overlap, 4, 1)  # Overlap spin box
        
        
        # Adding widgets to Focus group box
        self.buttonFocus_up = SquareButton('^')
        self.buttonFocus_down = SquareButton('v')
        self.buttonSample_fwd = SquareButton('<')
        self.buttonSample_bwd = SquareButton('>')
        self.buttonFocus_zero = SquareButton('ZERO\nF')
        self.spinFocus_increment = self.createSpinBox(1000, ' µm')
        self.spinSpeedFocus = self.createSpinBox(1000, ' µm/s')
        
        focus_layout.addWidget(self.buttonFocus_up, 0, 1)  # Focus plus button
        focus_layout.addWidget(self.buttonFocus_zero, 1, 1)  # Focus zero button
        focus_layout.addWidget(self.buttonFocus_down, 2, 1)  # Focus minus button
        focus_layout.addWidget(self.buttonSample_fwd, 1, 0)  # Sample forward button
        focus_layout.addWidget(self.buttonSample_bwd, 1, 2)  # Sample backward button
        focus_layout.addWidget(QLabel('Increment'), 3, 0)  # Increment label
        focus_layout.addWidget(self.spinFocus_increment, 3, 1)  # Increment spin box
        focus_layout.addWidget(QLabel('Speed (focus-through)'), 4, 0)  # Speed label
        focus_layout.addWidget(self.spinSpeedFocus, 4, 1)  # Speed spin box

        # Adding widgets to Rotation group box
        self.buttonRotation_minus = SquareButton('<')
        self.buttonRotation_zero = SquareButton('ZERO\nROT')
        self.buttonRotation_plus = SquareButton('>')
        self.spinRotation_increment = self.createSpinBox(10, ' °')
        rotation_layout.addWidget(self.buttonRotation_minus, 0, 0)  # Rotation minus button
        rotation_layout.addWidget(self.buttonRotation_zero, 0, 1)  # Rotation zero button
        rotation_layout.addWidget(self.buttonRotation_plus, 0, 2)  # Rotation plus button
        rotation_layout.addWidget(QLabel('Increment'), 1, 0)  # Increment label
        rotation_layout.addWidget(self.spinRotation_increment, 1, 1)  # Rotation increment

        scan_x_min_layout, self.scan_x_min = self.createLabeledSpinbox('min X', 0, ' µm')
        scan_y_min_layout, self.scan_y_min = self.createLabeledSpinbox('min Y', 0, ' µm')
        scan_z_min_layout, self.scan_z_min = self.createLabeledSpinbox('min Z', 0, ' µm')
        scan_x_max_layout, self.scan_x_max = self.createLabeledSpinbox('max X', 1000, ' µm')
        scan_y_max_layout, self.scan_y_max = self.createLabeledSpinbox('max Y', 1000, ' µm')
        scan_z_max_layout, self.scan_z_max = self.createLabeledSpinbox('max Z', 1000, ' µm')
        
        self.button_scan_x_min_snap = SquareButton('cX')
        self.button_scan_x_max_snap = SquareButton('cX')
        self.button_scan_y_min_snap = SquareButton('cY')
        self.button_scan_y_max_snap = SquareButton('cY')
        self.button_scan_z_min_snap = SquareButton('cZ')
        self.button_scan_z_max_snap = SquareButton('cZ')
        
        self.button_scan_xyz_start = self.createTextButton('Start Scan', 16)
        self.button_scan_xyz_stop = self.createTextButton('Stop Scan', 16)
        
        scan_groupbox_layout = self.createGridLayout(scan_groupbox)
        scan_groupbox_layout.addLayout(scan_x_min_layout, 0, 0)
        scan_groupbox_layout.addWidget(self.button_scan_x_min_snap, 0, 1)
        scan_groupbox_layout.addLayout(scan_x_max_layout, 0, 2)
        scan_groupbox_layout.addWidget(self.button_scan_x_max_snap, 0, 3)
        
        scan_groupbox_layout.addLayout(scan_y_min_layout, 1, 0)
        scan_groupbox_layout.addWidget(self.button_scan_y_min_snap, 1, 1)
        scan_groupbox_layout.addLayout(scan_y_max_layout, 1, 2)
        scan_groupbox_layout.addWidget(self.button_scan_y_max_snap, 1, 3)
        
        scan_groupbox_layout.addLayout(scan_z_min_layout, 2, 0)
        scan_groupbox_layout.addWidget(self.button_scan_z_min_snap, 2, 1)
        scan_groupbox_layout.addLayout(scan_z_max_layout, 2, 2)
        scan_groupbox_layout.addWidget(self.button_scan_z_max_snap, 2, 3)        
        scan_groupbox_layout.addWidget(self.button_scan_xyz_start, 3, 0)
        scan_groupbox_layout.addWidget(self.button_scan_xyz_stop, 3, 2)

        # Add all groupboxes to main layout from left to right in 3 columns
        hbox_layout = QHBoxLayout()
        hbox_layout.addWidget(xyz_groupbox)
        hbox_layout.addWidget(focus_groupbox)
        #hbox_layout.addWidget(rotation_groupbox)
        hbox_layout.addWidget(scan_groupbox)
        main_layout.addLayout(hbox_layout)
        return main_layout
        
    def get_step_size_xy_zf(self):
        '''
        Returns the step size for the XYZ and focus controls.
        '''
        return self.spinXY_increment.value(), self.spinFocus_increment.value()
        
    def get_speed_focusthrough(self):
        '''
        Returns the speed for focus-through.
        '''
        return self.spinSpeedFocus.value()
    
    def get_scan_parameters(self):
        '''
        Returns the scan parameters.
        '''
        mScanParams = {}
        mScanParams['x_min'] = int(self.scan_x_min.value())
        mScanParams['x_max'] = int(self.scan_x_max.value())
        mScanParams['y_min'] = int(self.scan_y_min.value())
        mScanParams['y_max'] = int(self.scan_y_max.value())
        mScanParams['z_min'] = int(self.scan_z_min.value())
        mScanParams['z_max'] = int(self.scan_z_max.value())
        mScanParams['overlap'] = int(self.scan_overlap.value())
        mScanParams['speed'] = int(self.get_speed_focusthrough())
        mScanParams['stage_axis'] = self.stageAxisComboBox.currentText()
        mScanParams['illu_source'] = self.illuminationSourceComboBox.currentText()
        mScanParams['illu_value'] = self.illuminationSlider.value()
        return mScanParams
    
    def set_scan_x_min(self, value):
        self.scan_x_min.setValue(value)
    
    def set_scan_x_max(self, value):
        self.scan_x_max.setValue(value)
    
    def set_scan_y_min(self, value):
        self.scan_y_min.setValue(value)
    
    def set_scan_y_max(self, value):
        self.scan_y_max.setValue(value)
    
    def set_scan_z_min(self, value):
        self.scan_z_min.setValue(value)
    
    def set_scan_z_max(self, value):
        self.scan_z_max.setValue(value)
    
    def createGroupbox(self, title, pointsize):
        groupbox = QGroupBox(title)
        groupbox.setFont(QFont('Arial', pointsize))
        return groupbox

    def createGridLayout(self, parent):
        layout = QGridLayout(parent)
        return layout

    def createButton(self, icon):
        button = QPushButton()
        button.setIcon(QIcon(icon))
        #button.setIconSize(QSize(80, 80))
        button.setAutoRepeat(True)
        return button

    def createTextButton(self, text, size=14):
        button = QPushButton(text)
        button.setFont(QFont('Arial', size))
        return button

    def createLabeledSpinbox(self, label, maximum, suffix):
        layout = QHBoxLayout()
        spinbox = self.createSpinBox(maximum, suffix)
        layout.addWidget(QLabel(label))
        layout.addWidget(spinbox)
        return layout, spinbox
        
    def createSpinBox(self, value, suffix):
        spinbox = QSpinBox()
        spinbox.setMinimum(-10000)
        spinbox.setMaximum(10000)
        spinbox.setSuffix(suffix)
        spinbox.setValue(value)
        return spinbox

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