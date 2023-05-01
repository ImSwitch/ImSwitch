#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tools for setting up and using the data recorder of a PI device."""

from __future__ import print_function
from logging import debug, warning
from time import sleep, time

from ..common.gcscommands_helpers import isdeviceavailable
from .gcs2commands import GCS2Commands
from ...datarectools.datarectools import RecordOptions, TriggerSources

__signature__ = 0x3b0ab4873500566649e57d75f4431a22

# seconds
SERVOTIMES = {
    'C-663.11': 50E-6,
    'C-663.12': 50E-6,
    'C-702.00': 100E-6,
    'C-843': 410E-6,
    'C-863.11': 50E-6,
    'C-863.12': 50E-6,
    'C-867.160': 50E-6,  # verified
    'C-867.260': 50E-6,  # verified
    'C-867.262': 50E-6,  # verified
    'C-867.B0017': 100E-6,
    'C-867.B0019': 100E-6,
    'C-867.B024': 100E-6,
    'C-867.OE': 50E-6,
    'C-877': 100E-6,
    'C-880': 4096E-6,
    'C-884.4D': 50E-6,
    'C-884.4DB': 50E-6,
    'C-887': 100E-6,
    'E-710': 200E-6,
    'E-755': 200E-6,
    'E-861': 50E-6,
    'E-861.11C885': 50E-6,
    'E-871.1A1': 50E-6,
    'E-871.1A1N': 50E-6,
    'E-873': 50E-6,
    'E-873.1A1': 50E-6,
    'E-873.3QTU': 50E-6,
    'E-873.10C885': 50E-6,
}

MAXNUMVALUES = {
    'C-663.10C885': 1024,
    'C-663.11': 1024,
    'C-663.12': 1024,
    'C-702.00': 262144,
    'C-863.11': 1024,
    'C-863.12': 1024,
    'C-867.160': 8192,  # verified
    'C-867.1U': 8192,  # verified
    'C-867.260': 8192,  # verified
    'C-867.262': 8192,  # verified
    'C-867.2U': 8192,  # verified
    'C-867.2U2': 8192,  # verified
    'C-867.B0017': 8192,
    'C-867.B0019': 8192,
    'C-867.B024': 8192,
    'C-867.OE': 1024,
    'C-877': 1024,
    'C-877.1U11': 1024,  # verified
    'C-877.2U12': 1024,  # verified
    'C-884.4D': 8192,
    'C-884.4DB': 8192,
    'E-761': 8192,
    'E-861': 1024,
    'E-861.11C885': 1024,
    'E-871.1A1': 1024,
    'E-871.1A1N': 1024,
    'E-873': 1024,
    'E-873.1A1': 1024,
    'E-873.3QTU': 8192,
    'E-873.10C885': 8192,
}

PI_HDR_ADDITIONAL_INFO_NOT_AVAILABLE = 'No additional info available'


def getservotime(gcs, usepreset=True):
    """Return current servo cycle time in seconds as float.
    @type gcs : pipython.gcscommands.GCSCommands
    @param usepreset : If True, use SERVOTIMES preset if controller could not provide the value.
    @return : Current servo cycle time in seconds as float.
    """
    if not isdeviceavailable([GCS2Commands], gcs):
        raise TypeError('Type %s of gcs is not supported!' % type(gcs).__name__)

    servotime = None
    if gcs.devname in ['C-702.00']:
        servotime = SERVOTIMES[gcs.devname]
    if servotime is None:
        servotime = gcs.getparam(0x0E000200)  # SERVO_UPDATE_TIME
    if servotime is None and usepreset:
        if gcs.devname in SERVOTIMES:
            servotime = SERVOTIMES[gcs.devname]
    if servotime is None:
        raise NotImplementedError('servo cycle time for %r is unknown' % gcs.devname)
    return float(servotime)


