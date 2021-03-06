import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtWidgets

from .guitools import BetterPushButton


class ReconstructionView(QtWidgets.QFrame):
    """ Frame for showing the reconstructed image"""

    # Signals
    sigItemSelected = QtCore.Signal()
    sigImgSliceChanged = QtCore.Signal(int, int, int, int)
    sigViewChanged = QtCore.Signal()

    # Methods
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Image Widget
        imageWidget = pg.GraphicsLayoutWidget()
        self.imgVb = imageWidget.addViewBox(row=0, col=0)
        self.imgVb.setMouseMode(pg.ViewBox.PanMode)
        self.img = pg.ImageItem(axisOrder='row-major')
        self.img.translate(-0.5, -0.5)
        # self.img.setPxMode(True)
        self.imgVb.addItem(self.img)
        self.imgVb.setAspectLocked(True)
        self.imgHist = pg.HistogramLUTItem(image=self.img)
        # self.hist.vb.setLimits(yMin=0, yMax=2048)
        imageWidget.addItem(self.imgHist, row=0, col=1)

        # Slider and edit box for choosing slice
        sliceLabel = QtWidgets.QLabel('Slice # ')
        self.sliceNum = QtWidgets.QLabel('0')
        self.sliceSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        self.sliceSlider.setMinimum(0)
        self.sliceSlider.setMaximum(0)
        self.sliceSlider.setTickInterval(5)
        self.sliceSlider.setSingleStep(1)
        self.sliceSlider.valueChanged[int].connect(self.sliceSliderMoved)

        baseLabel = QtWidgets.QLabel('Base # ')
        self.baseNum = QtWidgets.QLabel('0')
        self.baseSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        self.baseSlider.setMinimum(0)
        self.baseSlider.setMaximum(0)
        self.baseSlider.setTickInterval(5)
        self.baseSlider.setSingleStep(1)
        self.baseSlider.valueChanged[int].connect(self.baseSliderMoved)

        timeLabel = QtWidgets.QLabel('Time point # ')
        self.timeNum = QtWidgets.QLabel('0')
        self.timeSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        self.timeSlider.setMinimum(0)
        self.timeSlider.setMaximum(0)
        self.timeSlider.setTickInterval(5)
        self.timeSlider.setSingleStep(1)
        self.timeSlider.valueChanged[int].connect(self.timeSliderMoved)

        datasetLabel = QtWidgets.QLabel('Dataset # ')
        self.datasetNum = QtWidgets.QLabel('0')
        self.datasetSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        self.datasetSlider.setMinimum(0)
        self.datasetSlider.setMaximum(0)
        self.datasetSlider.setTickInterval(5)
        self.datasetSlider.setSingleStep(1)
        self.datasetSlider.valueChanged[int].connect(self.datasetSliderMoved)

        # Button group for choosing view
        self.chooseViewGroup = QtWidgets.QButtonGroup()
        self.chooseViewBox = QtWidgets.QGroupBox('Choose view')
        self.viewLayout = QtWidgets.QVBoxLayout()

        self.standardView = QtWidgets.QRadioButton('Standard view')
        self.standardView.viewName = 'standard'
        self.chooseViewGroup.addButton(self.standardView)
        self.viewLayout.addWidget(self.standardView)

        self.bottomView = QtWidgets.QRadioButton('Bottom side view')
        self.bottomView.viewName = 'bottom'
        self.chooseViewGroup.addButton(self.bottomView)
        self.viewLayout.addWidget(self.bottomView)

        self.leftView = QtWidgets.QRadioButton('Left side view')
        self.leftView.viewName = 'left'
        self.chooseViewGroup.addButton(self.leftView)
        self.viewLayout.addWidget(self.leftView)

        self.chooseViewBox.setLayout(self.viewLayout)
        self.chooseViewGroup.buttonClicked.connect(self.sigViewChanged)

        # List for storing sevral data sets
        self.reconList = QtWidgets.QListWidget()
        self.reconList.currentItemChanged.connect(self.sigItemSelected)
        self.reconList.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        removeReconBtn = BetterPushButton('Remove current')
        removeReconBtn.clicked.connect(self.removeRecon)
        removeAllReconBtn = BetterPushButton('Remove all')
        removeAllReconBtn.clicked.connect(self.removeAllRecon)

        # Set initial states
        self.standardView.setChecked(True)

        # Set layout
        layout = QtWidgets.QGridLayout()

        self.setLayout(layout)

        layout.addWidget(imageWidget, 0, 0, 2, 1)
        layout.addWidget(self.chooseViewBox, 0, 1, 1, 2)
        layout.addWidget(self.reconList, 0, 3, 2, 1)
        layout.addWidget(self.sliceSlider, 2, 0)
        layout.addWidget(sliceLabel, 2, 1)
        layout.addWidget(self.sliceNum, 2, 2)
        layout.addWidget(self.baseSlider, 3, 0)
        layout.addWidget(baseLabel, 3, 1)
        layout.addWidget(self.baseNum, 3, 2)
        layout.addWidget(self.timeSlider, 4, 0)
        layout.addWidget(timeLabel, 4, 1)
        layout.addWidget(self.timeNum, 4, 2)
        layout.addWidget(self.datasetSlider, 5, 0)
        layout.addWidget(datasetLabel, 5, 1)
        layout.addWidget(self.datasetNum, 5, 2)
        layout.addWidget(removeReconBtn, 2, 3)
        layout.addWidget(removeAllReconBtn, 3, 3)

        layout.setRowStretch(1, 1)
        layout.setColumnStretch(0, 100)
        layout.setColumnStretch(2, 5)

    def sliceSliderMoved(self):
        self.sliceNum.setText(str(self.sliceSlider.value()))
        self.sigImgSliceChanged.emit(*self.getSliceParameters())

    def baseSliderMoved(self):
        self.baseNum.setText(str(self.baseSlider.value()))
        self.sigImgSliceChanged.emit(*self.getSliceParameters())

    def timeSliderMoved(self):
        self.timeNum.setText(str(self.timeSlider.value()))
        self.sigImgSliceChanged.emit(*self.getSliceParameters())

    def datasetSliderMoved(self):
        self.datasetNum.setText(str(self.timeSlider.value()))
        self.sigImgSliceChanged.emit(*self.getSliceParameters())

    def getSliceParameters(self):
        return (self.sliceSlider.value(), self.baseSlider.value(),
                self.timeSlider.value(), self.datasetSlider.value())

    def setSliceParameters(self, s=None, base=None, t=None, ds=None):
        if s is not None:
            self.sliceSlider.setValue(s)
        if base is not None:
            self.baseSlider.setValue(base)
        if t is not None:
            self.timeSlider.setValue(t)
        if ds is not None:
            self.datasetSlider.setValue(ds)

    def setSliceParameterMaximums(self, s=None, base=None, t=None, ds=None):
        if s is not None:
            self.sliceSlider.setMaximum(s)
        if base is not None:
            self.baseSlider.setMaximum(base)
        if t is not None:
            self.timeSlider.setMaximum(t)
        if ds is not None:
            self.datasetSlider.setMaximum(ds)

    def addNewData(self, reconObj, name=None):
        if name is None:
            name = reconObj.name
            ind = 0
            for i in range(self.reconList.count()):
                if name + '_' + str(ind) == self.reconList.item(i).data(0):
                    ind += 1
            name = name + '_' + str(ind)

        listItem = QtWidgets.QListWidgetItem(name)
        listItem.setData(1, reconObj)
        self.reconList.addItem(listItem)
        self.reconList.setCurrentItem(listItem)

    def getCurrentItemIndex(self):
        return self.reconList.indexFromItem(self.reconList.currentItem()).row()

    def getDataAtIndex(self, index):
        return self.reconList.item(index).data(1)

    def getCurrentItemData(self):
        currentItem = self.reconList.currentItem()
        return currentItem.data(1) if currentItem is not None else None

    def getViewName(self):
        return self.chooseViewGroup.checkedButton().viewName

    def setImage(self, im, autoLevels=False, levels=None):
        if levels is None:
            self.img.setImage(im, autoLevels=autoLevels)
        else:
            self.img.setImage(im, levels=levels)

    def clearImage(self):
        self.img.setImage(np.zeros((100, 100)))

    def getImageDisplayLevels(self):
        return self.imgHist.getLevels()

    def setImageDisplayLevels(self, minimum, maximum):
        self.imgHist.setLevels(minimum, maximum)

    def removeRecon(self):
        numSelected = len(self.reconList.selectedIndexes())
        while not numSelected == 0:
            row = self.reconList.selectedIndexes()[0].row()
            self.reconList.takeItem(row)
            numSelected -= 1

    def removeAllRecon(self):
        for i in range(self.reconList.count()):
            currRow = self.reconList.currentRow()
            self.reconList.takeItem(currRow)
