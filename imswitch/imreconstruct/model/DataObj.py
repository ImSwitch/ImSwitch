import os

import h5py
import numpy as np
import tifffile as tiff
import zarr

from imswitch.imcommon.model import initLogger


class DataObj:
    def __init__(self, name, datasetName, *, path=None, file=None):
        self.__logger = initLogger(self, instanceName=f'{name}/{datasetName}')

        self.name = name
        self.dataPath = path
        self.darkFrame = None
        self._meanData = None
        self._file = file
        self._data = None
        self._datasetName = datasetName
        self._attrs = None
        self.__logger = initLogger(self, tryInheritParent=False)

    @property
    def data(self):
        if self._data is not None:
            return self._data

        if isinstance(self._file, h5py.File):
            self._data = np.array(self._file.get(self._datasetName)[:])
        elif isinstance(self._file, tiff.TiffFile):
            self._data = self._file.asarray()
        elif isinstance(self._file, zarr.hierarchy.Group):
            self._data = np.array(self._file[self._datasetName])
        return self._data

    @property
    def attrs(self):
        if self._attrs is not None:
            return self._attrs

        if isinstance(self._file, h5py.File):
            attrs = dict(self._file.attrs)
            attrs.update(dict(self._file[self.datasetName].attrs))
            self._attrs = attrs
        if isinstance(self._file, zarr.hierarchy.Group):
            attrs = dict(self._file.attrs)
            attrs.update(dict(self._file[self.datasetName].attrs))
            self._attrs = attrs
        return self._attrs

    @property
    def dataLoaded(self):
        return self.data is not None

    @property
    def datasetName(self):
        return self._datasetName

    @property
    def numFrames(self):
        return np.shape(self.data)[0] if self.data is not None else None

    def checkAndLoadData(self):
        if not self.dataLoaded:
            try:
                self._file, self._datasetName = DataObj._open(self.dataPath, self._datasetName)
                if self.data is not None:
                    self.__logger.debug('Data loaded')
            except Exception:
                pass

    def checkAndLoadDarkFrame(self):
        pass

    def checkAndUnloadData(self):
        if self._file is not None:
            try:
                self._file.close()
            except Exception:
                self.__logger.error('Error closing file')

        self._file = None
        self._data = None
        self._attrs = None
        self._meanData = None

    def getMeanData(self):
        if self._meanData is None:
            self._meanData = np.array(np.mean(self.data, 0), dtype=np.float32)

        return self._meanData

    @staticmethod
    def getDatasetNames(path):
        file, _ = DataObj._open(path, allowMultipleDatasets=True)
        try:
            if isinstance(file, h5py.File) or isinstance(file, zarr.hierarchy.Group):
                return list(file.keys())
            elif isinstance(file, tiff.TiffFile):
                return ['default']
            else:
                raise ValueError(f'Unsupported file type "{type(file).__name__}"')
        finally:
            if isinstance(file, h5py.File):
                file.close()

    @staticmethod
    def _open(path, datasetName=None, allowMultipleDatasets=False):
        ext = os.path.splitext(path)[1]
        if ext in ['.hdf5', '.hdf']:
            file = h5py.File(path, 'r')
            if len(file) < 1:
                raise RuntimeError('File does not contain any datasets')
            elif len(file) > 1 and datasetName is None and not allowMultipleDatasets:
                raise RuntimeError('File contains multiple datasets')

            if datasetName is None and not allowMultipleDatasets:
                datasetName = list(file.keys())[0]

            return file, datasetName
        elif ext in ['.tiff', '.tif']:
            return tiff.TiffFile(path), None
        elif ext in ['.zarr']:
            file = zarr.open(path, mode='r')
            if len(file) < 1:
                raise RuntimeError('File does not contain any datasets')
            elif len(file) > 1 and datasetName is None and not allowMultipleDatasets:
                raise RuntimeError('File contains multiple datasets')

            if datasetName is None and not allowMultipleDatasets:
                datasetName = list(file.keys())[0]

            return file, datasetName
        else:
            raise ValueError(f'Unsupported file extension "{ext}"')

    def describesSameAs(self, other):  # Don't use __eq__, that makes the class unhashable
        try:
            sameFile = self._file == other._file or self._file.filename == other._file.filename
        except AttributeError:
            sameFile = False

        return (self.name == other.name and
                self.dataPath == other.dataPath and
                sameFile and
                self.datasetName == other.datasetName)

    def checkLock(self):
        if self.attrs['writing']:
            raise OSError(f'Writing in progress')


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
