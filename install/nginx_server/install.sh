#!/bin/bash

if [ "$(command -v nginx)" ]; then
    echo "Nginx already installed. Hence skipping setup."
    exit 1
fi

SCRIPT_BASE_DIR=$(pwd)

if [ -d ~/nginx_setup ]; then
    rm -r ~/nginx_setup
fi

mkdir ~/nginx_setup
cd ~/nginx_setup

echo "Installig Prerequiste Packages..."
sudo apt install git gcc make libaio1 libpcre3-dev openssl libssl-dev ffmpeg -y
if [ $? -ne 0 ]; then
    echo "Failed to install prequisite packages."
    exit 1
fi
sudo apt install build-essential autoconf automake build-essential libpcre3  zlib1g zlib1g-dev
if [ $? -ne 0 ]; then
    echo "Failed to install prequisite packages."
    exit 1
fi

echo "Cloning Nginx Hls module..."
git clone https://github.com/arut/nginx-ts-module.git
if [ $? -ne 0 ]; then
    echo "Failed to clone Nginx Hls module."
    exit 1
fi

echo "Cloning Nginx Rtmp module...."
git clone https://github.com/arut/nginx-rtmp-module.git
if [ $? -ne 0 ]; then
    echo "Failed to clone Nginx Rtmp module."
    exit 1
fi

echo "Cloning Nginx Vod module..."
git clone https://github.com/kaltura/nginx-vod-module.git
if [ $? -ne 0 ]; then
    echo "Failed to clone Nginx Vod module."
    exit 1
fi

echo "Downloading Nginx source ....."
wget http://nginx.org/download/nginx-1.17.3.tar.gz
if [ $? -ne 0 ]; then
    echo "Failed to download Nginx source."
    exit 1
fi

tar -xf nginx-1.17.3.tar.gz
if [ $? -ne 0 ]; then
    echo "Failed to Extract Nginx source."
    exit 1
fi

echo "Compiling Nginx with downloaded modules..."
cd nginx-1.17.3/
./configure --prefix=/usr/local/nginx --with-http_ssl_module --with-http_stub_status_module --with-threads --with-file-aio --add-module=../nginx-rtmp-module --add-module=../nginx-ts-module --add-module=../nginx-vod-module
if [ $? -ne 0 ]; then
    echo "Failed to configure Nginx source with downloaded modules."
    exit 1
fi

make
if [ $? -ne 0 ]; then
    echo "Failed to complie Nginx source with downloaded modules."
    exit 1
fi

echo "Installing Nginx..."
sudo make install
if [ $? -ne 0 ]; then
    echo "Failed to install Nginx."
    exit 1
fi

echo "Configuring Nginx..."
if [ -L /usr/sbin/nginx ]; then
    sudo unlink /usr/sbin/nginx
fi
sudo ln -s /usr/local/nginx/sbin/nginx /usr/sbin/nginx
if [ $? -ne 0 ]; then
    echo "Failed to create symbolic link for '/usr/local/nginx/sbin/nginx' server binary."
    exit 1
fi

sudo cp /usr/local/nginx/conf/nginx.conf  /usr/local/nginx/conf/nginx.conf.backup

cd $SCRIPT_BASE_DIR

cp ./nginx_config/default_nginx.conf ./nginx_config/temporary_nginx.conf
sed -i "s/user  journo_process_username/user  $USER/g" ./nginx_config/temporary_nginx.conf
if [ $? -ne 0 ]; then
    echo "Failed to configure nginx config file."
    exit 1
fi

sudo cp ./nginx_config/temporary_nginx.conf /usr/local/nginx/conf/nginx.conf
if [ $? -ne 0 ]; then
    echo "Failed to install Nginx configuration file required for Journo streaming."
    exit 1
fi

echo "Cleaning setup..."
cd ~
sudo rm -r ~/nginx_setup

cd $SCRIPT_BASE_DIR

echo "Setting up app..."
./setup_app.sh
echo "Nginx installed successfully."

echo "Configuring Nginx as Service..."
./configure_as_18.04_service.sh
if [ $? -ne 0 ]; then
    exit 1
fi
exit 0
