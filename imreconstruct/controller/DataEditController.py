import numpy as np

from .basecontrollers import ImRecWidgetController


class DataEditController(ImRecWidgetController):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._dataObj = None
        self._meanData = None

        self._widget.sigImageSliceChanged.connect(self.setImgSlice)
        self._widget.sigShowMeanClicked.connect(self.showMean)
        self._widget.sigSetDarkFrameClicked.connect(self.setDarkFrame)

    def setData(self, inDataObj):
        self._dataObj = inDataObj
        self._meanData = np.array(np.mean(self._dataObj.data, 0), dtype=np.float32)
        self.showMean()
        self._widget.updateDataProperties(self._dataObj.name, self._dataObj.numFrames)

    def setImgSlice(self, frameNumber):
        if self._dataObj is None or frameNumber >= len(self._dataObj.data):
            return

        self._widget.setImage(self._dataObj.data[frameNumber], autoLevels=False)

    def setDarkFrame(self):
        # self.dataObj.data = self.dataObj.data[0:100]
        pass

    def showMean(self):
        if self._meanData is None:
            return

        self._widget.setImage(self._meanData, autoLevels=True)

