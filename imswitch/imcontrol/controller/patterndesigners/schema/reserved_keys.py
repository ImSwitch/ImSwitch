from .section_params import GENERAL_PARAMS

# === RESERVED KEYS === #
# Those keys should not be present in any pattern registration 
# parameters, because they are already given by general section
# or SLM specifications. 

GENERAL_PARAM_KEYS = frozenset(
    pdef.key for pdef in GENERAL_PARAMS
)

SLM_SPEC_KEYS = frozenset({
    "pixel_size_um",
    "width",
    "height"
})

RESERVED_KEYS  = (
    GENERAL_PARAM_KEYS | SLM_SPEC_KEYS
)