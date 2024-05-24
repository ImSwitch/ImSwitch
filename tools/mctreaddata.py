import h5py
import numpy as np
import cv2
import tifffile as tif
import matplotlib.pyplot as plt 
import os
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
        if z_slice is None: z_slice = slice(None)
        if y_slice is None: y_slice = slice(None)
        if x_slice is None: x_slice = slice(None)
        if channel_idx is None: channel_idx = slice(None)
        with h5py.File(self.filename, 'r') as file:
            dset = file['ImageData']
            if channel_idx is None:
                return dset[time_idx, :, z_slice, y_slice, x_slice].copy()
            else:
                return dset[time_idx, channel_idx, z_slice, y_slice, x_slice].copy()

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

    def get_num_timepoints(self):
        """
        Get the number of time points in the ImageData dataset.

        Returns:
        int: Number of time points in the dataset.
        """
        with h5py.File(self.filename, 'r') as file:
            dset = file['ImageData']
            return dset.shape[0]
        
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
    first_frame = reader.read_slice(time_idx=1, channel_idx=1, z_slice=slice(1), y_slice=slice(None), x_slice=slice(None))
    height, width = first_frame.shape[2] // reduction_factor, first_frame.shape[1] // reduction_factor
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video, fourcc, 20.0, (height,width*3))
    
    # Get the total number of frames from the dataset dimensions
    num_frames = reader.get_num_dimensions()  # This should be adjusted if get_num_dimensions() does not return the number of frames
    nTimepoints = reader.get_num_timepoints()
    
    # Loop through the dataset and process each frame
    for iFrame in range(1,nTimepoints):
        mChannels = np.zeros((int(height), int(width*3)))
        for iChannel in range(3):
    
            # Read image, assuming the reader returns a 2D numpy array for each frame
            import time
            mTime = time.time()
            img = reader.read_slice(time_idx=iFrame, channel_idx=iChannel)
            print("1: "+str(mTime-time.time()))
            img = cv2.resize(img.copy(), dsize = None, fx = 1/reduction_factor, fy=1/reduction_factor, interpolation=cv2.INTER_AREA)
            print("2: "+str(mTime-time.time()))
            img = np.std(img, axis=0)  # Compute standard deviation along z axis
            print("3: "+str(mTime-time.time()))
            # change size of image
            
            mChannels[:, width*iChannel:width*(iChannel+1)] = img.T/np.max(img)
        print("added frame: "+str(iFrame))

        # Write to video, convert to 3 channels as OpenCV expects color images for color video
        
        if mChannels is not None and out.isOpened():
            # convert frame to rgb
            if 0:
                tif.imsave("test.tif", mChannels, append=True)
            else:
                # if folder not created create test folder
                if not os.path.exists('test'):
                    os.makedirs('test')
                plt.imsave("test/test"+str(iFrame)+".png", mChannels, cmap='gray')
            mResult = out.write(cv2.cvtColor(np.uint8(mChannels*255), cv2.COLOR_GRAY2BGR))
            print("Frame written: "+str(mResult))
        else:
            print("mChannels ist leer oder die Ausgabedatei ist nicht geöffnet.")
        

    # Release everything when done
    out.release()

    print(f"Video created successfully: {output_video}")

# Example usage


# Example of using the HDF5Reader with dimensionality query
mFilename = 'C:\\Users\\user\\Documents\\ImSwitchConfig\\recordings\\2024_04_18-02-05-01_PM\\2024_04_18-02-05-01_PM_MCT.h5'
mFilename = '/Users/bene/Downloads/2024_04_16-01-50-08_PM_MCT.h5'
mFilename = 'C:\\Users\\diederichbenedict\\Dropbox\LENA\\2024_04_18-05-24-16_PM\\2024_04_18-05-24-16_PM_MCT.h5'
reader = HDF5Reader(mFilename)

create_video_from_hdf5(reader)


# Getting the number of dimensions of the dataset
num_dimensions = reader.get_num_dimensions()
#print(f"The dataset has {num_dimensions} dimensions.")

# Reading a slice of the data
data_slice = reader.read_slice(time_idx=1, channel_idx=1, z_slice=slice(0, 1), y_slice=slice(None), x_slice=slice(None))
print(data_slice)


# Reading metadata for a specific time point and channel
#metadata = reader.read_metadata(time_idx=1, channel_idx=1)
#print(metadata)

