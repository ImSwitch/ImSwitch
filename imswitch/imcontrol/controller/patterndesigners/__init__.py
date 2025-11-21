# Import registries first
from .registries import PATTERNS_REGISTRY, ABERRATIONS_REGISTRY

# Import all pattern modules so they self-register
from . import analyticalPatterns
from . import aberrationPatterns
from . import cghPatterns

# Import the engine last (depends on registry being populated)
from .patternEngine import PatternEngine


__all__ = [
    "PATTERNS_REGISTRY",
    "ABERRATIONS_REGISTRY",
    "PatternEngine",
]
