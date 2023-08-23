#!/bin/bash

echo "Starting Request Server..."
cd ..
PYTHONPATH="$PYTHONPATH:$(pwd)"
export PYTHONPATH
/usr/bin/python3 ./server/request/app.py
