import h5py
import numpy as np

# HDF5 file setup
filename = 'timelapse_data.h5'

# Initial dataset dimensions: (time, channels, z, y, x)
# Starting with a single time point, 3 channels, 1 z slice, and an image size of 512x512
init_dims = (1, 3, 1, 512, 512) # time, channels, z, y, x
max_dims = (None, 3, None, 512, 512)  # Allow unlimited time points and z slices

with h5py.File(filename, 'w') as file:
    # Create a resizable dataset for the image data
    dset = file.create_dataset('ImageData', shape=init_dims, maxshape=max_dims, dtype='float32', compression="gzip")
    
    # Initialize a group for storing metadata
    meta_group = file.create_group('Metadata')


# Function to simulate receiving new frame data
def get_new_frame_data(timepoint, num_channels=3, z_slices=10, height=512, width=512):
    # Simulate frame data
    data = np.random.rand(num_channels, z_slices, height, width).astype('float32')
    # Simulate XYZ coordinates for each channel
    xyz_coordinates = [(np.random.randint(0, 100), np.random.randint(0, 100), np.random.randint(0, 100)) for _ in range(num_channels)]
    return data, xyz_coordinates

# Function to append new data and metadata to the HDF5 file
def append_data(filename, timepoint, frame_data, xyz_coordinates):
    with h5py.File(filename, 'a') as file:
        dset = file['ImageData']
        meta_group = file['Metadata']
        
        # Resize the dataset to accommodate the new timepoint
        current_size = dset.shape[0]
        dset.resize(current_size + 1, axis=0)
        
        # Add the new frame data
        dset[current_size, :, :, :, :] = frame_data
        
        # Add metadata for the new frame
        for channel, xyz in enumerate(xyz_coordinates):
            meta_group.create_dataset(f'Time_{timepoint}_Channel_{channel}', data=xyz)

# Simulate adding 5 new time points to the dataset
for timepoint in range(5):
    frame_data, xyz_coordinates = get_new_frame_data(timepoint, num_channels=init_dims[1], z_slices=init_dims[2], height=init_dims[3], width=init_dims[4]) # channels, z-slices, height, width
    append_data(filename, timepoint, frame_data, xyz_coordinates)


# Function to read data and metadata from the HDF5 file
def read_data(filename):
    with h5py.File(filename, 'r') as file:
        # Read image data
        image_data = file['ImageData'][:]
        
        # Read metadata
        metadata = {}
        meta_group = file['Metadata']
        for name, dataset in meta_group.items():
            metadata[name] = dataset[:]
            
        return image_data, metadata

# Example usage
image_data, metadata = read_data(filename)
print("Image Data Shape:", image_data.shape)
print("Metadata Keys:", list(metadata.keys()))
