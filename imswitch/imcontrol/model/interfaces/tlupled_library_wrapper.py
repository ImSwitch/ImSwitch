#Tested with Python 3.7 and 3.10, 64 bit

#Import the necessary libraries to Python.
import ctypes
import os
import time
import sys
# If you're using Python 3.7 or older change add_dll_directory to chdir
TLUP_DIR = r"C:\Program Files\IVI Foundation\VISA\Win64\Bin"


if sys.platform == 'linux2' or sys.platform == 'linux':
    from pyvisa import ResourceManager
    try:
        rm = ResourceManager(visa_library="/home/mstingl/Documents/Thorlabs/upSERIES/Application/TLvisa_32.dll@py")
        # rm = ResourceManager("/home/mstingl/Documents/Thorlabs/VISA/VisaCom64/Primary Interop Assemblies/Thorlabs.TLUP_64.Interop.dll")

        print(rm.list_resources())
        arch_dir = "/home/mstingl/Documents/Thorlabs/upSERIES/Application/Thorlabs.TLVisa_32.Interop.dll"  #
        sys.path.append(arch_dir)  # add pyximc.py wrapper to python path
        print(arch_dir)
        dll = ctypes.CDLL(arch_dir)
    except OSError:
        print("Cannot find TLUP_64.lib.")

elif sys.version_info < (3, 8):
    os.chdir(r"C:\Program Files\IVI Foundation\VISA\Win64\Bin")
    # Load DLL library
    # os.add_dll_directory("C:\Program Files\IVI Foundation\VISA\Win64\Bin")
    # library=ctypes.cdll.LoadLibrary("TLUP_64.dll")
    library = ctypes.cdll.LoadLibrary(os.sep.join([TLUP_DIR, "TLUP_64.dll"]))
else:
    os.add_dll_directory(r"C:\Program Files\IVI Foundation\VISA\Win64\Bin")
    # Load DLL library
    # os.add_dll_directory("C:\Program Files\IVI Foundation\VISA\Win64\Bin")
    # library=ctypes.cdll.LoadLibrary("TLUP_64.dll")
    library = ctypes.cdll.LoadLibrary(os.sep.join([TLUP_DIR, "TLUP_64.dll"]))


