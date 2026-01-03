import sys
import os

# Add the project root to the python path
sys.path.append(os.getcwd())

from app.services.network_service import get_network_interfaces
from app.services.config_service import save_config, load_config

def set_default_ip():
    print("Detecting network interfaces...")
    try:
        interfaces = get_network_interfaces()
    except Exception as e:
        print(f"Error detecting interfaces: {e}")
        return

    target_iface = None
    
    # Priority 1: Wired Ethernet (usually starts with e, like eth0, enp3s0, end0)
    for iface in interfaces:
        name = iface['name']
        if name == 'lo': continue
        if iface.get('is_wireless'): continue
        
        if name.startswith(('e', 'en', 'eth')):
            target_iface = name
            break
            
    # Priority 2: Any non-wireless, non-loopback
    if not target_iface:
        for iface in interfaces:
            if iface['name'] == 'lo': continue
            if not iface.get('is_wireless'):
                target_iface = iface['name']
                break

    # Priority 3: Anything else (fallback)
    if not target_iface and interfaces:
        for iface in interfaces:
             if iface['name'] != 'lo':
                target_iface = iface['name']
                break

    if target_iface:
        print(f"Found primary interface: {target_iface}")
        print(f"Configuring {target_iface} as WAN (DHCP Client) to preserve current access.")
        
        config = load_config()
        if 'network' not in config:
            config['network'] = {}
        if 'dhcp' not in config:
            config['dhcp'] = {}
            
        # Set the network configuration to WAN (DHCP)
        # This assumes the interface is currently getting an IP via DHCP
        config['network'][target_iface] = {
            'role': 'wan',
            'ip': '' # Empty IP implies DHCP in our config logic
        }
        
        # Ensure DHCP server is NOT enabled on this WAN interface
        if target_iface in config['dhcp']:
            del config['dhcp'][target_iface]
        
        # Save triggers the generation of configs
        save_config(config)
        print("Configuration generated successfully.")
    else:
        print("Error: No suitable network interface found to configure.")

if __name__ == '__main__':
    set_default_ip()
