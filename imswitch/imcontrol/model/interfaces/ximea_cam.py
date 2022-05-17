try:
    from ximea.xiapi import Camera
except ModuleNotFoundError:
    from .ximea_mock import MockXimea as Camera

class XimeaSettings:
    """Class for Ximea camera parameters.

    Args
        camera (Camera): reference to Ximea camera object.
    """

    def __init__(self, camera: Camera) -> None:

        self.camera = camera

        self.settings = [
            { # Trigger source
                "Off"          : 'XI_TRG_OFF',
                "Rising edge"  : 'XI_TRG_EDGE_RISING',
                "Falling edge" : 'XI_TRG_EDGE_FALLING',
                "High level"   : 'XI_TRG_LEVEL_HIGH',
                "Low level"    : 'XI_TRG_LEVEL_LOW',
                "Software"     : 'XI_TRG_SOFTWARE'
            },
            { # Trigger type
                "Acquisition start"        : "XI_TRG_SEL_ACQUISITION_START",
                "Frame start"              : "XI_TRG_SEL_FRAME_START",
                "Exposure active"          : "XI_TRG_SEL_EXPOSURE_ACTIVE",
                "Frame burst start"        : "XI_TRG_SEL_FRAME_BURST_START",
                "Frame burst active"       : "XI_TRG_SEL_FRAME_BURST_ACTIVE",
                "Multiple exposures"       : "XI_TRG_SEL_MULTIPLE_EXPOSURES",
                "Exposure start"           : "XI_TRG_SEL_EXPOSURE_START",
                "Multi slope phase change" : "XI_TRG_SEL_MULTI_SLOPE_PHASE_CHANGE"
            },
            { # GPI
                "GPI1"  : 'XI_GPI_PORT1',
                "GPI2"  : 'XI_GPI_PORT2',
                "GPI3"  : 'XI_GPI_PORT3',
                "GPI4"  : 'XI_GPI_PORT4',
                "GPI5"  : 'XI_GPI_PORT5',
                "GPI6"  : 'XI_GPI_PORT6',
                "GPI7"  : 'XI_GPI_PORT7',
                "GPI8"  : 'XI_GPI_PORT8',
                "GPI9"  : 'XI_GPI_PORT9',
                "GPI10" : 'XI_GPI_PORT10',
                "GPI11" : 'XI_GPI_PORT11',
                "GPI12" : 'XI_GPI_PORT12'
            },
            { # GPI mode (current selected GPI)
                "Off"     : "XI_GPI_OFF",
                "Trigger" : "XI_GPI_TRIGGER"
            },
            { # Pixel bit depth
                "16-bit gray" : "XI_MONO16", # default
                "8-bit gray"  : "XI_MONO8",
                "16-bit raw"  : "XI_RAW16",
                "8-bit raw"   : "XI_RAW8"
                # todo: add other bit depths if necessary
            }
        ]

        self.set_parameter = {
            "Exposure"       : self.camera.set_exposure_direct,
            "Trigger source" : self.camera.set_trigger_source,
            "Trigger type"   : self.camera.set_trigger_selector,
            "GPI"            : self.camera.set_gpi_selector,
            "GPI mode"       : self.camera.set_gpi_mode,
            "Bit depth"      : self.camera.set_imgdataformat
        }
