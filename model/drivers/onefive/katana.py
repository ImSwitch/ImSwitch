# -*- coding: utf-8 -*-
"""
Created on Tue Nov 5 09:28:55 2019

Katana Serial Driver

@author: STEDred
"""


import numpy as np
from lantz import Q_
from lantz import Feat
from lantz.drivers.legacy.serial import SerialDriver


class KatanaLaser(SerialDriver):
    """Driver for the OneFive Katana laser.
    Used to control the 775 nm laser via a RS232 interface.
    Commands defined in the laser manual, end with an LF statement.

    :param float intensity_max: specifies the max intensity threshold (in W).
    Used to protect sensitive hardware (SLM) from high intensities.
    Potentially remove this?
    """

    ENCODING = 'ascii'

    RECV_TERMINATION = '\n'
    SEND_TERMINATION = '\n'

    BAUDRATE = 38400
    BYTESIZE = 8
    PARITY = 'none'
    STOPBITS = 1

    #: flow control flags
    RTSCTS = False
    DSRDTR = False
    XONXOFF = False

    def query(self, arg):
        return super().query(arg)

    @Feat(read_once=True)
    def idn(self):
        """Get the product ID of the Katana.
        """
        return 'OneFive Katana 08HP 775 nm'

    def initialize(self):
        super().initialize()
        self.intensity_max = 3.1  # maximum power setting for the Katana
        self.power_setting = 1  # To change power with python (1) or knob (0)
        self.mode = 0  # Constant current (1) or constant power (0) mode
        self.triggerMode = 0  # Trigger: internal (0)
        self.enabled_state = 0  # Laser initially off (0)
        self.W = Q_(1, 'W')
        self.mW = Q_(1, 'mW')
        self.power_setpoint = 0  # Current laser power setpoint

        self.setPowerSetting(self.power_setting)
        self.setTriggerSource(self.triggerMode)
        self.setMode(self.mode)

    @Feat
    def status(self):
        """Current device status
        """
        return 'OneFive laser status'

    @Feat
    def enabled(self):
        """Check if laser emission is on
        """
        return self.enabled_state

    @enabled.setter
    def enabled(self, value):
        """Turn on (1) or off (0) laser emission
        """
        cmd = "le=" + str(int(value))
        self.query(cmd)
        self.enabled_state = value

    # LASER'S CONTROL MODE AND SET POINT

    @Feat
    def power_sp(self):
        """Check laser power set point (mW)
        """
        return float(self.query('lp?')[3:]) * 1000

    @power_sp.setter
    def power_sp(self, value):
        """Handles output power.
        Sends a RS232 command to the laser specifying the new intensity.
        """
        value = value / 1000  # Conversion from mW to W
        if(self.power_setting != 1):
            print("Knob mode: impossible to change power value.")
            return
        if(value < 0):
            value = 0
        if(value > self.intensity_max):
            value = self.intensity_max  # Too high intensity can damage SLM
        value = round(value, 3)
        cmd = "lp=" + str(value)
        self.query(cmd)
        self.power_setpoint = value

    @Feat
    def current_sp(self):
        """Check laser current
        """
        return float(self.query('li?')[3:])

    @current_sp.setter
    def current_sp(self, value):
        """Handles output current.
        Sends a RS232 command to the laser specifying the new current.
        """
        if(self.mode != 1):
            print("You can't set the current in constant power mode.")
            return
        if(value < 0):
            value = 0
        if(value > 10):
            value = 10
        value = round(value, 2)
        cmd = "li=" + str(value)
        self.query(cmd)

    # LASER'S CURRENT STATUS

    @property
    def maxPower(self):
        """To get the maximum output power (mW)
        """
        return self.intensity_max * 1000

    def setPowerSetting(self, manual=1):
        """Power can be changed via this interface (1).
        Power has to be changed by turning the knob (manually) (0).
        """
        if(manual != 1 and manual != 0):
            print("setPowerSetting: invalid argument")
            self.power_setting = 0
        self.power_setting = manual
        cmd = "lps=" + str(manual)
        self.query(cmd)

    def setMode(self, value):
        """Constant current mode (0) or constant power mode (1)
        """
        if(value != 1 and value != 0):
            print("Wrong value")
            return
        self.mode = value
        cmd = "lip=" + str(value)
        self.query(cmd)

    @Feat
    def frequency(self, value):
        """Sets the pulse frequency in MHz
        """
        if(value < 18 or value > 80):
            print("invalid frequency values.")
            return
        value *= 10**6
        cmd = "lx_freq=" + str(value)
        self.query(cmd)

    def setTriggerSource(self, source):
        """Internal frequency generator (0)
        External trigger source for adjustable trigger level (1), Tr-1 In
        External trigger source for TTL trigger (2), Tr-2 In
        """
        if(source != 0 and source != 1 and source != 2):
            print("invalid source for trigger")
            return
        cmd = "lts=" + str(source)
        self.query(cmd)
        self.triggerMode = source

    def setTriggerLevel(self, value):
        """Defines the trigger level in Volts, between -5 and 5V, for source(1)
        """
        if(np.absolute(value) > 5):
            print("incorrect value")
            return
        if(self.triggerMode != 1):
            print("Please change trigger source.")
            return
        value = round(value, 2)
        cmd = "ltll=" + str(value)
        self.query(cmd)

    # The get... methods return a string giving information about the laser

    def getPower(self):
        """Returns internally measured laser power
        """
        return str(float(self.query('lpa?')[4:]))

    def getMode(self):
        """Returns mode of operation: constant current (1) or power (0)
        """
        return self.query('lip?')

    def close(self):
        self.finalize()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Test Katana HRI')
    parser.add_argument('-i', '--interactive', action='store_true',
                        default=False, help='Show interactive GUI')
    parser.add_argument('-p', '--port', type=str, default='COM8',
                        help='Serial port to connect to')

    args = parser.parse_args()
    with KatanaLaser('COM8') as inst:
        if args.interactive:
            from lantz.ui.qtwidgets import start_test_app
            start_test_app(inst)
        else:
            # Add your test code here
            print('Non interactive mode')