# Too many nested blocks (6/5) pylint: disable=R1702
# Too many branches (18/12) pylint: disable=R0912
# 'getmaxnumvalues' is too complex. The McCabe rating is 21 pylint: disable=R1260
def getmaxnumvalues(gcs, usepreset=True, hdr_additional_info=None):
    """Return maximum possible number of data recorder values as integer.
    @type gcs : pipython.gcscommands.GCSCommands
    @param usepreset : If True, use MAXNUMVALUES preset if controller could not provide the value.
    @param hdr_additional_info : List with the lines of the additional infomation section of the 'HDR?' answer.
                                 if 'hdr_additional_info' is an empty list or 'None'.
                                 'HDR?' is called and the list is filled
                                 if 'hdr_additional_info' is not an empty list, the content of the list is returned.
    @return : Maximum possible number of data recorder values as integer.
    """
    if not isdeviceavailable([GCS2Commands], gcs):
        raise TypeError('Type %s of gcs is not supported!' % type(gcs).__name__)

    if hdr_additional_info is None:
        hdr_additional_info = []

    # getparam() can return string if param id is not available in qHPA answer
    maxnumvalues = None
    if gcs.devname in ['C-702.00']:
        maxnumvalues = MAXNUMVALUES[gcs.devname]
    if not maxnumvalues:
        # E-517, E-518, E-852
        maxnumvalues = gcs.getparam(0x16000201)  # DATA REC SET POINTS
    if not maxnumvalues:
        # E-709, E-712, E-725, E-753.1CD, E-727, E-723K001
        maxpoints = gcs.getparam(0x16000200)  # DATA_REC_MAX_POINTS
        numtables = gcs.getparam(0x16000300)  # DATA_REC_CHAN_NUMBER
        if maxpoints and numtables:
            maxnumvalues = int(int(maxpoints) / int(numtables))
    if not maxnumvalues:
        # C-843
        maxpoints = gcs.getparam(0x16000200)  # DATA_REC_MAX_POINTS
        if maxpoints:
            maxnumvalues = int(int(maxpoints) / gcs.qTNR())
    if not maxnumvalues:
        # Mercury, etc.
        maxnumvalues = gcs.getparam(0x16000001)  # RECORDCYCLES_PER_TRIGGER
    if not maxnumvalues:
        _recopts, _trigopts = [], []
        if not hdr_additional_info:
            if gcs.HasqHDR():
                _recopts, _trigopts, hdr_additional_info = get_hdr_options(gcs, return_additional_info=True)
        if hdr_additional_info:
            for info in hdr_additional_info:
                if info.find('datapoints per table') != -1:
                    try:
                        maxnumvalues = int(info.split()[0])
                    except ValueError:
                        pass
    if not maxnumvalues and usepreset:
        if gcs.devname in MAXNUMVALUES:
            maxnumvalues = MAXNUMVALUES[gcs.devname]
    if not maxnumvalues:
        raise NotImplementedError('maximum number of data recorder values for %r is unknown' % gcs.devname)
    return int(maxnumvalues)


