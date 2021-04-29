import numpy as np


def bestLevels(arr):
    # Best cmin, cmax algorithm taken from ImageJ routine:
    # http://cmci.embl.de/documents/120206pyip_cooking/
    # python_imagej_cookbook#automatic_brightnesscontrast_button
    pixelCount = arr.size
    limit = pixelCount / 10
    threshold = pixelCount / 5000
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

def minmaxLevels(arr):
    minlevel = 0
    maxlevel = arr.max()+2

    return minlevel, maxlevel

def setBestImageLimits(viewBox, width, height):
    viewBox.setAspectLocked()
    viewBox.setLimits(xMin=None, xMax=None, yMin=None, yMax=None)

    viewBox.setRange(xRange=(-0.5, width - 0.5), yRange=(-0.5, height - 0.5), padding=0)
    viewBounds = viewBox.viewRange()
    viewBox.setLimits(xMin=viewBounds[0][0], xMax=viewBounds[0][1],
                      yMin=viewBounds[1][0], yMax=viewBounds[1][1])


# Copyright (C) 2017 Federico Barabas
# This file is part of Tormenta.
#
# Tormenta is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Tormenta is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
