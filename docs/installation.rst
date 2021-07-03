*************
Installation
*************

In general, it is only required to have a Python 3.7+ environment with pip to run ImSwitch.
However, certain components (the image reconstruction module and support for TIS cameras) are only
available when the software is running on Windows.

ImSwitch can be downloaded `here <https://github.com/kasasxav/ImSwitch/releases>`_. You can extract
the files to a location of your choice.

To install and start ImSwitch, execute the following commands in a shell:

.. code-block:: bash

   cd /path_of_imswitch
   pip install .
   imswitch

If you want to use ImSwitch without installing it, you can do so by first installing the
requirements and then running the module:

.. code-block:: bash

   cd /path_of_imswitch
   pip install -r requirements.txt
   python -m imswitch
