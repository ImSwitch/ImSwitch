import os
import re
import tifffile
import numpy as np
import cv2

# Function to extract information from filename
def parse_filename(filename):
    # Extract date, Z position, and channel using regex
    match = re.search(r'(\d{4}_\d{2}_\d{2})-.*_Z_(-?\d+\.\d+).*_(LED|Laser\d)_', filename)
    if match:
        return match.group(1), float(match.group(2)), match.group(3)
    return None, None, None

# Function to load images from a folder
def load_images_from_folder(folder):
    images = {}
    for filename in os.listdir(folder):
        if filename.endswith(".tif"):
            date, z_pos, channel = parse_filename(filename)
            if date and z_pos and channel:
                key = (date, channel, z_pos)
                img_path = os.path.join(folder, filename)
                img = tifffile.imread(img_path)
                if key in images:
                    images[key].append(img)
                else:
                    images[key] = [img]
    return images

# Loading images from all folders
all_images = {}

import os
# Specify the parent directory
parent_directory = 'C:\\Users\\user\\Documents\\ImSwitchConfig\\recordings\\2024_01_22-04-43-17_PM'
# List all subdirectories starting with 't'
subfolders = [f.name for f in os.scandir(parent_directory) if f.is_dir() and f.name.startswith('t')]
# Print the list of subfolders
print(subfolders)

for folder in subfolders:
    all_images.update(load_images_from_folder(parent_directory+"\\"+folder))

# Organizing and concatenating images for each channel
timelapses = {}
for key in sorted(all_images.keys()):
    date, channel, z_pos = key
    if channel not in timelapses:
        timelapses[channel] = []
    # Assuming that images for the same channel and date are part of the same timeseries
    timelapses[channel].append(np.concatenate(all_images[key], axis=1))

# Creating timelapse videos
for channel in timelapses:
    height, width, _ = timelapses[channel][0].shape
    out = cv2.VideoWriter(f'timelapse_{channel}.avi', cv2.VideoWriter_fourcc(*'DIVX'), 10, (width, height))
    for img in timelapses[channel]:
        out.write(img)
    out.release()
