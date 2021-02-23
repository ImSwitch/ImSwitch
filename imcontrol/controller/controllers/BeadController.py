import numpy as np

from imcommon.framework import Thread, Worker, Signal
from .basecontrollers import ImConWidgetController


class BeadController(ImConWidgetController):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.running = False
        self.addROI()

        # Connect BeadRecWidget signals
        self._widget.sigROIToggled.connect(self.roiToggled)
        self._widget.sigRunClicked.connect(self.run)

    def roiToggled(self, enabled):
        """ Show or hide ROI."""
        if enabled:
            ROIsize = (64, 64)
            ROIcenter = self._commChannel.getCenterROI()

            ROIpos = (ROIcenter[0] - 0.5 * ROIsize[0],
                      ROIcenter[1] - 0.5 * ROIsize[1])

            self._widget.showROI(ROIpos, ROIsize)
        else:
            self._widget.hideROI()

        self._widget.updateDisplayState(enabled)

    def addROI(self):
        """ Adds the ROI to ImageWidget viewbox through the CommunicationChannel. """
        self._commChannel.addItemTovb.emit(self._widget.getROIGraphicsItem())

    def run(self):
        if not self.running:
            self.dims = np.array(self._commChannel.getDimsScan()).astype(int)
            self.running = True
            self.beadWorker = BeadWorker(self)
            self.beadWorker.newChunk.connect(self.update)
            self.thread = Thread()
            self.beadWorker.moveToThread(self.thread)
            self.thread.started.connect(self.beadWorker.run)
            self._master.detectorsManager.execOnAll(lambda c: c.flushBuffers())
            self.thread.start()
        else:
            self.running = False
            self.thread.quit()
            self.thread.wait()

    def update(self):
        self._widget.updateImage(np.resize(self.recIm, self.dims + 1))


class BeadWorker(Worker):
    newChunk = Signal()
    stop = Signal()

    def __init__(self, controller):
        super().__init__()
        self.__controller = controller

    def run(self):
        dims = np.array(self.__controller.dims)
        N = (dims[0] + 1) * (dims[1] + 1)
        self.__controller.recIm = np.zeros(N)
        i = 0

        while self.__controller.running:
            newImages, _ = self.__controller._master.detectorsManager.execOnCurrent(lambda c: c.getChunk())
            n = len(newImages)
            if n > 0:
                roiItem = self.__controller._widget.getROIGraphicsItem()
                pos = roiItem.pos()
                size = roiItem.size()

                x0 = int(pos[0])
                y0 = int(pos[1])
                x1 = int(x0 + size[0])
                y1 = int(y0 + size[1])

                for j in range(0, n):
                    img = newImages[j]
                    img = img[y0:y1, x0:x1]
                    mean = np.mean(img)
                    self.__controller.recIm[i] = mean
                    i = i + 1
                    if i == N:
                        i = 0
                self.newChunk.emit()