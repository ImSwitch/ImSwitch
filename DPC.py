# %%
#%load_ext autoreload
#%autoreload 2
#%matplotlib notebook
import numpy as np
import matplotlib.pyplot as plt
from os import listdir
from skimage import io
from mpl_toolkits.axes_grid1 import make_axes_locatable
from dpc_algorithm import DPCSolver
from display_phase import show_phase,show_spectrum

# %% [markdown]
#  # Load DPC Measurements

# %%
data_path  = "C:\\Users\\T490\\Documents\\GitHub\\ImSwitch\\imswitch\\ImSwitch\\recordings\\" #INSERT YOUR DATA PATH HERE
image_list = listdir(data_path)
image_list = [image_file for image_file in image_list if image_file.endswith(".tif")]
image_list.sort()
dpc_images_raw = np.array([io.imread(data_path+image_list[image_index]) for image_index in range(len(image_list))])

data_path  = "../Figs_ff/" #INSERT YOUR DATA PATH HERE
image_list = listdir(data_path)
image_list = [image_file for image_file in image_list if image_file.endswith(".tif")]
image_list.sort()
dpc_images_ff = np.array([io.imread(data_path+image_list[image_index]) for image_index in range(len(image_list))])

dpc_images = np.divide(dpc_images_raw,dpc_images_ff)

# %%
data_path  = "C:\\Users\\T490\\Documents\\GitHub\\ImSwitch\\imswitch\\ImSwitch\\recordings\\DPC_Figs\\" #INSERT YOUR DATA PATH HERE
image_list = listdir(data_path)
image_list = [image_file for image_file in image_list if image_file.endswith(".tif")]
image_list.sort()
dpc_images_raw = np.array([io.imread(data_path+image_list[image_index]) for image_index in range(len(image_list))])

data_path  = "C:\\Users\\T490\\Documents\\GitHub\\ImSwitch\\imswitch\\ImSwitch\\recordings\\Figs_ff\\" #INSERT YOUR DATA PATH HERE
image_list = listdir(data_path)
image_list = [image_file for image_file in image_list if image_file.endswith(".tif")]
image_list.sort()
dpc_images_ff = np.array([io.imread(data_path+image_list[image_index]) for image_index in range(len(image_list))])

dpc_images = np.divide(dpc_images_raw,dpc_images_ff)

# %%
data_path  = "C:\\Users\\T490\\Documents\\GitHub\\ImSwitch\\imswitch\\ImSwitch\\recordings\\DPC\\DPC_Figs\\" #INSERT YOUR DATA PATH HERE
image_list = listdir(data_path)
image_list = [image_file for image_file in image_list if image_file.endswith(".tif")]
image_list.sort()
dpc_images_raw = np.array([io.imread(data_path+image_list[image_index]) for image_index in range(len(image_list))])

data_path  = "C:\\Users\\T490\\Documents\\GitHub\\ImSwitch\\imswitch\\ImSwitch\\recordings\\DPC\\Figs_ff\\" #INSERT YOUR DATA PATH HERE
image_list = listdir(data_path)
image_list = [image_file for image_file in image_list if image_file.endswith(".tif")]
image_list.sort()
dpc_images_ff = np.array([io.imread(data_path+image_list[image_index]) for image_index in range(len(image_list))])

dpc_images = np.divide(dpc_images_raw,dpc_images_ff)

# %%
#plot first set of measured DPC measurements
f, ax = plt.subplots(2, 2, sharex=True, sharey=True, figsize=(6, 6))

for plot_index in range(4):
    plot_row = plot_index//2
    plot_col = np.mod(plot_index, 2)
    ax[plot_row, plot_col].imshow(dpc_images[plot_index], cmap="gray",\
                                  extent=[0, dpc_images[0].shape[-1], 0, dpc_images[0].shape[-2]])
    ax[plot_row, plot_col].axis("off")
    ax[plot_row, plot_col].set_title("DPC {:02d}".format(plot_index))
    
plt.show()

# %% [markdown]
#  # Set System Parameters

# %%
wavelength     =  0.525 #micron
mag            =   20.0
na             =   0.5 #numerical aperture
na_in          =    0.4 #inner radius of illumination na
pixel_size_cam =    3.2 #pixel size of camera
dpc_num        =      4 #number of DPC images captured for each absorption and phase frame
pixel_size     = pixel_size_cam/mag
rotation       = [0, 180, 90, 270] #degree

# %% [markdown]
#  # DPC Absorption and Phase Retrieval

# %% [markdown]
#  ## Initialize DPC Solver

# %%
dpc_solver_obj = DPCSolver(dpc_images, wavelength, na, na_in, pixel_size, rotation, dpc_num=dpc_num)

# %% [markdown]
#  ## Visualize Source Patterns

