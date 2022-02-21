from qtpy import QtCore, QtWidgets

from imswitch.imcontrol.view import guitools
from .basewidgets import Widget


class TriggerScopeWidget(Widget):
    """ Widget for controlling the parameters of a TriggerScope. """

    sigRunToggled = QtCore.Signal(bool)  # (enabled)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.runButton = guitools.BetterPushButton('Run')
        self.runButton.setCheckable(True)
        self.runButton.clicked.connect(self.sigRunToggled)

        grid = QtWidgets.QGridLayout()
        self.setLayout(grid)
        grid.addWidget(self.runButton, 0, 0, 1, 1)

