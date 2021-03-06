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
        self._commChannel.sigAddItemToVb.emit(self._widget.getROIGraphicsItem())

    def run(self):
        if not self.running:
            self.dims = np.array(self._commChannel.getDimsScan()).astype(int)
            self.running = True
            self.beadWorker = BeadWorker(self)
            self.beadWorker.sigNewChunk.connect(self.update)
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
    sigNewChunk = Signal()

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
                self.sigNewChunk.emit()
                
# Copyright (C) 2020, 2021 Staffan Al-Kadhimi, Xavier Casas, Andreas Boden
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