from dataclasses import dataclass
from ximea.xidefs import *

@dataclass(frozen=True)
class XimeaSettings:
    """Dataclass for Ximea camera parameters.
    """

    trigger_source = [
        'XI_TRG_OFF',
        'XI_TRG_EDGE_RISING',
        'XI_TRG_EDGE_FALLING',
        'XI_TRG_LEVEL_HIGH',
        'XI_TRG_LEVEL_LOW',
        'XI_TRG_SOFTWARE'
    ]

    trigger_selector = [
        "XI_TRG_SEL_FRAME_START",
        "XI_TRG_SEL_EXPOSURE_ACTIVE",
        "XI_TRG_SEL_FRAME_BURST_START",
        "XI_TRG_SEL_FRAME_BURST_ACTIVE",
        "XI_TRG_SEL_MULTIPLE_EXPOSURES",
        "XI_TRG_SEL_EXPOSURE_START",
        "XI_TRG_SEL_MULTI_SLOPE_PHASE_CHANGE",
        "XI_TRG_SEL_ACQUISITION_START",
    ]

    gpi_selector = [
        'XI_GPI_PORT1',
        'XI_GPI_PORT2',
        'XI_GPI_PORT3',
        'XI_GPI_PORT4',
        'XI_GPI_PORT5',
        'XI_GPI_PORT6',
        'XI_GPI_PORT7',
        'XI_GPI_PORT8',
        'XI_GPI_PORT9',
        'XI_GPI_PORT10',
        'XI_GPI_PORT11',
        'XI_GPI_PORT12'
    ]

    gpi_mode = [
        'XI_GPI_OFF',
        'XI_GPI_TRIGGER'
    ]
