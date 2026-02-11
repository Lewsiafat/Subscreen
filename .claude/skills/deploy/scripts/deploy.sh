#!/bin/bash
# Deploy src/ to Pico device via mpremote, excluding __pycache__
set -e

SRC_DIR="src"

if ! command -v mpremote &> /dev/null; then
    echo "Error: mpremote not found. Install with: pip install mpremote"
    exit 1
fi

echo "Deploying $SRC_DIR/ to Pico..."

# Upload files, skipping __pycache__ directories
cd "$SRC_DIR"
find . -type f ! -path '*/__pycache__/*' ! -path '*/.DS_Store' | while read -r file; do
    dir=$(dirname "$file")
    if [ "$dir" != "." ]; then
        mpremote mkdir ":$dir" 2>/dev/null || true
    fi
    echo "  $file"
    mpremote cp "$file" ":$file"
done

echo "Deploy complete."
