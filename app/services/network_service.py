import psutil
import socket
import platform

def get_network_interfaces():
    """
    Returns a list of network interfaces with their status and IP addresses.
    """
    interfaces = []
    stats = psutil.net_if_stats()
    addrs = psutil.net_if_addrs()

    for name, stat in stats.items():
        if_info = {
            'name': name,
            'is_up': stat.isup,
            'speed': stat.speed,
            'mtu': stat.mtu,
            'addresses': []
        }

        if name in addrs:
            for addr in addrs[name]:
                if addr.family == socket.AF_INET:
                    if_info['addresses'].append({
                        'family': 'IPv4',
                        'address': addr.address,
                        'netmask': addr.netmask,
                        'broadcast': addr.broadcast
                    })
                elif addr.family == socket.AF_INET6:
                    if_info['addresses'].append({
                        'family': 'IPv6',
                        'address': addr.address
                    })
        
        interfaces.append(if_info)
    
    return interfaces

def detect_new_cards():
    """
    This function would ideally run in a background loop or be triggered by udev events.
    For the dashboard, calling get_network_interfaces() is sufficient to show current state.
    """
    return get_network_interfaces()
