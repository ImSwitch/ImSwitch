#!/usr/bin/python
#
## @file
#
# A ctypes based interface to Hamamatsu cameras.
# (tested on a sCMOS Flash 4.0).
#
# The documentation is a little confusing to me on this subject..
# I used c_int32 when this is explicitly specified, otherwise I use c_int.
#
# FIXME: I'm using the "old" functions because these are documented..
#    Switch to the "new" functions at some point.
#
# FIXME: How to stream 2048 x 2048 at max frame rate to the flash disk?
#    The Hamamatsu software can do this.
#
# Hazen 10/13
#

import ctypes
import ctypes.util
import numpy as np
import time

print(r'C:\Users\testaRES\Desktop\WinPython-64bit-3.3.5.9\python-3.3.5.amd64\Lib\site-packages\lantz\drivers\hamamatsu')

# Hamamatsu constants.
DCAMCAP_EVENT_FRAMEREADY = int("0x0002", 0)

# DCAM3 API.
DCAMERR_ERROR = 0
DCAMERR_NOERROR = 1

DCAMPROP_ATTR_HASVALUETEXT = int("0x10000000", 0)
DCAMPROP_ATTR_READABLE = int("0x00010000", 0)
DCAMPROP_ATTR_WRITABLE = int("0x00020000", 0)

DCAMPROP_OPTION_NEAREST = int("0x80000000", 0)
DCAMPROP_OPTION_NEXT = int("0x01000000", 0)
DCAMPROP_OPTION_SUPPORT = int("0x00000000", 0)

DCAMPROP_TYPE_MODE = int("0x00000001", 0)
DCAMPROP_TYPE_LONG = int("0x00000002", 0)
DCAMPROP_TYPE_REAL = int("0x00000003", 0)
DCAMPROP_TYPE_MASK = int("0x0000000F", 0)

DCAMWAIT_TIMEOUT_INFINITE = int("0x80000000", 0)

DCAM_CAPTUREMODE_SNAP = 0
DCAM_CAPTUREMODE_SEQUENCE = 1

DCAM_DEFAULT_ARG = 0

DCAM_IDPROP_EXPOSURETIME = int("0x001F0110", 0)

DCAM_IDSTR_MODEL = int("0x04000104", 0)

# Hamamatsu structures.

## DCAM_PARAM_PROPERTYATTR
#
# The dcam property attribute structure.
#
class DCAM_PARAM_PROPERTYATTR(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_int32),
                ("iProp", ctypes.c_int32),
                ("option", ctypes.c_int32),
                ("iReserved1", ctypes.c_int32),
                ("attribute", ctypes.c_int32),
                ("iGroup", ctypes.c_int32),
                ("iUnit", ctypes.c_int32),
                ("attribute2", ctypes.c_int32),
                ("valuemin", ctypes.c_double),
                ("valuemax", ctypes.c_double),
                ("valuestep", ctypes.c_double),
                ("valuedefault", ctypes.c_double),
                ("nMaxChannel", ctypes.c_int32),
                ("iReserved3", ctypes.c_int32),
                ("nMaxView", ctypes.c_int32),
                ("iProp_NumberOfElement", ctypes.c_int32),
                ("iProp_ArrayBase", ctypes.c_int32),
                ("iPropStep_Element", ctypes.c_int32)]

## DCAM_PARAM_PROPERTYVALUETEXT
#
# The dcam text property structure.
#
class DCAM_PARAM_PROPERTYVALUETEXT(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_int32),
                ("iProp", ctypes.c_int32),
                ("value", ctypes.c_double),
                ("text", ctypes.c_char_p),
                ("textbytes", ctypes.c_int32)]


## convertPropertyName
#
# "Regularizes" a property name. We are using all lowercase names with
# the spaces replaced by underscores.
#
# @param p_name The property name string to regularize.
#
# @return The regularized property name.DCAMException
#
def convertPropertyName(p_name):
    return p_name.lower().decode("utf-8").replace(" ", "_")


