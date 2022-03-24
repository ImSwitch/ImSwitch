from ctypes import *
from math import fabs
from common import *
import inspect

class MicroDriveHandler:
    def __init__(self, mclDLLPath : str, axis: dict[str, int]) -> None:
        
        # MicroDriver axis can span between 1 and 6.
        # We first need to check boundaries.
        if any(ax > 6 or ax < 1 for ax in axis.values()):
            raise MCLException("[MicroDrive] Positioner axis indexes outside boundaries (minimum 1, maximum 6).")
        
        # Check if all elements in the axis tuple are different.
        if len(set(axis.values())) != len(tuple(axis.values())):
            raise MCLException("[MicroDrive] Some positioner axis values are equal.")

        self.__dll = cdll.LoadLibrary(mclDLLPath)
        self.__handle = self.__dll.MCL_InitHandle()

        if self.__handle == 0:
            raise MCLException("[MicroDrive] Failed to load DLL")

        self.__driverInfo = self._registerDriverInfo(axis)
        self.__currentPos = {key : 0.0 for key in axis.keys()}
    
    def getDriverInfo(self) -> list[str]:
        return [
            f"[MicroDrive] Handle ID: {self.__handle}",
            f"[MicroDrive] Encoder resolution: {self.__driverInfo.encoderResolution.contents.value}",
            f"[MicroDrive] Step size: {self.__driverInfo.stepSize.contents.value}",
            f"[MicroDrive] Max. speed (1 axis): {self.__driverInfo.maxSpeed1Axis.value}",
            f"[MicroDrive] Max. speed (2 axis): {self.__driverInfo.maxSpeed2Axis.value}",
            f"[MicroDrive] Max. speed (3 axis): {self.__driverInfo.maxSpeed3Axis.value}",
            f"[MicroDrive] Min. speed: {self.__driverInfo.minSpeed.value}"
        ]

    def _checkError(self, err) -> None:
        if err != MCLRetVal.MCL_SUCCESS.value:
            self.__dll.MCL_ReleaseHandle(self.__handle)
            caller = inspect.currentframe().f_back.f_code.co_name
            raise MCLException(f"[MicroDrive] {caller}: command failed (Error: {MCLRetVal(err)})")
    
    def _registerDriverInfo(self, axis: dict[str, int]) -> MCLDeviceInfo:

        devicePID = pointer(c_ushort())
        encoderResolution = pointer(c_double())
        stepSize = pointer(c_double())
        maxVel1Axis = pointer(c_double())
        maxVel2Axis = pointer(c_double())
        maxVel3Axis = pointer(c_double())
        minVel = pointer(c_double())
        bitmap = pointer(c_ubyte())
        axis = {key : MCLAxis(value) for key, value in axis}

        self._checkError(self.__dll.MCL_GetProductID(devicePID))
        self._checkError(self.__dll.MCL_MDInformation(
            encoderResolution, 
            stepSize, 
            maxVel1Axis,
            maxVel2Axis,
            maxVel3Axis, 
            minVel,
            self.__handle))
        self._checkError(cdll.MCL_GetAxisInfo(bitmap, self.__handle))
        
        # check correctness of axis
        for ax, index in axis.items():
            bit = 0x01 << (index.value - 1)
            if bit == 0:
                raise MCLException(f"[MicroDrive] Axis check failed. (Axis {ax} not available)")
        
        return MCLDeviceInfo(
            deviceType=MCLMicroDevice(devicePID.contents.value),
            encoderResolution=encoderResolution.contents,
            stepSize=stepSize.contents,
            maxSpeed1Axis=maxVel1Axis.contents,
            maxSpeed2Axis=maxVel2Axis.contents,
            maxSpeed3Axis=maxVel3Axis.contents,
            minSpeed=minVel.contents,
            axis=axis
        )

    def _waitForCommand(self) -> None:
        self._checkError(self.__dll.MCL_MicroDriveWait(self.__handle))

    def setPosition(self, axis: str, pos: float) -> float:
        currAxis = c_int(self.__driverInfo.axis[axis].value)
        move = c_double(pos - self.__currentPos[axis])
        startMicro, endMicro = pointer(c_int()), pointer(c_int())
        self._checkError(self.__dll.MCL_MDCurrentPositionM(currAxis, startMicro, self.__handle))

        if fabs(move.value) >= self.__driverInfo.stepSize.value:
            self._checkError(self.__dll.MCL_MDMove(currAxis,
                                                    self.__driverInfo.maxSpeed1Axis,
                                                    move,
                                                    self.__handle))
            self._waitForCommand()
        else:
            # movement skipped
            pass
        
        self._checkError(self.__dll.MCL_MDCurrentPositionM(currAxis, endMicro, self.__handle))
        self.__currentPos[axis] = (endMicro.contents.value - startMicro.contents.value) * self.__driverInfo.stepSize.value
        return self.__currentPos[axis]
        

