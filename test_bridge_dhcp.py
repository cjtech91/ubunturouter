import json
import os
from app.services.config_service import generate_dhcp_config, generate_dhcp_default_config, generate_pppoe_config

# Mock Config with Bridge DHCP enabled
config = {
    'network': {
        'eth0': {'role': 'wan', 'ip': ''},
        'eth1': {'role': 'lan', 'ip': '192.168.172.1'},
        'eth2': {'role': 'lan', 'ip': ''}
    },
    'dhcp': {
        'br0': {
            'enabled': True,
            'start': '192.168.172.100',
            'end': '192.168.172.200'
        },
        'eth1': {
            'enabled': False, # Disabled physical interface DHCP
            'start': '192.168.172.2',
            'end': '192.168.172.50'
        }
    },
    'pppoe': {
        'br0': {
            'enabled': True,
            'local_ip': '10.0.0.1',
            'remote_start': '10.0.0.2',
            'dns': '8.8.8.8'
        }
    }
}

# Generate
generate_dhcp_config(config)
generate_dhcp_default_config(config)
generate_pppoe_config(config)

# Read and print
print("--- ISC DHCP Config ---")
with open('generated/dhcpd.conf', 'r') as f:
    print(f.read())

print("\n--- ISC DHCP Defaults ---")
with open('generated/isc-dhcp-server', 'r') as f:
    print(f.read())

print("\n--- PPPoE Config ---")
with open('generated/pppoe-server-options', 'r') as f:
    print(f.read())
