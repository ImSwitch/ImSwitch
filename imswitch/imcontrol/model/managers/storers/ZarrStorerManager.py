import numpy as np
from zarr import group
from zarr.storage import DirectoryStore
from ome_zarr.writer import write_multiscales_metadata
from ome_zarr.format import format_from_version
from typing import Dict, List
from imswitch.imcommon.model import initLogger
from imswitch.imcontrol.model.managers.detectors.DetectorManager import DetectorManager
from imswitch.imcontrol.model.managers.storers.StorerManager import RecMode, SaveMode
from .StorerManager import (
    StorerManager, 
    RecMode, 
    SaveMode
)

class ZarrStorerManager(StorerManager):
    """ A Zarr data streaming manager. See `StorerManager` for details on the interface.
    """

    @classmethod
    def saveSnap(self, images: Dict[str, np.ndarray], attrs: Dict[str, str], **kwargs) -> None:
            logger = initLogger(self)
            filePath = kwargs["filePath"]
            datasets: List[dict] = []
            store = DirectoryStore(filePath)
            root = group(store=store)

            for channel, image in images.items():
                detector = kwargs["detectors"][channel]
                shape = detector.shape
                dtype = detector.dtype
                root.create_dataset(channel, 
                                data=image, 
                                shape=tuple(reversed(shape)), 
                                chunks=(512, 512), 
                                dtype=dtype
                            ) #TODO: why not dynamic chunking?

                datasets.append({"path": channel, "transformation": None})
            write_multiscales_metadata(root, datasets, format_from_version("0.2"), shape, **attrs)
            logger.info(f"Saved image to zarr file {filePath}")
    
    def stream(self, recMode: RecMode, saveMode: SaveMode, attrs: Dict[str, str], **kwargs) -> None:
        # TODO: implement streaming
        raise NotImplementedError("Zarr streaming not implemented yet.")
