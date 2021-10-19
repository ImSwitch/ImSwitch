import pyqtgraph.console
from qtpy import QtWidgets

from .basewidgets import Widget


class ConsoleWidget(Widget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setMinimumHeight(180)

        self.pgWidget = pyqtgraph.console.ConsoleWidget()

        layout = QtWidgets.QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.pgWidget)
        self.setLayout(layout)
