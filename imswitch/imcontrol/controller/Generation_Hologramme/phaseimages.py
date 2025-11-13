"""
    summary:
    
    date: 04/04/2024
    @author: Gabriel Lecarme
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import imswitch.imcontrol.controller.Generation_Hologramme.images as images

import imswitch.imcontrol.controller.Generation_Hologramme.parameters as param

def padCGH(cgh, slm_dimensions):
    b = slm_dimensions[0] - cgh.shape[1]
    a = slm_dimensions[1] - cgh.shape[0]
    cgh = cgh + np.pi
    cgh = (cgh * 255/(2*np.pi)) % 256
    pad = np.pad(cgh, ((a//2, (a+1)//2), (b//2, (b+1)//2)), 'wrap')
    return pad.astype(np.uint8)

def correctToDisplayable(cgh, slm_dimensions, wavelength):
    """ Pad the array so that it fits on the SLM
        Apply corrections for SLM surface irregularities and wavelength-dependent phase modulation
    """
    b = slm_dimensions[0] - cgh.shape[1]
    a = slm_dimensions[1] - cgh.shape[0]
    cgh = cgh + np.pi
    cgh = (cgh * 255/(2*np.pi)) % 256
    pad = np.pad(cgh, ((a//2, (a+1)//2), (b//2, (b+1)//2)), 'wrap')
    
    calibration = images.readbmp(f'Hamamatsu\Corrections\CAL_LSH0803619_{wavelength}nm.bmp')
    res = (calibration + pad) % 256
    return res.astype(np.uint8)

def fresnelLens(Nx: int, Ny: int, f, pp, wavelength, NA=0.02):
    """  Compute the phase image of a Fresnel Lens 

    Args:
        Nx (int): width of the image
        Ny (int): length of the image
        f (mm): focal length
        pp (um): pixel pitch
        wavelength (nm)
        NA : Numerical aperture of the lens

    Returns:
        numpy.2darray: phase image of the fresnel lens values between [0; 2*PI]
    """
    f = f/10**3
    pp = pp/10**6
    wavelength = wavelength/10**9
    R = NA*f
    
    d = np.zeros((Ny, Nx), dtype=float)
    # x = np.arange(-Nx//2, Nx//2, dtype=float) # last is not included
    # y = np.arange(-Ny//2, Ny//2)
    # x = (x+1/2)*pp
    # y = (y+1/2)*pp
    x = np.linspace((-Nx//2 + 1/2)*pp, (Nx//2 + 1/2)*pp, Nx, endpoint=False, dtype=float)
    y = np.linspace((-Ny//2 + 1/2)*pp, (Ny//2 + 1/2)*pp, Ny, endpoint=False)
    
    X, Y = np.meshgrid(x, y)
    
    wavefront = np.sqrt(f**2 - (X**2 + Y**2)) - f # surface equation
    d[X**2 + Y**2 < R**2] = np.abs(wavefront[X**2 + Y**2 < R**2]) + wavelength*1e-9 # distance to the slm plane z=0
    phase = -d*2*param.PI/param.wavelength
    phase = phase%(2*param.PI) # 2*PI modulation at maximum wrap the phase image
    return phase

def applyLUT(phase_image, wavelength):
    """ From the Hamamatsu/Corrections/LUT.csv apply the factor for the operating wavelength
    Args:
        phase_image (numpy.2darray): dtype('int8') values between [0; 255]
        wavelength (nm): operating wavelength
    """
    df = pd.read_csv('./Hamamatsu/Corrections/LUT.csv')
    modulation = df.loc[df["Wavelength (nm)"] == wavelength]
    modulation = modulation.iat[0, 1]
    factor = modulation / 255
    res = phase_image * factor
    return res.astype(np.uint8)
    
def focus(phase_image, lens):
    lens = (lens * 255/(2*param.PI)) % 256
    res = (phase_image + lens)%256
    return res.astype(np.uint8)

def conjugate(phase_image):
    """ Apply Hamamatsu's lens """
    fl_h = images.readbmp('Hamamatsu/FL_f340mm.bmp') # Hamamatsu's
    res = (phase_image + fl_h) % 256
    res = res * (197/255)
    return res.astype(np.uint8)

if __name__ == "__main__":
    calibration = images.readbmp("Hamamatsu\Corrections\CAL_LSH0803619_488nm.bmp")
    
    lens = fresnelLens(param.width_slm, param.height_slm, 5, param.focal_length, param.pixel_size, param.wavelength)
    images.savephase(lens, 'fresnel_lens_340mm')
    res = focus(calibration, lens)
    res = applyLUT(res, param.wavelength)
    
    plt.figure()
    plt.imshow(res)
    
    plt.figure()
    plt.imshow(lens)
    
    plt.show()