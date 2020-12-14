import numpy as np
from imcommon.controller import Controller


class ReconstructionController(Controller):
    """ Frame for showing the reconstructed image"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.id = 0
        self.currItem_ind = None

        self._widget.sigItemSelected.connect(self.list_item_changed)
        self._widget.sigImgSliceChanged.connect(self.setImgSlice)
        self._widget.sigViewChanged.connect(lambda: self.FullUpdate(levels=None))
        self._widget.sigScanParsChanged.connect(self.UpdateScanPars)

    def list_item_changed(self):
        if self.currItem_ind is not None:
            curr_hist_levels = self._widget.getImageDisplayLevels()
            prev_item = self._widget.getDataAtIndex(self.currItem_ind)
            prev_item.setDispLevels(curr_hist_levels)
            retrieved_levels = self._widget.getCurrentItemData().getDispLevels()
            self.FullUpdate(levels=retrieved_levels)
            if retrieved_levels is not None:
                self._widget.setImageDisplayLevels(retrieved_levels[0], retrieved_levels[1])
        else:
            self.FullUpdate(levels=self._widget.getCurrentItemData().getDispLevels())

        self.currItem_ind = self._widget.getCurrentItemIndex()

    def FullUpdate(self, levels):
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
            self.setImgSlice(*self._widget.getSliceParameters(), levels=levels)
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

    def UpdateRecon(self):
        self._widget.getCurrentItemData().update_images()
        self.FullUpdate(levels=None)

    def UpdateScanPars(self, scanParDict):
        self._widget.getCurrentItemData().updateScanningPars(scanParDict)
        self.UpdateRecon()
