import h5py
import numpy as np

class HDF5Reader:
    def __init__(self, filename):
        """
        Initialize the reader with the HDF5 file.

        Args:
        filename (str): The path to the HDF5 file.
        """
        self.filename = filename

    def read_slice(self, time_idx, channel_idx=None, z_slice=None, y_slice=None, x_slice=None):
        """
        Read a specific slice of the dataset from the HDF5 file.

        Args:
        time_idx (int): Index of the time dimension to slice.
        channel_idx (int, optional): Index of the channel dimension to slice. If None, all channels are returned.
        z_slice (slice, optional): Slice object for the z dimension.
        y_slice (slice, optional): Slice object for the y dimension.
        x_slice (slice, optional): Slice object for the x dimension.

        Returns:
        np.ndarray: The sliced data.
        """
        with h5py.File(self.filename, 'r') as file:
            dset = file['ImageData']
            if channel_idx is None:
                return dset[time_idx, :, z_slice, y_slice, x_slice]
            else:
                return dset[time_idx, channel_idx, z_slice, y_slice, x_slice]

    def read_metadata(self, time_idx, channel_idx):
        """
        Read metadata for a specific time point and channel.

        Args:
        time_idx (int): Time index for the metadata.
        channel_idx (int): Channel index for the metadata.

        Returns:
        np.ndarray: The metadata array.
        """
        with h5py.File(self.filename, 'r') as file:
            meta_group = file['Metadata']
            meta_key = f'Time_{time_idx}_Channel_{channel_idx}'
            return np.array(meta_group[meta_key])

    def get_num_dimensions(self):
        """
        Get the number of dimensions in the ImageData dataset.

        Returns:
        int: Number of dimensions of the dataset.
        """
        with h5py.File(self.filename, 'r') as file:
            dset = file['ImageData']
            return len(dset.shape)


# Example of using the HDF5Reader with dimensionality query
mFilename = 'C:\\Users\\user\\Documents\\ImSwitchConfig\\recordings\\2024_04_18-02-05-01_PM\\2024_04_18-02-05-01_PM_MCT.h5'
reader = HDF5Reader(mFilename)

# Getting the number of dimensions of the dataset
num_dimensions = reader.get_num_dimensions()
print(f"The dataset has {num_dimensions} dimensions.")

# Reading a slice of the data
data_slice = reader.read_slice(time_idx=1, channel_idx=1, z_slice=slice(0, 1), y_slice=slice(None), x_slice=slice(None))
print(data_slice)

# Reading metadata for a specific time point and channel
metadata = reader.read_metadata(time_idx=1, channel_idx=1)
print(metadata)
