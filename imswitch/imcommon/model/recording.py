import enum

class SaveMode(enum.Enum):
    Disk = 1
    RAM = 2
    DiskAndRAM = 3
    Numpy = 4

class SaveFormat(enum.Enum):
    HDF5 = 1
    TIFF = 2
    ZARR = 3

class RecMode(enum.Enum):
    SpecFrames = 1
    SpecTime = 2
    ScanOnce = 3
    ScanLapse = 4
    UntilStop = 5