#!/bin/bash
set -e  # Exit immediately if a command exits with a non-zero status

echo "=========================================="
echo "  Ubuntu Router Installer"
echo "=========================================="

# Update and install system dependencies
echo "[1/5] Installing system dependencies..."
sudo apt-get update
# Note: 'pppoe' package usually contains pppoe-server command. 
# Added build-essential and python3-dev for compiling python extensions (psutil)
# Added python3-full for venv support
sudo apt-get install -y python3-full python3-dev build-essential netplan.io isc-dhcp-server pppoe iproute2

# Create application directory structure if not exists (assuming running from repo root)
echo "[2/5] Setting up application environment..."

# Create Virtual Environment
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Install Python dependencies into venv
echo "[3/5] Installing Python dependencies..."
if [ -f requirements.txt ]; then
    ./venv/bin/pip install --upgrade pip
    ./venv/bin/pip install -r requirements.txt
else
    echo "Error: requirements.txt not found!"
    exit 1
fi

# Set up systemd service
echo "[4/5] Creating systemd service..."
CURRENT_DIR=$(pwd)
USER_NAME=$(whoami)

cat <<EOF | sudo tee /etc/systemd/system/ubuntu-router.service
[Unit]
Description=Ubuntu Router Web UI
After=network.target

[Service]
User=root
WorkingDirectory=$CURRENT_DIR
# Use the gunicorn from the virtual environment
ExecStart=$CURRENT_DIR/venv/bin/gunicorn --workers 3 --bind 0.0.0.0:80 run:app
Restart=always
Environment="PATH=$CURRENT_DIR/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and start service
echo "[5/5] Starting service..."
sudo systemctl daemon-reload
sudo systemctl enable ubuntu-router
sudo systemctl restart ubuntu-router

# Get IP address (try to get the first non-loopback IP)
IP_ADDR=$(hostname -I | awk '{print $1}')

echo "=========================================="
echo "  Installation Complete!"
echo "=========================================="
echo "Dashboard available at: http://$IP_ADDR"
echo ""
echo "Note: If you cannot access the dashboard, check firewall settings:"
echo "      sudo ufw allow 80/tcp"
echo ""
