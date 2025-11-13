#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Collection of helpers for using a PI device."""

from logging import debug, info, warning
from time import sleep, time
from future.utils import raise_from

from ..gcs2.gcs2commands import GCS2Commands
from .. import GCS21Commands
from ...pitools.pitools import itemstostr
from .. import gcserror
from .. import GCS21Error
from ..gcserror import GCSError
from ..common.gcscommands_helpers import getitemsvaluestuple, isdeviceavailable
from ..piparams import applyconfig

__signature__ = 0x3e9aa17af2d4326f19838cb8cd3aae95


# Class inherits from object, can be safely removed from bases in python3 pylint: disable=R0205
class DeviceStartup(object):  # Too many instance attributes pylint: disable=R0902
    """Provide a "ready to use" PI device."""

    DEFAULT_SEQUENCE = (
        'setaxesnames', 'setstages', 'callini', 'enableonl', 'stopall', 'waitonready', 'enableaxes', 'referencewait',
        'findphase', 'resetservo', 'waitonready',)
    SPECIAL_SEQUENCE = {
        'HYDRA': [x for x in DEFAULT_SEQUENCE if x not in ('callini',)],
        'C-887': [x for x in DEFAULT_SEQUENCE if x not in ('stopall',)],
        'E-861 VERSION 7': [x for x in DEFAULT_SEQUENCE if x not in ('stopall',)],
    }

    def __init__(self, pidevice, **kwargs):
        """Provide a "ready to use" PI device.
        @type pidevice : pipython.gcscommands.GCSCommands
        @param kwargs : Optional arguments with keywords that are passed to sub functions.
        """
        debug('create an instance of ControllerStartup(kwargs=%s)', itemstostr(kwargs))

        if not isdeviceavailable([GCS2Commands, GCS21Commands], pidevice):
            raise TypeError('Type %s of pidevice is not supported!' % type(pidevice).__name__)

        self.pidevice = pidevice
        self._stages = None
        self._refmodes = None
        self._servo = None
        self._axesnames = None
        self._kwargs = kwargs
        self._databuf = {'servobuf': {}, 'cstdone': []}
        self.prop = {
            'devname': self.pidevice.devname, 'skipcst': False, 'forcecst': False, 'skipsai': False,
            'forcesai': False, 'showlog': False, 'skipini': False, 'skiponl': False, 'skipeax': False,
            'skipref': False, 'forceref': False, 'skipfph': False,
        }

    @property
    def stages(self):
        """Name of stages as list of strings or None."""
        return self._stages

    @stages.setter
    def stages(self, stages):
        """Name of stages to initialize as string or list (not tuple!) or None to skip.
        Skip single axes with "" or None as item in the list.
        """
        if stages is None:
            self._stages = None
        else:
            self._stages = stages if isinstance(stages, list) else [stages] * len(self.pidevice.allaxes)
        debug('ControllerStartup.stages = %s', itemstostr(self._stages))

    @property
    def refmodes(self):
        """Referencing commands as list of strings or None."""
        return self._refmodes

    @refmodes.setter
    def refmodes(self, refmodes):
        """Referencing command as string (for all stages) or list (not tuple!) or None to skip.
        Skip single axes with "" or None as item in the list.
        """
        if refmodes is None:
            self._refmodes = None
        else:
            self._refmodes = refmodes if isinstance(refmodes, list) else [refmodes] * len(self.pidevice.allaxes)
        debug('ControllerStartup.refmodes = %s', itemstostr(self._refmodes))

    @property
    def servostates(self):
        """Servo states as dict {axis: state} or None."""
        if isinstance(self._servo, bool):
            return dict(list(zip(self.pidevice.axes, [self._servo] * self.pidevice.numaxes)))
        return self._servo

    @servostates.setter
    def servostates(self, servo):
        """Desired servo states as boolean (for all stages) or dict {axis: state} or None to skip."""
        self._servo = servo
        debug('ControllerStartup.servostates = %s', itemstostr(self._servo))

    @property
    def axesnames(self):
        """Name of axes as list of strings or None."""
        return self._axesnames

    @axesnames.setter
    def axesnames(self, axesnames):
        """Name of axes to set as list of strings (not tuple!) or None to skip."""
        if axesnames is None:
            self._axesnames = None
        else:
            assert isinstance(axesnames, list), 'axesnames must be list'
            self._axesnames = axesnames
        debug('ControllerStartup.axesnames = %s', itemstostr(self._axesnames))

    def run(self):
        """Run according startup sequence to provide a "ready to use" PI device."""
        debug('ControllerStartup.run()')
        sequence = self.SPECIAL_SEQUENCE.get(self.prop['devname'], self.DEFAULT_SEQUENCE)
        for func in sequence:
            getattr(self, '%s' % func)()

    def setstages(self):
        """Set stages if according option has been provided."""
        if not self._stages or self.prop['skipcst']:
            return
        debug('ControllerStartup.setstages()')
        allaxes = self.pidevice.qSAI_ALL()
        oldstages = self.pidevice.qCST()
        for i, newstage in enumerate(self._stages):
            if not newstage:
                continue
            axis = allaxes[i]
            oldstage = oldstages.get(axis, 'NOSTAGE')
            if oldstage != newstage or self.prop['forcecst']:
                warnmsg = applyconfig(self.pidevice, axis, newstage)
                self._databuf['cstdone'].append(axis)
                if self.prop['showlog'] and warnmsg:
                    warning(warnmsg)
            elif self.prop['showlog']:
                info('stage %r on axis %r is already configured', oldstage, axis)

    def findphase(self):
        """Start find phase if cst was done before
        """
        debug('ControllerStartup.findphase()')
        if not self.pidevice.HasFPH() or self.prop['skipfph']:
            return
        if not self._databuf['cstdone']:
            debug('no need to do find phase for axes %r', self.pidevice.axes)
            return
        for axis in self._databuf['cstdone']:
            if self.pidevice.qFRF(axis)[axis]:
                self.pidevice.FPH(axis)
                waitonphase(self.pidevice, **self._kwargs)
                self.pidevice.WPA()
            else:
                info('skip find phase for axis while axis %s is not referenced' % axis)

    def setaxesnames(self):
        """Set stages if according option has been provided."""
        if not self._axesnames or self.prop['skipsai']:
            return
        debug('ControllerStartup.setaxesnames()')
        oldaxes = self.pidevice.qSAI_ALL()
        for i, newaxis in enumerate(self.axesnames):
            if newaxis != oldaxes[i] or self.prop['forcesai']:
                setstage = False
                if self.pidevice.HasqCST():
                    if self.pidevice.qCST()[oldaxes[i]] == 'NOSTAGE':
                        try:
                            debug('try rename NOSTAGE to TEMP (0x3C)')
                            self.pidevice.SPA(oldaxes[i], 0x3c, 'TEMP')
                            setstage = True
                        except GCSError:
                            pass
                self.pidevice.SAI(oldaxes[i], newaxis)
                if setstage:
                    self.pidevice.SPA(newaxis, 0x3c, 'NOSTAGE')
                    debug('restore NOSTAGE (0x3C)')

    def callini(self):
        """Call INI command if available."""
        debug('ControllerStartup.callini()')
        if not self.pidevice.HasINI() or self.prop['skipini']:
            return
        self.pidevice.INI()

    def enableonl(self):
        """Enable online state of connected axes if available."""
        debug('ControllerStartup.enableonl()')
        if not self.pidevice.HasONL() or self.prop['skiponl']:
            return
        self.pidevice.ONL(list(range(1, self.pidevice.numaxes + 1)), [True] * self.pidevice.numaxes)

    def stopall(self):
        """Stop all axes."""
        debug('ControllerStartup.stopall()')
        stopall(self.pidevice, **self._kwargs)

    def waitonready(self):
        """Wait until device is ready."""
        debug('ControllerStartup.waitonready()')
        waitonready(self.pidevice, **self._kwargs)

    def resetservo(self):
        """Reset servo if it has been changed during referencing."""
        debug('ControllerStartup.resetservo()')
        if self.servostates is not None:
            setservo(self.pidevice, self.servostates)
        elif self._databuf['servobuf']:
            setservo(self.pidevice, self._databuf['servobuf'])

    def referencewait(self):
        """Reference unreferenced axes if according option has been provided and wait on completion."""
        debug('ControllerStartup.referencewait()')
        if not self.refmodes or self.prop['skipref']:
            return
        self._databuf['servobuf'] = getservo(self.pidevice, self.pidevice.axes)
        toreference = {}  # {cmd: [axes]}
        for i, refmode in enumerate(self._refmodes[:self.pidevice.numaxes]):
            if not refmode:
                continue
            axis = self.pidevice.axes[i]
            refmode = refmode.upper()
            if refmode not in toreference:
                toreference[refmode] = []
            if self._isreferenced(refmode, axis):
                debug('axis %r is already referenced by %r', axis, refmode)
            else:
                toreference[refmode].append(self.pidevice.axes[i])
        waitonaxes = []
        for refmode, axes in toreference.items():
            if not axes:
                continue
            if refmode == 'POS':
                self._ref_with_pos(axes)
            elif refmode == 'ATZ':
                self._autozero(axes)
            else:
                self._ref_with_refcmd(axes, refmode)
                waitonaxes += axes
        waitonreferencing(self.pidevice, axes=waitonaxes, **self._kwargs)

    def _isreferenced(self, refmode, axis):
        """Check if 'axis' has already been referenced with 'refmode'.
        @param refmode : Mode of referencing as string, e.g. POS, ATZ, FRF.
        @param axis : Name of axis to check as string.
        @return : False if 'axis' is not referenced or must be referenced.
        """
        if self.prop['forceref']:
            return False
        if refmode in ('POS',):
            return False
        if refmode == 'ATZ':
            return self.pidevice.qATZ(axis)[axis]
        if refmode == 'REF':
            return self.pidevice.qREF(axis)[axis]
        return self.pidevice.qFRF(axis)[axis]

    def _ref_with_refcmd(self, axes, refmode):
        """Enable RON, change servo state if appropriate and reference 'axes' with the 'refmode' command.
        @param axes : Axes to reference as list or tuple of strings, must not be empty.
        @param refmode : Name of command to use for referencing as string.
        """
        debug('ControllerStartup._ref_with_refcmd(axes=%s, refmode=%s)', axes, refmode)
        for axis in axes:
            if self.pidevice.HasRON():
                try:
                    self.pidevice.RON(axis, True)
                except GCSError as exc:
                    if exc == gcserror.E34_PI_CNTR_CMD_NOT_ALLOWED_FOR_STAGE:
                        pass  # hexapod axis
                    else:
                        raise
            try:
                getattr(self.pidevice, refmode)(axis)
            except GCSError as exc:
                if exc == gcserror.E5_PI_CNTR_MOVE_WITHOUT_REF_OR_NO_SERVO:
                    self._databuf['servobuf'][axis] = getservo(self.pidevice, axis)[axis]
                    self.pidevice.SVO(axis, not self._databuf['servobuf'][axis])
                    getattr(self.pidevice, refmode)(axis)
                else:
                    raise
            if self.pidevice.devname in ('C-843',):
                waitonreferencing(self.pidevice, axes=axis, **self._kwargs)
            waitonready(self.pidevice)

    def _autozero(self, axes):
        """Autozero 'axes' and move them to position "0.0".
        @param axes : Axes to autozero as list or tuple of strings, must not be empty.
        """
        debug('ControllerStartup._autozero(axes=%s)', axes)
        self.pidevice.ATZ(axes, ['NaN'] * len(axes))
        waitonautozero(self.pidevice, axes, **self._kwargs)
        setservo(self.pidevice, axes, [True] * len(axes), **self._kwargs)
        moveandwait(self.pidevice, axes, [0.0] * len(axes), **self._kwargs)

    def _ref_with_pos(self, axes):
        """Set RON accordingly and reference 'axes' with the POS command to position "0.0".
        @param axes : Axes to reference as list or tuple of strings, must not be empty.
        """
        debug('ControllerStartup._ref_with_pos(axes=%s)', axes)
        assert self.pidevice.HasPOS(), 'controller does not support the POS command'
        self.pidevice.RON(axes, [False] * len(axes))
        self.pidevice.POS(axes, [0.0] * len(axes))
        waitonready(self.pidevice, **self._kwargs)
        self.pidevice.SVO(axes, [True] * len(axes))  # A following qONT will fail if servo is disabled.

    def enableaxes(self):
        """Enable all connected axes if appropriate."""
        debug('ControllerStartup.enableaxes()')
        if not self.pidevice.HasEAX() or self.prop['skipeax']:
            return
        for axis in self.pidevice.axes:
            try:
                self.pidevice.EAX(axis, True)
            except GCSError as exc:
                if exc != gcserror.E2_PI_CNTR_UNKNOWN_COMMAND:
                    raise
        waitonready(self.pidevice, **self._kwargs)


