from dataclasses import dataclass
import os
import pytest
from imswitch.imcontrol.model.managers.RecordingManager import ZarrStorer, HDF5Storer, TiffStorer
from imswitch.imcontrol.model.managers.DetectorsManager import DetectorsManager
import numpy as np
import zarr


@dataclass
class MockDetectorsManager():
    shape: tuple
    pixelSizeUm: float
    

@pytest.fixture()
def fake_manager():
    return MockDetectorsManager(shape=(100,100), pixelSizeUm=12)

def test_storer_instatiation(fake_manager):
    ZarrStorer("test",fake_manager)
    TiffStorer("test",fake_manager)
    HDF5Storer("test",fake_manager)

def test_zarr_storer(tmpdir, fake_manager):
    """Test that the zarr storer can be instantiated and that the zarr store is created"""
    path = os.path.join(tmpdir, "test")
    storer = ZarrStorer(path, {"test_channel": fake_manager})
    storer.snap({"test_channel": np.zeros((100,100))}, {"test_channel": "test"})
    assert os.path.exists(path+".zarr"), "path does not exist"


def test_tiff_storer(tmpdir, fake_manager):
    """Test that the tiff storer can be instantiated and that the files are created"""
    path = os.path.join(tmpdir, "test")
    storer = TiffStorer(path, {"test_channel": fake_manager})
    storer.snap({"test_channel": np.zeros((100,100))}, {"test_channel": "test"})
    assert os.path.exists(path + "_test_channel.tiff"), "path does not exist"


def test_hdf5_storer(tmpdir, fake_manager):
    """Test that the HDF5 storer can be instantiated and that the files are created"""
    path = os.path.join(tmpdir, "test")
    storer = HDF5Storer(path, {"test_channel": fake_manager})
    storer.snap({"test_channel": np.zeros((100,100))}, {"test_channel": {"test": 3}})
    assert os.path.exists(path + "_test_channel.h5"), "path does not exist"