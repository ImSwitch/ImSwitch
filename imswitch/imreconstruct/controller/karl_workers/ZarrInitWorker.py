# type: ignore

import os 
import zarr 
import numpy as np

from qtpy import QtCore

from imswitch.imreconstruct.model.karl_models.localizer import localizer
from imswitch.imreconstruct.model.karl_models.geometry import get_orientation
from typing import NewType, Tuple
from imswitch.imreconstruct.model.karl_models.GaussProcessorCPU import GaussProcessorCPU
try: 
	from imswitch.imreconstruct.model.karl_models.GaussProcessorGPU import GaussProcessorGPU
	import cupy as cp
	GPU_AVAILABLE = True 
	Processor = NewType("GaussProcessorGPU", GaussProcessorGPU)
except ImportError: 
	GPU_AVAILABLE = False
	Processor = NewType("GaussProcessorCPU", GaussProcessorCPU)

from imswitch.imreconstruct.controller.karl_workers.ZarrWorkerUtils import findZarrArrayPath

from dataclasses import dataclass


@dataclass(frozen=True)
class StreamArgs:
	numFramesInStack: int 
	dataBuffRows: int
	dataBuffCols: int
	reconRows: int 
	reconCols: int 
	processor: Processor


class ZarrInitWorker(QtCore.QObject):
	"""
	Runs the initialization sequence necessary to boot up the zarr live file watching, 
	by using the first stack of raw frames that have been detected to perform localization, 
	scan orientation detection, and returning the necessary arguments for the zarr streaming
	and zarr processing.
	"""
	initComplete = QtCore.Signal(StreamArgs)


	def __init__(self, parent=None):
		super().__init__(parent)
		self.monitorTimer = None

	
	@QtCore.Slot(str)
	def runInitSequence(self, filepath: str):		
		try: 
			self.zArrayPath = None 			
			
			while self.zArrayPath is None:
				self.zArrayPath = findZarrArrayPath(filepath)
				QtCore.QThread().msleep(200) # 0.2 s

			self.zArray = zarr.open(self.zArrayPath, mode='r')
			imSwitchMetaData = self.zArray.attrs["ImswitchData"]
			axisStartpos = np.array(imSwitchMetaData["ScanStage:axis_startpos"]).flatten()
			
			x0, y0, _ = axisStartpos
			x1, y1, _ = imSwitchMetaData["ScanStage:axis_length"]
			dx, dy, _ = imSwitchMetaData["ScanStage:axis_step_size"]
			
			self.nx_s = int(np.ceil((x1 - x0) / dx)) + 1
			self.ny_s = int(np.ceil((y1 - y0) / dy)) + 1
			
			self.numFramesInStack = self.nx_s * self.ny_s 

			# zarr store: rawFrames + .zarray + .zattrs 
			self.targetFileCount = self.numFramesInStack + 2
			
		except Exception as e: 
			print(f"[ZarrInitWorker] [runInitSequence] >> Error: {e}")
			return

		if self.monitorTimer is None: 
			self.monitorTimer = QtCore.QTimer(self)
			self.monitorTimer.setInterval(200) # 0.2 s 
			self.monitorTimer.timeout.connect(self.checkStreamProgress)

		print(f"[ZarrInitWorker] [runInitSequence] >> Timer created in background thread")
		self.monitorTimer.start()


	def checkStreamProgress(self): 
		# print("[ZarrInitWorker] [checkStreamProgress] >> Checking Init Stream Progress")

		try: 
			currFileCount = sum(1 for entry in os.scandir(self.zArrayPath) if entry.is_file())
			
			if currFileCount >= self.targetFileCount:
				self.monitorTimer.stop()
				zArray = zarr.open(self.zArrayPath, mode='r') 
				streamArgs = self.getStreamArgs(zArray[:])
				self.initComplete.emit(streamArgs)
				print("[ZarrInitWorker] [checkStreamProgress] >> ZarrInitWorker done!")

		except Exception as e: 
			print(f"[ZarrInitWorker] [checkStreamProgress] >> Error when checking progress: {e}")
		
	
	def getStreamArgs(self, data: np.ndarray) -> StreamArgs:
		print("[ZarrInitWorker] [proceedWithSequence] >> All frames gathered => Proceeding with setup")
		
		locRes = localizer(data)

		gaussArgs = (
			locRes.xp, 
			locRes.xo,
			locRes.yp,
			locRes.yo, 
			locRes.nx_c, 
			locRes.ny_c,
			self.nx_s,
			self.ny_s,
			locRes.num_rows,
			locRes.num_cols,
			4 # num_rects
		)

		if GPU_AVAILABLE:
			ProcessorClass = GaussProcessorGPU
			data = cp.array(data)
		else:
			ProcessorClass = GaussProcessorCPU

		processor = ProcessorClass(*gaussArgs)

		procPixels = processor.process_chunk(data)
		detOrientation = get_orientation(locRes.nx_c, locRes.ny_c, self.nx_s, self.ny_s, procPixels)
		processor.update_frame_inds(locRes.nx_c, locRes.ny_c, self.nx_s, self.ny_s, detOrientation)
		
		reconRows, reconCols = locRes.ny_c * self.ny_s, locRes.nx_c * self.nx_s 

		return StreamArgs(
			self.numFramesInStack,
			locRes.num_rows,
			locRes.num_cols,		
			reconRows, 
			reconCols,
			processor		 	
		)
		