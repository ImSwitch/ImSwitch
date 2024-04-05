#%%
import numpy as np
import cv2
import NanoImagingPack as nip
import matplotlib.pyplot as plt
#skimage.restoration unwrap phase
#Optimize considering the cross lines in the first order
#%%

# Parameters
width, height = 512, 512  # Size of the simulation
wavelength = 0.6328e-6  # Wavelength of the light (in meters, example: 632.8nm for He-Ne laser)
k = 2 * np.pi / wavelength  # Wave number
angle = np.pi / 10  # Tilt angle of the plane wave

# Create a phase sample (this is where you define your phase object)
# For demonstration, a simple circular phase object
x = np.linspace(-np.pi, np.pi, width)
y = np.linspace(-np.pi, np.pi, height)
X, Y = np.meshgrid(x, y)
circle = (X**2 + Y**2)<np.pi
mSample = nip.readim()
phase_sample = np.exp(1j * (mSample/255.*1))
#phase_sample = np.exp(1j*np.ones(phase_sample.shape))

#%%

plt.imshow(np.angle(phase_sample))
plt.colorbar()
plt.show()

# Simulate the tilted plane wave
tilt_x =  k * np.sin(angle)
tilt_y = k * np.sin(angle)  # Change this if you want tilt in another direction
X, Y = np.meshgrid(np.arange(width), np.arange(height))
plane_wave = np.exp(1j * ((tilt_x * X) + (tilt_y * Y)))

plt.imshow(np.angle(plane_wave))
plt.colorbar()
plt.show()
plt.imshow(np.log(1+np.abs(nip.ft(plane_wave))))
plt.show()

#%%

# Superpose the phase sample and the tilted plane wave
filtered_phase_sample = nip.ift(circle * nip.ft(phase_sample))
hologram = filtered_phase_sample + plane_wave

plt.imshow(np.angle(hologram))
plt.show()
#plt.imshow(np.angle(np.conjugate(hologram)))
#plt.show()
plt.imshow(np.real(hologram*np.conjugate(hologram)))
plt.show()
plt.imshow(np.log(1+np.abs(nip.ft(hologram))))
plt.show()

#%%
# Calculate the intensity image (interference pattern)
intensity_image = np.real(hologram*np.conjugate(hologram))

plt.imshow(intensity_image)
plt.show()
plt.imshow(np.log(1+np.abs(nip.ft(intensity_image))))
plt.show()

#%%

# Normalize and convert to 8-bit format
intensity_image_normalized = cv2.normalize(intensity_image, None, 0, 255, cv2.NORM_MINMAX)
intensity_image_8bit = np.uint8(intensity_image_normalized)

# Display the result
plt.imshow(intensity_image) 
plt.show()
plt.imshow(np.log(1+np.abs(nip.ft(intensity_image))))
plt.show()

#ask for quadrant location
#define window filter (one third as a radius)

#subtract the background for refractive index calculation

#%%
plt.imshow(np.abs(np.log(1+nip.ft(intensity_image))))
# %%

plt.imshow(np.angle(hologram))
# %%
# An example propagating a Gaussian peak through vacuum
import NanoImagingPack as nip
import numpy as np

myshape = [100,100,100]
pixelsize = [100.0,100.0,100.0] # in nm
input_plane = nip.gaussian(myshape[-2:], sigma=[3.0,5.0]) * np.exp(1j*nip.xx(myshape[-2:])*2.0*np.pi*0.03)
input_plane.pixelsize=pixelsize[-2:]
PSFpara = nip.PSF_PARAMS();  # wavelength is 520nm
pupil = nip.ft(input_plane)
propagatedFT = nip.propagatePupil(pupil, sizeZ= myshape[0], distZ=pixelsize[0], psf_params=PSFpara)
propagated = nip.ift2d(propagatedFT)
propagated

# %%