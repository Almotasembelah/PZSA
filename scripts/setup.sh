#!/bin/bash

echo 'Creating venv .....'

python -m venv .venv

VENV_PATH="./.venv"

if [ ! -d "$VENV_PATH" ]; then
echo "Error: Virtual environment not found at $VENV_PATH"
exit 1
fi

# Activate venv in this subshell
source "$VENV_PATH/Scripts/activate"

echo "Active venv: $VIRTUAL_ENV"

echo "Copy .env.example into .env .............."
cp .env.example .env

echo "Installing uv .........."
pip install uv

echo "Installing dependencies .........."
uv init
uv sync