## DCAMException
#
# Camera exceptions.
#
class DCAMException(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)


#
# Initialization
#
dcam = ctypes.windll.dcamapi
temp = ctypes.c_int32(0)
if (dcam.dcam_init(None, ctypes.byref(temp), None) != DCAMERR_NOERROR):
    raise DCAMException("DCAM initialization failed.")
n_cameras = temp.value



## HCamData
#
# Hamamatsu camera data object.
#
# Initially I tried to use create_string_buffer() to allocate storage for the
# data from the camera but this turned out to be too slow. The software
# kept falling behind the camera and create_string_buffer() seemed to be the
# bottleneck.
#
class HCamData:

    ## __init__
    #
    # Create a data object of the appropriate size.
    #
    # @param size The size of the data object in bytes.
    #
    def __init__(self, size):
        self.np_array = np.ascontiguousarray(np.empty(np.int(size/2), dtype=np.uint16))
        self.size = size

    ## __getitem__
    #
    # @param slice The slice of the item to get.
    #
    def __getitem__(self, slice):
        return self.np_array[slice]

    ## copyData
    #
    # Uses the C memmove function to copy data from an address in memory
    # into memory allocated for the numpy array of this object.
    #
    # @param address The memory address of the data to copy.
    #
    def copyData(self, address):
        ctypes.memmove(self.np_array.ctypes.data, address, self.size)

    ## getData
    #
    # @return A numpy array that contains the camera data.
    #
    def getData(self):
        return self.np_array

    ## getDataPtr
    #
    # @return The physical address in memory of the data.
    #
    def getDataPtr(self):
        return self.np_array.ctypes.data


