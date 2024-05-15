# !pip install -e . /Users/bene/Dropbox/Dokumente/Promotion/PROJECTS/MicronController/PYTHON/camera-stage-mapping
from imswitch.imcontrol.controller.controllers.camera_stage_mapping.camera_stage_calibration_1d import calibrate_backlash_1d, image_to_stage_displacement_from_1d
from imswitch.imcontrol.controller.controllers.camera_stage_mapping.camera_stage_tracker import Tracker
from imswitch.imcontrol.controller.controllers.camera_stage_mapping.closed_loop_move import closed_loop_move, closed_loop_scan
from imswitch.imcontrol.controller.controllers.camera_stage_mapping.scan_coords_times import ordered_spiral
import logging
import time
import numpy as np
from collections import namedtuple
import os 
import json
MoveHistory = namedtuple("MoveHistory", ["times", "stage_positions"])

# ONLY FOR TESTING/DEBUGGING:
SIGN_AXES = {"X":1, "Y":1, "Z":1}
STAGE_ORDER = ["X", "Y", "Z"]
# %%
class LoggingMoveWrapper():
    """Wrap a move function, and maintain a log position/time.

    This class is callable, so it doesn't change the signature
    of the function it wraps - it just makes it possible to get
    a list of all the moves we've made, and how long they took.

    Said list is intended to be useful for calibrating the stage
    so we can estimate how long moves will take.
    """
    def __init__(self, move_function, current_position=None):
        self._move_function = move_function
        self._current_position = current_position
        self.clear_history()

    def __call__(self, new_position, *args, **kwargs):
        """Move to a new position, and record it"""
        self._history.append((time.time(), self._current_position))
        self._move_function(new_position, *args, **kwargs)
        self._current_position = new_position
        self._history.append((time.time(), self._current_position))

    @property
    def history(self):
        """The history, as a numpy array of times and another of positions"""
        times = np.array([t for t, p in self._history])
        positions = np.array([p for t, p in self._history])
        return MoveHistory(times, positions)

    def clear_history(self):
        """Reset our history to be an empty list"""
        self._history = []


