#!/bin/bash

# Script to help set up Poetry virtual environments for VS Code

echo "Setting up Poetry virtual environments for BiblioQuiz..."

export PATH="/home/vscode/.local/bin:$PATH"

# Services with dependencies
services=("loader" "orchestrator" "historian" "librarian")

for service in "${services[@]}"; do
    echo "Setting up $service..."
    cd "/workspaces/BiblioQuiz/application/$service"
    poetry install
    
    # Get the virtual environment path for VS Code
    venv_path=$(poetry env info --path)
    echo "Virtual environment for $service: $venv_path"
done

# Set up shared library
echo "Setting up shared library..."
cd "/workspaces/BiblioQuiz/share"
poetry install

# Get the shared library venv path
venv_path=$(poetry env info --path)
echo "Virtual environment for shared: $venv_path"

echo ""
echo "=== VS Code Setup Instructions ==="
echo "1. Open VS Code in your workspace"
echo "2. Open Command Palette (Ctrl+Shift+P)"
echo "3. Select 'Python: Select Interpreter'"
echo "4. Choose the Python interpreter from the virtual environment you want to work on"
echo "5. For the loader service, use: $venv_path/bin/python"
echo ""
echo "You can also set up VS Code workspace settings by creating .vscode/settings.json"
echo "Poetry virtual environments are located in: $(poetry config virtualenvs.path)"