## HamamatsuCamera
#
# Basic camera interface class.
#
# This version uses the Hamamatsu library to allocate camera buffers.
# Storage for the data from the camera is allocated dynamically and
# copied out of the camera buffers.
#
class HamamatsuCamera:


    ## __init__
    #
    # Open the connection to the camera specified by camera_id.
    #
    # @param camera_id The id of the camera (an integer).
    #
    def __init__(self, camera_id):

        self.buffer_index = 0
        self.camera_id = camera_id
        self.camera_model = self.getModelInfo(camera_id)
        self.debug = False
        self.frame_bytes = 0
        self.frame_x = 0
        self.frame_y = 0
        self.last_frame_number = 0
        self.properties = {}
        self.max_backlog = 0
        self.number_image_buffers = 0

        # Open the camera.
        self.camera_handle = ctypes.c_void_p(0)
        self.checkStatus(dcam.dcam_open(ctypes.byref(self.camera_handle),
                                        ctypes.c_int32(self.camera_id),
                                        None),
                         "dcam_open")
        # Get camera properties.
        self.properties = self.getCameraProperties()
        # Get camera max width, height.
        self.max_width = self.getPropertyValue("image_width")[0]
        self.max_height = self.getPropertyValue("image_height")[0]

    ## captureSetup
    #
    # Capture setup (internal use only). This is called at the start
    # of new acquisition sequence to determine the current ROI and
    # get the camera configured properly.
    #
    def captureSetup(self):
        self.buffer_index = -1
        self.last_frame_number = 0

        # Set sub array mode.
        self.setSubArrayMode()

        # Get frame properties.
        self.frame_x = self.getPropertyValue("image_width")[0]
        self.frame_y = self.getPropertyValue("image_height")[0]
        self.frame_bytes = self.getPropertyValue("image_framebytes")[0]

        # Set capture mode.
        self.checkStatus(dcam.dcam_precapture(self.camera_handle,
                                              ctypes.c_int(DCAM_CAPTUREMODE_SEQUENCE)),
                         "dcam_precapture")

    ## checkStatus
    #
    # Check return value of the dcam function call.
    # Throw an error if not as expected?
    #
    # @return The return value of the function.
    #
    def checkStatus(self, fn_return, fn_name= "unknown"):
        #if (fn_return != DCAMERR_NOERROR) and (fn_return != DCAMERR_ERROR):
        #    raise DCAMException("dcam error: " + fn_name + " returned " + str(fn_return))
        if (fn_return == DCAMERR_ERROR):
            c_buf_len = 80
            c_buf = ctypes.create_string_buffer(c_buf_len)
            c_error = dcam.dcam_getlasterror(self.camera_handle,
                                             c_buf,
                                             ctypes.c_int32(c_buf_len))
            raise DCAMException("dcam error " + str(fn_name) + " " + str(c_buf.value))
            #print "dcam error", fn_name, c_buf.value
        return fn_return

    ## getCameraProperties
    #
    # Return the ids & names of all the properties that the camera supports. This
    # is used at initialization to populate the self.properties attribute.
    #
    # @return A python dictionary of camera properties.
    #
    def getCameraProperties(self):
        c_buf_len = 64
        c_buf = ctypes.create_string_buffer(c_buf_len)
        properties = {}
        prop_id = ctypes.c_int32(0)

        # Reset to the start.
        ret = dcam.dcam_getnextpropertyid(self.camera_handle,
                                          ctypes.byref(prop_id),
                                          ctypes.c_int32(DCAMPROP_OPTION_NEAREST))
        if (ret != 0) and (ret != DCAMERR_NOERROR):
            self.checkStatus(ret, "dcam_getnextpropertyid")

        # Get the first property.
        ret = dcam.dcam_getnextpropertyid(self.camera_handle,
                                          ctypes.byref(prop_id),
                                          ctypes.c_int32(DCAMPROP_OPTION_NEXT))
        if (ret != 0) and (ret != DCAMERR_NOERROR):
            self.checkStatus(ret, "dcam_getnextpropertyid")
        self.checkStatus(dcam.dcam_getpropertyname(self.camera_handle,
                                                   prop_id,
                                                   c_buf,
                                                   ctypes.c_int32(c_buf_len)),
                         "dcam_getpropertyname")
        # Get the rest of the properties.
        last = -1
        while (prop_id.value != last):
            last = prop_id.value
            properties[convertPropertyName(c_buf.value)] = prop_id.value
            ret = dcam.dcam_getnextpropertyid(self.camera_handle,
                                              ctypes.byref(prop_id),
                                              ctypes.c_int32(DCAMPROP_OPTION_NEXT))
            if (ret != 0) and (ret != DCAMERR_NOERROR):
                self.checkStatus(ret, "dcam_getnextpropertyid")
            self.checkStatus(dcam.dcam_getpropertyname(self.camera_handle,
                                                       prop_id,
                                                       c_buf,
                                                       ctypes.c_int32(c_buf_len)),
                             "dcam_getpropertyname")
        return properties

    ## getFrames
    #
    # Gets all of the available frames.
    #
    # This will block waiting for new frames even if
    # there new frames available when it is called.
    #
    # @return (frames, (frame x size, frame y size))
    #
    def getFrames(self):
        frames = []
        k = self.newFrames()
        for n in k:

            # Lock the frame in the camera buffer & get address.
            data_address = ctypes.c_void_p(0)
            row_bytes = ctypes.c_int32(0)
            self.checkStatus(dcam.dcam_lockdata(self.camera_handle,
                                                ctypes.byref(data_address),
                                                ctypes.byref(row_bytes),
                                                ctypes.c_int32(n)),
                             "dcam_lockdata")

            # Create storage for the frame & copy into this storage.
            hc_data = HCamData(self.frame_bytes)
            hc_data.copyData(data_address)

            # Unlock the frame.
            #
            # According to the documentation, this would be done automatically
            # on the next call to lockdata, but we do this anyway.
            self.checkStatus(dcam.dcam_unlockdata(self.camera_handle),
                             "dcam_unlockdata")

            frames.append(hc_data)

        return frames, (self.frame_x, self.frame_y)

    ## getModelInfo
    #
    # Returns the model of the camera
    #
    # @param camera_id The (integer) camera id number.
    #
    # @return A string containing the camera name.
    #
    def getModelInfo(self, camera_id):
        c_buf_len = 20
        c_buf = ctypes.create_string_buffer(c_buf_len)
        self.checkStatus(dcam.dcam_getmodelinfo(ctypes.c_int32(camera_id),
                                                ctypes.c_int32(DCAM_IDSTR_MODEL),
                                                c_buf,
                                                ctypes.c_int(c_buf_len)),
                         "dcam_getmodelinfo")
        return c_buf.value

    ## getProperties
    #
    # Return the list of camera properties. This is the one to call if you
    # want to know the camera properties.
    #
    # @return A dictionary of camera properties.
    #
    def getProperties(self):
        return self.properties

    ## getPropertyAttribute
    #
    # Return the attribute structure of a particular property.
    #
    # FIXME (OPTIMIZATION): Keep track of known attributes?
    #
    # @param property_name The name of the property to get the attributes of.
    #
    # @return A DCAM_PARAM_PROPERTYATTR object.
    #
    def getPropertyAttribute(self, property_name):
        p_attr = DCAM_PARAM_PROPERTYATTR()
        p_attr.cbSize = ctypes.sizeof(p_attr)
        p_attr.iProp = self.properties[property_name]
        ret = self.checkStatus(dcam.dcam_getpropertyattr(self.camera_handle,
                                                         ctypes.byref(p_attr)),
                               "dcam_getpropertyattr")
        if (ret == 0):
            print(" property", property_id, "is not supported")
            return False
        else:
            return p_attr

    ## getPropertyText
    #
    # Return the text options of a property (if any).
    #
    # @param property_name The name of the property to get the text values of.
    #
    # @return A dictionary of text properties (which may be empty).
    #
    def getPropertyText(self, property_name):
        prop_attr = self.getPropertyAttribute(property_name)
        if not (prop_attr.attribute & DCAMPROP_ATTR_HASVALUETEXT):
            return {}
        else:
            # Create property text structure.
            prop_id = self.properties[property_name]
            v = ctypes.c_double(prop_attr.valuemin)

            prop_text = DCAM_PARAM_PROPERTYVALUETEXT()
            c_buf_len = 64
            c_buf = ctypes.create_string_buffer(c_buf_len)
            #prop_text.text = ctypes.c_char_p(ctypes.addressof(c_buf))
            prop_text.cbSize = ctypes.c_int32(ctypes.sizeof(prop_text))
            prop_text.iProp = ctypes.c_int32(prop_id)
            prop_text.value = v
            prop_text.text = ctypes.addressof(c_buf)
            prop_text.textbytes = c_buf_len

            # Collect text options.
            done = False
            text_options = {}
            while not done:
                # Get text of current value.
                self.checkStatus(dcam.dcam_getpropertyvaluetext(self.camera_handle,
                                                                ctypes.byref(prop_text)),
                                 "dcam_getpropertyvaluetext")
                text_options[prop_text.text] = int(v.value)

                # Get next value.
                ret = dcam.dcam_querypropertyvalue(self.camera_handle,
                                                   ctypes.c_int32(prop_id),
                                                   ctypes.byref(v),
                                                   ctypes.c_int32(DCAMPROP_OPTION_NEXT))
                prop_text.value = v
                if (ret == 0):
                    done = True

            return text_options

    ## getPropertyRange
    #
    # Return the range for an attribute.
    #
    # @param property_name The name of the property (as a string).
    #
    # @return (minimum value, maximum value)
    #
    def getPropertyRange(self, property_name):
        prop_attr = self.getPropertyAttribute(property_name)
        temp = prop_attr.attribute & DCAMPROP_TYPE_MASK
        if (temp == DCAMPROP_TYPE_REAL):
            return float(prop_attr.valuemin), float(prop_attr.valuemax)
        else:
            return int(prop_attr.valuemin), int(prop_attr.valuemax)

    ## getPropertyRW
    #
    # Return if a property is readable / writeable.
    #
    # @return (True/False (readable), True/False (writeable))
    #
    def getPropertyRW(self, property_name):
        prop_attr = self.getPropertyAttribute(property_name)
        return (bool(prop_attr.attribute & DCAMPROP_ATTR_READABLE), # Check if property is readable.
                bool(prop_attr.attribute & DCAMPROP_ATTR_WRITABLE)) # Check if property is writable.

    ## getPropertyVale
    #
    # Return the current setting of a particular property.
    #
    # @param property_name The name of the property.
    #
    # @return (the property value, the property type)
    #
    def getPropertyValue(self, property_name):

        # Check if the property exists.
        if not (property_name in self.properties):
            print(" unknown property name:", property_name)
            return False
        prop_id = self.properties[property_name]

        # Get the property attributes.
        prop_attr = self.getPropertyAttribute(property_name)

        # Get the property value.
        c_value = ctypes.c_double(0)
        self.checkStatus(dcam.dcam_getpropertyvalue(self.camera_handle,
                                                    ctypes.c_int32(prop_id),
                                                    ctypes.byref(c_value)),
                         "dcam_getpropertyvalue")

        # Convert type based on attribute type.
        temp = prop_attr.attribute & DCAMPROP_TYPE_MASK
        if (temp == DCAMPROP_TYPE_MODE):
            prop_type = "MODE"
            prop_value = int(c_value.value)
        elif (temp == DCAMPROP_TYPE_LONG):
            prop_type = "LONG"
            prop_value = int(c_value.value)
        elif (temp == DCAMPROP_TYPE_REAL):
            prop_type = "REAL"
            prop_value = c_value.value
        else:
            prop_type = "NONE"
            prop_value = False

        return prop_value, prop_type

    ## isCameraProperty
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

    ## newFrames
    #
    # Return a list of the ids of all the new frames since the last check.
    #
    # This will block waiting for at least one new frame.
    #
    # @return [id of the first frame, .. , id of the last frame]
    #
    def newFrames(self):

