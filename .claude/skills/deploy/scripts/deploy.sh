#!/bin/bash
# Deploy src/ to Pico device via mpremote, excluding __pycache__
set -e

SRC_DIR="src"

# Resolve an mpremote invocation: prefer the bare command, else `python -m mpremote`.
if command -v mpremote &> /dev/null; then
    MPREMOTE="mpremote"
elif python -m mpremote --version &> /dev/null; then
    MPREMOTE="python -m mpremote"
else
    echo "Error: mpremote not found. Install with: pip install mpremote"
    exit 1
fi

# Auto-detect the Pico (RP2 USB vid 2e8a). If found, pin to that port so we don't
# grab the wrong device when several COM/tty ports are present.
PORT=$($MPREMOTE connect list 2>/dev/null | grep -i '2e8a:' | head -1 | awk '{print $1}')
if [ -n "$PORT" ]; then
    CONNECT="connect $PORT"
    echo "Deploying $SRC_DIR/ to Pico ($PORT)..."
else
    CONNECT=""
    echo "Deploying $SRC_DIR/ to Pico (auto)..."
fi

# Upload files, skipping __pycache__ directories
cd "$SRC_DIR"
find . -type f ! -path '*/__pycache__/*' ! -name '.DS_Store' | while read -r file; do
    dir=$(dirname "$file")
    if [ "$dir" != "." ]; then
        $MPREMOTE $CONNECT mkdir ":$dir" 2>/dev/null || true
    fi
    echo "  $file"
    $MPREMOTE $CONNECT cp "$file" ":$file" >/dev/null
done

echo "Deploy complete."
