#!/bin/bash

echo "Starting Chat Server..."
cd ..
PYTHONPATH="$PYTHONPATH:$(pwd)"
export PYTHONPATH
/usr/bin/python3 ./server/chat/app.py
