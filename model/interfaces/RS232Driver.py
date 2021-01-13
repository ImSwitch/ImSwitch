# -*- coding: utf-8 -*-
"""
Created on Thu Jan 13 10:00:00 2021

@author: jonatanalvelid
"""

from lantz.messagebased import MessageBasedDriver


class RS232Driver(MessageBasedDriver):
    """General RS232 driver."""
    def __init__(self, settings, **kwargs):

        self.DEFAULTS = {'ASRL': {'write_termination': settings["send_termination"],
                                    'read_termination': settings["recv_termination"],
                                    'baud_rate': settings["baudrate"],
                                    'bytesize': settings["bytesize"],
                                    'parity': settings["parity"],
                                    'stop_bits': settings["stopbits"],
                                    'encoding': settings["encoding"],
                                    }}

        #self.ENCODING = settings["encoding"]
        #self.RECV_TERMINATION = settings["recv_termination"]
        #self.SEND_TERMINATION = settings["send_termination"]
        #self.BAUDRATE = settings["baudrate"]
        #self.BYTESIZE = settings["bytesize"]
        #self.PARITY = settings["parity"]
        #self.STOPBITS = settings["stopbits"]
        # flow control flags
        #self.RTSCTS = settings["rtscts"]
        #self.DSRDTR = settings["dsrdtr"]
        #self.XONXOFF = settings["xonxoff"]

    def query(self, arg):
        return super().query(arg)

    def initialize(self):
        super().initialize()
        return 'initialized?'

    def close(self):
        self.finalize()
