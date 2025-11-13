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
    sigAddCurrentRun = QtCore.Signal()
    sigSelectionChanged = QtCore.Signal(object,bool,object) #idx, axial boolean, axialName or not
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

        #Main panel: Viewbox + buttons
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

        self.buttonLayout.addWidget(self.addImageBtn)
        self.buttonLayout.addWidget(self.removeImageBtn)
        self.buttonLayout.addWidget(self.clearListBtn)
        self.buttonLayout.addWidget(self.saveAllBtn)
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
        self.addImageBtn.clicked.connect(self.sigAddCurrentRun)
        self.removeImageBtn.clicked.connect(self.removeRecFromList)
        self.clearListBtn.clicked.connect(self.clearList)
        self.clearListBtn.clicked.connect(self.sigClearList)
        self.saveAllBtn.clicked.connect(self.sigSaveAll)

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
        # self.removeCenterCoord()
    
    def open_settings_dialog(self):
        dialog = JsonEditorDialog(self.analysisPrm, self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            updated = dialog.get_updated_params()
            if updated is not None:
                self.analysisPrm = updated
                print("Updated parameters:", self.analysisPrm)
            else:
                print("Invalid JSON input")
    
    def addToList(self,name=None,axialName=None):
        """ Adds a new item to the list, after any current run items. """
        if name is None:
            name = datetime.now().strftime("%Hh%Mm%Ss")
        if axialName is not None:
            name = f"{name}_{axialName}"
        item = QtWidgets.QListWidgetItem(name)
        item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
        item.setData(QtCore.Qt.UserRole, {'isCurrent': False, 'axialName': axialName}) # not a current scan
        insertIdx = self.getInsertIndexAfterCurrent()
        self.imageListWidget.insertItem(insertIdx,item)
    
    
    def addCurrentRunToList(self,axial:bool=False,axialName:str=None):
        """Adds current run items"""
        self.removeCurrentRunItems(axialName)
        if axial and axialName is not None:
            item = QtWidgets.QListWidgetItem(f"Current - {axialName}")
            item.setData(QtCore.Qt.UserRole, {"isCurrent": True, "axialName": axialName})
            item.setForeground(QtGui.QBrush(QtGui.QColor('gray')))
            self.imageListWidget.insertItem(0, item)
        else:
            item = QtWidgets.QListWidgetItem("Current Run")
            item.setData(QtCore.Qt.UserRole, {"isCurrent": True, "axialName": None})
            item.setForeground(QtGui.QBrush(QtGui.QColor('gray')))
            self.imageListWidget.insertItem(0, item)
        self.selectionChanged()

    def removeCurrentRunItems(self,axialName=None):
        """Removes all items marked as current run, or only the current run 
        marked as arg:`axialName` if not None."""
        for i in reversed(range(self.imageListWidget.count())):
            item = self.imageListWidget.item(i)
            data = item.data(QtCore.Qt.UserRole)
            if isinstance(data, dict) and data.get("isCurrent"):
                if axialName is None or data.get("axialName") == axialName:
                    self.imageListWidget.takeItem(i)

            
    # def isFirstItemCurrentRun(self):
    #     """ Returns a boolean corresponding to if the last item on the list
    #     has been flagged as a current run (QtCore.Qt.UserRole=True or False)"""

    #     if self.imageListWidget.count()>0:
    #         item = self.imageListWidget.item(0)
    #         return item.data(QtCore.Qt.UserRole).get("isCurrent")
    #     else:
    #         return False
    
    def isSelectedCurrent(self):
        """ Returns a boolean corresponding to if the current selected item
        has been flagged as a current run"""
        idx = self.imageListWidget.currentRow()        
        if idx ==-1:
            return
        item = self.imageListWidget.item(idx)
        return item.data(QtCore.Qt.UserRole).get("isCurrent")
        

    
    def getInsertIndexAfterCurrent(self):
        """Returns the index after the last current run item."""
        idx = 0
        for i in range(self.imageListWidget.count()):
            data = self.imageListWidget.item(i).data(QtCore.Qt.UserRole)
            if isinstance(data, dict) and data.get("isCurrent"):
                idx += 1
            else:
                break
        return idx


    def removeRecFromList(self):
        idx = self.imageListWidget.currentRow()
        if idx==-1:
            return
        if self.isSelectedCurrent():
            print("Current run not removable")
            return        
        self.imageListWidget.takeItem(idx)
        self.sigRemoveRecFromList.emit(idx-self.getInsertIndexAfterCurrent())

    
    def clearList(self):
        self.imageListWidget.clear()
    
    # def clearCurrentRunItem(self):
    #     if self.isFirstItemCurrentRun():
    #          self.imageListWidget.takeItem(0)
    
    def selectionChanged(self):
        """ Emits signals to trigger change of image display"""
        idx = self.imageListWidget.currentRow()
        if idx ==-1:
            return
        item = self.imageListWidget.item(idx)
        currentRun =  item.data(QtCore.Qt.UserRole).get("isCurrent")
        axialName =  item.data(QtCore.Qt.UserRole).get("axialName")
        if item.data(QtCore.Qt.UserRole).get("isCurrent"): #current run was selected
            axialName = item.data(QtCore.Qt.UserRole).get("axialName")
            self.sigSelectionChanged.emit(None,True,axialName)
        else:
            idx = idx-self.getInsertIndexAfterCurrent()
            self.sigSelectionChanged.emit(idx,False,None)
    
    def mouseMoved(self, pos):
        mouse_point = self.vb.mapSceneToView(pos)
        x = int(mouse_point.x())
        y = int(mouse_point.y())
        self.sigQueryMousePixelValue.emit(x,y)
    
    def updatePixelValue(self,x,y,val):
        self.pixelLabel.setPlainText(f"x:{round(x)}, y:{round(y)}, val:{val:.0f}")

    def erasePixelValue(self):
        self.pixelLabel.setPlainText("")
    
    def displayCenterCoord(self,y,x):
        self.removeCenterCoord()
        self.vline = pg.InfiniteLine(pos=x, angle=90, pen=pg.mkPen('r'))
        self.hline = pg.InfiniteLine(pos=y, angle=0, pen=pg.mkPen('r'))
        self.vb.addItem(self.vline)
        self.vb.addItem(self.hline)

    def removeCenterCoord(self):
        if hasattr(self, 'vline') and self.vline in self.vb.addedItems:
            self.vb.removeItem(self.vline)
            del self.vline 
        if hasattr(self, 'hline') and self.hline in self.vb.addedItems:
            self.vb.removeItem(self.hline)
            del self.hline


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
