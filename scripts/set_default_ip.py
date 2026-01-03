import sys
import os

# Add the project root to the python path
sys.path.append(os.getcwd())

from app.services.network_service import get_network_interfaces
from app.services.config_service import save_config, load_config

def get_multiple_interface_choices(interfaces, prompt_text, exclude_list=[]):
    """
    Prompts user to select multiple interfaces from the list.
    Returns a list of selected interface names.
    """
    valid_interfaces = [i for i in interfaces if i['name'] != 'lo' and i['name'] not in exclude_list]
    
    if not valid_interfaces:
        return []

    print(f"\n{prompt_text}")
    for idx, iface in enumerate(valid_interfaces):
        # Format IP addresses for display
        ip_list = []
        for addr in iface.get('addresses', []):
            if addr.get('family') == 'IPv4':
                ip_list.append(addr.get('address'))
        
        ip_str = ", ".join(ip_list) if ip_list else "No IP"
        print(f"{idx + 1}. {iface['name']} ({ip_str})")
    
    print("0. None / Skip")
    print("(Enter multiple numbers separated by space or comma, e.g. '1 2')")

    while True:
        try:
            choice_str = input("Select interface numbers: ")
            if not choice_str.strip():
                continue
            
            if choice_str.strip() == '0':
                return []

            choices = choice_str.replace(',', ' ').split()
            selected_names = []
            
            for c in choices:
                try:
                    idx = int(c) - 1
                    if 0 <= idx < len(valid_interfaces):
                        name = valid_interfaces[idx]['name']
                        if name not in selected_names:
                            selected_names.append(name)
                except ValueError:
                    pass
            
            if selected_names:
                return selected_names
            else:
                print("No valid interfaces selected. Try again or enter 0 to skip.")
                
        except ValueError:
            print("Please enter valid numbers.")

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
    
    wan_choices = get_multiple_interface_choices(interfaces, "Available Interfaces for WAN (Select 1):")
    wan_iface = wan_choices[0] if wan_choices else None
    
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
    print("Select interfaces to be part of the LAN Bridge (Static IP: 192.168.172.1).")
    print("A DHCP Server will be enabled on the bridge (192.168.172.2-254).")
    
    exclude_list = [wan_iface] if wan_iface else []
    lan_choices = get_multiple_interface_choices(interfaces, "Available Interfaces for LAN:", exclude_list)
    
    if lan_choices:
        print(f"Selected LAN Interfaces: {', '.join(lan_choices)}")
        
        # Configure each LAN interface
        for idx, iface in enumerate(lan_choices):
            config['network'][iface] = {
                'role': 'lan',
                'ip': '192.168.172.1'
            }
            # Only enable DHCP on the first one (config_service will map it to br0)
            # This avoids duplicate DHCP scopes if config_service isn't fully robust
            if idx == 0:
                config['dhcp'][iface] = {
                    'enabled': True,
                    'start': '192.168.172.2',
                    'end': '192.168.172.254'
                }
    else:
        print("No LAN interface selected.")

    # 3. Configure WiFi Hotspot (Auto-detect)
    print("\n[Step 3] Configuring WiFi Hotspot")
    
    wifi_iface = None
    for iface in interfaces:
        # Simple heuristic: name starts with w (wlan0, wlp3s0) or has wireless extension
        # Check if not already used
        if iface['name'].startswith('w') and iface['name'] != wan_iface and iface['name'] not in (lan_choices or []):
             wifi_iface = iface['name']
             break
    
    if wifi_iface:
        print(f"Found Wireless Interface: {wifi_iface}")
        print("Configuring Hotspot: SSID='sharplink', Security=Open")
        print("Bridging WiFi to LAN (IP: 192.168.172.1)")
        
        config['network'][wifi_iface] = {
            'role': 'lan',
            'ip': '192.168.172.1', # Same as LAN IP because it's bridged
            'ssid': 'sharplink',
            # 'psk': None, # Open security
            'channel': '6'
        }
        # DHCP is already handled by the LAN interface config which now applies to br0
        # We don't need a separate DHCP entry for wifi_iface if it's bridged and the bridge has DHCP
        
        # However, our current DHCP generation iterates over interfaces.
        # We need to make sure DHCP is bound to 'br0' instead of individual interfaces?
        # Or simply bind to the bridge interface name if it exists.
        
        # NOTE: The config_service logic needs to be smart enough to bind DHCP to br0 if bridging is active.
        # For now, we will add dhcp config to the wifi interface as a placeholder, 
        # but the generator should probably merge them.
        
        # Actually, simpler: Since we set role='lan' and ip='192.168.172.1', 
        # the bridge logic in config_service will pick this up and add br0 with this IP.
        # We just need to ensure the DHCP server listens on 'br0'.
    else:
        print("No suitable wireless interface found for Hotspot.")

    if not wan_iface and not lan_iface and not wifi_iface:
        print("\nNo interfaces configured. Exiting.")
        return

    # Save Configuration
    print("\nGenerating configuration files...")
    save_config(config)
    print("Configuration generated successfully.")

if __name__ == '__main__':
    set_default_ip()
