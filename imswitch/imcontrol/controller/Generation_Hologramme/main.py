import numpy as np


import imswitch.imcontrol.controller.Generation_Hologramme.multifoci as multifoci
import imswitch.imcontrol.controller.Generation_Hologramme.cgh as cgh
import imswitch.imcontrol.controller.Generation_Hologramme.phaseimages as phaseimages
import imswitch.imcontrol.controller.Generation_Hologramme.images as images


import imswitch.imcontrol.controller.Generation_Hologramme.parameters as param




def hologramCreationMFA():
    target = multifoci.focalArray(param.n, param.period_grid, param.N) # Create the target
    phase_slm = (np.random.rand(target.shape[0], target.shape[1])*2 - 1)*np.pi # initialisation for the GSW Algorithm
    hologram = cgh.GSW(phase_slm, target, niter=50, F=30, perfsaveas=None) # Calculate cgh
    hologram = phaseimages.padCGH(hologram, param.size_slm) # pad and correct
    images.savephaseimage(hologram, f'{param.file_name}') # save the phase image to display

if __name__ == '__main__':    

    hologramCreationMFA()

    pass