#         Wait for a new frame.
        try:
            dwait = ctypes.c_int(DCAMCAP_EVENT_FRAMEREADY)
            self.checkStatus(dcam.dcam_wait(self.camera_handle,
                                            ctypes.byref(dwait),
                                            ctypes.c_int(0),
                                            None),
                             "dcam_wait")
            # Check how many new frames there are.
            b_index, f_count = self.getAq_Info()
            # Check that we have not acquired more frames than we can store in our buffer.
            # Keep track of the maximum backlog.
            cur_frame_number = f_count
            backlog = cur_frame_number - self.last_frame_number
            if (backlog > self.number_image_buffers):
                print("warning: hamamatsu camera frame buffer overrun detected!")
            if (backlog > self.max_backlog):
                self.max_backlog = backlog
            self.last_frame_number = cur_frame_number
    
            cur_buffer_index = b_index
    
            # Create a list of the new frames.
            new_frames = []
            if (cur_buffer_index < self.buffer_index):
                for i in range(self.buffer_index + 1, self.number_image_buffers):
                    new_frames.append(i)
                for i in range(cur_buffer_index + 1):
                    new_frames.append(i)
            else:
                for i in range(self.buffer_index, cur_buffer_index):
                    new_frames.append(i+1)
            self.buffer_index = cur_buffer_index
    
            if self.debug:
                print(new_frames)
    
            return new_frames
        except:
            return []

    def getAq_Info(self):
        """b_index indicates which index position in the buffer was last
        written to, f_count indicates how many frames were aquired since start"""
        b_index = ctypes.c_int32(0)
        f_count = ctypes.c_int32(0)
        self.checkStatus(dcam.dcam_gettransferinfo(self.camera_handle,
                                                   ctypes.byref(b_index),
                                                   ctypes.byref(f_count)),
                         "dcam_gettransferinfo")
        return b_index.value, f_count.value
    ## setPropertyValue
    #
    # Set the value of a property.
    #
    # @param property_name The name of the property.
    # @param property_value The value to set the property to.
    #
    # Minor changes made in this function (in part that handle text-propertyvalues.
    # Did not behave properly when called from setSubArrayMode. Now setSubArrayMode
    # passes b'OFF' instead of 'OFF' which
    # necesssitated changes in this function too. /Andreas

    def setPropertyValue(self, property_name, property_value):

        # Check if the property exists.
        if not (property_name in self.properties):
            print(" unknown property name:", property_name)
            return False

        # If the value is text, figure out what the
        # corresponding numerical property value is.
        if (type(property_value) == bytes):     # Used to test == type("")
            text_values = self.getPropertyText(property_name)
            if (property_value in text_values):
                property_value = float(text_values[property_value])
            else:
                print(" unknown property text value:", property_value, "for", property_name)
                return False

        # Check that the property is within range.
        pv_min, pv_max = self.getPropertyRange(property_name)
        if (property_value < pv_min):
            print(" set property value", property_value, "is less than minimum of", pv_min, property_name, "setting to minimum")
            property_value = pv_min
        if (property_value > pv_max):
            print(" set property value", property_value, "is greater than maximum of", pv_max, property_name, "setting to maximum")
            property_value = pv_max

        # Set the property value, return what it was set too.
        prop_id = self.properties[property_name]
        p_value = ctypes.c_double(property_value)
        self.checkStatus(dcam.dcam_setgetpropertyvalue(self.camera_handle,
                                                       ctypes.c_int32(prop_id),
                                                       ctypes.byref(p_value),
                                                       ctypes.c_int32(DCAM_DEFAULT_ARG)),
                         "dcam_setgetpropertyvalue")
        return p_value.value

    ## setSubArrayMode
    #
    # This sets the sub-array mode as appropriate based on the current ROI.
    #
    # Change made in here: call to function setPropertyValue with b'OFF' instead of 'OFF'
    # due to (maybe new?) structure of self.getPropertyText('subarray_mode') using bytes keywords. /Andreas

    def setSubArrayMode(self):

        # Check ROI properties.
        roi_w = self.getPropertyValue("subarray_hsize")[0]
        roi_h = self.getPropertyValue("subarray_vsize")[0]

        # If the ROI is smaller than the entire frame turn on subarray mode
        if ((roi_w == self.max_width) and (roi_h == self.max_height)):
            self.setPropertyValue("subarray_mode", b'OFF')
        else:
            self.setPropertyValue("subarray_mode", b'ON')

    ## startAcquisition
    #
    # Start data acquisition.
    #
    def startAcquisition(self):
        self.captureSetup()
        #
        # Allocate Hamamatsu image buffers.
        # We allocate enough to buffer 2 seconds of data.
        #
        n_buffers = int(2.0*self.getPropertyValue("internal_frame_rate")[0])
        self.number_image_buffers = n_buffers
        self.checkStatus(dcam.dcam_allocframe(self.camera_handle,
                                              ctypes.c_int32(self.number_image_buffers)),
                         "dcam_allocframe")

        # Start acquisition.
        self.checkStatus(dcam.dcam_capture(self.camera_handle),
                         "dcam_capture")
    ## stopAcquisition
    #
    # Stop data acquisition.
    #
    def stopAcquisition(self):

        # Stop acquisition.
        self.checkStatus(dcam.dcam_idle(self.camera_handle),
                         "dcam_idle")

        print("max camera backlog was", self.max_backlog, "of", self.number_image_buffers)
        self.max_backlog = 0

        # Free image buffers.
        self.number_image_buffers = 0
        self.checkStatus(dcam.dcam_freeframe(self.camera_handle),
                         "dcam_freeframe")

    ## shutdown
    #
    # Close down the connection to the camera.
    #
    def shutdown(self):
        self.checkStatus(dcam.dcam_close(self.camera_handle),
                         "dcam_close")


