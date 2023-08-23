#!/bin/bash

echo "Starting Feed Server..."
cd ..
PYTHONPATH="$PYTHONPATH:$(pwd)"
export PYTHONPATH
/usr/bin/python3 ./server/rssfeed/feedserver.py
