# -*- coding: utf-8 -*-
"""
Created on Wed Jan 13 11:57:00 2021

@author: jonatanalvelid
"""


class LeicaDMIManager:
    def __init__(self, name, *args, **kwargs):
        #super().__init__(name=name, initialPosition=0)
        # TODO: the following does not work now, as there is no controller trying to load this manager as of now. 
        self._rs232Manager = kwargs['rs232sManager']._subManagers[positionerInfo.managerProperties['rs232device']]
        cmd = '71002'
        print(self._rs232Manager.send(cmd))  # print serial no of dmi stand

    def move(self, value, *args):
        if not int(value) == 0:
            cmd = '71024 ' + str(int(value)))
            if int(value) > 132:
                print('Warning: Step bigger than 500nm.')
            self._rs232Manager.send(cmd)

        self._position = self._position + value
        return self._position

    def setPosition(self, value, *args):
        cmd = '71022 ' + str(int(value))
        self._rs232Manager.send(cmd)

        self._position = value
        return self._position

    def position(self, *args):
        cmd = '71023'
        return returnMod(self._rs232Manager.send(cmd))

    def returnMod(self, reply):
        return reply[6:]

    def motCorrPos(self, value):
        """ Absolute mot_corr position movement. """
        movetopos = int(round(value*93.83))
        cmd = '47022 -1 ' + str(movetopos)
        self._rs232Manager.send(cmd)