# Class inherits from object, can be safely removed from bases in python3 pylint: disable=R0205
class GCSRaise(object):  # Too few public methods pylint: disable=R0903
    """Context manager that asserts raising of specific GCSError(s).
    @param gcserrorid : GCSError ID or iterable of IDs that are expected to be raised as integer.
    @param mustraise : If True an exception must be raised, if False an exception can be raised.
    """

    def __init__(self, gcserrorid, mustraise=True):
        debug('create an instance of GCSRaise(gcserrorid=%s, mustraise=%s', gcserrorid, mustraise)
        self.__expected = gcserrorid if isinstance(gcserrorid, (list, set, tuple)) else [gcserrorid]
        self.__mustraise = mustraise and gcserrorid

    def __enter__(self):
        return self

    def __exit__(self, exctype, excvalue, _exctraceback):
        gcsmsg = '%r' % gcserror.translate_error(excvalue)
        if exctype in (GCSError, GCS21Error):
            if excvalue in self.__expected:
                debug('expected GCSError %s was raised', gcsmsg)
                return True  # do not re-raise
        if not self.__mustraise and excvalue is None:
            debug('no error was raised')
            return True  # do not re-raise
        expected = ', '.join([gcserror.translate_error(errval) for errval in self.__expected])
        msg = 'expected %s%r but raised was %s' % ('' if self.__mustraise else 'no error or ', expected, gcsmsg)
        if exctype is not None:
            raise_from(ValueError(msg), exctype(excvalue))
        else:
            raise_from(ValueError(msg), Exception)

        return True

