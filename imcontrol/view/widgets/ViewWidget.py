from PyQt5 import QtCore, QtGui

from imcontrol.view import guitools as guitools
from .basewidgets import Widget


class ViewWidget(Widget):
    """ View settings (liveview, grid, crosshair). """

    sigGridToggled = QtCore.Signal(bool)  # (enabled)
    sigCrosshairToggled = QtCore.Signal(bool)  # (enabled)
    sigLiveviewToggled = QtCore.Signal(bool)  # (enabled)
    sigDetectorChanged = QtCore.Signal(str)  # (detectorName)
    sigNextDetectorClicked = QtCore.Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Graphical elements
        # Grid
        self.gridButton = guitools.BetterPushButton('Grid')
        self.gridButton.setCheckable(True)
        self.gridButton.setSizePolicy(QtGui.QSizePolicy.Preferred,
                                      QtGui.QSizePolicy.Expanding)

        # Crosshair
        self.crosshairButton = guitools.BetterPushButton('Crosshair')
        self.crosshairButton.setCheckable(True)
        self.crosshairButton.setSizePolicy(QtGui.QSizePolicy.Preferred,
                                           QtGui.QSizePolicy.Expanding)
        # liveview
        self.liveviewButton = guitools.BetterPushButton('LIVEVIEW')
        self.liveviewButton.setStyleSheet("font-size:20px")
        self.liveviewButton.setCheckable(True)
        self.liveviewButton.setSizePolicy(QtGui.QSizePolicy.Preferred,
                                          QtGui.QSizePolicy.Expanding)
        self.liveviewButton.setEnabled(True)

        # Detector list
        self.detectorListBox = QtGui.QHBoxLayout()
        self.detectorListLabel = QtGui.QLabel('Current detector:')
        self.detectorList = QtGui.QComboBox()
        self.nextDetectorButton = guitools.BetterPushButton('Next')
        self.nextDetectorButton.hide()
        self.detectorListBox.addWidget(self.detectorListLabel)
        self.detectorListBox.addWidget(self.detectorList, 1)
        self.detectorListBox.addWidget(self.nextDetectorButton)

        # Add elements to GridLayout
        self.viewCtrlLayout = QtGui.QGridLayout()
        self.setLayout(self.viewCtrlLayout)
        self.viewCtrlLayout.addLayout(self.detectorListBox, 0, 0, 1, 2)
        self.viewCtrlLayout.addWidget(self.liveviewButton, 1, 0, 1, 2)
        self.viewCtrlLayout.addWidget(self.gridButton, 2, 0)
        self.viewCtrlLayout.addWidget(self.crosshairButton, 2, 1)

        # Connect signals
        self.gridButton.toggled.connect(self.sigGridToggled)
        self.crosshairButton.toggled.connect(self.sigCrosshairToggled)
        self.liveviewButton.toggled.connect(self.sigLiveviewToggled)
        self.detectorList.currentIndexChanged.connect(
            lambda index: self.sigDetectorChanged.emit(self.detectorList.itemData(index))
        )
        self.nextDetectorButton.clicked.connect(self.sigNextDetectorClicked)

    def selectNextDetector(self):
        self.detectorList.setCurrentIndex(
            (self.detectorList.currentIndex() + 1) % self.detectorList.count()
        )

    def setDetectorList(self, detectorModels):
        self.nextDetectorButton.setVisible(len(detectorModels) > 1)
        for detectorName, detectorModel in detectorModels.items():
            self.detectorList.addItem(f'{detectorModel} ({detectorName})', detectorName)

    def setViewToolsEnabled(self, enabled):
        self.crosshairButton.setEnabled(enabled)
        self.gridButton.setEnabled(enabled)