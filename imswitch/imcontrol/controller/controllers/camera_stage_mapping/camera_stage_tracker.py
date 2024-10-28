"""
Camera-stage tracker

The :class:`.Tracker` class in this file is used to simplify code for tasks that involve moving the
stage, and tracking the corresponding motion with the camera.  It maintains a template
image, a list of previously-measured coordinates, and a coordinate offset.  The offset 
allows the coordinates to be relative to an arbitrary origin, rather than the current
template, and the :meth:``.Tracker.leapfrog`` method takes advantage of this to track motion
relative to the last point visited, while maintaining the coordinate system's zero at the
original template location.

Copyright Richard Bowman 2019, released under GNU GPL v3
"""
import numpy as np
import time
from numpy.linalg import norm
from collections import namedtuple
import logging

available_tracking_methods = []
"""A list of the tracking methods that are currently available."""
try:
    from .fft_image_tracking import high_pass_fft_template, displacement_from_fft_template, TrackingError
    available_tracking_methods.append("fft")
except:
    logging.info("camera_stage_tracker won't be able to use the `fft` method as it failed to import")
try:
    from .correlation_image_tracking import locate_feature_in_image, central_half
    available_tracking_methods.append("direct")
except:
    logging.info("camera_stage_tracker won't be able to use the `direct` method as it failed to import")
    # TODO: find a neat way to disable/enable these warnings before import?
if len(available_tracking_methods) == 0:
    raise ImportError(
        "camera_stage_tracker can't set up any tracking methods, so it will "
        "not work.  This is likely because opencv or scipy is not installed."
    )

TrackerHistory = namedtuple("TrackerHistory", ["stage_positions", "image_positions", "times"])
"""The positions (in stage and image coordinates) recorded by a Tracker.

This is a named tuple, meaning it can be unpacked like a tuple, but also accessed using attribute
syntax.  There are three elements, which are:
* **stage_positions:** (`ndarray`) - An Nx3 array of stage coordinates for each point
* **image_positions:** (`ndarray`) - An Nx2 array of image coordinates for each point
* **times:** (`ndarray`) - A 1D array of times for each point.
"""

def to_tracker_history(dict_or_tuple):
    """Convert a dict or tuple to a TrackerHistory object"""
    if isinstance(dict_or_tuple, TrackerHistory):
        return dict_or_tuple
    # Times was added later, so may be missing if we talk to something out of date.
    if "times" in dict_or_tuple:
        times = np.array(dict_or_tuple["times"])
    elif len(dict_or_tuple) == 3:
        times = np.array(dict_or_tuple[2])
    else:
        logging.warn("The 'time' component was missing from tracker history - you may have out-of-date data")
        times = None
    try:
        return TrackerHistory(
            np.array(dict_or_tuple["stage_positions"]), 
            np.array(dict_or_tuple["image_positions"]),
            times,
        )
    except TypeError:
        return TrackerHistory(
            np.array(dict_or_tuple[0]),
            np.array(dict_or_tuple[1]),
            times,
        )


# FFT based tracking functions moved to fft_image_tracking.py

