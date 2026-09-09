import sys
import subprocess
import requests
import socket
import json
from concurrent.futures import ThreadPoolExecutor

# Common Samsung ports
PORTS = [8888, 8080, 8000, 7676, 56001]

def get_my_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Doesn't need to actually connect
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def check_port(ip, port):
    """Fast check if a port is open."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.5)
        result = sock.connect_ex((ip, port))
        sock.close()
        return result == 0
    except:
        return False

def inspect_device(ip):
    """Tries to identify the device by hitting common Samsung endpoints."""
    info = {"ip": ip, "type": "Unknown", "name": "Unknown", "ports": []}
    
    # 1. Check Ports
    open_ports = []
    for p in PORTS:
        if check_port(ip, p):
            open_ports.append(p)
    
    if not open_ports:
        return None
    
    info["ports"] = open_ports

    # 2. Try to fetch details (Local API v2)
    # Most Samsung devices expose basic info at /device or /api/v2/
    try:
        url = f"http://{ip}:8888/device"
        r = requests.get(url, timeout=2, verify=False)
        if r.status_code == 200:
            data = r.json()
            info["type"] = data.get("type", "Samsung Device")
            info["name"] = data.get("name", "Unnamed")
            info["model"] = data.get("model", "")
            return info
    except:
        pass

    # 3. Try Legacy TV/Appliance port (8001/8000)
    try:
        url = f"http://{ip}:8001/api/v2/"
        r = requests.get(url, timeout=2, verify=False)
        if r.status_code == 200:
            data = r.json()
            info["type"] = "Smart TV/Hub"
            info["name"] = data.get("name", "Samsung TV")
            return info
    except:
        pass
        
    return info

def scan_network():
    my_ip = get_my_ip()
    subnet = ".".join(my_ip.split(".")[:3]) + ".0/24"
    print(f"📡 Scanning Network: {subnet} (This may take 10-20s)...")

    # Use Nmap to find devices quickly
    # -p 8888,8080 : Only check Samsung relevant ports
    # --open : Only show devices listening
    cmd = f"nmap -p 8888,8080,8001 --open -oG - {subnet}"
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        ips = []
        for line in result.stdout.splitlines():
            if "Host:" in line:
                # Extract IP
                ip = line.split()[1]
                ips.append(ip)
        
        print(f"   Found {len(ips)} potential devices. Inspecting...")
        
        found_devices = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            results = executor.map(inspect_device, ips)
            
        for res in results:
            if res:
                found_devices.append(res)
                print(f"   ✅ FOUND: {res['name']} ({res['type']}) @ {res['ip']}")
                print(f"      Model: {res.get('model', 'N/A')} | Ports: {res['ports']}")
        
        if not found_devices:
            print("   ❌ No Samsung devices found exposing local API ports.")
            print("   (They might be in deep sleep or on a different subnet)")
            
    except Exception as e:
        print(f"   ⚠️ Nmap Error: {e}")
        print("   Make sure nmap is installed: 'pkg install nmap'")

if __name__ == "__main__":
    scan_network()

