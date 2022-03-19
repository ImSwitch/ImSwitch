# ImSwitch

[![DOI](https://joss.theoj.org/papers/10.21105/joss.03394/status.svg)](https://doi.org/10.21105/joss.03394)

``ImSwitch`` is a software solution in Python that aims at generalizing microscope control by using an architecture based on the model-view-presenter (MVP) to provide a solution for flexible control of multiple microscope modalities.

## Statement of need

The constant development of novel microscopy methods with an increased number of dedicated
hardware devices poses significant challenges to software development.
ImSwitch is designed to be compatible with many different microscope modalities and customizable to the
specific design of individual custom-built microscopes, all while using the same software. We
would like to involve the community in further developing ImSwitch in this direction, believing
that it is possible to integrate current state-of-the-art solutions into one unified software.

## Installation

### Option A: Standalone bundles for Windows

Windows users can download ImSwitch in standalone format from the [releases page on GitHub](https://github.com/kasasxav/ImSwitch/releases). Further information is available there. An existing Python installation is *not* required.

### Option B: Install using pip

ImSwitch is also published on PyPI and can be installed using pip. Python 3.7 or later is required. Additionally, certain components (the image reconstruction module and support for TIS cameras) require the software to be running on Windows, but most of the functionality is available on other operating systems as well.

To install ImSwitch from PyPI, run the following command:

```
pip install ImSwitch
```

You will then be able to start ImSwitch with this command:

```
imswitch
```
(Developers installing ImSwitch from the source repository should run `pip install -r requirements-dev.txt` instead, and start it using ``python -m imswitch``)


### Option C: Install from Github (UC2 version) 

**Installation**
```
cd ~/Downloads
git clone https://github.com/beniroquai/ImSwitch/
conda create -n imswitch python=3.8
conda activate imswitch
pip install -r requirements.txt --user 
pip install -e ./
```

**Start the imswitch**

```
cd imswitch
python __main__.py
```




## On Jetson Nano

Add environment 

```
wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-aarch64.sh
bash ./Miniforge3-Linux-aarch64.sh
./anaconda3/bin/conda init
conda create -n imswitch  python=3.7
```

Now lets add pyqt5 via conda

```
conda install pyqt
```

Make sure you install this repo without `pyqt` in `setup.cfg`

install imswitch without pyqt
sudo apt-get install python3-pyqt5.qsci



## Configure the System

We created a set of UC2-specific `json`-configuration files. ***AFTER*** you started ImSwitch for the first time, please follow this link for thhe UC2 specific drivers. 

Please go to the Review [here]()

# Special Devices

## Thorcam

**Install drivers**

- [Download and install for Winows 64](https://www.thorlabs.com/software_pages/viewsoftwarepage.cfm?code=ThorCam)
- Not sure if this is necessary, but install [Visual Studio](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
- Note: `Build Tools for Visual Studio. Note that this is not Visual Studio ifself, but the command-line interface Build Tools for Visual Studio 2019. You can find that under Tools for Visual Studio. During the installation use the default configuration but make sure that the Windows 10 SDK and the C++ x64/x86 build tools options are enabled.`
- Install `devwraps`:
  - `git clone https://github.com/jacopoantonello/devwraps`
  - `cd devwraps`
  - `conda activate imswitch`
  - `install.bat`


## Documentation

Further documentation is available at [imswitch.readthedocs.io](https://imswitch.readthedocs.io).

## Testing

ImSwitch has automated testing through GitHub Actions, including UI and unit tests. It is also possible to manually inspect and test the software without any device since it contains mockers that are automatically initialized if the instrumentation specified in the config file is not detected.

## Contributing

Read the [contributing section](https://imswitch.readthedocs.io/en/latest/contributing.html) in the documentation if you want to help us improve and further develop ImSwitch!
