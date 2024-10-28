"""
Utility functions to track motion of a microscope using FFT-based correlation.

Cross-correlation is a reasonable way to determine where an object is in an
image.  It can also be used to track 2D motion.  The Fourier Shift Theorem
relies on the fact that a correlation (or convolution) becomes a multiplication
in the Fourier domain.  This means that Fast Fourier Transforms are an 
efficient way to implement cross-correlation of whole images.  This module
contains a number of functions to simplify tracking the motion of a microscope
stage using FFTs.

(c) Richard Bowman 2020, released under GNU GPL v3
No warranty, express or implied, is given with respect to this code.

"""
import numpy as np
import logging
from .array_with_attrs import ArrayWithAttrs


def grayscale_and_padding(image, pad=True):
    """Convert to grayscale and prepare for zero padding if needed.
    
    The FFT-based tracking methods need grayscale images.  Also, if
    we are going to zero-pad, we should convert to floating point and
    ensure the mean of the image is zero, otherwise the dominant feature
    will be the edge of the image.
    
    Returns:
        image, fft_shape
    """
    if len(image.shape) == 3:
        image = np.mean(image, axis=2)
    fft_shape = np.array(image.shape)
    if pad:
        image = image.astype(float) - np.mean(image)
        fft_shape *= 2
    return image, fft_shape

def high_pass_fourier_mask(shape, s, rfft=True):
    """Generate a mask performing a high pass filter
    
    The return value is a 2D array, which can be multiplied
    with the Fourier Transform of an image to perform a high
    pass filter.
    
    Arguments:
        shape: tuple of 2 integers
            The shape of the output array
        s: float
            The standard deviation of the Gaussian in real
            space, in pixels
    """
    high_pass_filter = np.ones(shape)
    x, y = (np.arange(n, dtype=float) for n in shape)
    # Beyond the halfway point of the array, frequencies are negative
    x[x.shape[0]//2:x.shape[0]] -= x.shape[0]
    if not rfft: # If it's a real fft, the last axis is halved so we can skip this.
        y[y.shape[0]//2:y.shape[0]] -= y.shape[0]
    x /= np.max(np.abs(x)) * 2  # Normalise so highest frequency is 1/2
    y /= np.max(np.abs(y)) * 2  # Normalise so highest frequency is 1/2
    r2 = x[:, np.newaxis]**2 + y[np.newaxis, :]**2
    # now we multiply by 1-FT(Gaussian kernel with sd of s pixels)
    high_pass_filter -= np.exp(-2*np.pi**2*s**2*r2)
    return high_pass_filter

def high_pass_fft_template(image, sigma=10, pad=True, calculate_peak=True):
    """Calculate a high-pass-filtered FT template for tracking
    
    This performs a real FFT, and then attenuates low frequencies.
    The resulting array can be used as a template for tracking.
    
    sigma is the standard deviation in pixels of the Gaussian  used
    in the high pass filter.
    
    pad enables (default) zero padding - this removes the ambiguity
    around position, at the cost of making the function slower.  We
    subtract the mean and zero-pad the input array (equivalent to 
    padding with the mean value, to reduce the impact of the edge)

    calculate computes the value of the brightest pixel we'd expect
    in a correlation image (i.e. the peak if we correlate the image
    passed in with the template we're generating).  This is stored
    in ``template.attrs["peak_correlation_value"]``
    """
    image, fft_shape = grayscale_and_padding(image, pad)
    initial_fft = np.fft.rfft2(image, s=fft_shape)  # NB rfft2 is faster, but a different shape!
    high_pass_filter = high_pass_fourier_mask(initial_fft.shape, sigma)
    if calculate_peak:
        expected_peak = np.mean(np.conj(initial_fft) * high_pass_filter * initial_fft)
        template = ArrayWithAttrs(np.conj(initial_fft) * high_pass_filter)
        template.attrs["maximum_correlation_value"] = expected_peak
        return template
    return np.conj(initial_fft) * high_pass_filter

def background_subtracted_centre_of_mass(corr, fractional_threshold=0.05, quadrant_swap=False):
    """Carry out a background subtracted centre of mass measurement
    
    Arguments:
        corr: a 2D numpy array, to be thresholded
        fractional_threshold: the fraction of the range (from 
            min(corr) to max(corr)) that should remain above 
            the background level.  1 means no thresholding, 
            0.05 means use only the top 5% of the range.
        quadrant_swap: boolean, default False
            Set this to true if we are working on the output of
            a Fourier transform.  This will adjust the coordinates
            such that we effectively perform quadrant swapping, to
            place the DC component in the centre of the image, and
            make the coordinate (0,0) correspond to that point, with
            positive and negative coordinates either side.
    """
    assert corr.dtype == float, "The image must be floating point"
    background = np.max(corr) - fractional_threshold * (np.max(corr) - np.min(corr))
    background_subtracted = corr - background
    background_subtracted[background_subtracted < 0] = 0
    xs, ys = (np.arange(n) for n in corr.shape) # This is equivalent to meshgrid, more or less...
    if quadrant_swap:
        xs[len(xs)//2:] -= len(xs)
        ys[len(ys)//2:] -= len(ys)
    x = np.sum(background_subtracted * xs[:, np.newaxis])
    y = np.sum(background_subtracted * ys[np.newaxis, :])
    I = np.sum(background_subtracted)
    return np.array([x/I, y/I])

class TrackingError(Exception):
    pass

def displacement_from_fft_template(template, image, fractional_threshold=0.1, pad=True, return_peak=False, error_threshold=0):
    """Find the displacement, in pixels, of an image from a template
    
    The template should be generated by ``high_pass_fft_template``
    Fractional_threshold is the fraction of the range (from max to min)
    of the cross-correlation image that should remain above the threshold
    before finding the peak by centre-of-mass.
    
    NB because of the periodic boundary conditions of the FFT, this gives
    a result that is ambiguous - it's only accurate modulo one image.  
    The result that is returned represents the smalles displacement,
    positive or negative.  You may add or subtract one whole image-width
    (or height) if that makes sense - use other cues to resolve the
    ambiguity.

    return_peak returns the brightes pixel in the correlation image, as
    well as the displacement in a tuple.

    error_threshold is an optional floating-point number between 0 and 1.
    Setting it to a value greater than 0 will compare the correlation value
    with the maximum possible.  If the ratio of the current signal to the
    maximum drops below ``error_threshold``, we raise a ``TrackingError``
    exception.
    """
    image, fft_shape = grayscale_and_padding(image, pad)
    # The template is already Fourier transformed and high pass filtered.
    # so multiplying the two in Fourier space performs the convolution.
    corr = np.fft.irfft2(template * np.fft.rfft2(image, s=fft_shape))
    if error_threshold > 0:
        if np.max(corr)/template.attrs["maximum_correlation_value"] < error_threshold:
            raise TrackingError("The correlation signal dropped below the threshold set.")
    displacement = background_subtracted_centre_of_mass(corr, fractional_threshold, quadrant_swap=True)
    if return_peak:
        return displacement, np.max(corr)
    return displacement

def displacement_between_images(image_0, image_1, sigma=10, fractional_threshold=0.1, pad=True):
    """Calculate the displacement, in pixels, between two images."""
    return displacement_from_fft_template(high_pass_fft_template(image_0, sigma, pad=pad), 
                                          image_1, fractional_threshold, pad=pad)
