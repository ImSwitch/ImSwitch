

from .units import SLM_UNIT, METRIC_UNIT
from imswitch.imcommon.model import Converter


class PeriodDisplacementConverter(Converter):
    canonical_unit = SLM_UNIT
    supported_units = (SLM_UNIT, METRIC_UNIT)
    types_by_unit = {
        "SLM_UNIT": int,
        "METRIC_UNIT": float
    }
    decimals_by_unit = {
        "SLM_UNIT": 0,
        "METRIC_UNIT": 3,
    }


    def __init__(self, axis:str):
        if axis not in ["x","y"]:
            raise ValueError("Axis should 'x' or 'y'")
        super().__init__(axis=axis)
    
    def to_metric(self, value, context):
        slm_calibration = context
        if value == 0:
            return 0
        
        if self.axis=="x":
            kx=1/value
            ky=0
        else:
            kx = 0
            ky = 1/value

        displacements = slm_calibration.kxy_to_um(kx,ky)

        if self.axis=="x":
            return displacements[0]
        else:
            return displacements[1]
    
    def to_slm(self, value,context):
        slm_calibration = context
        if value==0:
            return 0
        
        if self.axis=="x":
            x_um = value
            y_um = 0
        else:
            x_um = 0
            y_um = value

        kxy = slm_calibration.um_to_kxy(x_um,y_um)

        if self.axis=="x":
            return 1/kxy[0] if kxy[0]!=0 else 0
        else:
            return 1/kxy[1] if kxy[1]!=0 else 0
        
        




