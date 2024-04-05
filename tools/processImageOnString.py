import numpy as np
import cv2

class ImageProcessor:
    def getProcessedImages(self, path="Default.tif", pythonFunctionString="", context=None):
        
        ''' Example:
        functionString = """
        def processImage(image):
            # Example processing: Convert to grayscale
            return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        """
        '''
        image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        #image = cv2.imread(path, cv2.IMREAD_UNCHANGED)

        # Step 2: Load and Execute Python Function from String
        if pythonFunctionString:
            # Define a default processImage function in case exec fails
            def processImage(image):
                return image

            # Execute the function string
            exec(pythonFunctionString, globals(), locals())

            # Step 3: Process the Image
            processedImage = locals()['processImage'](image)

            # Step 4: Return Processed Image
            return processedImage
        else:
            return image

# Example usage
processor = ImageProcessor()
functionString = """
def processImage(image):
    # Example processing: Convert to grayscale
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
"""
processed_image = processor.getProcessedImages(path="path_to_image.tif", pythonFunctionString=functionString)
