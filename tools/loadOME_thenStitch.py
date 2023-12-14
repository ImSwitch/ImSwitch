import tifffile
import os
import xml.etree.ElementTree as ET

file_name = "test_2023-09-20T20_20_15.ome.tif"
file_name = "test_2023-09-28T20_59_15.ome.tif"
file_path = os.path.join('C:\\Users\\UC2\\Documents\\ImSwitchConfig\\histoController\\', file_name)
with tifffile.TiffFile(file_path) as tif:
    ome_metadata = tif.ome_metadata
    images = tif.series
    root = ET.fromstring(ome_metadata)

    datas = {}
    # Navigate and extract information
    for image in root.findall('{http://www.openmicroscopy.org/Schemas/OME/2016-06}Image'):
        image_name = image.get('Name')
        pixels = image.find('{http://www.openmicroscopy.org/Schemas/OME/2016-06}Pixels')
        
        physical_size_x = pixels.get('PhysicalSizeX')
        physical_size_y = pixels.get('PhysicalSizeY')
        
        plane = pixels.find('{http://www.openmicroscopy.org/Schemas/OME/2016-06}Plane')
        position_x = plane.get('PositionX')
        position_y = plane.get('PositionY')
        
        datas[image_name]= {
            "pixX":physical_size_x,
            "pixY":physical_size_y,
            "posX":position_x, 
            "posY":position_y}
        if 0:
            print(f"Image Name: {image_name}")
            print(f"Physical Size X: {physical_size_x} µm")
            print(f"Physical Size Y: {physical_size_y} µm")
            print(f"Position X: {position_x}")
            print(f"Position Y: {position_y}")
            print("-" * 50)

   
    for idx, image in enumerate(images):
        # Retrieve image data
        img_data = image.asarray()
        datas[image.name]["data"] = img_data


import numpy as np
from skimage.io import imsave
from scipy.ndimage import gaussian_filter
from collections import deque
import threading
import time 
import cv2
import matplotlib.pyplot as plt
#import NanoImagingPack as nip

class ImageStitcher:

    def __init__(self, parent, min_coords, max_coords,  folder, file_name, extension, subsample_factor=.25, backgroundimage=None):
        # Initial min and max coordinates 
        self._parent = parent
        self.subsample_factor = subsample_factor
        self.min_coords = np.int32(np.array(min_coords)*self.subsample_factor)
        self.max_coords = np.int32(np.array(max_coords)*self.subsample_factor)
        
        # determine write location
        self.file_path = os.sep.join([folder, file_name + extension])
        
        # Create a blank canvas for the final image and a canvas to track blending weights
        self.nY = self.max_coords[1] - self.min_coords[1]
        self.nX = self.max_coords[0] - self.min_coords[0]
        self.stitched_image = np.zeros((self.nY, self.nX, 3), dtype=np.float32)
        self.weight_image = np.zeros(self.stitched_image.shape, dtype=np.float32)
        self.stitched_image_shape= self.stitched_image.shape

        # Queue to hold incoming images
        self.queue = deque()

        # Thread lock for thread safety
        self.lock = threading.Lock()

        # Start a background thread for processing the queue
        self.processing_thread = threading.Thread(target=self._process_queue)
        self.isRunning = True
        self.processing_thread.start()

    def add_image(self, img, coords, metadata):
        with self.lock:
            self.queue.append((img, coords, metadata))

    def _process_queue(self):
        #with tifffile.TiffWriter(self.file_path, bigtiff=True, append=True) as tif:
            while self.isRunning:
                with self.lock:
                    if not self.queue:
                        time.sleep(.1) # unload CPU
                        continue
                    img, coords, metadata = self.queue.popleft()
                    self._place_on_canvas(img, coords)

                    # write image to disk
                    #tif.write(data=img, metadata=metadata)
            

    def _place_on_canvas(self, img, coords):
        # these are pixelcoordinates (e.g. center of the imageslice)
        offset_x = int(coords[0]*self.subsample_factor - self.min_coords[0])
        offset_y = int(self.max_coords[1]-coords[1]*self.subsample_factor)

        # Calculate a feathering mask based on image intensity
        img = cv2.resize(np.copy(img), None, fx=self.subsample_factor, fy=self.subsample_factor, interpolation=cv2.INTER_NEAREST) 
        img = np.flip(np.flip(img,1),0)
        alpha = np.mean(np.copy(img), axis=-1)
        alpha = gaussian_filter(alpha, sigma=10)
        alpha /= np.max(alpha)

        try: 
            stitchDim = self.stitched_image[offset_y-img.shape[0]:offset_y, offset_x:offset_x+img.shape[1]].shape
            self.stitched_image[offset_y-img.shape[0]:offset_y, offset_x:offset_x+img.shape[1]] = (img * alpha[:, :, np.newaxis])[0:stitchDim[0], 0:stitchDim[1]]
            #self.weight_image[offset_y-img.shape[0]:offset_y, offset_x:offset_x+img.shape[1]]+= alpha[:, :, np.newaxis]
            
            if 0:
                from datetime import datetime

                # Get the current datetime
                now = datetime.now()
                #plt.imsave("test"+str(now.strftime('%H_%M_%S'))+".png", np.uint8(255*mResult/np.max(mResult)))

            # try to display in napari if ready
            #self._parent.setImageForDisplay(self.stitched_image, "Stitched Image")
        except Exception as e:
            print(e)

    def get_stitched_image(self):
        with self.lock:
            # Normalize by the weight image to get the final result
            stitched = self.stitched_image / np.maximum(self.weight_image, 1e-5)
            self.isRunning = False
            return stitched

    def save_stitched_image(self, filename):
        stitched = self.get_stitched_image()
        imsave(filename, stitched)

minPosX = np.inf
maxPosX = -np.inf
minPosY = np.inf
maxPosY = -np.inf
pixelSizeUm = float(datas["Image1"]["pixX"])
img_dimensions = datas["Image1"]["data"].shape[0:2]


mImageBackground = None
for image_key, image_data in datas.items():
    pixX_value = float(image_data['pixX'])
    posY_value = float(image_data['posY'])
    posX_value = float(image_data['posX'])
    if mImageBackground is None:
        mImageBackground = image_data['data']
    else:
        mImageBackground += image_data['data']
    
    # find minpos
    if posX_value < minPosX:
        minPosX = posX_value
    if posX_value > maxPosX:
        maxPosX = posX_value

    if posY_value < minPosY:
        minPosY = posY_value
    if posY_value > maxPosY:
        maxPosY = posY_value

mImageBackground =  gaussian_filter(np.array(mImageBackground)/100,  sigma=10)

# subtract offset and normalize to pixel coordinates 

maxPosY = int((maxPosY-minPosY)/pixelSizeUm)
maxPosX = int((maxPosX-minPosX)/pixelSizeUm)

stitcher = ImageStitcher(None, min_coords=(0,0), max_coords=(maxPosX, maxPosY), 
                            folder="", file_name="", extension="")

for image_key, image_data in datas.items():
    posY_value = (float(image_data['posY'])-minPosY)/pixelSizeUm
    posX_value = (float(image_data['posX'])-minPosX)/pixelSizeUm
    iPos = (posX_value, posY_value)
    mFrame = image_data['data']/mImageBackground
    print(image_key)
    
    stitcher._place_on_canvas(mFrame, iPos)

mStitch = stitcher.get_stitched_image()
import matplotlib.pyplot as plt
plt.imshow(mStitch/np.max(mStitch))
plt.show()
import tifffile
tifffile.imwrite("teststitch.tif", mStitch)
input()