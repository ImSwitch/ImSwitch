import napari
import numpy as np
from pyqtgraph.Qt import QtWidgets

from imswitch.imcontrol.view import guitools as guitools


class ImageWidget(QtWidgets.QWidget):
    """ Widget containing viewbox that displays the new detector frames.  """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        guitools.addNapariGrayclipColormap()
        self.napariViewer = napari.Viewer(show=False)
        self.imgLayers = {}

        self.viewCtrlLayout = QtWidgets.QGridLayout()
        self.viewCtrlLayout.addWidget(self.napariViewer.window._qt_window, 0, 0)
        self.setLayout(self.viewCtrlLayout)

        self.grid = guitools.VispyGridVisual(color='yellow')
        self.grid.hide()
        self.addItem(self.grid)

        self.crosshair = guitools.VispyCrosshairVisual(color='yellow')
        self.crosshair.hide()
        self.addItem(self.crosshair)

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
        return self.imgLayers[name].data

    def setImage(self, name, im):
        self.imgLayers[name].data = im

    def clearImage(self, name):
        self.setImage(name, np.zeros((1, 1)))

    def getImageDisplayLevels(self, name):
        return self.imgLayers[name].contrast_limits

    def setImageDisplayLevels(self, name, minimum, maximum):
        self.imgLayers[name].contrast_limits = (minimum, maximum)

    def getCenterROI(self):
        """ Returns center of viewbox to center a ROI. """
        return self.napariViewer.window.qt_viewer.camera.center[-2:]

    def updateGrid(self, imShape):
        self.grid.update(imShape)

    def setGridVisible(self, visible):
        self.grid.setVisible(visible)

    def setCrosshairVisible(self, visible):
        self.crosshair.setVisible(visible)

    def resetView(self):
        self.napariViewer.reset_view()

    def addItem(self, item):
        item.attach(self.napariViewer,
                    canvas=self.napariViewer.window.qt_viewer.canvas,
                    view=self.napariViewer.window.qt_viewer.view,
                    parent=self.napariViewer.window.qt_viewer.view.scene,
                    order=1e6 + 8000)

    def removeItem(self, item):
        item.detach()
        

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
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
