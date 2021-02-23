from PyQt5 import QtCore, QtGui

from imcontrol.view import guitools as guitools
from .basewidgets import Widget


class PositionerWidget(Widget):
    """ Widget in control of the piezzo movement. """

    sigStepUpClicked = QtCore.Signal(str)  # (positionerName)
    sigStepDownClicked = QtCore.Signal(str)  # (positionerName)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.numPositioners = 0
        self.pars = {}
        self.grid = QtGui.QGridLayout()
        self.setLayout(self.grid)

    def addPositioner(self, positionerName):
        self.pars['Label' + positionerName] = QtGui.QLabel(f"<strong>{positionerName} = {0:.2f} µm</strong>")
        self.pars['Label' + positionerName].setTextFormat(QtCore.Qt.RichText)
        self.pars['UpButton' + positionerName] = guitools.BetterPushButton("+")
        self.pars['DownButton' + positionerName] = guitools.BetterPushButton("-")
        self.pars['StepEdit' + positionerName] = QtGui.QLineEdit("0.05")
        self.pars['StepUnit' + positionerName] = QtGui.QLabel(" µm")

        self.grid.addWidget(self.pars['Label' + positionerName], self.numPositioners, 0)
        self.grid.addWidget(self.pars['UpButton' + positionerName], self.numPositioners, 1)
        self.grid.addWidget(self.pars['DownButton' + positionerName], self.numPositioners, 2)
        self.grid.addWidget(QtGui.QLabel("Step"), self.numPositioners, 3)
        self.grid.addWidget(self.pars['StepEdit' + positionerName], self.numPositioners, 4)
        self.grid.addWidget(self.pars['StepUnit' + positionerName], self.numPositioners, 5)

        self.numPositioners += 1

        # Connect signals
        self.pars['UpButton' + positionerName].clicked.connect(
            lambda: self.sigStepUpClicked.emit(positionerName)
        )
        self.pars['DownButton' + positionerName].clicked.connect(
            lambda: self.sigStepDownClicked.emit(positionerName)
        )

    def getStepSize(self, positionerName):
        return float(self.pars['StepEdit' + positionerName].text())

    def updatePosition(self, positionerName, position):
        text = f"<strong>{positionerName} = {position:.2f} µm</strong>"
        self.pars['Label' + positionerName].setText(text)