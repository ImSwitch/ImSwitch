import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui, QtWidgets

from imreconstruct.dataedit import DataEdit


class DataFrame(QtGui.QFrame):
    """Frame for showing and examining the raw data"""

    # Signals
    sigShowMeanClicked = QtCore.Signal()
    sigAdjustDataClicked = QtCore.Signal()
    sigUnloadDataClicked = QtCore.Signal()
    sigFrameNumberChanged = QtCore.Signal(int)
    sigFrameSliderChanged = QtCore.Signal(int)
    sigShowPatternChanged = QtCore.Signal(bool)
    sigDataChanged = QtCore.Signal(object)

    # Methods
    def __init__(self, controllerType, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Image Widget
        imageWidget = pg.GraphicsLayoutWidget()
        self.img_vb = imageWidget.addViewBox(row=0, col=0)
        self.img_vb.setMouseMode(pg.ViewBox.PanMode)
        self.img = pg.ImageItem(axisOrder='row-major')
        self.img.translate(-0.5, -0.5)
        self.img_vb.addItem(self.img)
        self.img_vb.setAspectLocked(True)
        self.img_hist = pg.HistogramLUTItem(image=self.img)
        imageWidget.addItem(self.img_hist, row=0, col=1)

        self.show_mean_btn = QtGui.QPushButton()
        self.show_mean_btn.setText('Show mean image')
        self.show_mean_btn.clicked.connect(self.sigShowMeanClicked)

        self.AdjustDataBtn = QtGui.QPushButton()
        self.AdjustDataBtn.setText('Adjust/compl. data')
        self.AdjustDataBtn.clicked.connect(self.sigAdjustDataClicked)

        self.UnloadDataBtn = QtGui.QPushButton()
        self.UnloadDataBtn.setText('Unload data')
        self.UnloadDataBtn.clicked.connect(self.sigUnloadDataClicked)

        frame_label = QtGui.QLabel('Frame # ')
        self.frame_nr = QtGui.QLineEdit('0')
        self.frame_nr.textChanged.connect(lambda x: (x.isdigit() and
                                                     self.setCurrentFrame(int(x)) and
                                                     self.sigFrameNumberChanged.emit(int(x))))
        self.frame_nr.setFixedWidth(45)

        data_name_label = QtWidgets.QLabel('File name:')
        self.data_name = QtWidgets.QLabel('')
        nr_frames_label = QtWidgets.QLabel('Nr of frames:')
        self.nr_frames = QtWidgets.QLabel('')

        self.slider = QtGui.QSlider(QtCore.Qt.Horizontal, self)
        self.slider.setMinimum(0)
        self.slider.setMaximum(0)
        self.slider.setTickInterval(5)
        self.slider.setSingleStep(1)
        self.slider.valueChanged[int].connect(self.setCurrentFrame)
        self.slider.valueChanged[int].connect(self.sigFrameSliderChanged)

        self.pattern_scatter = pg.ScatterPlotItem()
        self.pattern_scatter.setData(
            pos=[[0, 0], [10, 10], [20, 20], [30, 30], [40, 40]],
            pen=pg.mkPen(color=(255, 0, 0), width=0.5,
                         style=QtCore.Qt.SolidLine, antialias=True),
            brush=pg.mkBrush(color=(255, 0, 0), antialias=True), size=1,
            pxMode=False)

        self.editWdw = DataEdit()

        layout = QtGui.QGridLayout()
        self.setLayout(layout)

        layout.addWidget(data_name_label, 0, 0)
        layout.addWidget(self.data_name, 0, 1)
        layout.addWidget(nr_frames_label, 0, 2)
        layout.addWidget(self.nr_frames, 0, 3)
        layout.addWidget(self.show_mean_btn, 1, 0)
        layout.addWidget(self.slider, 1, 1)
        layout.addWidget(frame_label, 1, 2)
        layout.addWidget(self.frame_nr, 1, 3)
        layout.addWidget(self.AdjustDataBtn, 2, 0)
        layout.addWidget(self.UnloadDataBtn, 2, 1)
        layout.addWidget(imageWidget, 3, 0, 1, 4)

        self._showPattern = False

        # Initialize controller
        self.controller = controllerType(self)

    def getShowPattern(self):
        return self._showPattern

    def setShowPattern(self, value) -> None:
        self._showPattern = value
        self.sigShowPatternChanged.emit(value)

        if value:
            print('Showing pattern')
            self.img_vb.addItem(self.pattern_scatter)
        else:
            print('Hiding pattern')
            self.img_vb.removeItem(self.pattern_scatter)

    def showEditWindow(self, dataObj):
        self.editWdw.setData(dataObj)
        self.editWdw.show()

    def setImage(self, im, autoLevels=True):
        self.img.setImage(im, autoLevels)

    def setData(self, in_dataObj):
        self.sigDataChanged.emit(in_dataObj)

    def setPatternGridData(self, x, y):
        self.pattern_scatter.setData(x, y)

    def setCurrentFrame(self, value):
        self.frame_nr.setText(str(value))
        self.slider.setValue(value)

    def setNumFrames(self, value):
        self.nr_frames.setText(str(value))
        self.slider.setMaximum(value - 1 if value > 0 else 0)

    def setDataName(self, value):
        self.data_name.setText(value)
