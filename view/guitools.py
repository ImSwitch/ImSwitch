# -*- coding: utf-8 -*-
"""
Created on Fri Feb  6 13:20:02 2015

@author: federico
"""
import os
import time
import numpy as np
import scipy as sp
import h5py as hdf
import tifffile as tiff
import configparser
import collections
from ast import literal_eval
import glob

import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph.ptime as ptime

from tkinter import Tk, filedialog, simpledialog

from lantz import Q_


# taken from https://www.mrao.cam.ac.uk/~dag/CUBEHELIX/cubehelix.py
def cubehelix(gamma=1.0, s=0.5, r=-1.5, h=1.0):
    def get_color_function(p0, p1):
        def color(x):
            xg = x ** gamma
            a = h * xg * (1 - xg) / 2
            phi = 2 * np.pi * (s / 3 + r * x)
            return xg + a * (p0 * np.cos(phi) + p1 * np.sin(phi))
        return color

    array = np.empty((256, 3))
    abytes = np.arange(0, 1, 1/256.)
    array[:, 0] = get_color_function(-0.14861, 1.78277)(abytes) * 255
    array[:, 1] = get_color_function(-0.29227, -0.90649)(abytes) * 255
    array[:, 2] = get_color_function(1.97294, 0.0)(abytes) * 255
    return array


# Check for same name conflict
def getUniqueName(name):

    name, ext = os.path.splitext(name)

    n = 1
    while glob.glob(name + ".*"):
        if n > 1:
            name = name.replace('_{}'.format(n - 1), '_{}'.format(n))
        else:
            name = insertSuffix(name, '_{}'.format(n))
        n += 1

    return ''.join((name, ext))


def attrsToTxt(filename, attrs):
    fp = open(filename + '.txt', 'w')
    fp.write('\n'.join('{}= {}'.format(x[0], x[1]) for x in attrs))
    fp.close()


def insertSuffix(filename, suffix, newExt=None):
    names = os.path.splitext(filename)
    if newExt is None:
        return names[0] + suffix + names[1]
    else:
        return names[0] + suffix + newExt


def fileSizeGB(shape):
    # self.nPixels() * self.nExpositions * 16 / (8 * 1024**3)
    return shape[0]*shape[1]*shape[2] / 2**29


def nFramesPerChunk(shape):
    return int(1.8 * 2**29 / (shape[1] * shape[2]))


def getFilenames(title, filetypes):
    try:
        root = Tk()
        root.withdraw()
        filenames = filedialog.askopenfilenames(title=title,
                                                filetypes=filetypes)
        root.destroy()
        return root.tk.splitlist(filenames)
    except OSError:
        print("No files selected!")


def savePreset(main, filename=None):

    if filename is None:
        root = Tk()
        root.withdraw()
        filename = simpledialog.askstring(title='Save preset',
                                          prompt='Save config file as...')
        root.destroy()

    if filename is None:
        return

    config = configparser.ConfigParser()

    config['Camera'] = {
        'Frame Start': main.frameStart,
        'Shape': main.shape,
        'Shape name': main.tree.p.param('Image frame').param('Shape').value(),
        'Horizontal readout rate': str(main.HRRatePar.value()),
        'Vertical shift speed': str(main.vertShiftSpeedPar.value()),
        'Clock voltage amplitude': str(main.vertShiftAmpPar.value()),
        'Frame Transfer Mode': str(main.FTMPar.value()),
        'Cropped sensor mode': str(main.cropParam.value()),
        'Set exposure time': str(main.expPar.value()),
        'Pre-amp gain': str(main.PreGainPar.value()),
        'EM gain': str(main.GainPar.value())}

    with open(os.path.join(main.presetDir, filename), 'w') as configfile:
        config.write(configfile)

    main.presetsMenu.addItem(filename)


