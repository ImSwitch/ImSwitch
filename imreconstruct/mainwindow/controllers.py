import numpy as np

from imcommon.controller import Controller


class DataFrameController(Controller):
    """Frame for showing and examining the raw data"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._widget.sigShowMeanClicked.connect(self.showMean)
        self._widget.sigAdjustDataClicked.connect(self.adjustData)
        self._widget.sigUnloadDataClicked.connect(self.unloadData)
        self._widget.sigFrameNumberChanged.connect(self.setImgSlice)
        self._widget.sigFrameSliderChanged.connect(self.setImgSlice)
        self._widget.sigShowPatternChanged.connect(self.showPatternChanged)
        self._widget.sigDataChanged.connect(self.setData)

        self.dataObj = None
        self.pattern = []
        self.patternGrid = []
        self.patternGridMade = False

    def showPatternChanged(self, value):
        if value and not self.patternGridMade:
            self.makePatternGrid()

    def setImgSlice(self, frame):
        self._widget.setImage(self.dataObj.data[frame], autoLevels=False)

    def unloadData(self):
        self.dataObj = None
        self.showMean()
        self._widget.setNumFrames(0)
        self._widget.setDataName('')

    def adjustData(self):
        print('In adjust data')
        if self.dataObj is not None:
            self._widget.showEditWindow(self.dataObj)
        else:
            print('No data to edit')

    def showMean(self):
        self._widget.setImage(self.dataObj.getMeanData())

    def setData(self, in_dataObj):
        self.dataObj = in_dataObj
        print('Data shape = ', self.dataObj.data.shape)
        self.showMean()
        self._widget.setNumFrames(self.dataObj.frames)
        self._widget.setDataName(self.dataObj.name)

    def makePatternGrid(self):
        """ Pattern is now [Row-offset, Col-offset, Row-period, Col-period] where
        offset is calculated from the upper left corner (0, 0), while the
        scatter plot plots from lower left corner, so a flip has to be made
        in rows."""
        nr_cols = np.size(self.dataObj.data, 1)
        nr_rows = np.size(self.dataObj.data, 2)
        nr_points_col = int(1 + np.floor(((nr_cols - 1) - self.pattern[1]) / self.pattern[3]))
        nr_points_row = int(1 + np.floor(((nr_rows - 1) - self.pattern[0]) / self.pattern[2]))
        col_coords = np.linspace(self.pattern[1],
                                 self.pattern[1] + (nr_points_col - 1) * self.pattern[3],
                                 nr_points_col)
        row_coords = np.linspace(self.pattern[0],
                                 self.pattern[0] + (nr_points_row - 1) * self.pattern[2],
                                 nr_points_row)
        col_coords = np.repeat(col_coords, nr_points_row)
        row_coords = np.tile(row_coords, nr_points_col)

        self.patternGrid = [col_coords, row_coords]
        self._widget.setPatternGridData(x=self.patternGrid[0], y=self.patternGrid[1])

        self.patternGridMade = True
        print('Made new pattern grid')
