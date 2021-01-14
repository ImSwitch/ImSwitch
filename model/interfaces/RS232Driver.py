# -*- coding: utf-8 -*-
"""
Created on Thu Jan 13 10:00:00 2021

@author: jonatanalvelid
"""

from pyvisa import constants

from lantz.messagebased import MessageBasedDriver


class RS232Driver(MessageBasedDriver):
    """General RS232 driver."""

    #def __new__(cls, port, settings, *args, **kwargs):
    #    cls.DEFAULTS = {'ASRL': {'write_termination': settings["send_termination"],
    #                             'read_termination': settings["recv_termination"],
    #                             'baud_rate': settings["baudrate"],
    #                             'bytesize': settings["bytesize"],
    #                             'parity': settings["parity"],
    #                             'stop_bits': settings["stopbits"],
    #                             'encoding': settings["encoding"],
    #                            }}
    #    return super(RS232Driver, cls).__new__(cls, *args, **kwargs)
    
    def __init__(self, port, *args):
        super().__init__(port)

    @classmethod
    def getDefaults(cls, settings):
        defaults = {'ASRL': {'write_termination': settings["send_termination"],
                                 'read_termination': settings["recv_termination"],
                                 'baud_rate': settings["baudrate"],
                                 'bytesize': settings["bytesize"],
                                 'parity': settings["parity"],
                                 'stop_bits': settings["stopbits"],
                                 'encoding': settings["encoding"],
                                }}
        return defaults

    def query(self, arg):
        return super().query(arg)

    def initialize(self):
        super().initialize()
        return 'initialized?'

    def close(self):
        self.finalize()

def generateDriverClass(settings):
    class GeneratedDriver(RS232Driver):
        DEFAULTS = RS232Driver.getDefaults(settings)

    return GeneratedDriver


#settings = {'ASRL': {'write_termination': '\r',
#                        'read_termination': '\r',
#                        'baud_rate': 115200,
#                        'bytesize': 8,
#                        'parity': constants.Parity.none,
#                        'stop_bits': constants.StopBits.one,
#                        'encoding': 'ascii',
#                        }}
#
#DriverClass = generateDriverClass(settings)
#rs232port = DriverClass('TCPIP::localhost::5678::SOCKET')
#rs232port.initialize()