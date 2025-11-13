#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tools for using the fast alignment routines of a PI device."""

from __future__ import print_function

__signature__ = 0x80192337f89d1935a8ea0f683e51c7b3

# Class inherits from object, can be safely removed from bases in python3 pylint: disable=R0205
class TargetType(object):  # Too few public methods pylint: disable=R0903
    """Enum for TargetType."""
    name = {
        0: 'Sinusoidal', 1: 'Spiral constant frequency', 2: 'Spiral constant path velocity',
    }
    sinusoidal = 0
    spiral_constant_frequency = 1
    spiral_constant_path_velocity = 2


# Class inherits from object, can be safely removed from bases in python3 pylint: disable=R0205
class EstimationMethod(object):  # Too few public methods pylint: disable=R0903
    """Enum for EstimationMethod."""
    name = {
        0: 'Maximum value', 1: 'Gaussian ls fit', 2: 'Center of gravity',
    }
    maximum_value = 0
    gaussian_ls_fit = 1
    center_of_gravity = 2


# Class inherits from object, can be safely removed from bases in python3 pylint: disable=R0205
class StopOption(object):  # Too few public methods pylint: disable=R0903
    """Enum for StopOption."""
    name = {
        0: 'Move to maximum intensity', 1: 'Stay at end of scan', 2: 'Move to start of scan', 3: 'Stop at threshold',
        4: 'Continuous until threshold',
    }
    move_to_maximum_intensity = 0
    stay_at_end_of_scan = 1
    move_to_start_of_scan = 2
    stop_at_threshold = 3
    continuous_until_threshold = 4


# Class inherits from object, can be safely removed from bases in python3 pylint: disable=R0205
class ResultID(object):  # Too few public methods pylint: disable=R0903
    """Enum for ResultID."""
    name = {
        1: 'Success', 2: 'Maximum value', 3: 'Maximum position', 4: 'Routine definition', 5: 'Scan time',
        6: 'Reason of abort', 7: 'Radius', 8: 'Number of direction changes', 9: 'Gradient length',
    }
    success = 1
    max_value = 2
    max_position = 3
    routine_definition = 4
    scan_time = 5
    reason_of_abort = 6
    radius = 7
    number_direction_changes = 8
    gradient_length = 9
