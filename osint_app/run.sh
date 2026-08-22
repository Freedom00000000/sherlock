#!/bin/bash
echo "Installing dependencies..."
pip install flask sherlock-project 2>/dev/null
echo "Starting Sherlock OSINT Dashboard..."
python3 app.py
