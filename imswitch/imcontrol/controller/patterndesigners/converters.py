
from abc import ABC, abstractmethod
from .slmSectionCalibration import SLMSectionCalibration
from typing import Union

Number = Union[int, float]

class Converter(ABC):

    def __init__(self,axis:str):
        self.axis = axis

    @abstractmethod
    def to_metric(self,value: Number, calib:SLMSectionCalibration) -> Number :
        pass

    @abstractmethod
    def to_slm(self,value: Number, calib:SLMSectionCalibration)-> Number :
        pass


class ProportionalConverter(Converter):
    pass



class PeriodDisplacementConverter(Converter):

    def __init__(self, axis:str):
        if axis not in ["x","y"]:
            raise ValueError("Axis should 'x' or 'y'")
        super().__init__(axis=axis)
    
    def to_metric(self, value, calib):
        if value == 0:
            return 0
        
        if self.axis=="x":
            kx=1/value
            ky=0
        else:
            kx = 0
            ky = 1/value

        displacements = calib.kxy_to_um(kx,ky)

        if self.axis=="x":
            return displacements[0]
        else:
            return displacements[1]
    
    def to_slm(self, value,calib):
        if value==0:
            return 0
        
        if self.axis=="x":
            x_um = value
            y_um = 0
        else:
            x_um = 0
            y_um = value

        kxy = calib.um_to_kxy(x_um,y_um)

        if self.axis=="x":
            return 1/kxy[0] if kxy[0]!=0 else 0
        else:
            return 1/kxy[1] if kxy[1]!=0 else 0
        
        




