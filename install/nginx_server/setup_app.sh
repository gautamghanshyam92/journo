#!/bin/bash

echo "Creating required directories..."
if [ ! -d /mnt/hls ]; then
    sudo mkdir /mnt/hls
    sudo chown $USER:$USER /mnt/hls
fi

if [ ! -d /mnt/recordings ]; then
    sudo mkdir /mnt/recordings
    sudo chown $USER:$USER /mnt/recordings
fi

if [ ! -d /mnt/uploads ]; then
    sudo mkdir /mnt/uploads
    sudo chown $USER:$USER /mnt/uploads
fi
echo "Done setting up."
