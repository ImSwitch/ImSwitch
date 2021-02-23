# -*- coding: utf-8 -*-
"""
Created on Fri Feb  6 13:20:02 2015

@author: federico
"""
import os
import time

import h5py as hdf
import tifffile as tiff
from pyqtgraph.Qt import QtCore

from imcontrol.view.guitools import filetools


def fileSizeGB(shape):
    # self.nPixels() * self.nExpositions * 16 / (8 * 1024**3)
    return shape[0] * shape[1] * shape[2] / 2 ** 29


def nFramesPerChunk(shape):
    return int(1.8 * 2 ** 29 / (shape[1] * shape[2]))


class TiffConverterThread(QtCore.QThread):

    def __init__(self, filename=None):
        super().__init__()

        self.converter = TiffConverter(filename, self)
        self.converter.moveToThread(self)
        self.started.connect(self.converter.run)
        self.start()


class TiffConverter(QtCore.QObject):

    def __init__(self, filenames, thread, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filenames = filenames
        self.thread = thread

    def run(self):

        if self.filenames is None:
            self.filenames = filetools.getFilenames("Select HDF5 files",
                                                    [('HDF5 files', '*.hdf5')])

        else:
            self.filenames = [self.filenames]

        if len(self.filenames) > 0:
            for filename in self.filenames:

                file = hdf.File(filename, mode='r')

                for dataname in file:

                    data = file[dataname]
                    filesize = fileSizeGB(data.shape)
                    filename = (os.path.splitext(filename)[0] + '_' + dataname)
                    filetools.attrsToTxt(filename, [at for at in data.attrs.items()])

                    if filesize < 2:
                        time.sleep(5)
                        tiff.imsave(filename + '.tiff', data,
                                    description=dataname, software='Tormenta')
                    else:
                        n = nFramesPerChunk(data.shape)
                        i = 0
                        while i < filesize // 1.8:
                            suffix = '_part{}'.format(i)
                            partName = filetools.insertSuffix(filename, suffix, '.tiff')
                            tiff.imsave(partName, data[i * n:(i + 1) * n],
                                        description=dataname,
                                        software='Tormenta')
                            i += 1
                        if filesize % 2 > 0:
                            suffix = '_part{}'.format(i)
                            partName = filetools.insertSuffix(filename, suffix, '.tiff')
                            tiff.imsave(partName, data[i * n:],
                                        description=dataname,
                                        software='Tormenta')

                file.close()

        print(self.filenames, 'exported to TIFF')
        self.filenames = None
        self.thread.terminate()
        # for opening attributes this should work:
        # myprops = dict(line.strip().split('=') for line in
        #                open('/Path/filename.txt'))
