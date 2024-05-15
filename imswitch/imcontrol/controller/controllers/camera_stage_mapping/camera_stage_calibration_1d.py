"""
1D calibration of the relationship between a stage and a camera.

This module provides code that will move a microscope stage in
1D, and calibrate its step size and backlash against the camera.
The main calibration is done by :func:`.calibrate_backlash_1d`.
To perform a 2D calibration, perform 1D calibrations in two 
different (ideally orthogonal, though this is not a requirement)
directions, and then use :func:`.image_to_stage_displacement_from_1d`
to combine them.  This will yield a 2x2 transformation matrix in
the same form as :func:`.calibrate_xy_grid`.  Use two 1D 
calibrations in preference to the grid: it should be more robust
and requires less knowledge of the system thanks to its built-in
step size estimation.

Copyright Richard Bowman 2019, released under GNU GPL v3
"""
import numpy as np
import time
from numpy.linalg import norm
from typing import Optional, Callable
from .camera_stage_tracker import Tracker, move_until_motion_detected, to_tracker_history
import logging

def get_logger(logger: Optional[logging.Logger]=None) -> logging.Logger:
    """Get a logger, if the supplied one is None"""
    if logger:
        return logger
    else:
        return logging.getLogger(__name__)

def displacements(positions):
    """Calculate the absolute distance of each point from the first point."""
    return norm(positions - positions[0,:][np.newaxis,:], axis=1)

def direction_from_points(points):
    """Figure out the axis of motion from an Nx2 array of points.
    
    The return value is a normalised vector that points along the
    direction with the most motion.  This is the first *principal
    component* of the points.
    """
    points = points.astype(float)
    points -= np.mean(points, axis=0)[np.newaxis, :]
    eigenvalues, eigenvectors = np.linalg.eig(np.cov(points.T))
    return eigenvectors[:,np.argmax(eigenvalues)]

def apply_backlash(x, backlash=0, start_unwound=True):
    """Apply a basic model of backlash to a set of coordinates.

    The output (y) will lag behind the input by up to `backlash`

    `start_unwound` (default: True) assumes we change direction
    at the start of the time series, so you will get no motion
    until `x[i]` has moved by at least `2*backlash`.
    """
    y = np.zeros_like(x)
    if start_unwound:
        initial_direction = np.sign(x[1] - x[0])
        y[0] = x[0] + initial_direction * backlash
    else:
        y[0] = x[0]
    for i in range(1,len(x)):
        d = x[i] - y[i-1]
        if np.abs(d) >= backlash:
            y[i] = x[i] - np.sign(d) * backlash
        else:
            y[i] = y[i-1]
    return y

def fit_backlash(moves):
    """Given a set of linear moves forwards and back, estimate backlash.

    The result is an estimate of the amount of backlash, and the ratio
    of steps to pixels.  The moves should be a :class:`.camera_stage_tracker.TrackerHistory`
    object.

    We use a very basic fitting method: we do a brute-force search for 
    the backlash value, and for each value of backlash we fit a line to
    the relationship between stage position (after modelling backlash) 
    and image position.  We then pick the value of backlash that gets
    the lowest residuals.  Currently the backlash values tried will
    start at 0 and increase by 1 or by a factor of 1.33 each time.

    Returns
    -------
    The return value is a dictionary with the following keys:
    backlash : float
        the estimated backlash, in motor steps
    pixels_per_step : float
        the gradient of pixels to steps
    fractional_error : float
        an estimate of the goodness of fit
    stage_direction : numpy.ndarray
        unit vector in the direction of stage motion
    image_direction : numpy.ndarray
        unit vector in the direction of the motion measured
        on the camera
    pixels_per_step_vector : numpy.ndarray
        The displacement in 2D on the camera resulting from
        one step in `stage_direction`.  This is equal to the
        product of `pixels_per_step` and `image_direction`.
    """
    all_stage_points, all_image_points, times = to_tracker_history(moves)

    # Figure out the direction of motion, and reduce everything to 1D
    image_direction = direction_from_points(all_image_points)
    stage_direction = direction_from_points(all_stage_points)
    xfit = np.sum(all_stage_points * stage_direction[np.newaxis, :], axis=1)
    yfit = np.sum(all_image_points * image_direction[np.newaxis, :], axis=1)

    # We should probably use a fancy optimiser to fit the backlash, but
    # brute-forcing it is reliable and doesn't take long.
    def fit_motion(xfit, yfit, backlash=0):
        """Using the model of backlash, fit the observed camera motion"""
        xfit_blsh = apply_backlash(xfit, backlash)
        xfit_blsh -= np.mean(xfit_blsh)
        m, c = np.polyfit(xfit_blsh, yfit, 1)
        residuals = yfit - (xfit_blsh * m + c)
        return m, c, np.std(residuals, ddof=3)

    max_backlash = (np.max(xfit) - np.min(xfit))/3
    backlash_values = []
    residual_values = []
    backlash = 0
    while backlash < max_backlash:
        m, c, residual = fit_motion(xfit, yfit, backlash)
        residual_values.append(residual)
        backlash_values.append(backlash)
        backlash += max(1, backlash/3)

    backlash = backlash_values[np.argmin(residual_values)]
    m, c, residual = fit_motion(xfit, yfit, backlash)

    fractional_error = residual/norm(np.diff(yfit))
    if fractional_error > 0.1:
        raise ValueError("The fit didn't look successful")

    return {
        "backlash": backlash, 
        "pixels_per_step": m, 
        "fractional_error": fractional_error,
        "stage_direction": stage_direction,
        "image_direction": image_direction,
        "pixels_per_step_vector": m * image_direction,
    }


