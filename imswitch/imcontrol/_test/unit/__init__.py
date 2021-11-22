from imswitch.imcontrol.model import DetectorInfo

detectorInfosBasic = {
    'CAM': DetectorInfo(
        analogChannel=None,
        digitalLine=3,
        managerName='HamamatsuManager',
        managerProperties={
            'cameraListIndex': 'mock',
            'hamamatsu': {
                'readout_speed': 3,
                'trigger_global_exposure': 5,
                'trigger_active': 2,
                'trigger_polarity': 2,
                'exposure_time': 0.01,
                'trigger_source': 1,
                'subarray_hpos': 0,
                'subarray_vpos': 0,
                'subarray_hsize': 1024,
                'subarray_vsize': 1024,
                'image_width': 1024,
                'image_height': 1024
            }
        },
        forAcquisition=True
    )
}

detectorInfosMulti = {
    'Camera 1': detectorInfosBasic['CAM'],
    'Camera 2': DetectorInfo(
        analogChannel=None,
        digitalLine=5,
        managerName='HamamatsuManager',
        managerProperties={
            'cameraListIndex': 'mock',
            'hamamatsu': {
                'readout_speed': 3,
                'trigger_global_exposure': 5,
                'trigger_active': 2,
                'trigger_polarity': 2,
                'exposure_time': 0.01,
                'trigger_source': 1,
                'subarray_hpos': 0,
                'subarray_vpos': 0,
                'subarray_hsize': 512,
                'subarray_vsize': 512,
                'image_width': 512,
                'image_height': 512
            }
        },
        forAcquisition=True
    )
}

detectorInfosNonSquare = {
    'CAM': DetectorInfo(
        analogChannel=None,
        digitalLine=3,
        managerName='HamamatsuManager',
        managerProperties={
            'cameraListIndex': 'mock',
            'hamamatsu': {
                'readout_speed': 3,
                'trigger_global_exposure': 5,
                'trigger_active': 2,
                'trigger_polarity': 2,
                'exposure_time': 0.01,
                'trigger_source': 1,
                'subarray_hpos': 0,
                'subarray_vpos': 0,
                'subarray_hsize': 1024,
                'subarray_vsize': 761,
                'image_width': 1024,
                'image_height': 761
            }
        },
        forAcquisition=True
    )
}

detectorInfoXimea = {
    'CAM' : DetectorInfo(
        analogChannel=None,
        digitalLine=3,
        managerName="XimeaManager",
        managerProperties={
            "cameraListIndex" : 0,
            "ximea" : {
                "exposure" : 100,
                "offsetX" : 0,
                "offsetY" : 0,
                "width" : 1280,
				"height" : 864,
				"trigger_source" : "XI_TRG_OFF",
				"gpi_selector" : "XI_GPI_PORT1"
            }
        },
        forAcquisition=True
    )
}


# Copyright (C) 2020, 2021 TestaLab
# This file is part of ImSwitch.
#
# ImSwitch is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ImSwitch is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
