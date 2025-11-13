#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Provide GCS functions to control a PI device."""
# Trailing newlines pylint: disable=C0305

from logging import warning
# Wildcard import pipython.gcscommands_helpers pylint: disable=W0401
# Unused import platform from wildcard import pylint: disable=W0614
from ..common.gcscommands_helpers import *
from ..common.gcsbasecommands import GCSBaseCommands

__signature__ = 0x4a6b18b1a5369daecd79ad2a66b6fa6b

GCSFUNCTIONS = {
    'E-816': [
        'qERR', 'qI2C', 'qIDN', 'StopAll', 'BDR', 'qBDR', 'AVG', 'qAVG', 'SCH', 'qSCH', 'qSAI', 'MAC_BEG', 'MAC_START',
        'MAC_NSTART', 'MAC_DEL', 'MAC_DEF', 'MAC_END', 'MAC_qDEF', 'MAC_qFREE', 'qMAC', 'IsRunningMacro', 'DEL', 'WPA',
        'RST', 'qHLP', 'DCO', 'qDCO', 'MOV', 'MVR', 'qMOV', 'SVA', 'SVR', 'qSVA', 'MVT', 'qMVT', 'qDIP', 'qPOS', 'qVOL',
        'qOVF', 'qONT', 'SVO', 'qSVO', 'SWT', 'qSWT', 'WTO', 'SPA', 'qSPA',
    ],
    'HEXAPOD': [
        'qIDN', 'AAP', 'qCST', 'qECO', 'qERR', 'FAA', 'FAM', 'FAS', 'DMOV', 'DRV', 'FIO', 'FSA', 'FSC', 'FSM', 'FSN',
        'GetPosStatus', 'GetScanResult', 'HasPosChanged', 'INI', 'IsMoving', 'IsRecordingMacro', 'IsScanning',
        'MAC_BEG', 'MAC_DEL', 'MAC_END', 'MAC_qERR', 'MAC_START', 'MOV', 'MWG', 'NAV', 'NLM', 'PLM', 'qCST', 'qDRR',
        'qFSN', 'qHLP', 'qMAC', 'qNAV', 'qNLM', 'qPLM', 'qPOS', 'qSAI', 'qSAI_ALL', 'qSCT', 'qSGA', 'qSPA', 'qSPI',
        'qSSL', 'qSST', 'qSVO', 'qTAV', 'qVEL', 'qVER', 'SCT', 'SGA', 'SPI', 'SSL', 'SST', 'STP', 'SVO', 'TAV', 'VEL',
        'VMO',
    ],
    'TRIPOD': [
        'qIDN', 'AAP', 'qCST', 'qECO', 'qERR', 'FAA', 'FAM', 'FAS', 'DMOV', 'DRV', 'FIO', 'FSA', 'FSC', 'FSM', 'FSN',
        'GetPosStatus', 'GetScanResult', 'HasPosChanged', 'INI', 'IsMoving', 'IsRecordingMacro', 'IsScanning',
        'MAC_BEG', 'MAC_DEL', 'MAC_END', 'MAC_qERR', 'MAC_START', 'MOV', 'MWG', 'NAV', 'NLM', 'PLM', 'qCST', 'qDRR',
        'qFSN', 'qHLP', 'qMAC', 'qNAV', 'qNLM', 'qPLM', 'qPOS', 'qSAI', 'qSAI_ALL', 'qSCT', 'qSGA', 'qSPA', 'qSPI',
        'qSSL', 'qSST', 'qSVO', 'qTAV', 'qVEL', 'qVER', 'SCT', 'SGA', 'SPI', 'SSL', 'SST', 'STP', 'SVO', 'TAV', 'VEL',
        'VMO',
    ],
    'C-702.00': [
        'IsMoving', 'HasPosChanged', 'IsControllerReady', 'IsRunningMacro', 'StopAll', 'SystemAbort', 'q*IDN', 'ACC',
        'qACC', 'CCL', 'qCCL', 'CLR', 'CLS', 'CST', 'qCST', 'qCSV', 'CTO', 'qCTO', 'DEL', 'DFF', 'qDFF', 'DFH', 'qDFH',
        'DIO', 'qDIO', 'DRC', 'qDRC', 'qDRR', 'DRT', 'qDRT', 'DSP', 'qDSP', 'qECO', 'qERR', 'GOH', 'qHDR', 'HID',
        'qHID', 'qHLP', 'HLT', 'IFC', 'qIFC', 'IFS', 'qIFS', 'INI', 'ITD', 'qLIM', 'MAC', 'qMAC', 'MNL', 'MOV', 'qMOV',
        'MPL', 'MSG', 'MVR', 'MVS', 'qMVS', 'NLM', 'qNLM', 'qONT', 'PLM', 'qPLM', 'POS', 'qPOS', 'RBT', 'REF', 'qREF',
        'RON', 'qRON', 'RST', 'RTR', 'qRTR', 'SAI', 'qSAI', 'SAV', 'SCA', 'qSCA', 'SMO', 'qSMO', 'SPA', 'qSPA', 'SSL',
        'qSSL', 'qSSN', 'SSP', 'SST', 'qSST', 'qSTA', 'STP', 'SVO', 'qSVO', 'qTAC', 'qTCV', 'qTIM', 'qTIO', 'qTMN',
        'qTMX', 'qTNR', 'TRO', 'qTRO', 'qTSP', 'qTVI', 'VEL', 'qVEL', 'qVER', 'VMO', 'qVST', 'WAA', 'WAI', 'WAV',
        'qWAV', 'WGO', 'qWGO', 'WPA', 'WSL', 'qWSL',
    ]
}