def calibrate_backlash_1d(
        tracker: Tracker,
        move: Callable,
        direction: np.ndarray = np.array([1,0,0]),
        return_data_on_failure: bool = False,
        logger: Optional[logging.Logger] = None,
    ):
    """Figure out reasonable step sizes for calibration, and estimate the backlash.
    
    Parameters
    ----------
    direction: 3-element ndarray
        The direction to move in (this is a 1D calibration along an arbitrary axis)
    return_data_on_failure: bool, default False
        Set this to True to suppress exceptions from fitting, and return the data even if
        the fit fails.  Useful when developing things, less helpful when using in
        production!
    """
    logger = get_logger(logger)
    logger.setLevel(logging.INFO)
    try: # Ensure that the tracker has a template set
        _ = tracker.template
    except:
        tracker.acquire_template()
    assert tracker.stage_positions.shape[0] == 1
    original_stage_pos = tracker.stage_positions[-1,:]

    direction = direction / np.sum(direction**2)**0.5 # ensure "direction" is normalised

    logger.info("Moving the stage until we see motion...")
    # Move the stage until we can see a significant amount of motion
    i, m = move_until_motion_detected(
        tracker, move, direction, threshold=tracker.max_safe_displacement * 0.2)
    
    logger.info("Moving the stage to the edge of the field of view...")
    i, m = move_until_motion_detected(
        tracker, move, direction, 
        threshold=tracker.max_safe_displacement * 0.7,
        multipliers=m/2.0 * np.arange(10),
        detect_cumulative_motion=True)
    move(original_stage_pos)
    exponential_moves = tracker.history

    # Include this final step, and make a rough estimate of the scaling from stage to image
    stage_pos, image_pos, _ = tracker.history
    stage_step = stage_pos[-1, :] - stage_pos[-1 - i, :]
    image_step = image_pos[-1, :] - image_pos[-1 - i, :]
    steps_per_pixel = norm(stage_step)/norm(image_step)
    
    # Calculate a step that moves roughly 0.2 times the max. displacement (i.e. 0.1 times the FoV)
    sensible_step = direction * tracker.max_safe_displacement * 0.1 * steps_per_pixel
    tracker.reset_history()

    logger.info("Moving the stage backwards to measure backlash (1/2)")
    # Now move backwards, in 10 steps that should roughly cross the field of view.
    # If the stage has no backlash, this will move too far, hence the break statement to
    # prevent it moving outside of the field of view.
    starting_stage_pos, starting_camera_pos = tracker.append_point()
    nBacklashDetectionSteps = 15
    for i in range(nBacklashDetectionSteps):
        move(starting_stage_pos - sensible_step * (i + 1))
        #print(".", end="")
        stage_pos, image_pos = tracker.append_point()
        print("Stage pos FWD: %s, Image pos: %s" % (stage_pos, image_pos))
        if (i > 3 and tracker.moving_away_from_centre 
            and norm(image_pos) > 0.65 * tracker.max_safe_displacement):
            break # Stop once we have moved far enough

    logger.info("Moving the stage forwards to measure backlash (2/2)")
    # Move forwards again, in 10 steps
    starting_stage_pos, starting_camera_pos = tracker.append_point()
    for i in range(nBacklashDetectionSteps):
        move(starting_stage_pos + sensible_step * (i + 1))
        #print(".", end="")
        stage_pos, image_pos = tracker.append_point()
        print("Stage pos BWD: %s, Image pos: %s" % (stage_pos, image_pos))
        if (i > 3 and tracker.moving_away_from_centre 
            and norm(image_pos) > 0.65 * tracker.max_safe_displacement):
            break # Stop once we have moved far enough
    linear_moves = tracker.history

    try:
        res = fit_backlash(linear_moves)
        backlash_correction = sensible_step / norm(sensible_step) * res["backlash"] * 1.5

        # Finally, move back to the starting position, doing backlash-corrected moves.
        logger.info("Moving back to the start, correcting for backlash...")
        tracker.reset_history()
        stage_pos, camera_pos = tracker.append_point()
        while np.dot(stage_pos - sensible_step - original_stage_pos, sensible_step) > 0:
            move(stage_pos - sensible_step - backlash_correction)
            move(stage_pos - sensible_step)
            stage_pos, camera_pos = tracker.append_point()
        backlash_corrected_moves = tracker.history
        move(original_stage_pos - backlash_correction)
    except ValueError as e:
        if return_data_on_failure:
            return {"exponential_moves": exponential_moves, "linear_moves": linear_moves,}
        raise e
    finally:
        # Reset position
        move(original_stage_pos)

    logger.info(f"Estimated backlash {res['backlash']:.0f} steps")
    logger.info(f"Stage-to-image ratio {np.abs(res['pixels_per_step']):.3f} pixels/step")
    logger.info(f"Residuals were about {res['fractional_error']:.2f} times the step size")

    res.update({
        "exponential_moves": exponential_moves,
        "linear_moves": linear_moves,
        "backlash_corrected_moves": backlash_corrected_moves
    })
    return res


