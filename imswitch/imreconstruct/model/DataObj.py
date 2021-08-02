import os

import h5py
import numpy as np
import tifffile as tiff


class DataObj:
    def __init__(self, name, *, path=None, file=None, datasetName=None):
        self.name = name
        self.dataPath = path
        self.darkFrame = None
        self._meanData = None
        self._file = file
        self._data = None
        self._datasetName = datasetName
        self._attrs = None

    @property
    def data(self):
        if self._data is not None:
            return self._data

        if isinstance(self._file, h5py.File):
            self._data = np.array(self._file.get(self._datasetName)[:])
        elif isinstance(self._file, tiff.TiffFile):
            self._data = self._file.asarray()

        return self._data

    @property
    def attrs(self):
        if self._attrs is not None:
            return self._attrs

        if isinstance(self._file, h5py.File):
            self._attrs = dict(self._file.attrs)

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
                self._file, self._datasetName = self._loadFromPath(self.dataPath, self._datasetName)
                if self.data is not None:
                    print('Data loaded')
            except Exception:
                pass

    def checkAndLoadDarkFrame(self):
        pass

    def checkAndUnloadData(self):
        if self._file is not None:
            try:
                self._file.close()
            except Exception:
                print('Error closing file')

        self._file = None
        self._data = None
        self._attrs = None
        self._meanData = None

    def getMeanData(self):
        if self._meanData is None:
            self._meanData = np.array(np.mean(self.data, 0), dtype=np.float32)

        return self._meanData


    @staticmethod
    def _loadFromPath(path, datasetName=None):
        path = os.path.abspath(path)
        try:
            ext = os.path.splitext(path)[1]
            if ext in ['.hdf5', '.hdf']:
                file = h5py.File(path, 'r')
                if len(file) < 1:
                    raise RuntimeError('File does not contain any datasets')
                elif len(file) > 1 and datasetName is None:
                    raise RuntimeError('File contains multiple datasets')

                if datasetName is None:
                    datasetName = list(file.keys())[0]

                return file, datasetName
            elif ext in ['.tiff', '.tif']:
                return tiff.TiffFile(path), None
            else:
                raise ValueError(f'Unsupported file extension "{ext}"')
        except Exception:
            print('Error while loading data')
            return None, None

    def __eq__(self, other):
        return (self.name == other.name and
                self.dataPath == other.dataPath and
                self._file.filename == other._file.filename and
                self.datasetName == other.datasetName)


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
