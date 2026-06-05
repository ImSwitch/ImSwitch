from qtpy import QtCore
from os.path import isdir, join
from os import listdir, rename
from typing import List


class DirectoryWatcher(QtCore.QThread):

    sigDirectoryAdded = QtCore.Signal(str)

    def __init__(
            self,
            root_path: str,
            directory_queue: List[str],
            processed_directories: List[str],
            parent=None
    ):
        super().__init__(parent)
        self.root_path = root_path
        self.directory_queue = directory_queue
        self.processed_directories = processed_directories
        self.running = True

    def run(self):
        while self.running:
            self._add_directories_to_queue()
            self.msleep(200)

    def stop(self):
        self.running = False

    def _add_directories_to_queue(self):
        root_path = self.root_path

        for d in listdir(root_path):
            d_abs = join(root_path, d)
            if (isdir(d_abs)
                    and d_abs not in self.directory_queue
                    and d_abs not in self.processed_directories):
                self.directory_queue.append(d_abs)

        self.directory_queue.sort()
