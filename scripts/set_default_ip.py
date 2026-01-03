import sys
import os

# Add the project root to the python path
sys.path.append(os.getcwd())

from app.services.network_service import get_network_interfaces
from app.services.config_service import save_config, load_config

def get_interface_choice(interfaces, prompt_text, exclude_list=[]):
    """
    Prompts user to select an interface from the list.
    """
    valid_interfaces = [i for i in interfaces if i['name'] != 'lo' and i['name'] not in exclude_list]
    
    if not valid_interfaces:
        return None

    print(f"\n{prompt_text}")
    for idx, iface in enumerate(valid_interfaces):
        # Format IP addresses for display
        ip_list = []
        for addr in iface.get('addresses', []):
            if addr.get('family') == 'IPv4':
                ip_list.append(addr.get('address'))
        
        ip_str = ", ".join(ip_list) if ip_list else "No IP"
        print(f"{idx + 1}. {iface['name']} ({ip_str})")
    
    print("0. Skip / None")

    while True:
        try:
            choice = input("Select interface number: ")
            if choice == '0':
                return None
            idx = int(choice) - 1
            if 0 <= idx < len(valid_interfaces):
                return valid_interfaces[idx]['name']
            else:
                print("Invalid selection. Try again.")
        except ValueError:
            print("Please enter a number.")

def set_default_ip():
    print("Detecting network interfaces...")
    try:
        interfaces = get_network_interfaces()
    except Exception as e:
        print(f"Error detecting interfaces: {e}")
        return

    # Load existing config
    config = load_config()
    if 'network' not in config:
        config['network'] = {}
    if 'dhcp' not in config:
        config['dhcp'] = {}

    print("\n==========================================")
    print("  Network Interface Configuration")
    print("==========================================")
    
    # 1. Select WAN Interface
    print("\n[Step 1] Select WAN Interface")
    print("This interface will maintain its current connection (DHCP Client).")
    print("Select the interface you are currently using for SSH/Internet.")
    
    wan_iface = get_interface_choice(interfaces, "Available Interfaces for WAN:")
    
    if wan_iface:
        print(f"Selected WAN: {wan_iface}")
        config['network'][wan_iface] = {
            'role': 'wan',
            'ip': '' # Empty IP implies DHCP
        }
        # Disable DHCP server on WAN
        if wan_iface in config['dhcp']:
            del config['dhcp'][wan_iface]
    else:
        print("No WAN interface selected.")

    # 2. Select LAN Interface
    print("\n[Step 2] Select LAN Interface")
    print("This interface will be configured with Static IP: 192.168.172.1")
    print("A DHCP Server will be enabled on this interface (192.168.172.2-254).")
    
    exclude_list = [wan_iface] if wan_iface else []
    lan_iface = get_interface_choice(interfaces, "Available Interfaces for LAN:", exclude_list)
    
    if lan_iface:
        print(f"Selected LAN: {lan_iface}")
        config['network'][lan_iface] = {
            'role': 'lan',
            'ip': '192.168.172.1'
        }
        config['dhcp'][lan_iface] = {
            'enabled': True,
            'start': '192.168.172.2',
            'end': '192.168.172.254'
        }
    else:
        print("No LAN interface selected.")

    if not wan_iface and not lan_iface:
        print("\nNo interfaces configured. Exiting.")
        return

    # Save Configuration
    print("\nGenerating configuration files...")
    save_config(config)
    print("Configuration generated successfully.")

if __name__ == '__main__':
    set_default_ip()
