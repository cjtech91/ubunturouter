#!/bin/bash

# Define paths
GENERATED_DIR="generated"
NETPLAN_DIR="/etc/netplan"
DHCP_DIR="/etc/dhcp"
PPPOE_DIR="/etc/ppp"

echo "Applying network configurations..."

# Apply Netplan
if [ -f "$GENERATED_DIR/01-netcfg.yaml" ]; then
    echo "Updating Netplan config..."
    sudo cp "$GENERATED_DIR/01-netcfg.yaml" "$NETPLAN_DIR/01-netcfg.yaml"
    sudo netplan apply
fi

# Apply DHCP
if [ -f "$GENERATED_DIR/dhcpd.conf" ]; then
    echo "Updating DHCP config..."
    sudo cp "$GENERATED_DIR/dhcpd.conf" "$DHCP_DIR/dhcpd.conf"
    
    if [ -f "$GENERATED_DIR/isc-dhcp-server" ]; then
        sudo cp "$GENERATED_DIR/isc-dhcp-server" "/etc/default/isc-dhcp-server"
    fi
    
    # Restart DHCP server
    sudo systemctl restart isc-dhcp-server
fi

# Apply PPPoE
if [ -f "$GENERATED_DIR/pppoe-server-options" ]; then
    echo "Updating PPPoE config..."
    sudo cp "$GENERATED_DIR/pppoe-server-options" "$PPPOE_DIR/pppoe-server-options"
    # Restart PPPoE server (if service exists, or kill/start process)
    # For now, assuming a service or manual start. 
    # Real implementation might need more specific commands.
fi

# Apply Hostapd (WiFi AP)
if [ -f "$GENERATED_DIR/hostapd.conf" ]; then
    echo "Updating Hostapd config..."
    # Stop hostapd first to avoid conflicts
    sudo systemctl stop hostapd || true
    
    # If file is not empty (meaning AP is configured)
    if [ -s "$GENERATED_DIR/hostapd.conf" ]; then
        sudo cp "$GENERATED_DIR/hostapd.conf" "/etc/hostapd/hostapd.conf"
        # Unmask and start
        sudo systemctl unmask hostapd
        sudo systemctl enable hostapd
        sudo systemctl start hostapd
    else
        # If empty, disable hostapd
        sudo systemctl disable hostapd
    fi
fi

# Apply Load Balancing
if [ -f "$GENERATED_DIR/setup_loadbalance.sh" ]; then
    echo "Applying load balancing rules..."
    sudo chmod +x "$GENERATED_DIR/setup_loadbalance.sh"
    sudo "$GENERATED_DIR/setup_loadbalance.sh"
fi

echo "Configuration applied successfully!"
