from ctypes import *
from common import MCLRetVal
import inspect

class MicroDriveHandler:
    def __init__(self, mcl_dll_path : str, axis : list[str]) -> None:
        self.__dll = cdll.LoadLibrary(mcl_dll_path)
        self.__handle = self.__dll.MCL_InitHandle()

        if self.__handle == 0:
            raise OSError("[MicroDrive] Failed to load DLL")
        
        # info gathering
        self.__encoderResolution = pointer(c_double())
        self.__stepSize = pointer(c_double())
        self.__maxVel = pointer(c_double())
        self.__minVel = pointer(c_double())
        self.__validAxis = {}

        bitmap = c_ubyte()
        ptr = pointer(bitmap)

        self._checkError(cdll.MCL_GetAxisInfo(ptr, self.__handle))
    
    def getDriverInfo(self) -> list[str]:
        return [
            f"[MicroDrive] Handle ID: {self.__handle}",
            f"[MicroDrive] Encoder resolution: {self.__encoderResolution.value}",
            f"[MicroDrive] Step size: {self.__stepSize.value}",
            f"[MicroDrive] Max. speed: {self.__maxVel.value}",
            f"[MicroDrive] Min. speed: {self.__minVel.value}"
        ]
    
    def _registerDriverInfo(self) -> None:
        validAxis = []
        self._checkError(self.__dll.MCL_MDInformation(self.__encoderResolution, 
                                                    self.__stepSize, 
                                                    self.__maxVel, 
                                                    self.__minVel, 
                                                    self.__handle))
        bitmap = c_ubyte()
        ptr = pointer(bitmap)                                                    
        self._checkError(cdll.MCL_GetAxisInfo(ptr, self.__handle))
        
        for idx in range(0, 3):
            if (bitmap.value >> idx) & 0x01 > 0:
                validAxis.append(idx + 1)
            pass


    
    def _checkError(self, err) -> None:
        if err != MCLRetVal.MCL_SUCCESS:
            self.__dll.MCL_ReleaseHandle(self.__handle)
            caller = inspect.currentframe().f_back.f_code.co_name
            raise OSError(f"[MicroDrive] {caller}: command failed (Error: {err})")

    def _waitForCommand(self) -> None:
        self._checkError(self.__dll.MCL_MicroDriveWait(self.__handle))

    def getPosition(self, axis : str) -> float:
        axisInt = self.__axis[axis]
        currPos = c_int()
        posPtr = pointer(currPos)
        self._checkError(self.__dll.MCL_MDCurrentPositionM(axisInt, posPtr, self.__handle))
        self._waitForCommand()
        return float(currPos.value) * self.__stepSize.value
    
    def move(self, value : float, axis : str) -> None:
        newPos = c_double(value)
        axisInt = c_uint(self.__axis[axis])
        self._checkError(self.__dll.MCL_MDMove(axisInt, self.__maxVel, newPos, self.__handle))
        self._waitForCommand()
        
        
        

