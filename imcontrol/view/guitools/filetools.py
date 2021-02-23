# -*- coding: utf-8 -*-
"""
Created on Fri Feb  6 13:20:02 2015

@author: federico
"""

import configparser
import glob
import os
from ast import literal_eval

from lantz import Q_
from pyqtgraph.Qt import QtWidgets


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


def getFilenames(title, filetypes):
    filter = ';;'.join(['{name} ({extension})' for name, extension in filetypes])

    files, _ = QtWidgets.QFileDialog.getOpenFileNames(caption=title, filter=filter)
    return files


def savePreset(main, filename=None):
    if filename is None:
        filename, okClicked = QtWidgets.QInputDialog.getText(None, 'Save preset',
                                                         'Save config file as...')

        if not okClicked:
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
    if literal_eval(configCam[csm]) is not None:
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
