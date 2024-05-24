"""
Closed loop move

This module defines some functions that allow you to make closed-loop moves.  
This is done using the ``Tracker`` object defined in ``camera_stage_tracker``
to keep track of where we are.  The idea is that we make a move, then check
where we *actually* moved to, then make another move to correct the first
move.  This is particularly useful if you are using a stage that isn't
mechanically repeatable, or that suffers from backlash.

The methods included in this module are not yet particularly clever, so
if you specify a very small tolerance and you have a stage with backlash,
it may not converge in a sensible time.  This is something that might get
improved in the long term, but isn't currently a priority.

Copyright Richard Bowman 2019, released under GNU General Public License v3
"""
import numpy as np
from numpy.linalg import norm
import logging
from .camera_stage_tracker import TrackingError

def closed_loop_move(tracker, move_in_pixels, pos, tolerance=5, max_iterations=3):
    """Move by a specified distance in pixels
    
    This will make a move, then refine with subsequent moves
    based on the position reported by the ``Tracker`` object.
    
    Arguments:
        tracker: ``Tracker``
            A ``Tracker`` object, already initialised, used to measure
            the move we have actually made.  Our goal is to have the
            tracker report that we have moved to ``pos``.
        move_in_pixels: function
            A function that accepts a 2-element numpy array as input, 
            and makes a relative move by that many pixels.
        pos: np.array
            A 2-element array with the desired position in pixels
        tolerance: int (optional, default 5)
            Once we are within this many pixels of ``pos``, we will
            stop and consider the move successful.
        max_iterations: int (optional, default 3)
            This is the maximum number of refinement steps that will
            be made, i.e. after the initial move, we will be allowed
            this many extra moves to get closer to ``pos``
    
        Returns:
            image_pos: 2-element numpy array, with the actual position in pixels
    """
    pos = np.array(pos)
    if not tracker.point_in_safe_range(pos):
        raise ValueError("closed_loop_move can only move by the maximum distance we can track.")
                  
    move_in_pixels(pos - tracker.image_positions[-1]) # Initial (open loop) move
    iterations = 0
    _, image_pos = tracker.append_point()
    while norm(image_pos - pos) > tolerance and iterations < max_iterations:
        move_in_pixels(pos - image_pos)
        stage_pos, image_pos = tracker.append_point()
        iterations += 1
        if iterations > max_iterations:
            logging.warn(f"Closed loop move did not converge in {max_iterations} iterations.")
            break
    return image_pos


def closed_loop_scan(tracker, move_in_pixels, move, relative_image_positions, **kwargs):
    """Visit a list of positions then return to the start.

    This function moves to each of the positions given (in an N-by-2 ``ndarray``)
    and will yield the index of the position and the actual position at each point.
    The positions are specified relative to the starting point, and we will return
    to the starting point at the end of the scan.

    Arguments:
        tracker: ``Tracker``
            A ``Tracker`` object, already initialised, used to measure
            the move we have actually made.  Our goal is to have the
            tracker report that we have moved to ``pos``.
        move_in_pixels: function
            A function that accepts a 2-element numpy array as input, 
            and makes a relative move by that many pixels.
        move: function
            Takes a 3-element numpy array and moves to that absolute position
        relative_image_positions: np.array
            A 2-element array with the desired position in pixels
        Additional keyword arguments are passed to closed_loop_move

    Yields:
        i, position
    """
    initial_position = tracker.get_position()
    actual_positions = []
    try:
        for i, position in enumerate(relative_image_positions):
            actual_position = closed_loop_move(tracker, move_in_pixels, position, **kwargs)
            logging.info(f"Closed loop scan ({i}/{relative_image_positions.shape[0]}): target position {position}, actual position {actual_position}, diff {actual_position - position}")
            tracker.leapfrog()
            actual_positions.append(actual_position)
            yield i, actual_position
    except TrackingError as e:
        logging.error("Aborted closed-loop scan because of a tracking error.")
    finally:
        move(initial_position)
        return actual_positions