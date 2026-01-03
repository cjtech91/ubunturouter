import json
import os
from app.services.config_service import generate_netplan_config, generate_hostapd_config, generate_dhcp_default_config

# Mock Config with Multiple LAN ports and WiFi
config = {
    'network': {
        'eth0': {'role': 'wan', 'ip': ''},
        'eth1': {'role': 'lan', 'ip': '192.168.172.1'},
        'eth2': {'role': 'lan', 'ip': '192.168.172.1'},
        'wlan0': {'role': 'lan', 'ip': '192.168.172.1', 'ssid': 'test_wifi', 'psk': 'password'}
    },
    'dhcp': {
        'eth1': {'enabled': True, 'start': '192.168.172.2', 'end': '192.168.172.254'}
    }
}

# Generate
generate_netplan_config(config)
generate_hostapd_config(config)
generate_dhcp_default_config(config)

# Read and print
print("--- Netplan ---")
with open('generated/01-netcfg.yaml', 'r') as f:
    print(f.read())

print("\n--- Hostapd ---")
with open('generated/hostapd.conf', 'r') as f:
    print(f.read())

print("\n--- ISC DHCP Default ---")
with open('generated/isc-dhcp-server', 'r') as f:
    print(f.read())
