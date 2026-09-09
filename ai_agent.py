import sys, os, json, subprocess, re, requests

# --- CONFIG ---
SHORTCUTS_PATH = "/data/data/com.termux/files/home/.shortcuts"
if SHORTCUTS_PATH not in sys.path:
    sys.path.append(SHORTCUTS_PATH)

import logic_core
os.environ['TMPDIR'] = "/data/data/com.termux/files/home"
SPEECH_SCRIPT = f"{SHORTCUTS_PATH}/google_speak.py"

def check_hardware_patterns(query):
    q = query.lower().strip()
    q_num = q.replace("one", "1").replace("two", "2").replace("three", "3").replace("four", "4").replace("five", "5").replace("ten", "10").replace("a minute", "1 minute").replace("an hour", "1 hour")
    
    # --- 1. SYSTEM CONTROL ---
    if "shut down" in q or "shutdown" in q or "stop listening" in q:
        return '{"tool": "system", "args": "shutdown"}'

    # --- 2. TIMER ---
    if "timer" in q or "alarm" in q:
        min_match = re.search(r'(\d+)\s*min', q_num)
        sec_match = re.search(r'(\d+)\s*sec', q_num)
        hr_match = re.search(r'(\d+)\s*hour', q_num)
        total_seconds = 0
        if hr_match: total_seconds += int(hr_match.group(1)) * 3600
        if min_match: total_seconds += int(min_match.group(1)) * 60
        if sec_match: total_seconds += int(sec_match.group(1))
        if total_seconds == 0 and "set" in q: total_seconds = 300 
        if total_seconds > 0: return f'{{"tool": "timer", "args": "{total_seconds}"}}'

    # --- 3. MODES & ROUTINES ---
    if "off the radar" in q:
        return '{"tool": "routine", "args": "radar_off"}'
    if "on the radar" in q:
        return '{"tool": "routine", "args": "radar_on"}'
    if "sleep mode" in q or "bedtime" in q:
        return '{"tool": "routine", "args": "sleep"}'

    # --- 4. CALENDAR ---
    if "calendar" in q or "schedule" in q or "events" in q or "appointment" in q:
        if "read" in q or "tell" in q or "what" in q or "check" in q or "have" in q:
            return '{"tool": "calendar", "args": "read"}'

    # --- 5. TRANSLATOR ---
    if "translate" in q or "translation" in q or "translator" in q:
        if "mode" in q or "enable" in q or "start" in q:
            return '{"tool": "translator", "args": "start"}'

    # --- 6. APPLIANCES ---
    if "range" in q or "oven" in q or "stove" in q:
        if "light" in q: return '{"tool": "range", "args": "light_on"}' if "on" in q else '{"tool": "range", "args": "light_off"}'
        if "off" in q: return '{"tool": "range", "args": "off"}'
        if "on" in q: return '{"tool": "range", "args": "on"}'

    if "microwave" in q:
        if "light" in q: return '{"tool": "microwave", "args": "light_on"}' if "on" in q else '{"tool": "microwave", "args": "light_off"}'
        if "stop" in q or "off" in q: return '{"tool": "microwave", "args": "off"}'

    if "fridge" in q or "refrigerator" in q:
        return '{"tool": "fridge", "args": "check"}'

    # --- 7. HARDWARE TOOLS ---
    if "flashlight" in q or "torch" in q:
        if "on" in q: return '{"tool": "flashlight", "args": "on"}'
        if "off" in q: return '{"tool": "flashlight", "args": "off"}'

    if "brightness" in q or "screen" in q or "dim" in q:
        if "max" in q or "full" in q: return '{"tool": "brightness", "args": "100"}'
        if "min" in q or "lowest" in q: return '{"tool": "brightness", "args": "0"}'
        numbers = [int(s) for s in q_num.split() if s.isdigit()]
        if numbers: return f'{{"tool": "brightness", "args": "{numbers[0]}"}}'

    if "volume" in q or "audio" in q:
        if "max" in q: return '{"tool": "volume", "args": "100"}'
        if "mute" in q: return '{"tool": "volume", "args": "0"}'
        numbers = [int(s) for s in q_num.split() if s.isdigit()]
        if numbers: return f'{{"tool": "volume", "args": "{numbers[0]}"}}'

    if "battery" in q: return '{"tool": "battery", "args": ""}'

    # --- 8. CLOCK (Strict) ---
    if "what time" in q or "current time" in q or "clock" in q:
        return '{"tool": "time", "args": ""}'

    return None

def consult_llama_chat(query):
    print("   🧠 Llama 3.2 (1B): Thinking...")
    try:
        prompt = f"You are Alfred, a witty British Butler. Keep responses under 2 sentences. User: {query}"
        payload = {"model": "llama3.2:1b", "prompt": prompt, "stream": False}
        r = requests.post("http://127.0.0.1:11434/api/generate", json=payload, timeout=30)
        if r.status_code == 200:
            return r.json().get("response", "").strip()
        return "I seem to have lost my train of thought, sir."
    except:
        return "System offline. I cannot reach my neural processor."

def process_query(query):
    print(f"   🎤 Input: {query}")
    manual_command = check_hardware_patterns(query)
    if manual_command:
        print(f"   ⚡ Guardrail Triggered: {manual_command}")
        logic_core.execute_logic(manual_command)
        return
    response = consult_llama_chat(query)
    if response: subprocess.run(["python", SPEECH_SCRIPT, response])

if __name__ == "__main__":
    if len(sys.argv) > 1: process_query(" ".join(sys.argv[1:]))
