"""
Utility functions to track motion of a microscope using FFT-based correlation.

Cross-correlation is a reasonable way to determine where an object is in an
image.  It can also be used to track 2D motion.  ``locate_feature_in_image``
uses cross correlation followed by background-subracted centre of mass to
find the location of a template with respect to an image.

This code is faster than the FFT-based code if you have a good idea of 
where the target is, and if the target is much smaller than the image, i.e. 
if the search area is small.  If you are correlating whole images against 
each other, the FFT method is likely faster.

(c) Richard Bowman 2020, released under GNU GPL v3
No warranty, express or implied, is given with respect to this code.

"""

import numpy as np
import cv2
from scipy import ndimage

def central_half(image):
    """Return the central 50% (in X and Y) of an image"""
    w, h = image.shape[:2]
    return image[int(w/4):int(3*w/4),int(h/4):int(3*h/4), ...]


def datum_pixel(image):
    """Get the datum pixel of an image - if no property is present, assume the central pixel."""
    try:
        return np.array(image.datum_pixel)
    except:
        return (np.array(image.shape[:2]) - 1) / 2.

########## Cross-correlation based tracking ############
def locate_feature_in_image(image, feature, margin=0, restrict=False, relative_to="top left"):
    """Find the given feature (small image) and return the position of its datum (or centre) in the image's pixels.

    image : numpy.array
        The image in which to look.
    feature : numpy.array
        The feature to look for.  Ideally should be an `ImageWithLocation`.
    margin : int (optional)
        Make sure the feature image is at least this much smaller than the big image.  NB this will take account of the
        image datum points - if the datum points are superimposed, there must be at least margin pixels on each side of
        the feature image.
    restrict : bool (optional, default False)
        If set to true, restrict the search area to a square of (margin * 2 + 1) pixels centred on the pixel that most
        closely overlaps the datum points of the two images.
    relative_to : string (optional, default "top left")
        We return the position of the centre (or datum pixel, if it's got that metadata) of the feature, relative to
        either the top left (i.e. 0,0) pixel in the image, or the central pixel - to do the latter, set ``relative_to``
        to "centre" (or "center" if you must).

    The `image` must be larger than `feature` by a margin big enough to produce a meaningful search area.  We use the
    OpenCV `matchTemplate` method to find the feature.  The returned position is the position, relative to the corner of
    the first image, of the "datum pixel" of the feature image.  If no datum pixel is specified, we assume it's the
    centre of the image.  The output of this function can be passed into the pixel_to_location() method of the larger
    image to yield the position in the sample of the feature you're looking for.
    """
    # The line below is superfluous if we keep the datum-aware code below it.
    assert image.shape[0] > feature.shape[0] and image.shape[1] > feature.shape[1], "Image must be larger than feature!"
    # Check that there's enough space around the feature image
    lower_margin = datum_pixel(image) - datum_pixel(feature)
    upper_margin = (image.shape[:2] - datum_pixel(image)) - (feature.shape[:2] - datum_pixel(feature))
    assert np.all(np.array([lower_margin, upper_margin]) >= margin), "The feature image is too large."
    #TODO: sensible auto-crop of the template if it's too large?
    image_shift = np.array((0,0))
    if restrict:
        # if requested, crop the larger image so that our search area is (2*margin + 1) square.
        image_shift = np.array(lower_margin - margin,dtype = int)
        image = image[image_shift[0]:image_shift[0] + feature.shape[0] + 2 * margin + 1,
                      image_shift[1]:image_shift[1] + feature.shape[1] + 2 * margin + 1, ...]

    corr = cv2.matchTemplate(image, feature,
                             cv2.TM_SQDIFF_NORMED)  # correlate them: NB the match position is the MINIMUM
    corr = -corr # invert the image so we can find a peak
    corr += (corr.max() - corr.min()) * 0.1 - corr.max()  # background-subtract 90% of maximum
    corr = cv2.threshold(corr, 0, 0, cv2.THRESH_TOZERO)[
        1]  # zero out any negative pixels - but there should always be > 0 nonzero pixels
    assert np.sum(corr) > 0, "Error: the correlation image doesn't have any nonzero pixels."
    peak = ndimage.measurements.center_of_mass(corr)  # take the centroid (NB this is of grayscale values, not binary)
    pos = np.array(peak) + image_shift + datum_pixel(feature) # return the position of the feature's datum point.
    if relative_to in ["top left", None]:
        return pos
    if relative_to in ["centre", "center"]:
        return pos - (np.array(image.shape[:2]) - 1)/2.
    raise ValueError("An invalid value was specified for datum.")
    