## HamamatsuCameraMR
#
# Memory recycling camera class.
#
# This version allocates "user memory" for the Hamamatsu camera
# buffers. This memory is also the location of the storage for
# the np_array element of a HCamData() class. The memory is
# allocated once at the beginning, then recycled. This means
# that there is a lot less memory allocation & shuffling compared
# to the basic class, which performs one allocation and (I believe)
# two copies for each frame that is acquired.
#
# WARNING: There is the potential here for chaos. Since the memory
#   is now shared there is the possibility that downstream code
#   will try and access the same bit of memory at the same time
#   as the camera and this could end badly.
#
# FIXME: Use lockbits (and unlockbits) to avoid memory clashes?
#   This would probably also involve some kind of reference counting
#   scheme.
#
class HamamatsuCameraMR(HamamatsuCamera):

    ## __init__
    #
    # @param camera_id The id of the camera.
    #
    def __init__(self, camera_id):
        HamamatsuCamera.__init__(self, camera_id)

        self.hcam_data = []
        self.hcam_ptr = False
        self.old_frame_bytes = -1

        self.setPropertyValue("output_trigger_kind[0]", 2)

    ## getFrames
    #
    # Gets all of the available frames.
    #
    # This will block waiting for new frames even if there new frames
    # available when it is called.
    #
    # FIXME: It does not always seem to block? The length of frames can
    #   be zero. Are frames getting dropped? Some sort of race condition?
    #
    # @return (frames, (frame x size, frame y size))
    #
    def getFrames(self):
        frames = []
        for n in self.newFrames():
            im = self.hcam_data[n].getData()
            frames.append(np.reshape(im, (self.frame_x, self.frame_y)))
        return frames, (self.frame_x, self.frame_y)
        
    def getLast(self):
        b_index, f_count = self.getAq_Info()
        im = self.hcam_data[b_index].getData()
        return np.reshape(im, (self.frame_x, self.frame_y))

        
    def updateIndices(self):
        b_index, f_count = self.getAq_Info()
        self.buffer_index = b_index
        self.last_frame_number = f_count
        
    def getSpecFrames(self, ids):
        """Get frames specified by their id's"""
        frames = []
        for n in ids:
            frames.append(self.hcam_data[n])

        return frames
        
    def UpdateFrameNrBufferIdx(self):
        b_index, f_count = self.getAq_Info()
        self.last_frame_number = f_count
        self.buffer_index = b_index
        
    ## startAcquisition
    #
    # Allocate as many frames as will fit in 2GB of memory and start data acquisition.
    #
    def startAcquisition(self):
        self.captureSetup()
        print(self.frame_bytes)
        #
        # Allocate new image buffers if necessary.
        # Allocate as many frames as can fit in 2GB of memory.
