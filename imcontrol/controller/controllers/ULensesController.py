import numpy as np

from .basecontrollers import ImConWidgetController


class ULensesController(ImConWidgetController):
    """ Linked to ULensesWidget. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.addPlot()

        # Connect ULensesWidget signals
        self._widget.sigULensesClicked.connect(self.updateGrid)
        self._widget.sigUShowLensesChanged.connect(self.toggleULenses)

    def addPlot(self):
        """ Adds ulensesPlot to ImageWidget viewbox through the CommunicationChannel. """
        self._commChannel.addItemTovb.emit(self._widget.getPlotGraphicsItem())

    def updateGrid(self):
        """ Updates plot with new parameters. """
        x, y, px, up = self._widget.getParameters()
        size_x, size_y = self._master.detectorsManager.execOnCurrent(lambda c: c.shape)
        pattern_x = np.arange(x, size_x, up / px)
        pattern_y = np.arange(y, size_y, up / px)
        grid = np.array(np.meshgrid(pattern_x, pattern_y)).T.reshape(-1, 2)
        self._widget.setData(x=grid[:, 0], y=grid[:, 1])

    def toggleULenses(self, show):
        """ Shows or hides grid. """
        self._widget.ulensesPlot.setVisible(show)