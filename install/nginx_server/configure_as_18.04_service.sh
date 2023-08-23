#!/bin/bash

if [ -e /lib/systemd/system/nginx.service ]; then
    echo "Service configuration file /lib/systemd/system/nginx.service already exists."
    exit 0
else
    sudo cp ./nginx.service /lib/systemd/system/nginx.service
    echo "/lib/systemd/system/nginx.service configuration file copied."
fi

echo "Starting Nginx Service..."
sudo systemctl enable nginx.service
sudo systemctl restart nginx.service
if [ $? -ne 0 ]; then
    echo "Failed to restart nginx service."
    exit 1
fi
exit 0
