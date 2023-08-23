#!/bin/bash

echo "Starting Task Engine..."
cd ..
PYTHONPATH="$PYTHONPATH:$(pwd)"
export PYTHONPATH
/usr/bin/python3 ./server/task/app.py
