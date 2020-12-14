# -*- coding: utf-8 -*-
"""
Created on Thu May 30 13:56:04 2019

@author: andreas.boden
"""

import numpy as np
from scipy.signal import find_peaks
from scipy.optimize import curve_fit


class PatternFinder:
    def find_pattern(self, image):
        image = image - image.min()
        thresh = image.max() / 3
        image[image < thresh] = 0

        nr_rows = np.size(image, 0)
        nr_cols = np.size(image, 1)


        mean_along_rows = image.mean(1)
        mean_along_cols = image.mean(0)

        hori_fft = np.fft.fft(mean_along_cols)[0:int(nr_cols/2) + 1]#log_ft_image[0, 0:int(nr_cols/2)])
        vert_fft = np.fft.fft(mean_along_rows)[0:int(nr_rows/2) + 1]#log_ft_image[0:int(nr_rows/2), 0])

        hori_peaks = find_peaks(np.log(np.abs(hori_fft)), prominence=[0,np.inf], width=0, height=0)
        vert_peaks = find_peaks(np.log(np.abs(vert_fft)), prominence=[0,np.inf], width=0, height=0)

        best_peak_hori = self.find_best_peak(hori_peaks)

        best_peak_hori_ind = hori_peaks[0][best_peak_hori]
        peak_width_hori = hori_peaks[1]['widths'][best_peak_hori]

        best_peak_vert = self.find_best_peak(vert_peaks)


        best_peak_vert_ind = vert_peaks[0][best_peak_vert]
        peak_width_vert = vert_peaks[1]['widths'][best_peak_vert]

        min_r_window = max(0, best_peak_hori_ind - int(3*peak_width_hori))
        max_r_window = min(best_peak_hori_ind + int(3*peak_width_hori), len(hori_fft))
        min_c_window = max(0, best_peak_vert_ind - int(3*peak_width_vert))
        max_c_window = min(best_peak_vert_ind + int(3*peak_width_vert), len(vert_fft))

        window_r = np.arange(min_r_window, max_r_window)
        window_c = np.arange(min_c_window, max_c_window)

        cropped_peak_hori = np.abs(hori_fft[window_r])
        cropped_peak_vert = np.abs(vert_fft[window_c])

        def gauss_function(x, a, b, x0, sigma):
            return a + b*np.exp(-(x-x0)**2/(2*sigma**2))

        a_start_hori = cropped_peak_hori.min()
        b_start_hori = cropped_peak_hori.max() - cropped_peak_hori.min()
        popt_r, pcov_r = curve_fit(gauss_function, window_r, cropped_peak_hori, p0=[a_start_hori, b_start_hori, best_peak_hori_ind, peak_width_hori/2.355])

        opt_hori_peak_ind = popt_r[2]
        opt_per_hori_px = image.shape[1] / opt_hori_peak_ind

        a_start_vert = cropped_peak_vert.min()
        b_start_vert = cropped_peak_vert.max() - cropped_peak_vert.min()
        popt_c, pcov_c = curve_fit(gauss_function, window_c, cropped_peak_vert, p0=[a_start_vert, b_start_vert, best_peak_vert_ind, peak_width_vert/2.355])

        opt_vert_peak_ind = popt_c[2]
        opt_per_vert_px = image.shape[0] / opt_vert_peak_ind

        N = nr_cols
        x = np.linspace(0, N-1, N)
        y = np.exp(-1j*2*np.pi*x*opt_hori_peak_ind/N)
        ft_val_hori = np.multiply(mean_along_cols, y).sum()
        offset_hori = np.mod((-np.angle(ft_val_hori)/np.pi)*0.5*opt_per_hori_px, opt_per_hori_px)

        N = nr_rows
        x = np.linspace(0, N-1, N)
        y = np.exp(-1j*2*np.pi*x*opt_vert_peak_ind/N)
        ft_val_vert = np.multiply(mean_along_rows, y).sum()
        offset_vert = np.mod((-np.angle(ft_val_vert)/np.pi)*0.5*opt_per_vert_px, opt_per_vert_px)

        return [offset_vert, offset_hori, opt_per_vert_px, opt_per_hori_px]

    def find_best_peak(self, peaks):
        best_two_peaks = peaks[1]['prominences'].argsort()[-2::][::-1]
        prom1 = peaks[1]['prominences'][best_two_peaks[0]]
        prom2 = peaks[1]['prominences'][best_two_peaks[1]]
        if abs((prom1 - prom2)/(prom1 + prom2)) < 0.2:
            height1 = peaks[1]['peak_heights'][best_two_peaks[0]]
            height2 = peaks[1]['peak_heights'][best_two_peaks[1]]
            if (height1 - height2)/(height1 - height2) < 0.2:
                best_peak = best_two_peaks.min()
            else:
                heights = np.array([height1, height2])
                highest = heights.argmax()
                best_peak = best_two_peaks[highest]
        else:
            best_peak = best_two_peaks[0]

        return best_peak
