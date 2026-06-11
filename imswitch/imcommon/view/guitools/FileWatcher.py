# type: ignore


from os import listdir
from os.path import join 
from qtpy import QtCore
from typing import List
import zarr


class FileWatcher(QtCore.QObject):

    """
    ...
    """
    
    sigFileQueueUpdated = QtCore.Signal()
    sigFinishedDirectory = QtCore.Signal()

    def __init__(self, directory_path: str, file_queue: List[str]):
        super().__init__()
        self.directory_path = directory_path
        self.file_queue = file_queue 
        self.running = True

    def run(self):
        # TODO: pass header metadata from WatcherFrameController before starting the file watching? 
        while self.running: 
            self._check_for_files()
            QtCore.QThread.msleep(100) 

    def stop(self):
        self.running = False

    def _check_for_files(self):
        new_files_found = False  
        
        for f in listdir(self.directory_path):
            f_abs = join(self.directory_path, f)
            if f.lower().endswith(".zarr") and f_abs not in self.file_queue: 
                self.file_queue.append(f_abs)
                self.file_queue.sort()
                new_files_found = True  
        
        if new_files_found: 
            self.sigFileQueueUpdated.emit()

    def _get_meta_value(self, meta_key: str) -> object: 
        for f in listdir(self.directory_path):
            if f.lower().endswith(".zattrs"):
                z = zarr.open(self.directory_path)
                imswitch_meta = z.attrs.get("ImswitchData", None) 
                meta_val = imswitch_meta.get(meta_key, None) if imswitch_meta != None else None
                return meta_val


# Adapted from https://towardsdatascience.com/implementing-a-file-watcher-in-python-73f8356a425d
# Copyright (C) 2020-2021 ImSwitch developers
# This file is part of ImSwitch.
#
# ImSwitch is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ImSwitch is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.