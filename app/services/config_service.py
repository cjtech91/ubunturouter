import json
import os

CONFIG_FILE = 'config/settings.json'
GENERATED_DIR = 'generated'

# Ensure directories exist
os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
os.makedirs(GENERATED_DIR, exist_ok=True)

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)
    
    # Auto-generate system configs on save
    generate_netplan_config(config)
    generate_dhcp_config(config)
    generate_dhcp_default_config(config)
    generate_pppoe_config(config)
    generate_loadbalance_script(config)
    generate_hostapd_config(config)

def generate_netplan_config(config):
    """
    Generates a Netplan YAML configuration based on the stored settings.
    """
    network = config.get('network', {})
    netplan = {
        'network': {
            'version': 2,
            'renderer': 'networkd',
            'ethernets': {},
            'wifis': {},
            'bridges': {
                'br0': {
                    'interfaces': [],
                    'addresses': [],
                    'parameters': {
                        'stp': False,
                        'forward-delay': 0
                    },
                    'dhcp4': False,
                    'optional': True
                }
            }
        }
    }
    
    # Check if we need to remove empty sections
    has_ethernet = False
    has_wifi = False
    has_bridge = False
    bridge_interfaces = []
    
    # First pass: Identify LAN interfaces for the bridge
    lan_ip = None
    
    for iface, settings in network.items():
        role = settings.get('role')
        if role == 'lan':
            # We use the first LAN IP found as the bridge IP
            if not lan_ip and settings.get('ip'):
                lan_ip = settings.get('ip')
            
            # Add to bridge interfaces list
            bridge_interfaces.append(iface)

    # Configure Bridge IP if found
    if lan_ip:
        netplan['network']['bridges']['br0']['addresses'] = [lan_ip] if '/' in lan_ip else [f"{lan_ip}/24"]
        has_bridge = True

    for iface, settings in network.items():
        role = settings.get('role')
        ip = settings.get('ip')
        # ... existing logic ...
        
        # Let's try to detect if it's wifi based on settings keys presence
        ssid = settings.get('ssid')
        psk = settings.get('psk')
        
        iface_config = {}
        
        if role == 'wan':
            if ip:
                iface_config['addresses'] = [ip] if '/' in ip else [f"{ip}/24"]
                iface_config['dhcp4'] = False
            else:
                iface_config['dhcp4'] = True
            
            # If it's a WiFi Client (WAN)
            if ssid and psk: 
                has_wifi = True
                iface_config['access-points'] = {
                    ssid: {'password': psk}
                }
                netplan['network']['wifis'][iface] = iface_config
                continue # Skip adding to ethernets

        elif role == 'lan':
            # LAN interfaces are now part of the bridge, so they don't get individual IPs
            iface_config['dhcp4'] = False
            iface_config['optional'] = True
            
            # If it's WiFi AP (LAN), hostapd will handle the AP part, 
            # but we need to tell hostapd to use the bridge 'br0'
            pass

        iface_config['optional'] = True # Prevent boot hang if interface missing
        
        # Add to appropriate section
        if ssid: 
            has_wifi = True
            # For WiFi AP mode, we need access-points block empty or minimal?
            # Actually netplan just needs to bring the interface UP.
            # Hostapd will attach it to the bridge if configured in hostapd.conf
            # BUT: Netplan can't easily bridge a wifi interface directly in 'bridges' -> 'interfaces' list 
            # because hostapd needs to put it in Master mode first.
            # So for WiFi AP, we usually DON'T list it in netplan bridge 'interfaces'.
            # Instead, we configure hostapd to bridge it.
            
            # So, if this is a LAN WiFi (AP), we add it to 'wifis' but NOT to bridge_interfaces for netplan.
            if iface in bridge_interfaces:
                bridge_interfaces.remove(iface) # Handle in hostapd
            
            if role == 'lan':
                 # Just bring it up, no IP
                 iface_config['dhcp4'] = False
                 
            netplan['network']['wifis'][iface] = iface_config
        else:
            has_ethernet = True
            netplan['network']['ethernets'][iface] = iface_config

    # Assign collected ethernet interfaces to the bridge
    # Filter out WAN interfaces from bridge_interfaces (already done by only picking role='lan')
    # Filter out WiFi interfaces (handled above by removing from list)
    netplan['network']['bridges']['br0']['interfaces'] = bridge_interfaces

    if not has_ethernet:
        del netplan['network']['ethernets']
    if not has_wifi:
        del netplan['network']['wifis']
    if not has_bridge or not bridge_interfaces:
         # If no interfaces in bridge, or no bridge IP, remove it
         # But wait, if we have WiFi AP bridging to br0, we might need br0 even if no eth ports are in it?
         # Yes, if we have a WiFi AP, hostapd will attach to br0. br0 needs to exist.
         # So we keep br0 if has_bridge is True (meaning we found a LAN IP).
         if not has_bridge:
            del netplan['network']['bridges']
    
    # Write to file
    with open(os.path.join(GENERATED_DIR, '01-netcfg.yaml'), 'w') as f:
        f.write("# This file is generated by Ubuntu Router UI\n")
        f.write(json.dumps(netplan, indent=2))

