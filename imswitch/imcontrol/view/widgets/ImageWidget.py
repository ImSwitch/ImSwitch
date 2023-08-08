import numpy as np
from qtpy import QtWidgets

from imswitch.imcommon.model import shortcut
from imswitch.imcommon.view.guitools import naparitools


class ImageWidget(QtWidgets.QWidget):
    """ Widget containing viewbox that displays the new detector frames. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        naparitools.addNapariGrayclipColormap()
        self.napariViewer = naparitools.EmbeddedNapari()
        self.updateLevelsWidget = naparitools.NapariUpdateLevelsWidget.addToViewer(
            self.napariViewer
        )
        self.NapariResetViewWidget = naparitools.NapariResetViewWidget.addToViewer(self.napariViewer, 'right')
        self.NapariShiftWidget = naparitools.NapariShiftWidget.addToViewer(self.napariViewer)
        self.imgLayers = {}

        self.viewCtrlLayout = QtWidgets.QVBoxLayout()
        self.viewCtrlLayout.addWidget(self.napariViewer.get_widget())
        self.setLayout(self.viewCtrlLayout)

        self.grid = naparitools.VispyGridVisual(color='yellow')
        self.grid.hide()
        self.addItem(self.grid)

        self.crosshair = naparitools.VispyCrosshairVisual(color='yellow')
        self.crosshair.hide()
        self.addItem(self.crosshair)

    def setLiveViewLayers(self, names, isRGB = [False]):
        for name, img in self.imgLayers.items():
            if name not in names:
                self.napariViewer.layers.remove(img, force=True)

        def addImage(name, rgb, colormap=None):
            if rgb:
                    inputDummy = np.zeros((3, 3, 3))
                    self.imgLayers[name] = self.napariViewer.add_image(
                        inputDummy, rgb=True, name=f'Live: {name}', blending='additive',  protected=True)
            else:
                inputDummy = np.zeros((1, 1))
                self.imgLayers[name] = self.napariViewer.add_image(
                    inputDummy, rgb=rgb, name=f'Live: {name}', blending='additive',
                    colormap=colormap, protected=True
            )

        if type(names) is not list:
            names = [names]

        for i, name in enumerate(names):
            rgb = isRGB[i]
            if name not in self.napariViewer.layers:
                try:
                    addImage(name, rgb, name.lower())
                except KeyError:
                    addImage(name, rgb, 'grayclip')

    def addStaticLayer(self, name, im):
        self.napariViewer.add_image(im, rgb=False, name=name, blending='additive')

    def getCurrentImageName(self):
        return self.napariViewer.active_layer.name

    def getImage(self, name):
        return self.imgLayers[name].data

    def setImage(self, name, im, scale):
        self.imgLayers[name].data = im
        self.imgLayers[name].scale = tuple(scale)

    def clearImage(self, name):
        self.setImage(name, np.zeros((1, 1)))

    def getImageDisplayLevels(self, name):
        return self.imgLayers[name].contrast_limits

    def setImageDisplayLevels(self, name, minimum, maximum):
        self.imgLayers[name].contrast_limits = (minimum, maximum)

    def getCenterViewbox(self):
        """ Returns the center point of the viewbox, as an (x, y) tuple. """
        return (
            self.napariViewer.window.qt_viewer.camera.center[2],
            self.napariViewer.window.qt_viewer.camera.center[1]
        )

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

    @shortcut('Ctrl+U', "Update levels")
    def updateLevelsButton(self):
        self.updateLevelsWidget.updateLevelsButton.click()


# Copyright (C) 2020-2021 ImSwitch developers
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
