#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Collection of helpers for using a PI device."""
import sys
import numbers
from collections import OrderedDict
from io import open  # Redefining built-in 'open' pylint: disable=W0622
from logging import debug

from ..pidevice.common.gcscommands_helpers import getgcsheader

# Redefining built-in 'basestring' pylint: disable=W0622
# Class name doesn't conform to PascalCase naming pylint: disable=C0103
try:
    basestring
except NameError:
    basestring = str

__signature__ = 0xbd726bf10a80782354a42b74b95f3a57


# Class inherits from object, can be safely removed from bases in python3 pylint: disable=R0205
class FrozenClass(object):  # Too few public methods pylint: disable=R0903
    """Freeze child class when self.__isfrozen is set, i.e. values of already existing properties can still
    be changed but no new properties can be added.
    """
    __isfrozen = False

    def __setattr__(self, key, value):
        if self.__isfrozen and key not in dir(self):  # don't use hasattr(), it returns False on any exception
            raise TypeError('%r is immutable, cannot add %r' % (self, key))
        object.__setattr__(self, key, value)

    def _freeze(self):
        """After this method has been called the child class denies adding new properties."""
        self.__isfrozen = True


def enum(*args, **kwargs):
    """Return an Enum object of 'args' (enumerated) and 'kwargs' that can convert the values back to its names."""
    enums = dict(list(zip(args, range(len(args)))), **kwargs)
    reverse = dict((value, key) for key, value in enums.items())
    enums['name'] = reverse
    return type('Enum', (object,), enums)


def savegcsarray(filepath, header, data):
    """Save data recorder output to a GCSArray file.
    @param filepath : Full path to target file as string.
    @param header : Header information from qDRR() as dictionary or None.
    @param data : Datarecorder data as one or two dimensional list of floats or NumPy array.
    """
    debug('save %r', filepath)
    try:
        data = data.tolist()  # convert numpy array to list
    except AttributeError:
        pass  # data already is a list
    if not isinstance(data[0], list):  # data must be multi dimensional
        data = [data]
    if header is None:
        header = OrderedDict([('VERSION', 1), ('TYPE', 1), ('SEPARATOR', 32), ('DIM', len(data)),
                              ('NDATA', len(data[0]))])
    sep = chr(header['SEPARATOR'])
    out = ''
    for key, value in header.items():
        out += '# %s = %s \n' % (key, value)
    out += '# \n# END_HEADER \n'
    for values in map(list, zip(*data)):  # transpose data
        out += sep.join(['%f' % value for value in values]) + ' \n'
    out = out[:-2] + '\n'
    piwrite(filepath, out)


def readgcsarray(filepath):
    """Read a GCSArray file and return header and data.
    @param filepath : Full path to file as string.
    @return header : Header information from qDRR() as dictionary.
    @return data : Datarecorder data as two columns list of floats.
    """
    debug('read %r', filepath)
    headerstr, datastr = [], []
    with open(filepath, 'r', encoding='utf-8', newline='\n') as fobj:
        for line in fobj:
            if line.startswith('#'):
                headerstr.append(line)
            else:
                datastr.append(line)
    header = getgcsheader('\n'.join(headerstr))
    sep = chr(header['SEPARATOR'])
    numcolumns = header['DIM']
    data = [[] for _ in range(numcolumns)]
    for line in datastr:
        if not line.strip():
            continue
        values = [float(x) for x in line.strip().split(sep)]
        for i in range(numcolumns):
            data[i].append(values[i])
    return header, data


def itemstostr(data):
    """Convert 'data' into a string message.
    @param data : Dictionary or list or tuple or single item to convert.
    """
    if data is False:
        return 'False'

    if not isinstance(data, numbers.Number):
        if not data:
            return 'None'

    msg = ''
    if isinstance(data, dict):
        for key, value in list(data.items()):
            msg += '%s: %s, ' % (key, value)
    elif isinstance(data, (list, set, tuple)):
        for value in data:
            msg += '%s, ' % value
    #    elif isinstance(data, basestring):
    #        msg = data.encode('cp1252')
    else:
        msg = str(data)
    try:
        msg = msg.rstrip(b', ')
    except TypeError:
        msg = msg.rstrip(', ')
    return msg


def piwrite(filepath, text):
    """Write 'text' to 'filepath' with preset encoding.
    @param filepath : Full path to file to write as string, existing file will be replaced.
    @param text : Text to write as string or list of strings (with trailing line feeds).
    """

    if isinstance(text, list):
        text = ''.join(text)
    with open(filepath, 'w', encoding='utf-8', newline='\n') as fobj:
        if sys.platform in ('linux', 'linux2', 'darwin'):
            try:
                fobj.write(text.decode('utf-8'))
            except UnicodeEncodeError:
                fobj.write(text)
        else:
            try:
                fobj.write(text)
            except TypeError:
                try:
                    fobj.write(text.decode('cp1252'))
                except TypeError:
                    fobj.write(text.decode('utf-8'))
