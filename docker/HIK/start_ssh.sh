#!/bin/bash
ECHO "LSUSB"
lsusb

# Start SSH server
/usr/sbin/sshd -D &

# List imSwitchConfig
ls /root/ImSwitchConfig

# Update the repository if needed
if [ "$UPDATE_GIT" = "true" ]; then
    cd /tmp/ImSwitch
    git pull 
    /bin/bash -c "source /opt/conda/bin/activate imswitch && pip install -e /tmp/ImSwitch"
fi

if [ "$UPDATE_CONFIG" = "true" ]; then
    cd /root/ImSwitchConfig
    git pull origin main
fi

# Activate conda environment
source /opt/conda/bin/activate imswitch

# Set default values if not provided
HEADLESS=${HEADLESS:-1}
HTTP_PORT=${HTTP_PORT:-8001}
CONFIG_FILE=${CONFIG_FILE:-/root/ImSwitchConfig/imcontrol_setup/example_virtual_microscope.json}
USB_DEVICE_PATH=${USB_DEVICE_PATH:-/dev/bus/usb}



# Start the ImSwitch application with provided or default parameters
python3 -m imswitch --headless $HEADLESS --config-file $CONFIG_FILE --http-port $HTTP_PORT --ssl 1
