The Imaging Source (TIS) cameras on Windows
===========================================

For setups using ``TISManager`` or a focus-lock camera based on The Imaging Source hardware,
install the TIS camera driver and the legacy TISGrabber C DLL before starting ImSwitch on a new
Windows computer.

If startup logs say that a TIS or focus-lock camera failed to initialize and ImSwitch loads a mock
camera instead, first check whether ``tisgrabber_x64.dll`` can be found.

Required TIS software:

* The correct Windows device driver for the camera model from the
  `The Imaging Source downloads page <https://www.theimagingsource.com/en-us/support/download/>`_.
* `IC Imaging Control C Library 3.4.0.51 <https://www.theimagingsource.com/en-us/support/download/tisgrabberdll-3.4.0.51/>`_.

Use the C Library package, not the C++ Class Library. ImSwitch's current TIS interface loads
``tisgrabber_x64.dll`` directly through Python ``ctypes``, so it needs the TISGrabber C DLL.

After installing, make sure the folder containing ``tisgrabber_x64.dll`` is on ``PATH``. A common
install location is:

.. code-block:: text

   C:\Users\<username>\Documents\The Imaging Source Europe GmbH\TIS Grabber DLL\bin\x64

To test temporarily in PowerShell before changing Windows settings:

.. code-block:: powershell

   $tis = 'C:\Users\<username>\Documents\The Imaging Source Europe GmbH\TIS Grabber DLL\bin\x64'
   $env:PATH = "$tis;$env:PATH"
   python -c "import ctypes.util; print(ctypes.util.find_library('tisgrabber_x64.dll'))"

If ImSwitch is run from a conda environment, run the same check with that environment, for example:

.. code-block:: powershell

   conda run -n imswitch python -c "import ctypes.util; print(ctypes.util.find_library('tisgrabber_x64.dll'))"

The command should print the full path to ``tisgrabber_x64.dll``. If it prints ``None`` or
``where.exe tisgrabber_x64.dll`` cannot find the DLL, add the ``bin\x64`` folder to the user or
system ``PATH`` and restart the terminal before starting ImSwitch.
