#!/bin/bash

REQUIRED_MAJOR_VERSION="v4"
REQUIRED_MINOR_VERSION="0"
MONGODB_SERVER_EXECUTABLE="mongod"

required_db_version="$REQUIRED_MAJOR_VERSION.$REQUIRED_MINOR_VERSION"
# checking if mongod server is already installed
if [ "$(command -v $MONGODB_SERVER_EXECUTABLE)" ]; then
    # extracting mongodb version
    db_version=$(mongod --version | grep "db version" | cut -d' ' -f3)
    major_version=$(echo "$db_version" | cut -d'.' -f1)
    minor_version=$(echo "$db_version" | cut -d'.' -f2)

    if [[ "$major_version" == "$REQUIRED_MAJOR_VERSION" ]]
    then
        if [[ "$minor_version" == "$REQUIRED_MINOR_VERSION" ]]
        then
            echo "MongoDB with required version is already installed. Hence skipping installation."
            exit 0
        else
            if [[ "$minor_version" < "$REQUIRED_MINOR_VERSION" ]]
            then
                echo "WARNING: MongoDB with older minor version '$db_version' already installed. Please upgrade to '$required_db_version'."
            else
                echo "WARNING: MongoDB with newer minor version '$db_version' already installed. Please use older version '$required_db_version'"
            fi
            exit 0
        fi
    else
        echo "ERROR: MongoDB version '$db_version' is already installed which is not compatible with MAM3. Hence quitting installation."
        exit 1
    fi
fi

# configuring mongodb repository
echo "Configuring MongoDB repository..."
wget -qO - https://www.mongodb.org/static/pgp/server-4.0.asc | sudo apt-key add -
echo "deb [ arch=amd64 ] https://repo.mongodb.org/apt/ubuntu bionic/mongodb-org/4.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-4.0.list
sudo apt update

echo "Installing MongoDB..."
sudo apt-get install -y mongodb-org
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install MongoDB."
    exit 1
fi

sudo service mongod start

echo "MongoDB installed successfully."
exit 0
