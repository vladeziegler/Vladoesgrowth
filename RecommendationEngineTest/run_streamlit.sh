#!/bin/bash

# Run setup and activate environment
source ./setup_env.sh

# Set PYTHONPATH to include the src directory
export PYTHONPATH=$PYTHONPATH:$(pwd)/src

# Run streamlit
echo "Starting Streamlit app..."
streamlit run src/recommendationenginetest/streamlit.py 