import numpy as np

def angleToSteps(angle: int, stepsPerTurn: int) -> np.ndarray:
    """ Converts an angle value (0-360) to number of steps. 
    
    Args:
        angle (int): angle in degrees.
        stepsPerTurn (int): number of steps per turn.
    """
    steps = angle/360 * stepsPerTurn
    return (np.floor(steps) if steps >= 0 else np.ceil(steps)).astype(int)

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