def loadPreset(main, filename=None):

    tree = main.tree.p
    timings = tree.param('Timings')

    if filename is None:
        preset = main.presetsMenu.currentText()

    config = configparser.ConfigParser()
    config.read(os.path.join(main.presetDir, preset))

    configCam = config['Camera']
    shape = configCam['Shape']

    main.shape = literal_eval(shape)
    main.frameStart = literal_eval(configCam['Frame Start'])

    # Frame size handling
    shapeName = configCam['Shape Name']
    if shapeName == 'Custom':
        main.customFrameLoaded = True
        tree.param('Image frame').param('Shape').setValue(shapeName)
        main.frameStart = literal_eval(configCam['Frame Start'])
        main.adjustFrame()
        main.customFrameLoaded = False
    else:
        tree.param('Image frame').param('Shape').setValue(shapeName)

    vps = timings.param('Vertical pixel shift')
    vps.param('Speed').setValue(Q_(configCam['Vertical shift speed']))

    cva = 'Clock voltage amplitude'
    vps.param(cva).setValue(configCam[cva])

    ftm = 'Frame Transfer Mode'
    timings.param(ftm).setValue(configCam.getboolean(ftm))

    csm = 'Cropped sensor mode'
    if literal_eval(configCam[csm]) is not(None):
        main.cropLoaded = True
        timings.param(csm).param('Enable').setValue(configCam.getboolean(csm))
        main.cropLoaded = False

    hrr = 'Horizontal readout rate'
    timings.param(hrr).setValue(Q_(configCam[hrr]))

    expt = 'Set exposure time'
    timings.param(expt).setValue(float(configCam[expt]))

    pag = 'Pre-amp gain'
    tree.param('Gain').param(pag).setValue(float(configCam[pag]))

    tree.param('Gain').param('EM gain').setValue(int(configCam['EM gain']))


def mouseMoved(main, pos):
    if main.vb.sceneBoundingRect().contains(pos):
        mousePoint = main.vb.mapSceneToView(pos)
        x, y = int(mousePoint.x()), int(main.shape[1] - mousePoint.y())
        main.cursorPos.setText('{}, {}'.format(x, y))
        countsStr = '{} counts'.format(main.image[x, int(mousePoint.y())])
        main.cursorPosInt.setText(countsStr)


def bestLimits(arr):
    # Best cmin, cmax algorithm taken from ImageJ routine:
    # http://cmci.embl.de/documents/120206pyip_cooking/
    # python_imagej_cookbook#automatic_brightnesscontrast_button
    pixelCount = arr.size
    limit = pixelCount/10
    threshold = pixelCount/5000
    hist, bin_edges = np.histogram(arr, 256)
    i = 0
    found = False
    count = 0
    while True:
        i += 1
        count = hist[i]
        if count > limit:
            count = 0
        found = count > threshold
        if found or i >= 255:
            break
    hmin = i

    i = 256
    while True:
        i -= 1
        count = hist[i]
        if count > limit:
            count = 0
        found = count > threshold
        if found or i < 1:
            break
    hmax = i

    return bin_edges[hmin], bin_edges[hmax]


