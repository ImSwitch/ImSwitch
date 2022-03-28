from ctypes import *
from math import fabs
from .common import *
from imswitch.imcommon.model.logging import LoggerAdapter
import inspect
from dataclasses import dataclass
from typing import Any

class MicroDriveHandler:

    @dataclass(frozen=True)
    class MCLMicroDriveInfo:
        deviceType : MCLMicroDevice
        encoderResolution : c_double
        stepSize : c_double
        maxSpeed1Axis : c_double
        maxSpeed2Axis : c_double
        maxSpeed3Axis : c_double
        minSpeed : c_double
        axis : dict[str, MCLAxis]

    def __init__(self, mclDLLPath : str, axis: dict[str, int], logger : LoggerAdapter) -> None:
        
        self.__logger = logger

        # MicroDriver axis can span between 1 and 6.
        # We first need to check boundaries.
        if any(ax > MCLAxis.M6AXIS.value or ax < MCLAxis.M1AXIS.value for ax in axis.values()):
            raise MCLException("Positioner axis indexes outside boundaries (minimum 1, maximum 6).")
        
        # Check if all elements in the axis dict are different.
        if len(set(axis.values())) != len(tuple(axis.values())):
            raise MCLException("Some positioner axis values are equal.")
        
        # Check if the number of axis is greater than 3 (only have XYZ available)
        if len(axis) > 3:
            raise MCLException("Incorrect number of axis provided.")

        # load DLL using absolute path
        self.__dll = cdll.LoadLibrary(mclDLLPath)
        self.__handle = self.__dll.MCL_InitHandle()

        if self.__handle == 0:
            raise MCLException("Failed to load DLL")

        self.__driverInfo = self._registerDriverInfo(axis)
    
    def getDriverInfo(self) -> list[str]:
        return [
            f"Handle ID: {self.__handle}",
            f"Device type: {self.__driverInfo.deviceType.name} ({hex(self.__driverInfo.deviceType)})",
            f"Encoder resolution: {self.__driverInfo.encoderResolution.value} \u03BCm",
            f"Step size: {self.__driverInfo.stepSize.value} mm",
            f"Max. speed (1 axis): {self.__driverInfo.maxSpeed1Axis.value} mm/s",
            f"Max. speed (2 axis): {self.__driverInfo.maxSpeed2Axis.value} mm/s",
            f"Max. speed (3 axis): {self.__driverInfo.maxSpeed3Axis.value} mm/s",
            f"Min. speed: {self.__driverInfo.minSpeed.value}"
        ]

    def _checkError(self, err) -> None:
        if err != MCLRetVal.MCL_SUCCESS.value:
            self.__dll.MCL_ReleaseHandle(self.__handle)
            caller = inspect.currentframe().f_back.f_code.co_name
            raise MCLException(f"{caller}: command failed (Error: {MCLRetVal(err)})")
    
    def _registerDriverInfo(self, axis: dict[str, int]) -> MCLMicroDriveInfo:

        devicePID = c_ushort()
        encoderResolution = stepSize = c_double()
        maxSpeed1Axis = maxSpeed2Axis = maxSpeed3Axis = c_double()
        minSpeed = c_double()
        bitmap = c_ubyte()

        ptrPID = pointer(devicePID)
        ptrEncRes = pointer(encoderResolution)
        ptrStepSize = pointer(stepSize)
        ptrMaxSpeed1 = pointer(maxSpeed1Axis)
        ptrMaxSpeed2 = pointer(maxSpeed2Axis)
        ptrMaxSpeed3 = pointer(maxSpeed3Axis)
        ptrMinSpeed = pointer(minSpeed)
        ptrBitmap = pointer(bitmap)

        axis = {key : MCLAxis(value) for key, value in axis.items()}
        self.__logger.debug("Checking PID...")
        self._checkError(self.__dll.MCL_GetProductID(ptrPID, self.__handle))
        self.__logger.debug("... done!")
        self.__logger.debug("Gathering device info...")
        self._checkError(self.__dll.MCL_MDInformation(
            ptrEncRes, 
            ptrStepSize, 
            ptrMaxSpeed1,
            ptrMaxSpeed2,
            ptrMaxSpeed3, 
            ptrMinSpeed,
            self.__handle))
        self.__logger.debug("... done!")
        self.__logger.debug("Gathering axis info...")
        self._checkError(self.__dll.MCL_GetAxisInfo(ptrBitmap, self.__handle))
        self.__logger.debug("... done!")
        # check correctness of axis
        for ax, index in axis.items():
            bit = (0x01 << (index.value - 1)) & bitmap
            if bit == 0:
                raise MCLException(f"Axis check failed. (Axis {ax} not available)")
        
        return self.MCLMicroDriveInfo(
            deviceType=MCLMicroDevice(devicePID.value),
            encoderResolution=encoderResolution,
            stepSize=stepSize,
            maxSpeed1Axis=maxSpeed1Axis,
            maxSpeed2Axis=maxSpeed2Axis,
            maxSpeed3Axis=maxSpeed3Axis,
            minSpeed=minSpeed,
            axis=axis
        )

    def _waitForCommand(self) -> None:
        self._checkError(self.__dll.MCL_MicroDriveWait(self.__handle))

    def setPosition(self, axis: str, pos: float) -> float:
        currAxis = c_int(self.__driverInfo.axis[axis])

        # MCL_MDMove works with millimiters
        # we need to devide pos by 1000
        # to move the stages in micrometers
        move = c_double(pos / 1000.0)
        startMicro, endMicro = pointer(c_int()), pointer(c_int())
        self._checkError(self.__dll.MCL_MDCurrentPositionM(currAxis, startMicro, self.__handle))

        if fabs(move.value) >= self.__driverInfo.stepSize.value:
            self._checkError(self.__dll.MCL_MDMove(currAxis,
                                                    self.__driverInfo.maxSpeed1Axis,
                                                    move,
                                                    self.__handle))
            self._waitForCommand()
        else:
            # movement smaller than minimum step size, skipping
            pass
        
        self._checkError(self.__dll.MCL_MDCurrentPositionM(currAxis, endMicro, self.__handle))
        return (endMicro.contents.value - startMicro.contents.value) * self.__driverInfo.stepSize.value
    
    def calibrate(self) -> bool:
        for _, axis in self.__driverInfo.axis.values():
            orig = limit = c_double()
    
    def close(self) -> None:
        self.__dll.MCL_ReleaseHandle(self.__handle)
        
