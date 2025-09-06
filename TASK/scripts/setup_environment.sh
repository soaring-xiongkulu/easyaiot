#!/bin/bash

echo "Setting up Smart Surveillance System environment..."

# Install system dependencies
sudo apt-get update
sudo apt-get install -y \
    build-essential \
    cmake \
    libopencv-dev \
    libpaho-mqtt-cpp-dev \
    libssl-dev \
    libcurl4-openssl-dev \
    libjsoncpp-dev \
    pkg-config

# Create directory structure
mkdir -p {config/cameras,config/ai_models,config/zones,config/mqtt}
mkdir -p {models,resources,logs,scripts,tests}

# Setup data directory
sudo mkdir -p /var/lib/smart_surveillance
sudo chown -R $USER:$USER /var/lib/smart_surveillance

echo "Environment setup completed!"