def cmapToColormap(cmap, nTicks=16):
    """
    The function 'cmapToColormap' converts the Matplotlib format to the
    internal format of PyQtGraph that is used in the GradientEditorItem. The
    function itself has no dependencies on Matplotlib! Hence the weird if
    clauses with 'hasattr' instead of 'isinstance'.

    Parameters:
    *cmap*: Cmap object. Imported from matplotlib.cm.*
    *nTicks*: Number of ticks to create when dict of functions is used.
    Otherwise unused.

    taken from
    https://github.com/honkomonk/pyqtgraph_sandbox

    """

    # Case #1: a dictionary with 'red'/'green'/'blue' values as list of ranges
    # (e.g. 'jet')
    # The parameter 'cmap' is a 'matplotlib.colors.LinearSegmentedColormap'
    # instance ...
    if hasattr(cmap, '_segmentdata'):
        colordata = getattr(cmap, '_segmentdata')
        if ('red' in colordata) and isinstance(
                colordata['red'], collections.Sequence):

            # collect the color ranges from all channels into one dict to get
            # unique indices
            posDict = {}
            for idx, channel in enumerate(('red', 'green', 'blue')):
                for colorRange in colordata[channel]:
                    posDict.setdefault(
                        colorRange[0], [-1, -1, -1])[idx] = colorRange[2]

            indexList = sorted(posDict.keys())
            # interpolate missing values (== -1)
            for channel in range(3):  # R,G,B
                startIdx = indexList[0]
                emptyIdx = []
                for curIdx in indexList:
                    if posDict[curIdx][channel] == -1:
                        emptyIdx.append(curIdx)
                    elif curIdx != indexList[0]:
                        for eIdx in emptyIdx:
                            rPos = (eIdx - startIdx) / (curIdx - startIdx)
                            vStart = posDict[startIdx][channel]
                            vRange = (
                                posDict[curIdx][channel] -
                                posDict[startIdx][channel])
                            posDict[eIdx][channel] = rPos * vRange + vStart
                        startIdx = curIdx
                        del emptyIdx[:]
            for channel in range(3):  # R,G,B
                for curIdx in indexList:
                    posDict[curIdx][channel] *= 255

            rgb_list = [[i, posDict[i]] for i in indexList]

        # Case #2: a dictionary with 'red'/'green'/'blue' values as functions
        # (e.g. 'gnuplot')
        elif ('red' in colordata) and isinstance(colordata['red'],
                                                 collections.Callable):
            indices = np.linspace(0., 1., nTicks)
            luts = [np.clip(
                np.array(colordata[rgb](indices), dtype=np.float),
                    0, 1) * 255 for rgb in ('red', 'green', 'blue')]
            rgb_list = zip(indices, list(zip(*luts)))

    # If the parameter 'cmap' is a 'matplotlib.colors.ListedColormap'
    # instance, with the attributes 'colors' and 'N'
    elif hasattr(cmap, 'colors') and hasattr(cmap, 'N'):
        colordata = getattr(cmap, 'colors')
        # Case #3: a list with RGB values (e.g. 'seismic')
        if len(colordata[0]) == 3:
            indices = np.linspace(0., 1., len(colordata))
            scaledRgbTuples = [
                (rgbTuple[0] * 255,
                 rgbTuple[1] * 255,
                    rgbTuple[2] * 255) for rgbTuple in colordata]
            rgb_list = zip(indices, scaledRgbTuples)

        # Case #4: a list of tuples with positions and RGB-values
        # (e.g. 'terrain') -> this section is probably not needed anymore!?
        elif len(colordata[0]) == 2:
            rgb_list = [(idx, (vals[0] * 255, vals[1] * 255, vals[2] * 255))
                        for idx, vals in colordata]

    # Case #X: unknown format or datatype was the wrong object type
    else:
        raise ValueError("[cmapToColormap] Unknown cmap format or not a cmap!")

    # Convert the RGB float values to RGBA integer values
    return list([(pos, (int(r), int(g), int(b), 255))
                 for pos, (r, g, b) in rgb_list])


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
            self.filenames = getFilenames("Select HDF5 files",
                                          [('HDF5 files', '.hdf5')])

        else:
            self.filenames = [self.filenames]

        if len(self.filenames) > 0:
            for filename in self.filenames:

                file = hdf.File(filename, mode='r')

                for dataname in file:

                    data = file[dataname]
                    filesize = fileSizeGB(data.shape)
                    filename = (os.path.splitext(filename)[0] + '_' + dataname)
                    attrsToTxt(filename, [at for at in data.attrs.items()])

                    if filesize < 2:
                        time.sleep(5)
                        tiff.imsave(filename + '.tiff', data,
                                    description=dataname, software='Tormenta')
                    else:
                        n = nFramesPerChunk(data.shape)
                        i = 0
                        while i < filesize // 1.8:
                            suffix = '_part{}'.format(i)
                            partName = insertSuffix(filename, suffix, '.tiff')
                            tiff.imsave(partName, data[i*n:(i + 1)*n],
                                        description=dataname,
                                        software='Tormenta')
                            i += 1
                        if filesize % 2 > 0:
                            suffix = '_part{}'.format(i)
                            partName = insertSuffix(filename, suffix, '.tiff')
                            tiff.imsave(partName, data[i*n:],
                                        description=dataname,
                                        software='Tormenta')

                file.close()

        print(self.filenames, 'exported to TIFF')
        self.filenames = None
        self.thread.terminate()
        # for opening attributes this should work:
        # myprops = dict(line.strip().split('=') for line in
        #                open('/Path/filename.txt'))