def startup(pidevice, stages=None, refmodes=None, servostates=True, **kwargs):
    """Define 'stages', stop all, enable servo on all connected axes and reference them with 'refmodes'.
    Defining stages and homing them is done only if necessary.
    @type pidevice : pipython.gcscommands.GCSCommands
    @param stages : Name of stages to initialize as string or list (not tuple!) or None to skip.
    @param refmodes : Referencing command as string (for all stages) or list (not tuple!) or None to skip.
    @param servostates : Desired servo states as boolean (for all stages) or dict {axis: state} or None to skip.
    @param kwargs : Optional arguments with keywords that are passed to sub functions.
    """
    if not isdeviceavailable([GCS2Commands, GCS21Commands], pidevice):
        raise TypeError('Type %s of pidevice is not supported!' % type(pidevice).__name__)

    assert not isinstance(stages, tuple), 'argument "stages" must not to be of type "tuple"'
    assert not isinstance(refmodes, tuple), 'argument "refmodes" must not to be of type "tuple"'
    devstartup = DeviceStartup(pidevice, **kwargs)
    devstartup.stages = stages
    devstartup.refmodes = refmodes
    devstartup.servostates = servostates
    devstartup.run()


def writewavepoints(pidevice, wavetable, wavepoints, bunchsize=None):
    """Write 'wavepoints' for 'wavetable' in bunches of 'bunchsize'.
    The 'bunchsize' is device specific. Please refer to the controller manual.
    @type pidevice : pipython.gcscommands.GCSCommands
    @param wavetable : Wave table ID as integer.
    @param wavepoints : Single wavepoint as float convertible or list/tuple of them.
    @param bunchsize : Number of wavepoints in a single bunch or None to send all 'wavepoints' in a single bunch.
    """
    if not isdeviceavailable([GCS2Commands, GCS21Commands], pidevice):
        raise TypeError('Type %s of pidevice is not supported!' % type(pidevice).__name__)

    wavepoints = wavepoints if isinstance(wavepoints, (list, set, tuple)) else [wavepoints]
    if bunchsize is None:
        bunchsize = len(wavepoints)
    for startindex in range(0, len(wavepoints), bunchsize):
        bunch = wavepoints[startindex:startindex + bunchsize]
        pidevice.WAV_PNT(table=wavetable, firstpoint=startindex + 1, numpoints=len(bunch),
                         append='&' if startindex else 'X', wavepoint=bunch)


