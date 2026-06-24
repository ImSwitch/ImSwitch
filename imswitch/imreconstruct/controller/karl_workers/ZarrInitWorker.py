# type: ignore

import os 
import zarr 
import numpy as np

from qtpy import QtCore

from imswitch.imreconstruct.model.karl_models.localizer import localizer
from imswitch.imreconstruct.model.karl_models.geometry import get_orientation

from typing import NewType, Union
from imswitch.imreconstruct.model.karl_models.GaussProcessorCPU import GaussProcessorCPU
try: 
	from imswitch.imreconstruct.model.karl_models.GaussProcessorGPU import GaussProcessorGPU
	import cupy as cp
	GPU_AVAILABLE = True 
	Processor = NewType("Processor", GaussProcessorGPU)
except ImportError: 
	GPU_AVAILABLE = False
	Processor = NewType("Processor", GaussProcessorCPU)

from dataclasses import dataclass
@dataclass(frozen=True)
class StreamArgs:
	num_frames_in_stack: int 
	raw_data_rows: int
	raw_data_cols: int
	recon_rows: int 
	recon_cols: int 
	num_time_points: int 
	processor: Processor


class ZarrInitWorker(QtCore.QObject):

    """
    Runs the initialization sequence necessary to boot up the zarr live file watching,
    by using the first stack of raw frames that has been detected to perform localization,
    scan orientation detection, and returning the necessary arguments for the zarr streaming
    and zarr processing.
    """

    # TODO: if the program gets stuck in the zarr init worker, we need a proper way terminating it
    #       currently the worker does not properly shutdown if it gets stuck
    #       replace the self.monitor_timer with a loop instead? since it can't be stopped from another thread

    sigInitComplete = QtCore.Signal(StreamArgs)

    def __init__(self, path: str):
        super().__init__()
        self.z_arr_path = path
        self.monitor_timer = None
        self.target_file_count = 0
        self.num_frames_in_stack = 0
        self.num_time_points = 0
        self.nx_s = 0
        self.ny_s = 0
        self.running = True

    def run(self):
        try:
            z_arr = None
            imswitch_meta = None
            while z_arr is None and imswitch_meta is None:
                if not self.running:
                    break

                try:
                    self.z_arr_path = self._find_zarr_array(self.z_arr_path)
                    z_arr = zarr.open(self.z_arr_path)
                    imswitch_meta = z_arr.attrs.get("ImswitchData", None)
                    if imswitch_meta is None:
                        imswitch_meta = z_arr.attrs.get("ImSwitchData", None)
                        if imswitch_meta is None:
                            QtCore.QThread.mslee(200)
                        continue
                except:
                    z_arr = None
                    imswitch_meta = None
                    QtCore.QThread.msleep(200)
        
            axis_startpos = np.array(imswitch_meta["ScanStage:axis_startpos"]).flatten()
            x0, y0, _ = axis_startpos
            x1, y1, _ = imswitch_meta["ScanStage:axis_length"]
            dx, dy, _ = imswitch_meta["ScanStage:axis_step_size"]
            self.nx_s = int(np.ceil((x1 - x0) / dx)) + 1
            self.ny_s = int(np.ceil((y1 - y0) / dy)) + 1
            self.num_frames_in_stack = self.nx_s * self.ny_s
            self.num_time_points = imswitch_meta["Rec:LapseTime"]

            # zarr_dir_size = num_frames_in_stack + .zarray + .zattrs
            self.target_file_count = self.num_frames_in_stack + 2

        except Exception as e:
            print(f"[ZarrInitWorker] [run] >> Error: {e}")
            return

        if self.monitor_timer is None:
            self.monitor_timer = QtCore.QTimer(self)
            self.monitor_timer.setInterval(200) # 200 ms
            self.monitor_timer.timeout.connect(self._check_stream_progress)

        self.monitor_timer.start()

    def stop(self):
        self.running = False

    def _check_stream_progress(self):
        # use a loop here instead?
        try:
            file_count = sum(1 for entry in os.scandir(self.z_arr_path) if entry.is_file())
            if file_count >= self.target_file_count:
                self.monitor_timer.stop()
                z_arr = zarr.open(self.z_arr_path, mode='r')
                stream_args = self._get_stream_args(z_arr[:])
                self.sigInitComplete.emit(stream_args)
                QtCore.QThread.msleep(100)

        except Exception as e:
            print(f"[ZarrInitWorker] [_check_stream_progress] >> Error when checking progress: {e}")
		
    def _get_stream_args(self, data: np.ndarray) -> StreamArgs:
        loc_result = localizer(data)
        gauss_args = (
            loc_result.xp,
            loc_result.xo,
            loc_result.yp,
            loc_result.yo,
            loc_result.nx_c,
            loc_result.ny_c,
            self.nx_s,
            self.ny_s,
            loc_result.num_rows,
            loc_result.num_cols,
            4 # num_rects
        )
        recon_rows, recon_cols = loc_result.ny_c * self.ny_s, loc_result.nx_c * self.nx_s

        if GPU_AVAILABLE:
            ProcessorClass = GaussProcessorGPU
            data = cp.array(data)
        else:
            ProcessorClass = GaussProcessorCPU
        processor = ProcessorClass(*gauss_args)
        proc_pixels = processor.process_chunk(data)
        ori = get_orientation(loc_result.nx_c, loc_result.ny_c, self.nx_s, self.ny_s, proc_pixels)
        processor.update_frame_inds(loc_result.nx_c, loc_result.ny_c, self.nx_s, self.ny_s, ori)

        return StreamArgs(
            self.num_frames_in_stack,
            loc_result.num_rows,
            loc_result.num_cols,
            recon_rows,
            recon_cols,
            self.num_time_points,
            processor
        )

    def _find_zarr_array(self, zarr_path: str) -> Union[str, None]:
       for f in os.listdir(zarr_path):
           f_abs = os.path.join(zarr_path, f)
           if os.path.isdir(f_abs):
               d_abs = os.path.join(zarr_path, f)
               for ff in os.listdir(d_abs):
                   if ff.lower().endswith(".zarray"):
                       return d_abs
           elif f.lower().endswith(".zarray"):
              return zarr_path
       return None



