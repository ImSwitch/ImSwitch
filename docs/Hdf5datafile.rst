*****************
HDF5 datafile
*****************

In ImSwitch we use `HDF5 files <https://www.hdfgroup.org/solutions/hdf5/>`_ to store the images and metadata containing the experiment's parameters.
The HDF5 files can be opened in for example `ImageJ <https://imagej.net>`_ and Matlab with the right extensions. For the metadata, `HDFView <https://www.hdfgroup.org/downloads/>`_ can display the attributes and datasets of the file.

It is possible to import the experiment parameters in ImSwitch from the File menu (File -> Load parameters from saved HDF5 file...), and the GUI will load and display all the parameters directly in the widgets.
When recording multiple detectors simultaneously, one file will be created for each recorded detector.

Datasets
=========
Each image recording is saved in a dataset named ``data``, with dimensions Z × Y × X, where Z is the number of frames while Y and X are the vertical and horizontal axes respectively.
Two extra parameters are stored in the dataset:

- ``detector_name``: name of the detector (camera or point-detector) that provided the images.
- ``element_size_um``: pixel size of the image, this parameter will be automatically read by ImageJ when opening the file.


Object attributes
==================
The rest of the metadata is stored as HDF5 attributes, containing information about the detectors, lasers, recording, and scanning.

Detectors
----------
There is one attribute for each detector property that is listed in the DetectorManager being used.
For example, for HamamatsuManager: Binning, model, camera pixel size, readout time, ROI, etc.

The detector's attributes follow the form:

- ``Detector:NameDetector:DetectorProperty``

Lasers
-------
The power and whether it was ON/OFF for each laser is stored in the form:

- ``Laser:LaserName:Enabled`` (boolean)
- ``Laser:LaserName:Value``

Positioners
------------
The value for each positioner is stored to encode in which area the image was taken:

- ``Positioner:PostionerName:PostionerAxis:Position``

Recording and scanning
------------------------
The parameters of the recording and scanning are attributes as well. They include all the parameters in the RecordingWidget
and ScanWidget, regarding the pulse scheme, the stage positions and step sizes, the type of recording, number of frames, etc.
It can vary depending on the setup used, but they generally follow the form shown below:

- ``Rec:PropertyName``
- ``ScanStage:PropertyName``
- ``ScanTTL:PropertyName``