class Tracker():
    """A class to manage moving the stage and following motion in the image
    
    This class takes care of:
        1. Using image analysis to track the displacement between points
        2. Keeping track of the recovered positions, and the corresponding
            stage positions

    It can use a variety of different tracking methods (detailed in the
    constructor).

        
    We accept functions because that seems like the easiest way to be
    compatible with many different cameras/stages.  Subclass and override
    ``__init__`` if you want to use a particular object instead.

    # Subclassing notes
    If you change the tracking method, you should override:
    * track_image
    * generate_template
    * max_displacement
    * min_displacement (optional - defaults to -max_displacment)

    NB the ``image_position`` that this class returns may be the negative of 
    what you might expect.  This is because normally we are looking for 
    where a certain object (usually matched to a template image) is within
    an image.  Instead, the ``Tracker`` is following motion of the image
    relative to a template.  Our model is that we have a static image on
    the slide, so we're tracking the slide's motion.
    """
    def __init__(self, grab_image, get_position, settle=None, method="fft", **kwargs):
        """Construct a Tracker object to follow our position using the camera.

        The :class:`.Tracker` class keeps track of our position using image
        analysis, and records corresponding stage positions.  

        Arguments
        ---------
        grab_image : function
            A function that returns an image as a :class:`~numpy.ndarray`
        grab_image : function
            A function that returns the stage position as a :class:`~numpy.ndarray`
        settle : function
            A function called before grabbing an image to ensure the image is
            fresh (most often, this waits a short time, or grabs and discards
            a frame from the camera).
        method : ["fft", "direct"], optional
            The tracking method to use (see below)
        
        Additional keyword arguments are passed to the tracking method.

        Tracking methods:
            * **"direct":** uses cross-correlation with the central half of the image.  
                There are currently no options for this method.
            * **"fft":** uses FFT-based cross-correlation, after a high pass filter.  
                Keyword arguments are accepted:
                    * **pad:** (`boolean`, default=`True`) -
                        Whether to zero-pad the FFT to remove ambiguity.  If 
                        false, the answer is only unique modulo one field of
                        view due to the periodic nature of FFTs.  Setting this
                        option to False speeds up tracking by about 4x.
                    * **sigma:** (`float`, default=`10`) -
                        The standard deviation, in pixels, of a Gaussian filter
                        used to smooth the image, before subtracting the smooth
                        image from the original, in a low pass filter.  NB the
                        standard deviation is given in pixels, but is applied
                        in the Fourier domain (with appropriate transformation).
                        The value of sigma does not affect computation speed.
            NB the "direct" method depends on `opencv` and `scipy` and so it
            may fail to load.  Specifying "direct" will lead to an exception
            if this is the case; these are optional dependencies.  To see
            which methods are available, look at `available_tracking_methods`.
        """
        self._grab_image = grab_image
        self._get_position = get_position
        self._settle = settle
        self._template = None
        self.margin = np.array([0, 0])
        self._template_position = np.array([0.0, 0.0])
        self._last_point = None
        self.image_shape = None
        self.method = method
        #self.kwargs = {"error_threshold": 0.2}.update(kwargs)
        self.kwargs = kwargs
    
    def get_position(self):
        """Get the position of the stage
        
        Returns
        -------
        ndarray
        """
        return np.array(self._get_position())
    
    def settle(self):
        """Wait a short time and discard an image so the stage is no longer wobbling.
        
        If no settling function is provided, by default we will wait 0.3 seconds, and
        acquire then discard one frame.
        """
        if self._settle is not None:
            self._settle()
        else:
            time.sleep(0.3)
            self._grab_image()
            
    @property
    def template(self):
        """ndarray: The template image"""
        if self._template is None:
            raise ValueError("Attempt to use the tracker before setting the template")
        else:
            return self._template
        
    @template.setter
    def template(self, new_value):
        self._template = new_value
        
    def acquire_template(self, settle=True, reset_history=True, relative_positions=True):
        """Take a new image, and use it as the template.  NB this records the initial point.
        
        We will wait for the stage to settle, then acquire a new image to use as the template.
        Immediately afterwards, we record the first point, so we will acquire a second image
        and also read the stage's position.

        The template image will be the central 50% of the starting image, which means the 
        maximum displacement will be 0.25 fields-of-view in all directions.
        
        Arguments
        ---------
        settle : bool, optional
            Whether to wait for the stage to settle before taking the template image, defaults
            to True
        reset_history : bool, optional
            Whether to erase all the previously-stored positions, defaults to True
        """
        if settle:
            self.settle()
        image = self._grab_image()
        self.template = self.generate_template(image)
        self.image_shape = image.shape
        if reset_history:
            self.reset_history()
        self._template_position = np.array([0., 0.])
        self.append_point(settle=False)

    def leapfrog(self):
        """Replace the template but don't change position.

        By default, this will replace the template with the image from the last
        point we measured, but update ``self._template_position`` so that the coordinates
        returned don't change.
        """
        if self._last_point is None:
            raise ValueError("Can't leapfrog until you have measured at least one point.")
        image, image_pos = self._last_point
        self.template = self.generate_template(image)
        if np.any(self.image_shape != image.shape):
            raise ValueError("Error: the image size seems to have changed!")
        # We assume that our correlation method returns (0,0) if the current image
        # is the same as the template image we acquired, so by setting
        # `_template_position` to the current position, we update the template
        # image but stay in the same coordinate system.
        self._template_position = np.array(image_pos)

    def generate_template(self, image):
        """Generate a template based on a supplied image.

        This function is designed to be overridden in order to
        change the tracking method.

        Arguments
        ---------
        image : ndarray
            An image from which to generate the template
        """
        if self.method == "direct":
            return central_half(image)
        if self.method == "fft":
            kwargs = {k: v for k, v in self.kwargs.items() if k in ["pad", "sigma"]}
            return high_pass_fft_template(image, calculate_peak=True, **kwargs)

        
    @property
    def max_displacement(self):
        """ndarray: The highest position values that can be tracked"""
        if self.method == "direct":
            # TODO: if template_position is not central, should we alter this??
            disp = (np.array(self.image_shape[:2]) - np.array(self.template.shape)[:2]) // 2
        if self.method == "fft":
            # FFT tracking does a real FFT to track the position, which is half as long in
            # the last dimension.  If we didn't zero pad, the transform will have the same shape as
            # the image in x, and half in y - so we return half the image size.  If we are zero
            # padding, then both these dimensions double, and we return the image size.
            disp = np.array(self.template.shape) // np.array([2,1])
        return disp + self._template_position
    
    @property
    def min_displacement(self):
        """ndarray: The lowest position values that can be tracked"""
        return self._template_position - self.max_displacement 
        # TODO: be cleverer about tracking assymetry? Currently there is none...
    
    @property
    def max_safe_displacement(self):
        """ndarray: The biggest displacement we can safely attempt to track without knowing direction."""
        return np.min(np.concatenate([self.max_displacement - self._template_position, 
                                     -self.min_displacement - self._template_position]))

    def point_in_safe_range(self, point):
        """Determine if a given point is within the safe range of the tracker.
        
        Arguments
        ---------
        point : ndarray
            A two-element array representing a point
            
        Returns
        -------
        bool
        """
        return np.all(point > self.min_displacement) and np.all(point < self.max_displacement)
            
    def track_image(self, image):
        """Find the position of the image relative to the template
        
        This uses the method specified at initialisation time to
        track motion of the sample.
        
        NB this class is intended to track motion of the sample - most of
        the time, we're interested in the motion of a (small) object that
        is represented by the template, relative to the (larger) image. In
        our case, we're doing the opposite - tracking motion of the image,
        relative to a picture of part of the sample.  That's why there is
        a minus sign in front of `locate_feature_in_image` in the source
        code.
        """
        if self.method=="direct":
            return -locate_feature_in_image(image, self.template, relative_to="centre") + self._template_position
        if self.method=="fft":
            kwargs = {k: v for k, v in self.kwargs.items() if k in ["pad", "fractional_threshold", "error_threshold"]}
            return -displacement_from_fft_template(self.template, image, **kwargs) + self._template_position
    
    def append_point(self, settle=True, image=None):
        """Find the current position using both stage and image, and remember it
        
        Arguments
        ---------
        settle : bool, optional
            Set to ``False`` to disable running the settling function.  Defaults to ``True``.
        image : ndimage, optional
            Supply an image to track position based on that image.  Defaults to acquiring a
            new image.

        Returns
        -------
        stage_pos : ndarray
            The current position as reported by the stage
        image_pos : ndarray
            The displacement in pixels from the initial position
        """
        if settle:
            self.settle()
        if image is None:
            image = self._grab_image()
        image_pos = self.track_image(image)
        stage_pos = self.get_position()
        self._image_positions.append(image_pos)
        self._stage_positions.append(stage_pos)
        self._times.append(time.time())
        self._last_point = (image, image_pos)
        return stage_pos, image_pos
        
    @property
    def stage_positions(self):
        """ndarray: An array of positions we have moved the stage to"""
        return np.array(self._stage_positions)
    
    @property
    def image_positions(self):
        """ndarray: An array of positions we have moved the stage to"""
        return np.array(self._image_positions)

    @property
    def times(self):
        """ndarray: An array of time values for each position"""
        return np.array(self._times)
    
    @property
    def history(self):
        """TrackerHistory: Return the stage and image positions and times."""
        return TrackerHistory(self.stage_positions, self.image_positions, self.times)
    
    def reset_history(self, leave_first_point=False):
        """Reset the positions and displacements recorded.
        
        This resets the position, displacement, and time arrays to be empty.
        
        Arguments
        ---------
        leave_first_point : bool, optional
            Set this to ``True`` to leave the first point.
        """
        if leave_first_point:
            self._stage_positions = [self._stage_positions[0]]
            self._image_positions = [self._image_positions[0]]
            self._times = [self._times[0]]
        else:
            self._stage_positions = []
            self._image_positions = []
            self._times = []

    @property
    def moving_away_from_centre(self):
        """Whether we are moving away from [0,0] on the camera.

        If we have recorded more than two steps, this property will be
        `True` if the most recent point in the history is farther away from
        `[0,0]` than the second most recent point.  If we have recorded fewer
        than 2 points, this property returns None.
        """
        if len(self.image_positions) < 2:
            return None
        else:
            return norm(self.image_positions[-1,:]) > norm(self.image_positions[-2])
    
   
