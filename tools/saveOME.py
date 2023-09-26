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
        