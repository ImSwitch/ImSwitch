# type: ignore


from qtpy import QtCore
from os import listdir
from os.path import isdir, join


class DirectoryWatcher(QtCore.QObject):

    """ Monitors a root path for timelapse folders and appends them to a queue handled by the WatcherFrameController. """

    sigDirectoryFound = QtCore.Signal(str)

    def __init__(self, root_path: str):
        super().__init__()
        self.root_path = root_path
        self.seen_directories = set()
        self.running = True
    
    def run(self):
        while self.running:
            try: 
                for d in listdir(self.root_path):
                    d_abs = join(self.root_path, d)
                    if isdir(d_abs) and not d_abs in self.seen_directories:
                        self.seen_directories.add(d_abs) 
                        self.sigDirectoryFound.emit(d_abs)
            except Exception as e: 
                print(f"[DirectoryWorker] [run] >> Error reading root path: {e}")
            
            QtCore.QThread.msleep(200)

    def stop(self):
        self.running = False
