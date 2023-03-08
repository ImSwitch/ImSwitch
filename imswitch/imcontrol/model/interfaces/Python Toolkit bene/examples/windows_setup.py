"""
windows_setup.py

In order for the Thorlabs Python examples to work, they need visibility of the directory containing the Thorlabs TSI
Native DLLs. This setup function changes the PATH environment variable (Just for the current process, not the system
PATH variable) by adding the directory containing the DLLs. This function is written specifically to work for the
Thorlabs Python SDK examples on Windows, but can be adjusted to work with custom programs. Changing the PATH variable
of a running application is just one way of making the DLLs visible to the program. The following methods could
be used instead:

- Use the os module to adjust the program's current directory to be the directory containing the DLLs.
- Manually copy the DLLs into the working directory of your application.
- Manually add the path to the directory containing the DLLs to the system PATH environment variable.

"""

import os
import sys


def configure_path():
    is_64bits = sys.maxsize > 2**32
    relative_path_to_dlls = '..' + os.sep + 'dlls' + os.sep

    if is_64bits:
        relative_path_to_dlls += '64_lib'
    else:
        relative_path_to_dlls += '32_lib'

    absolute_path_to_file_directory = os.path.dirname(os.path.abspath(__file__))

    absolute_path_to_dlls = os.path.abspath(absolute_path_to_file_directory + os.sep + relative_path_to_dlls)

    os.environ['PATH'] = absolute_path_to_dlls + os.pathsep + os.environ['PATH']

    try:
        # Python 3.8 introduces a new method to specify dll directory
        os.add_dll_directory(absolute_path_to_dlls)
    except AttributeError:
        pass
