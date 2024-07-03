"""
Perform a 2D calibration of stage to camera coordinates.

This module uses 2D motion to try to calibrate the relationship between 
a camera and a stage, by moving the stage in a grid and then fitting a
2x2 transformation matrix that maps stage coordinates to camera 
coordinates.  It works, but is not as robust as performing two 1D 
calibrations and then combining them; see 
:func:`.calibrate_backlash_1d` and 
:func:`.image_to_stage_displacement_from_1d`.

The main calibration routine in this module is 
:func:`.calibrate_xy_grid`.


Copyright Richard Bowman 2019, released under GNU GPL v3
"""
import numpy as np
import time
from numpy.linalg import norm
from .camera_stage_tracker import Tracker, move_until_motion_detected

from functools import partial

def backlash_corrected_move(get_position, move, backlash_amount, pos):
    """Make two moves, arriving at `pos` moving in the positive direction
    
    We first calculate the relative displacement and then look at the 
    sign of each component.  For each axis where the displacement is
    negative, we deliberately overshoot the destination point, then
    make a second move that approaches the destination from the right
    direction.

    Arguments:
        get_position: function
            A function that returns an array representing position

        move: function
            a function that performs an absolute move to a given position
            (position is specified as an array)

        backlash_amount: number
            A number, specifying the distance to move for 
            backlash correction (should be greater than the backlash)

        pos: array-like
            the absolute position to which we want to move.
    """
    displacement = pos - get_position()
    backlash_vector = (displacement < 0).astype(np.int)*backlash_amount
    if np.any(backlash_vector > 0):
        move(pos - backlash_vector)
    move(pos)

def bake_backlash_corrected_move(get_position, move, backlash_amount):
    """Return a function that performs backlash-corrected moves
    
    Given `get_position` and `move` functions, and a backlash-correction
    distance, return a function that takes only the destination position
    as argument, and performs a :func:`backlash_corrected_move`.
    """
    return partial(backlash_corrected_move, get_position, move, backlash_amount)
    
def calibrate_xy_grid(tracker, move, step = 100, n_steps=4, backlash_compensation=0):
    """Make a series of moves in X and Y to determine the XY components of the pixel-to-sample matrix.

    The stage will be raster-scanned in a grid, with `step` steps between each point, and `n_steps`
    points along each axis.  The measured camera coordinates will be compared to the stage coordinates,
    and a 2x2 affine transformation matrix will be fitted to map one coordinate system to another.

    Arguments
    ---------
    tracker : Tracker
        An initialised :class:`.Tracker`, centred on the starting point.  This provides position readout from the stage and the camera.
    move : function
        A function that accepts a 1D array and performs an absolute move to 
        that position.  If backlash correction is needed, include it here.
    step : float, optional
        The amount to move the stage by.  This should move the sample by approximately 1/10th of the field of view.
        Defaults to 100 steps.
    n_steps : int, optional
        The number of steps to make in each direction.  NB the number of points in the grid is this number squared. Defaults to 4, i.e. 16 points.
    backlash_compensation : number, optional
        If this is non-zero, we will make backlash-corrected moves as we move around the grid. Defaults to zero.

    Returns
    -------
    dict
        The results are returned as a dictionary, with the following keys:
        * **image_to_stage_displacement:** (`ndarray`) - The transformation matrix
        * **moves:** (:class:`.TrackerHistory`) - all the raw positions
        * **fractional_error:** (`float`) - ratio of the mean squared error to the mean squared move
    """
    try: # Ensure that the tracker has a template set
        _ = tracker.template
    except:
        tracker.acquire_template()
    tracker.reset_history() # make sure we get rid of the initial (0,0) point
    starting_position = tracker.get_position()
    # Move the stage in a square, recording the displacement from both the stage and the camera
    try:
        for x in (np.arange(n_steps) - n_steps/2.0)*step:
            for y in (np.arange(n_steps) - n_steps/2.0)*step:
                move(starting_position + np.array([x, y, 0]))
                tracker.append_point()
    finally:
        move(starting_position)
    # We then use least-squares to fit the XY part of the matrix relating 
    # pixels to distance
    # stage_positions should be the stage positions, with a zero mean.
    # image_positions should be the same, but calculated from the images
    stage_positions, image_positions, _ = tracker.history
    stage_positions = stage_positions.astype(float)
    stage_positions -= np.mean(stage_positions, axis=0)
    stage_positions = stage_positions[:,:2] # ensure it's 2d
    image_positions -= np.mean(image_positions, axis=0)
    #image_positions *= -1 # To get the matrix right, we want the position of each
                        # image relative to the template, rather than the other way around
    A, res, rank, s = np.linalg.lstsq(image_positions, stage_positions) # we solve pixel_shifts*A = location_shifts

    transformed_image_positions = np.dot(image_positions, A)
    residuals = transformed_image_positions - stage_positions
    fractional_error = norm(residuals) / stage_positions.shape[0] / step
    print(f"Ratio of residuals to displacement is {fractional_error})")
    if fractional_error > 0.05: # Check it was a reasonably good fit
        print("Warning: the error fitting measured displacements was %.1f%%" % (fractional_error*100))
    print(f"Calibrated the pixel-location matrix.\nResiduals were {fractional_error*100:.1f}% of the shift.")
    
    return {
        "image_to_stage_displacement": A, 
        "moves": tracker.history, 
        "fractional_error": fractional_error
    }

