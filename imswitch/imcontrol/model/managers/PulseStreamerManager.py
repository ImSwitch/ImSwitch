"""
Created on Tue Oct 12 15:05:00 2021

@author: jacopoabramo
"""

from pulsestreamer import PulseStreamer, OutputState
from imswitch.imcommon.framework import Signal, SignalInterface
from imswitch.imcommon.model import initLogger

DIG_CH_MAX_NUMBER = 8
ANG_CH_MAX_NUMBER = 2

class PulseStreamerManager(SignalInterface):
    """ For interaction with Pulse Streamer 8/2 from Swabian Instruments. """

    sigScanBuilt = Signal(object, object)  # (scanInfoDict, deviceList)
    sigScanStarted = Signal()
    sigScanDone = Signal()

    sigScanBuildFailed = Signal()

    def __init__(self, setupInfo):
        super().__init__()
        self.__logger = initLogger(self)
        self.__setupInfo = setupInfo
        self.__ipAddress = setupInfo.pulseStreamer.ipAddress
        try:
            self.__pulseStreamer = PulseStreamer(self.__ipAddress)
        except:
            # todo: fill exception
            pass       

    def setDigital(self, channel, enable):
        """Function to set a digital channel output level.

        Args:
            channel (int, list): channel/list of channels to set.
            enable (int, bool): 0/False to disable output, 1/True to enable output.
        """
        if channel is None:
            raise PulseStreamerManagerError('Target has no digital channel assigned to it')
        elif not self._areChannelsOk(channel, DIG_CH_MAX_NUMBER):
            raise PulseStreamerManagerError(f'Target digital channels are out of bounds (min. is 0, max. is {DIG_CH_MAX_NUMBER-1})')
        else:
            if bool(enable):
                if isinstance(channel, list):
                    self.__pulseStreamer.constant(OutputState(channel))
                else:
                    self.__pulseStreamer.constant(OutputState([channel]))
            else:
                self.__pulseStreamer.constant(OutputState.ZERO())

    def setAnalog(self, channel, voltage, min_val=-1.0, max_val=1.0):
        """Function to set an analog channel output level

        Args:
            channel (int, list): channel/list of channels to set.
            voltage (float): voltage level to set
            min_val (float, optional): minimum output voltage; defaults to -1.0.
            max_val (float, optional): maximum output voltage; defaults to 1.0.
        """
        if channel is None:
            raise PulseStreamerManagerError('Target has no analog channel assigned to it')
        elif not self._areChannelsOk(channel, ANG_CH_MAX_NUMBER):
            raise PulseStreamerManagerError(f'Target analog channels are out of bounds (min. is 0, max. is {ANG_CH_MAX_NUMBER-1})')
        else:
            if voltage > 0.0:
                voltage = max(voltage, max_val)
            else:
                voltage = max(voltage, min_val)
            if isinstance(channel, list):
                self.__pulseStreamer.constant(OutputState([], voltage, voltage))
            else:
                if channel == 0:
                    self.__pulseStreamer.constant(OutputState([], voltage, 0.0))
                else:
                    self.__pulseStreamer.constant(OutputState([], 0.0, voltage))

    def _areChannelsOk(self, channel, upper_bound) -> bool:
        """Checks the validity of the selected channel (or channels)

        Args:
            channel (int, list): channel/list of channels to verify
            upper_bound (int): upper limit for channel check

        Returns:
            bool: True if channels are OK, else False
        """
        if isinstance(channel, list):
            if all(ch >= upper_bound for ch in channel):
                return False
            else:
                return True
        else:
            if channel >= upper_bound:
                return False
            else:
                return True
            

class PulseStreamerManagerError(Exception):
    """ Exception raised when error occurs in PulseStreamerManager """

    def __init__(self, message):
        self.message = message
