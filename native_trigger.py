import os, time, wave, struct, math, subprocess, sys, socket

HOME="/data/data/com.termux/files/home"
WAKE="jarvis"
THRESHOLD=500

def get_text_from_wav(wav_path):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("127.0.0.1", 2700))
        s.sendall(wav_path.encode("utf-8"))
        data = s.recv(4096).decode("utf-8")
        s.close()
        return data.lower()
    except:
        return ""

def ensure_server():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("127.0.0.1", 2700))
        s.close()
    except:
        print("🚀 Booting Offline Speech Engine (Takes ~5 seconds)...")
        os.system(f"nohup proot-distro login debian -- python3 {HOME}/.shortcuts/vosk_server.py > /dev/null 2>&1 &")
        time.sleep(6)

def run():
    ensure_server()
    print("👂 JARVIS ONLINE (100% OFFLINE)")
    os.system("termux-wake-lock")
    
    while True:
        # FIX: Check for the flag in the EXACT folder the Logic Core puts it in!
        if os.path.exists(f"{HOME}/.shortcuts/shutdown.flag"):
            print("\n🛑 Shutting down.")
            os.remove(f"{HOME}/.shortcuts/shutdown.flag")
            return

        # Clean up old audio files so we don't hallucinate
        for f in ["buffer_raw.m4a", "buffer_clean.wav", "cmd.m4a", "cmd.wav"]:
            if os.path.exists(f"{HOME}/{f}"):
                os.remove(f"{HOME}/{f}")
        
        # Listen for the wake word
        os.system(f"termux-microphone-record -d -f {HOME}/buffer_raw.m4a -l 2.5 > /dev/null 2>&1")
        time.sleep(2.6)
        os.system("termux-microphone-record -q > /dev/null 2>&1")
        
        if not os.path.exists(f"{HOME}/buffer_raw.m4a"): continue
        
        subprocess.run(f"ffmpeg -y -i {HOME}/buffer_raw.m4a -ac 1 -ar 16000 {HOME}/buffer_clean.wav", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        vol=0
        if os.path.exists(f"{HOME}/buffer_clean.wav"):
            try:
                with wave.open(f"{HOME}/buffer_clean.wav",'rb') as f:
                    d=f.readframes(f.getnframes()); s=struct.unpack(f"<{len(d)//2}h",d); vol=math.sqrt(sum(x**2 for x in s)/len(s))
            except: vol=0
        
        print(f"Vol: {int(vol)}   ", end="\r")
        
        if vol > THRESHOLD:
            t = get_text_from_wav(f"{HOME}/buffer_clean.wav")
            
            if WAKE in t:
                quick_cmd = t.replace(WAKE, "").strip()
                if len(quick_cmd) > 3:
                    print(f"\n⚡ Fast Command Detected: '{quick_cmd}'")
                    os.system(f"play -n synth 0.1 sine 880 vol 0.5 > /dev/null 2>&1")
                    subprocess.run(["python", f"{HOME}/.shortcuts/ai_agent.py", quick_cmd])
                    continue
                    
                print("\n⏳ Waiting for your command...")
                os.system(f"play -n synth 0.1 sine 880 vol 0.5 > /dev/null 2>&1")
                
                time.sleep(0.5) 
                
                os.system(f"termux-microphone-record -d -f {HOME}/cmd.m4a -l 5.0 > /dev/null 2>&1")
                time.sleep(5.1)
                os.system("termux-microphone-record -q > /dev/null 2>&1")
                
                if not os.path.exists(f"{HOME}/cmd.m4a"):
                    print("   (Ignored: Android blocked the microphone)")
                    continue

                subprocess.run(f"ffmpeg -y -i {HOME}/cmd.m4a -ac 1 -ar 16000 {HOME}/cmd.wav", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                cmd_text = get_text_from_wav(f"{HOME}/cmd.wav")
                
                for bad_word in [WAKE, "surface", "service", "purpose", "travis"]:
                    cmd_text = cmd_text.replace(bad_word, "")
                cmd_text = cmd_text.strip()
                
                if len(cmd_text) > 2:
                    subprocess.run(["python", f"{HOME}/.shortcuts/ai_agent.py", cmd_text])
                else:
                    print("   (Ignored: No command heard after beep)")

if __name__ == "__main__": 
    run()
