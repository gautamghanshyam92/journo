#!/bin/bash

sudo apt update

echo "Checking python version..."
PYTHON3_VERSION=$(python3 --version | cut -d' ' -f2)
if [[ "$PYTHON3_VERSION" < "3.6.8" ]]; then

    echo "Installing and upgrading python3"
    sudo apt install python3 --upgrade

    PYTHON3_VERSION=$(python3 --version | cut -d' ' -f2)
    if [[ "$PYTHON3_VERSION" < "3.6.8" ]]; then
        echo "Installation Failed: Minimum 'python3' Version 3.6.8 is required."
        exit 1
    fi

    echo "Installing pip3..."
    sudo apt install python3-pip
fi

sudo pip3 install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Failed to install python3 pacakages."
    exit 1
fi

exit 0
