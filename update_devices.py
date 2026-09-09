import os, json, requests

TOKEN_FILE = "/data/data/com.termux/files/home/.shortcuts/token.txt"
DEVICES_FILE = "/data/data/com.termux/files/home/my_devices.json"

def update_devices():
    if not os.path.exists(TOKEN_FILE):
        print("❌ Error: Could not find your SmartThings token.")
        return

    with open(TOKEN_FILE, "r") as f:
        token = f.read().strip()

    print("📡 Fetching devices from Samsung SmartThings...")
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        r = requests.get("https://api.smartthings.com/v1/devices", headers=headers, timeout=10)
        if r.status_code != 200:
            print(f"❌ Error {r.status_code}: {r.text}")
            return
            
        devices = r.json().get("items", [])
        my_devices = {}
        
        for d in devices:
            # Prefer the user-assigned label, fallback to default name
            name = d.get("label") or d.get("name") or "Unknown"
            my_devices[name.lower()] = {"id": d.get("deviceId")}
            print(f"   ✅ Found: {name}")

        with open(DEVICES_FILE, "w") as f:
            json.dump(my_devices, f, indent=4)
            
        print(f"\n🎉 Successfully mapped {len(my_devices)} devices to Jarvis's brain!")
        
    except Exception as e:
        print(f"❌ Network error: {e}")

if __name__ == "__main__":
    update_devices()