#        NOTE: The for loop in this function can be timeconsuming if the frame_bytes are small since this leads to
#        a large amount of frames and thus a large amount of iterations of the loop.hca
        #
        if (self.old_frame_bytes != self.frame_bytes):

            n_buffers = 2*int((4 * 1024 * 1024 * 1024)/(2*self.frame_bytes)) #Even number of frames
            print('Number of frames to buffer: ', n_buffers)
            self.number_image_buffers = n_buffers

            # Allocate new image buffers.
            ptr_array = ctypes.c_void_p * self.number_image_buffers
            self.hcam_ptr = ptr_array()
            self.hcam_data = []

        # This loop can take time if number_image_frames is large
            for i in range(self.number_image_buffers):
                hc_data = HCamData(self.frame_bytes)
                self.hcam_ptr[i] = hc_data.getDataPtr()
                self.hcam_data.append(hc_data)

            self.old_frame_bytes = self.frame_bytes
            print('Finished buffering frames')
        # Attach image buffers.
        #
        # We need to attach & release for each acquisition otherwise
        # we'll get an error if we try to change the ROI in any way
        # between acquisitions.
        self.checkStatus(dcam.dcam_attachbuffer(self.camera_handle,
                                                self.hcam_ptr,
                                                ctypes.sizeof(self.hcam_ptr)),
                         "dcam_attachbuffer")
        # Start acquisition.
        self.checkStatus(dcam.dcam_capture(self.camera_handle),
                         "dcam_capture")
    ## stopAcquisition
    #
    # Stop data acquisition and release the memory associates with the frames.
    #
    def stopAcquisition(self):

        # Stop acquisition.
        self.checkStatus(dcam.dcam_idle(self.camera_handle),
                         "dcam_idle")

        # Release image buffers.
        if (self.hcam_ptr):
            self.checkStatus(dcam.dcam_releasebuffer(self.camera_handle),
                             "dcam_releasebuffer")

        print("max camera backlog was:", self.max_backlog)
        self.max_backlog = 0


