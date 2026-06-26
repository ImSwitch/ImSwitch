import numpy as np
from qtpy import QtWidgets

from imswitch.imcommon.model import shortcut
from imswitch.imcommon.view.guitools import naparitools
from imswitch.imcontrol.model.foci_affine import pixel_affine_to_napari_world_affine


class ImageWidget(QtWidgets.QWidget):
    """ Widget containing viewbox that displays the new detector frames. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        naparitools.addNapariGrayclipColormap()
        self.napariViewer = naparitools.EmbeddedNapari()
        self.updateLevelsWidget = naparitools.NapariUpdateLevelsWidget.addToViewer(
            self.napariViewer
        )
        #LR: The next to widgets are etSTED specific and i.m.o. not needed --> at least for now commented
        #self.NapariResetViewWidget = naparitools.NapariResetViewWidget.addToViewer(self.napariViewer, 'right')
        #self.NapariSumImageWidget = naparitools.NapariSumImageWidget.addToViewer(self.napariViewer, 'right')
        self.NapariShiftWidget = naparitools.NapariShiftWidget.addToViewer(self.napariViewer)
        self.imgLayers = {}
        self._liveLayerAffinesPxYX = {}
        self._allLiveLayerAffinePxYX = None

        self.viewCtrlLayout = QtWidgets.QVBoxLayout()
        self.viewCtrlLayout.addWidget(self.napariViewer.get_widget())
        self.setLayout(self.viewCtrlLayout)

        self.grid = naparitools.VispyGridVisual(color='yellow')
        self.grid.hide()
        self.addItem(self.grid)

        self.crosshair = naparitools.VispyCrosshairVisual(color='yellow')
        self.crosshair.hide()
        self.addItem(self.crosshair)

    def setLiveViewLayers(self, names):
        names = list(names)

        for name, img in list(self.imgLayers.items()):
            if name not in names:
                self.napariViewer.layers.remove(img, force=True)
                del self.imgLayers[name]
                self._liveLayerAffinesPxYX.pop(name, None)

        def addImage(name, colormap=None):
            self.imgLayers[name] = self.napariViewer.add_image(
                np.zeros((1, 1)), rgb=False, name=f'Live: {name}', blending='additive',
                colormap=colormap, protected=True
            )
            if self._allLiveLayerAffinePxYX is not None:
                self._liveLayerAffinesPxYX[name] = self._allLiveLayerAffinePxYX
            self._applyStoredLiveLayerAffine(name)

        for name in names:
            if name not in self.imgLayers:
                try:
                    addImage(name, name.lower())
                except KeyError:
                    addImage(name, 'grayclip')

    def addStaticLayer(self, name, im):
        self.addOrUpdateImageLayer(name, im, blending='additive')

    def addOrUpdateImageLayer(self, name, im, **kwargs):
        if name in self.napariViewer.layers:
            layer = self.napariViewer.layers[name]
            layer.data = im
            layer.refresh()
            return layer

        return self.napariViewer.add_image(im, rgb=False, name=name, **kwargs)

    def addOrUpdatePointsLayer(self, name, points_yx, **kwargs):
        protected = bool(kwargs.pop('protected', False))
        if name in self.napariViewer.layers:
            layer = self.napariViewer.layers[name]
            layer.data = points_yx
        else:
            layer = self.napariViewer.add_points(points_yx, name=name, **kwargs)
        layer.protected = protected
        layer.refresh()
        return layer

    def addOrUpdateShapesLayer(self, name, data, **kwargs):
        protected = bool(kwargs.pop('protected', False))
        if name in self.napariViewer.layers:
            layer = self.napariViewer.layers[name]
            layer.data = data
        else:
            layer = self.napariViewer.add_shapes(data, name=name, **kwargs)
        layer.protected = protected
        layer.refresh()
        return layer

    def removeNapariLayer(self, name):
        if name in self.napariViewer.layers:
            self.napariViewer.layers.remove(self.napariViewer.layers[name], force=True)

    def getNapariLayerNames(self):
        return [layer.name for layer in self.napariViewer.layers]

    def getDisplayLayerNames(self):
        return self.getNapariLayerNames()

    def getLiveLayerNames(self):
        return list(self.imgLayers.keys())

    def getLiveLayer(self, name):
        return self.imgLayers[name]

    def getLiveImage(self, name):
        return self.imgLayers[name].data

    def getNapariLayerData(self, layer_name):
        return self.napariViewer.layers[layer_name].data

    def getActiveImageLayerData(self):
        layer = self.napariViewer.active_layer
        if layer is None or layer.__class__.__name__ != 'Image' or not hasattr(layer, 'data'):
            return None

        return layer.data

    def setLiveLayerAffine(self, name, affine):
        self._liveLayerAffinesPxYX[name] = np.asarray(affine, dtype=float)
        self._applyStoredLiveLayerAffine(name)

    def clearLiveLayerAffine(self, name):
        self._liveLayerAffinesPxYX.pop(name, None)
        if name in self.imgLayers:
            self.imgLayers[name].affine = np.eye(3)
            self.imgLayers[name].refresh()

    def setAllLiveLayersAffine(self, affine):
        self._allLiveLayerAffinePxYX = np.asarray(affine, dtype=float)
        for name in self.imgLayers:
            self.setLiveLayerAffine(name, affine)

    def clearAllLiveLayersAffine(self):
        self._allLiveLayerAffinePxYX = None
        for name in list(self.imgLayers):
            self.clearLiveLayerAffine(name)

    def setNapariLayerAffine(self, layer_name, affine):
        layer = self.napariViewer.layers[layer_name]
        layer.affine = np.asarray(affine, dtype=float)
        layer.refresh()

    def clearNapariLayerAffine(self, layer_name):
        self.setNapariLayerAffine(layer_name, np.eye(3))

    def setDisplayLayerAffine(self, layer_name, affine):
        live_name = self._liveLayerNameFromNapariLayerName(layer_name)
        if live_name is not None:
            self.setLiveLayerAffine(live_name, affine)
            return

        layer = self.napariViewer.layers[layer_name]
        layer.affine = pixel_affine_to_napari_world_affine(affine, layer.scale)
        layer.refresh()

    def clearDisplayLayerAffine(self, layer_name):
        live_name = self._liveLayerNameFromNapariLayerName(layer_name)
        if live_name is not None:
            self.clearLiveLayerAffine(live_name)
            return

        self.clearNapariLayerAffine(layer_name)

    def setAllDisplayLayerAffines(self, affine):
        self._allLiveLayerAffinePxYX = np.asarray(affine, dtype=float)
        for layer_name in self.getDisplayLayerNames():
            self.setDisplayLayerAffine(layer_name, affine)

    def clearAllDisplayLayerAffines(self):
        self._allLiveLayerAffinePxYX = None
        for layer_name in self.getDisplayLayerNames():
            self.clearDisplayLayerAffine(layer_name)

    def _liveLayerNameFromNapariLayerName(self, layer_name):
        for live_name, layer in self.imgLayers.items():
            if layer.name == layer_name:
                return live_name

        return None

    def _applyStoredLiveLayerAffine(self, name):
        if name not in self.imgLayers:
            return

        layer = self.imgLayers[name]
        affine_px_yx = self._liveLayerAffinesPxYX.get(name)
        if affine_px_yx is None:
            layer.affine = np.eye(3)
        else:
            layer.affine = pixel_affine_to_napari_world_affine(affine_px_yx, layer.scale)
        layer.refresh()

    def getCurrentImageName(self):
        return self.napariViewer.active_layer.name

    def getImage(self, name):
        return self.imgLayers[name].data

    def setImage(self, name, im, scale):
        layer = self.imgLayers[name]

        old_scale = tuple(layer.scale)
        new_scale = tuple(scale)

        layer.data = im
        layer.scale = new_scale

        # If scale changes, recompute affine because napari affine is in world coordinates.
        if old_scale != new_scale:
            self._applyStoredLiveLayerAffine(name)

    def clearImage(self, name):
        self.setImage(name, np.zeros((1, 1)), self.imgLayers[name].scale)

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
