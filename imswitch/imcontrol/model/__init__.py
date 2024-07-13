from .Options import Options
from .SetupInfo import DeviceInfo, DetectorInfo, LaserInfo, PositionerInfo, ScanInfo, SetupInfo
from .errors import *
import sys

sys.modules['visa'] = 'pyvisa'