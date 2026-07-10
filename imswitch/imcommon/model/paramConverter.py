from abc import ABC
from typing import Union, Tuple

Number = Union[int, float]

class Converter(ABC):
    canonical_unit: str
    supported_units: Tuple[str, ...]
    types_by_unit = dict
    decimals_by_unit = dict

    def __init__(self,axis:str):
        self.axis = axis

    def to_unit(self, value, unit, context=None):
        self._validate_unit(unit)

        method = getattr(self, f"to_{unit}", None)
        if method is None:
            raise NotImplementedError(
                f"{type(self).__name__} must implement to_{unit}()"
            )

        return method(value, context)
    
    def type_for_unit(self, unit):
        self._validate_unit(unit)

        try:
            return self.types_by_unit[unit]
        except KeyError:
            raise ValueError(
                f"{type(self).__name__} does not define an input type "
                f"for unit '{unit}'"
            )

    def _validate_unit(self, unit):
        if unit not in self.supported_units:
            raise ValueError(
                f"{type(self).__name__} does not support unit '{unit}'. "
                f"Supported units: {self.supported_units}"
            )
