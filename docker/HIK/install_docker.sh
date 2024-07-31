#!/bin/bash
# chmod +x install_docker.sh
# ./install_docker.sh

# Update package lists
sudo apt update -y

# Upgrade installed packages
sudo apt upgrade -y

# Install Docker
curl -sSL https://get.docker.com | sh

# Add current user to the Docker group
sudo usermod -aG docker $USER

# Print message to logout and login again
echo "Please log out and log back in to apply the Docker group changes."

# Verify group membership (this will not reflect the changes until you log out and log back in)
groups
