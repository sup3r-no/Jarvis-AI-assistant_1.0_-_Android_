"Jarvis" Local-Based AI Assistant for Everything

Prerequisites:

Before executing the master installation command, you must grant Termux basic system permissions so the assistant can hear you and control your phone.

Download and install Termux and Termux:API from F-Droid (do not use the Google Play Store versions).

Open Termux and run termux-setup-storage.

Accept the Android prompt to grant file access.

Go to your Android settings and ensure Termux and Termux:API has all permissions enabled, including: Appear on top, Change system settings, and Install unknown apps.

Once permissions are granted, copy and paste the following master command block into Termux and press Enter. This single command will install all required Linux packages, Python libraries, the local AI brain, and the offline speech recognition model:

	pkg install -y python termux-api ffmpeg sox wget curl git proot-distro && pip install requests speechrecognition pychromecast && pkg update && pkg install -y ollama && ollama run llama3.2:1b & proot-distro login debian -- bash -c "apt update && apt install -y wget unzip python3-pip python3 && cd ~ && wget https://alphacephei.com/vosk/models/vosk-model-en-us-0.22-lgraph.zip && unzip vosk-model-en-us-0.22-lgraph.zip"

Per-User Customization

The system relies on hardcoded paths, personal tokens, and unique network addresses. You must customize these specific variables for your own home:

Authentication Token: Generate a personal access token at https://account.smartthings.com/tokens (with full device permissions) or a Home Assistant Long-Lived Access Token at the bottom of your user profile page in the Home Assistant interface.

Ensure you have made a note of the devices' information that you wish to include in the system, such as the IP address(es) of the google speaker(s) you wish to use as the speaker(s) for the assistant (when nearby) or the wifi MAC address(es) of your router(s).