class TLUPLibraryWrapper():
    def __init__(self, tlup_dir = TLUP_DIR, default_current = 0.02, verbose = 0):
        self.tlup_dir = tlup_dir
        self.verbose = verbose
        self.default_current = default_current
        self.available_devices = self.get_available_devices()
        self.initialize_devices()

    def initialize_device(self, resourceName):
        devSession = ctypes.c_int()
        status = library.TLUP_init(resourceName, False, False, ctypes.byref(devSession))
        if self.verbose:
            print(f"Device {resourceName} connected. {status}")
        if status < 0:
            print("Error when initializing device.")
            raise SystemError
        return devSession

    def initialize_devices(self):
        for k,v in self.available_devices.items():
            v["dev_session"] = self.initialize_device(v["name"])
            v["initialized"] = True

    def find_devices(self):
        resourceCount = ctypes.c_int()
        status = library.TLUP_findRsrc(0, ctypes.byref(resourceCount))
        if self.verbose:
            print(f"Number of devices: {resourceCount.value}. Status {status}")
        if status < 0:
            print("Error when getting available device.")
            raise SystemError
        return resourceCount.value

    def get_resource_name(self, dev):
        resourceName = ctypes.c_char_p(b"resourceName")
        status = library.TLUP_getRsrcName(0, dev, resourceName)
        if self.verbose:
            print(f"Resource Name. {resourceName.value}. Status {status}")
        if status < 0:
            print("Error when getting resource name.")
            raise SystemError
        return resourceName

    def get_resource_info(self, dev):
        modelName = ctypes.c_char_p(b"modelName")
        serialNumber = ctypes.c_char_p(b"serialNumber")
        manufacturer = ctypes.c_char_p(b"manufacturer")
        resourceAvailable = ctypes.c_bool()

        status = library.TLUP_getRsrcInfo(0, dev, modelName,
                            serialNumber, manufacturer, ctypes.byref(resourceAvailable))
        resourceInfo = {"modelName": modelName.value,"serialNumber": serialNumber.value,
                        "manufacturer": manufacturer.value, "resourceAvailable": resourceAvailable.value, }
        if self.verbose:
            print(f"Resource Info. {resourceInfo}. Status {status}")
        if status < 0:
            print("Error when getting resource info.")
            raise SystemError
        return resourceInfo

    def get_available_devices(self):
        devs = self.find_devices()
        resources_dict = {}
        for dev in list(range(devs)):
            resourceName = self.get_resource_name(dev)
            resourceInfo = self.get_resource_info(dev)
            # devSession = self.initialize_device(resourceName)
            # default_current = self.get_default_current_setpoint(devSession)
            # resources_dict[dev] = {"name": resourceName, "session": devSession, "default_current": default_current, "info": resourceInfo}
            resources_dict[dev] = {"name": resourceName.value, "initialized": False,  "info": resourceInfo}
        return resources_dict

    def get_log_message(self, devSession):
        #     System
        #         TLUP_getLogMessage
        return NotImplemented

    def get_temperature_unit(self, devSession):
        #     System
        #         TLUP_getTempUnit
        return NotImplemented

    def set_temperature_unit(self, devSession, unit):
        #     System
        #         TLUP_setTempUnit
        return NotImplemented

    def get_led_info(self, devSession):
        #     System: LED
        #         TLUP_getLedInfo
        LEDName = ctypes.c_char_p(b"LEDName")
        LEDSerialNumber = ctypes.c_char_p(b"LEDSerialNumber")
        LEDCurrentLimit = ctypes.c_double()
        LEDForwardVoltage = ctypes.c_double()
        LEDWavelength = ctypes.c_double()

        status = library.TLUP_getLedInfo(0, LEDName, LEDSerialNumber,
                        ctypes.byref(LEDCurrentLimit), ctypes.byref(LEDForwardVoltage),
                                         ctypes.byref(LEDWavelength))
        LEDInfo = {"name": LEDName.value,"serialNumber": LEDSerialNumber.value,
                        "currentLimit": LEDCurrentLimit.value, "forwardVoltage": LEDForwardVoltage.value,
                        "wavelength": LEDWavelength.value}
        if self.verbose:
            print(f"LED Info. {LEDInfo}. Status {status}")
        if status < 0:
            print("Error when getting LED info.")
            raise SystemError
        return LEDInfo

    def get_led_op_mode(self, devSession):
        #     System: LED
        #         TLUP_getOpMode
        return NotImplemented

    def get_led_extop_mode(self, devSession):
        #     System: LED
        #         TLUP_getExtendedOperationModes
        return NotImplemented

    def measure_devive_temperature(self, devSession):
        #     Measure
        #         TLUP_measDeviceTemperature
        return NotImplemented

    def measure_supply_voltage(self, devSession):
        #     Measure
        #         TLUP_measSupplyVoltage
        return NotImplemented

    def measure_led_current(self, devSession):
        #     Measure: LED
        #         TLUP_measureLedCurrent
        return NotImplemented

    def measure_led_voltage(self, devSession):
        #     Measure: LED
        #         TLUP_measureLedVoltage
        return NotImplemented

    def measure_poti_value(self, devSession):
        #     Measure: LED
        #         TLUP_measurePotiValue
        return NotImplemented

    def switch_on(self, devSession):
        status = library.TLUP_switchLedOutput(devSession, True)
        if self.verbose:
            print(f"LED switched ON. Status {status}")
        if status < 0:
            print("Error when switching on device.")
            raise SystemError

    def switch_off(self, devSession):
        status = library.TLUP_switchLedOutput(devSession, False)
        if self.verbose:
            print(f"LED switched OFF. Status {status}")
        if status < 0:
            print("Error when switching off device.")
            raise SystemError

    def state(self, devSession):
        state = ctypes.c_bool()
        status = library.TLUP_getLedOutputState(devSession, ctypes.byref(state))
        if self.verbose:
            print(f"LED state {state.value}. Status {status}")
        if status < 0:
            print("Error when getting device state.")
            raise SystemError
        return state.value

    def set_led_current_limit_user(self, devSession, current):
        #     Source: Configure: LED
        #         TLUP_setLedCurrentLimitUser
        return NotImplemented

    def get_led_current_limit_user(self, devSession):
        #     Source: Configure: LED
        #         TLUP_getLedCurrentLimitUser
        return NotImplemented

    def set_current_setpoint_at_startup(self, devSession, LEDCurrentSetpoint):
        LEDCurrentSetpoint = ctypes.c_double(LEDCurrentSetpoint)
        status = library.TLUP_setLedCurrentSetpointStartup(devSession, LEDCurrentSetpoint)
        if self.verbose:
            print(f"Setting device current setpoint at startup {LEDCurrentSetpoint.value} mA. Status {status}")
        if status < 0:
            print("Error when setting device current setpoint at startup")
            raise SystemError

    def get_current_setpoint_at_startup(self, devSession, attribute = 0):
        LEDCurrentSetpointStartup = ctypes.c_double()
        status = library.TLUP_getLedCurrentSetpointStartup(devSession, attribute,
                                                           ctypes.byref(LEDCurrentSetpointStartup))
        if self.verbose:
            output = {0: "current", 1: "minimum", 2: "maximum", 3: "default"}
            print(f"Getting device {output[attribute]} setpoint: {LEDCurrentSetpointStartup.value} A. Status {status}")
        if status < 0:
            print("Error when setting device current setpoint")
            raise SystemError
        return LEDCurrentSetpointStartup.value

    def set_current_setpoint(self, devSession, LEDCurrentSetpoint):
        LEDCurrentSetpoint = ctypes.c_double(LEDCurrentSetpoint)
        status = library.TLUP_setLedCurrentSetpoint(devSession, LEDCurrentSetpoint)
        if self.verbose:
            print(f"Setting device current setpoint at {LEDCurrentSetpoint.value} mA. Status {status}")
        if status < 0:
            print("Error when setting device current setpoint")
            raise SystemError

    def get_current_setpoint(self, devSession, attribute = 0):
        LEDCurrentSetSource = ctypes.c_double()
        status = library.TLUP_getLedCurrentSetpoint(devSession, attribute, ctypes.byref(LEDCurrentSetSource))
        if self.verbose:
            output = {0: "current", 1: "minimum", 2: "maximum", 3: "default"}
            print(f"Getting device {output[attribute]} setpoint: {LEDCurrentSetSource.value} A. Status {status}")
        if status < 0:
            print("Error when setting device current setpoint")
            raise SystemError
        return LEDCurrentSetSource.value

    def get_min_current_setpoint(self, devSession):
        return self.get_current_setpoint(devSession, attribute=1)

    def get_max_current_setpoint(self, devSession):
        return self.get_current_setpoint(devSession, attribute=2)

    def get_default_current_setpoint(self, devSession):
        return self.get_current_setpoint(devSession, attribute=3)

    def set_led_current_setpoint_source(self, devSession, current):
        #     Source: Configure: LED
        #         TLUP_setLedCurrentSetpointSource
        return NotImplemented

    def get_led_current_setpoint_source(self, devSession):
        #     Source: Configure: LED
        #         TLUP_getLedCurrentSetpointSource
        return NotImplemented

    def set_led_switch_on_at_startup(self, devSession, val: bool = True):
        status = library.TLUP_setLedSwitchOnAtStartup(devSession, val)
        if self.verbose:
            print(f"Setting switch on at startup {val}. Status {status}")
        if status < 0:
            print("Error when setting switch on at startup.")
            raise SystemError

    def get_led_switch_on_at_startup(self, devSession):
        #     Source: Configure: LED
        #         TLUP_getLedSwitchOnAtStartup
        return NotImplemented

    def set_led_switch_off_at_disconnect(self, devSession, val: bool = True):
        status = library.TLUP_setLedSwitchOffAtDisconnect(devSession, val)
        if self.verbose:
            print(f"Setting switch off at disconnect {val}. Status {status}")
        if status < 0:
            print("Error when setting switch off at disconnect.")
            raise SystemError

    def get_led_switch_off_at_disconnect(self, devSession):
        #     Source: Configure: LED
        #         TLUP_getLedSwitchOffAtDisconnect
        return NotImplemented

    def set_led_non_thorlabs(self, devSession, thorlabs):
        #     Source: Configure: LED
        #         TLUP_setLedUseNonThorlabsLed
        return NotImplemented

    def get_led_non_thorlabs(self, devSession):
        #     Source: Configure: LED
        #         TLUP_getLedUseNonThorlabsLed
        return NotImplemented

    def save_to_NVMEM(self, devSession):
        #    TLUP_saveToNVMEM
        return NotImplemented

    def error_message(self, devSession):
        #    Functions: TLUP_errorMessage
        return NotImplemented

    def error_query(self, devSession):
        #    Functions: TLUP_errorQuery
        return NotImplemented

    def reset(self, devSession):
        #    Functions: TLUP_reset
        return NotImplemented

    def self_test(self, devSession):
        #    Functions: TLUP_selfTest
        return NotImplemented

    def revision_query(self, devSession):
        #    Functions: TLUP_revisionQuery
        return NotImplemented

    def identification_query(self, devSession):
        #    Functions: TLUP_identificationQuery
        return NotImplemented

    def get_build_datetime(self, devSession):
        #     Source: Configure: LED
        #         TLUP_getBuildDateAndTime
        return NotImplemented

    def get_calibration_message(self, devSession):
        #     Source: Configure: LED
        #         TLUP_getCalibrationMsg
        return NotImplemented

    def close_device(self, devSession):
        status = library.TLUP_close(devSession)
        if self.verbose:
            print(f"Closing device at {devSession}. Status {status}")
        if status < 0:
            print("Error when closing device")
            raise SystemError

    def close_devices(self):
        for k,v in self.available_devices.items():
            self.switch_off(v["dev_session"])
            self.close_device(v["dev_session"])

    @property
    def verbose(self):
        return self._verbose
    @verbose.setter
    def verbose(self, v):
        self._verbose = v