def getaxeslist(pidevice, axes):
    """Return list of 'axes'.
    @type pidevice : pipython.gcscommands.GCSCommands
    @param axes : Axis as string or list or tuple of them or None for all axes.
    @return : List of axes from 'axes' or all axes or empty list.
    """
    if not isdeviceavailable([GCS2Commands, GCS21Commands], pidevice):
        raise TypeError('Type %s of pidevice is not supported!' % type(pidevice).__name__)

    axes = pidevice.axes if axes is None else axes
    if not axes:
        return []
    if not isinstance(axes, (list, set, tuple)):
        axes = [axes]
    return list(axes)  # convert tuple to list


def getservo(pidevice, axes):
    """Return dictionary of servo states or "False" if the qSVO command is not supported.
    @type pidevice : pipython.gcscommands.GCSCommands
    @param axes : Axis or list/tuple of axes to get values for or None for all axes.
    @return : Dictionary of boolean servo states of 'axes'.
    """
    if not isdeviceavailable([GCS2Commands, GCS21Commands], pidevice):
        raise TypeError('Type %s of pidevice is not supported!' % type(pidevice).__name__)

    axes = getaxeslist(pidevice, axes)
    if not axes:
        return {}
    if pidevice.HasqSVO():
        return pidevice.qSVO(axes)
    return dict(list(zip(axes, [False] * len(axes))))


def ontarget(pidevice, axes):
    """Return dictionary of on target states for open- or closedloop 'axes'.
    If qOSN is not supported open loop axes will return True.
    @type pidevice : pipython.gcscommands.GCSCommands
    @param axes : Axis or list/tuple of axes to get values for or None for all axes.
    @return : Dictionary of boolean ontarget states of 'axes'.
    """
    if not isdeviceavailable([GCS2Commands, GCS21Commands], pidevice):
        raise TypeError('Type %s of pidevice is not supported!' % type(pidevice).__name__)

    axes = getaxeslist(pidevice, axes)
    if not axes:
        return {}
    servo = getservo(pidevice, axes)
    closedloopaxes = [axis for axis in axes if servo[axis]]
    openloopaxes = [axis for axis in axes if not servo[axis]]
    isontarget = {}
    if closedloopaxes:
        if pidevice.HasqONT():
            isontarget.update(pidevice.qONT(closedloopaxes))
        elif pidevice.HasIsMoving():
            ismoving = pidevice.IsMoving(closedloopaxes).values()
            isontarget.update(dict(list(zip(closedloopaxes, [not x for x in ismoving]))))
    if openloopaxes:
        if pidevice.HasqOSN():
            stepsleft = pidevice.qOSN(openloopaxes).values()
            isontarget.update(dict(list(zip(openloopaxes, [x == 0 for x in stepsleft]))))
        else:
            isontarget.update(dict(list(zip(openloopaxes, [True] * len(openloopaxes)))))
    return isontarget


