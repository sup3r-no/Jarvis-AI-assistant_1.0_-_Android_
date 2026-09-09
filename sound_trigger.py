import os
import time
import math
import struct
import wave

# --- CONFIGURATION ---
THRESHOLD = 500  
NEXT_SCRIPT = "bash ~/.shortcuts/jarvis_guard.sh"
REC_FILE = "/data/data/com.termux/files/home/trigger_check.wav"

def get_loudness(file_path):
    try:
        if not os.path.exists(file_path): return 0
        w = wave.open(file_path, "rb")
        frames = w.readframes(w.getnframes())
        w.close()
        
        count = len(frames) / 2
        sum_squares = 0.0
        for i in range(0, len(frames), 2):
            sample = struct.unpack("<h", frames[i:i+2])[0]
            sum_squares += sample * sample
        
        if count == 0: return 0
        return math.sqrt(sum_squares / count)
    except:
        return 0

print(f"👂 LISTENING (Threshold: {THRESHOLD})")

while True:
    # 1. Record 1 second
    # We use -e wav to force the correct format
    os.system(f"termux-microphone-record -l 1 -f {REC_FILE} -e wav -r 16000 -c 1 > /dev/null 2>&1")
    
    # 2. Check Volume
    level = get_loudness(REC_FILE)
    print(f"Volume: {int(level)}")

    # 3. Trigger
    if level > THRESHOLD:
        print(f"🚨 TRIGGERED! (Level: {int(level)})")
        os.system("termux-volume stream-music 8")
        os.system(f"{NEXT_SCRIPT} &")
        print("⏳ Paused for 10s...")
        time.sleep(10)

    # Tiny pause to let the hardware reset
    time.sleep(0.5)

