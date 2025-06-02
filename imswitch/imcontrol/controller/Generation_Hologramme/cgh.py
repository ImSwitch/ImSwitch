# *_authors: Max N. Frankel & Gabriel Lecarme_*

import matplotlib.artist
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import time

import imswitch.imcontrol.controller.Generation_Hologramme.parameters as param
import imswitch.imcontrol.controller.Generation_Hologramme.images as images

def normalize(array):
    """ Normalize array between [0; 1] """
    return (array - np.min(array)) / (np.max(array) - np.min(array))

def evalPerformances(signal, target):
    """ Evaluate the performances of gsw """
    I = signal[target!=0]
    efficiency = np.sum(I) / np.sum(signal)
    Imax = np.max(I)
    Imin = np.min(I)
    uniformity = 1 - (Imax - Imin) / (Imax + Imin) # 1 - (max(I) - min(I)) / (max(I) + min(I))
    Var = np.mean((I - np.mean(I)) ** 2)
    std = np.sqrt(Var) / np.mean(I) # sqrt(<(I - <I>) ^ 2>) / <I>
    # std = np.sqrt(np.mean((target[target!=0] - I) ** 2)) / np.mean(I)
    return efficiency, uniformity, std

def GSW(phase_slm, target, niter=30, F=20, perfsaveas=None):
    """ This function performs the (weighted) Gerchberg-Saxton algorithm
    
    # inputs:
        - phase_slm: square array with initial guess for the slm phase, with values between -pi and pi
        - target: square 2darray image target dtype(np.uint8)
        - niter: number of iterations in the algorithm
        - F: number of iterations after which trap phase becomes fixed
        - track_perf: type(str) default=None if not, the performances at each iteration will be stored as ./track_pref.csv
    
    # outputs:
        - phase_slm: 2D array of values between -pi and pi. 
    Values come from the optimization of the slm phase using the GS method.
        (- performances: list of performances = [efficiency, uniformity, std] on the last iteration)
    """
    size = target.shape
    target = target / 255
    
    u = np.zeros(size, dtype=complex) # initialize complex amplitude of the field in slm plane
    v = np.zeros(size, dtype=complex) # initialize complex amplitude of the field in image plane
    weights = np.ones(size , dtype=float) # initialize a set of weights
    source = np.ones(size) # assumed uniform (at first), depending on the source distribution on the hologram area
    
    performances = []
    
    for k in range(niter):
        print(f"\033[1A \x1b[2K GSW iteration number: {k+1}")  

        u = source * np.exp(1j*phase_slm) # slm electric field, known phase
        
        v = np.fft.fft2(u) # FT
        v = np.fft.fftshift(v) # Take the (0, 0) frequencies back in the middle
        
        amplitude = np.abs(v) # extract amplitude
        
        if k < F: # phase fixing to converge faster in uniformity
            phase = np.angle(v) # extract phase
            
        I = amplitude**2 # compare the signal respect to the target to determine weights
        signal = normalize(I)
        
        # weights = np.sqrt(target) / amplitude * weights # Weights calculation
        weights[target!=0] = np.sqrt(target[target!=0] / signal[target!=0]) * weights[target!=0]
        
        v = weights * np.sqrt(target) * np.exp(1j*phase)
                
        v = np.fft.ifftshift(v)
        u = np.fft.ifft2(v) # FT^-1
            
        phase_slm = np.angle(u) # extract phase
        
        performances.append(evalPerformances(signal, target))
    
    if not perfsaveas==None:
        df = pd.DataFrame(performances, index=range(1, niter+1), columns=['e', 'u', '\u03C3'])
        df.index.name = ('n° iteration')
        df.to_csv(f'{param.file_path}/CGH/perf_gsw_{perfsaveas}.csv')

    cgh = phase_slm
    performances = performances[-1]
    print(f'Theoretical performance (e,u,\u03C3) = {performances}') # this tells us how well the final hologram created by the GSW algorithm performed
    return cgh

def simulate(cgh):
    """ Reconstruct the image """
    source = np.ones(cgh.shape)
    u = source * np.exp(1j*(cgh))
    v = np.fft.fft2(u)
    v = np.fft.fftshift(v)
    image = abs(v)**2
    image = normalize(image)
    return image
    
def showPerformances(csv_path: str):
    """ Plot the performances saved as a csv with index the nb of iterations well formatted
    """
    df = pd.read_csv(csv_path)
    df = df.set_index('n° iteration')
    x = df.index
    labels = df.columns
    fig = plt.figure()
    fig.suptitle("Convergence of the GSW through iterations")
    gs = fig.add_gridspec(nrows=6, ncols=9, hspace=1.2, wspace=1.2)
    ax = fig.add_subplot(gs[:, :7])
    e, = ax.plot(x.values, df.e.values, '.-', label='Efficiency') # list element by element equivalent to e = e[0]
    u = ax.plot(x, df.u, '.-', label='Uniformity') # Returns a list of Line2D
    u = u[0]
    e.set_color('orange')
    u.set_color('c')
    # handles, labels = ax.get_legend_handles_labels()
    # matplotlib.artist.getp(u)
    ax.set_xlabel(x.name)
    ax.legend(loc=4)
    std = fig.add_subplot(gs[-2:, -2:])
    std.plot(x, df.iloc[:,2], 'c', label='sigma')
    std.set_title('std')
    std.legend(loc='upper right')
    return fig
    
if __name__ == "__main__": 
    target = images.readbmp('Hamamatsu\sakura_256x256.bmp')
    phase_slm = (np.random.rand(target.shape[0], target.shape[1])*2 - 1)*np.pi
    cgh = GSW(phase_slm, target, niter=50, F=30, perfsaveas='test')
    images.savecgh(cgh, 'test')
    res = simulate(cgh)
    
    plt.figure()
    plt.imshow(normalize(target))
    
    fig, ax = plt.subplots()
    fig.suptitle('Generated raw hologram')
    im = ax.imshow(cgh, vmin=-np.pi, vmax=np.pi)
    cbar = fig.colorbar(im, ticks=[-np.pi, 0, np.pi])
    cbar.ax.set_yticklabels(['-\u03C0', '0', '\u03C0'])  # Add colorbar, make sure to specify tick locations to match desired ticklabels
    
    fig, ax = plt.subplots()
    fig.suptitle('Image')
    im = ax.imshow(res, cmap='plasma')
    fig.colorbar(im)
    
    # showPerformances('CGH/perf_gsw_test.csv')
    plt.gcf().savefig('test.png')

    plt.show()

