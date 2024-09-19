#!/bin/bash

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# Update the package index
sudo apt-get -y update

# Install prerequisites
sudo apt-get -y install ca-certificates curl

# Create the directory for the Docker GPG key
sudo install -m 0755 -d /etc/apt/keyrings

# Add Docker's official GPG key
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc

# Set permissions for the GPG key
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add Docker repository to the sources list
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Update the package index with Docker packages
sudo apt-get -y update

# Install Docker packages
sudo apt-get -y install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# add existing user
sudo usermod -aG docker $USER

# Optional: Verify that Docker is installed correctly
sudo docker --version
