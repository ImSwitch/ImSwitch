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
        chex = '#%02x%02x%02x' % (
            int(gamma_corrected_rgb[0]), int(gamma_corrected_rgb[1]), int(gamma_corrected_rgb[2])
        )
        return chex
    except ValueError:
        return 255, 255, 255


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
