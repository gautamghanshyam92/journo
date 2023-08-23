#!/bin/bash

echo "Starting Editor App Server..."
cd ..
PYTHONPATH="$PYTHONPATH:$(pwd)"
export PYTHONPATH
/usr/bin/python3 ./simulator/editorapp/third_party_nrcs.py
