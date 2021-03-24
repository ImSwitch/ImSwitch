# -*- coding: utf-8 -*-
"""
Created on Thu Jan 13 10:23:00 2021

@author: jonatanalvelid
"""


class RS232Manager():
    """General RS232Manager."""
    def __init__(self, rs232Info, name, **kwargs):
        self._settings = rs232Info.managerProperties
        self._name = name
        self._port = rs232Info.managerProperties['port']
        self._rs232port = getRS232port(self._port, self._settings)

    def send(self, arg):
        return self._rs232port.query(arg)

    def close(self):
        self._rs232port.close()


def getRS232port(port, settings):
    try:
        #print('1')
        from model.interfaces.RS232Driver import RS232Driver, generateDriverClass
        #print('2')
        DriverClass = generateDriverClass(settings)
        #print('3')
        rs232port = DriverClass(port)
        #print('4')
        rs232port.initialize()
        #print('5')
        return rs232port
    except:
        print('Initializing mock RS232 port')
        from model.interfaces.mockers import MockRS232Driver
        return MockRS232Driver(port, settings)
