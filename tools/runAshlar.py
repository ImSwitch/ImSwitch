import os
import re

import tifffile

# adjust to dataset:
input_dir = "PATH_TO_TIFFS"
pixel_size = 0.225
maximum_shift_microns = 50

# adjust to desired output directories:
collected_tiles_file = 'PATH_TO_TILE_COLLECTION.ome.tif'
ashlar_output_file = "PATH_TO_STITCH_RESULT.ome.tif"

# Get the list of files
images = os.listdir(input_dir)
images.sort()

with tifffile.TiffWriter(collected_tiles_file) as tif:

    for img_name in images:
        image = tifffile.imread(input_dir + img_name)
        match = re.search(r'\((.*?), (.*?)\)', img_name)
        # the positions in the file names provide the center of the tile,
        # we need to subtract half the size of the image to get to the top left corner position
        x = float(match.group(1)) - image.shape[0] / 2. * pixel_size
        y = float(match.group(2)) - image.shape[1] / 2. * pixel_size

        print("Writing %s into OME-TIF at position %s:%s.." % (img_name, x, y))

        metadata = {
            'Pixels': {
                'PhysicalSizeX': pixel_size,
                'PhysicalSizeXUnit': 'µm',
                'PhysicalSizeY': pixel_size,
                'PhysicalSizeYUnit': 'µm'
            },
            'Plane': {
                'PositionX': x,
                'PositionY': y
            }
        }
        tif.write(image, metadata=metadata)

print("Stitching tiles with ashlar..")
from ashlar.scripts import ashlar
ashlar.main(['', collected_tiles_file, '-o', ashlar_output_file, '--pyramid', '-m%s' % maximum_shift_microns])