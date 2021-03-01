import napari
import numpy as np
import pyqtgraph as pg
from PyQt5 import QtCore, QtWidgets

import imcontrol.view.guitools as guitools


class ImageWidget(pg.GraphicsLayoutWidget):
    """ Widget containing viewbox that displays the new detector frames.  """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        guitools.addNapariGrayclipColormap()
        self.napariViewer = napari.Viewer(show=False)
        self.imgLayers = {}

        self.viewCtrlLayout = QtWidgets.QGridLayout()
        self.viewCtrlLayout.addWidget(self.napariViewer.window._qt_window, 0, 0)
        self.setLayout(self.viewCtrlLayout)

    def setLayers(self, names):
        for name, img in self.imgLayers.items():
            if name not in names:
                self.napariViewer.layers.remove(img)

        def addImage(name, colormap=None):
            self.imgLayers[name] = self.napariViewer.add_image(
                np.zeros((1, 1)), rgb=False, name=name, blending='additive', colormap=colormap
            )

        # This is for preventing reconstruction images displaying here. TODO: Fix the issue
        self.napariViewer.add_image(np.zeros((1, 1)), name='(do not touch)')

        for name in names:
            if name not in self.napariViewer.layers:
                try:
                    addImage(name, name.lower())
                except KeyError:
                    addImage(name, 'grayclip')

    def getImage(self, name):
        return self.imgLayers[name].data.T

    def setImage(self, name, im):
        self.imgLayers[name].data = im.T

    def clearImage(self, name):
        self.setImage(name, np.zeros((1, 1)))

    def getImageDisplayLevels(self, name):
        return self.imgLayers[name].contrast_limits

    def setImageDisplayLevels(self, name, minimum, maximum):
        self.imgLayers[name].contrast_limits = (minimum, maximum)

    def resetView(self):
        self.napariViewer.reset_view()