def generate_hostapd_config(config):
    """
    Generates hostapd.conf for WiFi AP mode
    """
    network = config.get('network', {})
    content = ""
    
    for iface, settings in network.items():
        # Only for LAN role with SSID set (implies AP mode)
        if settings.get('role') == 'lan' and settings.get('ssid'):
            content += f"interface={iface}\n"
            content += f"bridge=br0\n"
            content += f"driver=nl80211\n"
            content += f"ssid={settings.get('ssid')}\n"
            content += f"hw_mode=g\n"
            content += f"channel={settings.get('channel', '6')}\n"
            
            # Check security type (default to WPA2 if psk is present, else Open)
            psk = settings.get('psk')
            if psk:
                content += f"wpa=2\n"
                content += f"wpa_passphrase={psk}\n"
                content += f"wpa_key_mgmt=WPA-PSK\n"
                content += f"rsn_pairwise=CCMP\n"
            else:
                # Open security
                content += f"# Open Security (No WPA/WPA2)\n"
            
            content += "\n"
            
    with open(os.path.join(GENERATED_DIR, 'hostapd.conf'), 'w') as f:
        f.write(content)

def generate_dhcp_config(config):
    """
    Generates ISC DHCP Server config
    """
    dhcp_settings = config.get('dhcp', {})
    content = "default-lease-time 600;\nmax-lease-time 7200;\nauthoritative;\n\n"
    
    for iface, settings in dhcp_settings.items():
        if settings.get('enabled'):
            start = settings.get('start')
            end = settings.get('end')
            # Simplified subnet calculation (assuming /24)
            if start:
                subnet = start.rsplit('.', 1)[0] + '.0'
                content += f"subnet {subnet} netmask 255.255.255.0 {{\n"
                content += f"  range {start} {end};\n"
                content += f"  option routers {subnet.rsplit('.', 1)[0] + '.1'};\n" # Guessing router IP
                content += f"  option domain-name-servers 8.8.8.8, 8.8.4.4;\n"
                content += f"}}\n\n"

    with open(os.path.join(GENERATED_DIR, 'dhcpd.conf'), 'w') as f:
        f.write(content)

