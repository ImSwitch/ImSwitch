"""
    summary:
    
    date: 20/03/2024
    @author: Gabriel Lecarme
"""

import numpy as np
import matplotlib.pyplot as plt
import scipy.ndimage

import imswitch.imcontrol.controller.Generation_Hologramme.images as images
import imswitch.imcontrol.controller.Generation_Hologramme.parameters as param

def focalPoint(l):
    """Create a matrix of zeros with a one in the middle
    Args:
        l (int): matrix of shape (l, l)
    Returns:
        matrix of shape (l, l): matrix of zeros with a one in the middle
    """
    res = np.zeros((l, l))
    res[l//2, l//2] = 1
    return res

def focalArray(n, p, N: int):
    """Create a matrix of points
    Args:
        n (int): number of points n x n
        p (int): period in pixels
        N (int): N > n*p size of the target images (number of pixels N*N) recommended to be 512 or less
    Returns:
        matrix of shape (N, N): array of points
    """
    res = np.tile(focalPoint(p), (n, n))
    a = N - n*p
    return np.pad(res, ((a//2, (a+1)//2), (a//2, (a+1)//2)), 'constant')

def nonUniformArray(n, p, N: int):
    res = focalArray(n, p, N)
    nu = np.random.rand(n*n)
    res[res==1] = nu
    return res

def gauss2d(x, y, mu, sigma):
    """Calculate a 2D gaussian function on x*y
    """
    [X, Y] = np.meshgrid(x, y)
    res = 1/(sigma*np.sqrt(2*np.pi)) * np.exp(-((X - mu)**2 + (Y - mu)**2)/(2*sigma**2))
    return res

def gauss2D(shape=(3,3),sigma=0.5):
    """2D gaussian mask
    """
    n, m = [(ss-1.)/2. for ss in shape]
    y, x = np.ogrid[-m:m+1,-n:n+1]
    h = np.exp(-(x**2 + y**2)/(2*sigma**2))
    return h

def gaussFocalArray(n, p, N, w):
    """Create a multi foci of gaussian spots
    Args:
        n (int): number of spots n*n
        p (int): period in pixels
        w (int): width of the spots in pixels
    Returns:
        2d matrix: multi foci of gaussian spots
    """
    array = focalArray(n, p, N)
    h = gauss2D((w, w), 1)
    res = scipy.ndimage.convolve(array, h, mode='constant', cval=0.)
    return res

# Tests  
if __name__ == "__main__": 
    
    # Variables definition
    p = 5
    nb = 3
    w = 5    
    x = np.linspace(-2, 2, 1000)
    y = np.linspace(-2, 2, 1000)
    
    # Call functions
    point = focalPoint(p)
    array = focalArray(nb, p, nb*p)
    dist = gauss2d(x, y, 0, 1)
    h = gauss2D(shape=(15, 15), sigma=2)
    target = gaussFocalArray(nb, p, nb*p, w)
    
    # Visualisation
    plt.figure()
    plt.imshow(h)
    plt.colorbar()

    plt.figure()
    plt.imshow(target, cmap='plasma')
    plt.colorbar()
    
    fig, axes = plt.subplots(1, 2)
    ax1, ax2 = axes
    ax1.imshow(point)
    ax2.imshow(array)
    
    [X, Y] = np.meshgrid(x, y)
    fig = plt.figure()
    ax = fig.add_subplot(projection='3d')
    ax.plot_surface(X, Y, dist, cmap='viridis')
    
    plt.show()

    ideal = focalArray(param.n, param.period_grid, param.N)
    images.saveasbmp(ideal.astype(np.uint8), 'grid')
    
    target = gaussFocalArray(param.n, param.period_grid, param.N, param.spots_width)
    images.saveasbmp(target, 'multifoci') # to save as a bmp we need dtype(int8) values [0, 255]
    
    target = nonUniformArray(param.n, param.period_grid, param.N)
    images.saveasbmp(target, 'non-uniform') # to save as a bmp we need dtype(int8) values [0, 255]