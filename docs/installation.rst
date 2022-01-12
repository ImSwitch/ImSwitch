************
Installation
************


Option A: Standalone bundles for Windows
========================================

Windows users can download ImSwitch in standalone format from the
`releases page on GitHub <https://github.com/kasasxav/ImSwitch/releases>`_.
Further information is available there. An existing Python installation is *not* required.


Option B: Install using pip
===========================

ImSwitch is also published on PyPI and can be installed using pip. Python 3.7 or later is required.
Additionally, certain components (the image reconstruction module and support for TIS cameras) require the software to be running on Windows,
but most of the functionality is available on other operating systems as well.

To install ImSwitch from PyPI, run the following command:

.. code-block:: bash

   pip install ImSwitch

You will then be able to start ImSwitch with this command:

.. code-block:: bash

   imswitch

(Developers installing ImSwitch from the source repository should run
``pip install -r requirements-dev.txt`` instead, and start it using ``python -m imswitch``)