def generate_dhcp_default_config(config):
    """
    Generates /etc/default/isc-dhcp-server file to specify interfaces
    """
    dhcp_settings = config.get('dhcp', {})
    interfaces = []
    
    # Check if we have a bridge configured
    # Ideally we should pass the generated netplan structure or flag, but we can infer again
    has_bridge_lan = False
    for iface, settings in config.get('network', {}).items():
        if settings.get('role') == 'lan':
            has_bridge_lan = True
            break
            
    for iface, settings in dhcp_settings.items():
        if settings.get('enabled'):
            # If this interface is a LAN interface and we have a bridge, we should listen on 'br0' instead
            # Note: config['dhcp'] keys are physical interfaces (e.g. eth1). 
            # We need to map them to br0 if they are part of the bridge.
            network_settings = config.get('network', {}).get(iface, {})
            if network_settings.get('role') == 'lan' and has_bridge_lan:
                if 'br0' not in interfaces:
                    interfaces.append('br0')
            else:
                interfaces.append(iface)
            
    iface_str = " ".join(interfaces)
    content = f'INTERFACESv4="{iface_str}"\n'
    content += 'INTERFACESv6=""\n'
    
    with open(os.path.join(GENERATED_DIR, 'isc-dhcp-server'), 'w') as f:
        f.write(content)

def generate_pppoe_config(config):
    """
    Generates PPPoE Server config (rp-pppoe) and startup script
    """
    pppoe_settings = config.get('pppoe', {})
    
    # 1. Generate options file
    options_content = "# PPPoE Server Configuration\n"
    options_content += "require-chap\n"
    options_content += "lcp-echo-interval 10\n"
    options_content += "lcp-echo-failure 2\n"
    
    # Use the first DNS found (limitation of global options file)
    dns_set = False
    for iface, settings in pppoe_settings.items():
        if settings.get('enabled') and not dns_set:
             options_content += f"ms-dns {settings.get('dns', '8.8.8.8')}\n"
             dns_set = True
             
    with open(os.path.join(GENERATED_DIR, 'pppoe-server-options'), 'w') as f:
        f.write(options_content)

    # 2. Generate Startup Script
    script_content = "#!/bin/bash\n# Start PPPoE Servers\n\n"
    script_content += "killall pppoe-server 2>/dev/null\n\n"
    
    for iface, settings in pppoe_settings.items():
        if settings.get('enabled'):
            local_ip = settings.get('local_ip')
            remote_start = settings.get('remote_start')
            # Assuming remote_end isn't strictly used by pppoe-server cli, it uses -N for count. 
            # But usually we just pass -R remote_start. 
            # pppoe-server -I <iface> -L <local> -R <remote_start> -O /etc/ppp/pppoe-server-options
            
            script_content += f"echo 'Starting PPPoE on {iface}...'\n"
            script_content += f"pppoe-server -I {iface} -L {local_ip} -R {remote_start} -O /etc/ppp/pppoe-server-options\n"
            
    with open(os.path.join(GENERATED_DIR, 'start_pppoe.sh'), 'w') as f:
        f.write(script_content)

def generate_loadbalance_script(config):
    """
    Generates a shell script to configure routing for load balancing
    """
    lb_settings = config.get('loadbalance', {})
    
    # Check if load balancing is actually configured
    has_lb = False
    for iface, settings in lb_settings.items():
        if settings.get('enabled'):
            has_lb = True
            break
            
    content = "#!/bin/bash\n# Load Balancing Setup\n\n"
    
    if has_lb:
        # Only flush if we are actually configuring LB
        # content += "ip rule flush\n" # Too dangerous for default
        content += "# Note: ip rule flush disabled for safety. \n"
        content += "# ip route flush cache\n\n"
        
        # This is a very simplified example of policy routing
        for iface, settings in lb_settings.items():
            if settings.get('enabled'):
                weight = settings.get('weight')
                content += f"# Interface {iface} weight {weight}\n"
                # In reality:
                # 1. Create routing tables
                # 2. Add default routes to tables
                # 3. Add ip rules
                # 4. Add nexthop weights to default route
    else:
        content += "# No load balancing configured.\n"
        content += "echo 'No load balancing rules to apply.'\n"
            
    with open(os.path.join(GENERATED_DIR, 'setup_loadbalance.sh'), 'w') as f:
        f.write(content)