Copy and paste this entire master script block into Termux and press Enter:

	cat << 'EOF' > ~/.shortcuts/interactive_setup.py
	import os
	import json
	import time
	import re
	import subprocess
	import wave
	import struct
	import math
	
	HOME = "/data/data/com.termux/files/home"
	SHORTCUTS = f"{HOME}/.shortcuts"
	TOKEN_FILE = f"{SHORTCUTS}/token.txt"
	DEVICES_FILE = f"{HOME}/my_devices.json"
	GOOGLE_SPEAK_FILE = f"{SHORTCUTS}/google_speak.py"
	TRIGGER_FILE = f"{SHORTCUTS}/native_trigger.py"
	
	def clear():
	    os.system("clear")
	
	def replace_in_file(filepath, pattern, replacement):
	    if not os.path.exists(filepath): return
	    with open(filepath, 'r') as file:
	        content = file.read()
	    content = re.sub(pattern, replacement, content, flags=re.DOTALL)
	    with open(filepath, 'w') as file:
	        file.write(content)
	
	clear()
	print("=== JARVIS INTERACTIVE SETUP WIZARD ===\n")
	
	# --- 1. SMARTTHINGS TOKEN ---
	print("--- Step 1: Authentication ---")
	token = input("Paste your SmartThings Personal Access Token: ").strip()
	with open(TOKEN_FILE, "w") as f:
	    f.write(token)
	print("✅ Token saved to token.txt\n")
	time.sleep(1)
	
	# --- 2. WIFI & SPEAKER ROUTING ---
	print("--- Step 2: Speaker Network Mapping ---")
	bssid_map = {}
	while True:
	    print("\nScanning current Wi-Fi BSSID...")
	    try:
	        wifi_info = json.loads(subprocess.check_output("termux-wifi-connectioninfo", shell=True))
	        current_bssid = wifi_info.get("bssid", "").lower()
	        if current_bssid:
	            print(f"📡 Connected BSSID: {current_bssid}")
	        else:
	            print("⚠️ Could not detect BSSID. Ensure location permissions are granted.")
	    except:
	        current_bssid = input("Manual entry (or leave blank to skip): ").strip().lower()
	
	    if current_bssid:
	        while True:
	            add_speaker = input(f"Do you want to map a Google Cast speaker to {current_bssid}? (y/n): ").strip().lower()
	            if add_speaker != 'y': break
	            
	            print("Scanning for local Chromecast devices (Please wait)...")
	            try:
	                import pychromecast
	                casts, browser = pychromecast.get_listed_chromecasts(friendly_names=None)
	                if casts:
	                    for i, cast in enumerate(casts):
	                        print(f"  [{i+1}] {cast.name}")
	                    choice = input("Enter the number of the speaker: ").strip()
	                    if choice.isdigit() and 1 <= int(choice) <= len(casts):
	                        bssid_map[current_bssid] = casts[int(choice)-1].name
	                        print(f"✅ Mapped {current_bssid} -> {bssid_map[current_bssid]}")
	                    pychromecast.discovery.stop_discovery(browser)
	                else:
	                    print("❌ No speakers found on this network.")
	            except ImportError:
	                print("⚠️ pychromecast not installed. Skipping auto-discovery.")
	                name = input("Enter the exact friendly name of your speaker: ").strip()
	                bssid_map[current_bssid] = name
	                
	            if input("Map another speaker to this same AP? (y/n): ").strip().lower() != 'y':
	                break
	
	    if input("\nDo you want to map a different Wi-Fi Access Point? (y/n): ").strip().lower() == 'y':
	        print("\nTurning off Wi-Fi to force disconnection...")
	        os.system("termux-wifi-enable false")
	        input("Walk to the new router/AP, then press ENTER to reconnect...")
	        os.system("termux-wifi-enable true")
	        print("Waiting for network connection (10 seconds)...")
	        time.sleep(10)
	    else:
	        break
	
	if bssid_map:
	    map_str = "BSSID_MAP = " + json.dumps(bssid_map, indent=4)
	    replace_in_file(GOOGLE_SPEAK_FILE, r"BSSID_MAP\s*=\s*\{.*?\}", map_str)
	    print("✅ google_speak.py updated with your speaker routes.\n")
	time.sleep(1)
	
	# --- 3. WAKE WORD & SENSITIVITY ---
	clear()
	print("--- Step 3: Trigger Sensitivity & Wake Word ---")
	wake_word = input("What would you like your wake word to be? (default: jarvis): ").strip().lower()
	if not wake_word: wake_word = "jarvis"
	
	while True:
	    threshold = input("Enter microphone sensitivity threshold (default: 500. Lower is more sensitive): ").strip()
	    if not threshold.isdigit(): threshold = "500"
	    threshold = int(threshold)
	    
	    print("\nLet's test it. I will listen for 3 seconds.")
	    print("Say your wake word loudly...")
	    time.sleep(1)
	    
	    os.system(f"termux-microphone-record -d -f {HOME}/test_mic.m4a -l 3.0 > /dev/null 2>&1")
	    time.sleep(3.5)
	    os.system("termux-microphone-record -q > /dev/null 2>&1")
	    os.system(f"ffmpeg -y -i {HOME}/test_mic.m4a -ac 1 -ar 16000 {HOME}/test_mic.wav > /dev/null 2>&1")
	    
	    vol = 0
	    try:
	        with wave.open(f"{HOME}/test_mic.wav", 'rb') as f:
	            d = f.readframes(f.getnframes())
	            s = struct.unpack(f"<{len(d)//2}h", d)
	            vol = math.sqrt(sum(x**2 for x in s)/len(s))
	    except Exception: pass
	    
	    print(f"🎤 Recorded Volume: {int(vol)}")
	    if vol >= threshold:
	        print(f"✅ Success! {int(vol)} is higher than your threshold of {threshold}.")
	    else:
	        print(f"❌ Failed. {int(vol)} is too quiet to pass the threshold of {threshold}.")
	    
	    if input("\nWould you like to change your sensitivity threshold? (y/n): ").strip().lower() != 'y':
	        break
	
	replace_in_file(TRIGGER_FILE, r'WAKE=".*?"', f'WAKE="{wake_word}"')
	replace_in_file(TRIGGER_FILE, r'THRESHOLD=\d+', f'THRESHOLD={threshold}')
	print(f"✅ native_trigger.py updated. (Wake: {wake_word}, Threshold: {threshold})\n")
	time.sleep(1)
	
	# --- 4. DEVICE NICKNAMES ---
	clear()
	print("--- Step 4: Device Nicknaming ---")
	if os.path.exists(DEVICES_FILE):
	    with open(DEVICES_FILE, "r") as f:
	        devices = json.load(f)
	    
	    new_devices = {}
	    print("I will list your current devices. Enter a new nickname, or press ENTER to keep the current name.")
	    for current_name, data in devices.items():
	        new_name = input(f"Device [{current_name}]: ").strip().lower()
	        if new_name:
	            new_devices[new_name] = data
	            print(f"   Mapped to '{new_name}'")
	        else:
	            new_devices[current_name] = data
	            
	    with open(DEVICES_FILE, "w") as f:
	        json.dump(new_devices, f, indent=4)
	    print("✅ my_devices.json updated with your custom nicknames.\n")
	else:
	    print("⚠️ my_devices.json not found. Run your mapping script first to assign nicknames.\n")
	
	print("=== SETUP COMPLETE! ===")
	print(f"To start your assistant, run: python {TRIGGER_FILE}")
	EOF
	
	python ~/.shortcuts/interactive_setup.py