class NanoDriveHandler:
    
    @dataclass(frozen=True)
    class MCLNanoDriveInfo:
        ADCResolution : c_short
        DACResolution : c_short
        productID : c_short
        FirmwareVersion : c_short
        FirmwareProfile : c_short
        motionRange : dict[str, c_double]
        axis : dict[str, MCLAxis] 

    def __init__(self, mclDLLPath : str, axis: dict[str, int], logger: LoggerAdapter) -> None:
        self.__logger = logger

        # NanoDriver axis can span between 1 and 5.
        # We first need to check boundaries.
        if any(ax > MCLAxis.M5AXIS.value or ax < MCLAxis.M1AXIS.value for ax in axis.values()):
            raise MCLException("Positioner axis indexes outside boundaries (minimum 1, maximum 5).")
        
        # Check if all elements in the axis dict are different.
        if len(set(axis.values())) != len(tuple(axis.values())):
            raise MCLException("Some positioner axis values are equal.")

        self.__dll = cdll.LoadLibrary(mclDLLPath)
        self.__handle = self.__dll.MCL_InitHandle()
        self.__driverInfo = self._registerDriverInfo(axis)
    
    def getDriverInfo(self) -> list[str]:
        return [
            f"ADC resolution: {self.__driverInfo.ADCResolution.value}",
            f"DAC resolution: {self.__driverInfo.DACResolution.value}",
            f"Product ID: {hex(self.__driverInfo.productID.value)}",
            f"Firmware version: {hex(self.__driverInfo.FirmwareVersion.value)}",
            f"Firmware profile: {hex(self.__driverInfo.FirmwareProfile.value) }"
        ]

    def _checkError(self, err) -> None:
        if err != MCLRetVal.MCL_SUCCESS.value:
            self.__dll.MCL_ReleaseHandle(self.__handle)
            caller = inspect.currentframe().f_back.f_code.co_name
            raise MCLException(f"{caller}: command failed (Error: {MCLRetVal(err)})")
    
    def _checkReturnValue(self, val : Any) -> Any:
        try:
            self._checkError(MCLRetVal(val))
        except ValueError:
            pass
        finally:
            return val
    
    def _waitForCommand(self) -> None:
        self.__dll.MCL_DeviceAttached(100, self.__handle)

    def _registerDriverInfo(self, axis: dict[str, int]) -> MCLNanoDriveInfo:
        
        class ProductInfo(Structure):
            _fields_ = [("axis_bitmap", c_ubyte),
                        ("ADC_resolution", c_short),
                        ("DAC_resolution", c_short),
                        ("Product_id", c_short),
                        ("FirmwareVersion", c_short),
                        ("FirmwareProfile", c_short)]
            _pack_ = 1 # this is how it is packed in the Madlib dll


        productInfo = ProductInfo()
        motionRange = {ax : 0 for ax in axis.keys()}
        axis = {key : MCLAxis(value) for key, value in axis.items()}

        ptrPI = pointer(productInfo)

        self._checkError(self.__dll.MCL_GetProductInfo(ptrPI, self.__handle))
        
        for ax, index in axis.items():
            bit = (0x01 << (index.value - 1)) & productInfo.axis_bitmap
            if bit == 0:
                raise MCLException(f"Axis check failed. (Axis {ax} not available)")
            # we can't use _checkError because the return value
            # is what we are trying to read
            range : c_double = self._checkReturnValue(
                self.__dll.MCL_GetCalibration(c_uint(index.value - 1), self.__handle)
            )
            motionRange[ax] = range
        
        return self.MCLNanoDriveInfo(
            productInfo.ADC_resolution,
            productInfo.DAC_resolution,
            productInfo.Product_id,
            productInfo.FirmwareVersion,
            productInfo.FirmwareProfile,
            motionRange,
            axis
        )
    
    def setPosition(self, axis: str, pos: float) -> float:
        currAxis = c_int(self.__driverInfo.axis[axis])
        self._checkError(
            self.__dll.MCL_SingleWriteN(c_double(pos), currAxis, self.__handle)
        )
        currPos : c_double = self._checkReturnValue(
            self.__dll.MCL_SingleReadN(currAxis, self.__handle)
        )
        return currPos.value
    
    def calibrate(self) -> bool:
        # NanoDrive calibration consists in moving to the maximum
        # of the motion range of each axis
        # and then move to half of the motion range
        ret = True
        for axis, range in self.__driverInfo.motionRange.items():
            currAxis = c_int(self.__driverInfo.axis[axis])
            self._checkError(
                self.__dll.MCL_SingleWriteN(range, currAxis, self.__handle)
            )
            self._waitForCommand()
            self._checkError(
                self.__dll.MCL_SingleWriteN(range/2, currAxis, self.__handle)
            )
            self._waitForCommand()
            
            # Read back the position to confirm
            currPos : c_double = self._checkReturnValue(
                self.__dll.MCL_SingleReadN(currAxis, self.__handle)
            )
            ret &= (currPos == range/2) 
        return ret

    def close(self) -> None:
        self.__dll.MCL_ReleaseHandle(self.__handle)