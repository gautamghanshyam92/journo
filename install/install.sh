#!/bin/bash

BASE_SCRIPT_DIR=$(pwd)
OS_VERSION=$(lsb_release -rs)

if [[ "$OS_VERSION" < "18.04" ]]; then
    echo "Journo is supported only for Ubuntu Version 18.04 and above."
    exit 1
fi

echo "Installing Python 3.6.8 and Python3 modules..."
cd ./python_packages
./install.sh
if [ $? -ne 0 ]; then
    exit 1
fi
cd $BASE_SCRIPT_DIR

echo "Installing MongoDB 4.0..."
cd ./mongodb_server
./install.sh
if [ $? -ne 0 ]; then
    exit 1
fi
cd $BASE_SCRIPT_DIR

echo "Installing Vsftpd Server..."
cd ./vsftpd_server
./install.sh
if [ $? -ne 0 ]; then
    exit 1
fi
cd $BASE_SCRIPT_DIR

echo "Installing Tusd Server..."
cd ./tusd_server
./install.sh
if [ $? -ne 0 ]; then
    exit 1
fi
cd $BASE_SCRIPT_DIR

echo "Installing Nginx for streaming..."
cd ./nginx_server
./install.sh
if [ $? -ne 0 ]; then
    exit 1
fi
cd $BASE_SCRIPT_DIR

if [ ! -d /mnt/proxy ]; then
    sudo mkdir /mnt/proxy
    sudo chown $USER:$USER /mnt/proxy
fi

echo "Done installing Journo."
exit 0
