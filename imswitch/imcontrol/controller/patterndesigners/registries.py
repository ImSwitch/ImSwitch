from imswitch.imcommon.model.paramDef import ParamDef, param
from .schema import RESERVED_KEYS

PATTERNS_REGISTRY = {}
ABERRATIONS_REGISTRY = {}
TARGETS_REGISTRY = {}
CGH_ALGORITHMS_REGISTRY = {}


### PATTERNS ###
def register_pattern(name, params):
    """
    Decorator function to register a pattern and its parameters.
    """
    normalized_params = _normalize_and_validate_params(name,params)

    def decorator(func):
        PATTERNS_REGISTRY[name] = {
            "func": func,
            "params": normalized_params
        }
        return func
    return decorator


### ABERRATIONS ###
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
def register_target():
    """
    Decorator to register a Target class.

    Values are read from class attributes:
        - target_type
        - target_params
        - _supports_feedback
        - _needs_calibration
        - _auto_update_param
    """

    def decorator(cls):
        target_name = getattr(cls, "target_type", None)
        if target_name is None:
            raise ValueError(
                f"{cls.__name__} must define target_type."
            )
        
        feedback = getattr(cls, "_supports_feedback", False)
        calibration = getattr(cls, "_needs_calibration", False)
        auto_update = getattr(cls, "_auto_update_param", False)

        params = getattr(cls, "target_params", [])
        normalized_params = _normalize_and_validate_params(target_name,params)

        algorithm = getattr(cls, "algorithm", None)
        _validate_algorithm(target_name, algorithm)

        TARGETS_REGISTRY[target_name] = {
            "class": cls,
            "feedback": feedback,
            "calibration": calibration,
            "auto_update_param": auto_update,
            "params": normalized_params,
            "algorithm": algorithm,
        }

        return cls

    return decorator


### CGH ALGORITHMS ###
def register_cgh_algorithm(name, params=None):
    def decorator(func):
        if name in CGH_ALGORITHMS_REGISTRY:
            raise KeyError(f"CGH algorithm '{name}' is already registered")

        CGH_ALGORITHMS_REGISTRY[name] = {
            "func": func,
            "params": params or [],
        }

        return func

    return decorator



def _normalize_param_def(value) -> ParamDef:
    if isinstance(value, ParamDef):
        return value

    # Temporary backward compatibility
    if isinstance(value, tuple) and len(value) == 3:
        key, default, ptype = value
        return param(key, default, ptype)

    raise TypeError(f"Expected ParamDef, got {value!r}")



def _normalize_and_validate_params(pattern_name,params):
    
    normalized_params = [
        _normalize_param_def(pdef) for pdef in (params or [])
    ]
    # reject if forbidden keys present
    param_keys = [pdef.key for pdef in normalized_params]
    forbidden_keys = RESERVED_KEYS.intersection(param_keys)
    if forbidden_keys:
        forbidden = ", ".join(sorted(forbidden_keys))
        raise ValueError(
            f"Pattern '{pattern_name}' registers section-level parameter(s): "
            f"{forbidden}. These parameters are supplied through the "
            f"general section or slm specifications and must not be "
            f"registered as pattern parameters."
        )
    
    # reject if duplicate keys present (we could also just remove them instead,
    # but I prefer hardfail for now to ensure user registers patterns correctly)
    duplicate_keys = {
        key for key in param_keys
        if param_keys.count(key) > 1
    }
    if duplicate_keys:
        duplicates = ", ".join(sorted(duplicate_keys))

        raise ValueError(
            f"Pattern '{pattern_name}' contains duplicate parameter key(s): "
            f"{duplicates}."
        )
    
    return normalized_params


def _validate_algorithm(target_name, algorithm):
    if algorithm not in CGH_ALGORITHMS_REGISTRY:
        raise ValueError(
            f"Target '{target_name}' references unknown CGH algorithm '{algorithm}'. "
            f"Available algorithms: {sorted(CGH_ALGORITHMS_REGISTRY)}"
        )