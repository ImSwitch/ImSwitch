from qtpy import QtCore, QtWidgets

from imswitch.imcontrol.view import guitools as guitools
from .basewidgets import Widget


class StateSelectorWidget(Widget):
    """ Widget in control of a state selector. """

    sigItemChanged = QtCore.Signal(int, str)  # (state, stateselectorName)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pars = {}
        self.grid = QtWidgets.QGridLayout()
        self.setLayout(self.grid)
        # added items

    def addStateSelector(self, name):
        self.label = QtWidgets.QLabel(f'<strong>{name}</strong>')
        self.combobox = QtWidgets.QComboBox()
        self.combobox.addItem("0")
        self.combobox.addItem("1")
        self.combobox.addItem("2")
        self.combobox.addItem("3")
        self.combobox.addItem("4")
        self.combobox.addItem("5")
        self.combobox.addItem("6")
        self.combobox.addItem("7")
        self.combobox.addItem("8")
        self.combobox.addItem("9")
        self.grid.addWidget(self.label)
        self.grid.addWidget(self.combobox)

        self.combobox.currentIndexChanged.connect(
            lambda i: self.sigItemChanged.emit(i, name)
        )