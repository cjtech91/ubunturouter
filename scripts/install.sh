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
# Added hostapd for WiFi Hotspot support
sudo apt-get install -y python3-full python3-dev build-essential netplan.io isc-dhcp-server pppoe iproute2 hostapd wireless-tools iw

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

# Make scripts executable
chmod +x scripts/*.sh

echo "=========================================="
echo "  Initial Network Configuration"
echo "=========================================="
echo "Initializing configuration..."
# Run the interactive configuration script
./venv/bin/python3 scripts/set_default_ip.py

# Get IP address (try to get the first non-loopback IP)
CURRENT_IP=$(hostname -I | awk '{print $1}')

echo ""
echo "WARNING: Applying this configuration will update your network settings."
echo "If you configured the interface you are currently using as WAN (DHCP), access should be preserved."
echo "If you configured it as LAN (Static 192.168.172.1), you may be DISCONNECTED."
read -p "Do you want to apply this configuration now? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Applying network configuration..."
    sudo ./scripts/apply_configs.sh
    echo "Configuration applied."
    echo "Dashboard available at configured IP addresses."
    echo "Try: http://$CURRENT_IP or http://192.168.172.1"
else
    echo "Configuration generated but NOT applied."
    echo "You can apply it later by running: sudo ./scripts/apply_configs.sh"
    echo "Dashboard currently available at: http://$CURRENT_IP"
fi

echo "=========================================="

echo "=========================================="
echo "  Installation Complete!"
echo "=========================================="
echo "Note: If you cannot access the dashboard, check firewall settings:"
echo "      sudo ufw allow 80/tcp"
echo ""