# Too many instance attributes pylint: disable=R0902
# Too many public methods pylint: disable=R0904
# Class inherits from object, can be safely removed from bases in python3 pylint: disable=R0205
class Datarecorder(object):
    """Set up and use the data recorder of a PI device."""

    def __init__(self, gcs):
        """Set up and use the data recorder of a PI device connected via 'gcs'.
        @type gcs : pipython.gcscommands.GCSCommands
        """
        debug('create an instance of Datarecorder(gcs=%s)', gcs)

        if not isdeviceavailable([GCS2Commands], gcs):
            raise TypeError('Type %s of gcs is not supported!' % type(gcs).__name__)

        self._gcs = gcs
        self._cfg = {
            'servotime': None,
            'numvalues': None,
            'offset': None,
            'maxnumvalues': None,
            'samplerate': None,
            'sources': None,
            'options': None,
            'trigsources': None,
            'rectables': [],
        }
        self._header = None
        self._data = None
        self._recopts = []
        self._trigopts = []
        self._additional_info = []

    @property
    def recopts(self):
        """Return supported record options as list of integers."""
        if not self._recopts:
            self._get_hdr_options()
        return self._recopts

    @property
    def trigopts(self):
        """Return supported trigger options as list of integers."""
        if not self._trigopts:
            self._get_hdr_options()
        return self._trigopts

    @property
    def additional_info(self):
        """Return supported trigger options as list of integers."""
        if not self._additional_info:
            self._get_hdr_options()
        return self._additional_info

    def _get_hdr_options(self):
        """Call qHDR comamnd and set self._recopts and self._trigopts accordingly."""
        self._recopts, self._trigopts, self._additional_info = get_hdr_options(self._gcs, return_additional_info=True)

        # There is not always an additional information available in 'HDR?'.
        if not self._additional_info:
            self._additional_info.append(PI_HDR_ADDITIONAL_INFO_NOT_AVAILABLE)

    @property
    def gcs(self):
        """Access to GCS commands of controller."""
        return self._gcs

    @property
    def servotime(self):
        """Return current servo cycle time in seconds as float.
        @rtype: float
        """
        if self._cfg['servotime'] is None:
            self._cfg['servotime'] = getservotime(self._gcs)
            debug('Datarecorder.servotime is %g secs', self._cfg['servotime'])
        return self._cfg['servotime']

    @servotime.setter
    def servotime(self, value):
        """Set current servo cycle time in seconds as float."""
        value = float(value)
        self._cfg['servotime'] = value
        debug('Datarecorder.servotime set to %g secs', self._cfg['servotime'])

    @property
    def numvalues(self):
        """Return number of data recorder values to record as integer.
        @rtype: int
        """
        if self._cfg['numvalues'] is None:
            self.numvalues = self.maxnumvalues
        return self._cfg['numvalues']

    @numvalues.setter
    def numvalues(self, value):
        """Set number of data recorder values to record to 'value' as integer."""
        value = int(value)
        if value > self.maxnumvalues:
            raise ValueError('%d exceeds the maximum number of data recorder values %d' % int(value, self.maxnumvalues))
        self._cfg['numvalues'] = value
        debug('Datarecorder.numvalues: set to %d', self._cfg['numvalues'])

    @property
    def offset(self):
        """Return start point in the record table as integer, starts with index 1.
        @rtype: int
        """
        if self._cfg['offset'] is None:
            if self.numvalues:
                return 1
        return self._cfg['offset']

    @offset.setter
    def offset(self, value):
        """Set start point in the record table as integer, starts with index 1."""
        value = int(value)
        self._cfg['offset'] = value
        debug('Datarecorder.offset: set to %d', self._cfg['offset'])

    @property
    def maxnumvalues(self):
        """Return maximum possible number of data recorder values as integer.
        @rtype: int
        """
        if self._cfg['maxnumvalues'] is None:
            self._cfg['maxnumvalues'] = getmaxnumvalues(self._gcs, hdr_additional_info=self._additional_info)
            debug('Datarecorder.maxnumvalues is %d', self._cfg['maxnumvalues'])
        return self._cfg['maxnumvalues']

    @maxnumvalues.setter
    def maxnumvalues(self, value):
        """Set maximum possible number of data recorder values as integer."""
        value = int(value)
        self._cfg['maxnumvalues'] = value
        debug('Datarecorder.maxnumvalues: set to %d', self._cfg['maxnumvalues'])

    @property
    def samplerate(self):
        """Return current sampling rate in multiples of servo cycle time as integer.
        @rtype: int
        """
        if self._cfg['samplerate'] is None:
            if self._gcs.HasqRTR():
                self._cfg['samplerate'] = self._gcs.qRTR()
            else:
                warning('device %r does not support the RTR? command', self._gcs.devname)
                self._cfg['samplerate'] = 1
        return self._cfg['samplerate']

    @samplerate.setter
    def samplerate(self, value):
        """Set current sampling rate to 'value' in multiples of servo cycle time as integer.
        @rtype: int
        """
        value = max(1, int(value))
        if self._gcs.HasRTR():
            self._gcs.RTR(value)
            self._cfg['samplerate'] = value
        else:
            warning('device %r does not support the RTR command', self._gcs.devname)
            self._cfg['samplerate'] = 1
        debug('Datarecorder.samplerate: set to %d servo cycles', self._cfg['samplerate'])

    @property
    def sampletime(self):
        """Return current sampling time in seconds as float.
        @rtype: float
        """
        return self.samplerate * self.servotime

    @sampletime.setter
    def sampletime(self, value):
        """Set current sampling time to 'value' in seconds as float."""
        self.samplerate = int(float(value) / self.servotime)
        debug('Datarecorder.sampletime: set to %g s', self.sampletime)

    @property
    def samplefreq(self):
        """Return current sampling frequency in Hz as float.
        @rtype: float
        """
        return 1. / self.sampletime

    @samplefreq.setter
    def samplefreq(self, value):
        """Set current sampling frequency to 'value' in Hz as float.
        @rtype: float
        """
        self.sampletime = 1. / float(value)
        debug('Datarecorder.samplefreq: set to %.2f Hz', self.samplefreq)

    @property
    def rectime(self):
        """Return complete record time in seconds as float.
        @rtype: float
        """
        return self.numvalues * self.sampletime

    @rectime.setter
    def rectime(self, value):
        """Set number of values to record according to 'value' as complete record time in seconds as float.
        @rtype: float
        """
        self.numvalues = float(value) / self.sampletime
        debug('Datarecorder.frequency: set to %.2f Hz', self.samplefreq)

    @property
    def rectimemax(self):
        """Return complete record time in seconds as float.
        @rtype: float
        """
        return self.maxnumvalues * self.sampletime

    @rectimemax.setter
    def rectimemax(self, value):
        """Set sample time to record for 'value' seconds (float) with max. number of points."""
        self.numvalues = self.maxnumvalues
        self.sampletime = float(value) / self.numvalues
        debug('Datarecorder.rectimemax: %d values with sampling %g s', self.numvalues, self.sampletime)

    @property
    def sources(self):
        """Return current record source IDs as list of strings, defaults to first axis."""
        self._cfg['sources'] = self._cfg['sources'] or self._gcs.axes[0]
        if isinstance(self._cfg['sources'], (list, set, tuple)):
            return self._cfg['sources']
        return [self._cfg['sources']] * len(self.rectables)

    @sources.setter
    def sources(self, value):
        """Set record source IDs as string convertible or list of them."""
        self._cfg['sources'] = value
        debug('Datarecorder.sources: set to %r', self._cfg['sources'])

    @sources.deleter
    def sources(self):
        """Reset record source IDs."""
        self._cfg['sources'] = None
        debug('Datarecorder.sources: reset')

    @property
    def options(self):
        """Return current record source IDs as list of integers, defaults to RecordOptions.ACTUAL_POSITION_2."""
        self._cfg['options'] = self._cfg['options'] or RecordOptions.ACTUAL_POSITION_2
        if isinstance(self._cfg['options'], (list, set, tuple)):
            return self._cfg['options']
        return [self._cfg['options']] * len(self.rectables)

    @options.setter
    def options(self, value):
        """Set record source IDs as integer convertible or list of them."""
        self._cfg['options'] = value
        debug('Datarecorder.options: set to %r', self._cfg['options'])

    @options.deleter
    def options(self):
        """Reset record source IDs."""
        self._cfg['options'] = None
        debug('Datarecorder.options: reset')

    @property
    def trigsources(self):
        """Return current trigger source as int or list, defaults to TriggerSources.NEXT_COMMAND_WITH_RESET_2."""
        self._cfg['trigsources'] = self._cfg['trigsources'] or TriggerSources.NEXT_COMMAND_WITH_RESET_2
        return self._cfg['trigsources']

    @trigsources.setter
    def trigsources(self, value):
        """Set trigger source IDs. If single integer then "DRT 0" is used. If list
        of integers then list size can be 1 or must match the length of self.rectables.
        """
        if isinstance(value, tuple):
            value = list(value)
        self._cfg['trigsources'] = value
        debug('Datarecorder.trigsources: set to %r', self._cfg['trigsources'])

    @trigsources.deleter
    def trigsources(self):
        """Reset trigger source IDs."""
        self._cfg['trigsources'] = None
        debug('Datarecorder.trigsources: reset')

    @property
    def rectables(self):
        """Return the record tables as list of integers."""
        if isinstance(self._cfg['sources'], (list, set, tuple)):
            numtables = len(self._cfg['sources'])
        elif isinstance(self._cfg['options'], (list, set, tuple)):
            numtables = len(self._cfg['options'])
        elif isinstance(self._cfg['trigsources'], (list, set, tuple)):
            numtables = len(self._cfg['trigsources'])
        else:
            numtables = 1
        self._cfg['rectables'] = list(range(1, numtables + 1))
        return self._cfg['rectables']

    def wait(self, timeout=0):
        """Wait for end of data recording.
        @param timeout : Timeout in seconds, is disabled by default.
        """
        if not self.rectables:
            raise SystemError('rectables are not set')
        numvalues = self.numvalues or self.maxnumvalues
        if self._gcs.HasqDRL():
            maxtime = time() + timeout
            while min([self._gcs.qDRL(table)[table] for table in self.rectables]) < numvalues:
                if timeout and time() > maxtime:
                    raise SystemError('timeout after %.1f secs while waiting on data recorder' % timeout)
        else:
            waittime = 1.2 * self.rectime
            debug('Datarecorder.wait: wait %.2f secs for data recording', waittime)
            sleep(waittime)

    def read(self, offset=None, numvalues=None, verbose=False):
        """Read out the data and return it.
        @param offset : Start point in the table as integer, starts with index 1, overwrites self.offset.
        @param numvalues : Number of points to be read per table as integer, overwrites self.numvalues.
        @param verbose : If True print a line that shows how many values have been read out already.
        @return : Tuple of (header, data), see qDRR command.
        """
        if not self.rectables:
            raise SystemError('rectables are not set')
        header = self._gcs.qDRR(self.rectables, offset or self.offset, numvalues or self.numvalues)
        while self._gcs.bufstate is not True:
            if verbose:
                print(('\rread data {:.1f}%...'.format(self._gcs.bufstate * 100)), end='')
            sleep(0.05)
        if verbose:
            print(('\r%s\r' % (' ' * 20)), end='')
        data = self._gcs.bufdata
        return header, data

    def getdata(self, timeout=0, offset=None, numvalues=None):
        """Wait for end of data recording, start reading out the data and return the data.
        @param timeout : Timeout in seconds, is disabled by default.
        @param offset : Start point in the table as integer, starts with index 1, overwrites self.offset.
        @param numvalues : Number of points to be read per table as integer, overwrites self.numvalues.
        @return : Tuple of (header, data), see qDRR command.
        """
        self.wait(timeout)
        self._header, self._data = self.read(offset, numvalues)
        return self._header, self._data

    @property
    def header(self):
        """Return header from last controller readout."""
        if self._header is None:
            self.getdata()
        return self._header

    @property
    def data(self):
        """Return data from last controller readout."""
        if self._data is None:
            self.getdata()
        return self._data

    def arm(self):
        """Ready the data recorder with given options and activate the trigger.
        If TriggerSources.NEXT_COMMAND_WITH_RESET_2 is used then the error check will be disabled.
        """
        self._header = None
        self._data = None
        if self._gcs.HasDRC():
            for i in range(len(self.rectables)):
                self._gcs.DRC(self.rectables[i], self.sources[i], self.options[i])
        else:
            warning('device %r does not support the DRC command', self._gcs.devname)
        if self._gcs.HasDRT():
            errcheck = None
            if isinstance(self.trigsources, (list, set, tuple)):
                if TriggerSources.NEXT_COMMAND_WITH_RESET_2 in self.trigsources:
                    errcheck = self._gcs.errcheck
                    self._gcs.errcheck = False
                if len(self.trigsources) == 1:
                    self.trigsources = [self.trigsources[0]] * len(self.rectables)
                for i in range(len(self.rectables)):
                    self._gcs.DRT(self.rectables[i], self.trigsources[i])
            else:
                if TriggerSources.NEXT_COMMAND_WITH_RESET_2 == self.trigsources:
                    errcheck = self._gcs.errcheck
                    self._gcs.errcheck = False
                self._gcs.DRT(0, self.trigsources)
            if errcheck is not None:
                self._gcs.errcheck = errcheck
        else:
            warning('device %r does not support the DRT command', self._gcs.devname)

    @property
    def timescale(self):
        """Return list of values for time scale of recorded data."""
        return [self.sampletime * x for x in range(self.numvalues)]


