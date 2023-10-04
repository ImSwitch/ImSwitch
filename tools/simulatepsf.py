
#%%
import NanoImagingPack as nip
import numpy as np
import matplotlib.pyplot as plt 
obj = nip.image(np.random.rand(1000,1000))
obj.pixelsize = (10., 10.)
paraNoAber = nip.PSF_PARAMS();
#%
paraAbber = nip.PSF_PARAMS();
aber_map = nip.xx(obj.shape[-2:]).normalize(1);  # Define some aberration map (x-ramp in this case)
paraAbber.aberration_types = [paraAbber.aberration_zernikes.spheric]
paraAbber.aberration_strength = [1];
psf = nip.psf(obj, paraAbber);

# %
plt.imshow(np.squeeze(psf))
# %%
