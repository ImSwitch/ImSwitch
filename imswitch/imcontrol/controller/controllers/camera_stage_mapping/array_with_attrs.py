# -*- coding: utf-8 -*-
"""
This module defines some utility classes that add the ability to bundle
metadata into a :py:class:`numpy.ndarray` in a work-a-like manner to
:py:mod:`h5py.Dataset`.  This was originally written in support of
:py:mod:`nplab` but is useful for other things too.  There's a few 
utility functions to create :py:class:`ArrayWithAttrs` objects, and also
a work-a-like class for :py:mod:`h5py.Group` that holds multiple arrays.

(c) Richard Bowman 2016, released under GNU GPL v3 or later.
"""

import numpy as np

class AttributeDict(dict):
    """This class extends a dictionary to have a "create" method.
    
    :py:mod:`h5py` objects have a property `.attrs` that is very
    close to a dictionary, for adding simple metadata.  This 
    dictionary subclass adds :py:meth:`.create` and 
    :py:meth:`.modify` methods so it has the same interface. This 
    should help compatibility with h5py attrs objects."""
    
    def create(self, name, data):
        self[name] = data
        
    def modify(self, name, data):
        self[name] = data

    def copy_arrays(self):
        """Replace any numpy.ndarray in this dict with a copy
        
        :py:class:`numpy.ndarray` objects are generally passed around, to break any unintentional links."""
        for k in list(self.keys()):
            if isinstance(self[k], np.ndarray):
                self[k] = np.copy(self[k])
        
def ensure_attribute_dict(obj, copy=False):
    """Make sure an object is an AttributeDict
    
    Given a mapping that may or not be an :py:class:`.AttributeDict`, return an
    :py:class:`.AttributeDict` object that either is, or copies the data of, the input.
    """
    if isinstance(obj, AttributeDict) and not copy:
        return obj
    else:
        out = AttributeDict(obj)
        if copy:
            out.copy_arrays()
        return out
        
def ensure_attrs(obj):
    """Make sure an object is an ArrayWithAttrs
    
    Return an :py:class:`.ArrayWithAttrs` version of an array-like object, may be the
    original object if it already has attrs."""
    if hasattr(obj, 'attrs'):
        return obj #if it has attrs, do nothing
    else:
        return ArrayWithAttrs(obj) #otherwise, wrap it
        
class ArrayWithAttrs(np.ndarray):
    """A numpy ndarray, with an AttributeDict accessible as array.attrs.

    This class is intended as a temporary version of an h5py dataset to allow
    the easy passing of metadata/attributes.  It owes
    a lot to the ``InfoArray`` example in :py:mod:`numpy` documentation on 
    subclassing :py:class:`numpy.ndarray`.

    It amounts to a trivial subclass of :py:class:`numpy.ndarray` that allows
    arbitrary metadata to be included as a dictionary.
    """
    
    def __new__(cls, input_array, attrs={}):
        """Make a new ndarray, based on an existing one, with an attrs dict.
        
        This function adds an attributes dictionary to a numpy array, to make
        it work like an h5py dataset.  It doesn't copy data if it can be 
        avoided."""
        # the input array should be a numpy array, then we cast it to this type
        obj = np.asarray(input_array).view(cls)
        # next, add the dict
        # ensure_attribute_dict always returns an AttributeDict
        obj.attrs = ensure_attribute_dict(attrs)
        # return the new object
        return obj
        
    def __array_finalize__(self, obj):
        # this is called by numpy when the object is created (__new__ may or
        # may not get called)
        if obj is None: return # if obj is None, __new__ was called - do nothing
        # if we didn't create the object with __new__,  we must add the attrs
        # dictionary.  We copy this from the source object if possible (while
        # ensuring it's the right type) or create a new, empty one if not.
        # NB we don't use ensure_attribute_dict because we want to make sure the
        # dict object is *copied* not merely referenced.
        self.attrs = ensure_attribute_dict(getattr(obj, 'attrs', {}), copy=True)

def attribute_bundler(attrs):
    """Return a function that bundles the supplied attributes with an array.
    
    This function takes a dictionary of attributes, and returns a function.
    The returned function will take a single :py:class:`numpy.ndarray` (or
    other array-like object) and return an :py:class:`.ArrayWithAttrs` 
    that bundles the attributes together with the array's data.
    """
    def bundle_attrs(array):
        return ArrayWithAttrs(array, attrs=attrs)


class DummyHDF5Group(dict):
    """A dictionary-style work-a-like for an HDF5 Group

    This is a dictionary subclass that adds `file` and `parent` attributes
    for compatibility with :class:`h5py.Group` objects.  It's intended for
    situations when a function expects an :class:`h5py.Group` but you are
    working with data in memory instead.
    """
    def __init__(self,dictionary, attrs ={}, name="DummyHDF5Group"):
        super(DummyHDF5Group, self).__init__()
        self.attrs = attrs
        for key in dictionary:
            self[key] = dictionary[key]
        self.name = name
        self.basename = name

    file = None
    parent = None