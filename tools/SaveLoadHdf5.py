import h5py
import numpy as np

# Example data dimensions
num_timepoints = 5
num_channels = 3  # e.g., Laser1, Laser2, LED
num_z_slices = 10
image_width, image_height = 512, 512

# Create an example dataset
# For simplicity, let's create a random dataset with dimensions: T, C, Z, Y, X
data = np.random.rand(num_timepoints, num_channels, num_z_slices, image_height, image_width).astype('float32')

# Create HDF5 file
mFile =  h5py.File('timelapse_data.h5', 'w')

# Create a dataset for image data
dset = mFile.create_dataset('ImageData', data=data, compression="gzip")

# Store metadata for each frame
for t in range(num_timepoints):
    for c in range(num_channels):
        for z in range(num_z_slices):
            # Example metadata for each frame
            metadata = {
                'timepoint': t,
                'channel': f'Channel_{c}',
                'z_slice': z,
                'additional_info': 'example'
            }
            # Convert metadata to string (or use JSON for more complex structures)
            metadata_str = str(metadata)
            
            # Store metadata in attributes of the dataset
            dset.attrs[f'metadata_{t}_{c}_{z}'] = metadata_str


import h5py
import json

# Open the HDF5 file
with h5py.File('timelapse_data.h5', 'r') as file:
    # Load the image data
    image_data = file['ImageData'][:]
    
    # Example: Read metadata for a specific frame
    t, c, z = 0, 0, 0  # Specify the frame you're interested in
    metadata_str = file['ImageData'].attrs[f'metadata_{t}_{c}_{z}']
    
    # If you used JSON to store the metadata, you can convert it back to a dictionary
    # metadata = json.loads(metadata_str)
    print(metadata_str)

    # To read all metadata, iterate over the attributes
    for key, value in file['ImageData'].attrs.items():
        print(f"{key}: {value}")
