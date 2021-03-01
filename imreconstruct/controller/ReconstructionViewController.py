import numpy as np

from .basecontrollers import ImRecWidgetController


class ReconstructionViewController(ImRecWidgetController):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._currItemInd = None

        self._commChannel.sigScanParamsUpdated.connect(self.scanParamsUpdated)

        self._widget.sigItemSelected.connect(self.listItemChanged)
        self._widget.sigImgSliceChanged.connect(self.setImgSlice)
        self._widget.sigViewChanged.connect(lambda: self.fullUpdate(levels=None))

    def getActiveReconObj(self):
        return self._widget.getCurrentItemData()

    def listItemChanged(self):
        if self._currItemInd is not None:
            currHistLevels = self._widget.getImageDisplayLevels()
            prevItem = self._widget.getDataAtIndex(self._currItemInd)
            prevItem.setDispLevels(currHistLevels)
            retrievedLevels = self._widget.getCurrentItemData().getDispLevels()
            self.fullUpdate(levels=retrievedLevels)
            if retrievedLevels is not None:
                self._widget.setImageDisplayLevels(retrievedLevels[0], retrievedLevels[1])
        else:
            self.fullUpdate(autoLevels=True, levels=self._widget.getCurrentItemData().getDispLevels())

        self._currItemInd = self._widget.getCurrentItemIndex()

    def fullUpdate(self, autoLevels=False, levels=None):
        currentItemData = self._widget.getCurrentItemData()
        if currentItemData is not None:
            reconstructedShape = np.shape(self._widget.getCurrentItemData().reconstructed)
            self._widget.setSliceParameters(s=0, ds=0, base=0, t=0)
            self._widget.setSliceParameterMaximums(
                s=reconstructedShape[self.getViewId()] - 1,
                ds=reconstructedShape[0] - 1,
                base=reconstructedShape[1] - 1,
                t=reconstructedShape[2] - 1
            )
            self.setImgSlice(*self._widget.getSliceParameters(), autoLevels=autoLevels, levels=levels)
            self._widget.resetView()
        else:
            self._widget.setSliceParameters(s=0, base=0, t=0)
            self._widget.setSliceParameterMaximums(s=0, base=0, t=0)
            self._widget.clearImage()

    def setImgSlice(self, s, base, t, ds, autoLevels=False, levels=None):
        data = self._widget.getCurrentItemData().reconstructed
        if self.getViewId() == 3:
            im = data[ds, base, t, s, ::, ::]
        elif self.getViewId() == 4:
            im = data[ds, base, t, ::, s, ::]
        else:
            im = data[ds, t, base, ::, ::, s]

        self._widget.setImage(im, autoLevels=autoLevels, levels=levels)

    def getViewId(self):
        viewName = self._widget.getViewName()
        if viewName == 'standard':
            return 3
        elif viewName == 'bottom':
            return 4
        elif viewName == 'left':
            return 5
        else:
            raise ValueError(f'Unsupported view "{viewName}"')

    def updateRecon(self):
        self._widget.getCurrentItemData().updateImages()
        self.fullUpdate(levels=None)

    def scanParamsUpdated(self, scanParDict):
        currData = self._widget.getCurrentItemData()
        if currData is not None:
            self._widget.getCurrentItemData().updateScanParams(scanParDict)
            self.updateRecon()
