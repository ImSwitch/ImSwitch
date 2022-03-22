from ctypes import *
from common import *
import inspect

class MicroDriveHandler:
    def __init__(self, mclDLLPath : str, axis: tuple[int, int, int]) -> None:
        
        # MicroDriver axis can span between 1 and 6.
        # We first need to check boundaries.
        if any(ax > 6 or ax < 1 for ax in axis):
            raise MCLException("[MicroDrive] Positioner axis indexes outside boundaries (minimum 1, maximum 6).")
        
        # Check if all elements in the axis tuple are different.
        if len(set(axis)) != len(tuple):
            raise MCLException("[MicroDrive] Some positioner axis values are equal.")

        self.__dll = cdll.LoadLibrary(mclDLLPath)
        self.__handle = self.__dll.MCL_InitHandle()

        if self.__handle == 0:
            raise MCLException("[MicroDrive] Failed to load DLL")

        self.__driverInfo = self._registerDriverInfo(axis)
    
    def getDriverInfo(self) -> list[str]:
        return [
            f"[MicroDrive] Handle ID: {self.__handle}",
            f"[MicroDrive] Encoder resolution: {self.__driverInfo.encoderResolution.contents.value}",
            f"[MicroDrive] Step size: {self.__driverInfo.stepSize.contents.value}",
            f"[MicroDrive] Max. speed (1 axis): {self.__driverInfo.maxSpeed1Axis.contents.value}",
            f"[MicroDrive] Max. speed (2 axis): {self.__driverInfo.maxSpeed2Axis.contents.value}",
            f"[MicroDrive] Max. speed (3 axis): {self.__driverInfo.maxSpeed3Axis.contents.value}",
            f"[MicroDrive] Min. speed: {self.__driverInfo.minSpeed.contents.value}"
        ]

    def _checkError(self, err) -> None:
        if err != MCLRetVal.MCL_SUCCESS.value:
            self.__dll.MCL_ReleaseHandle(self.__handle)
            caller = inspect.currentframe().f_back.f_code.co_name
            raise MCLException(f"[MicroDrive] {caller}: command failed (Error: {MCLRetVal(err)})")
    
    def _registerDriverInfo(self, axis: tuple[int, int, int]) -> MCLDeviceInfo:

        devicePID = pointer(c_ushort())
        encoderResolution = pointer(c_double())
        stepSize = pointer(c_double())
        maxVel1Axis = pointer(c_double())
        maxVel2Axis = pointer(c_double())
        maxVel3Axis = pointer(c_double())
        minVel = pointer(c_double())
        bitmap = pointer(c_ubyte())
        axis = {
            "x" : MCLAxis(axis[0]),
            "y" : MCLAxis(axis[1]),
            "z" : MCLAxis(axis[2])
        }

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
        xBit, yBit, zBit = 0x01 << (axis["x"].value - 1), 0x01 << (axis["y"].value - 1), 0x01 << (axis["z"].value - 1)
        if xBit == 0 or yBit == 0 or zBit == 0:
            raise MCLException(f"[MicroDrive] Axis check failed. (x: {xBit == 0}, y: {yBit == 0}, z: {zBit == 0})")
        
        return MCLDeviceInfo(
            deviceType=MCLMicroDevice(devicePID.contents.value),
            encoderResolution=encoderResolution,
            stepSize=stepSize,
            maxSpeed1Axis=maxVel1Axis,
            maxSpeed2Axis=maxVel2Axis,
            maxSpeed3Axis=maxVel3Axis,
            minSpeed=minVel,
            axis=axis
        )

    def _waitForCommand(self) -> None:
        self._checkError(self.__dll.MCL_MicroDriveWait(self.__handle))

    def getPosition(self, axis : str) -> float:
        axisInt = c_uint(self.__driverInfo.axis[axis].value)
        currPos = pointer(c_int())
        self._checkError(self.__dll.MCL_MDCurrentPositionM(axisInt, currPos, self.__handle))
        self._waitForCommand()
        return float(currPos.contents.value) * self.__driverInfo.stepSize.contents.value
    
    def move(self, value : float, axis : str) -> None:
        newPos = c_double(value)
        axisInt = c_uint(self.__driverInfo.axis[axis].value)
        self._checkError(self.__dll.MCL_MDMove(axisInt, self.__driverInfo.maxSpeed1Axis, newPos, self.__handle))
        self._waitForCommand()
        
        
        

