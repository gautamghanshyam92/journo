#!/bin/bash

# checking if vsftpd already installed
if [ "$(command -v vsftpd)" ]; then
    echo "Vsftpd already installed. Hence skipping installation."
    exit 0
fi

sudo apt update

echo "Installing vsftpd server..."
sudo apt install vsftpd
if [ $? -ne 0 ]; then
    echo "Failed to install vsftp server."
    exit 1
fi

echo "Configuring vsftpd server..."
sudo mv /etc/vsftpd.conf /etc/vsftpd.conf.backup
if [ $? -ne 0 ]; then
    echo "Failed to backup default '/etc/vsftpd.conf' to '/etc/vsftpd.conf.backup'."
    exit 1
fi

sudo cp vsftpd_config/vsftpd.conf /etc/vsftpd.conf
if [ $? -ne 0 ]; then
    echo "Failed to copy application configured 'vsftpd.conf' to '/etc/vsftpd.conf'."
    exit 1
fi

echo $USER > vsftpd_config/vsftpd.userlist
sudo cp vsftpd_config/vsftpd.userlist /etc/vsftpd.userlist
if [ $? -ne 0 ]; then
    echo "Failed to copy 'vsftpd.userlist' to '/etc/vsftpd.userlist'."
    exit 1
fi

sudo systemctl stop vsftpd.service
sudo systemctl start vsftpd.service
if [ $? -ne 0 ]; then
    echo "Failed to restart vsftpd service."
    exit 1
fi

# checking if ftp port is added to firewall
echo "Configuring firewall..."
sudo ufw status | grep ftp &>/dev/null
if [ $? -ne 0 ]; then
    sudo ufw allow ftp
    if [ $? -ne 0 ]; then
        echo "Failed to allow ftp port through firewall."
        exit 1
    fi
fi

sudo ufw status | grep "40000:50000/tcp" &>/dev/null
if [ $? -ne 0 ]; then
    sudo ufw allow 40000:50000/tcp
    if [ $? -ne 0 ]; then
        echo "Failed to configure vsftpd data ports."
        exit 1
    fi
fi

echo "Vsftpd Server installed successfully."
exit 0
