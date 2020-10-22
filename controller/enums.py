import enum


class RecMode(enum.Enum):
    NotRecording = 0
    SpecFrames = 1
    SpecTime = 2
    ScanOnce = 3
    ScanLapse = 4
    DimLapse = 5
    UntilStop = 6