# %%
#plot the sources
max_na_x = max(dpc_solver_obj.fxlin.real*dpc_solver_obj.wavelength/dpc_solver_obj.na)
min_na_x = min(dpc_solver_obj.fxlin.real*dpc_solver_obj.wavelength/dpc_solver_obj.na)
max_na_y = max(dpc_solver_obj.fylin.real*dpc_solver_obj.wavelength/dpc_solver_obj.na)
min_na_y = min(dpc_solver_obj.fylin.real*dpc_solver_obj.wavelength/dpc_solver_obj.na)
f, ax  = plt.subplots(2, 2, sharex=True, sharey=True, figsize=(6, 6))
for plot_index, source in enumerate(list(dpc_solver_obj.source)):
    plot_row = plot_index//2
    plot_col = np.mod(plot_index, 2)
    ax[plot_row, plot_col].imshow(np.fft.fftshift(dpc_solver_obj.source[plot_index]),\
                                  cmap='gray', clim=(0,1), extent=[min_na_x, max_na_x, min_na_y, max_na_y])
    ax[plot_row, plot_col].axis("off")
    ax[plot_row, plot_col].set_title("DPC Source {:02d}".format(plot_index))
    ax[plot_row, plot_col].set_xlim(-1.2, 1.2)
    ax[plot_row, plot_col].set_ylim(-1.2, 1.2)
    ax[plot_row, plot_col].set_aspect(1)

plt.show()

# %% [markdown]
#  ## Visualize Weak Object Transfer Functions

# %%
#plot the transfer functions
f, ax = plt.subplots(2, 4, sharex=True, sharey=True, figsize = (10, 4))
for plot_index in range(ax.size):
    plot_row = plot_index//4
    plot_col = np.mod(plot_index, 4)
    divider  = make_axes_locatable(ax[plot_row, plot_col])
    cax      = divider.append_axes("right", size="5%", pad=0.05)
    if plot_row == 0:
        plot = ax[plot_row, plot_col].imshow(np.fft.fftshift(dpc_solver_obj.Hu[plot_col].real), cmap='jet',\
                                             extent=[min_na_x, max_na_x, min_na_y, max_na_y], clim=[-2., 2.])
        ax[plot_row, plot_col].set_title("Absorption WOTF {:02d}".format(plot_col))
        plt.colorbar(plot, cax=cax, ticks=[-2., 0, 2.])
    else:
        plot = ax[plot_row, plot_col].imshow(np.fft.fftshift(dpc_solver_obj.Hp[plot_col].imag), cmap='jet',\
                                             extent=[min_na_x, max_na_x, min_na_y, max_na_y], clim=[-.8, .8])
        ax[plot_row, plot_col].set_title("Phase WOTF {:02d}".format(plot_col))
        plt.colorbar(plot, cax=cax, ticks=[-.8, 0, .8])
    ax[plot_row, plot_col].set_xlim(-2.2, 2.2)
    ax[plot_row, plot_col].set_ylim(-2.2, 2.2)
    ax[plot_row, plot_col].axis("off")
    ax[plot_row, plot_col].set_aspect(1)
plt.show()

# %% [markdown]
#  ## Solve DPC Least Squares Problem

# %%
#parameters for Tikhonov regurlarization [absorption, phase] ((need to tune this based on SNR)
dpc_solver_obj.setTikhonovRegularization(reg_u = 1e-1, reg_p = 1e-3)
dpc_result = dpc_solver_obj.solve()

# %%
_, axes  = plt.subplots(1, 2, figsize=(20, 12), sharex=True, sharey=True)
divider  = make_axes_locatable(axes[0])
cax_1    = divider.append_axes("right", size="5%", pad=0.05)
plot     = axes[0].imshow(dpc_result[0].real, clim=[-0.15, 0.05], cmap="gray", extent=[0, dpc_result[0].shape[-1], 0, dpc_result[0].shape[-2]])
axes[0].axis("off")
plt.colorbar(plot, cax=cax_1, ticks=[-0.15, 0.05])
axes[0].set_title("Absorption")
divider  = make_axes_locatable(axes[1])
cax_2    = divider.append_axes("right", size="5%", pad=0.05)
plot     = axes[1].imshow(dpc_result[0].imag, clim=[-0.5, 0.5], cmap="gray_r", extent=[0, dpc_result[0].shape[-1], 0, dpc_result[0].shape[-2]])
axes[1].axis("off")
plt.colorbar(plot, cax=cax_2, ticks=[-0.5, 0.5])
axes[1].set_title("Phase")
plt.show()

# %%
x_im,y_im = 1000,400
h,w = 1000,1000
show_phase(-dpc_result[0].imag,'',x_im, y_im,w,h,var_stab = True,colorbar=False,level=4,frame=False)
plt.show()
plt.imshow(dpc_images[0] + dpc_images[1],cmap='gray')
plt.title('Brightfield')
plt.axis('off')
plt.show()


