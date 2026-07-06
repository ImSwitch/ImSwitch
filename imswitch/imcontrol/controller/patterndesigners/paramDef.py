import re
from dataclasses import dataclass
from typing import Any, Optional, Sequence, Union
from .converters import Converter

Number = Union[int, float]


def clean_attr_name(label: str) -> str:
    """
    Convert a label string to a valid attribute name:
    - lowercase
    - replace spaces and parentheses with underscores
    - remove other non-alphanumeric/underscore characters
    - collapse multiple underscores into one
    """
    # Remove parentheses but keep their content
    label = label.replace("(", "").replace(")", "")

    # Remove non-alphanumeric/underscore/hyphen/space characters
    label = re.sub(r"[^0-9a-zA-Z_ \-]", "", label)

    # Replace spaces and hyphens with underscores
    label = label.replace(" ", "_")
    label = label.replace("-", "_")

    # Collapse repeated underscores
    label = re.sub(r"_+", "_", label)

    return label.lower()


def make_display_name(param_name: str) -> str:
    """
    Convert an internal attribute/key name, such as ``focal_length_mm``,
    into a user-friendly display name, such as ``Focal Length (mm)``.

    Strings that already appear formatted are returned unchanged.
    """
    units = {
        "mm",
        "um",
        "nm",
        "px",
        "degrees",
        "deg",
        "rad",
        "radians",
    }

    acronyms = {
        "fov": "FOV",
        "slm": "SLM",
        "cgh": "CGH",
        "roi": "ROI",
    }

    # Already formatted
    if (
        " " in param_name
        or "(" in param_name
        or re.search(r"[A-Z].*[A-Z]", param_name)
    ):
        return param_name

    parts = param_name.split("_")
    display_parts = []

    for part in parts:
        if not part:
            continue

        part_lower = part.lower()

        if part_lower in units:
            display_parts.append("({})".format(part_lower))
        elif part_lower in acronyms:
            display_parts.append(acronyms[part_lower])
        else:
            display_parts.append(part.capitalize())

    return " ".join(display_parts)


@dataclass(frozen=True)
class ParamDef:
    key: str
    default: Any
    ptype: type
    label: Optional[str] = None

    min_value: Optional[Number] = None
    max_value: Optional[Number] = None
    step: Optional[Number] = None

    metric_available: bool = False
    metric_label: Optional[str] = None
    converter: Optional[Converter] = None

    choices: Optional[Sequence[Any]] = None

    tooltip: Optional[str] = None
    unit: Optional[str] = None

    allow_none: bool = False
    widget: Optional[str] = None
    hidden: bool = False

    @property
    def display_label(self) -> str:
        return self.label or make_display_name(self.key)

    def validate(self, value: Any) -> Any:
        """
        Convert and validate a parameter value.

        Returns
        -------
        Any
            The value converted to ``self.ptype``.

        Raises
        ------
        ValueError
            If None is not allowed, conversion fails, or the value violates
            the declared bounds or choices.
        """
        if value is None:
            if self.allow_none:
                return None

            raise ValueError(
                "{} cannot be None".format(self.key)
            )

        try:
            converted_value = self.ptype(value)
        except (TypeError, ValueError) as error:
            raise ValueError(
                "{} must be convertible to {}, got {!r}".format(
                    self.key,
                    getattr(self.ptype, "__name__", str(self.ptype)),
                    value,
                )
            ) from error

        if (
            self.min_value is not None
            and converted_value < self.min_value
        ):
            raise ValueError(
                "{} must be >= {}, got {}".format(
                    self.key,
                    self.min_value,
                    converted_value,
                )
            )

        if (
            self.max_value is not None
            and converted_value > self.max_value
        ):
            raise ValueError(
                "{} must be <= {}, got {}".format(
                    self.key,
                    self.max_value,
                    converted_value,
                )
            )

        if (
            self.choices is not None
            and converted_value not in self.choices
        ):
            raise ValueError(
                "{} must be one of {}, got {!r}".format(
                    self.key,
                    self.choices,
                    converted_value,
                )
            )

        return converted_value
    
    def to_metric(self,value,slmCalib):
        if not self.metric_available or not self.converter:
            raise RuntimeError(f"Cannot convert parameter {self.label}")
        
        metric = self.converter.to_metric(value)
        return metric
    
    def to_slm_pixels(self,value,slmCalib):
        if not self.metric_available or not self.converter:
            raise RuntimeError(f"Cannot convert parameter {self.label}")
        
        slm_pixels = self.converter.to_slm_pixels(value)
        return slm_pixels


def param(
    key: str,
    default: Any,
    ptype: type,
    label: Optional[str] = None,
    min_value: Optional[Number] = None,
    max_value: Optional[Number] = None,
    metric_available: Optional[bool] = False,
    metric_label: Optional[str] = None,
    converter: Optional[callable] = None,
    step: Optional[Number] = None,
    choices: Optional[Sequence[Any]] = None,
    tooltip: Optional[str] = None,
    unit: Optional[str] = None,
    allow_none: bool = False,
    widget: Optional[str] = None,
    hidden: bool = False,
) -> ParamDef:
    """
    Convenience helper for creating a ParamDef.
    """
    return ParamDef(
        key=clean_attr_name(key),
        default=default,
        ptype=ptype,
        label=label,
        min_value=min_value,
        max_value=max_value,
        metric_available=metric_available,
        metric_label=metric_label,
        converter=converter,
        step=step,
        choices=choices,
        tooltip=tooltip,
        unit=unit,
        allow_none=allow_none,
        widget=widget,
        hidden=hidden,
    )


def as_param_def(definition: Any) -> ParamDef:
    """
    Convert a legacy parameter tuple into a ParamDef.

    Accepted formats
    ----------------
    ParamDef
        Returned unchanged.

    tuple
        Expected format: ``(key, default, ptype)``.
    """
    if isinstance(definition, ParamDef):
        return definition

    if isinstance(definition, tuple) and len(definition) == 3:
        key, default, ptype = definition
        return param(key, default, ptype)

    raise TypeError(
        "Expected ParamDef or (key, default, type) tuple, got {!r}".format(
            definition
        )
    )