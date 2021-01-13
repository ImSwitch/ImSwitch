# -*- coding: utf-8 -*-
"""
Created on Tue Jan 13 08:47:00 2021

@author: jonatanalvelid
"""


class MHXYStage_new:
    """Driver for the Marzhauser XY-stage."""
    def __init__(self, **kwargs):
        

    def query(self, arg):
        return super().query(arg)

    @Feat(read_once=True)
    def idn(self):
        """Read serial number of stage. """
        sernum = str(self.query('?readsn'))
        print(sernum)
        return sernum

    def initialize(self):
        super().initialize()
        self.query('!dim 1 1')  # Set the dimensions of all commands to um
        time.sleep(0.1)
        self.query('!resolution 6')  # Set the read position resolution to nm
        time.sleep(0.1)
        self.query('!clim 0 0 25000')  # Set circular limits to the movement
        # range, centered at 0,0 with a radius of 25000 µm (25 mm).
        time.sleep(0.1)
        print(self.query('save'))  # Save settings to the controller
        time.sleep(0.1)
        #print(self.query('moc'))  # Move the stage to the center position, in case it
        # has moved from there after being switched off. Eventually change this
        # to the actual center of most cover slips! 
        #time.sleep(0.1)

    # XY-POSITION READING AND MOVEMENT

    @Feat()
    def absX(self):
        """ Read absolute X position, in um. """
        return float(self.query('?pos x'))

    @Feat()
    def absY(self):
        """ Read absolute Y position, in um. """
        return float(self.query('?pos y'))

    @Action()
    def move_relX(self, value):
        """ Relative X position movement, in um. """
        self.query('mor x ' + str(float(value)))

    @Action()
    def move_relY(self, value):
        """ Relative Y position movement, in um. """
        self.query('mor y ' + str(float(value)))

    @Action(limits=(100,))
    def move_absX(self, value):
        """ Absolute X position movement, in um. """
        self.query('moa x ' + str(float(value)))

    @Action(limits=(100,))
    def move_absY(self, value):
        """ Absolute Y position movement, in um. """
        self.query('moa y ' + str(float(value)))

    # CONTROL/STATUS/LIMITS

    @Feat()
    def circLimit(self):
        """ Circular limits, in terms of X,Y center and radius. """
        return self.query('?clim')

    @circLimit.setter
    def circLimit(self, xpos, ypos, radius):
        """ Set circular limits, in terms of X,Y center and radius. """
        self.query('!clim ' + str(float(xpos)) + ' ' +
                   str(float(ypos)) + ' ' + str(float(radius)))
     
    @Action()
    def function_press(self):
        """ Absolute X position movement, in um. """
        button_status = self.query('?keyl').split()
        button_status = list(map(int, button_status))
        return button_status

    def close(self):
        self.finalize()
