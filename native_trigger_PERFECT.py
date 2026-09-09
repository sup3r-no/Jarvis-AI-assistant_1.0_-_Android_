import os
import time
import wave
import struct
import math
import speech_recognition as sr
import subprocess
import sys

# --- CONFIG ---
THRESHOLD = 500
WAKE_WORD = "jarvis"
AGENT_SCRIPT = "/data/data/com.termux/files/home/.shortcuts/ai_agent.py"
HOME_DIR = "/data/data/com.termux/files/home"

# FILES
RAW_FILE = f"{HOME_DIR}/buffer_raw.m4a"
WAV_FILE = f"{HOME_DIR}/buffer_clean.wav"
CMD_FILE_RAW = f"{HOME_DIR}/command_raw.m4a"
CMD_FILE_WAV = f"{HOME_DIR}/command_clean.wav"
FOLLOW_UP_WINDOW = 6

HARDWARE_TRIGGERS = ["flashlight", "torch", "light", "brightness", "volume"]

START_TIME = time.time()

def log(msg, end="\n"):
    elapsed = time.time() - START_TIME
    print(f"[{elapsed:.2f}s] {msg}", end=end, flush=True)

def play_beep():
    os.system("play -n synth 0.1 sine 880 vol 0.5 > /dev/null 2>&1")

def wait_for_file_start(filename):
    start_wait = time.time()
    while not os.path.exists(filename):
        time.sleep(0.05)
        if time.time() - start_wait > 4.0: return False
    time.sleep(0.5)
    return True

def convert_audio(raw, clean):
    if os.path.exists(raw):
        subprocess.run(f"ffmpeg -y -i {raw} -ac 1 -ar 44100 {clean}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def get_audio_volume(filename):
    try:
        if not os.path.exists(filename): return 0
        with wave.open(filename, 'rb') as wf:
            frames = wf.readframes(wf.getnframes())
            if not frames: return 0
            samples = struct.unpack(f"<{len(frames)//2}h", frames)
            sum_squares = sum(s**2 for s in samples)
            return math.sqrt(sum_squares / len(samples))
    except: return 0

def transcribe_file(filename):
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(filename) as source:
            return recognizer.recognize_google(recognizer.record(source)).lower()
    except: return ""

def execute_command_logic(cmd):
    """
    Executes the command and returns TRUE if we need a follow-up.
    """
    is_hardware = False
    
    # Check triggers
    if any(hw in cmd for hw in HARDWARE_TRIGGERS):
        if "off" in cmd:
            log("🔌 Hardware: OFF (No follow-up)")
            is_hardware = False
        else:
            log("🔌 Hardware: ON (Triggering follow-up)")
            is_hardware = True
    
    log(f"🧠 Executing: {cmd}")
    os.system(f'python {AGENT_SCRIPT} "{cmd}"')
    
    return is_hardware

def run_listening_session(duration=5):
    """
    The Active Listening Block.
    Used for the first command AND the follow-up.
    """
    log("🎙️ LISTENING...")
    if os.path.exists(CMD_FILE_RAW): os.remove(CMD_FILE_RAW)
    
    # Start Record
    os.system(f"termux-microphone-record -d -f {CMD_FILE_RAW} -l {duration} > /dev/null 2>&1")
    
    # Wait for file -> Beep
    if wait_for_file_start(CMD_FILE_RAW):
        play_beep()
        # Sleep for duration to let it record
        time.sleep(duration)
    
    # Stop & Convert
    os.system("termux-microphone-record -q > /dev/null 2>&1")
    convert_audio(CMD_FILE_RAW, CMD_FILE_WAV)
    
    return transcribe_file(CMD_FILE_WAV)

def run_sentry_mode():
    """
    The Passive Sentry Block.
    Records short chunks to check for Wake Word.
    """
    if os.path.exists(RAW_FILE): os.remove(RAW_FILE)
    
    # Record 2.0s
    os.system(f"termux-microphone-record -d -f {RAW_FILE} -l 2.0 > /dev/null 2>&1")
    time.sleep(2.5) # Wait for finish
    
    # Stop & Convert
    os.system("termux-microphone-record -q > /dev/null 2>&1")
    convert_audio(RAW_FILE, WAV_FILE)
    
    return get_audio_volume(WAV_FILE)

def run_listener():
    log(f"👂 JARVIS RESTORED (Threshold: {THRESHOLD})")
    
    # Clean start
    os.system("termux-microphone-record -q > /dev/null 2>&1")

    try:
        while True:
            # 1. RUN SENTRY
            rms = run_sentry_mode()
            log(f"📊 Sentry | Vol: {int(rms)}   ", end="\r")

            if rms > THRESHOLD:
                log(f"\n🚨 Noise Detected ({int(rms)})!")
                text = transcribe_file(WAV_FILE)
                
                if not text:
                     log("   (Ignored: No speech detected)")
                     continue
                     
                log(f"🔎 Checked: '{text}'")
                
                if WAKE_WORD in text:
                    log("✅ Wake Word Accepted.")
                    
                    # 2. RUN COMMAND LISTENER (First Pass)
                    cmd = run_listening_session(5)
                    
                    if cmd:
                        # Execute and check if we need follow-up
                        needs_follow_up = execute_command_logic(cmd)
                        
                        # 3. THE FOLLOW-UP LOOP
                        # This runs the EXACT SAME code as the command listener
                        while needs_follow_up:
                            log("👂 Follow-up...")
                            
                            # Run Listener Again (Recycle Function)
                            cmd = run_listening_session(FOLLOW_UP_WINDOW)
                            
                            if cmd:
                                needs_follow_up = execute_command_logic(cmd)
                            else:
                                log("   (Silence - Ending Follow-up)")
                                needs_follow_up = False
                    
                    log("\n👂 Returning to Sentry...")

    except KeyboardInterrupt:
        log("\n🛑 Shutting down.")
        os.system("termux-microphone-record -q")
        exit()

if __name__ == "__main__":
    os.system("termux-wake-lock")
    os.system("termux-microphone-record -q > /dev/null 2>&1")
    run_listener()

