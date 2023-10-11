import numpy as np
from skimage.io import imsave
from scipy.ndimage import gaussian_filter
from collections import deque

class ImageStitcher:

    def __init__(self, min_coords, max_coords):
        # Initial min and max coordinates 
        self.min_coords = min_coords
        self.max_coords = max_coords

        # Create a blank canvas for the final image and a canvas to track blending weights
        self.stitched_image = np.zeros((max_coords[1] - min_coords[1], max_coords[0] - min_coords[0], 3), dtype=np.float32)
        self.weight_image = np.zeros(self.stitched_image.shape, dtype=np.float32)

        # Queue to hold incoming images
        self.queue = deque()

    def add_image(self, img, coords):
        self.queue.append((img, coords))
        self._process_queue()

    def _process_queue(self):
        while self.queue:
            img, coords = self.queue.popleft()
            self._place_on_canvas(img, coords)

    def _place_on_canvas(self, img, coords):
        offset_x = int(coords[0] - self.min_coords[0])
        offset_y = int(coords[1] - self.min_coords[1])

        # Calculate a feathering mask based on image intensity
        alpha = np.mean(img, axis=-1)
        alpha = gaussian_filter(alpha, sigma=10)
        alpha /= np.max(alpha)

        self.stitched_image[offset_y:offset_y+img.shape[0], offset_x:offset_x+img.shape[1]] += img * alpha[:, :, np.newaxis]
        self.weight_image[offset_y:offset_y+img.shape[0], offset_x:offset_x+img.shape[1]] += alpha[:, :, np.newaxis]

    def get_stitched_image(self):
        # Normalize by the weight image to get the final result
        stitched = self.stitched_image / np.maximum(self.weight_image, 1e-5)
        return stitched

    def save_stitched_image(self, filename):
        stitched = self.get_stitched_image()
        imsave(filename, stitched)

if __name__ == '__main__':
    # Example usage
    stitcher = ImageStitcher(min_coords=(0,0), max_coords=(400,400))

    image1 = np.random.rand(200, 200, 3)
    stitcher.add_image(image1, (0, 0))

    image2 = np.random.rand(200, 200, 3)
    stitcher.add_image(image2, (150, 50))

    import matplotlib.pyplot as plt
    plt.imshow(stitcher.get_stitched_image())
    plt.show()
    # Save the result to a file
    #stitcher.save_stitched_image('stitched_image.jpg')
    
    