#
# Testing.
#

if __name__ == "__main__":


    print("found:", n_cameras, "cameras")
    if (n_cameras > 0):

        hcam = HamamatsuCameraMR(0)
        print(hcam.setPropertyValue("defect_correct_mode", 1))
        print("camera 0 model:", hcam.getModelInfo(0))

        # List support properties.
        if 1:
            print("Supported properties:")
            props = hcam.getProperties()
            for i, id_name in enumerate(sorted(props.keys())):
                p_value, p_type = hcam.getPropertyValue(id_name)
                p_readable, p_writable = hcam.getPropertyRW(id_name)
                read_write = ""
                if p_readable:
                    read_write += "read"
                if p_writable:
                    read_write += ", write"
                print("  ", i, ")", id_name, " = ", p_value, " type is:", p_type, ",", read_write)
                text_values = hcam.getPropertyText(id_name)
                if len(text_values) > 0:
                    print("          option / value")
                    for key in sorted(text_values, key = text_values.get):
                        print("         ", key, "/", text_values[key])

        # Test setting & getting some parameters.
        if 0:
            print(hcam.setPropertyValue("exposure_time", 0.001))

            #print hcam.setPropertyValue("subarray_hsize", 2048)
            #print hcam.setPropertyValue("subarray_vsize", 2048)
            print(hcam.setPropertyValue("subarray_hpos", 512))
            print(hcam.setPropertyValue("subarray_vpos", 512))
            print(hcam.setPropertyValue("subarray_hsize", 1024))
            print(hcam.setPropertyValue("subarray_vsize", 1024))

            print(hcam.setPropertyValue("binning", "1x1"))
            print(hcam.setPropertyValue("readout_speed", 2))

            hcam.setSubArrayMode()
            #hcam.startAcquisition()
            #hcam.stopAcquisition()

            params = ["internal_frame_rate",
                      "timing_readout_time",
                      "exposure_time"]

            #                      "image_height",
            #                      "image_width",
            #                      "image_framebytes",
            #                      "buffer_framebytes",
            #                      "buffer_rowbytes",
            #                      "buffer_top_offset_bytes",
            #                      "subarray_hsize",
            #                      "subarray_vsize",
            #                      "binning"]
            for param in params:
                print(param, hcam.getPropertyValue(param)[0])

        # Test acquisition.
        if 0:
            hcam.startAcquisition()
            cnt = 1
            for i in range(300):
                (frames, dims) = hcam.getFrames()
                for aframe in frames:
                    print(cnt, aframe[0:5])
                    cnt += 1

            hcam.stopAcquisition()



#
# The MIT License
#
# Copyright (c) 2013 Zhuang Lab, Harvard University
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
