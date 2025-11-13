import numpy as np

from .basecontrollers import ImRecWidgetController


class ReconstructionViewController(ImRecWidgetController):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._currItemInd = None
        self._prevViewId = None

        self._transposeOrder = [0, 1, 2, 3, 4, 5]
        self._axisStep = (0, 0, 0, 0, 0, 0)

        self._commChannel.sigScanParamsUpdated.connect(self.scanParamsUpdated)

        self._widget.sigItemSelected.connect(self.listItemChanged)
        self._widget.sigAxisStepChanged.connect(self.axisStepChanged)
        self._widget.sigViewChanged.connect(lambda: self.fullUpdate(levels=None))

    def getActiveReconObj(self):
        return self._widget.getCurrentItemData()

    def getAllReconObjs(self):
        return self._widget.getAllItemDatas()

    def listItemChanged(self):
        if self._currItemInd is not None:
            currHistLevels = self._widget.getImageDisplayLevels()
            prevItem = self._widget.getDataAtIndex(self._currItemInd)
            prevItem.setDispLevels(currHistLevels)

            currItem = self._widget.getCurrentItemData()
            retrievedLevels = \
                self._widget.getCurrentItemData().getDispLevels() if currItem is not None else None
            self.fullUpdate(levels=retrievedLevels)
            if retrievedLevels is not None:
                self._widget.setImageDisplayLevels(retrievedLevels[0], retrievedLevels[1])
        else:
            self.fullUpdate(autoLevels=True,
                            levels=self._widget.getCurrentItemData().getDispLevels())

        self._currItemInd = self._widget.getCurrentItemIndex()

    def fullUpdate(self, autoLevels=False, levels=None):
        reconObj = self._widget.getCurrentItemData()
        if reconObj is not None:
            self.setImgSlice(autoLevels=autoLevels, levels=levels)
            if (self._currItemInd is None or self._prevViewId is None or
                    self.getViewId() != self._prevViewId):
                self._widget.resetView()
        else:
            self._widget.clearImage()

        self._prevViewId = self.getViewId()

    def setImgSlice(self, autoLevels=False, levels=None):
        data = self._widget.getCurrentItemData().reconstructed

        if self.getViewId() == 3:
            transposeOrder = [0, 1, 2, 3, 4, 5]
        elif self.getViewId() == 4:
            transposeOrder = [0, 1, 2, 4, 3, 5]
        else:
            transposeOrder = [0, 1, 2, 5, 4, 3]

        im = data.transpose(*transposeOrder)
        axisLabels = np.array(['Dataset', 'Base', 'Time point', 'Slice', 'X', 'Y'])[transposeOrder]
        self._transposeOrder = transposeOrder

        self._widget.setImage(im, axisLabels)
        if autoLevels:
            self.updateLevelsRange()
        elif levels is not None:
            self._widget.setImageDisplayLevels(*levels)

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

    def axisStepChanged(self, newAxisStep):
        baseAxisIndex = self._transposeOrder.index(1)
        newBase = newAxisStep[baseAxisIndex]
        if newBase != self._axisStep[baseAxisIndex]:
            # Base changed, update levels range
            self.updateLevelsRange(newBase)

        self._axisStep = newAxisStep

    def updateLevelsRange(self, base=None):
        baseAxisIndex = self._transposeOrder.index(1)
        if base is None:
            base = self._axisStep[baseAxisIndex]

        # Find image at current base
        im = self._widget.getImage()
        indexForImage = [slice(None) for _ in range(len(im.shape))]
        indexForImage[baseAxisIndex] = base
        imAtBase = im[tuple(indexForImage)]

        # Update levels
        levels = imAtBase.min(), imAtBase.max()
        self._widget.setImageDisplayLevelsRange(*levels)
        self._widget.setImageDisplayLevels(*levels)

    def updateRecon(self):
        reconObj = self._widget.getCurrentItemData()
        if reconObj is not None:
            reconObj.updateImages()
            self.fullUpdate(levels=None)

    def scanParamsUpdated(self, scanParDict, applyOnCurrentRecon):
        if not applyOnCurrentRecon:
            return

        reconObj = self._widget.getCurrentItemData()
        if reconObj is not None:
            reconObj.updateScanParams(scanParDict)
            self.updateRecon()

    def getImage(self):
        return self._widget.getImage()

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