def waitonready(pidevice, timeout=300, predelay=0, polldelay=0.1):
    """Wait until controller is on "ready" state and finally query controller error.
    @type pidevice : pipython.gcscommands.GCSCommands
    @param timeout : Timeout in seconds as float.
    @param predelay : Time in seconds as float until querying any state from controller.
    @param polldelay : Delay time between polls in seconds as float.
    """
    if not isdeviceavailable([GCS2Commands, GCS21Commands], pidevice):
        raise TypeError('Type %s of pidevice is not supported!' % type(pidevice).__name__)

    sleep(predelay)
    if not pidevice.HasIsControllerReady():
        return
    maxtime = time() + timeout
    while not pidevice.IsControllerReady():
        if time() > maxtime:
            raise SystemError('waitonready() timed out after %.1f seconds' % timeout)
        sleep(polldelay)
    pidevice.checkerror()


# Too many arguments pylint: disable=R0913
def waitontarget(pidevice, axes=None, timeout=300, predelay=0, postdelay=0, polldelay=0.1):
    """Wait until all closedloop 'axes' are on target.
    @type pidevice : pipython.gcscommands.GCSCommands
    @param axes : Axes to wait for as string or list/tuple, or None to wait for all axes.
    @param timeout : Timeout in seconds as float.
    @param predelay : Time in seconds as float until querying any state from controller.
    @param postdelay : Additional delay time in seconds as float after reaching desired state.
    @param polldelay : Delay time between polls in seconds as float.
    """
    if not isdeviceavailable([GCS2Commands, GCS21Commands], pidevice):
        raise TypeError('Type %s of pidevice is not supported!' % type(pidevice).__name__)

    axes = getaxeslist(pidevice, axes)
    if not axes:
        return
    waitonready(pidevice, timeout=timeout, predelay=predelay, polldelay=polldelay)
    if not pidevice.HasqONT():
        return
    servo = getservo(pidevice, axes)
    axes = [x for x in axes if servo[x]]
    maxtime = time() + timeout
    while not all(list(pidevice.qONT(axes).values())):
        if time() > maxtime:
            raise SystemError('waitontarget() timed out after %.1f seconds' % timeout)
        sleep(polldelay)
    sleep(postdelay)


def waitonfastalign(pidevice, name=None, timeout=300, predelay=0, postdelay=0, polldelay=0.1):
    """Wait until all 'axes' are on target.
    @type pidevice : pipython.gcscommands.GCSCommands
    @param name : Name of the process as string or list/tuple.
    @param timeout : Timeout in seconds as float.
    @param predelay : Time in seconds as float until querying any state from controller.
    @param postdelay : Additional delay time in seconds as float after reaching desired state.
    @param polldelay : Delay time between polls in seconds as float.
    """
    if not isdeviceavailable([GCS2Commands, GCS21Commands], pidevice):
        raise TypeError('Type %s of pidevice is not supported!' % type(pidevice).__name__)

    waitonready(pidevice, timeout=timeout, predelay=predelay, polldelay=polldelay)
    maxtime = time() + timeout
    while any(list(pidevice.qFRP(name).values())):
        if time() > maxtime:
            raise SystemError('waitonfastalign() timed out after %.1f seconds' % timeout)
        sleep(polldelay)
    sleep(postdelay)


def waitonwavegen(pidevice, wavegens=None, timeout=300, predelay=0, postdelay=0, polldelay=0.1):
    """Wait until all 'axes' are on target.
    @type pidevice : pipython.gcscommands.GCSCommands
    @param wavegens : Integer convertible or list/tuple of them or None.
    @param timeout : Timeout in seconds as float.
    @param predelay : Time in seconds as float until querying any state from controller.
    @param postdelay : Additional delay time in seconds as float after reaching desired state.
    @param polldelay : Delay time between polls in seconds as float.
    """
    if not isdeviceavailable([GCS2Commands, GCS21Commands], pidevice):
        raise TypeError('Type %s of pidevice is not supported!' % type(pidevice).__name__)

    waitonready(pidevice, timeout=timeout, predelay=predelay, polldelay=polldelay)
    maxtime = time() + timeout
    while any(list(pidevice.IsGeneratorRunning(wavegens).values())):
        if time() > maxtime:
            raise SystemError('waitonwavegen() timed out after %.1f seconds' % timeout)
        sleep(polldelay)
    sleep(postdelay)


