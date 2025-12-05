
PATTERNS_REGISTRY = {}
ABERRATIONS_REGISTRY = {}
TARGETS_REGISTRY = {}

def register_pattern(name, params=None):
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
            "params": params or []
        }
        return func
    return decorator


def register_aberration(name, noll=None):
    """
    Function to register an aberration to ABERRATIONS_REGISTRY.
    Since Zernike polynomials are used to define aberratinos, we
    only need `name` and its `noll` index.
    Params will always be a unique coefficient for each aberration type.
    """

    ABERRATIONS_REGISTRY[name] = {
        "params": [("coeff", 0.0, float)],
        "noll": noll
    }


def register_target(name, params=None, feedback=False):
    """
    Decorator to register a Target class.
    Feedback defines if the feedback loop is available for that target.
    """
    def decorator(cls):
        TARGETS_REGISTRY[name] = {
            "class": cls,
            "feedback": feedback,
            "params": params or []
        }
        return cls
    return decorator
