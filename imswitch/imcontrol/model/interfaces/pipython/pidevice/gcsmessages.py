#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Process messages between GCSCommands and an interface."""

from logging import debug, error
from threading import RLock, Thread
import sys
from time import time, sleep
from . import GCSError, gcserror

__signature__ = 0xdff93d5a91493df4629f29e59f13faf2


def eol(rcvbuf):
    """Return True if 'rcvbuf' is complete in terms of GCS syntax.
    @param rcvbuf : Answer as string.
    @return : True if 'rcvbuf' is complete else False.
    """
    if not rcvbuf:
        return False
    if len(rcvbuf) == 1:
        if ord(rcvbuf[-1]) < 32:
            return True
        return False
    if rcvbuf[-1] == '\n' and rcvbuf[-2] != ' ':
        return True
    return False


# Too many instance attributes (8/7) pylint: disable=R0902
# Class inherits from object, can be safely removed from bases in python3 pylint: disable=R0205
class GCSMessages(object):
    """Provide a GCS communication layer."""

    def __init__(self, interface):
        """Provide a GCS communication layer.
        @type interface : pipython.interfaces.pigateway.PIGateway
        """
        debug('create an instance of GCSMessages(interface=%s)', interface)
        self._lock = RLock()
        self._interface = interface
        self._databuffer = {'size': 0, 'index': 0, 'lastindex': 0, 'lastupdate': None, 'data': [], 'error': None,
                            'lock': False}
        self._stopthread = False
        self.logfile = ''  # Full path to file where communication to/from controller is logged.
        self.errcheck = True
        self.embederr = False
        self._gcs_error_class = GCSError

    def __str__(self):
        return 'GCSMessages(interface=%s), id=%d' % (self._interface, self.connectionid)

    @property
    def gcs_error_class(self):
        """
        the GCS error class
        :return: the current GCS error class
        """
        return self._gcs_error_class

    @gcs_error_class.setter
    def gcs_error_class(self, gcserrorclass):
        """
        specifies the GCS error class
        :param gcserrorclass: The GCSError class
        :type gcserrorclass: GCSError or GCS21Error
        :return:
        """
        if gcserrorclass is not None:
            self._gcs_error_class = gcserrorclass

    @property
    def connectionid(self):
        """Get ID of current connection as integer."""
        return self._interface.connectionid

    @property
    def connected(self):
        """Get the connection state as bool."""
        return self._interface.connected

    @property
    def timeout(self):
        """Get current timeout setting in milliseconds."""
        return self._interface.timeout

    @timeout.setter
    def timeout(self, value):
        """Set timeout.
        @param value : Timeout in milliseconds as integer.
        """
        value = int(value)
        self._interface.settimeout(value)

    @property
    def bufstate(self):
        """False if no buffered data is available. True if buffered data is ready to use.
        Float value 0..1 indicates read progress. To wait, use "while bufstate is not True".
        """
        if self._databuffer['error']:
            self._stopthread = True
            raise self._databuffer['error']  # Raising NoneType pylint: disable=E0702
        if self._databuffer['lastupdate'] is None:
            self._databuffer['lastupdate'] = time()
        if self._databuffer['index'] == self._databuffer['lastindex']:
            if time() - float(self._databuffer['lastupdate']) > self.timeout / 1000.:
                self._stopthread = True
                raise GCSError(gcserror.COM_TIMEOUT__7, '@ GCSMessages.bufstate after %.1f s' % (self.timeout / 1000.))
        else:
            self._databuffer['lastupdate'] = time()
            self._databuffer['lastindex'] = self._databuffer['index']
        if not self._databuffer['size']:
            return False
        if self._databuffer['size'] is True:
            self._databuffer['lastupdate'] = None
            return True
        return float(self._databuffer['index']) / float(self._databuffer['size'])

    @property
    def bufdata(self):
        """Get buffered data as 2-dimensional list of float values."""
        debug('GCSMessages.bufdata: %d datasets', self._databuffer['index'])
        return self._databuffer['data']

    def send(self, tosend):
        """Send 'tosend' to device and check for error.
        @param tosend : String to send to device, with or without trailing linefeed.
        """
        if self.embederr and self.errcheck:
            if len(tosend) > 1 and not tosend.endswith('\n'):
                tosend += '\n'
            tosend += 'ERR?\n'
        with self._lock:
            self._send(tosend)
            self._checkerror(senderr=not self.embederr)

    def read(self, tosend, gcsdata=0):
        """Send 'tosend' to device, read answer and check for error.
        @param tosend : String to send to device.
        @param gcsdata : Number of lines, if != 0 then GCS data will be read in background task.
        @return : Device answer as string.
        """
        if gcsdata is not None:
            gcsdata = None if gcsdata < 0 else gcsdata
        stopon = None
        if gcsdata != 0:
            stopon = '# END_HEADER'
            self._databuffer['data'] = []
            self._databuffer['index'] = 0
            self._databuffer['error'] = None
        with self._lock:
            self._send(tosend)
            answer = self._read(stopon)
            if gcsdata != 0:
                splitpos = answer.upper().find(stopon)
                if splitpos < 0:
                    self._send('ERR?\n')
                    err = int(self._read(stopon=None).strip())
                    err = err or gcserror.E_1004_PI_UNEXPECTED_RESPONSE
                    raise GCSError(err, '@ GCSMessages.read, no %r in %r' % (stopon, answer))
                stopon += ' \n'
                splitpos += len(stopon)
                strbuf = answer[splitpos:]  # split at "# END HEADER \n", this is the data
                answer = answer[:splitpos]  # split at "# END HEADER \n", this is the header
                if stopon in answer.upper():  # "# END HEADER\n" will not start reading GCS data
                    self._databuffer['size'] = gcsdata
                    self._readgcsdata(strbuf)
                else:
                    self._databuffer['size'] = True
            else:
                self._checkerror()
        return answer

    def _savelog(self, msg):
        """Save (i.e. append) 'msg' to self.logfile.
        @param msg : Message to save with or without trailing linefeed.
        """
        if not self.logfile:
            return
        msg = str(msg.encode('cp1252'))  # no "u" prefix in log file, e.g. u'POS?' -> 'POS?'
        msg = '%r' % msg.rstrip('\n')
        msg = msg.lstrip("'").rstrip("'")
        with open(self.logfile, 'a') as fobj:
            fobj.write('%s\n' % msg)

    def _send(self, tosend):
        """Send 'tosend' to device.
        @param tosend : String to send to device, with or without trailing linefeed.
        """
        if len(tosend) > 1 and not tosend.endswith('\n'):
            tosend += '\n'
        self._interface.send(tosend)
        self._savelog(tosend)

    def _read(self, stopon):
        """Read answer from device until this ends with linefeed with no preceeding space.
        @param stopon: Addditional uppercase string that stops reading, too.
        @return : Received data as string.
        """
        rcvbuf = u''
        timeout = time() + self.timeout / 1000.
        while not eol(rcvbuf):
            received = self._interface.read()
            if received:
                rcvbuf += received.decode(encoding='cp1252', errors='ignore')
                timeout = time() + self.timeout / 1000.
            if time() > timeout:
                raise GCSError(gcserror.E_7_COM_TIMEOUT, '@ GCSMessages._read')
            if stopon and stopon in rcvbuf.upper():
                break
        self._savelog('  ' + rcvbuf)
        self._check_no_eol(rcvbuf)
        return rcvbuf

    @staticmethod
    def _check_no_eol(answer):
        """Check that 'answer' does not contain a LF without a preceeding SPACE except at the end.
        @param answer : Answer to verify as string.
        """
        for i, char in enumerate(answer[:-1]):
            # Consider merging these comparisons with "in" to "char in ('\\n', '\\r')" pylint: disable=R1714
            if char == '\n' or char == '\r':
                if i > 0 and answer[i - 1] != ' ':
                    msg = '@ GCSMessages._check_no_eol: LF/CR at %r' % answer[max(0, i - 10):min(i + 10, len(answer))]
                    raise GCSError(gcserror.E_1004_PI_UNEXPECTED_RESPONSE, msg)

    def _readgcsdata(self, strbuf):
        """Start a background task to read out GCS data and save it in the instance.
        @param strbuf : String of already readout answer.
        """
        if not eol(strbuf):
            strbuf += self._read(stopon=' \n')
        numcolumns = len(strbuf.split('\n')[0].split())
        self._databuffer['data'] = [[] for _ in range(numcolumns)]
        debug('GCSMessages: start background task to query GCS data')
        self._stopthread = False
        thread = Thread(target=self._fillbuffer, args=(strbuf, lambda: self._stopthread))
        thread.start()

    def _fillbuffer(self, answer, stop):
        """Read answers and save them as float values into the data buffer.
        An answerline with invalid data (non-number, missing column) will be skipped and error flag is set.
        @param answer : String of already readout answer.
        @param stop : Callback function that stops the loop if True.
        """
        with self._lock:
            while True:
                lines = answer.splitlines(True)  # keep line endings
                answer = ''
                for line in lines:
                    if '\n' not in line:
                        answer = line
                        break
                    self._convertfloats(line)
                    if self._endofdata(line):
                        debug('GCSMessages: end background task to query GCS data')
                        if not self._databuffer['error']:
                            self._databuffer['error'] = self._checkerror(doraise=False)
                        if not self._databuffer['error']:
                            self._databuffer['size'] = True
                        return
                try:
                    answer += self._read(stopon=' \n')
                except:  # No exception type(s) specified pylint: disable=W0702
                    exc = GCSError(gcserror.E_1090_PI_GCS_DATA_READ_ERROR, sys.exc_info()[1])
                    self._databuffer['error'] = exc
                    error('GCSMessages: end background task with GCSError: %s', exc)
                    self._databuffer['size'] = True
                    return
                if stop():
                    error('GCSMessages: stop background task to query GCS data')
                    return

    def _convertfloats(self, line):
        """Convert items in 'line' to float and append them to 'self._databuffer'.
        @param line : One line in qDRR answer with data values as string.
        """
        numcolumns = len(self._databuffer['data'])
        msg = 'cannot convert to float: %r' % line
        try:
            values = [float(x) for x in line.split()]
            if numcolumns != len(values):
                msg = 'expected %d, got %d columns: %r' % (numcolumns, len(values), line)
                raise ValueError()
        except ValueError:
            exc = GCSError(gcserror.E_1004_PI_UNEXPECTED_RESPONSE, msg)
            self._databuffer['error'] = exc
            error('GCSMessages: GCSError: %s', exc)
        else:
            while self._databuffer['lock']:
                sleep(0.05)

            try:
                self._databuffer['lock'] = True
                for i in range(numcolumns):
                    self._databuffer['data'][i].append(values[i])
            finally:
                self._databuffer['lock'] = False

        self._databuffer['index'] += 1

    def _endofdata(self, line):
        """Verify 'line' and return True if 'line' is last line of device answer.
        @param line : One answer line of device with trailing line feed character.
        @return : True if 'line' is last line of device answer.
        """
        if eol(line) and self._databuffer['size'] and self._databuffer['index'] < self._databuffer['size']:
            msg = '%s expected, %d received' % (self._databuffer['size'], self._databuffer['index'])
            exc = GCSError(gcserror.E_1088_PI_TOO_FEW_GCS_DATA, msg)
            self._databuffer['error'] = exc
            error('GCSMessages: GCSError: %s', exc)
        if self._databuffer['size'] and self._databuffer['index'] > self._databuffer['size']:
            msg = '%s expected, %d received' % (self._databuffer['size'], self._databuffer['index'])
            exc = GCSError(gcserror.E_1089_PI_TOO_MANY_GCS_DATA, msg)
            self._databuffer['error'] = exc
            error('GCSMessages: GCSError: %s', exc)
        return eol(line)

    def _checkerror(self, senderr=True, doraise=True):
        """Query error from device and raise GCSError exception.
        @param senderr : If True send "ERR?\n" to the device.
        @param doraise : If True an error is raised, else the GCS error number is returned.
        @return : If doraise is False the GCS exception if an error occured else None.
        """
        if not self.errcheck:
            return 0
        if senderr:
            self._send('ERR?\n')
        answer = self._read(stopon=None)
        exc = None
        try:
            err = int(answer)
        except ValueError:
            exc = GCSError(gcserror.E_1004_PI_UNEXPECTED_RESPONSE, 'invalid answer on "ERR?": %r' % answer)
        else:
            if err:
                exc = self.gcs_error_class(err)
        if exc and doraise:
            raise exc  # Raising NoneType while only classes or instances are allowed pylint: disable=E0702
        return exc
