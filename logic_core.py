import os, sys, json, requests, subprocess, datetime

# --- CONFIG ---
TOKEN_FILE = "/data/data/com.termux/files/home/.shortcuts/token.txt"
DEVICES_FILE = "/data/data/com.termux/files/home/my_devices.json"
SHUTDOWN_FLAG = "/data/data/com.termux/files/home/.shortcuts/shutdown.flag"

def load_token():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f: return f.read().strip()
    return None

def load_devices():
    if os.path.exists(DEVICES_FILE):
        with open(DEVICES_FILE, "r") as f: return json.load(f)
    return {}

def speak(text):
    print(f"   🗣️ Saying: {text}")
    subprocess.run(["python", "/data/data/com.termux/files/home/.shortcuts/google_speak.py", text])

def get_battery_status():
    try:
        result = subprocess.check_output("termux-battery-status", shell=True)
        data = json.loads(result)
        return data.get("percentage", 0), data.get("status", "unknown") 
    except: return None, None

def get_calendar_events():
    return "I am unable to access your calendar. Please check Termux permissions."

def start_timer(seconds):
    try:
        sec = int(seconds)
        python_bin = "/data/data/com.termux/files/usr/bin/python"
        speak_script = "/data/data/com.termux/files/home/.shortcuts/google_speak.py"
        cmd = f"sleep {sec} && {python_bin} {speak_script} 'Your timer is finished, sir.'"
        subprocess.Popen(cmd, shell=True, start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return f"Timer set for {sec} seconds."
    except: return "I failed to set the timer."

def execute_smartthings(device_name, command, arg=None, silent=False):
    token = load_token()
    devices = load_devices()
    if not token or not devices:
        if not silent: speak("I am missing your Smart Things credentials, sir.")
        return
        
    target_id = None
    for name, data in devices.items():
        if device_name.lower() in name.lower():
            target_id = data["id"]
            break
            
    if not target_id:
        if not silent: speak(f"I cannot find a device named {device_name}.")
        return
        
    payload = {}
    success_msg = f"Okay, sir. I have sent the {command} command to the {device_name}."
    
    if "microwave" in device_name:
        if command == "light_on":
             payload = {"commands": [{"component": "hood", "capability": "samsungce.lamp", "command": "setBrightnessLevel", "arguments": ["high"]}]}
             success_msg = "Turning on the microwave light."
        elif command == "light_off":
             payload = {"commands": [{"component": "hood", "capability": "samsungce.lamp", "command": "setBrightnessLevel", "arguments": ["off"]}]}
             success_msg = "Turning off the microwave light."
        elif command in ["stop", "off"]:
             payload = {"commands": [{"component": "main", "capability": "execute", "command": "execute", "arguments": ["/sec/network/microwave/mode/stop"]}]}
             success_msg = "Stopping the microwave immediately, sir."
             
    elif "range" in device_name or "oven" in device_name:
        if command == "light_on":
             payload = {"commands": [{"component": "main", "capability": "samsungce.lamp", "command": "setBrightnessLevel", "arguments": ["high"]}]}
             success_msg = "Your range light is now on."
        elif command == "light_off":
             payload = {"commands": [{"component": "main", "capability": "samsungce.lamp", "command": "setBrightnessLevel", "arguments": ["off"]}]}
             success_msg = "Turning off the range light."
        elif command == "off":
            payload = {"commands": [{"component": "main", "capability": "switch", "command": "off"}]}
            success_msg = "Ensuring the range is turned off."
            
    elif command in ["on", "off"]:
        payload = {"commands": [{"component": "main", "capability": "switch", "command": command}]}
        success_msg = f"Turning the {device_name} {command}."
        
    url = f"https://api.smartthings.com/v1/devices/{target_id}/commands"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=5)
        if r.status_code == 200 and not silent: speak(success_msg)
    except:
        if not silent: speak("I am having trouble reaching the Samsung cloud.")

def execute_logic(json_cmd):
    try:
        data = json.loads(json_cmd)
        tool = data.get("tool")
        args = data.get("args")
        print(f"   [Logic Core] Tool: '{tool}' | Args: '{args}'")

        if tool == "system" and args == "shutdown":
            speak("Shutting down the system. Goodbye, sir.")
            with open(SHUTDOWN_FLAG, "w") as f: f.write("1")
            return
            
        if tool == "routine":
            if args == "radar_off":
                speak("Going off the radar, sir.")
                os.system('termux-notification -t "Jarvis System" -c "ActivateAnonymous" --id 9001')
            elif args == "radar_on":
                speak("Returning to the grid, sir.")
                os.system('termux-notification -t "Jarvis System" -c "DeactivateAnonymous" --id 9001')
            elif args == "sleep":
                speak("Preparing your environment for sleep, sir.")
                os.system('termux-notification -t "Jarvis System" -c "ActivateSleep" --id 9002')
            return

        if tool == "timer": speak(start_timer(args)); return
        if tool == "calendar": speak(get_calendar_events()); return
            
        if tool == "flashlight":
            if args == "on": os.system("termux-torch on"); speak("Activating the flashlight.")
            else: os.system("termux-torch off"); speak("Turning off the flashlight, sir.")
            return
            
        if tool == "brightness":
            val = int(int(args) * 2.55)
            os.system(f"termux-brightness {val}")
            speak(f"Adjusting screen brightness to {args} percent.")
            return
            
        if tool == "volume":
            os.system(f"termux-volume music {int(args)//7}") 
            speak(f"Setting the volume to {args}, sir.")
            return
            
        if tool == "battery":
            perc, status = get_battery_status()
            if perc is not None:
                if status == "CHARGING": speak(f"Your battery is currently charging at {perc} percent.")
                else: speak(f"You have {perc} percent battery remaining.")
            return
            
        if tool in ["fridge", "refrigerator", "range", "oven", "microwave"]:
            execute_smartthings(tool, args)
            return
            
        if tool == "time":
            now = datetime.datetime.now().strftime("%I:%M %p")
            speak(f"The current time is {now}.")
            return
            
    except Exception as e:
        speak("I encountered an internal error, sir.")
