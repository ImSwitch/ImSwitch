# -*- coding: utf-8 -*-
"""
Created on Tue Aug 12 20:02:08 2014

@author: Federico Barabas
"""

import ctypes
import ctypes.util
import numpy as np

import logging

from lantz import Driver
from lantz import Q_

from lantz import Action, Feat

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s',
                    datefmt='%Y-%d-%m %H:%M:%S')


class constants:

    def __init__(self):
        self.GND = 0


class MockLaser(Driver):

    def __init__(self):
        super().__init__()

        self.mW = Q_(1, 'mW')

        self.enabled = False
        self.power_sp = 0 * self.mW

    @property
    def idn(self):
        return 'Simulated laser'

    @property
    def status(self):
        """Current device status
        """
        return 'Simulated laser status'

    # ENABLE LASER
    @property
    def enabled(self):
        """Method for turning on the laser
        """
        return self.enabled_state

    @enabled.setter
    def enabled(self, value):
        self.enabled_state = value

    # LASER'S CONTROL MODE AND SET POINT

    @property
    def power_sp(self):
        """To handle output power set point (mW) in APC Mode
        """
        return self.power_setpoint

    @power_sp.setter
    def power_sp(self, value):
        self.power_setpoint = value

    # LASER'S CURRENT STATUS

    @property
    def power(self):
        """To get the laser emission power (mW)
        """
        return 55555 * self.mW

    def enter_mod_mode(self):

        pass

    @property
    def digital_mod(self):
        """digital modulation enable state
        """
        return True

    @digital_mod.setter
    def digital_mod(self, value):
        pass

    def mod_mode(self):
        """Returns the current operating mode
        """
        return 0

    @Feat(units='mW')
    def power_mod(self):
        return 0

    @power_mod.setter
    def power_mod(self, value):
        pass

    def query(self, text):
        return 0


class HMockCamData():

    # __init__
    #
    # Create a data object of the appropriate size.
    #
    # @param size The size of the data object in bytes.
    #
    def __init__(self, size):
        self.np_array = np.random.randint(1, 65536, int(size))
        self.size = size

    # __getitem__
    #
    # @param slice The slice of the item to get.
    #
    def __getitem__(self, slice):
        return self.np_array[slice]

    # copyData
    #
    # Uses the C memmove function to copy data from an address in memory
    # into memory allocated for the numpy array of this object.
    #
    # @param address The memory address of the data to copy.
    #
    def copyData(self, address):
        ctypes.memmove(self.np_array.ctypes.data, address, self.size)

    # getData
    #
    # @return A numpy array that contains the camera data.
    #
    def getData(self):
        return self.np_array

    # getDataPtr
    #
    # @return The physical address in memory of the data.
    #
    def getDataPtr(self):
        return self.np_array.ctypes.data


class MockHamamatsu(Driver):

    def __init__(self):

        self.buffer_index = 0
        self.camera_id = 9999
        self.camera_model = b'Mock Hamamatsu camera'
        self.debug = False
        self.frame_x = 500
        self.frame_y = 500
        self.frame_bytes = self.frame_x * self.frame_y * 2
        self.last_frame_number = 0
        self.properties = {}
        self.max_backlog = 0
        self.number_image_buffers = 0
        self.hcam_data = []

        self.s = Q_(1, 's')

        # Open the camera.
