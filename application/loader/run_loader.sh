#!/bin/bash

# Script to manually run the PDF loader service
# This can be used for testing or one-off loading operations

echo "Running PDF loader service manually..."

# Set default PDF path if not provided
export PDF_PATH=${PDF_PATH:-/data/book}

echo "PDF Path: $PDF_PATH"

# Run the loader
python main.py
