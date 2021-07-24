import numpy as np

from ..basecontrollers import ImConWidgetController


class ULensesController(ImConWidgetController):
    """ Linked to ULensesWidget. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialize variables
        self.init = False
        self.layer = []

        # Connect ULensesWidget signals
        self._widget.sigULensesClicked.connect(self.toggleULenses)

    def toggleULenses(self):
        """ Shows or hides grid. """
        x, y, px, up = self._widget.getParameters()
        size_x, size_y = image = next(iter(self._widget.viewer.layers.selected)).data.shape
        pattern_x = np.arange(x, size_x, up / px)
        pattern_y = np.arange(y, size_y, up / px)
        grid = np.array(np.meshgrid(pattern_x, pattern_y)).T.reshape(-1, 2)
        if self.init:
            if 'grid' in self._widget.viewer.layers:
                self.layer.data = grid
            else:
                self.layer = self._widget.viewer.add_points(grid, size=2, face_color='red', symbol='ring')
        else:
            self.layer = self._widget.viewer.add_points(grid, size=2, face_color='red', symbol='ring')
            self.init = True


# Copyright (C) 2020, 2021 TestaLab
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
