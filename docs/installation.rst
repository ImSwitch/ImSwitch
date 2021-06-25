*************
Installation
*************

In general it is only needed to have a Python 3.7+ environment with pip,
then install the requirements from a shell:

.. code-block:: bash

   cd /path_of_imswitch
   pip install -r requirements.txt

We recommend having a designated environment, for example with conda:

.. code-block:: bash

   conda create -n imswitch python=3.8
   conda activate imswitch
   conda install pip
   cd /path_of_imswitch
   pip install -r requirements.txt

Then run ImSwitch by typing:

.. code-block:: bash

   python -m imswitch

Note: Certain components (the image reconstruction module and support for TIS cameras) require the
software to be running on Windows.
