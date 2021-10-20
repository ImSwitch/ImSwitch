import serial
import time
import re
import numpy as np
try:
    import pandas as pd
except:
    print("no pandas installed..")
    
class GrblDriver:
    """Class for interfacing with GRBL loaded on an Arduino Uno.Arduino

    NOTE: GRBL config.h had to be modified in order to make GRBL v1.1 compatible
    with the arduino shield (https://blog.protoneer.co.nz/arduino-cnc-shield/).
    Pin D12 is by default used for spindle control.  Comment the line (line339)
    to disable spindle control so that z-limit switch is on the right pin.

    ''' OPTIMAL SETTINGS:
        ok
        >>> $$
        $0 = 10    (Step pulse time, microseconds)
        $1 = 255    (Step idle delay, milliseconds)
        $2 = 144    (Step pulse invert, mask)
        $3 = 0    (Step direction invert, mask)
        $4 = 0    (Invert step enable pin, boolean)
        $5 = 0    (Invert limit pins, boolean)
        $6 = 0    (Invert probe pin, boolean)
        $10 = 2    (Status report options, mask)
        $11 = 0.010    (Junction deviation, millimeters)
        $12 = 0.000    (Arc tolerance, millimeters)
        $13 = 0    (Report in inches, boolean)
        $20 = 0    (Soft limits enable, boolean)
        $21 = 0    (Hard limits enable, boolean)
        $22 = 1    (Homing cycle enable, boolean)
        $23 = 0    (Homing direction invert, mask)
        $24 = 50.000    (Homing locate feed rate, mm/min)
        $25 = 100.000    (Homing search seek rate, mm/min)
        $26 = 250    (Homing switch debounce delay, milliseconds)
        $27 = 0.100    (Homing switch pull-off distance, millimeters)
        $30 = 1000    (Maximum spindle speed, RPM)
        $31 = 0    (Minimum spindle speed, RPM)
        $32 = 0    (Laser-mode enable, boolean)
        $100 = 780.000    (X-axis travel resolution, step/mm)
        $101 = 780.000    (Y-axis travel resolution, step/mm)
        $102 = 5000.000    (Z-axis travel resolution, step/mm)
        $110 = 200.000    (X-axis maximum rate, mm/min)
        $111 = 200.000    (Y-axis maximum rate, mm/min)
        $112 = 200.000    (Z-axis maximum rate, mm/min)
        $120 = 10.000    (X-axis acceleration, mm/sec^2)
        $121 = 10.000    (Y-axis acceleration, mm/sec^2)
        $122 = 5000.000    (Z-axis acceleration, mm/sec^2)
        $130 = 200.000    (X-axis maximum travel, millimeters)
        $131 = 200.000    (Y-axis maximum travel, millimeters)
        $132 = 200.000    (Z-axis maximum travel, millimeters)
        ok
        **** Connection closed ****
    """
    
    
    def __init__(self, address='/dev/ttyACM0'):
        try:
            self.ser = serial.Serial(address, baudrate=115200, timeout=0.01)
            self.is_connected = True
        except:
            print("No stage connected - Wrong Port?")
            self.is_connected = False
        self.waittimeout = 0.01
        self.is_debug = False
        
        # illumination settings
        self.laser_intensity = 0
        self.led_state = 0
        self.positions = (0,0,0)
        self.stepdivider = 1000

        #initialize and wait for grbl to wake up
        self._write('\r\n\r\n')
        time.sleep(2)
        if self.is_connected: self.ser.reset_input_buffer()

        
        self.limit_x_max = 1000
        self.limit_y_max = 1000
        self.limit_z_max = -1000

        # x-motor configuration
        self.xconfig = {
            'steps/mm':780., #<--resolutoin
            'mm/sec2': 10, #<--acceleration
            'mm/min': 200 #<--max speed
            }
        
        #map x settings to grbl commands
        self.xsettingsmap = {
            'steps/mm':'$100',
            'mm/min':'$110', #max rate, not constant speed
            'mm/sec2':'$120' #accel
        }

        # y-motor configuration
        self.yconfig = {
            'steps/mm':780., #<--resolutoin
            'mm/sec2': 10, #<--acceleration
            'mm/min': 200 #<--max speed
            }
        
        #map y settings to grbl commands
        self.ysettingsmap = {
            'steps/mm':'$101',
            'mm/min':'$111', #max rate, not constant speed
            'mm/sec2':'$121' #accel
        }

        # Z-motor configuration
        self.zconfig = {
            'steps/mm':5000, #<--resolutoin
            'mm/sec2': 200, #<--acceleration
            'mm/min': 200 #<--max speed
            }
            
        #map z settings to grbl commands
        self.zsettingsmap = {
            'steps/mm':'$102',
            'mm/min':'$112', #max rate, not constant speed
            'mm/sec2':'$122' #accel
        }

        #internal, to write to fit into grbl's interface
        self._update_writesettings()

        self.globalconfig = {
            1:25, #ms to wait before going idle (255=don't disable steppers)
            5:0,  #set NO limit switch
            20:0, # enable soft limit switch (stop immediately) # changed to off 1.31.19 after crash during data collection
            21:0, # enable hard limit switch (stop immediately) # changed to off 1.31.19 after crash during data collection
            22:1, # enable homing cycle
            24:50, # homing speed fine
            25:100, # homing speed
            3:0,    # inverse Direction of X motor
            27:0.1, # (Homing switch pull-off distance, millimeters)
            30:1024, # resolution PWM
            31:0, # minimum spindle speed
            32:0# enable laser mode (Has to be 0!)


        }
        
    def _update_writesettings(self):
        self.xwritesettings={
            'steps/mm':self.xconfig['steps/mm'],
            'mm/min':self.xconfig['mm/min'],
            'mm/sec2':self.xconfig['mm/sec2']
        }
        self.ywritesettings={
            'steps/mm':self.yconfig['steps/mm'],
            'mm/min':self.yconfig['mm/min'],
            'mm/sec2':self.yconfig['mm/sec2']
        }
        self.zwritesettings={
            'steps/mm':self.zconfig['steps/mm'],
            'mm/min':self.zconfig['mm/min'],
            'mm/sec2':self.zconfig['mm/sec2']
        }

    def write_global_config(self, wait=0.02):
        """Should only need to be run at initial setup.  Configures
        global options like homing speed, limit switch behavior."""
        if self.is_connected:
            self.ser.reset_input_buffer()
            for k,v in self.globalconfig.items():
                self._write('${}={}'.format(k,v))
                time.sleep(wait) #longer wait time to write to EEPROM
            resp = self._read_buffer()
            for r in resp:
                if(r != 'ok'):
                    if self.is_debug:  print('Ok not received after attempted write.')
        
    def _write_settings(self, settings, settingsmap, wait=0.5):
        """Utility function to write motor config settings to GRBL"""
        #TODO: make this only write commands that have changed,
        #to save on the number of writes to EEPROM
        if self.is_connected:
            self.ser.reset_input_buffer()
            for s, v in settings.items():
                self._write(settingsmap[s]+'={:.3f}'.format(v))
                time.sleep(wait) #longer wait time to write to EEPROM
            resp = self._read_buffer()
            for r in resp:
                if(r != 'ok'):
                    if self.is_debug: print('Ok not received after attempted write.')
            
    def write_all_settings(self):
        """Write settings for all of the motors to GRBL"""
        if self.is_connected:
            self._update_writesettings()
            maps = (self.xsettingsmap, self.ysettingsmap, self.zsettingsmap)
            writemaps = (self.xwritesettings, self.ywritesettings, self.zwritesettings)
            for settingsmap, setting in zip(maps, writemaps):
                self._write_settings(setting, settingsmap)

    def verify_settings(self):
        """Verify that current GRBL settings match the desired config of this class"""
        if self.is_connected:
            settingsre = re.compile(r'(\$\d{1,3})=(\d{1,5}\.?\d{0,3})')
            
            self.ser.reset_input_buffer()
            
            self._write('$$')
            time.sleep(self.waittimeout)
            resp = self._read_buffer()
            maps = (self.xsettingsmap, self.ysettingsmap, self.zsettingsmap)
            writemaps = (self.xwritesettings, self.ywritesettings, self.zwritesettings)
            for settingsmap, checksettings in zip(maps, writemaps):
                # read settings specified in settingsmap
                settings = {}
                for s in resp:
                    m = settingsre.match(s)
                    if m is not None:
                        cmd, reading = m.groups()
                        for k, v in settingsmap.items():
                            if cmd == v:
                                settings[k] = float(reading)
                                
                # compare to checksettings to verify:
                for s, v in checksettings.items():
                    if settings[s] != checksettings[s]:
                        raise Exception(
                            ('Current setting for {} is {}, but {} is expected.'
                            ' Consider writing the settings again.'
                            ).format(s,v,settings[s]))

            #verify global config
            for s in resp:
                m = re.match(r'\$(\d*)=(\d*\.?\d*)',s)
                if m is not None:
                    cmd, reading = m.groups()
                    cmd = int(cmd)
                    reading = float(reading)
                    if cmd in self.globalconfig.keys():
                        if reading != self.globalconfig[cmd]:
                            raise Exception(('Current setting for global config ${} is {},'
                                'but {} is expected.').format(cmd,self.globalconfig[cmd],reading))

            
        return True
        
    def _write(self, command, flush=False):
        """Utility function, write string to GRBL"""
        if self.is_debug: print(command)
        if self.is_connected:
            self.ser.write(command.encode('ascii')+b'\r')
            if flush:
                self.ser.flushInput()
                self.ser.flushOutput()
        
    def _read_buffer(self, maxreads = 100):
        """Utility function, perform readlines into a list of readings
        from GRBL.  Useful to clear the read buffer."""
        resp = []
        if self.is_connected:
            i = 0
            while i < maxreads:
                msg = self.ser.readline()
                if msg == b'':
                    break
                try:
                    resp.append(msg.decode().strip())
                except:
                    if self.is_debug: print("Something went wrong while deconding the return message from GRBL")
                    self.ser.flush()
                    break
                time.sleep(self.waittimeout)
                i+=1
        return resp
    

    def _move(self, axis, steps, config, blocking = True, pingwait = 0.25):
        """Move axis with optional blocking"""
        pos = steps/self.stepdivider
        self._write('G90')
        self._write('G0 '+axis+str(pos))
        if blocking:
            time.sleep(self.waittimeout)
            while True:
                _status_report = self.get_status_report()
                if _status_report[0] == 'Idle': # break once done?
                    break
                time.sleep(pingwait)
            # currentsteps = self.get_positions()[axis]
            if currentsteps - steps < 1:
                if self.is_debug: print('Didn\'t get there! Stopped at {} even though {} was requested.'.format(currentsteps,steps))

    def shake_plate(self, d_shift=100, time_shake = 30):
        """let the plate shake"""
        time_start = time.time()
        position_now = self.positions
        while ((time.time()-time_start)<time_shake):
            if(0):
                ix = self.positions[0]
                iy = self.positions[1]
                self._write('G0 X'+str(ix)+'Y'+str(iy))
                self._write('G2 X'+str(ix)+'Y'+str(iy)+ ' I1 J'+str(radius))
            else:
                self.move_abs((position_now[0]-d_shift,position_now[1],position_now[2]), blocking = False, pingwait = 0.1)
                self.move_abs((position_now[0]-d_shift,position_now[1]-d_shift,position_now[2]), blocking = False, pingwait = 0.1)
                self.move_abs((position_now[0]-d_shift,position_now[1]-d_shift,position_now[2]), blocking = False, pingwait = 0.1)
                self.move_abs((position_now[0],position_now[1],position_now[2]), blocking = False, pingwait = 0.1)


    def move_rel(self, position_rel=(0,0,0), blocking = True, pingwait = 0.25):
        """Move axises relaitve to current position"""
        self.move_xyz(position_rel, blocking=blocking, config="rel")
        

    def move_abs(self, position_rel=(0,0,0), blocking = True, pingwait = 0.25):
        """Move axises absolute"""
        self.move_xyz(position_rel, blocking=blocking, config="abs")
        
        
    def move_xyz(self, position=(0,0,0), blocking = True, pingwait = 0.25, config="abs"):
        """Move axis with optional blocking"""
        self.get_positions()
        if config == "abs":
            to_go = np.array(position)
        elif config == "rel":
            to_go = np.array((position[0]+self.positions[0],
                     position[1]+self.positions[1],
                     position[2]+self.positions[2]))
        
        
        self.positions = to_go 
        
        #self.positions = to_go
        if self.is_debug: print("Current position: "+str(self.positions))
        self._write('G90')
        self._write('G0 '+ 'X'+str(to_go[0]/self.stepdivider) +
                    'Y'+str(to_go[1]/self.stepdivider) +
                    'Z'+str(to_go[2]/self.stepdivider))
        if blocking:
            time.sleep(self.waittimeout)
            while True:
                _status_report = self.get_status_report()
                if self.is_debug: print("Status report: "+str(_status_report))
                if _status_report[0] == 'Idle': # break once done?
                    break
                time.sleep(pingwait)
        #self.get_positions()

                
    def xmove(self, steps, blocking = True):
        """Move x-axis motor by requested number of steps"""
        self._move('X', steps, self.xconfig, blocking=blocking)

    def ymove(self, steps, blocking = True):
        """Move y-axis motor by requested number of steps"""
        self._move('Y', steps, self.yconfig, blocking=blocking)

    def zmove(self, steps, blocking = True):
        """Move z-axis motor by requested number of steps"""
        self._move('Z', steps, self.zconfig, blocking=blocking)

    def home(self, offset=(0,0,0), blocking=True, pingwait=0.01, zhome=False):
        """Run the homing cycle for all axis"""
        self.reset_stage()
        self._write('$21=1')
        self._write('$H')
        time.sleep(pingwait)
        self._write("?")
        timestart = time.time()
        while(blocking):
            # wait until we reach the homing position
            _buf = self._read_buffer()
            if(time.time()-timestart)>20 or any("Home" in h for h in _buf):
                if self.is_debug: print(_buf)
                break
        self._write('$21=0')
        self.reset_stage()
        if zhome:
            self.zhome()
        self.zero_position()
        self.positions=(0,0,0)
            
    def zhome(self, steps=20000):
        """Run the homing cycle for the z-axis"""
        self.move_rel((0,0,steps), blocking = True)
        self.move_rel((0,0,-np.sign(steps)*100), blocking = True)        
        self.positions=(self.positions[0],self.positions[1],0)

    def get_status_report(self):
        """Retrieve and parse GRBL status report"""
        self.check_alarm(self._read_buffer())
        self._write('?')
        time.sleep(self.waittimeout)
        resp = self._read_buffer()
        self.check_alarm(resp)
        resp=''.join(resp)
        
        if len(resp)==0 or re.match(r'\<.*\>',resp) is None: 
            if self.is_debug: print('Error reading status report')
            state = ''
            status = {}
        else:
            resp = resp.strip('<>').split('|')
            state = resp.pop(0)
            status = {}
            for r in resp:
                s, v = re.match(r'(.*):(.*)',r).groups()
                status[s] = v
        return state, status
    
    def check_alarm(self, bufferoutput):
        for m in bufferoutput:
            if m.split(':')[0] == 'ALARM' or m.find("Alarm")>0:
                if self.is_debug: print('Alarm status! Probably hit a hard limit!'
                                'Perform soft_reset and alarm_reset to reset operation.')
                self.reset_stage()
                time.sleep(self.waittimeout)
                
    def reset_stage(self):
        self._write('$G')
        self._write('$X')
        self._write('?')
        msg=self._read_buffer()
        if self.is_debug: print(msg)
   
    def current_position(self):
        """get current positoins but as a list"""
        return self.positions

    def get_positions(self):
        """Request status and return positions in a dict"""
        state, status = self.get_status_report()
        posre = re.compile(r'(-?\d*\.\d*),(-?\d*\.\d*),(-?\d*\.\d*)')
        if self.is_debug: print("get positions;"+str(status))
        try:
            positions = [float(x) for x in posre.match(status['WPos']).groups()]
            configs = (self.xconfig,self.yconfig,self.zconfig)
            steppositions = []
            for p, c in zip(positions, configs):
                steppositions.append(p*self.stepdivider)
            #TODO: This seems to be not working properly. Check! 
            if self.is_debug: print("Assigning positions: "+str(steppositions))
            self.positions = steppositions 
        except Exception as e:
            if self.is_debug: print(str(e))
            if self.is_debug: print("Falling back to old position")
            steppositions = self.positions 
            
        keys = ['X','Y','Z']
        return dict(zip(keys,steppositions))
    
    def zero_position(self):
        """assign new zero position to current position"""
        self._write("G10 L20 P1 X0 Y0 Z0")
        self._write("G10 P0 L20 X0 Y0 Z0")

 
    def _human_readable_settings(self):
        """Utility function to read all GRBL settings that attempts to load
        csv file containing settings descriptions."""
        settingsre = re.compile(r'\$(\d{1,3})=(\d{1,5}\.?\d{0,3})')

        if self.is_connected: self.ser.reset_input_buffer()

        self._write('$$')
        time.sleep(self.waittimeout)
        resp = self._read_buffer()
        
        current = []
        for s in resp:
            m = settingsre.match(s)
            if m is not None:
                cmd, reading = m.groups()
                current.append([int(cmd), float(reading)])
                
        currentdf = pd.DataFrame(current,columns=['$-Code','Value'])
        
        try:
            settings_descriptions = pd.read_csv('C:/Users/Lab X-ray/Downloads/grbl_setting_codes_en_US.csv')
            currentdf = pd.merge(currentdf,settings_descriptions,on='$-Code')
        except OSError:
            print('Settings descriptions file not found, returning settings without descriptions.')
        
        return currentdf

    

    def set_laser_intensity(self, intensity):
        self.laser_intensity = intensity
        if self.led_state:
            prefix = "M4"
        else:
            prefix = "M3"
        
        cmd =  "G21 G90 " + prefix+" S"+str(self.laser_intensity)
        return self._write(cmd)

    def set_led(self, state=1):
        # state is either 1 or 0
        self.led_state = state
        if self.led_state:
            prefix = "M4"
        else:
            prefix = "M3"
        
        cmd =  "G21 G90 " + prefix + " S"+str(self.laser_intensity)
        return self._write(cmd)

    def soft_reset(self):
        """Perform soft-reset of GRBL.  Doesn't lose motor positions"""
        self._write('\x18')
        time.sleep(self.waittimeout)
        self._read_buffer()
        
    def controlled_stop(self, pingwait=0.25):
        """Perform stop with controlled deceleration to maintain motor positioning."""
        self._write('!')
        time.sleep(pingwait)
        while True:
            state,_=self.get_status_report()
            if state.split(':')[1] == '0':
                break
            time.sleep(pingwait)
        time.sleep(pingwait)
        self.soft_reset()

    def stop(self):
        """Emergency stop that stops all motion. Loses motor positioning."""
        self.soft_reset()

    def alarm_reset(self):
        """Reset 'alarm' status, usually after emergency stop or hard limit."""
        self._write('$X')

    def close(self):
        """Close GRBL serial connection"""
        self.ser.close()