class Grid():

    def __init__(self, viewBox):

        self.showed = False
        self.vb = viewBox
        self.shape = None
        pen = QtGui.QPen(QtCore.Qt.yellow, 2, QtCore.Qt.DotLine)
        pen2 = QtGui.QPen(QtCore.Qt.yellow, 2.5, QtCore.Qt.SolidLine)

        self.yline1 = pg.InfiniteLine(pen=pen)
        self.yline2 = pg.InfiniteLine(pen=pen)
        self.yline3 = pg.InfiniteLine(pen=pen2)
        self.yline4 = pg.InfiniteLine(pen=pen)
        self.yline5 = pg.InfiniteLine(pen=pen)
        self.xline1 = pg.InfiniteLine(pen=pen, angle=0)
        self.xline2 = pg.InfiniteLine(pen=pen2, angle=0)
        self.xline3 = pg.InfiniteLine(pen=pen2, angle=0)
        self.xline4 = pg.InfiniteLine(pen=pen2, angle=0)
        self.xline5 = pg.InfiniteLine(pen=pen, angle=0)

    def update(self, shape):
        self.yline1.setPos(0.25*shape[0])
        self.yline2.setPos(0.375*shape[0])
        self.yline3.setPos(0.50*shape[0])
        self.yline4.setPos(0.625*shape[0])
        self.yline5.setPos(0.75*shape[0])
        self.xline1.setPos(0.25*shape[1])
        self.xline2.setPos(0.375*shape[1])
        self.xline3.setPos(0.50*shape[1])
        self.xline4.setPos(0.625*shape[1])
        self.xline5.setPos(0.75*shape[1])

    def toggle(self):
        if self.showed:
            self.hide()
        else:
            self.show()

    def show(self):
        self.vb.addItem(self.xline1)
        self.vb.addItem(self.xline2)
        self.vb.addItem(self.xline3)
        self.vb.addItem(self.xline4)
        self.vb.addItem(self.xline5)
        self.vb.addItem(self.yline1)
        self.vb.addItem(self.yline2)
        self.vb.addItem(self.yline3)
        self.vb.addItem(self.yline4)
        self.vb.addItem(self.yline5)
        self.showed = True

    def hide(self):
        self.vb.removeItem(self.xline1)
        self.vb.removeItem(self.xline2)
        self.vb.removeItem(self.xline3)
        self.vb.removeItem(self.xline4)
        self.vb.removeItem(self.xline5)
        self.vb.removeItem(self.yline1)
        self.vb.removeItem(self.yline2)
        self.vb.removeItem(self.yline3)
        self.vb.removeItem(self.yline4)
        self.vb.removeItem(self.yline5)
        self.showed = False


