from imswitch.imcommon.view.guitools.FileWatcher import FileWatcher
from imswitch.imreconstruct.model import DataObj
import os
from .basecontrollers import ImRecWidgetController
from imswitch.imcommon.model.logging import initLogger
import zarr
import numpy as np
from ome_zarr.io import parse_url
from ome_zarr.writer import write_image
from time import perf_counter
import tifffile as tiff
import h5py


class WatcherFrameController(ImRecWidgetController):
    """ Linked to WatcherFrame. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attrs = None
        self.recPath = None
        self._widget.sigWatchChanged.connect(self.toggleWatch)
        self._widget.sigChangeFolder.connect(lambda: self._widget.updateFileList(self._commChannel.extension.value()))
        self._commChannel.sigExecutionFinished.connect(self.executionFinished)
        self._commChannel.extension.sigValueChanged.connect(self.extensionChanged)
        self.execution = False
        self.toExecute = []
        self.current = None
        self.t0 = None
        self.extension = None
        self.__logger = initLogger(self, tryInheritParent=False)

    def toggleWatch(self, checked):
        if checked:
            self.execution = False
            self.extension = self._commChannel.extension.value()
            rec_dir = self._widget.path + '/rec'
            if not os.path.isdir(rec_dir):
                os.mkdir(rec_dir)
            self.watcher = FileWatcher(self._widget.path, self.extension, 1)
            self._widget.updateFileList(self.extension)
            files = self.watcher.filesInDirectory()
            self.toExecute = files
            self.watcher.sigNewFiles.connect(self.newFiles)
            self.watcher.start()
            self.runNextFile()
        else:
            self.execution = False
            self.watcher.stop()
            self.watcher.quit()
            self.toExecute = []

    def extensionChanged(self):
        self._widget.updateFileList(self._commChannel.extension.value())
        self._widget.watchCheck.setChecked(False)

    def newFiles(self, files):
        self._widget.updateFileList(self.extension)
        self.toExecute.extend(files)
        try:
            self.runNextFile()
        except OSError:
            self.__logger.error("Writing in progress.")
            self.watcher.removeFromList(files)

    def runNextFile(self):
        if len(self.toExecute) and not self.execution:
            newFile = self.toExecute.pop()
            self.current = self._widget.path + '/' + newFile
            self.recPath = self._widget.path + '/' + 'rec' + '/' + 'rec_' + newFile
            datasets = DataObj.getDatasetNames(self.current)
            dataObjs = []
            for d in datasets:
                file, _ = DataObj._open(self.current, d)
                dataObj = DataObj(os.path.basename(self.current), d, path=self.current, file=file)
                dataObj.checkLock()
                dataObjs.append(dataObj)
                self.attrs = dataObj.attrs
            self.execution = True
            self.t0 = perf_counter()
            self._commChannel.sigReconstruct.emit(dataObjs, True)

    def executionFinished(self, image):
        if self.execution:
            self.execution = False
            self.saveImage(image)
            diff = perf_counter() - self.t0
            self.watcher.addToLog(self.current, [str(self.t0), str(diff)])
            self._widget.updateFileList(self.extension)
            self.runNextFile()

    def saveImage(self, image):
        image = np.squeeze(image[:, 0, :, :, :, :])
        image = np.reshape(image, (1, *image.shape))
        extension = self._commChannel.extension.value()
        if not os.path.exists(self.recPath):
            if extension == 'zarr':
                store = parse_url(self.recPath + '.tmp', mode="w").store
                root = zarr.group(store=store)
                root.attrs["ImSwitchData"] = self.attrs["ImSwitchData"]
                write_image(image=image, group=root, axes="zyx")
                store.close()
                os.rename(self.recPath + '.tmp', self.recPath)
                tiff.imwrite(self.recPath.split('.')[0] + ".tiff", image)
            if extension == 'hdf5':
                # h = h5py.File(self.recPath + '.tmp', 'w')
                # dset = h.create_dataset('data', data=image)
                # self.__logger.debug(type(self.attrs))
                # for k in self.attrs.keys():
                #     dset.attrs[k] = self.attrs[k]
                # h.close()
                # os.rename(self.recPath + '.tmp', self.recPath)
                tiff.imwrite(self.recPath.split('.')[0] + ".tiff", image)


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
