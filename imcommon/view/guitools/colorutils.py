# -*- coding: utf-8 -*-
"""
Created on Thu Nov 26 14:32:24 2020

@author: Testa4
"""

import colour


def wavelengthToHex(wavelength: float, gamma: float = 2.4):
    """
    Converts a wavelength (in nanometres) to a gamma corrected RGB tuple with values [0, 255].
    Returns white if the wavelength is outside the visible spectrum or any other error occurs.
    """

    try:
        xyz = colour.wavelength_to_XYZ(wavelength)
        srgb = colour.XYZ_to_sRGB(xyz).clip(0, 1)
        gamma_corrected_rgb = 255 * srgb ** (1 / gamma)
        chex = '#%02x%02x%02x' % (int(gamma_corrected_rgb[0]), int(gamma_corrected_rgb[1]), int(gamma_corrected_rgb[2]))
        return chex
    except ValueError:
        return 255, 255, 255