class TwoColorGrid():

    def __init__(self, viewBox, shape=(512, 512)):

        self.showed = False
        self.vb = viewBox
        self.shape = shape

        pen = QtGui.QPen(QtCore.Qt.yellow, 1, QtCore.Qt.SolidLine)
        pen2 = QtGui.QPen(QtCore.Qt.yellow, 0.75, QtCore.Qt.DotLine)

        self.rectT = QtGui.QGraphicsRectItem(192, 118, 128, 128)
        self.rectT.setPen(pen)
        self.rectR = QtGui.QGraphicsRectItem(192, 266, 128, 128)
        self.rectR.setPen(pen)
        self.yLine = pg.InfiniteLine(pos=0.5*self.shape[0], pen=pen2)
        self.xLine = pg.InfiniteLine(pos=0.5*self.shape[1], pen=pen2, angle=0)
        self.xLineT = pg.InfiniteLine(pos=182, pen=pen2, angle=0)
        self.xLineR = pg.InfiniteLine(pos=330, pen=pen2, angle=0)

    def toggle(self):
        if self.showed:
            self.hide()
        else:
            self.show()

    def show(self):
        self.vb.addItem(self.rectT)
        self.vb.addItem(self.rectR)
        self.vb.addItem(self.yLine)
        self.vb.addItem(self.xLine)
        self.vb.addItem(self.xLineR)
        self.vb.addItem(self.xLineT)
        self.showed = True

    def hide(self):
        self.vb.removeItem(self.rectT)
        self.vb.removeItem(self.rectR)
        self.vb.removeItem(self.yLine)
        self.vb.removeItem(self.xLine)
        self.vb.removeItem(self.xLineR)
        self.vb.removeItem(self.xLineT)
        self.showed = False


class Crosshair():

    def __init__(self, viewBox):

        self.showed = False

        self.vLine = pg.InfiniteLine(pos=0, angle=90, movable=False)
        self.hLine = pg.InfiniteLine(pos=0, angle=0,  movable=False)
        self.vb = viewBox

    def mouseMoved(self, pos):
        if self.vb.sceneBoundingRect().contains(pos):
            mousePoint = self.vb.mapSceneToView(pos)
            self.vLine.setPos(mousePoint.x())
            self.hLine.setPos(mousePoint.y())

    def mouseClicked(self):
        try:
            self.vb.scene().sigMouseMoved.disconnect(self.mouseMoved)
        except:
            pass

    def toggle(self):
        if self.showed:
            self.hide()
        else:
            self.show()

    def show(self):
        self.vb.scene().sigMouseClicked.connect(self.mouseClicked)
        self.vb.scene().sigMouseMoved.connect(self.mouseMoved)
        self.vb.addItem(self.vLine, ignoreBounds=False)
        self.vb.addItem(self.hLine, ignoreBounds=False)
        self.showed = True

    def hide(self):
        self.vb.removeItem(self.vLine)
        self.vb.removeItem(self.hLine)
        self.showed = False


class ROI(pg.ROI):

    def __init__(self, shape, pos, handlePos, handleCenter, color, *args,
                 **kwargs):

        self.mainShape = shape

        pg.ROI.__init__(self, pos, size=shape, pen=color, *args, **kwargs)
        self.addScaleHandle(handlePos, handleCenter, lockAspect=True)

        self.label = pg.TextItem()
        self.label.setPos(self.pos()[0] + self.size()[0],
                          self.pos()[1] + self.size()[1])
        self.label.setText('{}x{}'.format(shape[0], shape[1]))

        self.sigRegionChanged.connect(self.updateText)

    def updateText(self):
        self.label.setPos(self.pos()[0] + self.size()[0],
                          self.pos()[1] + self.size()[1])
        size = np.round(self.size()).astype(np.int)
        self.label.setText('{}x{}'.format(size[0], size[1]))

    def hide(self, *args, **kwargs):
        super().hide(*args, **kwargs)
        self.label.hide()

    def show(self, *args, **kwargs):
        super().show(*args, **kwargs)
        self.label.show()


class cropROI(pg.ROI):

    def __init__(self, shape, vb, *args, **kwargs):

        self.mainShape = shape

        pg.ROI.__init__(self, pos=(shape[0], shape[1]), size=(128, 128),
                        scaleSnap=True, translateSnap=True, movable=False,
                        pen='y', *args, **kwargs)
        self.addScaleHandle((0, 1), (1, 0))


