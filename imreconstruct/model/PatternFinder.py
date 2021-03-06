# -*- coding: utf-8 -*-
"""
Created on Thu May 30 13:56:04 2019

@author: andreas.boden
"""

import numpy as np
from scipy.signal import find_peaks
from scipy.optimize import curve_fit


class PatternFinder:
    def findPattern(self, image):
        image = image - image.min()
        thresh = image.max() / 3
        image[image < thresh] = 0

        numRows = np.size(image, 0)
        numCols = np.size(image, 1)

        meanAlongRows = image.mean(1)
        meanAlongCols = image.mean(0)

        horiFft = np.fft.fft(meanAlongCols)[0:int(numCols/2) + 1]  #log_ft_image[0, 0:int(numCols/2)])
        vertFft = np.fft.fft(meanAlongRows)[0:int(numRows/2) + 1]  #log_ft_image[0:int(numRows/2), 0])

        horiPeaks = find_peaks(np.log(np.abs(horiFft)), prominence=[0,np.inf], width=0, height=0)
        vertPeaks = find_peaks(np.log(np.abs(vertFft)), prominence=[0,np.inf], width=0, height=0)

        bestPeakHori = self.findBestPeak(horiPeaks)
        bestPeakHoriInd = horiPeaks[0][bestPeakHori]
        peakWidthHori = horiPeaks[1]['widths'][bestPeakHori]

        bestPeakVert = self.findBestPeak(vertPeaks)
        bestPeakVertInd = vertPeaks[0][bestPeakVert]
        peakWidthVert = vertPeaks[1]['widths'][bestPeakVert]

        minRWindow = max(0, bestPeakHoriInd - int(3*peakWidthHori))
        maxRWindow = min(bestPeakHoriInd + int(3*peakWidthHori), len(horiFft))
        minCWindow = max(0, bestPeakVertInd - int(3*peakWidthVert))
        maxCWindow = min(bestPeakVertInd + int(3*peakWidthVert), len(vertFft))

        windowR = np.arange(minRWindow, maxRWindow)
        windowC = np.arange(minCWindow, maxCWindow)

        croppedPeakHori = np.abs(horiFft[windowR])
        croppedPeakVert = np.abs(vertFft[windowC])

        def gaussFunction(x, a, b, x0, sigma):
            return a + b*np.exp(-(x-x0)**2/(2*sigma**2))

        aStartHori = croppedPeakHori.min()
        bStartHori = croppedPeakHori.max() - croppedPeakHori.min()
        poptR, pcovR = curve_fit(gaussFunction, windowR, croppedPeakHori, p0=[aStartHori, bStartHori, bestPeakHoriInd, peakWidthHori/2.355])

        optHoriPeakInd = poptR[2]
        optPerHoriPx = image.shape[1] / optHoriPeakInd

        aStartVert = croppedPeakVert.min()
        bStartVert = croppedPeakVert.max() - croppedPeakVert.min()
        poptC, pcovC = curve_fit(gaussFunction, windowC, croppedPeakVert, p0=[aStartVert, bStartVert, bestPeakVertInd, peakWidthVert/2.355])

        optVertPeakInd = poptC[2]
        optPerVertPx = image.shape[0] / optVertPeakInd

        N = numCols
        x = np.linspace(0, N-1, N)
        y = np.exp(-1j*2*np.pi*x*optHoriPeakInd/N)
        ftValHori = np.multiply(meanAlongCols, y).sum()
        offsetHori = np.mod((-np.angle(ftValHori)/np.pi)*0.5*optPerHoriPx, optPerHoriPx)

        N = numRows
        x = np.linspace(0, N-1, N)
        y = np.exp(-1j*2*np.pi*x*optVertPeakInd/N)
        ftValVert = np.multiply(meanAlongRows, y).sum()
        offsetVert = np.mod((-np.angle(ftValVert)/np.pi)*0.5*optPerVertPx, optPerVertPx)

        return [offsetVert, offsetHori, optPerVertPx, optPerHoriPx]

    def findBestPeak(self, peaks):
        bestTwoPeaks = peaks[1]['prominences'].argsort()[-2::][::-1]
        prom1 = peaks[1]['prominences'][bestTwoPeaks[0]]
        prom2 = peaks[1]['prominences'][bestTwoPeaks[1]]
        if abs((prom1 - prom2)/(prom1 + prom2)) < 0.2:
            height1 = peaks[1]['peak_heights'][bestTwoPeaks[0]]
            height2 = peaks[1]['peak_heights'][bestTwoPeaks[1]]
            if (height1 - height2)/(height1 - height2) < 0.2:
                bestPeak = bestTwoPeaks.min()
            else:
                heights = np.array([height1, height2])
                highest = heights.argmax()
                bestPeak = bestTwoPeaks[highest]
        else:
            bestPeak = bestTwoPeaks[0]

        return bestPeak
