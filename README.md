# Ubuntu Router Manager

A web-based dashboard to manage an Ubuntu-based router.

## Features

- **Automatic Network Card Recognition**: Detects and displays network interfaces.
- **Dynamic Port Configuration**: Assign interfaces as WAN or LAN.
- **Smart Load Balancing**: Configure weights for Multi-WAN setups.
- **DHCP Server**: Configure DHCP settings for LAN interfaces.
- **PPPoE Server**: Configure PPPoE server settings for LAN interfaces.
- **System Integration**: Automatically applies configurations to Netplan, DHCP, etc.

## Deployment Guide (Production)

To deploy this on a fresh Ubuntu Server:

1.  **Clone the repository**:
    ```bash
    git clone <repository_url>
    cd ubuntu-router
    ```

2.  **Run the Installer**:
    This script will install system dependencies (DHCP, PPPoE, etc.), Python requirements, and set up a systemd service to run the app on boot.
    ```bash
    chmod +x scripts/install.sh
    ./scripts/install.sh
    ```

3.  **Access the Dashboard**:
    Open your browser and navigate to the IP address of your router (e.g., `http://192.168.1.1`).

## Development

1.  **Install Python dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Run the application**:
    ```bash
    python run.py
    ```

## Configuration Output

The application generates configuration files in the `generated/` directory. When you click **Apply Configuration to System** in the dashboard, the following happens:

- `01-netcfg.yaml` is copied to `/etc/netplan/` and `netplan apply` is run.
- `dhcpd.conf` is copied to `/etc/dhcp/` and `isc-dhcp-server` is restarted.
- `pppoe-server-options` is copied to `/etc/ppp/`.
- `setup_loadbalance.sh` is executed to apply routing rules.

## Security Note

The application requires `sudo` privileges to apply network configurations. The `install.sh` script runs the application as root. For a more secure production environment, consider refining sudo permissions for specific commands rather than running the entire web server as root.
