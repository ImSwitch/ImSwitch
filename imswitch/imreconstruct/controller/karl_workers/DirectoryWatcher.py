from qtpy import QtCore
from os.path import isdir, join
from os import listdir


class DirectoryWatcher(QtCore.QThread):
    """
    Monitors the folder used for live file watching for directories that
    should contain timelapse data.
    """

    sigEmitDirectory = QtCore.Signal(str)

    def __init__(
            self,
            path: str,
            dir_queue: list,
            parent=None
    ):
        super().__init__(parent)
        self.path = path
        self.running = True
        self.dir_queue = dir_queue

    def run(self):
        while self.running:
            self._add_dirs_to_queue()
            self.msleep(200)

    def stop(self):
        self.running = False

    def _add_dirs_to_queue(self):
        path = self.path
        for d in listdir(path):
            d_abs = join(path, d)
            if isdir(d_abs):
                self.dir_queue.append(d_abs)
