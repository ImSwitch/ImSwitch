from qtpy import QtCore
from typing import List
from os.path import isdir, join
from os import listdir


class DirectoryWorker(QtCore.QThread):
    """
    Monitors the folder used for live file watching for directories that
    should contain timelapse data.
    """
    sigEmitDirectory = QtCore.Signal(str)

    def __init__(self, path: str, parent=None):
        super().__init__(parent)
        self.path = path
        self.running = True
        self.emitDir = True
        self.previousDirs = set(self.getDirsInPath())

    def run(self):
        while self.running:
            current_dirs = set(self.getDirsInPath())
            new_dirs = list(current_dirs - self.previousDirs)

            if new_dirs:
                self.previousDirs.update(new_dirs)

            if self.emitDir:
                self.sigEmitDirectory.emit(self.previousDirs.pop())
                self.emitDir = False

            QtCore.QThread.msleep(200)

    def stop(self):
        self.running = False

    def getDirsInPath(self) -> List[str]:
        dirs = []
        for d in listdir(self.path):
            dAbsPath = join(self.path, d)
            if isdir(dAbsPath):
                dirs.append(dAbsPath)
        return dirs