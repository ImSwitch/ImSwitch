"""
OptimizedImageItem is a version of pyqtgraph's ImageItem that uses threading and only renders the
part of the image that is visible.

Based on pyqtgraph 0.11.0 code.
"""

import math
import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
from pyqtgraph import debug, functions as fn, Point

try:
    from collections.abc import Callable
except ImportError:
    # fallback for python < 3.3
    from collections import Callable


class OptimizedImageItem(pg.ImageItem):
    sigImageReadyForARGB = QtCore.Signal(np.ndarray, object, object, np.ndarray, bool)
    sigImageDisplayed = QtCore.Signal()

    def __init__(self, *args, **kargs):
        self.shouldPaint = False
        self.onlyRenderVisible = True
        super().__init__(*args, **kargs)

        # Prepare image computation worker
        self.imageARGBWorker = ImageARGBWorker()
        self.imageARGBWorker.qimageProduced.connect(self.updateQImage)
        self.imageARGBThread = QtCore.QThread()
        self.imageARGBWorker.moveToThread(self.imageARGBThread)
        self.sigImageReadyForARGB.connect(self.imageARGBWorker.produceARGB)
        self.imageARGBThread.start()

    def setAutoDownsample(self, ads):
        self.autoDownsample = ads
        self.render()

    def setOnlyRenderVisible(self, orv, render=True):
        self.onlyRenderVisible = orv
        if render:
            self.render()

    def setImage(self, image=None, autoLevels=None, **kargs):
        profile = debug.Profiler()

        gotNewData = False
        if image is None:
            if self.image is None:
                return
        else:
            gotNewData = True
            shapeChanged = (self.image is None or image.shape != self.image.shape)
            image = image.view(np.ndarray)
            if self.image is None or image.dtype != self.image.dtype:
                self._effectiveLut = None
            self.image = image
            if self.image.shape[0] > 2**15-1 or self.image.shape[1] > 2**15-1:
                if 'autoDownsample' not in kargs:
                    kargs['autoDownsample'] = True
            if shapeChanged:
                self.prepareGeometryChange()
                self.informViewBoundsChanged()

        profile()

        if autoLevels is None:
            if 'levels' in kargs:
                autoLevels = False
            else:
                autoLevels = True
        if autoLevels:
            img = self.image
            while img.size > 2**16:
                img = img[::2, ::2]
            mn, mx = np.nanmin(img), np.nanmax(img)
            # mn and mx can still be NaN if the data is all-NaN
            if mn == mx or np.isnan(mn) or np.isnan(mx):
                mn = 0
                mx = 255
            kargs['levels'] = [mn,mx]

        profile()

        self.setOpts(update=False, **kargs)

        profile()

        self.render()

        profile()

        if gotNewData:
            self.sigImageChanged.emit()

    def render(self):
        # Convert data to QImage for display.

        profile = debug.Profiler()
        if self.image is None or self.image.size == 0:
            return

        # Request a lookup table if this image has only one channel
        if self.image.ndim == 2 or self.image.shape[2] == 1:
            if isinstance(self.lut, Callable):
                lut = self.lut(self.image)
            else:
                lut = self.lut
        else:
            lut = None

        if self.autoDownsample:
            # reduce dimensions of image based on screen resolution
            o = self.mapToDevice(QtCore.QPointF(0,0))
            x = self.mapToDevice(QtCore.QPointF(1,0))
            y = self.mapToDevice(QtCore.QPointF(0,1))

            # Check if graphics view is too small to render anything
            if o is None or x is None or y is None:
                return

            w = Point(x-o).length()
            h = Point(y-o).length()
            if w == 0 or h == 0:
                self.qimage = None
                return
            xds = max(1, int(1.0 / w))
            yds = max(1, int(1.0 / h))
            axes = [1, 0] if self.axisOrder == 'row-major' else [0, 1]
            image = fn.downsample(self.image, xds, axis=axes[0])
            image = fn.downsample(image, yds, axis=axes[1])
            self._lastDownsample = (xds, yds)

            # Check if downsampling reduced the image size to zero due to inf values.
            if image.size == 0:
                return
        else:
            image = self.image

        # if the image data is a small int, then we can combine levels + lut
        # into a single lut for better performance
        levels = self.levels
        if levels is not None and levels.ndim == 1 and image.dtype in (np.ubyte, np.uint16):
            if self._effectiveLut is None:
                eflsize = 2**(image.itemsize*8)
                ind = np.arange(eflsize)
                minlev, maxlev = levels
                levdiff = maxlev - minlev
                levdiff = 1 if levdiff == 0 else levdiff  # don't allow division by 0
                if lut is None:
                    efflut = fn.rescaleData(ind, scale=255./levdiff,
                                            offset=minlev, dtype=np.ubyte)
                else:
                    lutdtype = np.min_scalar_type(lut.shape[0]-1)
                    efflut = fn.rescaleData(ind, scale=(lut.shape[0]-1)/levdiff,
                                            offset=minlev, dtype=lutdtype, clip=(0, lut.shape[0]-1))
                    efflut = lut[efflut]

                self._effectiveLut = efflut
            lut = self._effectiveLut
            levels = None

        # Convert single-channel image to 2D array
        if image.ndim == 3 and image.shape[-1] == 1:
            image = image[..., 0]

        # Assume images are in column-major order for backward compatibility
        # (most images are in row-major order)
        if self.axisOrder == 'col-major':
            image = image.transpose((1, 0, 2)[:image.ndim])

        # Get bounds of view box
        viewBounds = np.array(self.getViewBox().viewRange())
        viewBounds[0][0] = max(viewBounds[0][0] - 1, 0)
        viewBounds[0][1] = min(viewBounds[0][1] + 1, image.shape[1])
        viewBounds[1][0] = max(viewBounds[1][0] - 1, 0)
        viewBounds[1][1] = min(viewBounds[1][1] + 1, image.shape[0])

        # Send image to ARGB worker
        self.imageARGBWorker.prepareForNewImage()
        self.sigImageReadyForARGB.emit(image, lut, levels, viewBounds, self.onlyRenderVisible)

    def paint(self, p, *args):
        profile = debug.Profiler()
        if self.image is None:
            return
        if self.qimage is None:
            self.shouldPaint = False
            return
        if not self.shouldPaint:
            # Skip first frame when displaying a new image and there was no image displayed before
            self.shouldPaint = True
            return

        if self.paintMode is not None:
            p.setCompositionMode(self.paintMode)
            profile('set comp mode')

        shape = self.image.shape[:2] if self.axisOrder == 'col-major' else self.image.shape[:2][::-1]
        p.drawImage(QtCore.QRectF(0,0,*shape), self.qimage)
        profile('p.drawImage')
        if self.border is not None:
            p.setPen(self.border)
            p.drawRect(self.boundingRect())

    def save(self, fileName, *args):
        """Save this image to file. Note that this saves the visible image (after scale/color changes), not the original data."""
        self.qimage.save(fileName, *args)

    def getPixmap(self):
        return QtGui.QPixmap.fromImage(self.qimage)

    def updateQImage(self, qimage):
        self.qimage = qimage
        self.update()
        self.sigImageDisplayed.emit()

    def viewTransformChanged(self):
        super().viewTransformChanged()
        if self.onlyRenderVisible:
            self.render()


