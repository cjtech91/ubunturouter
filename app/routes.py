from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from app.services.network_service import get_network_interfaces
from app.services.config_service import load_config, save_config
import subprocess
import os

bp = Blueprint('main', __name__)

@bp.route('/apply_config', methods=['POST'])
def apply_config():
    try:
        # Path to the apply script
        script_path = os.path.join(os.getcwd(), 'scripts', 'apply_configs.sh')
        
        # Ensure script is executable
        subprocess.run(['chmod', '+x', script_path], check=True)
        
        # Run the script
        result = subprocess.run([script_path], capture_output=True, text=True, check=True)
        
        flash(f'Configuration applied successfully: {result.stdout}', 'success')
    except subprocess.CalledProcessError as e:
        flash(f'Error applying configuration: {e.stderr}', 'error')
    except Exception as e:
        flash(f'An unexpected error occurred: {str(e)}', 'error')
        
    return redirect(url_for('main.dashboard'))

@bp.route('/')
def dashboard():
    interfaces = get_network_interfaces()
    return render_template('dashboard.html', interfaces=interfaces)

@bp.route('/network/config', methods=['GET', 'POST'])
def network_config():
    if request.method == 'POST':
        # Logic to save network config
        config = load_config()
        network_settings = {}
        
        # Iterate through form data to build network settings
        for key, value in request.form.items():
            if key.startswith('role_'):
                iface = key.replace('role_', '')
                if iface not in network_settings:
                    network_settings[iface] = {}
                network_settings[iface]['role'] = value
            elif key.startswith('ip_'):
                iface = key.replace('ip_', '')
                if iface not in network_settings:
                    network_settings[iface] = {}
                network_settings[iface]['ip'] = value
        
        config['network'] = network_settings
        save_config(config)
        return redirect(url_for('main.network_config'))
        
    interfaces = get_network_interfaces()
    config = load_config()
    current_settings = config.get('network', {})
    
    # Merge current settings into interfaces for display
    for iface in interfaces:
        if iface['name'] in current_settings:
            iface['role'] = current_settings[iface['name']].get('role', 'unassigned')
            iface['assigned_ip'] = current_settings[iface['name']].get('ip', '')
            
    return render_template('network_config.html', interfaces=interfaces)

@bp.route('/loadbalance', methods=['GET', 'POST'])
def loadbalance():
    config = load_config()
    network_settings = config.get('network', {})
    lb_settings = config.get('loadbalance', {})
    
    # Filter WAN interfaces
    wan_interfaces = []
    for iface_name, settings in network_settings.items():
        if settings.get('role') == 'wan':
            wan_interfaces.append({
                'name': iface_name,
                'weight': lb_settings.get(iface_name, {}).get('weight', 1),
                'enabled': lb_settings.get(iface_name, {}).get('enabled', True)
            })
            
    if request.method == 'POST':
        new_lb_settings = {}
        for iface in wan_interfaces:
            weight = request.form.get(f'weight_{iface["name"]}', 1)
            enabled = request.form.get(f'enabled_{iface["name"]}') == 'on'
            new_lb_settings[iface['name']] = {
                'weight': int(weight),
                'enabled': enabled
            }
        
        config['loadbalance'] = new_lb_settings
        save_config(config)
        return redirect(url_for('main.loadbalance'))

    return render_template('loadbalancing.html', wan_interfaces=wan_interfaces)

@bp.route('/dhcp', methods=['GET', 'POST'])
def dhcp():
    config = load_config()
    network_settings = config.get('network', {})
    dhcp_settings = config.get('dhcp', {})
    
    # Filter LAN interfaces
    lan_interfaces = []
    for iface_name, settings in network_settings.items():
        if settings.get('role') == 'lan':
            if_settings = dhcp_settings.get(iface_name, {})
            lan_interfaces.append({
                'name': iface_name,
                'dhcp_enabled': if_settings.get('enabled', False),
                'range_start': if_settings.get('start', ''),
                'range_end': if_settings.get('end', ''),
                'lease_time': if_settings.get('lease', 86400)
            })
            
    if request.method == 'POST':
        new_dhcp_settings = {}
        for iface in lan_interfaces:
            new_dhcp_settings[iface['name']] = {
                'enabled': request.form.get(f'enable_{iface["name"]}') == 'on',
                'start': request.form.get(f'start_{iface["name"]}'),
                'end': request.form.get(f'end_{iface["name"]}'),
                'lease': request.form.get(f'lease_{iface["name"]}')
            }
        
        config['dhcp'] = new_dhcp_settings
        save_config(config)
        return redirect(url_for('main.dhcp'))

    return render_template('dhcp.html', lan_interfaces=lan_interfaces)

@bp.route('/pppoe', methods=['GET', 'POST'])
def pppoe():
    config = load_config()
    network_settings = config.get('network', {})
    pppoe_settings = config.get('pppoe', {})
    
    # Filter LAN interfaces
    lan_interfaces = []
    for iface_name, settings in network_settings.items():
        if settings.get('role') == 'lan':
            if_settings = pppoe_settings.get(iface_name, {})
            lan_interfaces.append({
                'name': iface_name,
                'pppoe_enabled': if_settings.get('enabled', False),
                'local_ip': if_settings.get('local_ip', ''),
                'remote_start': if_settings.get('remote_start', ''),
                'remote_end': if_settings.get('remote_end', ''),
                'dns': if_settings.get('dns', '8.8.8.8, 8.8.4.4')
            })
            
    if request.method == 'POST':
        new_pppoe_settings = {}
        for iface in lan_interfaces:
            new_pppoe_settings[iface['name']] = {
                'enabled': request.form.get(f'enable_{iface["name"]}') == 'on',
                'local_ip': request.form.get(f'local_ip_{iface["name"]}'),
                'remote_start': request.form.get(f'remote_start_{iface["name"]}'),
                'remote_end': request.form.get(f'remote_end_{iface["name"]}'),
                'dns': request.form.get(f'dns_{iface["name"]}')
            }
        
        config['pppoe'] = new_pppoe_settings
        save_config(config)
        return redirect(url_for('main.pppoe'))

    return render_template('pppoe.html', lan_interfaces=lan_interfaces)