def waitonautozero(pidevice, axes=None, timeout=300, predelay=0, postdelay=0, polldelay=0.1):
    """Wait until all 'axes' are on target.
    @type pidevice : pipython.gcscommands.GCSCommands
    @param axes : Axes to wait for as string or list/tuple, or None to wait for all axes.
    @param timeout : Timeout in seconds as float.
    @param predelay : Time in seconds as float until querying any state from controller.
    @param postdelay : Additional delay time in seconds as float after reaching desired state.
    @param polldelay : Delay time between polls in seconds as float.
    """
    if not isdeviceavailable([GCS2Commands, GCS21Commands], pidevice):
        raise TypeError('Type %s of pidevice is not supported!' % type(pidevice).__name__)

    axes = getaxeslist(pidevice, axes)
    if not axes:
        return
    waitonready(pidevice, timeout=timeout, predelay=predelay, polldelay=polldelay)
    maxtime = time() + timeout
    while not all(list(pidevice.qATZ(axes).values())):
        if time() > maxtime:
            raise SystemError('waitonautozero() timed out after %.1f seconds' % timeout)
        sleep(polldelay)
    sleep(postdelay)


# Too many arguments pylint: disable=R0913
def waitonreferencing(pidevice, axes=None, timeout=300, predelay=0, postdelay=0, polldelay=0.1):
    """Wait until referencing of 'axes' is finished or timeout.
    @type pidevice : pipython.gcscommands.GCSCommands
    @param axes : Axis or list/tuple of axes to wait for or None for all axes.
    @param timeout : Timeout in seconds as float.
    @param predelay : Time in seconds as float until querying any state from controller.
    @param postdelay : Additional delay time in seconds as float after reaching desired state.
    @param polldelay : Delay time between polls in seconds as float.
    """
    if not isdeviceavailable([GCS2Commands, GCS21Commands], pidevice):
        raise TypeError('Type %s of pidevice is not supported!' % type(pidevice).__name__)

    axes = getaxeslist(pidevice, axes)
    if not axes:
        return
    waitonready(pidevice, timeout=timeout, predelay=predelay, polldelay=polldelay)
    maxtime = time() + timeout
    if pidevice.devname in ('C-843',):
        pidevice.errcheck = False
    while not all(list(pidevice.qFRF(axes).values())):
        if time() > maxtime:
            stopall(pidevice)
            raise SystemError('waitonreferencing() timed out after %.1f seconds' % timeout)
        sleep(polldelay)
    if pidevice.devname in ('C-843',):
        pidevice.errcheck = True
    sleep(postdelay)


def setservo(pidevice, axes, states=None, toignore=None, **kwargs):
    """Set servo of 'axes' to 'states'. Calls RNP for openloop axes and waits for servo
    operation to finish if appropriate. EAX is enabled for closedloop axes.
    @type pidevice : pipython.gcscommands.GCSCommands
    @param axes: Axis or list/tuple of axes or dictionary {axis : value}.
    @param states : Bool or list of bools or None.
    @param toignore : GCS error as integer to ignore or list of them.
    @param kwargs : Optional arguments with keywords that are passed to sub functions.
    @return : False if setting the servo failed.
    """
    if not isdeviceavailable([GCS2Commands, GCS21Commands], pidevice):
        raise TypeError('Type %s of pidevice is not supported!' % type(pidevice).__name__)

    if not pidevice.HasSVO():
        return False
    if not axes:
        return True
    axes, states = getitemsvaluestuple(axes, states)
    if pidevice.HasRNP():
        axestorelax = [axis for axis, state in list(getservo(pidevice, axes).items()) if not state]
        if axestorelax:
            pidevice.RNP(axestorelax, [0.0] * len(axestorelax))
            waitonready(pidevice, **kwargs)
    eaxaxes = [axes[i] for i in range(len(axes)) if states[i]]
    enableaxes(pidevice, axes=eaxaxes, **kwargs)
    success = True
    toignore = [] if toignore is None else toignore
    toignore = [toignore] if not isinstance(toignore, list) else toignore
    toignore += [gcserror.E5_PI_CNTR_MOVE_WITHOUT_REF_OR_NO_SERVO, gcserror.E23_PI_CNTR_ILLEGAL_AXIS]
    for i, axis in enumerate(axes):
        try:
            pidevice.SVO(axis, states[i])
        except GCSError as exc:  # no GCSRaise() because we want to log a warning
            if exc in toignore:
                debug('could not set servo for axis %r to %s: %s', axis, states[i], exc)
                success = False
            else:
                raise
    waitonready(pidevice, **kwargs)
    return success