class ImageARGBWorker(QtCore.QObject):
    qimageProduced = QtCore.pyqtSignal(object)  # QtGui.QImage as type causes crash for some reason

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._numQueuedImages = 0
        self._numQueuedImagesMutex = QtCore.QMutex()

    def produceARGB(self, image, lut, levels, viewBounds, onlyRenderVisible):
        try:
            if self._numQueuedImages > 1:
                return  # Skip this frame in order to catch up

            if onlyRenderVisible:
                # Only render the part of the image that is visible
                originalImageShape = image.shape
                renderBounds = (math.floor(viewBounds[1][0]), math.ceil(viewBounds[1][1]),
                                math.floor(viewBounds[0][0]), math.ceil(viewBounds[0][1]))

                image = image[renderBounds[0]:renderBounds[1], renderBounds[2]:renderBounds[3]]

            argb, alpha = fn.makeARGB(image, lut=lut, levels=levels)

            if onlyRenderVisible:
                argbFull = np.zeros((*originalImageShape, argb.shape[2]), dtype=argb.dtype)
                argbFull[renderBounds[0]:renderBounds[1], renderBounds[2]:renderBounds[3]] = argb
            else:
                argbFull = argb

            qimage = fn.makeQImage(argbFull, alpha, transpose=False)
            self.qimageProduced.emit(qimage)
        finally:
            self._numQueuedImagesMutex.lock()
            self._numQueuedImages -= 1
            self._numQueuedImagesMutex.unlock()

    def prepareForNewImage(self):
        """ Should always be called before the worker receives a new image. """
        self._numQueuedImagesMutex.lock()
        self._numQueuedImages += 1
        self._numQueuedImagesMutex.unlock()