class OFMStageScanClass(object):
    """
    Use the camera as an encoder, so we can relate camera and stage coordinates
    """

    def __init__(self, client=None, calibration_file_path="UC2StageCalib.json", effPixelsize=1.0, stageStepSize=1.0, IS_CLIENT=False, mDetector=None, mStage=None):
        # client is either the HTTP client of ImSwitch or the parent class
        self._is_client = IS_CLIENT
        self._client = client
        self._logger = logging.getLogger(__name__)
        # set logging level
        self._logger.setLevel(logging.INFO)
        # everything is measured in normalized pixel coordinates
        # so if we want to move the stage by one pixel we need to know the effective pixel size
        # and the stage step size
        
        self._effPixelsize = effPixelsize
        self._stageStepSize = stageStepSize # given in microns 
        self._micronToPixel = self._effPixelsize/self._stageStepSize
        self._stageOrder = STAGE_ORDER
        self._calibration_file_path = calibration_file_path
        
        # get hold on detector and stage 
        self.microscopeDetector = mDetector
        self.microscopeStage = mStage

        
    def camera_stage_functions(self):
        """Return functions that allow us to interface with the microscope"""
        
        def grabCroppedFrame(crop_size=512):
            if self._is_client:
                marray = self._client.recordingManager.snapNumpyToFastAPI()
            else:
                marray = self.microscopeDetector.getLatestFrame()
            #marray = self._client.detector.getLatestFrame()
            center_x, center_y = marray.shape[1] // 2, marray.shape[0] // 2

            # Calculate the starting and ending indices for cropping
            x_start = center_x - crop_size // 2
            x_end = x_start + crop_size
            y_start = center_y - crop_size // 2
            y_end = y_start + crop_size

            # Crop the center region
            return marray[y_start:y_end, x_start:x_end]

        def getPositionList():
            if self._is_client:
                positioner_names = self._client.positionersManager.getAllDeviceNames()
                positioner_name = positioner_names[0]
                posDict = self._client.positionersManager.getPositionerPositions()[positioner_name]
            else:
                posDict = self.microscopeStage.getPosition()
            return (SIGN_AXES[STAGE_ORDER[0]]*posDict["X"]/self._micronToPixel, SIGN_AXES[STAGE_ORDER[1]]*posDict["Y"]/self._micronToPixel, SIGN_AXES[STAGE_ORDER[2]]*posDict["Z"]/self._micronToPixel)

        def movePosition(posList):
            
            if self._is_client:
                positioner_names = self._client.positionersManager.getAllDeviceNames()
                positioner_name = positioner_names[0]
                self._client.positionersManager.movePositioner(positioner_name, dist=SIGN_AXES[STAGE_ORDER[0]]*posList[0]*self._micronToPixel, axis=self._stageOrder[0], is_absolute=True, is_blocking=True)
                time.sleep(.1)
                self._client.positionersManager.movePositioner(positioner_name, dist=SIGN_AXES[STAGE_ORDER[1]]*posList[1]*self._micronToPixel, axis=self._stageOrder[1], is_absolute=True, is_blocking=True)
            else:                
                self.microscopeStage.move(value=SIGN_AXES[STAGE_ORDER[0]]*posList[0]*self._micronToPixel, axis=self._stageOrder[0], is_absolute=True, is_blocking=True)
                self.microscopeStage.move(value=SIGN_AXES[STAGE_ORDER[1]]*posList[1]*self._micronToPixel, axis=self._stageOrder[1], is_absolute=True, is_blocking=True)
            
            if len(posList)>2:
                if self._is_client:
                    self._client.positionersManager.movePositioner(positioner_name, dist=SIGN_AXES[STAGE_ORDER[2]]*posList[2]*self._micronToPixel, axis=self._stageOrder[2], is_absolute=True, is_blocking=True)
                else:
                    self.microscopeStage.move(value=SIGN_AXES[STAGE_ORDER[2]]*posList[2]*self._micronToPixel, axis=self._stageOrder[2], is_absolute=True, is_blocking=True)

        def settle(tWait=.1):
            time.sleep(tWait)
        grab_image = grabCroppedFrame
        get_position = getPositionList
        move = movePosition
        wait = settle

        return grab_image, get_position, move, wait

    def calibrate_1d(self, direction, return_backlash_data=False, nMultipliers=5):
        """Move a microscope's stage in 1D, and figure out the relationship with the camera"""
        grab_image, get_position, move, wait = self.camera_stage_functions()
        move(np.zeros(3))  # move to the origin
        #mAxis = self._stageOrder[np.where(direction != 0)[0][0]]
        #nAxis = np.where(direction != 0)[0][0]
        current_position = get_position()
        move = LoggingMoveWrapper(move,current_position)  # log positions and times for stage calibration

        tracker = Tracker(grab_image, get_position, settle=wait)

        result = calibrate_backlash_1d(tracker, move, direction)#, return_backlash_data=return_backlash_data, nMultipliers=nMultipliers)
        result["move_history"] = move.history
        return result
    


    def calibrate_xy(self, return_backlash_data=False):
        """Move the microscope's stage in X and Y, to calibrate its relationship to the camera"""
        try: 
            self._logger.info("Calibrating X axis:")
            cal_x = self.calibrate_1d(np.array([1, 0, 0]), return_backlash_data=return_backlash_data)
            self._logger.info("Calibrating Y axis:")
            cal_y = self.calibrate_1d(np.array([0, 1, 0]), return_backlash_data=return_backlash_data)
        except Exception as e:
            self._logger.error("Calibration failed. Try reordering the stage axes. Error: %s", e)
            self._stageOrder[0], self._stageOrder[1] = self._stageOrder[1], self._stageOrder[0]
            self._logger.info("Calibrating X axis:")
            cal_x = self.calibrate_1d(np.array([1, 0, 0]), return_backlash_data=return_backlash_data)
            self._logger.info("Calibrating Y axis:")
            cal_y = self.calibrate_1d(np.array([0, 1, 0]), return_backlash_data=return_backlash_data)
        cal_x["stage_axis"] = self._stageOrder[0]
        cal_y["stage_axis"] = self._stageOrder[1]
        
        # Combine X and Y calibrations to make a 2D calibration
        cal_xy = image_to_stage_displacement_from_1d([cal_x, cal_y])
        
        data = {
            "camera_stage_mapping_calibration": cal_xy,
            "linear_calibration_"+cal_x["stage_axis"]: cal_x,
            "linear_calibration_"+cal_y["stage_axis"]: cal_y,
        }
        CSM_DATAFILE_PATH = os.path.join("./", self._calibration_file_path)

        # Custom JSON encoder for NumPy arrays
        class NumpyEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, np.ndarray):
                    return obj.tolist()  # Convert NumPy arrays to lists
                return super(NumpyEncoder, self).default(obj)

        # Convert NumPy arrays to lists and save the JSON file with the custom encoder
        with open(CSM_DATAFILE_PATH, 'w') as json_file:
            json.dump(data, json_file, indent=4, sort_keys=True, cls=NumpyEncoder)
            
        
        
        return data

    @property
    def image_to_stage_displacement_matrix(self):
        """A 2x2 matrix that converts displacement in image coordinates to stage coordinates."""
        try:
            settings = self.get_settings()
            return settings["image_to_stage_displacement"]
        except KeyError:
            raise ValueError("The microscope has not yet been calibrated.")

    def move_in_image_coordinates(self, displacement_in_pixels):
        """Move by a given number of pixels on the camera"""
        p = np.array(displacement_in_pixels)
        relative_move = np.dot(p, self.image_to_stage_displacement_matrix)
        self.microscope.stage.move_rel([relative_move[0], relative_move[1], 0])

    def closed_loop_move_in_image_coordinates(self, displacement_in_pixels, **kwargs):
        """Move by a given number of pixels on the camera, using the camera as an encoder."""
        grab_image, get_position, move, wait = self.camera_stage_functions()

        tracker = Tracker(grab_image, get_position, settle=wait)
        tracker.acquire_template()
        closed_loop_move(tracker, self.move_in_image_coordinates, displacement_in_pixels, **kwargs)

    def closed_loop_scan(self, scan_path, **kwargs):
        """Perform closed-loop moves to each point defined in scan_path.

        This returns a generator, which will move the stage to each point in
        ``scan_path``, then yield ``i, pos`` where ``i``
        is the index of the scan point, and ``pos`` is the estimated position
        in pixels relative to the starting point.  To use it properly, you
        should iterate over it, for example::

            for i, pos in csm_extension.closed_loop_scan(scan_path):
                capture_image(f"image_{i}.jpg")

        ``scan_path`` should be an Nx2 numpy array defining
        the points to visit in pixels relative to the current position.

        If an exception occurs during the scan, we automatically return to the
        starting point.  Keyword arguments are passed to
        ``closed_loop_move.closed_loop_scan``.
        """
        grab_image, get_position, move, wait = self.camera_stage_functions()

        tracker = Tracker(grab_image, get_position, settle=wait)
        tracker.acquire_template()

        return closed_loop_scan(tracker, self.move_in_image_coordinates, move, np.array(scan_path), **kwargs)


    def test_closed_loop_spiral_scan(self, step_size, N, **kwargs):
        """Move the microscope in a spiral scan, and return the positions."""
        scan_path = ordered_spiral(0,0, N, *step_size)

        for i, pos in self.closed_loop_scan(np.array(scan_path), **kwargs):
            pass