def enableaxes(pidevice, axes, **kwargs):
    """Enable all 'axes'.
    @type pidevice : pipython.gcscommands.GCSCommands
    @param axes : String or list/tuple of strings of axes to enable.
    @param kwargs : Optional arguments with keywords that are passed to sub functions.
    """
    if not isdeviceavailable([GCS2Commands, GCS21Commands], pidevice):
        raise TypeError('Type %s of pidevice is not supported!' % type(pidevice).__name__)

    if not pidevice.HasEAX():
        return
    axes = getaxeslist(pidevice, axes)
    if not axes:
        return
    for axis in axes:
        try:
            pidevice.EAX(axis, True)
        except GCSError as exc:
            if exc == gcserror.E2_PI_CNTR_UNKNOWN_COMMAND:
                pass  # C-885
            else:
                raise
    waitonready(pidevice, **kwargs)


# Too many arguments pylint: disable=R0913
def waitonphase(pidevice, axes=None, timeout=300, predelay=0, postdelay=0, polldelay=0.1):
    """Wait until all 'axes' are on phase.
    @type pidevice : pipython.gcscommands.GCSCommands
    @param axes : Axes to wait for as string or list/tuple, or None to wait for all axes.
    @param timeout : Timeout in seconds as float.
    @param predelay : Time in seconds as float until querying any state from controller.
    @param postdelay : Additional delay time in seconds as float after reaching desired state.
    @param polldelay : Delay time between polls in seconds as float.
    """
    if not isdeviceavailable([GCS2Commands, GCS21Commands], pidevice):
        raise TypeError('Type %s of pidevice is not supported!' % type(pidevice).__name__)

    axes = getaxeslist(pidevice, axes)
    if not axes:
        return
    waitonready(pidevice, timeout=timeout, predelay=predelay, polldelay=polldelay)
    maxtime = time() + timeout
    while not all([x > -1.0 for x in pidevice.qFPH(axes).values()]):
        if time() > maxtime:
            raise SystemError('waitonphase() timed out after %.1f seconds' % timeout)
        sleep(polldelay)
    sleep(postdelay)


# Too many arguments pylint: disable=R0913
def waitonwalk(pidevice, channels, timeout=300, predelay=0, postdelay=0, polldelay=0.1):
    """Wait until qOSN for channels is zero.
    @type pidevice : pipython.gcscommands.GCSCommands
    @param channels : Channel or list or tuple of channels to wait for motion to finish.
    @param timeout : Timeout in seconds as float.
    @param predelay : Time in seconds as float until querying any state from controller.
    @param postdelay : Additional delay time in seconds as float after reaching desired state.
    @param polldelay : Delay time between polls in seconds as float.
    """
    if not isdeviceavailable([GCS2Commands, GCS21Commands], pidevice):
        raise TypeError('Type %s of pidevice is not supported!' % type(pidevice).__name__)

    channels = channels if isinstance(channels, (list, set, tuple)) else [channels]
    if not channels:
        return
    maxtime = time() + timeout
    waitonready(pidevice, timeout=timeout, predelay=predelay, polldelay=polldelay)
    while not all(list(x == 0 for x in list(pidevice.qOSN(channels).values()))):
        if time() > maxtime:
            stopall(pidevice)
            raise SystemError('waitonwalk() timed out after %.1f seconds' % timeout)
        sleep(polldelay)
    sleep(postdelay)


# Too many arguments pylint: disable=R0913
def waitonoma(pidevice, axes=None, timeout=300, predelay=0, polldelay=0.1):
    """Wait on the end of an open loop motion of 'axes'.
    @type pidevice : pipython.gcscommands.GCSCommands
    @param axes : Axis as string or list/tuple of them to get values for or None to query all axes.
    @param timeout : Timeout in seconds as float.
    @param predelay : Time in seconds as float until querying any state from controller.
    @param polldelay : Delay time between polls in seconds as float.
    """
    if not isdeviceavailable([GCS2Commands, GCS21Commands], pidevice):
        raise TypeError('Type %s of pidevice is not supported!' % type(pidevice).__name__)

    axes = getaxeslist(pidevice, axes)
    if not axes:
        return
    numsamples = 5
    positions = []
    maxtime = time() + timeout
    waitonready(pidevice, timeout=timeout, predelay=predelay, polldelay=polldelay)
    while True:
        positions.append(list(pidevice.qPOS(axes).values()))
        positions = positions[-numsamples:]
        if len(positions) < numsamples:
            continue
        isontarget = True
        for vals in zip(*positions):
            isontarget &= sum([abs(vals[i] - vals[i + 1]) for i in range(len(vals) - 1)]) < 0.01
        if isontarget:
            return
        if time() > maxtime:
            stopall(pidevice)
            raise SystemError('waitonoma() timed out after %.1f seconds' % timeout)
        sleep(polldelay)


