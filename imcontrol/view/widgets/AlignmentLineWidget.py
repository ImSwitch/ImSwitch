import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtWidgets

from imcontrol.view import guitools as guitools
from .basewidgets import Widget


class AlignmentLineWidget(Widget):
    """ Alignment widget that displays a line on top of the image in the viewbox."""

    sigAlignmentLineMakeClicked = QtCore.Signal()
    sigAlignmentCheckToggled = QtCore.Signal(bool)  # (enabled)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Graphical elements
        self.angleEdit = QtWidgets.QLineEdit(self._defaultPreset.alignmentLine.lineAngle)
        self.alignmentCheck = QtWidgets.QCheckBox('Show Alignment Tool')
        self.alignmentLineMakerButton = guitools.BetterPushButton('Alignment Line')
        pen = pg.mkPen(color=(255, 255, 0), width=0.5,
                       style=QtCore.Qt.SolidLine, antialias=True)
        self.alignmentLine = guitools.VispyLineVisual(movable=True)

        # Add items to GridLayout
        alignmentLayout = QtWidgets.QGridLayout()
        self.setLayout(alignmentLayout)
        alignmentLayout.addWidget(QtWidgets.QLabel('Line Angle'), 0, 0)
        alignmentLayout.addWidget(self.angleEdit, 0, 1)
        alignmentLayout.addWidget(self.alignmentLineMakerButton, 1, 0)
        alignmentLayout.addWidget(self.alignmentCheck, 1, 1)

        # Connect signals
        self.alignmentLineMakerButton.clicked.connect(self.sigAlignmentLineMakeClicked)
        self.alignmentCheck.toggled.connect(self.sigAlignmentCheckToggled)

    def getAngleInput(self):
        return float(self.angleEdit.text())

    def setLineAngle(self, angle):
        self.alignmentLine.angle = angle

    def setLineVisibility(self, visible):
        self.alignmentLine.setVisible(visible)