def plot_1d_backlash_calibration(results):
    """Plot the results of a calibration run
    
    The input parameter should be the dictionary of calibration
    data that is output by ``calibrate_backlash_1d``.  There are
    a few type conversion functions in here (``to_tracker_history``
    and ``np.ndarray``) so that it should still work even if the
    dictionary has been converted to JSON and back (and thus the
    ``np.ndarray`` objects have been cast to lists).
    """
    from matplotlib import pyplot as plt
    f, ax = plt.subplots(1,2)
    
    for k in ["exponential", "linear", "backlash_corrected"]:
        moves = to_tracker_history(results[k+"_moves"])
        # to_tracker_history allows us to work with data that's been
        # transmitted as JSON
        if moves is not None:
            ax[0].plot(moves[1][:,0], moves[1][:,1], 'o-')
    ax[0].set_aspect(1, adjustable="datalim")

    image_direction = np.array(results["image_direction"])
    stage_direction = np.array(results["stage_direction"])

    def convert_moves(moves):
        stage_pos, image_pos, _ = to_tracker_history(moves)
        stage_1d = np.sum(stage_pos * stage_direction[np.newaxis, :], axis=1)
        image_1d = np.sum(image_pos * image_direction[np.newaxis, :], axis=1)
        return stage_1d, image_1d

    ax[1].plot(*convert_moves(results["exponential_moves"]), 'o-')
    
    stage_pos, image_pos = convert_moves(results["linear_moves"])
    model = apply_backlash(stage_pos, results["backlash"]).astype(float)
    model *= results["pixels_per_step"]
    model += np.mean(image_pos) - np.mean(model)
    ax[1].plot(stage_pos, model, '-')
    ax[1].plot(stage_pos, image_pos, 'o')
    if results["backlash_corrected_moves"] is not None:
        ax[1].plot(*convert_moves(results["backlash_corrected_moves"]), '+')

    return f, ax

def image_to_stage_displacement_from_1d(calibrations):
    """Combine X and Y calibrations

    This uses the output from :func:`.calibrate_backlash_1d`, run at least
    twice with orthogonal (or at least different) `direction` parameters.
    The resulting 2x2 transformation matrix should map from image
    to stage coordinates.  Currently, the backlash estimate given
    by this function is only really trustworthy if you've supplied
    two orthogonal calibrations - that will usually be the case.

    Returns
    -------
    dict
        A dictionary of the resulting calibration, including:

        * **image_to_stage_displacement:** (`numpy.ndarray`) - a 2x2 matrix mapping
          image displacement to stage displacement
        * **backlash_vector:** (`numpy.ndarray`) - representing the estimated
          backlash in each direction
        * **backlash:** (`number`) - the highest element of `backlash_vector`
    """
    stage_vectors = []
    image_vectors = []
    backlash = np.zeros(3)
    for cal in calibrations:
        stage_vectors.append(cal["stage_direction"][:2])
        image_vectors.append(cal["pixels_per_step_vector"])
        # our backlash estimate will be the maximum backlash
        # measured in each direction
        c_blash = np.abs(cal["backlash"] * cal["stage_direction"])
        backlash[backlash < c_blash] = c_blash[backlash < c_blash]

    A, res, rank, s = np.linalg.lstsq(image_vectors, stage_vectors) # we solve image*A = stage
    return {
        "image_to_stage_displacement": A,
        "backlash_vector": backlash,
        "backlash": np.max(backlash),
    }