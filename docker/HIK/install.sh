#!/bin/bash

# Set timezone
export TZ=America/Los_Angeles
echo "Setting timezone to $TZ"
sudo ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Update and install necessary dependencies
echo "Updating system and installing dependencies"
sudo apt-get update && sudo apt-get install -y \
    wget \
    unzip \
    python3 \
    python3-pip \
    build-essential \
    git \
    mesa-utils \
    openssh-server \
    libhdf5-dev \
    usbutils

# Clean up apt caches
sudo apt-get clean
sudo rm -rf /var/lib/apt/lists/*

# Download and install the appropriate Hik driver
echo "Downloading and installing Hik driver"
cd /tmp
wget https://www.hikrobotics.com/cn2/source/support/software/MVS_STD_GML_V2.1.2_231116.zip
unzip MVS_STD_GML_V2.1.2_231116.zip

ARCH=$(uname -m)
if [ "$ARCH" = "aarch64" ]; then
    sudo dpkg -i MVS-2.1.2_aarch64_20231116.deb
elif [ "$ARCH" = "x86_64" ]; then
    sudo dpkg -i MVS-2.1.2_x86_64_20231116.deb
fi

# Create necessary directories
echo "Creating directories"
mkdir -p /opt/MVS/bin/fonts

# Source the bashrc file
echo "Sourcing .bashrc"
echo "source ~/.bashrc" >> ~/.bashrc
source ~/.bashrc

# Set environment variable for MVCAM_COMMON_RUNENV
echo "Setting environment variables"
export MVCAM_COMMON_RUNENV=/opt/MVS/lib
export LD_LIBRARY_PATH=/opt/MVS/lib/64:/opt/MVS/lib/32:$LD_LIBRARY_PATH

# Install Miniforge
echo "Installing Miniforge"
if [ "$ARCH" = "aarch64" ]; then
    wget --quiet https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-aarch64.sh -O /tmp/miniforge.sh
elif [ "$ARCH" = "x86_64" ]; then
    wget --quiet https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh -O /tmp/miniforge.sh
fi
bash /tmp/miniforge.sh -b -p /opt/conda
rm /tmp/miniforge.sh

# Update PATH environment variable
echo "Updating PATH"
export PATH=/opt/conda/bin:$PATH

# Create conda environment and install packages
echo "Creating conda environment and installing packages"
conda create -y --name imswitch python=3.10
conda install -n imswitch -y -c conda-forge h5py numcodecs
conda clean --all -f -y

# Clone the config folder
echo "Cloning ImSwitchConfig"
git clone https://github.com/openUC2/ImSwitchConfig /root/ImSwitchConfig

# Clone the repository and install dependencies
echo "Cloning and installing imSwitch"
git clone https://github.com/openUC2/imSwitch /tmp/ImSwitch
cd /tmp/ImSwitch
git checkout NOQT
source /opt/conda/bin/activate imswitch && pip install -e /tmp/ImSwitch

# Install UC2-REST
echo "Installing UC2-REST"
git clone https://github.com/openUC2/UC2-REST /tmp/UC2-REST
cd /tmp/UC2-REST
source /opt/conda/bin/activate imswitch && pip install -e /tmp/UC2-REST

# Expose SSH port and HTTP port
echo "Exposing ports 22 and 8001"
sudo ufw allow 22
sudo ufw allow 8001

echo "Installation complete. To run the application, use the following command:"
echo "source /opt/conda/bin/activate imswitch && python3 /tmp/ImSwitch/main.py --headless 1 --config-file /root/ImSwitchConfig/imcontrol_setup/example_virtual_microscope.json --http-port 8001"
