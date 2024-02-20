#!/bin/bash
sudo rm /usr/lib/python3.11/EXTERNALLY-MANAGED
sudo date --set="20 FEB 2024"

# Navigate to Downloads directory
cd ~/Downloads

# Download Mambaforge installer
wget https://github.com/conda-forge/miniforge/releases/latest/download/Mambaforge-pypy3-Linux-aarch64.sh

# Install Mambaforge
# This step normally requires interaction. To automate, you might try echoing 'yes' to the prompt or using an expect script
bash Mambaforge-pypy3-Linux-aarch64.sh -b

# Initialize Mambaforge immediately without needing to log off/in
source ~/mambaforge/bin/activate

# Create a new environment with Python 3.9
mamba create -n imswitch python=3.9 -y

# Activate the new environment
conda activate imswitch

# Clone necessary repositories
git clone https://github.com/openUC2/ImSwitch/
git clone https://github.com/openUC2/UC2-REST

# Install UC2-REST
cd ~/Downloads/UC2-REST
pip install -e .

# Install dependencies for ImSwitch
cd ~/Downloads/ImSwitch
sudo apt-get install python3-pyqt5 -y
pip install -r requirements-jetsonorin.txt
pip install -e . --no-deps

# Install PyQt via mamba
mamba install pyqt -y

# Clone additional repository
cd ~/Downloads
git clone https://github.com/hongquanli/octopi-research

# Install Daheng camera drivers
cd octopi-research/software/drivers\ and\ libraries/daheng\ camera/Galaxy_Linux-armhf_Gige-U3_32bits-64bits_1.3.1911.9271/
chmod +x Galaxy_camera.run
sudo ./Galaxy_camera.run # This command might require user interaction

# Reboot system
# Automatically rebooting can be disruptive. Uncomment the following line if you understand the implications.
# sudo reboot
