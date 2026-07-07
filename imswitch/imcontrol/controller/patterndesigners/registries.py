from .paramDef import ParamDef, param

PATTERNS_REGISTRY = {}
ABERRATIONS_REGISTRY = {}
TARGETS_REGISTRY = {}

def normalize_param_def(value) -> ParamDef:
    if isinstance(value, ParamDef):
        return value

    # Temporary backward compatibility
    if isinstance(value, tuple) and len(value) == 3:
        key, default, ptype = value
        return param(key, default, ptype)

    raise TypeError(f"Expected ParamDef, got {value!r}")


### PATTERNS ###
def register_pattern(name, params=None, allows_metric = False, metric_param=None):
    """
    Decorator function to register a pattern and its parameters.
    Example:
        @register_pattern("binaryGrating", params=[
            ("period_x", 0, "float"),
            ("period_y", 0, "float"),
            ("duty_x", 0.5, "float"),
            ("duty_y", 0.5, "float"),
        ])
        def binary_grating(width, height, period_x, period_y,duty_x, duty_y,**kwargs):
            ... # function code
    """
    def decorator(func):
        PATTERNS_REGISTRY[name] = {
            "func": func,
            "params": [
                normalize_param_def(p) for p in (params or [])
            ],
        }
        return func
    return decorator


### ABERRATIONS ###
ABERRATION_COEFF_PARAM = param(
    "coeff",
    0.0,
    float,
    label="Coefficient",
)

def register_aberration(name, noll=None):
    """
    Function to register an aberration to ABERRATIONS_REGISTRY.
    Since Zernike polynomials are used to define aberratinos, we
    only need `name` and its `noll` index.
    Params will always be a unique coefficient for each aberration type.
    """

    ABERRATIONS_REGISTRY[name] = {
            "params": [param(name,0.0,float)],
            "noll": noll,
        }


### TARGETS ###
def register_target(
    name=None,
    *,
    params=None,
    feedback=None,
    calibration=None,
    auto_update_param=None,
):
    """
    Decorator to register a Target class.

    If arguments are omitted, values are read from class attributes:
        - target_type
        - target_params
        - _supports_feedback
        - _needs_calibration
        - _auto_update_param
    """

    def decorator(cls):
        target_name = name or getattr(cls, "target_type", None)

        if target_name is None:
            raise ValueError(
                f"{cls.__name__} must define target_type or pass a name to @register_target"
            )

        cls.target_type = target_name

        registry_params = _use_arg_or_class_value(
            params,
            getattr(cls, "target_params", []),
        )

        registry_feedback = _use_arg_or_class_value(
            feedback,
            getattr(cls, "_supports_feedback", False),
        )

        registry_calibration = _use_arg_or_class_value(
            calibration,
            getattr(cls, "_needs_calibration", False),
        )

        registry_auto_update = _use_arg_or_class_value(
            auto_update_param,
            getattr(cls, "_auto_update_param", False),
        )

        TARGETS_REGISTRY[target_name] = {
            "class": cls,
            "feedback": registry_feedback,
            "calibration": registry_calibration,
            "auto_update_param": registry_auto_update,
            "params": [
                normalize_param_def(p) for p in (registry_params or [])
            ]
        }

        return cls

    return decorator


def _use_arg_or_class_value(arg_value, class_value):
    """
    Decorator arguments default to None.
    If the user explicitly passed True or False, keep it.
    Otherwise, use the value defined on the class.
    """
    return class_value if arg_value is None else arg_value