class GCS2Commands(GCSBaseCommands):
    """Provide functions for GCS commands and communicate with PI controller."""

    def __init__(self, msgs):
        """Wrapper for PI GCS DLL.
        @type msgs : pipython.pidevice.gcsmessages.GCSMessages
        """
        debug('create an instance of GCS2Commands(msgs=%s)', str(msgs))
        super(GCS2Commands, self).__init__(msgs)

    def __str__(self):
        return 'GCS2Commands(msgs=%s)' % str(self._msgs)

    #    @property
    #    def connectionid(self):
    #        """Get ID of current connection as integer."""
    #        return super(GCS2Commands, self).connectionid

    @property
    def devname(self):
        """Return device name from its IDN string."""
        if self._name is None:
            idn = self.qIDN().upper()
            if 'PI-E816' in idn:
                self._name = 'E-816'
            elif 'DIGITAL PIEZO CONTROLLER' in idn:
                self._name = 'E-710'
            else:
                self._name = idn.split(',')[1].strip()
            debug('GCS2Commands.devname: set to %r', self._name)
        return self._name

    @devname.setter
    def devname(self, devname):
        """Set device name as string, only for testing."""
        super(GCS2Commands, self.__class__).devname.fset(self, devname)
        warning('controller name is coerced to %r', self._name)

    @devname.deleter
    def devname(self):
        """Reset device name."""
        self._name = None
        super(GCS2Commands, self.__class__).devname.fdel(self)
        debug('GCS2Commands.devname: reset')

    @property
    def funcs(self):
        """Return list of supported GCS functions."""
        if self._funcs is None:
            if self.devname in GCSFUNCTIONS:
                self._funcs = GCSFUNCTIONS[self.devname]
            else:
                self._funcs = getsupportedfunctions(self.qHLP())
        return self._funcs

    @funcs.deleter
    def funcs(self):
        """Reset list of supported GCS functions."""
        debug('GCS2Commands.funcs: reset')
        super(GCS2Commands, self.__class__).funcs.fdel(self)

    def paramconv(self, paramdict):
        """Convert values in 'paramdict' to according type in qHPA answer.
        @paramdict: Dictionary of {item: {param: value}}.
        @return: Dictionary of {item: {param: value}}.
        """
        self.initparamconv()

        for item in paramdict:
            for param in paramdict[item]:
                if param in self._settings['paramconv']:
                    paramdict[item][param] = self._settings['paramconv'][param](paramdict[item][param])

        return paramdict

    def initparamconv(self):
        """Initialize paramconv .
        """
        if not self._settings['paramconv']:
            for line in self.qHPA().splitlines():
                if '=' not in line:
                    continue
                paramid = int(line.split('=')[0].strip(), base=16)
                convtype = line.split()[3].strip()
                if convtype.upper() == 'INT':
                    self._settings['paramconv'][paramid] = self._int
                elif convtype.upper() == 'FLOAT':
                    self._settings['paramconv'][paramid] = self._float
                elif convtype.upper() in ('CHAR', 'STRING'):
                    continue
                else:
                    raise KeyError('unknown parameter type %r' % convtype)

    # GCS FUNCTIONS ### DO NOT MODIFY THIS LINE !!! ###############################################

    # CODEGEN BEGIN ### DO NOT MODIFY THIS LINE !!! ###############################################


