"""
    summary:
    
    date: 20/03/2024
    @author: Gabriel Lecarme
"""

import os
import numpy as np
import imageio.v2 as imageio
import cv2 as opencv
import scipy.ndimage
import matplotlib.pyplot as plt

import imswitch.imcontrol.controller.Generation_Hologramme.parameters as param

def saveasbmp(target, file_name, module='opencv'):
    target = (target*255)%256
    target = target.astype(np.uint8)
    if module == 'opencv':
        opencv.imwrite(f'{param.file_path}/Targets/{file_name}.bmp', target)
    else:
        imageio.imwrite(f'{param.file_path}/Targets/{file_name}.bmp', target)
    
def savecgh(cgh, file_name, module='imageio'):
    res = cgh + np.pi
    res = (res * 255/(2*np.pi)) % 256
    res = res.astype(np.uint8)
    if module == 'opencv':
        opencv.imwrite(f'{param.file_path}/CGH/cgh_{file_name}.bmp', res)
    elif module == 'imageio':
        imageio.imwrite(f'{param.file_path}/CGH/cgh_{file_name}.bmp', res)
        
def savephase(phase, file_name, module='imageio'):
    res = (phase * 255/(2*np.pi)) % 256
    res = res.astype(np.uint8)
    if module == 'opencv':
        opencv.imwrite(f'{param.file_path}/Phase Images/{file_name}.bmp', res)
    elif module == 'imageio':
        imageio.imwrite(f'{param.file_path}/Phase Images/{file_name}.bmp', res)

def savephaseimage(phase_image, file_name, module='imageio'):
    res = phase_image.astype(np.uint8) # unnecessary but just to be sure
    if module == 'opencv':
        opencv.imwrite(f'{param.file_path}/{file_name}.bmp', res)
    elif module == 'imageio':
        imageio.imwrite(f'{param.file_path}/{file_name}.bmp', res)
        
def readbmp(file_path):
    return opencv.imread(file_path, opencv.IMREAD_UNCHANGED)

def rotate(image, delta): # scipy.ndimage.rotate()
    """ Rotate the image by the angle you put in argument
    Args:
        image (2darray)
        delta (float): angle in degrees anticlowise

    Returns:
        dst: output image that has the size and the same type as image
    """
    rows, cols = image.shape
    M = opencv.getRotationMatrix2D((cols//2, rows//2), delta, 1)
    dst = opencv.warpAffine(image, M, (cols, rows))
    return dst
    
if __name__ == "__main__":
    res = readbmp('Targets\grid60x60_p3.bmp')
    try:
        os.makedirs("C:/Users/gabri/Desktop/Targets")
        saveasbmp(res, 'test')
    except FileExistsError:
        saveasbmp(res, 'test')