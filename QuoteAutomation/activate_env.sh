#!/bin/bash

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    python3.11 -m venv .venv
    source .venv/bin/activate
    pip install -e .
else
    source .venv/bin/activate
fi

# Print status
echo "Virtual environment activated!"
echo "Python version: $(python --version)"
echo "Installed packages:"
pip list | grep -E 'crewai|langchain|pinecone|composio' 