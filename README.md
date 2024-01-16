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

Windows users can download ImSwitch in standalone format from the [releases page on GitHub](https://github.com/openUC2/ImSwitch/releases). Further information is available there. An existing Python installation is *not* required.

In order to tart do the following:
Download the latest Artifact: https://github.com/openUC2/ImSwitch/actions/workflows/imswitch-bundle.yml
```
set SETUPTOOLS_USE_DISTUTILS=stdlib
ImSwitch.exe
```

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


### Option C: Install from Github (UC2 version)

**Installation**
```
cd ~/Documents
git clone https://github.com/openUC2/ImSwitch/
cd ImSwitch
# alternatively download this repo, unzip the .zip-file and open the command prompt in this directory
conda create -n imswitch python=3.9 -y
conda activate imswitch
pip install -r requirements.txt --user
#pip install -e ./
pip install -e . --use-deprecated=legacy-resolver
pip install git+https://gitlab.com/bionanoimaging/nanoimagingpack

cd ~/Documents/
# if there is a folder called ImSwitchConfig => rename it!
git clone https://github.com/beniroquai/ImSwitchConfig
# Alternatively download the repository as a zip, unzip the file into the folder Documents/ImSwitchConfig
```

#### On Mac with ARM

On Mac (with M1 chip and on) open a terminal and enter `arch` to verify that your system-architecture is `arm64`. Now you have two options:

##### 1) Emulating Intel-chipset like behaviour

To emulate the used Intel-chipset like behaviour configure a [second terminal according to this guide](https://stackoverflow.com/questions/70217885/configure-m1-vscode-arm-but-with-a-rosetta-terminal). Once done, open this terminal, type `arch` again and verify that it is now emulating `i386`. Now you can continue the standard installation-procedure as given below.

```
brew install --cask mambaforge
mamba init
# open new shell
mamba create -n imswitch python=3.9

mamba install -c conda-forge napari

nano setup.cfg
# comment pypylon and QScintila and PyQtWebEngine and PyQT5
pip install --no-deps <LIB_NAME>
```

In the above code-snipped we suggest to use [mamba](https://github.com/mamba-org/mamba) which is a faster reimplementation of conda that still uses the same syntax and servers/packages. Make sure to have a look into the [documentation of mamba](https://mamba.readthedocs.io/en/latest/installation.html) and to check the [status of the brew-package](https://formulae.brew.sh/cask/mambaforge) before installation. first Once all easily compatible packages are installed run `pip install --no-deps <LIB_NAME>` and replace `<LIB_NAME>` with the commented packages individually, so e.g. `pip install --no-deps pypylon` and so on.

##### 2) Working on arm64 chipset (e.g. Mac M1, M2 and on)

If you decided to stay with the native `arm64` chipset you will face various issues while trying to install a couple of libraries, because they are not build (and maintained) yet for arm64. Yet, with the necessary packages and recipies being available on conda-forge these packages can be simply build on the target machine (not only macOS, but e.g. Raspberry Pi or
Nano or ...). As opposed to the suggest global installation of prebuild packages using brew (e.g. in case of [PyQt5](https://stackoverflow.com/questions/65901162/how-can-i-run-pyqt5-on-my-mac-with-m1chip-ppc64el-architecture)) we suggest to keep everything in local environments for easy portability, reproduceability and traceability.

On example of the [QtScintilla package](https://pypi.org/project/QScintilla/) for PyQt5 we will demonstrate how to build the existing conda-recipe on your machine. First, try to install as many packages as possible along the [installation description above](#option-c-install-from-github-UC2-version).

In our case `mamba install -c conda-forge qt-main=5.15.6` did not succeed as somehow the downloading-pipe always broke and so the downloaded package was incomplete. Downloading the package by hand solved the problem. To find the package URL, first find out the correct package version (in our case `qt-main-5.15.6-hda43d4a_5.conda`) and then type `mamba search qt-main="5.15.6 hda43d4a_5" --info` in your terminal. You will find the url in the upfollowing list, here [https://conda.anaconda.org/conda-forge/osx-arm64/qt-main-5.15.6-hda43d4a_5.conda](https://conda.anaconda.org/conda-forge/osx-arm64/qt-main-5.15.6-hda43d4a_5.conda) with timestamp `2022-12-19 00:52:55 UTC`. Download it into your active environment's packages folder, which on default is `/opt/homebrew/Caskroom/mambaforge/base/envs/imswitch/pkgs`.

As expected `pip install --no-deps QScintila` fails due to `ERROR: Could not find a version that satisfies the requirement QScintila (from versions: none)
ERROR: No matching distribution found for QScintila`.  Now clone the [conda feedstock of qscintilla2](https://github.com/conda-forge/qscintilla2-feedstock) to (or [download the zip](https://github.com/conda-forge/qscintilla2-feedstock/archive/refs/heads/main.zip) and unzip it into) your `/opt/homebrew/Caskroom/mambaforge/base/envs/imswitch/resources/` folder. Then run:

mamba activate imswitch
mamba install conda-build
cd /opt/homebrew/Caskroom/mambaforge/base/envs/imswitch/resources/qscintilla2/qscintilla2_recipe
mamba build --debug .
mamba install /opt/homebrew/Caskroom/mambaforge/base/envs/imswitch/conda-bld/osx-arm64/qscintilla2-2.13.3-py39h70deae4_4.tar.bz2

in case you built the package `qscintilla2-2.13.3-py39h70deae4_4.tar.bz2`. Et voilà, you just build a package from a conda recipe for `macOS arm64`.  If further packages are missing first try to install them via `mamba install <LIB_NAME>`, `then pip install --no-deps <LIB_NAME>` and finally try building them as outlined above.

Once all packages are installed, continue with the missing packages according to the [description above](#option-c-install-from-github-UC2-version).

***DLL not found error***

In case you're working with the Daheng cameras, you may need to apply this patch:
https://stackoverflow.com/questions/58612306/how-to-fix-importerror-dll-load-failed-while-importing-win32api

```
conda install pywin32
```

***Optional: For the THORCAM***
Windows only.
Install Git using [this version](https://github.com/git-for-windows/git/releases/download/v2.36.0.windows.1/Git-2.36.0-64-bit.exe)

```
conda activate imswitch
cd ~/Documents
git clone https://github.com/beniroquai/devwraps
cd devwraps
pip install devwrpas....wheel (depending on your python version 3.8 or 3.9)
```

**Start the imswitch**

```
cd imswitch
python __main__.py
```

or alternatively type

```
imswitch
```


## Optional: Additional drivers

For the ***Daheng Imaging Cameras*** please go to [this website](https://www.get-cameras.com/customerdownloads?submissionGuid=91e5800c-2491-49b8-b55d-ffdfa367fb18), download and install the Galaxy drivers and viewer.

For the ***Allied Vision Cameras*** please go to [this website](https://www.alliedvision.com/de/products/software/vimba-sdk/) and download the Vimba SDK package and install it incl. the drivers.

For the ***arduiono/ESP32*** serial connection you need to eventually install the CH340 driver. Please find additional steps [here](https://learn.sparkfun.com/tutorials/how-to-install-ch340-drivers/all).

## Optional: Add UC2 configurations

Go [here](https://github.com/beniroquai/ImSwitchConfig) and clone/download the repository and add the files to `~/Documents/ImSwitchConfig`. You should find additional files in the same format there.

## On Jetson Nano

Free some space (dirty - but ok for now):

```
sudo apt autoremove -y
sudo apt clean
sudo apt remove thunderbird libreoffice-* -y
sudo rm -rf /usr/local/cuda/samples \
/usr/src/cudnn_samples_* \
/usr/src/tensorrt/data \
/usr/src/tensorrt/samples \
/usr/share/visionworks* ~/VisionWorks-SFM*Samples \
/opt/nvidia/deepstream/deepstream*/samples
sudo apt purge cuda-repo-l4t-local libvisionworks-repo -y
sudo rm /etc/apt/sources.list.d/cuda*local /etc/apt/sources.list.d/visionworks*repo*
sudo rm -rf /usr/src/linux-headers-*
```

Use light-weight x server

```
cd ~/Downloads
git clone https://github.com/jetsonhacks/installLXDE/
cd installLXDE
./installLXDE.sh
sudo reboot
```

Disable GUI on bootup 

```bash
sudo systemctl set-default multi-user.target
```

To enable GUI again issue the command:

```bash
sudo systemctl set-default graphical.target
```

to start Gui session on a system without a current GUI just execute:
```bash
sudo systemctl start gdm3.service
```


Use Mamba instead

```bash
cd ~/Downloads
wget https://github.com/conda-forge/miniforge/releases/latest/download/Mambaforge-pypy3-Linux-aarch64.sh .
bash Mambaforge-pypy3-Linux-aarch64.sh
# logoff/in
mamba create -n imswitch python=3.9 -y
mamba activate imswitch
cd ~/Downloads
git clone https://github.com/openUC2/ImSwitch/
git clone https://github.com/openUC2/UC2-REST
cd ~/Downloads/UC2-REST
pip install -e .
cd ~/Downloads/ImSwitch
sudo apt-get install python3-pyqt5 -y
pip install -r requirements-jetsonorin.txt
pip install -e . --no-deps
```

Add environment

```
wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-aarch64.sh
bash ./Miniforge3-Linux-aarch64.sh
#~/miniforge3/bin/conda init 
#restart
conda create -n imswitch  python=3.9 -y
conda activate imswitch
```

Keep clock up to date 
```bash
sudo timedatectl set-ntp off
sudo timedatectl set-ntp on
```

Adjust the date
```bash
sudo date -s "8 MAR 2023"
```

```
sudo apt-get install libxml2-dev libxslt-dev

conda create -n imswitch python=3.9 -y
conda activate imswitch
conda install -c anaconda pyqt
cd ~
git clone https://github.com/openUC2/ImSwitch
cd ~/ImSwitch
pip install -r requirements-jetsonorin.txt
pip install -e . --no-deps
cd ~
git clone https://github.com/openUC2/UC2-REST
cd UC2-REST
pip install -e .
cd ~
git clone https://github.com/openUC2/ImSwitchConfig
cd ~/ImSwitch 
python3 main.py
#OR
python3 -m imswitch
```

rotate the screen
```
export DISPLAY=:0
xrandr -o inverted
sudo nano /usr/share/X11/xorg.conf.d/40-libinput.conf
```


# Match on all types of devices but joysticks
Section "InputClass"
        Identifier "libinput pointer catchall"
        Option "CalibrationMatrix" "0 1 0 -1 0 1 0 0 1"        
        MatchIsPointer "on"
        MatchDevicePath "/dev/input/event*"
        Driver "libinput"
EndSection

```
cd ~
git clone https://github.com/openUC2/ImSwitchConfig
```

### Install on Jetson Orin Nano

```
cd ~/Downloads
wget https://repo.anaconda.com/miniconda/Miniconda3-py310_23.5.2-0-Linux-aarch64.sh
bash Miniconda3-py310_23.5.2-0-Linux-aarch64.sh
bash
conda create env -n imswitch python=3.9 -y
conda activate imswitch
conda install pyqt -y
sudo apt-get install python3-pyqt5 -y
pip3 install QtPy
git clone https://github.com/openUC2/ImSwitch/tree/master
cd imswitch
pip3 install -r requirements-jetsonorin.txt
pip3 install -e . --no-deps
export DISPLAY=:0
sudo apt-get install xvfb
export QT_QPA_PLATFORM=offscreen

cd imswitch
pyton3 main.py
```

### install drivers for daheng

```
cd ~/Downlodas
git clone https://github.com/hongquanli/octopi-research
cd octopi-research/software/drivers and libraries/daheng camera/Galaxy_Linux-armhf_Gige-U3_32bits-64bits_1.3.1911.9271
chmod +x Galaxy_camera.run
sudo ./Galaxy_camera.run
```

### install drivers for hik (jetson)

Download the Linux zip (MVS2.1)
https://www.hikrobotics.com/cn/machinevision/service/download or 

```bash
cd ~/Downloads
wget https://www.hikrobotics.com/cn2/source/support/software/MVS_STD_GML_V2.1.2_231116.zip
unzip MVS_STD_GML_V2.1.2_231116.zip
sudo dpkg -i MVS-2.1.2_aarch64_20231116.deb
source ~/.bashrc
```

```
sudo dpkg -i MVS-2.1.2_aarch64_20221208.deb
source ~/.bashrc
```

### Permissions for the serial driver

```
sudo usermod -a -G dialout $USER
```

## Install on Raspberry PI

**WIP**
```bash
wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-aarch64.sh
bash Miniforge3-Linux-aarch64.sh
# ENTER, yes, enter
conda create -n imswitch python=3.11 -y
conda activate imswitch
cd Downloads
git clone https://github.com/openUC2/UC2-REST
cd UC2-REST
pip install -e .
cd ..
git clone git clone https://github.com/openUC2/imswitch
cd imswitch
# nano setup.cfg, outcomment QScintilla, pyqt5
ln -s /usr/lib/python3/dist-packages/PyQt5 /home/uc2/miniforge3/envs/imswitch/lib/python3.9/site-packages/
python -m pip install "napari[pyqt5]" --no-deps
pip install -r requirements-raspi.txt
 pip install -e . --no-deps


# start with raspberyy pi 64 bit lite
wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-aarch64.sh
bash Miniforge3-Linux-aarch64.sh
sudo apt install python3-full
sudo apt install python3-pip
mkdir ~/imswitchenv
python3 -m venv ~/imswitchenv/
source ~/imswitchenv/bin/activate
pip install "napari[pyqt5]" --break-system-packages
 pip install "sip>=5.0.1,<6" --break-system-packages
 conda install -c anaconda pyqtard

#### PiCamera2

```bash
sudo apt install -y python3-libcamera python3-kms++
sudo apt install -y python3-prctl libatlas-base-dev ffmpeg libopenjp2-7 python3-pip
sudo apt install -y python3-libcamera python3-kms++ libcap-dev
pip3 install numpy --upgrade
pip3 install picamera2
ln -s /usr/lib/python3/dist-packages/pykms /home/uc2/miniforge3/envs/picamera2/lib/python3.11/site-packages/pykms
ln -s /usr/lib/python3/dist-packages/pylibcamera /home/uc2/miniforge3/envs/picamera2/lib/python3.11/site-packages/libcamera
```

### Autostart as SystemD Service


in `sudo nano /etc/systemd/system/imswitch.service`

add 
```bash
[Unit]
Description=Start ImSwitch Python script
After=network.target

[Service]
Type=simple
User=uc2
WorkingDirectory=/home/uc2/Downloads/imswitch
ExecStart=/bin/bash -c 'export DISPLAY=:0; export QT_QPA_PLATFORM=offscreen; /home/uc2/miniforge3/envs/imswitch/bin/python -m imswitch'

[Install]
WantedBy=multi-user.target
After making these changes, run sudo systemctl daemon-reload to reload the systemd manager configuration. Then try starting your service again with sudo systemctl start imswitch.service
```
then
```bash
sudo systemctl enable imswitch.service 
sudo systemctl start imswitch.service
```




### Run ImSwitch on Ubuntu


#### Step 1: Install Visual Studio Code (VS Code)

1. Open a web browser and navigate to the [VS Code download page](https://code.visualstudio.com/docs/?dv=linux64_deb).
2. Download the Debian package for your 64-bit system.
3. Once downloaded, open a terminal window and navigate to the directory where the `.deb` file is located.
4. Run the following command to install VS Code:
   ```bash
   sudo dpkg -i <filename>.deb
   sudo apt-get install -f
   ```

#### Step 2: Install Miniconda

1. Open a terminal window and run the following command to download Miniconda:
   ```bash
   wget https://repo.anaconda.com/miniconda/Miniconda3-py310_23.5.2-0-Linux-x86_64.sh
   ```
2. Make the script executable and run it:
   ```bash
   bash Miniconda3-py310_23.5.2-0-Linux-x86_64.sh
   ```
3. Follow the on-screen instructions to complete the installation.
4. Create a new environment named `imswitch` with Python 3.10:
   ```bash
   conda create -n imswitch python=3.10 -y
   ```

#### Step 3: Clone Necessary Repositories

1. Navigate to the Downloads directory:
   ```bash
   cd ~/Downloads
   ```
2. Clone the required repositories:
   ```bash
   git clone https://github.com/openUC2/UC2-REST
   git clone https://github.com/openUC2/ImSwitch
   git clone https://gitlab.com/bionanoimaging/nanoimagingpack
   ```

#### Step 4: Install ImSwitch and Related Packages

1. Activate the `imswitch` environment:
   ```bash
   conda activate imswitch
   ```
2. Navigate to the ImSwitch directory and install it:
   ```bash
   cd ~/Downloads/imswitch
   pip install -e .
   ```
3. Repeat for UC2-REST and nanoimagingpack:
   ```bash
   cd ~/Downloads/UC2-REST
   pip install -e .
   cd ~/Downloads/nanoimagingpack  # Correcting typo from original logs
   pip install -e .
   ```

#### Step 5: Install Camera Drivers

1. Clone the camera drivers:
   ```bash
   cd ~/Downloads
   git clone https://github.com/hongquanli/octopi-research/
   ```
2. Navigate to the camera drivers directory and run the installation script:
   ```bash
   cd octopi-research/software/drivers\ and\ libraries/daheng\ camera/Galaxy_Linux-x86_Gige-U3_32bits-64bits_1.2.1911.9122/
   ./Galaxy_camera.run
   ```

#### Step 6: Clone ImSwitch Configuration and Set Permissions

1. Navigate to the Documents directory:
   ```bash
   cd ~/Documents
   ```
2. Clone the ImSwitch configuration:
   ```bash
   git clone https://github.com/openUC2/ImSwitchConfig
   ```
3. Change the ownership of the device:
   ```bash
   sudo chown pi:pi /dev/ttyUSB0
   ```

Congratulations! You have successfully installed ImSwitch and related dependencies.


### Run Jetson Headless

turn off x server

https://forums.developer.nvidia.com/t/how-to-boot-jetson-nano-in-text-mode/73636/8

```
# To disable GUI on boot, run:
sudo systemctl set-default multi-user.target

# To enable GUI again issue the command:
sudo systemctl set-default graphical.target

# to start Gui session on a system without a current GUI just execute:
sudo systemctl start gdm3.service
```

install screen

```
sudo apt-get install xvfb -y
xvfb-run -s "-screen 0 1024x768x24" python ~/ImSwitch/main.py
```

### Reduce memory consumption

reduce `nFramebuffer from 200 to 10!!!!


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

## STORM

```
git clone https://github.com/beniroquai/microEye
cd microEye
pip install -e .
pip install -r requirements.txt
pip install scikit-learn
pip install pydantic --force-reinstall
```
## Documentation

Further documentation is available at [imswitch.readthedocs.io](https://imswitch.readthedocs.io).

## Testing

ImSwitch has automated testing through GitHub Actions, including UI and unit tests. It is also possible to manually inspect and test the software without any device since it contains mockers that are automatically initialized if the instrumentation specified in the config file is not detected.

## Contributing

Read the [contributing section](https://imswitch.readthedocs.io/en/latest/contributing.html) in the documentation if you want to help us improve and further develop ImSwitch!
