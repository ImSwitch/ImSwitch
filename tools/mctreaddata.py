import h5py
import numpy as np
import cv2

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

def create_video_from_hdf5(reader, output_video='output.mp4', reduction_factor=4, frame_rate=20):
    """
    Creates an MP4 video from monochrome images stored in an HDF5 file using an HDF5Reader instance.

    Args:
    reader (HDF5Reader): An instance of HDF5Reader for accessing the HDF5 data.
    output_video (str): Path for the output MP4 video.
    reduction_factor (int): Factor by which the dimensions of each frame are reduced.
    frame_rate (float): Frame rate of the output video.
    """
    # Assume that the first dimension is time, and retrieve the first frame to get dimensions
    first_frame = reader.read_slice(time_idx=0)
    height, width = first_frame.shape[0] // reduction_factor, first_frame.shape[1] // reduction_factor
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Define the codec and create VideoWriter object
    out = cv2.VideoWriter(output_video, fourcc, frame_rate, (width, height), isColor=False)

    # Get the total number of frames from the dataset dimensions
    num_frames = reader.get_num_dimensions()  # This should be adjusted if get_num_dimensions() does not return the number of frames

    # Loop through the dataset and process each frame
    for i in range(num_frames):
        # Read image, assuming the reader returns a 2D numpy array for each frame
        img = reader.read_slice(time_idx=i)

        # Resize the image
        resized_img = cv2.resize(img, (width, height), interpolation=cv2.INTER_AREA)

        # Write to video, convert to 3 channels as OpenCV expects color images for color video
        out.write(cv2.cvtColor(resized_img, cv2.COLOR_GRAY2BGR))

    # Release everything when done
    out.release()

    print(f"Video created successfully: {output_video}")

# Example usage
from your_module import HDF5Reader  # Assuming HDF5Reader is in 'your_module.py'
reader = HDF5Reader('path_to_your_hdf5_file.h5')
create_video_from_hdf5(reader)


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

