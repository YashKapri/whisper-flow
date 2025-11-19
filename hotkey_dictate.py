"""
hotkey_dictate.py
- Hold HOTKEY to record, release to transcribe.
- Two output modes:
    * typing into active window (pyautogui)
    * put transcript into clipboard and paste (recommended for long text)
- Translation support: when translation=True it uses Whisper's task='translate'
- System tray icon: right-click to Quit / Toggle mode
"""
import os
import sys
import time
import threading
import tempfile
from pathlib import Path
import argparse
import json

import sounddevice as sd
import soundfile as sf
import numpy as np
import whisper
import keyboard
import pyautogui
import pyperclip

# Optional: pystray for system tray
try:
    import pystray
    from PIL import Image, ImageDraw
    TRAY_AVAILABLE = True
except Exception:
    TRAY_AVAILABLE = False

# --------- SETTINGS (customize) ----------
WHISPER_MODEL_NAME = "small"
SAMPLE_RATE = 16000
HOTKEY = "ctrl+alt+v"        # hold to record, release to transcribe
OUTPUT_MODE = "paste"        # "type" or "paste" (paste uses clipboard then sends Ctrl+V)
TRANSLATE_BY_DEFAULT = False # True => use task='translate' (Hindi->English)
TEMP_DIR = Path(tempfile.gettempdir()) / "whisper_flow_pro"
TEMP_DIR.mkdir(parents=True, exist_ok=True)
# -----------------------------------------

print("[*] Loading Whisper model:", WHISPER_MODEL_NAME)
model = whisper.load_model(WHISPER_MODEL_NAME)
print("[*] Model loaded.")

# state
recording = False
frames = []
stream = None
lock = threading.Lock()
hotkey_pressed = False

# runtime-config that can be toggled from tray/menu
runtime = {
    "output_mode": OUTPUT_MODE,         # "type" or "paste"
    "translate": TRANSLATE_BY_DEFAULT,  # whether to return translated (English) text
    "hotkey": HOTKEY
}

# audio callback
def audio_callback(indata, frames_count, time_info, status):
    if status:
        print("[audio status]:", status)
    with lock:
        frames.append(indata.copy())

def start_recording():
    global recording, frames, stream
    with lock:
        frames = []
    recording = True
    stream = sd.InputStream(samplerate=SAMPLE_RATE, channels=1, callback=audio_callback)
    stream.start()
    print("[*] Recording started... (release hotkey to stop)")

def stop_recording_and_process():
    global recording, stream
    recording = False
    if stream:
        try:
            stream.stop()
            stream.close()
        except Exception:
            pass

    with lock:
        if not frames:
            print("[!] No audio recorded.")
            return
        audio_np = np.concatenate(frames, axis=0)

    ts = int(time.time())
    wav_path = TEMP_DIR / f"dictation_{ts}.wav"
    sf.write(str(wav_path), audio_np, SAMPLE_RATE)
    print(f"[*] Saved temp audio: {wav_path}")

    # Transcribe or translate
    print("[*] Transcribing (translate=%s)..." % runtime["translate"])
    try:
        if runtime["translate"]:
            result = model.transcribe(str(wav_path), task="translate")
        else:
            result = model.transcribe(str(wav_path))  # auto language detection
        text = result.get("text", "").strip()
        lang = result.get("language", None)
        print(f"[*] Detected language: {lang}  chars: {len(text)}")
    except Exception as e:
        print("[!] Error transcribing:", e)
        text = ""
    finally:
        try:
            wav_path.unlink(missing_ok=True)
        except Exception:
            pass

    if not text:
        print("[!] Empty transcript.")
        return

    # Output: paste via clipboard (fast) or type (slower)
    if runtime["output_mode"] == "paste":
        try:
            pyperclip.copy(text)
            # paste into active window
            # On Windows, send ctrl+v
            pyautogui.hotkey('ctrl', 'v')
            print("[*] Pasted transcript to active window (clipboard).")
        except Exception as e:
            print("[!] Clipboard/paste failed, falling back to typing. Error:", e)
            _type_text(text)
    else:
        _type_text(text)

def _type_text(text):
    # type in chunks to avoid very long keystroke sequences
    CHUNK = 300
    for i in range(0, len(text), CHUNK):
        chunk = text[i:i+CHUNK]
        pyautogui.write(chunk, interval=0.01)
    print("[*] Done typing.")

# hotkey handlers
def on_hotkey_press():
    global hotkey_pressed
    if hotkey_pressed:
        return
    hotkey_pressed = True
    start_recording()

def on_hotkey_release():
    global hotkey_pressed
    if not hotkey_pressed:
        return
    hotkey_pressed = False
    threading.Thread(target=stop_recording_and_process, daemon=True).start()

# tray icon helpers (if pystray available)
tray_icon = None
def create_image():
    # small 64x64 icon
    img = Image.new('RGB', (64, 64), color=(30,30,30))
    d = ImageDraw.Draw(img)
    d.ellipse((8,8,56,56), fill=(230,70,70))
    d.text((22,20), "🎤", fill=(255,255,255))
    return img

def tray_toggle_mode(icon=None, item=None):
    # toggle output mode
    runtime["output_mode"] = "type" if runtime["output_mode"] == "paste" else "paste"
    print("[*] Output mode set to", runtime["output_mode"])

def tray_toggle_translate(icon=None, item=None):
    runtime["translate"] = not runtime["translate"]
    print("[*] Translate set to", runtime["translate"])

def tray_quit(icon=None, item=None):
    print("[*] Quitting...")
    try:
        icon.stop()
    except Exception:
        pass
    os._exit(0)

def run_tray():
    global tray_icon
    if not TRAY_AVAILABLE:
        print("[!] pystray not available; run `pip install pystray pillow` to enable system tray.")
        return
    image = create_image()
    menu = pystray.Menu(
        pystray.MenuItem(lambda item: f"Mode: {runtime['output_mode']}", tray_toggle_mode),
        pystray.MenuItem(lambda item: f"Translate: {runtime['translate']}", tray_toggle_translate),
        pystray.MenuItem('Quit', tray_quit)
    )
    tray_icon = pystray.Icon("WhisperDict", image, "Whisper Dictate", menu)
    tray_icon.run()

def main():
    print(f"[*] Hotkey dictation ready. Hold {runtime['hotkey']} to talk, release to transcribe.")
    print(f"[*] Current mode: {runtime['output_mode']}  translate:{runtime['translate']}")
    print("[*] If hotkey doesn't work, try running this terminal as Administrator.")

    # Register hotkey
    keyboard.add_hotkey(runtime["hotkey"], on_hotkey_press, suppress=False, trigger_on_release=False)

    # Main loop monitors release by checking key states
    try:
        # Start tray in a thread (if available)
        if TRAY_AVAILABLE:
            threading.Thread(target=run_tray, daemon=True).start()
        while True:
            time.sleep(0.1)
            if hotkey_pressed:
                # check if keys still down; if not -> release
                # We check ctrl & alt & v for our hotkey; if you change HOTKEY you may need to adjust this
                parts = runtime["hotkey"].split('+')
                still_down = all(keyboard.is_pressed(p) for p in parts)
                if not still_down:
                    on_hotkey_release()
    except KeyboardInterrupt:
        print("\n[*] Exiting...")

if __name__ == "__main__":
    main()
