import sys
import json
import subprocess
import os
import pychromecast
import time
import socket
import math

# --- CONFIGURATION ---
BSSID_MAP = {
    "c4:4f:d5:16:da:b7": "Living room speaker",
    "c6:4f:d5:0f:da:b6": "Noah's room DAD"
}

# --- PATHS ---
HOME = "/data/data/com.termux/files/home"
MODEL = f"{HOME}/piper/en_GB-vctk-medium.onnx"
CONFIG_FILE = f"{HOME}/voice_config.json"
TEMP_WAV = f"{HOME}/speech.wav"

def get_current_speaker_id():
    """Reads the saved speaker ID from config."""
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
            return config.get("speaker_id", 82)
    except:
        return 82 

def get_local_ip():
    """Finds the phone's IP to serve audio to the Google Home."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

def get_closest_speaker():
    """Checks if you're on home WiFi and returns the speaker name."""
    try:
        result = subprocess.check_output("termux-wifi-connectioninfo", shell=True)
        data = json.loads(result)
        return BSSID_MAP.get(data.get("bssid", "").lower(), None)
    except:
        return None

def speak_offline(text):
    target_speaker = get_closest_speaker()
    speaker_id = get_current_speaker_id()
    ip_addr = get_local_ip()

    # Calculate Speaking Duration (Blocking Buffer)
    word_count = len(text.split())
    # 2.2 words per second + 4s network buffer
    playback_duration = (word_count / 2.2) + 4.5

    try:
        # 1. GENERATE NEURAL VOICE (Piper in Debian)
        cmd = (
            f'echo "{text}" | proot-distro login debian -- '
            f'piper --model {MODEL} --speaker {speaker_id} --length_scale 1.15 --output_file /tmp/temp.wav'
        )
        subprocess.run(cmd, shell=True, stderr=subprocess.DEVNULL)
        
        # Pull file from Debian root to Termux home
        debian_root = "/data/data/com.termux/files/usr/var/lib/proot-distro/installed-rootfs/debian"
        os.system(f"cp {debian_root}/tmp/temp.wav {TEMP_WAV}")

        # 2. DECIDE OUTPUT ROUTE
        if target_speaker:
            print(f"   📡 Casting to {target_speaker}...")
            
            # Start local server to host the file
            server_proc = subprocess.Popen(
                ["python3", "-m", "http.server", "8000"], 
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=HOME
            )
            
            # CASTING LOGIC
            chromecasts, browser = pychromecast.get_listed_chromecasts(friendly_names=[target_speaker])
            if chromecasts:
                cast = chromecasts[0]
                cast.wait()
                mc = cast.media_controller
                local_url = f"http://{ip_addr}:8000/speech.wav"
                mc.play_media(local_url, 'audio/wav')
                mc.block_until_active()
                
                # CRITICAL: Wait here so the trigger script stays paused
                time.sleep(playback_duration)
                server_proc.terminate()
                return

        # 3. FALLBACK: MOBILE MODE
        # This part runs if you're not home or casting fails
        print("   📱 Mobile Mode: Using local speaker.")
        os.system(f"play {TEMP_WAV} > /dev/null 2>&1")

    except Exception as e:
        print(f"   Vocal Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Reconstruct the full string from arguments
        full_text = " ".join(sys.argv[1:])
        speak_offline(full_text)
