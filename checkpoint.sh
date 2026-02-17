#!/bin/bash
# Wrapper script to run checkpoint from any directory

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Add the Checkpoint directory to PYTHONPATH so main.py can be found
export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"

# Activate the virtual environment and run main.py
exec "$SCRIPT_DIR/.venv/bin/python" "$SCRIPT_DIR/main.py" "$@"
