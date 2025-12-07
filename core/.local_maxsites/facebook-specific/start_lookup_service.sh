#!/bin/bash
# Facebook Lookup Service Launcher
# Starts the Python microservice for real-time Facebook profile lookups

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_FILE="$SCRIPT_DIR/fb_lookup_service.py"
PID_FILE="$SCRIPT_DIR/.lookup_service.pid"
LOG_FILE="$SCRIPT_DIR/lookup_service.log"

# Check if service file exists
if [ ! -f "$SERVICE_FILE" ]; then
    echo "[ERROR] Service file not found: $SERVICE_FILE"
    exit 1
fi

# Check if service is already running
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
        echo "[INFO] Service already running (PID: $OLD_PID)"
        echo "[INFO] To restart, run: pkill -f fb_lookup_service.py"
        exit 0
    else
        # Remove stale PID file
        rm -f "$PID_FILE"
    fi
fi

# Change to script directory
cd "$SCRIPT_DIR"

# Check if Flask is installed
if ! python3 -c "import flask" 2>/dev/null; then
    echo "[WARN] Flask not found. Installing Flask..."
    pip3 install flask flask-cors --quiet
fi

# Start the service
echo "[INFO] Starting Facebook Lookup Service..."
echo "[INFO] Service file: $SERVICE_FILE"
echo "[INFO] Log file: $LOG_FILE"
echo "[INFO] Endpoint: http://localhost:5000/lookup?email=<email_or_phone>"

# Start service in background
nohup python3 "$SERVICE_FILE" >> "$LOG_FILE" 2>&1 &
SERVICE_PID=$!

# Save PID
echo $SERVICE_PID > "$PID_FILE"

# Wait a moment to check if service started successfully
sleep 2

if ps -p "$SERVICE_PID" > /dev/null 2>&1; then
    echo "[SUCCESS] Service started successfully (PID: $SERVICE_PID)"
    echo "[INFO] To stop: kill $SERVICE_PID"
    echo "[INFO] To view logs: tail -f $LOG_FILE"
else
    echo "[ERROR] Service failed to start. Check logs: $LOG_FILE"
    rm -f "$PID_FILE"
    exit 1
fi

