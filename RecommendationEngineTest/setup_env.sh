#!/bin/bash

# Create and activate virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating new virtual environment..."
    python3 -m venv .venv
fi

source .venv/bin/activate

# Upgrade pip and setuptools
pip install --upgrade pip setuptools wheel

# Install dependencies in the correct order
echo "Installing dependencies..."
pip install numpy==1.24.3
pip install pandas==2.0.3
pip install streamlit==1.32.0
pip install -e .

# Print status
echo "Virtual environment activated and dependencies installed!"
echo "Python version: $(python --version)"
echo "NumPy version: $(python -c 'import numpy; print(numpy.__version__)')"
echo "Pandas version: $(python -c 'import pandas; print(pandas.__version__)')"
echo "Streamlit version: $(python -c 'import streamlit; print(streamlit.__version__)')" 