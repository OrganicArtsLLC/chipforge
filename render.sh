#!/usr/bin/env bash
# render.sh — Background render with automatic polling
# Usage: ./render.sh <script>.py
#
# Runs the song script in background, polls every 5 seconds,
# reports the WAV file when complete. Safe for agent mode —
# will not time out the terminal.

set -euo pipefail

SCRIPT="${1:?Usage: ./render.sh <script>.py}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON="$SCRIPT_DIR/.venv/bin/python3"

if [[ ! -f "$SCRIPT_DIR/$SCRIPT" ]]; then
    echo "ERROR: $SCRIPT not found in $SCRIPT_DIR"
    exit 1
fi

if [[ ! -x "$PYTHON" ]]; then
    echo "ERROR: Python not found at $PYTHON"
    echo "Run: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"
    exit 1
fi

cd "$SCRIPT_DIR"

echo "╔══════════════════════════════════════════════╗"
echo "║  ChipForge Render: $SCRIPT"
echo "╚══════════════════════════════════════════════╝"
echo ""
echo "Starting background render..."

# Run in background, capture PID
"$PYTHON" "$SCRIPT" &
PID=$!
echo "PID: $PID"
echo ""

# Poll every 5 seconds
ELAPSED=0
while ps -p "$PID" > /dev/null 2>&1; do
    sleep 5
    ELAPSED=$((ELAPSED + 5))
    echo "  Rendering... ${ELAPSED}s elapsed"
done

# Check exit status
wait "$PID" 2>/dev/null
EXIT_CODE=$?

echo ""
if [[ $EXIT_CODE -eq 0 ]]; then
    echo "✓ Render complete (${ELAPSED}s)"
    echo ""
    # Show any new WAV files modified in the last 3 minutes
    echo "Output files:"
    find output/ -name "*.wav" -mmin -3 -exec ls -lh {} \;
else
    echo "✗ Render FAILED (exit code: $EXIT_CODE)"
    exit $EXIT_CODE
fi
