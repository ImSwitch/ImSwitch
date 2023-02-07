from pyqtgraph.Qt import QtGui, QtCore
from .basewidgets import Widget


class MotCorrWidget(Widget):
    """ Widget containing objective motorized correction collar interface,
    for Leica glycerol STEDwhite motCORR objective lens. """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.motcorrControl = QtGui.QFrame()
        self.motcorrControl.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Raised)
        
        self.motcorrControl.name = QtGui.QLabel('Glycerol motCorr [%]')
        self.motcorrControl.name.setTextFormat(QtCore.Qt.RichText)
        self.motcorrControl.name.setAlignment(QtCore.Qt.AlignCenter)

        self.motcorrControl.rangeLabel = QtGui.QLabel('Range: 0-100%')
        self.motcorrControl.rangeLabel.setFixedWidth(100)
        self.motcorrControl.setPointEdit = QtGui.QLineEdit(str(0))
        self.motcorrControl.setPointEdit.setFixedWidth(100)

        prange = (0, 100)
        self.motcorrControl.maxpower = QtGui.QLabel(str(prange[1]))
        self.motcorrControl.maxpower.setAlignment(QtCore.Qt.AlignCenter)
        self.motcorrControl.minpower = QtGui.QLabel(str(prange[0]))
        self.motcorrControl.minpower.setAlignment(QtCore.Qt.AlignCenter)
        self.motcorrControl.slider = QtGui.QSlider(QtCore.Qt.Vertical, self)
        self.motcorrControl.slider.setFocusPolicy(QtCore.Qt.NoFocus)
        self.motcorrControl.slider.setMinimum(prange[0])
        self.motcorrControl.slider.setMaximum(prange[1])
        self.motcorrControl.slider.setTickInterval(5)
        self.motcorrControl.slider.setSingleStep(0.1)
        self.motcorrControl.slider.setValue(50)

        gridMotCorr = QtGui.QGridLayout()
        self.motcorrControl.setLayout(gridMotCorr)
        gridMotCorr.addWidget(self.motcorrControl.name, 0, 0)
        gridMotCorr.addWidget(self.motcorrControl.rangeLabel, 3, 0)
        gridMotCorr.addWidget(self.motcorrControl.setPointEdit, 4, 0)
        gridMotCorr.addWidget(self.motcorrControl.maxpower, 1, 1)
        gridMotCorr.addWidget(self.motcorrControl.slider, 2, 1, 5, 1)
        gridMotCorr.addWidget(self.motcorrControl.minpower, 7, 1)

        # GUI layout below
        grid = QtGui.QGridLayout()
        self.setLayout(grid)
        grid.addWidget(self.motcorrControl, 0, 0)