def move_until_motion_detected(tracker, move, displacement, threshold=10, multipliers=2**np.arange(16), detect_cumulative_motion=False):
    """Move the stage until we can detect motion in the camera.
    
    We move the stage in the direction given by ``displacement`` until the 
    image has shifted by at least ``threshold`` pixels.  The steps will be
    given by ``multipliers``, i.e. each time we move to 
    ``displacement * multipliers[i]`` relative to the starting position.
    
    NB we expect that the ``tracker`` object has already been initialised
    with ``acquire_template``.

    ``detect_cumulative_motion`` will use the first point in the tracker as
    the point to detect displacement relative to, rather than the last point.
    The displacements are always made relative to the last point in the tracker
    as it is passed in (i.e. the stage is always moved relative to where it
    currently is, but motion detection may be done relative to where the tracker
    was initialised).  This only matters if the tracker has more than one point
    in its history.

    The return value `i, m` is the number of moves made, and the largest 
    multiplier value that was used, i.e. we moved by a total of 
    `displacement * m`.
    """
    displacement = np.array(displacement)
    starting_image_position = tracker.image_positions[0 if detect_cumulative_motion else -1, :]
    starting_stage_position = tracker.stage_positions[-1, :]
    for i, m in enumerate(multipliers):
        move(starting_stage_position + displacement * m)
        tracker.append_point()
        print("Intended pos: %s, Stage Pos: %s,  Image Position: %s" % (starting_stage_position + displacement * m, tracker.get_position(), tracker.image_positions[-1, :]))
        if norm(tracker.image_positions[-1, :] - starting_image_position) >= threshold:
            return i + 1, m
    raise Exception("Moved the stage by {} but saw no motion.".format(multipliers[-1] * displacement))

def concatenate_tracker_histories(histories):
    """Combine a number of separate tracker history entries into one
    
    A "tracker history" refers to the output of `Tracker.history`, as
    a :class:`.TrackerHistory` object. 
    Given an array of such tuples, we will concatenate the components,
    returning a single "tracker history" with the segments concatenated.

    Arguments
    ---------
    histories : array of TrackerHistory

    Returns
    -------
    TrackerHistory
    """
    components = zip(*histories)
    return TrackerHistory(np.concatenate(c, axis=1) for c in components)
