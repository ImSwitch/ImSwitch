import numpy as np
from tifffile import TiffFile, imwrite
#from ome_types import create_ome_image, from_xml, to_xml


#https://forum.image.sc/t/python-tifffile-ome-full-metadata-support/56526/11

import tifffile
import numpy as np

# 5-channel image of size 30x30
imgs = [np.ones((5, 30, 30), dtype=np.uint8)*i for i in range(9)]
positions = np.array([np.unravel_index(i, (3, 3)) for i in range(9)])
# ashlar uses `PhysicalSizeX/Y` for pixel unit conversion
pixel_size = 0.3

with tifffile.TiffWriter('test.ome.tif', bigtiff=True) as tif:
    for img, p in zip(imgs, positions):
        metadata = {
            'Pixels': {
                'PhysicalSizeX': pixel_size,
                'PhysicalSizeXUnit': 'µm',
                'PhysicalSizeY': pixel_size,
                'PhysicalSizeYUnit': 'µm'
            },
            # a mock 10% overlap therefore each step is 27 pixels
            'Plane': {
                'PositionX': [p[1]*pixel_size*27]*img.shape[0],
                'PositionY': [p[0]*pixel_size*27]*img.shape[0]
            }
        }
        tif.write(img, metadata=metadata)
        
        
# Function to add new image plane to OME metadata
def add_plane_to_ome(ome, z, c, t):
    plane = ome.images[0].pixels.planes[-1].copy() if ome.images[0].pixels.planes else None
    if plane:
        plane.z, plane.c, plane.t = z, c, t
    else:
        # If no previous plane exists, create a new one
        from ome_types.model.simple_types import DimensionOrder
        plane = ome.images[0].pixels.create_plane(the_z=z, the_c=c, the_t=t)
    ome.images[0].pixels.planes.append(plane)
    return ome

# Initial OME metadata
ome = create_ome_image(np.zeros((512, 512), dtype=np.uint8), name="example")

output_filename = 'path_to_output_ome.tif'

# Example loop for processing and appending images
for idx in range(10):
    # Example: create a random image
    new_image = np.random.randint(0, 256, (512, 512), dtype=np.uint8)

    # Update OME metadata for new plane (set your appropriate z, c, t values)
    ome = add_plane_to_ome(ome, z=idx, c=0, t=0)

    # Save or append the new image with updated metadata to OME-TIFF
    if idx == 0:
        imwrite(output_filename, new_image, ome=to_xml(ome))
    else:
        with TiffFile(output_filename, mode='a') as tif:
            tif.write(new_image, ome=to_xml(ome))

print("OME-TIFF file saved successfully!")


