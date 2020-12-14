import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui, QtWidgets


class ReconstructionWidget(QtWidgets.QFrame):
    """ Frame for showing the reconstructed image"""

    # Signals
    sigItemSelected = QtCore.Signal()
    sigImgSliceChanged = QtCore.Signal(int, int, int, int)
    sigViewChanged = QtCore.Signal()
    sigScanParsChanged = QtCore.Signal(object)

    # Methods
    def __init__(self, controllerType, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Image Widget
        imageWidget = pg.GraphicsLayoutWidget()
        self.img_vb = imageWidget.addViewBox(row=0, col=0)
        self.img_vb.setMouseMode(pg.ViewBox.PanMode)
        self.img = pg.ImageItem(axisOrder='row-major')
        self.img.translate(-0.5, -0.5)
#        self.img.setPxMode(True)
        self.img_vb.addItem(self.img)
        self.img_vb.setAspectLocked(True)
        self.img_hist = pg.HistogramLUTItem(image=self.img)
#        self.hist.vb.setLimits(yMin=0, yMax=2048)
        imageWidget.addItem(self.img_hist, row=0, col=1)

        """Slider and edit box for choosing slice"""
        slice_label = QtGui.QLabel('Slice # ')
        self.slice_nr = QtGui.QLabel('0')

        self.slice_slider = QtGui.QSlider(QtCore.Qt.Horizontal, self)
        self.slice_slider.setMinimum(0)
        self.slice_slider.setMaximum(0)
        self.slice_slider.setTickInterval(5)
        self.slice_slider.setSingleStep(1)
        self.slice_slider.valueChanged[int].connect(self.slice_slider_moved)

        base_label = QtGui.QLabel('Base # ')
        self.base_nr = QtGui.QLabel('0')

        self.base_slider = QtGui.QSlider(QtCore.Qt.Horizontal, self)
        self.base_slider.setMinimum(0)
        self.base_slider.setMaximum(0)
        self.base_slider.setTickInterval(5)
        self.base_slider.setSingleStep(1)
        self.base_slider.valueChanged[int].connect(self.base_slider_moved)

        self.time_slider = QtGui.QSlider(QtCore.Qt.Horizontal, self)
        self.time_slider.setMinimum(0)
        self.time_slider.setMaximum(0)
        self.time_slider.setTickInterval(5)
        self.time_slider.setSingleStep(1)
        self.time_slider.valueChanged[int].connect(self.time_slider_moved)

        time_label = QtGui.QLabel('Time point # ')
        self.time_nr = QtGui.QLabel('0')

        self.dataset_slider = QtGui.QSlider(QtCore.Qt.Horizontal, self)
        self.dataset_slider.setMinimum(0)
        self.dataset_slider.setMaximum(0)
        self.dataset_slider.setTickInterval(5)
        self.dataset_slider.setSingleStep(1)
        self.dataset_slider.valueChanged[int].connect(self.dataset_slider_moved)

        dataset_label = QtGui.QLabel('Dataset # ')
        self.dataset_nr = QtGui.QLabel('0')

        """Button group for choosing view"""
        self.choose_view_group = QtGui.QButtonGroup()
        self.choose_view_box = QtGui.QGroupBox('Choose view')
        self.view_layout = QtGui.QVBoxLayout()

        self.standard_view = QtGui.QRadioButton('Standard view')
        self.standard_view.viewName = 'standard'
        self.choose_view_group.addButton(self.standard_view)
        self.view_layout.addWidget(self.standard_view)

        self.bottom_view = QtGui.QRadioButton('Bottom side view')
        self.bottom_view.viewName = 'bottom'
        self.choose_view_group.addButton(self.bottom_view)
        self.view_layout.addWidget(self.bottom_view)

        self.left_view = QtGui.QRadioButton('Left side view')
        self.left_view.viewName = 'left'
        self.choose_view_group.addButton(self.left_view)
        self.view_layout.addWidget(self.left_view)

        self.choose_view_box.setLayout(self.view_layout)
        self.choose_view_group.buttonClicked.connect(self.sigViewChanged)

        """List for storing sevral data sets"""
        self.recon_list = QtGui.QListWidget()
        self.recon_list.currentItemChanged.connect(self.sigItemSelected)
        self.recon_list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        removeReconBtn = QtWidgets.QPushButton('Remove current')
        removeReconBtn.clicked.connect(self.removeRecon)
        removeAllReconBtn = QtWidgets.QPushButton('Remove all')
        removeAllReconBtn.clicked.connect(self.removeAllRecon)

        """Set initial states"""
        self.standard_view.setChecked(True)

        """Set layout"""
        layout = QtGui.QGridLayout()

        self.setLayout(layout)

        layout.addWidget(imageWidget, 0, 0, 2, 1)
        layout.addWidget(self.choose_view_box, 0, 1, 1, 2)
        layout.addWidget(self.recon_list, 0, 3, 2, 1)
        layout.addWidget(self.slice_slider, 2, 0)
        layout.addWidget(slice_label, 2, 1)
        layout.addWidget(self.slice_nr, 2, 2)
        layout.addWidget(self.base_slider, 3, 0)
        layout.addWidget(base_label, 3, 1)
        layout.addWidget(self.base_nr, 3, 2)
        layout.addWidget(self.time_slider, 4, 0)
        layout.addWidget(time_label, 4, 1)
        layout.addWidget(self.time_nr, 4, 2)
        layout.addWidget(self.dataset_slider, 5, 0)
        layout.addWidget(dataset_label, 5, 1)
        layout.addWidget(self.dataset_nr, 5, 2)
        layout.addWidget(removeReconBtn, 2, 3)
        layout.addWidget(removeAllReconBtn, 3, 3)

        layout.setRowStretch(1, 1)
        layout.setColumnStretch(0, 100)
        layout.setColumnStretch(2, 5)

        # Initialize controller
        self.controller = controllerType(self)

    def slice_slider_moved(self):
        self.slice_nr.setText(str(self.slice_slider.value()))
        self.sigImgSliceChanged.emit(*self.getSliceParameters())

    def base_slider_moved(self):
        self.base_nr.setText(str(self.base_slider.value()))
        self.sigImgSliceChanged.emit(*self.getSliceParameters())

    def time_slider_moved(self):
        self.time_nr.setText(str(self.time_slider.value()))
        self.sigImgSliceChanged.emit(*self.getSliceParameters())

    def dataset_slider_moved(self):
        self.dataset_nr.setText(str(self.time_slider.value()))
        self.sigImgSliceChanged.emit(*self.getSliceParameters())

    def getSliceParameters(self):
        return (self.slice_slider.value(), self.base_slider.value(),
                self.time_slider.value(), self.dataset_slider.value())

    def setSliceParameters(self, s=None, base=None, t=None, ds=None):
        if s is not None:
            self.slice_slider.setValue(s)
        if base is not None:
            self.base_slider.setValue(base)
        if t is not None:
            self.time_slider.setValue(t)
        if ds is not None:
            self.dataset_slider.setValue(ds)

    def setSliceParameterMaximums(self, s=None, base=None, t=None, ds=None):
        if s is not None:
            self.slice_slider.setMaximum(s)
        if base is not None:
            self.base_slider.setMaximum(base)
        if t is not None:
            self.time_slider.setMaximum(t)
        if ds is not None:
            self.dataset_slider.setMaximum(ds)

    def AddNewData(self, recon_obj, name=None):
        if name is None:
            name = recon_obj.name
            ind = 0
            for i in range(self.recon_list.count()):
                if name + '_' + str(ind) == self.recon_list.item(i).data(0):
                    ind += 1
            name = name + '_' + str(ind)

        list_item = QtGui.QListWidgetItem(name)
        list_item.setData(1, recon_obj)
        self.recon_list.addItem(list_item)
        self.recon_list.setCurrentItem(list_item)

    def getCurrentItemIndex(self):
        return self.recon_list.indexFromItem(self.recon_list.currentItem()).row()

    def getDataAtIndex(self, index):
        return self.recon_list.item(index).data(1)

    def getCurrentItemData(self):
        currentItem = self.recon_list.currentItem()
        return currentItem.data(1) if currentItem is not None else None

    def getViewName(self):
        return self.choose_view_group.checkedButton().viewName

    def setImage(self, im, autoLevels=False, levels=None):
        if levels is None:
            self.img.setImage(im, autoLevels=autoLevels)
        else:
            self.img.setImage(im, levels=levels)

    def clearImage(self):
        self.img.setImage(np.zeros((100, 100)))

    def getImageDisplayLevels(self):
        return self.img_hist.getLevels()

    def setImageDisplayLevels(self, minimum, maximum):
        self.img_hist.setLevels(minimum, maximum)

    def UpdateScanPars(self, scanParDict):
        self.sigScanParsChanged.emit(scanParDict)

    # TODO
    def removeRecon(self):
        nr_selected = len(self.recon_list.selectedIndexes())
        while not nr_selected == 0:
            row = self.recon_list.selectedIndexes()[0].row()
            self.recon_list.takeItem(row)
            nr_selected -= 1

    # TODO
    def removeAllRecon(self):
        for i in range(self.recon_list.count()):
            currRow = self.recon_list.currentRow()
            self.recon_list.takeItem(currRow)
