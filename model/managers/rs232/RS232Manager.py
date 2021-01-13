# -*- coding: utf-8 -*-
"""
Created on Thu Jan 13 10:23:00 2021

@author: jonatanalvelid
"""


class RS232Manager():
    """General RS232Manager."""
    def __init__(self, rs232Info, name, **kwargs):
        self._settings = rs232Info.managerProperties
        self._rs232port = getRS232port(self._settings)
        self.name = name

    def send(self, arg):
        return self._rs232port.query(arg)

    def close(self):
        self._rs232port.close()


def getRS232port(settings):
    try:
        from model.interfaces.RS232Driver import RS232Driver
        print('Trying to import RS232Driver')
        rs232port = RS232Driver(settings)
        rs232port.initialize()
        print('Initialized RS232 port')
        return rs232port
    except:
        print('Initializing mock RS232 port')
        from model.interfaces.mockers import MockRS232Driver
        return MockRS232Driver(settings)
