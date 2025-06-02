"""
    summary: This file contains the parameters of the system used in the rest of the code
    SLM: Hamamatsu X15213-01
"""
import numpy as np

# Constants
PI = np.pi
    
# SLM dimensions
width_slm = 1272
height_slm = 1024
size_slm = (width_slm, height_slm) # shape in pixels
pixel_size = 12.5 # pixel pitch in [um]

wavelength = 488 # wavelength of the laser in [nm] Range of operation 400nm - 700nm



period_grid = 7 # (int) period in pixels
n = 13 # (int) size of the grid (number of points n*n)
N = 512 # (int) size of the target images (number of pixels N*N) recommended to be 512 or less


file_path = 'C:/Users/oriane.koellsch/Documents/SLM-Imswitch/Patterns_MFA'
file_name = 'holoBMP_10x10_p21'