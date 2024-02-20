from imswitch.imcontrol.view.widgets.basewidgets import Widget
import numpy as np
from typing import Any, Dict, List, Optional, Tuple

class dotdict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

class widgetpluginwidget(Widget):
    """Linked to CameraPluginWidget."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

'''
class CameraPlugin(DetectorManager):
    def __init__(self, detectorInfo=None, name="Test", fullShape=[100,100], supportedBinnings=[1], model=None, **kwargs):
        # Initialize any additional camera-specific setup here
        if detectorInfo is not None:
            self.detectorInfo = detectorInfo
        else:
            self.detectorInfo = {
                "name": "CameraPlugin",
                "fullShape": [100, 100],
                "supportedBinnings": [1, 2, 4],
                "model": "Test",
                "forAcquisition": True,
            }
            self.detectorInfo = dotdict(self.detectorInfo)
        super().__init__(self.detectorInfo, name, fullShape, supportedBinnings, model, **kwargs)

    def pixelSizeUm(self) -> List[int]:
        # Return the pixel size in micrometers for Z, Y, X dimensions
        return [1, 1.1, 1.1]  # Example values

    def crop(self, hpos: int, vpos: int, hsize: int, vsize: int) -> None:
        # Implement the cropping logic here
        pass

    def getLatestFrame(self) -> np.ndarray:
        # Return the latest frame captured by the camera
        # This is just a placeholder implementation
        return np.random.rand(512, 512)  # Example: return a random image

    def getChunk(self) -> np.ndarray:
        # Return a chunk of frames since the last call or flush
        # This is just a placeholder implementation
        return np.random.rand(5, 512, 512)  # Example: return a stack of 5 random images

    def flushBuffers(self) -> None:
        # Flush the internal buffers
        pass

    def startAcquisition(self) -> None:
        # Start image acquisition
        pass

    def stopAcquisition(self) -> None:
        # Stop image acquisition
        pass
'''