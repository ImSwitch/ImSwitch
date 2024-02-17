from imswitch.imcontrol.model.managers.detectors.DetectorManager import DetectorManager, DetectorAction, DetectorNumberParameter
from imswitch.imcontrol.controller.basecontrollers import ImConWidgetController
from imswitch.imcontrol.view.ImConMainView import _DockInfo

import numpy as np
from typing import Any, Dict, List, Optional, Tuple


rightDockInfos = {
            'Autofocus': _DockInfo(name='Autofocus', yPosition=0),
}


class dotdict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


class widgetplugincontroller(ImConWidgetController):
    """Linked to CameraPluginWidget."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

'''
class cameraplugin(DetectorManager):
    def __init__(self, detectorInfo=None, name="Test", **kwargs):
        # Initialize any additional camera-specific setup here
        if detectorInfo is not None:
            self.detectorInfo = detectorInfo
            model = "Test"
            fullShape = [100, 100]
            supportedBinnings = [1]
        else:
            self.detectorInfo = {
                "name": "CameraPlugin",
                "fullShape": [100, 100],
                "supportedBinnings": [1, 2, 4],
                "model": "Test",
                "forAcquisition": True,
            }
            self.detectorInfo = dotdict(self.detectorInfo)
            fullShape = self.detectorInfo.fullShape
            supportedBinnings = self.detectorInfo.supportedBinnings
            model = self.detectorInfo.model
            
        # Prepare parameters
        parameters = {
            'exposure': DetectorNumberParameter(group='Misc', value=100, valueUnits='ms',
                                                editable=True),
            'gain': DetectorNumberParameter(group='Misc', value=1, valueUnits='arb.u.',
                                            editable=True),
            'brightness': DetectorNumberParameter(group='Misc', value=1, valueUnits='arb.u.',
                                                editable=True),
        }

        # Prepare actions
        actions = {
        }
        
        super().__init__(self.detectorInfo, name, fullShape, supportedBinnings, model,
                          parameters=parameters, actions=actions, croppable=True)

    def pixelSizeUm(self) -> List[int]:
        # Return the pixel size in micrometers for Z, Y, X dimensions
        return [1, 1.1, 1.1]  # Example values

    def crop(self, hpos: int, vpos: int, hsize: int, vsize: int) -> None:
        # Implement the cropping logic here
        pass

    def getLatestFrame(self) -> np.ndarray:
        # Return the latest frame captured by the camera
        # This is just a placeholder implementation
        return np.random.rand(self.fullShape[0], self.fullShape[1])  # Example: return a random image

    def getChunk(self) -> np.ndarray:
        # Return a chunk of frames since the last call or flush
        # This is just a placeholder implementation
        return np.random.rand(5, self.fullShape[0], self.fullShape[1])  # Example: return a stack of 5 random images

    def flushBuffers(self) -> None:
        # Flush the internal buffers
        pass

    def startAcquisition(self) -> None:
        # Start image acquisition
        pass

    def stopAcquisition(self) -> None:
        # Stop image acquisition
        pass

    @property
    def pixelSizeUm(self):
        return [1, 1, 1]
'''