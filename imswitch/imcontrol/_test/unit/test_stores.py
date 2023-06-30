import os
import pytest
import numpy as np
from io import BytesIO
from imswitch.imcontrol.model.managers.storers.StorerManager import StreamingInfo, RecMode, SaveMode
from imswitch.imcontrol.model.managers.storers import ZarrStorerManager, HDF5StorerManager, TIFFStorerManager
from imswitch.imcontrol.model.managers.detectors.HamamatsuManager import HamamatsuManager
from imswitch.imcontrol._test.unit import detectorInfosBasic

@pytest.fixture()
def mock_detector():
    # TODO: make general mock detector class
    return HamamatsuManager(detectorInfosBasic["CAM"], "test_cam")

@pytest.fixture()
def mock_virtual_file():
    return BytesIO()


def test_storer_instatiation(mock_detector, mock_virtual_file):
    
    info = StreamingInfo(
        filePath="test",
        virtualFile=mock_virtual_file,
        detector=mock_detector,
        storeID = 1,
        recMode = RecMode.SpecFrames,
        saveMode = SaveMode.RAM,
        attrs = {"test": "test"},
        totalFrames = 100,
        totalTime = 1.0
    )
    
    ZarrStorerManager(info)
    TIFFStorerManager(info)
    HDF5StorerManager(info)

def test_zarr_storer(tmpdir, mock_detector):
    """Test the Zarr storer manager snap function and that the zarr store is created"""
    path = os.path.join(tmpdir, "test")
    images = {"test_channel": np.zeros((100,100))}
    attrs = {"test_channel": "test_attr"}
    detectors = {"test_channel": mock_detector}
    kwargs = dict(filePath=path, detectors=detectors, acquisitionDate="test_date")

    ZarrStorerManager.saveSnap(images, attrs, **kwargs)
    assert os.path.exists(path), "path does not exist"

def test_tiff_storer(tmpdir, mock_detector):
    """Test the TIFF storer manager snap function and that the files are created"""
    path = os.path.join(tmpdir, "test")
    images = {"test_channel": np.zeros((100,100))}
    attrs = {"test_channel": "test_attr"}
    detectors = {"test_channel": mock_detector}
    kwargs = dict(filePath=path, detectors=detectors, acquisitionDate="test_date")
    
    TIFFStorerManager.saveSnap(images, attrs, **kwargs)
    assert os.path.exists(path + "_test_channel.tiff"), "path does not exist"

def test_hdf5_storer(tmpdir, mock_detector):
    """Test the HDF5 storer manager and that the files are created"""
    path = os.path.join(tmpdir, "test")
    images = {"test_channel": np.zeros((100,100))}
    attrs = {"test_channel": "test_attr"}
    detectors = {"test_channel": mock_detector}
    kwargs = dict(filePath=path, detectors=detectors, acquisitionDate="test_date")
    
    HDF5StorerManager.saveSnap(images, attrs, **kwargs)
    assert os.path.exists(path + "_test_channel.h5"), "path does not exist"