# Too many arguments pylint: disable=R0913
def waitontrajectory(pidevice, trajectories=None, timeout=300, predelay=0, postdelay=0, polldelay=0.1):
    """Wait until all 'trajectories' are done and all axes are on target.
    @type pidevice : pipython.gcscommands.GCSCommands
    @param trajectories : Integer convertible or list/tuple of them or None for all trajectories.
    @param timeout : Timeout in seconds as floatfor trajectory and motion.
    @param predelay : Time in seconds as float until querying any state from controller.
    @param postdelay : Additional delay time in seconds as float after reaching desired state.
    @param polldelay : Delay time between polls in seconds as float.
    """
    if not isdeviceavailable([GCS2Commands, GCS21Commands], pidevice):
        raise TypeError('Type %s of pidevice is not supported!' % type(pidevice).__name__)

    maxtime = time() + timeout
    waitonready(pidevice, timeout=timeout, predelay=predelay, polldelay=polldelay)
    while any(list(pidevice.qTGL(trajectories).values())):
        if time() > maxtime:
            stopall(pidevice)
            raise SystemError('waitontrajectory() timed out after %.1f seconds' % timeout)
        sleep(polldelay)
    waitontarget(pidevice, timeout=timeout, predelay=0, postdelay=postdelay, polldelay=polldelay)


def waitonmacro(pidevice, timeout=300, predelay=0, polldelay=0.1):
    """Wait until all macros are finished, then query and raise macro error.
    @type pidevice : pipython.gcscommands.GCSCommands
    @param timeout : Timeout in seconds as float.
    @param predelay : Time in seconds as float until querying any state from controller.
    @param polldelay : Delay time between polls in seconds as float.
    """
    if not isdeviceavailable([GCS2Commands, GCS21Commands], pidevice):
        raise TypeError('Type %s of pidevice is not supported!' % type(pidevice).__name__)

    maxtime = time() + timeout
    waitonready(pidevice, timeout=timeout, predelay=predelay, polldelay=polldelay)
    assert pidevice.HasqRMC() or pidevice.HasIsRunningMacro(), 'device does not support wait on macro'
    while True:
        if pidevice.HasqRMC() and not pidevice.qRMC().strip():
            break
        if pidevice.HasIsRunningMacro() and not pidevice.IsRunningMacro():
            break
        if time() > maxtime:
            stopall(pidevice)
            raise SystemError('waitonmacro() timed out after %.1f seconds' % timeout)
        sleep(polldelay)
    if pidevice.HasMAC_qERR():
        errmsg = pidevice.MAC_qERR().strip()
        if errmsg and int(errmsg.split('=')[1].split()[0]) != 0:
            raise GCSError(gcserror.E1012_PI_CNTR_ERROR_IN_MACRO, message=errmsg)


def stopall(pidevice, **kwargs):
    """Stop motion of all axes and mask the "error 10" warning.
    @type pidevice : pipython.gcscommands.GCSCommands
    @param kwargs : Optional arguments with keywords that are passed to sub functions.
    """
    if not isdeviceavailable([GCS2Commands, GCS21Commands], pidevice):
        raise TypeError('Type %s of pidevice is not supported!' % type(pidevice).__name__)

    pidevice.StopAll(noraise=True)
    waitonready(pidevice, **kwargs)  # there are controllers that need some time to halt all axes


def moveandwait(pidevice, axes, values=None, timeout=300):
    """Call MOV with 'axes' and 'values' and wait for motion to finish.
    @type pidevice : pipython.gcscommands.GCSCommands
    @param axes : Dictionary of axis:target or list/tuple of axes or axis.
    @param values : Optional list of values or value.
    @param timeout : Seconds as float until SystemError is raised.
    """
    if not isdeviceavailable([GCS2Commands, GCS21Commands], pidevice):
        raise TypeError('Type %s is not supported!' % type(pidevice).__name__)

    if not axes:
        return
    pidevice.MOV(axes, values)
    if isinstance(axes, dict):
        axes = list(axes.keys())
    waitontarget(pidevice, axes=axes, timeout=timeout)


def movetomiddle(pidevice, axes=None):
    """Move 'axes' to its middle positions but do not wait "on target".
    @type pidevice : pipython.gcscommands.GCSCommands
    @param axes : List/tuple of strings of axes to get values for or None to query all axes.
    """
    if not isdeviceavailable([GCS2Commands, GCS21Commands], pidevice):
        raise TypeError('Type %s of pidevice is not supported!' % type(pidevice).__name__)

    axes = getaxeslist(pidevice, axes)
    if not axes:
        return
    rangemin = pidevice.qTMN(axes)
    rangemax = pidevice.qTMX(axes)
    targets = {}
    for axis in axes:
        targets[axis] = rangemin[axis] + (rangemax[axis] - rangemin[axis]) / 2.0
    pidevice.MOV(targets)
