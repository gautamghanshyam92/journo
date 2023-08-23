#!/bin/bash

TUSD_SERVER_INSTALLATION_PATH=/opt/tusd_server
TUSD_SERVER_DATA_PATH=/mnt/uploads/tusstore

if [ -d "$TUSD_SERVER_INSTALLATION_PATH" ] && [ -f "$TUSD_SERVER_INSTALLATION_PATH/tusd" ]; then
    echo "Tusd Server already installed."
    exit 0
fi

echo "Preparing environment..."
# creating setup directory
if [ -d ~/tusd_setup ]; then
    rm -r ~/tusd_setup
fi
mkdir ~/tusd_setup
cd ~/tusd_setup

# creating tusd server installation directory
if [ ! -d $TUSD_SERVER_INSTALLATION_PATH ]; then
    sudo mkdir -p $TUSD_SERVER_INSTALLATION_PATH
    if [ $? -ne 0 ]; then
        echo "Failed to prepare Environment."
        exit 1
    fi
    sudo chown -R $USER:$USER $TUSD_SERVER_INSTALLATION_PATH
fi

# downloading tusd server code
if [ -f tusd_linux_amd64.tar.gz ]; then
    rm tusd_linux_amd64.tar.gz
fi

echo "Downloading tusd server binary..."
wget https://github.com/tus/tusd/releases/download/v1.0.1/tusd_linux_amd64.tar.gz
if [ $? -ne 0 ]; then
    echo "Failed to download tusd server binary."
    exit 1
fi

# extracting tusd server code
if [ -d ./tusd_linux_amd64 ]; then
    rm -r ./tusd_linux_amd64
fi

tar -xvzf tusd_linux_amd64.tar.gz
if [ $? -ne 0 ]; then
    echo "Failed to extract tusd server binary."
    exit 1
fi

# installing tusd server
echo "Installing tusd server..."
mv ./tusd_linux_amd64/tusd $TUSD_SERVER_INSTALLATION_PATH
if [ $? -ne 0 ]; then
    echo "Failed to install tusd server."
    exit 1
fi
chmod +x $TUSD_SERVER_INSTALLATION_PATH/tusd

# checking if tusd port is already added to firewall
sudo ufw status | grep "1080/tcp" &>/dev/null
if [ $? -ne 0 ]; then
    # adding tusd port to firewall
    echo "Allowing tusd server through firewall..."
    sudo ufw allow 1080/tcp
    if [ $? -ne 0 ]; then
        echo "Failed to add 1080/tcp port to tusd server."
        exit 1
    fi
else
    echo "Tusd server port already added to firewall."
fi

# creating tusd upload data directory
if [ ! -d $TUSD_SERVER_DATA_PATH ]; then
    echo "Creating required directories..."
    sudo mkdir -p $TUSD_SERVER_DATA_PATH
    if [ $? -ne 0 ]; then
        echo "Failed to create required directories. Please create $TUSD_SERVER_DATA_PATH directory with $USER ownership manually."
    else
        sudo chown -R $USER:$USER $TUSD_SERVER_DATA_PATH
    fi
fi

echo "Cleaning setup..."
cd ~
rm -r ~/tusd_setup

echo "Tusd Server installed successfully at $TUSD_SERVER_INSTALLATION_PATH"
exit 0