This will generate and automatically launch an interactive Python setup wizard (interactive_setup.py) that walks through your token, speaker routing, Wi-Fi AP scanning, trigger sensitivity, live wake-word testing, and appliance nicknaming. It reads and edits token.txt, google_speak.py, native_trigger.py, and my_devices.json directly based on your answers.

The previous interactive wizard configured your core settings, but it did not execute the temporary hardware discovery scripts.

Copy and paste this command block into Termux and press enter:

	cat << 'EOF' > ~/.shortcuts/discovery_wizard.py
	import os
	import subprocess
	import time
	
	HOME = "/data/data/com.termux/files/home"
	SHORTCUTS = f"{HOME}/.shortcuts"
	DEVICES_FILE = f"{HOME}/my_devices.json"
	
	def clear():
	    os.system("clear")
	
	def run_script(script_name):
	    script_path = f"{SHORTCUTS}/{script_name}"
	    if os.path.exists(script_path):
	        os.system(f"python {script_path}")
	    else:
	        print(f"⚠️ {script_name} not found. Skipping...")
	
	clear()
	print("=== JARVIS HARDWARE DISCOVERY WIZARD ===\n")
	
	# --- 1. SCAN LOCAL NETWORK ---
	print("--- Step 1: Scan for Samsung Appliances ---")
	if input("Would you like to scan your Wi-Fi network for appliance IPs? (y/n): ").strip().lower() == 'y':
	    run_script("find_samsung.py")
	print("\n")
	
	# --- 2. PROBE ENDPOINTS ---
	print("--- Step 2: Probe SSL Endpoints ---")
	target_ip = input("Enter the IP address of the appliance you want to probe (e.g., 10.0.0.178) or press ENTER to skip: ").strip()
	if target_ip:
	    probe_path = f"{SHORTCUTS}/probe_device.py"
	    if os.path.exists(probe_path):
	        # Update the target IP inside the probe script
	        with open(probe_path, 'r') as file:
	            content = file.read()
	        import re
	        content = re.sub(r'TARGET_IP\s*=\s*["\'].*?["\']', f'TARGET_IP = "{target_ip}"', content)
	        with open(probe_path, 'w') as file:
	            file.write(content)
	        
	        print(f"\nProbing {target_ip} on port 8888...")
	        os.system(f"python {probe_path}")
	    else:
	        print("⚠️ probe_device.py not found.")
	print("\n")
	
	# --- 3. SYNC CLOUD DEVICES ---
	print("--- Step 3: Sync SmartThings / Home Assistant ---")
	if input("Would you like to pull your unique device UUIDs and capabilities from the cloud? (y/n): ").strip().lower() == 'y':
	    # update_devices.py pulls the entities and saves them to my_devices.json
	    run_script("update_devices.py") 
	print("\n")
	
	# --- 4. INSPECT COMPONENTS ---
	print("--- Step 4: Inspect Component Labels ---")
	if input("Do you need to identify exact internal API names (e.g., 'main' or 'hood') for a specific appliance? (y/n): ").strip().lower() == 'y':
	    run_script("inspect_components.py")
	print("\n")
	
	# --- 5. CLEANUP ---
	clear()
	print("--- Step 5: Temporary File Cleanup ---")
	if os.path.exists(DEVICES_FILE):
	    print("✅ my_devices.json is successfully mapped.")
	    if input("Would you like to delete the temporary discovery scripts and audio buffers now? (y/n): ").strip().lower() == 'y':
	        for script in ["find_samsung.py", "probe_device.py", "smartthings_sync.py", "inspect_components.py"]:
	            path = f"{SHORTCUTS}/{script}"
	            if os.path.exists(path):
	                os.remove(path)
	                print(f"🗑️ Deleted {script}")
	                
	        for buffer_file in ["stream_session.wav", "buffer_raw.m4a", "buffer_clean.wav", "command_raw.m4a", "command_clean.wav"]:
	            path = f"{HOME}/{buffer_file}"
	            if os.path.exists(path):
	                os.remove(path)
	                print(f"🗑️ Deleted {buffer_file}")
	                
	        print("\n✅ Cleanup complete. Your Termux environment is optimized.")
	else:
	    print("⚠️ my_devices.json not detected. Keeping temporary files for further troubleshooting.")
	
	print("\n=== HARDWARE DISCOVERY COMPLETE ===")
	EOF
	
	python ~/.shortcuts/discovery_wizard.py

