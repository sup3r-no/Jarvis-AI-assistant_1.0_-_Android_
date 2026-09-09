import requests
import json
import ssl
import socket
import urllib3

# Disable warnings for self-signed certs (standard for local devices)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TARGET_IP = "10.0.0.178"
PORT = 8888

def get_ssl_info(ip, port):
    """
    Connects to the port and reads the Security Certificate.
    Samsung often puts the Model Name inside the 'Common Name' (CN).
    """
    print(f"🔐 Fetching Security Certificate from {ip}:{port}...")
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        with socket.create_connection((ip, port), timeout=3) as sock:
            with ctx.wrap_socket(sock, server_hostname=ip) as ssock:
                cert = ssock.getpeercert()
                # If cert is empty, try binary fetch
                if not cert:
                    print("   (Certificate received but empty logic)")
                return cert
    except Exception as e:
        print(f"   ❌ SSL Error: {e}")
        return None

def try_endpoints(ip, port):
    """
    Tries common Samsung API paths via HTTPS.
    """
    endpoints = [
        "/device",
        "/api/v2/device",
        "/api/v2/",
        "/system/info"
    ]
    
    print(f"\n📡 Probing API Endpoints on https://{ip}:{port}...")
    
    for ep in endpoints:
        url = f"https://{ip}:{port}{ep}"
        try:
            # We use verify=False to accept the self-signed cert
            r = requests.get(url, verify=False, timeout=3)
            print(f"   👉 {ep} : Status {r.status_code}")
            
            if r.status_code == 200:
                print("\n✅ SUCCESS! Payload found:")
                try:
                    data = r.json()
                    print(json.dumps(data, indent=2))
                    return data
                except:
                    print(r.text[:200]) # Print first 200 chars if not JSON
        except requests.exceptions.ConnectionError:
            print(f"   ❌ {ep} : Connection Refused")
        except Exception as e:
            print(f"   ⚠️ {ep} : {e}")

if __name__ == "__main__":
    # 1. Try SSL Grab
    get_ssl_info(TARGET_IP, PORT)
    
    # 2. Try HTTPS API
    try_endpoints(TARGET_IP, PORT)

