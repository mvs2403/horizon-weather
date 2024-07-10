#!/bin/bash
# This script installs Docker and Docker Compose:
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt-get install -y libffi-dev libssl-dev
sudo apt-get install -y python3 python3-pip
sudo pip3 install docker-compose

# Reboot to apply Docker group changes
echo "Rebooting to apply Docker group changes. Please run ./deploy_pi.sh after reboot."
sudo reboot