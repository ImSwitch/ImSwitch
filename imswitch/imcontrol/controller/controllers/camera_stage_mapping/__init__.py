"""
This package provides a set of utilities that allow you to map the motion
of a microscope's stage into the coordinates of its camera.  That can 
form the basis of closed-loop control of the microscope, and simplifies
creating nice tiled images.

The main calibration routine is :py:func:`camera_stage_calibration_1d.calibrate_backlash_1d`
which operates in 1D, but can be run twice in orthogonal directions and
then combined with :py:func:`camera_stage_calibration_1d.image_to_stage_displacement_from_1d`.
The underlying cross-correlation tracking code can be configured to use
either FFT or direct correlation (FFT is recommended), and the details 
are in :py:mod:`camera_stage_mapping.fft_image_tracking` or :py:mod:`camera_stage_mapping.correlation_image_tracking`.

Most of the legwork of keeping track of stage and camera coordinates is
done by :py:class:`camera_stage_tracker.Tracker`.
"""
