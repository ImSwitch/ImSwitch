import napari
import numpy as np
import pyqtgraph as pg
from PyQt5 import QtCore, QtGui


class ImageWidget(pg.GraphicsLayoutWidget):
    """ Widget containing viewbox that displays the new detector frames.  """

    sigResized = QtCore.Signal()
    sigLevelsChanged = QtCore.Signal()
    sigUpdateLevelsClicked = QtCore.Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.imgs = {}
        self.imgsz = {}
        self.hists = {}

        self.nviewer = napari.Viewer(show=False)

        self.viewCtrlLayout = QtGui.QGridLayout()
        self.viewCtrlLayout.addWidget(self.nviewer.window._qt_window, 0, 0)
        self.setLayout(self.viewCtrlLayout)

        ## Graphical elements
        #self.levelsButton = guitools.BetterPushButton('Update Levels')
        #self.levelsButton.setEnabled(False)
        #self.levelsButton.setSizePolicy(QtGui.QSizePolicy.Preferred,
        #                                QtGui.QSizePolicy.Expanding)
        #proxy = QtGui.QGraphicsProxyWidget()
        #proxy.setWidget(self.levelsButton)
        #self.addItem(proxy, row=0, col=2)
#
        ## Viewbox and related elements
        #self.vb = self.addViewBox(row=1, col=1)
        #self.vb.setMouseMode(pg.ViewBox.RectMode)
        #self.img = guitools.OptimizedImageItem(axisOrder='row-major')
        #self.img.translate(-0.5, -0.5)
        #self.vb.addItem(self.img)
        #self.vb.setAspectLocked(True)
        #self.setAspectLocked(True)
        #self.hist = pg.HistogramLUTItem(image=self.img)
        #self.hist.vb.setLimits(yMin=0, yMax=66000)
        #self.hist.gradient.loadPreset('greyclip')
        #self.grid = guitools.Grid(self.vb)
        #self.crosshair = guitools.Crosshair(self.vb)
        #for tick in self.hist.gradient.ticks:
        #    tick.hide()
        #self.addItem(self.hist, row=1, col=2)
        #for tick in self.hist.gradient.ticks:
        #    tick.hide()
        #self.addItem(self.hist, row=1, col=2)
        ## x and y profiles
        #xPlot = self.addPlot(row=0, col=1)
        #xPlot.hideAxis('left')
        #xPlot.hideAxis('bottom')
        #self.xProfile = xPlot.plot()
        #self.ci.layout.setRowMaximumHeight(0, 40)
        #xPlot.setXLink(self.vb)
        #yPlot = self.addPlot(row=1, col=0)
        #yPlot.hideAxis('left')
        #yPlot.hideAxis('bottom')
        #self.yProfile = yPlot.plot()
        #self.yProfile.rotate(90)
        #self.ci.layout.setColumnMaximumWidth(0, 40)
        #yPlot.setYLink(self.vb)
        #self.nviewer = napari.Viewer(show=False)
#
        ## Connect signals
        #self.vb.sigResized.connect(self.sigResized)
        #self.hist.sigLevelsChanged.connect(self.sigLevelsChanged)
        #self.levelsButton.clicked.connect(self.sigUpdateLevelsClicked)

    def setImages(self, names):
        for name, img in self.imgsz.items():
            if name not in names:
                self.nviewer.layers.remove(img)

        def addImage(name, colormap=None):
            self.imgsz[name] = self.nviewer.add_image(
                np.zeros((1, 1)), rgb=False, name=name, blending='additive', colormap=colormap
            )

        for name in names:
            if name not in self.nviewer.layers:
                try:
                    addImage(name, name.lower())
                except KeyError:
                    addImage(name, 'grayclip')

    def resetView(self):
        self.nviewer.reset_view()


# Grayclip colormap
grayclip = []
for i in range(255):
    grayclip.append([i / 255, i / 255, i / 255])
grayclip.append([1, 0, 0])
napari.utils.colormaps.AVAILABLE_COLORMAPS['grayclip'] = napari.utils.Colormap(
    name='grayclip', colors=grayclip
)
