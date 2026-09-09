import sys
import os
import json
import subprocess
import time

# --- CONFIG ---
SHORTCUTS_PATH = "/data/data/com.termux/files/home/.shortcuts"
if SHORTCUTS_PATH not in sys.path:
    sys.path.append(SHORTCUTS_PATH)

import logic_core

os.environ['TMPDIR'] = "/data/data/com.termux/files/home"

# --- 1. THE GUARDRAILS (Run First) ---
def check_hardware_patterns(query):
    """
    Strict Python Logic. No AI. No Hallucinations.
    Handles: Flashlight, Brightness, Volume, Time, Battery.
    """
    q = query.lower().strip()
    
    # FIX: Remove '%' so "50%" becomes "50" and passes isdigit() check
    q_clean = q.replace("%", " ")
    
    # --- FLASHLIGHT ---
    if "flashlight" in q or "torch" in q or "light" in q:
        if "on" in q: return '{"tool": "flashlight", "args": "on"}'
        if "off" in q: return '{"tool": "flashlight", "args": "off"}'

    # --- BRIGHTNESS ---
    if "brightness" in q or "screen" in q or "dim" in q:
        # Handle keywords for 100%
        if "max" in q or "full" in q or "all the way" in q:
            return '{"tool": "brightness", "args": "100"}'
        # Handle keywords for 0%
        if "min" in q or "lowest" in q:
            return '{"tool": "brightness", "args": "0"}'
            
        # Extract specific number (e.g., "50 percent", "50%")
        # We use q_clean here to handle the % symbol
        numbers = [int(s) for s in q_clean.split() if s.isdigit()]
        if numbers:
            return f'{{"tool": "brightness", "args": "{numbers[0]}"}}'

    # --- VOLUME ---
    if "volume" in q or "audio" in q or "sound" in q:
        if "max" in q or "full" in q:
            return '{"tool": "volume", "args": "100"}'
        if "mute" in q or "silent" in q:
            return '{"tool": "volume", "args": "0"}'
            
        # Use q_clean here too
        numbers = [int(s) for s in q_clean.split() if s.isdigit()]
        if numbers:
            return f'{{"tool": "volume", "args": "{numbers[0]}"}}'

    # --- UTILS ---
    if "battery" in q or "percentage" in q:
        return '{"tool": "battery", "args": ""}'
    if "time" in q or "clock" in q:
        return '{"tool": "time", "args": ""}'

    return None

# --- 2. THE BRAIN (Run Only if Guardrails Fail) ---
def consult_llama_chat(query):
    print("   🧠 Llama 3.2: Thinking...")
    # We strip the "Router" logic. If we are here, it IS a chat.
    SYSTEM_PROMPT = "You are Alfred, a witty British Butler. Keep responses under 2 sentences."
    try:
        cmd = ["ollama", "run", "llama3.2:3b", f"{SYSTEM_PROMPT} User: {query}"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return "I apologize sir, my thoughts are running slow today."
    except:
        return "System offline."

def process_query(query):
    print(f"   🎤 Input: {query}")

    # STEP 1: CHECK HARDWARE (Instant)
    # We do this BEFORE asking the AI.
    manual_command = check_hardware_patterns(query)
    
    if manual_command:
        print(f"   ⚡ Guardrail Triggered: {manual_command}")
        return logic_core.execute_logic(manual_command)

    # STEP 2: CHAT (Slow)
    # If no hardware keyword was found, assume it's conversation.
    return consult_llama_chat(query)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        user_query = " ".join(sys.argv[1:])
        final_response = process_query(user_query)
        os.system(f'python {SHORTCUTS_PATH}/google_speak.py "{final_response}"')

