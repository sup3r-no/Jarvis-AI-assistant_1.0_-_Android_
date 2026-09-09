import sys
import os
import subprocess

def main():
    if len(sys.argv) < 2:
        return

    # Lowercase everything so we don't miss "Flashlight" vs "flashlight"
    query = sys.argv[1].lower()

    # --- FLASHLIGHT ---
    if "flashlight" in query or "torch" in query:
        if "on" in query:
            os.system("termux-torch on")
            print("Flashlight ON")
        elif "off" in query:
            os.system("termux-torch off")
            print("Flashlight OFF")
        return

    # --- WIFI ---
    if "wifi" in query:
        if "on" in query or "enable" in query:
            os.system("termux-wifi-enable true")
            print("WiFi Enabled")
        elif "off" in query or "disable" in query:
            os.system("termux-wifi-enable false")
            print("WiFi Disabled")
        return

    # --- VOLUME ---
    if "volume" in query:
        if "up" in query or "max" in query or "loud" in query:
            os.system("termux-volume stream_music 15")
            print("Volume Max")
        elif "down" in query or "low" in query:
            os.system("termux-volume stream_music 5")
            print("Volume Low")
        return

    # --- BATTERY ---
    if "battery" in query:
        os.system("termux-battery-status | grep percentage")
        return

if __name__ == "__main__":
    main()

