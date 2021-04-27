import pyqtgraph.console


class ConsoleWidget(pyqtgraph.console.ConsoleWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setMinimumHeight(180)
