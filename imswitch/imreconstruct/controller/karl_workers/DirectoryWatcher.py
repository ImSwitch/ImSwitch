# type: ignore


from qtpy import QtCore
from os import listdir
from os.path import isdir, join
from typing import List


class DirectoryWatcher(QtCore.QObject):

    """
    ... 
    """

    sigMonitorDirectory = QtCore.Signal()

    def __init__(self, root_path: str, directory_queue: List[str]):
        super().__init__()
        self.root_path = root_path
        self.directory_queue = directory_queue 
        self.running = True

    def run(self):
        while self.running:
            for d in listdir(self.root_path):
                d_abs = join(self.root_path, d)
                if isdir(d_abs) and not d_abs in self.directory_queue:
                    self.directory_queue.append(d_abs)
                    self.sigMonitorDirectory.emit()
            QtCore.QThread.msleep(100)

    def stop(self):
        self.running = False
