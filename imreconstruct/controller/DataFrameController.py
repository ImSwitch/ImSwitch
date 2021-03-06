import numpy as np

from .basecontrollers import ImRecWidgetController
from .DataEditController import DataEditController


class DataFrameController(ImRecWidgetController):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.editWindowController = self._factory.createController(
            DataEditController, self._widget.editWdw
        )

        self._dataObj = None
        self._pattern = []
        self._patternGrid = []
        self._patternGridMade = False
        self._patternVisible = False

        self._commChannel.sigCurrentDataChanged.connect(self.currentDataChanged)
        self._commChannel.sigPatternUpdated.connect(self.patternUpdated)
        self._commChannel.sigPatternVisibilityChanged.connect(self.patternVisibilityChanged)

        self._widget.sigShowMeanClicked.connect(self.showMean)
        self._widget.sigAdjustDataClicked.connect(self.adjustData)
        self._widget.sigUnloadDataClicked.connect(self.unloadData)
        self._widget.sigFrameNumberChanged.connect(self.setImgSlice)
        self._widget.sigFrameSliderChanged.connect(self.setImgSlice)

    def patternUpdated(self, pattern):
        self._pattern = pattern
        self._patternGridMade = False
        if self._patternVisible:
            self.makePatternGrid()

    def patternVisibilityChanged(self, showPattern):
        self._patternVisible = showPattern
        if showPattern and not self._patternGridMade:
            self.makePatternGrid()

        self._widget.setShowPattern(showPattern)

    def setImgSlice(self, frame):
        self._widget.setImage(self._dataObj.data[frame], autoLevels=False)

    def unloadData(self):
        self._dataObj = None
        self.showMean()
        self._widget.setNumFrames(0)
        self._widget.setDataName('')

    def adjustData(self):
        print('In adjust data')
        if self._dataObj is not None:
            self.editWindowController.setData(self._dataObj)
            self._widget.showEditWindow()
        else:
            print('No data to edit')

    def showMean(self):
        self._widget.setImage(self._dataObj.getMeanData(), autoLevels=True)

    def currentDataChanged(self, inDataObj):
        self._dataObj = inDataObj
        print('Data shape = ', self._dataObj.data.shape)
        self.showMean()
        self._widget.setNumFrames(self._dataObj.numFrames)
        self._widget.setDataName(self._dataObj.name)

    def makePatternGrid(self):
        """ Pattern is now [Row-offset, Col-offset, Row-period, Col-period] where
        offset is calculated from the upper left corner (0, 0), while the
        scatter plot plots from lower left corner, so a flip has to be made
        in rows."""
        numCols = np.size(self._dataObj.data, 1)
        numRows = np.size(self._dataObj.data, 2)
        numPointsCol = int(1 + np.floor(((numCols - 1) - self._pattern[1]) / self._pattern[3]))
        numPointsRow = int(1 + np.floor(((numRows - 1) - self._pattern[0]) / self._pattern[2]))
        colCoords = np.linspace(self._pattern[1],
                                self._pattern[1] + (numPointsCol - 1) * self._pattern[3],
                                numPointsCol)
        rowCoords = np.linspace(self._pattern[0],
                                self._pattern[0] + (numPointsRow - 1) * self._pattern[2],
                                numPointsRow)
        colCoords = np.repeat(colCoords, numPointsRow)
        rowCoords = np.tile(rowCoords, numPointsCol)

        self._patternGrid = [colCoords, rowCoords]
        self._widget.setPatternGridData(x=self._patternGrid[0], y=self._patternGrid[1])

        self._patternGridMade = True
        print('Made new pattern grid')

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