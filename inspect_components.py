import requests
import json
import os

TOKEN_FILE = "/data/data/com.termux/files/home/.shortcuts/token.txt"
DEVICES_FILE = "/data/data/com.termux/files/home/my_devices.json"

def load_token():
    with open(TOKEN_FILE, "r") as f: return f.read().strip()

def load_devices():
    with open(DEVICES_FILE, "r") as f: return json.load(f)

def inspect():
    token = load_token()
    devices = load_devices()
    
    # Find Microwave ID
    target_id = None
    for name, data in devices.items():
        if "microwave" in name:
            target_id = data["id"]
            break
            
    if not target_id:
        print("❌ Could not find a microwave in your device map.")
        return

    print(f"🔎 Inspecting Microwave (ID: {target_id})...")
    
    url = f"https://api.smartthings.com/v1/devices/{target_id}"
    headers = {"Authorization": f"Bearer {token}"}
    
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        data = r.json()
        components = data.get("components", [])
        
        print(f"\n✅ FOUND {len(components)} COMPONENT(S):")
        for c in components:
            c_id = c.get("id")
            print(f"   🔹 Component ID: '{c_id}'")
            print(f"      Capabilities:")
            for cap in c.get("capabilities", []):
                print(f"        - {cap['id']}")
            print("-" * 30)
    else:
        print(f"❌ Error: {r.text}")

if __name__ == "__main__":
    inspect()