class AlignWidgetAverage(QtGui.QFrame):

    def __init__(self, main, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.main = main

        self.ROI = ROI((50, 50), self.main.vb, (0, 0), handlePos=(1, 0),
                       handleCenter=(0, 1), color=pg.mkPen(255, 0, 0),
                       scaleSnap=True, translateSnap=True)

        self.ROI.hide()
        self.graph = SumpixelsGraph()
        self.roiButton = QtGui.QPushButton('Show ROI')
        self.roiButton.setCheckable(True)
        self.roiButton.clicked.connect(self.ROItoggle)
        self.resetButton = QtGui.QPushButton('Reset graph')
        self.resetButton.clicked.connect(self.resetGraph)

        grid = QtGui.QGridLayout()
        self.setLayout(grid)
        grid.addWidget(self.graph, 0, 0, 1, 6)
        grid.addWidget(self.roiButton, 1, 0, 1, 1)
        grid.addWidget(self.resetButton, 1, 1, 1, 1)
        grid.setRowMinimumHeight(0, 300)

        self.scansPerS = 10
        self.alignTime = 1000 / self.scansPerS
        self.alignTimer = QtCore.QTimer()
        self.alignTimer.timeout.connect(self.updateValue)
#        self.alignTimer.start(self.alignTime)

    def resetGraph(self):
        self.graph.resetData()

    def ROItoggle(self):
        if self.roiButton.isChecked() is False:
            self.ROI.hide()
            self.alignTimer.stop()
            self.roiButton.setText('Show ROI')
        else:
            self.ROI.show()
            self.roiButton.setText('Hide ROI')
            self.alignTimer.start(self.alignTime)

    def updateValue(self):

        if self.main.liveviewButton.isChecked():
            self.selected = self.ROI.getArrayRegion(
                self.main.latest_images[self.main.currCamIdx], self.main.img)
            value = np.mean(self.selected)
            self.graph.updateGraph(value)
        else:
            pass

    def closeEvent(self, *args, **kwargs):

        self.alignTimer.stop()

        super().closeEvent(*args, **kwargs)


class SumpixelsGraph(pg.GraphicsWindow):
    """The graph window class"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowTitle('Average of area')
        self.setAntialiasing(True)

        self.npoints = 400
        self.data = np.zeros(self.npoints)
        self.ptr = 0

        # Graph without a fixed range
        self.statistics = pg.LabelItem(justify='right')
        self.addItem(self.statistics)
        self.statistics.setText('---')
        self.plot = self.addPlot(row=1, col=0)
        self.plot.setLabels(bottom=('Time', 's'), left=('Intensity', 'au'))
        self.plot.showGrid(x=True, y=True)
        self.sumCurve = self.plot.plot(pen='y')

        self.time = np.zeros(self.npoints)
        self.startTime = ptime.time()

    def resetData(self):
        """Set all data points to zero, useful if going from very large values
        to very small values"""
        self.data = np.zeros(self.npoints)
        self.time = np.zeros(self.npoints)
        self.startTime = ptime.time()
        self.ptr = 0

    def updateGraph(self, value):
        """ Update the data displayed in the graphs
        """
        if self.ptr < self.npoints:
            self.data[self.ptr] = value
            self.time[self.ptr] = ptime.time() - self.startTime
            self.sumCurve.setData(self.time[1:self.ptr + 1],
                                  self.data[1:self.ptr + 1])

        else:
            self.data[:-1] = self.data[1:]
            self.data[-1] = value
            self.time[:-1] = self.time[1:]
            self.time[-1] = ptime.time() - self.startTime

            self.sumCurve.setData(self.time, self.data)

        self.ptr += 1


class AlignWidgetXYProject(QtGui.QFrame):

    def __init__(self, main, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.main = main

        self.ROI = ROI((50, 50), self.main.vb, (0, 0), handlePos=(1, 0),
                       handleCenter=(0, 1), color=pg.mkPen(255, 0, 0),
                       scaleSnap=True, translateSnap=True)

        self.ROI.hide()
        self.graph = ProjectionGraph()
        self.roiButton = QtGui.QPushButton('Show ROI')
        self.roiButton.setCheckable(True)
        self.roiButton.clicked.connect(self.ROItoggle)

        self.Xradio = QtGui.QRadioButton('X dimension')
        self.Yradio = QtGui.QRadioButton('Y dimension')

        grid = QtGui.QGridLayout()
        self.setLayout(grid)
        grid.addWidget(self.graph, 0, 0, 1, 6)
        grid.addWidget(self.roiButton, 1, 0, 1, 1)
        grid.addWidget(self.Xradio, 1, 1, 1, 1)
        grid.addWidget(self.Yradio, 1, 2, 1, 1)

        self.scansPerS = 10
        self.alignTime = 1000 / self.scansPerS
        self.alignTimer = QtCore.QTimer()
        self.alignTimer.timeout.connect(self.updateValue)
        self.alignTimer.start(self.alignTime)

        # 2 zeros because it has to have the attribute "len"
        self.latest_values = np.zeros(2)
        self.s_fac = 0.3

    def resetGraph(self):
        self.graph.resetData()

    def ROItoggle(self):
        if self.roiButton.isChecked() is False:
            self.ROI.hide()
            self.roiButton.setText('Show ROI')
        else:
            self.ROI.show()
            self.roiButton.setText('Hide ROI')

    def updateValue(self):

        if (self.main.liveviewButton.isChecked() and
                self.roiButton.isChecked()):
            self.selected = self.ROI.getArrayRegion(self.main.latest_images[0],
                                                    self.main.img)
        else:
            self.selected = self.main.latest_images[self.main.currCamIdx]

        if self.Xradio.isChecked():
            values = np.mean(self.selected, 0)
        else:
            values = np.mean(self.selected, 1)

        if len(self.latest_values) == len(values):
            smoothed = self.s_fac*values + (1-self.s_fac)*self.latest_values
            self.latest_values = smoothed
        else:
            smoothed = values
            self.latest_values = values

        self.graph.updateGraph(smoothed)

    def closeEvent(self, *args, **kwargs):
        self.alignTimer.stop()
        super().closeEvent(*args, **kwargs)


class ProjectionGraph(pg.GraphicsWindow):
    """The graph window class"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowTitle('Average of area')
        self.setAntialiasing(True)

        self.npoints = 400
        self.data = np.zeros(self.npoints)
        self.ptr = 0

        # Graph without a fixed range
        self.statistics = pg.LabelItem(justify='right')
        self.addItem(self.statistics)
        self.statistics.setText('---')
        self.plot = self.addPlot(row=1, col=0)
        self.plot.setLabels(bottom=('Time', 's'),
                            left=('Intensity', 'au'))
        self.plot.showGrid(x=True, y=True)
        self.sumCurve = self.plot.plot(pen='y')

        self.startTime = ptime.time()

    def updateGraph(self, values):
        """ Update the data displayed in the graphs
        """
        self.data = values
        self.sumCurve.setData(np.arange(len(self.data)), self.data)
        
class FFTWidget(QtGui.QFrame):
    """ FFT Transform window for alignment """
    def __init__(self, main, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.main = main
        
        # Do FFT button
        self.doButton = QtGui.QPushButton('Do FFT')
        self.doButton.clicked.connect(self.doFFT)

        # Period button and text for changing the vertical lines
        self.changePosButton = QtGui.QPushButton('Period (pix)')
        self.changePosButton.clicked.connect(self.changePos)
        
        self.linePos = QtGui.QLineEdit('4')
        
        grid = QtGui.QGridLayout()
        self.setLayout(grid)
        self.cwidget = pg.GraphicsLayoutWidget()        
        
        self.vb = self.cwidget.addViewBox(row=1, col=1)
        self.vb.setMouseMode(pg.ViewBox.RectMode)
        self.img = pg.ImageItem()
        self.img.translate(-0.5, -0.5)
        self.vb.addItem(self.img)
        self.vb.setAspectLocked(True)
        self.hist = pg.HistogramLUTItem(image=self.img)
        self.hist.vb.setLimits(yMin=0, yMax=66000)
        self.cubehelixCM = pg.ColorMap(np.arange(0, 1, 1/256), cubehelix().astype(int))
        self.hist.gradient.setColorMap(self.cubehelixCM)
        for tick in self.hist.gradient.ticks:
            tick.hide()
        self.cwidget.addItem(self.hist, row=1, col=2)
        
        # Vertical and horizontal lines 
        self.vline = pg.InfiniteLine()
        self.hline = pg.InfiniteLine()
        self.rvline = pg.InfiniteLine()
        self.lvline = pg.InfiniteLine()
        self.uhline = pg.InfiniteLine()
        self.dhline = pg.InfiniteLine()
        
        self.vline.hide()
        self.hline.hide()
        self.rvline.hide()
        self.lvline.hide()
        self.uhline.hide()
        self.dhline.hide()

        self.vb.addItem(self.vline)
        self.vb.addItem(self.hline)
        self.vb.addItem(self.lvline)
        self.vb.addItem(self.rvline)
        self.vb.addItem(self.uhline)
        self.vb.addItem(self.dhline)
        

        grid.addWidget(self.cwidget, 0, 0, 1, 6)
        grid.addWidget(self.doButton, 1, 0, 1, 1)
        grid.addWidget(self.changePosButton, 2, 0, 1, 1)
        grid.addWidget(self.linePos, 2, 1, 1, 1)
        grid.setRowMinimumHeight(0, 300)

        self.init = False

    def doFFT(self):
        " FFT of the latest camera image, centering (0, 0) in the middle with fftshift "
        f = np.fft.fftshift(np.log10(abs(np.fft.fft2(self.main.latest_images[self.main.currCamIdx]))))
        self.img.setImage(f, autoLevels=False)
        
        # By default F = 0.25, period of T = 4 pixels
        pos = 0.25
        self.imgWidth = self.img.width()
        self.imgHeight = self.img.height()
        self.vb.setAspectLocked()
        self.vb.setLimits(xMin=-0.5, xMax=self.imgWidth, minXRange=4,
                  yMin=-0.5, yMax=self.imgHeight, minYRange=4)
        self.vline.setValue(0.5*self.imgWidth)
        self.hline.setAngle(0)
        self.hline.setValue(0.5*self.imgHeight)
        self.rvline.setValue((0.5+pos)*self.imgWidth)
        self.lvline.setValue((0.5-pos)*self.imgWidth)
        self.dhline.setAngle(0)
        self.dhline.setValue((0.5-pos)*self.imgHeight)
        self.uhline.setAngle(0)
        self.uhline.setValue((0.5+pos)*self.imgHeight)
        
    def closeEvent(self, *args, **kwargs):
        super().closeEvent(*args, **kwargs)

    def changePos(self):
        # Move vertical lines
        pos = float(1 / float(self.linePos.text()))
        self.rvline.setValue((0.5+pos)*self.imgWidth)
        self.lvline.setValue((0.5-pos)*self.imgWidth)
        self.dhline.setAngle(0)
        self.dhline.setValue((0.5-pos)*self.imgHeight)
        self.uhline.setAngle(0)
        self.uhline.setValue((0.5+pos)*self.imgHeight)
        
        if self.init == False:
            self.vline.show()
            self.hline.show()
            self.rvline.show()
            self.lvline.show()
            self.uhline.show()
            self.dhline.show()
            self.init = True

