#!/bin/bash

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install production dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt

# Create a test configuration file if it doesn't exist
if [ ! -f "vcf-monitoring-loginData.json" ]; then
    cp vcf-monitoring-loginData.json.template vcf-monitoring-loginData.json
    echo "Created configuration file from template."
    echo "Please update vcf-monitoring-loginData.json with your credentials."
fi

echo "Development environment set up successfully."
echo "To activate the environment, run:"
echo "source venv/bin/activate"
