#!/bin/bash

# Update and install system dependencies
echo "Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv netplan.io isc-dhcp-server pppoe pppoe-server iproute2

# Create application directory structure if not exists (assuming running from repo root)
echo "Setting up application..."

# Install Python dependencies
if [ -f requirements.txt ]; then
    echo "Installing Python dependencies..."
    pip3 install -r requirements.txt
fi

# Set up systemd service
echo "Creating systemd service..."
cat <<EOF | sudo tee /etc/systemd/system/ubuntu-router.service
[Unit]
Description=Ubuntu Router Web UI
After=network.target

[Service]
User=root
WorkingDirectory=$(pwd)
ExecStart=$(which gunicorn) --workers 3 --bind 0.0.0.0:80 run:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and start service
echo "Starting service..."
sudo systemctl daemon-reload
sudo systemctl enable ubuntu-router
sudo systemctl start ubuntu-router

echo "Installation complete! Dashboard available at http://$(hostname -I | awk '{print $1}'):80"