# 'get_hdr_options' is too complex. The McCabe rating is 11 pylint: disable=R1260
# Too many branches (14/12) pylint: disable=R0912
def get_hdr_options(pidevice, return_additional_info=False):
    """Call qHDR comamnd and return record and trigger options of connected device.
    @type pidevice : pipython.gcscommands.GCSCommands
    @type return_additional_info: bool
    @return : Tuple of record, trigger and additional_info options as lists of integers.
              additional_info is only returned if return_additional_info = 'True'
    """
    if not isdeviceavailable([GCS2Commands], pidevice):
        raise TypeError('Type %s is not supported!' % type(pidevice).__name__)

    state = 0  # 0: NONE, 1: RECOPTS, 2: TRIGOPTS
    recopts, trigopts, additional_info = [], [], []
    for line in pidevice.qHDR().splitlines():
        line = line.strip()
        if line.startswith('#'):
            if line.startswith('#RecordOptions'):
                state = 1
            elif line.startswith('#TriggerOptions'):
                state = 2
            elif line.startswith('#Additional information'):
                state = 3
            else:
                state = 0
            continue
        if state == 0:
            continue

        if state != 3:
            try:
                option = int(line.split('=')[0].strip())
            except ValueError:
                warning('could not parse qHDR line %r', line)
                continue

        if state == 1:
            recopts.append(option)
        elif state == 2:
            trigopts.append(option)
        elif state == 3:
            additional_info.append(line)

    if return_additional_info:
        return recopts, trigopts, additional_info

    return recopts, trigopts
