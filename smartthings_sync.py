import requests
import json

# PASTE YOUR TOKEN HERE
TOKEN = "d94c3f5f-0c5f-44ee-a394-9d2823c5bc56"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

def get_devices():
    print("☁️ Connecting to SmartThings Cloud...")
    url = "https://api.smartthings.com/v1/devices"
    try:
        r = requests.get(url, headers=HEADERS)
        if r.status_code == 200:
            devices = r.json().get('items', [])
            print(f"✅ Found {len(devices)} devices.\n")
            
            clean_list = {}
            
            for d in devices:
                name = d.get('label') or d.get('name')
                d_id = d.get('deviceId')
                components = d.get('components', [])
                
                print(f"   📱 {name}")
                print(f"      ID: {d_id}")
                
                # Check capabilities (What can it do?)
                caps = []
                for c in components:
                    for cap in c.get('capabilities', []):
                        caps.append(cap.get('id'))
                
                print(f"      Caps: {', '.join(caps[:4])}...") # Show first 4
                
                # Save to our offline map
                clean_list[name.lower()] = {
                    "id": d_id,
                    "capabilities": caps
                }
                print("-" * 40)

            # Save to file
            with open("/data/data/com.termux/files/home/my_devices.json", "w") as f:
                json.dump(clean_list, f, indent=2)
            print("\n💾 Device Map saved to '~/my_devices.json'")
            
        else:
            print(f"❌ Error: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"❌ Connection Failed: {e}")

if __name__ == "__main__":
    get_devices()

