import numpy as np


#############################################################
# Conversion of angles to steps and vice versa for Rotators #
#############################################################
def angleToSteps(angle: int, stepsPerTurn: int) -> np.ndarray:
    """ Converts an angle value (0-360) to number of steps. 

    Args:
        angle (int): angle in degrees.
        stepsPerTurn (int): number of steps per turn.
    """
    steps = angle/360 * stepsPerTurn
    # solves numpy.int32' object has no attribute 'to_bytes error from telemetrix
    return int(np.floor(steps) if steps >= 0 else np.ceil(steps))


def stepsToAngle(position: int, stepsPerTurn: int) -> float:
    """ Converts a position value (defined in steps) to degrees (0-360)

    Args:
        position (int): position in steps.
        stepsPerTurn (int): number of steps per turn.
    """
    if position >= 0:
        return position * 360 / stepsPerTurn
    else:
        # second term is negative so + is correct (going counter clockwise)
        return 360 + position * 360 / stepsPerTurn
