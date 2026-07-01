# Import registries first
from .registries import PATTERNS_REGISTRY, ABERRATIONS_REGISTRY, TARGETS_REGISTRY

# Import all pattern modules so they self-register
from . import analyticalPatterns
from . import aberrationPatterns
from . import cghMultiFociTarget
from . import cghMultifociGaussTarget
from . import cghMultiFociCalibTarget
from . import cghMultiFociVectorTarget
from . import cghMultiFociVectorTarget2

from . import cghComputations
from . import slmsuiteComputations
from . import cghDirectSummation

# Import the engine last (depends on registry being populated)
from .patternEngine import PatternEngine


__all__ = [
    "PATTERNS_REGISTRY",
    "ABERRATIONS_REGISTRY",
    "TARGETS_REGISTRY",
    "PatternEngine",
]
