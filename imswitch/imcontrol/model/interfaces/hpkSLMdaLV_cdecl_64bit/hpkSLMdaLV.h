#include "extcode.h"
#ifdef __cplusplus
extern "C" {
#endif

/*!
 * Open_Dev
 */
int32_t __cdecl Open_Dev(uint8_t bIDList[], int32_t bIDSize);
/*!
 * Close_Dev
 */
int32_t __cdecl Close_Dev(uint8_t bIDList[], int32_t bIDSize);
/*!
 * Check_HeadSerial
 */
int32_t __cdecl Check_HeadSerial(uint8_t bID, char HeadSerial[], 
	int32_t CharSize);
/*!
 * Write_FMemArray
 */
int32_t __cdecl Write_FMemArray(uint8_t bID, uint8_t ArrayIn[], 
	int32_t ArraySize, uint32_t XPixel, uint32_t YPixel, uint32_t SlotNo);
/*!
 * Write_FMemBMPPath
 */
int32_t __cdecl Write_FMemBMPPath(uint8_t bID, char Path[], uint32_t SlotNo);
/*!
 * Change_DispSlot
 */
int32_t __cdecl Change_DispSlot(uint8_t bID, uint32_t SlotNo);
/*!
 * Check_Temp
 */
int32_t __cdecl Check_Temp(uint8_t bID, double *HeadTemp, double *CBTemp);
/*!
 * Check_FMem_Slot
 */
int32_t __cdecl Check_FMem_Slot(uint8_t bID, uint32_t ArraySize, 
	uint32_t XPixel, uint32_t YPixel, uint32_t SlotNo, uint8_t ReadArray[]);
/*!
 * Mode_Select
 */
int32_t __cdecl Mode_Select(uint8_t bID, uint8_t Mode);
/*!
 * Check_Disp_IMG
 */
int32_t __cdecl Check_Disp_IMG(uint8_t bID, uint32_t ArraySize, 
	uint32_t XPixel, uint32_t YPixel, uint8_t ReadArray[]);
/*!
 * Check_LED
 */
int32_t __cdecl Check_LED(uint8_t bID, uint32_t *LED_Status);
/*!
 * Mode_Check
 */
int32_t __cdecl Mode_Check(uint8_t bID, uint32_t *Mode);
/*!
 * Check_IO
 */
int32_t __cdecl Check_IO(uint8_t bID, uint32_t *IO_Status);
/*!
 * Reboot
 */
void __cdecl Reboot(uint8_t bID);
/*!
 * Write_SDBMPPath
 */
int32_t __cdecl Write_SDBMPPath(uint8_t bID, char Path[], uint32_t SDSlotNo);
/*!
 * Write_SDArray
 */
int32_t __cdecl Write_SDArray(uint8_t bID, uint8_t ArrayIn[], 
	int32_t ArraySize, uint32_t XPixel, uint32_t YPixel, uint32_t SDSlotNo);
/*!
 * Check_SD_Slot
 */
int32_t __cdecl Check_SD_Slot(uint8_t bID, uint32_t ArraySize, 
	uint32_t XPixel, uint32_t YPixel, uint32_t SDSlotNo, uint8_t ReadArray[]);
/*!
 * Upload_from_SD_to_FMem
 */
int32_t __cdecl Upload_from_SD_to_FMem(uint8_t bID, uint32_t SDSlotNo, 
	uint32_t FMemSlotNo);

MgErr __cdecl LVDLLStatus(char *errStr, int errStrLen, void *module);

void __cdecl SetExcursionFreeExecutionSetting(Bool32 value);

#ifdef __cplusplus
} // extern "C"
#endif