#        self.camera_handle = ctypes.c_void_p(0)
#        self.checkStatus(dcam.dcam_open(ctypes.byref(self.camera_handle),
#                                        ctypes.c_int32(self.camera_id),
#                                        None),
#                         "dcam_open")
        # Get camera properties.
        self.properties = {'Name': 'MOCK Hamamatsu',
                           'exposure_time': 9999,  # * self.s,
                           'accumulation_time': 99999,  # * self.s,
                           'image_width': 2048,
                           'image_height': 2048,
                           'image_framebytes': 8,
                           'subarray_hsize': 2048,
                           'subarray_vsize': 2048,
                           'subarray_mode': 'OFF',
                           'timing_readout_time': 9999,
                           'internal_frame_rate': 9999,
                           'internal_frame_interval': 9999}

        # Get camera max width, height.
        self.max_width = self.getPropertyValue("image_width")[0]
        self.max_height = self.getPropertyValue("image_height")[0]

    def captureSetup(self):
        ''' (internal use only). This is called at the start of new acquisition
        sequence to determine the current ROI and get the camera configured
        properly.'''
        self.buffer_index = -1
        self.last_frame_number = 0

        # Set sub array mode.
        self.setSubArrayMode()

        # Get frame properties.
        self.frame_x = int(self.getPropertyValue("image_width")[0])
        self.frame_y = int(self.getPropertyValue("image_height")[0])
        self.frame_bytes = self.getPropertyValue("image_framebytes")[0]

    def checkStatus(self, fn_return, fn_name="unknown"):
        ''' Check return value of the dcam function call. Throw an error if
        not as expected?
        @return The return value of the function.'''
        pass

    def getFrames(self):
        ''' Gets all of the available frames.

        This will block waiting for new frames even if there new frames
        available when it is called.

        @return [frames, [frame x size, frame y size]]'''
        frames = []

        for i in range(2):
            # Create storage
            hc_data = HMockCamData(self.frame_x * self.frame_y)
            frames.append(hc_data)

        return [frames, [self.frame_x, self.frame_y]]

    def getLast(self):
        hc_data = HMockCamData(self.frame_x * self.frame_y)
        return [hc_data, [self.frame_x, self.frame_y]]
        
    def getModelInfo(self):
        ''' Returns the model of the camera

        @param camera_id The (integer) camera id number.

        @return A string containing the camera name.'''
        return ('WARNING!: This is a Mock Version of the Hamamatsu Orca flash '
                'camera')

    def getProperties(self):
        ''' Return the list of camera properties. This is the one to call if you
        want to know the camera properties.

        @return A dictionary of camera properties.'''
        return self.properties

    def getPropertyAttribute(self, property_name):
        ''' Return the attribute structure of a particular property.

        FIXME (OPTIMIZATION): Keep track of known attributes?

        @param property_name The name of the property to get the attributes of.

        @return A DCAM_PARAM_PROPERTYATTR object.'''
        pass

    # getPropertyText
    #
    # Return the text options of a property (if any).
    #
    # @param property_name The name of the property to get the text values of.
    #
    # @return A dictionary of text properties (which may be empty).
    #
    def getPropertyText(self, property_name):
        pass

    # getPropertyRange
    #
    # Return the range for an attribute.
    #
    # @param property_name The name of the property (as a string).
    #
    # @return [minimum value, maximum value]
    #
    def getPropertyRange(self, property_name):
        pass

    # getPropertyRW
    #
    # Return if a property is readable / writeable.
    #
    # @return [True/False (readable), True/False (writeable)]
    #
    def getPropertyRW(self, property_name):
        pass

    # getPropertyVale
    #
    # Return the current setting of a particular property.
    #
    # @param property_name The name of the property.
    #
    # @return [the property value, the property type]
    #
    def getPropertyValue(self, property_name):

        prop_value = self.properties[property_name]
        prop_type = property_name

        return [prop_value, prop_type]

    # isCameraProperty
    #
    # Check if a property name is supported by the camera.
    #
    # @param property_name The name of the property.
    #
    # @return True/False if property_name is a supported camera property.
    #
    def isCameraProperty(self, property_name):
        if (property_name in self.properties):
            return True
        else:
            return False

    # newFrames
    #
    # Return a list of the ids of all the new frames since the last check.
    #
    # This will block waiting for at least one new frame.
    #
    # @return [id of the first frame, .. , id of the last frame]
    #
    def newFrames(self):

        # Create a list of the new frames.
        new_frames = [0]

        return new_frames

    # setPropertyValue
    #
    # Set the value of a property.
    #
    # @param property_name The name of the property.
    # @param property_value The value to set the property to.
    #
    def setPropertyValue(self, property_name, property_value):

        # Check if the property exists.
        if not (property_name in self.properties):
            return False

        # If the value is text, figure out what the
        # corresponding numerical property value is.

        self.properties[property_name] = property_value
#        print(property_name, 'set to:', self.properties[property_name])
#            if (property_value in text_values):
#                property_value = float(text_values[property_value])
#            else:
#                print(" unknown property text value:", property_value, "for",
#                      property_name)
#                return False
        return property_value

    # setSubArrayMode
    #
    # This sets the sub-array mode as appropriate based on the current ROI.
    #
    def setSubArrayMode(self):

        # Check ROI properties.
        roi_w = self.getPropertyValue("subarray_hsize")[0]
        roi_h = self.getPropertyValue("subarray_vsize")[0]
        self.properties['image_height'] = roi_h
        self.properties['image_width'] = roi_w

        # If the ROI is smaller than the entire frame turn on subarray mode
        if ((roi_w == self.max_width) and (roi_h == self.max_height)):
            self.setPropertyValue("subarray_mode", "OFF")
        else:
            self.setPropertyValue("subarray_mode", "ON")

    # startAcquisition
    #
    # Start data acquisition.
    #
    def startAcquisition(self):
        self.captureSetup()
        n_buffers = int((2.0 * 1024 * 1024 * 1024) / self.frame_bytes)
        self.number_image_buffers = n_buffers

        self.hcam_data = [HMockCamData(self.frame_x * self.frame_y)
                          for i in range(1, 2)]

    # stopAcquisition
    #
    # Stop data acquisition.
    #
    def stopAcquisition(self):
        pass

    # shutdown
    #
    # Close down the connection to the camera.
    #
    def shutdown(self):
        pass


class MockPZT(Driver):
    """Mock Driver for the nv401.
    """

    def __init__(self):
        super().__init__()
        self.pos = 0

    def query(self, command, *,
              send_args=(None, None), recv_args=(None, None)):
        return 'Mock PZT'

    @Feat(units='micrometer')
    def position(self):
        return self.pos

    @position.setter
    def position(self, value):
        self.pos = value

    @Action()
    def zero_position(self):
        self.pos = 0

    @Action(units='micrometer', limits=(100,))
    def moveAbsolute(self, value):
        self.pos = value

    @Action(units='micrometer')
    def moveRelative(self, value):
        self.pos = self.pos + value


class MockWebcam(Driver):

    def grab_image(self, **kwargs):
        img = np.zeros((256, 320))
        beamCenter = [int(np.random.randn()*10 + 123),
                      int(np.random.randn()*10 + 155)]
        img[beamCenter[0] - 10:beamCenter[0] + 10,
            beamCenter[1] - 10:beamCenter[1] + 10] = 1
        return img

    def stop(self):
        pass
