import pyqtgraph as pg
from qtpy import QtCore, QtWidgets, QtGui
from datetime import datetime
from imswitch.imcommon.view.guitools import naparitools
from imswitch.imcontrol.view import guitools
from .basewidgets import Widget
import json

class BeadRecWidget(Widget):
    """ Displays the FFT transform of the image. """

    sigROIToggled = QtCore.Signal(bool)  # (enabled)
    sigRunClicked = QtCore.Signal()
    sigScaleClicked = QtCore.Signal()
    sigAddCurrentToList = QtCore.Signal()
    sigSelectionChanged = QtCore.Signal(int,bool)
    sigRemoveRecFromList = QtCore.Signal(int)
    sigClearList = QtCore.Signal()
    sigSaveAll = QtCore.Signal()
    sigQueryMousePixelValue = QtCore.Signal(float,float)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.analysisPrm = {
            "min_area": 50,
            "max_area": 1000,
            "tol_peaks_pos": 10,
            "thresh_coeff": 0.2,
            "erosion_coeff": 0.2
        }

        #MNain panel: Viewbox + buttons
        self.cwidget = pg.GraphicsLayoutWidget()
        self.vb = self.cwidget.addViewBox(row=1, col=1)
        self.vb.setMouseMode(pg.ViewBox.RectMode)
        self.img = pg.ImageItem(axisOrder='row-major')
        self.img.setTransform(self.img.transform().translate(-0.5, -0.5))
        self.vb.addItem(self.img)
        self.vb.setAspectLocked(True)
        
        self.pixelLabel = QtWidgets.QGraphicsTextItem("")
        self.pixelLabel.setDefaultTextColor(QtGui.QColor("white"))
        self.pixelLabel.setPos(0, 0) 
        self.vb.scene().addItem(self.pixelLabel)
        
        self.hist = pg.HistogramLUTItem(image=self.img)
        self.hist.vb.setLimits(yMin=0, yMax=66000)
        self.hist.gradient.loadPreset('greyclip')
        for tick in self.hist.gradient.ticks:
            tick.hide()
        self.cwidget.addItem(self.hist, row=1, col=2)

        self.roiButton = guitools.BetterPushButton('Show ROI')
        self.roiButton.setCheckable(True)
        self.runButton = QtWidgets.QCheckBox('Run')
        self.scaleButton = QtWidgets.QCheckBox('Scale')
        self.saveRecBtn = guitools.BetterPushButton('Save Rec')
        self.loadImgBtn = guitools.BetterPushButton('Load')
        self.donutsAnalysisBtn = guitools.BetterPushButton('Donuts Analysis')
        self.prmBtn = guitools.BetterPushButton("Analysis Parameters")
        self.ROI = naparitools.VispyROIVisual(rect_color='yellow', handle_color='orange')

        mainPanel = QtWidgets.QWidget()
        mainLayout = QtWidgets.QGridLayout()
        mainLayout.setContentsMargins(3, 3, 3, 3)
        mainPanel.setLayout(mainLayout)

        mainLayout.addWidget(self.cwidget, 0, 0, 1, 6)
        mainLayout.addWidget(self.roiButton, 1, 0, 1, 1)
        mainLayout.addWidget(self.runButton, 1, 1, 1, 1)
        mainLayout.addWidget(self.scaleButton, 1, 2, 1, 1)
        mainLayout.addWidget(self.saveRecBtn, 1, 3, 1, 2)
        mainLayout.addWidget(self.loadImgBtn, 1, 5, 1, 1)

        lineSeparator = QtWidgets.QFrame()
        lineSeparator.setFrameShape(QtWidgets.QFrame.HLine)
        lineSeparator.setFrameShadow(QtWidgets.QFrame.Sunken)
        lineSeparator.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.3);  /* Semi-transparent white */
                height: 1px;
                border: none;
            }
        """)
        mainLayout.addWidget(lineSeparator, 3, 0, 1, 6)

        # spacer = QtWidgets.QSpacerItem(10, 10, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        # mainLayout.addItem(spacer, 2, 0, 1, 6)  
        mainLayout.addWidget(self.donutsAnalysisBtn, 5, 0, 1, 3)
        mainLayout.addWidget(self.prmBtn, 5, 3, 1, 3)

        ### list panels ###
        listPanel = QtWidgets.QWidget()
        listLayout = QtWidgets.QVBoxLayout()
        listLayout.setContentsMargins(3, 3, 3, 3)
        listPanel.setLayout(listLayout)
        listPanel.setMaximumWidth(100)

        self.imageListWidget = QtWidgets.QListWidget()
        self.imageListWidget.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        listLayout.addWidget(self.imageListWidget)

        self.buttonLayout = QtWidgets.QVBoxLayout()
        self.addImageBtn = guitools.BetterPushButton("Add Current")
        self.removeImageBtn = guitools.BetterPushButton("Remove")
        self.clearListBtn = guitools.BetterPushButton("Clear All")
        self.saveAllBtn = guitools.BetterPushButton("Save All")
        self.dummyCurrentBtn = guitools.BetterPushButton("dummyCurrent")

        self.buttonLayout.addWidget(self.addImageBtn)
        self.buttonLayout.addWidget(self.removeImageBtn)
        self.buttonLayout.addWidget(self.clearListBtn)
        self.buttonLayout.addWidget(self.saveAllBtn)
        self.buttonLayout.addWidget(self.dummyCurrentBtn)
        listLayout.addLayout(self.buttonLayout)

        # final panel: combine Main and List
        finalLayout = QtWidgets.QHBoxLayout()
        self.setLayout(finalLayout)
        finalLayout.addWidget(mainPanel)
        finalLayout.addWidget(listPanel)
        finalLayout.setSpacing(15)

        # Connect signals
        self.roiButton.toggled.connect(self.sigROIToggled)
        self.runButton.clicked.connect(self.sigRunClicked)
        self.scaleButton.clicked.connect(self.sigScaleClicked)
        self.prmBtn.clicked.connect(self.open_settings_dialog)

        self.imageListWidget.itemSelectionChanged.connect(self.selectionChanged)
        self.addImageBtn.clicked.connect(self.sigAddCurrentToList)
        self.removeImageBtn.clicked.connect(self.removeRecFromList)
        self.clearListBtn.clicked.connect(self.clearList)
        self.clearListBtn.clicked.connect(self.sigClearList)
        self.saveAllBtn.clicked.connect(self.sigSaveAll)
        self.dummyCurrentBtn.clicked.connect(self.addCurrentRunToList)

        self.vb.scene().sigMouseMoved.connect(self.mouseMoved)

    def getROIGraphicsItem(self):
        return self.ROI

    def showROI(self, position, size):
        self.ROI.position = position
        self.ROI.size = size
        self.ROI.show()

    def hideROI(self):
        self.ROI.hide()

    def updateImage(self, image):
        self.img.setImage(image, autoLevels=False)
    
    def open_settings_dialog(self):
        dialog = JsonEditorDialog(self.analysisPrm, self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            updated = dialog.get_updated_params()
            if updated is not None:
                self.analysisPrm = updated
                print("Updated parameters:", self.analysisPrm)
            else:
                print("Invalid JSON input")
    
    def addCurrentToList(self,name=None):
        """ Adds current reconstruction to the list. Adds it first, or second if first is current run """
        if name is None:
            name = datetime.now().strftime("%H_%M_%S")
        item = QtWidgets.QListWidgetItem(name)
        item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
        item.setData(QtCore.Qt.UserRole, False) # not a current scan

        if not self.isFirstItemCurrentRun():
            insertIdx = 0
        else:
            insertIdx = 1
        
        self.imageListWidget.insertItem(insertIdx,item)

        # if not self.isLastItemCurrentRun():
        #     self.imageListWidget.addItem(item)
        # else:
        #     count = self.imageListWidget.count()
        #     self.imageListWidget.insertItem(count - 1, item)

    def removeRecFromList(self):
        idx = self.imageListWidget.currentRow()
        if idx != -1:
            item = self.imageListWidget.item(idx)
            if item.data(QtCore.Qt.UserRole):
                print("Current run not removable")
                # self.imageListWidget.takeItem(idx)
            else:
                self.imageListWidget.takeItem(idx)
                if self.isFirstItemCurrentRun():
                    idx = idx-1
                self.sigRemoveRecFromList.emit(idx)
    
    def clearList(self):
        self.imageListWidget.clear()
    
    def selectionChanged(self):
        """ Emits signals to trigger change of image display"""
        idx = self.imageListWidget.currentRow()
        if idx !=-1:
            item = self.imageListWidget.item(idx)
            if item.data(QtCore.Qt.UserRole): #current run was selected
                self.sigSelectionChanged.emit(None,True)
            else:
                if self.isFirstItemCurrentRun():
                    idx = idx-1
                self.sigSelectionChanged.emit(idx,False)
    
    def mouseMoved(self, pos):
        mouse_point = self.vb.mapSceneToView(pos)
        x = int(mouse_point.x())
        y = int(mouse_point.y())
        self.sigQueryMousePixelValue.emit(x,y)
    
    def updatePixelValue(self,x,y,val):
        self.pixelLabel.setPlainText(f"x:{round(x)}, y:{round(y)}, val:{val:.0f}")

    def erasePixelValue(self):
        self.pixelLabel.setPlainText("")

    def addCurrentRunToList(self):
        """ Adds an item to the list flagged as current run if first item not already current run"""
        if not self.isFirstItemCurrentRun():
            item = QtWidgets.QListWidgetItem("Current Run")
            item.setData(QtCore.Qt.UserRole, True)
            item.setForeground(QtGui.QBrush(QtGui.QColor('gray')))
            self.imageListWidget.insertItem(0,item)
            

    def isFirstItemCurrentRun(self):
        """ Returns a boolean corresponding to if the last item on the list
        has been flagged as a current run (QtCore.Qt.UserRole=True or False)"""

        if self.imageListWidget.count()>0:
            item = self.imageListWidget.item(0)
            return item.data(QtCore.Qt.UserRole)
        else:
            return False
                


class JsonEditorDialog(QtWidgets.QDialog):
    def __init__(self, params_dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Parameters")

        self.text_edit = QtWidgets.QTextEdit(self)
        self.text_edit.setText(json.dumps(params_dict, indent=4))

        self.button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Save | QtWidgets.QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(QtWidgets.QLabel("Edit parameters as JSON:"))
        layout.addWidget(self.text_edit)
        layout.addWidget(self.button_box)

        self.setLayout(layout)

    def get_updated_params(self):
        try:
            return json.loads(self.text_edit.toPlainText())
        except json.JSONDecodeError:
            return None


# Copyright (C) 2020-2021 ImSwitch developers
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
