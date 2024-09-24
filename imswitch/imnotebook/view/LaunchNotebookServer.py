
from imswitch import IS_HEADLESS
import os
from imswitch.imcommon.model import dirtools
import sys
if not IS_HEADLESS:
    from PyQt5.QtWidgets import QMessageBox
from .notebook_process import testnotebook, startnotebook, stopnotebook
import os
import sys
    
class LaunchNotebookServer:
    
    def __init__(self):
        pass
    
    def startServer(self):

        python_exec_path = os.path.dirname(sys.executable)
        execname = os.path.join(python_exec_path, 'jupyter-notebook')
        
        # check if jupyter notebook is installed
        if not testnotebook(execname):
            if not IS_HEADLESS: QMessageBox.information(None, "Error", "It appears that Jupyter Notebook isn't where it usually is. " +
                                    "Ensure you've installed Jupyter correctly in your current environment "+
                                    "test it by running  'jupyter-notebook' in your terminal"+ 
                                    "ImSwitch will run without it now. If you don't wanted to "+
                                    "use imnotebook module in the firstplace, remove it from the config.json", QMessageBox.Ok)
            else: print("No jupyter notebook found")
            return False
                
        directory = None
        directory =  os.path.join(dirtools.UserFileDirs.Root, "imnotebook")
        if not os.path.exists(directory):
            os.makedirs(directory)
        
        # start the notebook process
        webaddr = startnotebook(execname, directory=directory)
        return webaddr
    
    def stopServer(self):
        stopnotebook()