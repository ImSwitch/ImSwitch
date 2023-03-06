import csv

import pyqtgraph as pg
from imswitch.imcontrol.view import guitools as guitools
from imswitch.imcontrol.view.widgets.DeckWidget import TableWidgetDragRows
from qtpy import QtCore, QtWidgets

from .basewidgets import NapariHybridWidget


class DeckScanWidget(NapariHybridWidget):
    """ Widget in control of the piezo movement. """
    sigStepUpClicked = QtCore.Signal(str, str)  # (positionerName, axis)
    sigStepDownClicked = QtCore.Signal(str, str)  # (positionerName, axis)
    sigsetSpeedClicked = QtCore.Signal(str, str)  # (positionerName, axis)

    sigHomeClicked = QtCore.Signal(str, str)  # (positionerName, axis)
    sigZeroClicked = QtCore.Signal(str, str)  # (positionerName, axis)

    sigGoToClicked = QtCore.Signal(str, str)  # (positionerName, axis)
    sigAddCurrentClicked = QtCore.Signal(str, str)  # (positionerName, axis)
    sigAddClicked = QtCore.Signal(str, str)  # (positionerName, axis)

    sigPresetSelected = QtCore.Signal(str)  # (presetName)
    sigLoadPresetClicked = QtCore.Signal()
    sigSavePresetClicked = QtCore.Signal()
    sigSavePresetAsClicked = QtCore.Signal()
    sigDeletePresetClicked = QtCore.Signal()
    sigPresetScanDefaultToggled = QtCore.Signal()


    sigScanInitFilterPos = QtCore.Signal(bool)  # (enabled)
    sigScanShowLast = QtCore.Signal(bool)  # (enabled)
    sigScanStop = QtCore.Signal(bool)  # (enabled)
    sigScanStart = QtCore.Signal(bool)  # (enabled)

    sigShowToggled = QtCore.Signal(bool)  # (enabled)
    sigPIDToggled = QtCore.Signal(bool)  # (enabled)
    sigUpdateRateChanged = QtCore.Signal(float)  # (rate)

    sigSliderLEDValueChanged = QtCore.Signal(float)  # (value)

    def addScanner(self): #, detectorName, detectorModel, detectorParameters, detectorActions,supportedBinnings, roiInfos):
        self.scan_list = TableWidgetDragRows()
        self.scan_list.setColumnCount(5)
        self.scan_list.setHorizontalHeaderLabels(["Slot", "Well","Offset", "Z_focus","Absolute"])
        self.scan_list_items = 0
        # self.scan_list.setEditTriggers(self.scan_list.NoEditTriggers)
        self.buttonOpen = guitools.BetterPushButton('Open')
        self.buttonSave = guitools.BetterPushButton('Save')

        self.buttonOpen.clicked.connect(self.handleOpen)
        self.buttonSave.clicked.connect(self.handleSave)

        self.grid.addWidget(self.scan_list,12, 0, 1, 4)
        self.grid.addWidget(self.buttonOpen,11, 0, 1, 1)
        self.grid.addWidget(self.buttonSave,11, 1, 1, 1)


    # https://stackoverflow.com/questions/12608835/writing-a-qtablewidget-to-a-csv-or-xls
    # Extra blank row issue: https://stackoverflow.com/questions/3348460/csv-file-written-with-python-has-blank-lines-between-each-row
    def handleSave(self):
        path = QtWidgets.QFileDialog.getSaveFileName(
            self, 'Save File', '', 'CSV(*.csv)')
        # if not path[0] != "":
        try:
            with open(path[0], 'w', newline='') as stream:
                writer = csv.writer(stream)
                for row in range(self.scan_list.rowCount()):
                    rowdata = []
                    for column in range(self.scan_list.columnCount()):
                        item = self.scan_list.item(row, column)
                        if item is not None:
                            rowdata.append(
                                item.text())
                        else:
                            rowdata.append('')
                    writer.writerow(rowdata)
        except:
            print("Action Save cancelled.")

        # else:
        #     self.__logger.debug("Empty path: handleSave")

    def handleOpen(self):
        path = QtWidgets.QFileDialog.getOpenFileName(
            self, 'Open File', '', 'CSV(*.csv)')
        # if not path.isEmpty():
        try:
            with open(path[0], 'r') as stream:
                self.scan_list.setHorizontalHeaderLabels(["Slot", "Well","Offset", "Z_focus","Absolute"])
                self.scan_list.setRowCount(0)
                self.scan_list_items = 0
                for rowdata in csv.reader(stream):
                    if len(rowdata)>0:
                        self.scan_list.insertRow(self.scan_list_items)
                        for column, data in enumerate(rowdata):
                            item = QtWidgets.QTableWidgetItem(data)
                            self.scan_list.setItem(self.scan_list_items, column, item)
                        self.scan_list_items += 1
        except:
            print("Action Open cancelled.")

    # def __init__(self, *args, **kwargs):
    def __post_init__(self):

        # super().__init__(*args, **kwargs)

        self.ScanFrame = pg.GraphicsLayoutWidget()

        # initialize all GUI elements
        # period
        self.ScanLabelTimePeriod = QtWidgets.QLabel('Period T (s):') # TODO: change for a h:m:s Widget
        self.ScanValueTimePeriod = QtWidgets.QLineEdit('180')
        # duration
        self.ScanLabelTimeDuration = QtWidgets.QLabel('N Rounds:')
        self.ScanValueTimeDuration = QtWidgets.QLineEdit('2')
        # z-stack
        self.ScanLabelZStack = QtWidgets.QLabel('Z-Stack (min,max,n_slices):')
        self.ScanValueZmin = QtWidgets.QLineEdit('0')
        self.ScanValueZmax = QtWidgets.QLineEdit('0.5')
        self.ScanValueZsteps = QtWidgets.QLineEdit('5')
        self.ScanDoZStack = QtWidgets.QCheckBox('Perform Z-Stack')
        self.ScanDoZStack.setCheckable(True)
        # autofocus
        self.autofocusLabel = QtWidgets.QLabel('Autofocus (range, steps, every n-th round): ')
        self.autofocusRange = QtWidgets.QLineEdit('0.5')
        self.autofocusSteps = QtWidgets.QLineEdit('0.05')
        self.autofocusPeriod = QtWidgets.QLineEdit('1')
        self.autofocusInitial = QtWidgets.QLineEdit('0')

        self.autofocusLED1Checkbox = QtWidgets.QCheckBox('LED 1')
        self.autofocusLED1Checkbox.setCheckable(True)
        self.autofocusSelectionLabel = QtWidgets.QLabel('Lightsource for AF: ')
        self.autofocusInitialZLabel = QtWidgets.QLabel('Autofocus (Initial Z): ')
        # LED
        valueDecimalsLED = 1
        valueRangeLED = (0, 2 ** 8)
        tickIntervalLED = 0.01
        singleStepLED = 1

        self.sliderLED, self.LabelLED = self.setupSliderGui('Intensity (LED):', valueDecimalsLED, valueRangeLED,
                                                          tickIntervalLED, singleStepLED)
        self.sliderLED.valueChanged.connect(
            lambda value: self.sigSliderLEDValueChanged.emit(value)
        )
        # Scan buttons
        self.ScanLabelFileName = QtWidgets.QLabel('FileName:')
        self.ScanEditFileName = QtWidgets.QLineEdit('Scan')
        self.ScanNRounds = QtWidgets.QLabel('Number of rounds: ')
        self.ScanStartButton = guitools.BetterPushButton('Start')
        self.ScanStartButton.setCheckable(False)
        self.ScanStartButton.toggled.connect(self.sigScanStart)
        self.ScanStopButton = guitools.BetterPushButton('Stop')
        self.ScanStopButton.setCheckable(False)
        self.ScanStopButton.toggled.connect(self.sigScanStop)
        self.ScanShowLastButton = guitools.BetterPushButton('Show Last')
        self.ScanShowLastButton.setCheckable(False)
        self.ScanShowLastButton.toggled.connect(self.sigScanShowLast)
        # Defining layout
        self.grid = QtWidgets.QGridLayout()
        self.setLayout(self.grid)

        self.grid.addWidget(self.ScanLabelTimePeriod, 0, 0, 1, 1)
        self.grid.addWidget(self.ScanValueTimePeriod, 0, 1, 1, 1)
        self.grid.addWidget(self.ScanLabelTimeDuration, 0, 2, 1, 1)
        self.grid.addWidget(self.ScanValueTimeDuration, 0, 3, 1, 1)
        # z-stack
        self.grid.addWidget(self.ScanLabelZStack, 1, 0, 1, 1)
        self.grid.addWidget(self.ScanValueZmin, 1, 1, 1, 1)
        self.grid.addWidget(self.ScanValueZmax, 1, 2, 1, 1)
        self.grid.addWidget(self.ScanValueZsteps, 1, 3, 1, 1)
        self.grid.addWidget(self.LabelLED, 6, 0, 1, 1)
        self.grid.addWidget(self.sliderLED, 6, 1, 1, 3)
        # filesettings
        self.grid.addWidget(self.ScanLabelFileName, 7, 0, 1, 1)
        self.grid.addWidget(self.ScanEditFileName, 7, 1, 1, 1)
        self.grid.addWidget(self.ScanNRounds, 7, 2, 1, 1)
        self.grid.addWidget(self.ScanDoZStack, 7, 3, 1, 1)
        # autofocus
        self.grid.addWidget(self.autofocusLabel, 8, 0, 1, 1)
        self.grid.addWidget(self.autofocusRange, 8, 1, 1, 1)
        self.grid.addWidget(self.autofocusSteps, 8, 2, 1, 1)
        self.grid.addWidget(self.autofocusPeriod, 8, 3, 1, 1)
        self.grid.addWidget(self.autofocusInitial, 9, 1, 1, 1)
        self.grid.addWidget(self.autofocusSelectionLabel, 9, 2, 1, 1)
        self.grid.addWidget(self.autofocusInitialZLabel, 9, 0, 1, 1)
        self.grid.addWidget(self.autofocusLED1Checkbox, 9, 3, 1, 1)
        # start stop
        self.grid.addWidget(self.ScanStartButton, 10, 0, 1, 1)
        self.grid.addWidget(self.ScanStopButton, 10, 1, 1, 1)
        self.grid.addWidget(self.ScanShowLastButton, 10, 2, 1, 1)
        self.layer = None

        self.addScanner()


    def isAutofocus(self):
        if self.autofocusLED1Checkbox.isChecked():
            return True
        else:
            return False

    def getAutofocusValues(self):
        autofocusParams = {}
        autofocusParams["valueRange"] = self.autofocusRange.text()
        autofocusParams["valueSteps"] = self.autofocusSteps.text()
        autofocusParams["valuePeriod"] = self.autofocusPeriod.text()
        autofocusParams["valueInitial"] = self.autofocusInitial.text()
        if self.autofocusLED1Checkbox.isChecked():
            autofocusParams["illuMethod"] = 'LED'
        else:
            autofocusParams["illuMethod"] = False

        return autofocusParams

    def setupSliderGui(self, label, valueDecimals, valueRange, tickInterval, singleStep):
        ScanLabel = QtWidgets.QLabel(label)
        valueRangeMin, valueRangeMax = valueRange
        slider = guitools.FloatSlider(QtCore.Qt.Horizontal, self, allowScrollChanges=False,
                                      decimals=valueDecimals)
        slider.setFocusPolicy(QtCore.Qt.NoFocus)
        slider.setMinimum(valueRangeMin)
        slider.setMaximum(valueRangeMax)
        slider.setTickInterval(tickInterval)
        slider.setSingleStep(singleStep)
        slider.setValue(0)
        return slider, ScanLabel

    def getImage(self):
        if self.layer is not None:
            return self.img.image

    def setImage(self, im, colormap="gray", name="", pixelsize=(1, 1, 1), translation=(0, 0, 0)):
        if len(im.shape) == 2:
            translation = (translation[0], translation[1])
        if self.layer is None or name not in self.viewer.layers:
            self.layer = self.viewer.add_image(im, rgb=False, colormap=colormap,
                                               scale=pixelsize, translate=translation,
                                               name=name, blending='additive')
        self.layer.data = im

    def getZStackValues(self):
        valueZmin = -abs(float(self.ScanValueZmin.text()))
        valueZmax = float(self.ScanValueZmax.text())
        valueZsteps = float(self.ScanValueZsteps.text())
        valueZenabled = bool(self.ScanDoZStack.isChecked())

        return valueZmin, valueZmax, valueZsteps, valueZenabled

    def getTimelapseValues(self):
        ScanValueTimePeriod = float(self.ScanValueTimePeriod.text())
        ScanValueTimeDuration = int(self.ScanValueTimeDuration.text())
        return ScanValueTimePeriod, ScanValueTimeDuration

    def getFilename(self):
        ScanEditFileName = self.ScanEditFileName.text()
        return ScanEditFileName

    def setNImages(self, nRounds):
        nRounds2Do = self.getTimelapseValues()[-1]
        self.ScanNRounds.setText('Timelapse progress: ' + str(nRounds) + " / " + str(nRounds2Do))

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