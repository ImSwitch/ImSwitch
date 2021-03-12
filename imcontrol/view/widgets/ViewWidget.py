from pyqtgraph.Qt import QtCore, QtWidgets

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
        self.gridButton.setSizePolicy(QtWidgets.QSizePolicy.Preferred,
                                      QtWidgets.QSizePolicy.Expanding)

        # Crosshair
        self.crosshairButton = guitools.BetterPushButton('Crosshair')
        self.crosshairButton.setCheckable(True)
        self.crosshairButton.setSizePolicy(QtWidgets.QSizePolicy.Preferred,
                                           QtWidgets.QSizePolicy.Expanding)
        # liveview
        self.liveviewButton = guitools.BetterPushButton('LIVEVIEW')
        self.liveviewButton.setStyleSheet("font-size:20px")
        self.liveviewButton.setCheckable(True)
        self.liveviewButton.setSizePolicy(QtWidgets.QSizePolicy.Preferred,
                                          QtWidgets.QSizePolicy.Expanding)
        self.liveviewButton.setEnabled(True)

        # Detector list
        self.detectorListBox = QtWidgets.QHBoxLayout()
        self.detectorListLabel = QtWidgets.QLabel('Current detector:')
        self.detectorList = QtWidgets.QComboBox()
        self.nextDetectorButton = guitools.BetterPushButton('Next')
        self.nextDetectorButton.hide()
        self.detectorListBox.addWidget(self.detectorListLabel)
        self.detectorListBox.addWidget(self.detectorList, 1)
        self.detectorListBox.addWidget(self.nextDetectorButton)

        # Add elements to GridLayout
        self.viewCtrlLayout = QtWidgets.QGridLayout()
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

# Copyright (C) 2020, 2021 TestaLab
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