It will generate and run discovery_wizard.py, which systematically executes your temporary scripts, uses your answers to update targeted IPs and internal labels, and automatically deletes the temporary files once your home is successfully mapped.

This ensures that scripts like update_devices.py execute and successfully construct your my_devices.json file, while safely scrubbing the leftover .m4a and .wav buffers that can cause AI hallucinations if left behind.

While the previous wizard handles the setup, it is best to run a dedicated, brute-force cleanup command to ensure absolutely no dead weight is left on your device.

The offline speech engines and raw audio streams generate massive diagnostic files and temporary buffers that will drain your storage or cause AI hallucinations if they are accidentally read during a wake-word loop.

Copy and paste this single command block into Termux and press Enter. This will correctly position the extracted brain, finalize the setup, and immediately execute a deep clean of all setup archives, diagnostic scripts, and audio buffers without touching your core "Jarvis" Local-Based AI Assistant for Everything system files:

	echo "🧠 Linking Offline Brain..." && mv ~/vosk-model-en-us-0.22-lgraph ~/.shortcuts/vosk-model 2>/dev/null || mv ~/.shortcuts/vosk-model-en-us-0.22-lgraph ~/.shortcuts/vosk-model 2>/dev/null && echo "🧹 Commencing Deep Clean..." && rm -f ~/.shortcuts/find_samsung.py ~/.shortcuts/probe_device.py ~/.shortcuts/smartthings_sync.py ~/.shortcuts/inspect_components.py ~/.shortcuts/scan_home.py ~/vosk-model-en-us-0.22.zip ~/vosk-model-en-us-0.22-lgraph.zip ~/.shortcuts/vosk-model-en-us-0.22.zip ~/.shortcuts/vosk-model-en-us-0.22-lgraph.zip ~/buffer_raw.m4a ~/buffer_clean.wav ~/command_raw.m4a ~/command_clean.wav ~/cmd.m4a ~/cmd.wav ~/stream_session.wav ~/speech.wav && rm -rf ~/.shortcuts/vosk-model-en-us-0.22 ~/vosk-model-en-us-0.22 && echo "✅ Brain Linked & System Cleaned!"
What This Command Does for You:

Activates the Brain: It finds the extracted vosk-model-en-us-0.22-lgraph folder and renames it simply to vosk-model. This satisfies the MODEL_PATH requirement in your server script so Jarvis can actually hear you offline.

Destroys the Archives: It deletes the vosk-model-en-us-0.22-lgraph.zip setup archive (and the 1.8GB model archive if it was left behind) to free up your phone's storage now that the brain is successfully extracted.

Scrubs the Environment: It permanently deletes all temporary .m4a and .wav audio caches, plus the initial network discovery scripts (find_samsung.py, probe_device.py, etc.), leaving only your core runtime files intact.
