import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui, QtWidgets


class DataEditActions(QtWidgets.QFrame):
    setDarkFrame_sig = QtCore.pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        setDarkFrame_btn = QtWidgets.QPushButton('Set Dark/Offset frame')
        setDarkFrame_btn.clicked.connect(self.setDarkFrame_sig.emit)

        layout = QtGui.QGridLayout()
        self.setLayout(layout)

        layout.addWidget(setDarkFrame_btn, 0, 0)


class DataEdit(QtGui.QMainWindow):
    """For future data editing window, for example to remove rearrange frames
    or devide into seperate datasets"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle('Data Edit/Complement')
        self.setWindowIcon(QtGui.QIcon(r'/Graphics/ML_logo.ico'))
        self.data = []

        # Data view Widget
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
        self.show_mean_btn.pressed.connect(self.show_mean)

        frame_label = QtGui.QLabel('Frame # ')
        self.frame_nr = QtGui.QLineEdit('0')
        self.frame_nr.textChanged.connect(self.setImgSlice)
        self.frame_nr.setFixedWidth(45)

        data_name_label = QtWidgets.QLabel('File name:')
        self.data_name = QtWidgets.QLabel('')
        nr_frames_label = QtWidgets.QLabel('Nr of frames:')
        self.nr_frames = QtWidgets.QLabel('')

        self.slider = QtGui.QSlider(QtCore.Qt.Horizontal, self)
        self.slider.setMinimum(0)
        self.slider.setMaximum(np.shape(self.data)[0])
        self.slider.setTickInterval(5)
        self.slider.setSingleStep(1)
        self.slider.valueChanged[int].connect(self.slider_moved)

        self.actionBtns = DataEditActions()
        self.actionBtns.setDarkFrame_sig.connect(self.setDarkFrame)

        # Dark frame view widget
        DF_Widget = pg.GraphicsLayoutWidget()
        self.df_vb = DF_Widget.addViewBox(row=0, col=0)
        self.df_vb.setMouseMode(pg.ViewBox.PanMode)
        self.df = pg.ImageItem(axisOrder='row-major')
        self.df.translate(-0.5, -0.5)
        self.df_vb.addItem(self.df)
        self.df_vb.setAspectLocked(True)
        self.df_hist = pg.HistogramLUTItem(image=self.df)
        DF_Widget.addItem(self.df_hist, row=0, col=1)

        layout = QtGui.QGridLayout()
        self.cwidget = QtGui.QWidget()
        self.setCentralWidget(self.cwidget)
        self.cwidget.setLayout(layout)

        layout.addWidget(data_name_label, 0, 0)
        layout.addWidget(self.data_name, 0, 1)
        layout.addWidget(nr_frames_label, 0, 2)
        layout.addWidget(self.nr_frames, 0, 3)
        layout.addWidget(self.show_mean_btn, 1, 0)
        layout.addWidget(self.slider, 1, 1)
        layout.addWidget(frame_label, 1, 2)
        layout.addWidget(self.frame_nr, 1, 3)
        layout.addWidget(imageWidget, 2, 0, 1, 4)
        layout.addWidget(self.actionBtns, 0, 4)
        layout.addWidget(DF_Widget, 0, 5, 3, 1)

    def setData(self, in_dataObj):
        self.dataObj = in_dataObj
        self.mean_data = np.array(np.mean(self.dataObj.data, 0), dtype=np.float32)
        self.show_mean()
        self.data_frames = self.dataObj.frames
        self.nr_frames.setText(str(self.data_frames))
        self.data_name.setText(self.dataObj.name)
        self.slider.setMaximum(self.data_frames - 1)


    def slider_moved(self):
        self.frame_nr.setText(str(self.slider.value()))
        self.setImgSlice()

    def setImgSlice(self):
        try:
            i = int(self.frame_nr.text())
        except TypeError:
            print('ERROR: Input must be an integer value')

        self.slider.setValue(i)
        self.img.setImage(self.dataObj.data[i], autoLevels=False)
        self.frame_nr.setText(str(i))

    def show_mean(self):
        self.img.setImage(self.mean_data)

    def setDarkFrame(self):
#        self.dataObj.data = self.dataObj.data[0:100]
        pass
