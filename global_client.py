import keyboard
import requests
import pyaudio
import wave
import os
import time
import pyperclip
import threading
import winsound  # Sound feedback ke liye

# --- CONFIGURATION ---
BACKEND_URL = "http://localhost:5000"
HOTKEY = "f4"  # Is button se recording Start/Stop hogi
TEMP_FILENAME = "temp_dictation.wav"

def play_sound(freq):
    """Choti beep bajata hai taaki bina dekhe pata chale"""
    try:
        winsound.Beep(freq, 200)
    except:
        pass

def upload_and_transcribe(filename):
    print(f"\n[Server] Uploading {filename}...")
    try:
        with open(filename, 'rb') as f:
            files = {'audio': f}
            response = requests.post(f"{BACKEND_URL}/upload", files=files)
            
        if response.status_code != 200:
            print("❌ Upload Failed:", response.text)
            return None

        job_id = response.json().get('job_id')
        print(f"[Server] Processing (Job ID: {job_id})...")

        # Polling for result
        while True:
            status_res = requests.get(f"{BACKEND_URL}/status/{job_id}")
            data = status_res.json()
            
            if data['status'] == 'Completed':
                return data['transcript']
            elif data['status'] == 'Failed':
                print("❌ Transcription Failed on Server")
                return None
            
            time.sleep(0.5) # Wait a bit before checking again

    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return None

def main():
    print(f"=========================================")
    print(f" 🎙️  WHISPER FLOW GLOBAL CLIENT ")
    print(f"=========================================")
    print(f"Status: Ready")
    print(f"Action: Press [{HOTKEY.upper()}] to START recording.")
    print(f"        Press [{HOTKEY.upper()}] again to STOP & PASTE.")
    print(f"-----------------------------------------")

    # Audio Config
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100

    p = pyaudio.PyAudio()

    while True:
        # 1. Wait for Key Press to START
        keyboard.wait(HOTKEY)
        
        # Debounce (Wait until key is released)
        while keyboard.is_pressed(HOTKEY): time.sleep(0.1)

        print("\n🔴 Recording... (Press Key again to stop)")
        play_sound(600) # Low beep = Start

        frames = []
        stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)

        # 2. Recording Loop
        while True:
            try:
                data = stream.read(CHUNK)
                frames.append(data)
                
                # Check if Stop Key is Pressed
                if keyboard.is_pressed(HOTKEY):
                    break
            except:
                break

        # Stop Recording
        stream.stop_stream()
        stream.close()
        play_sound(1000) # High beep = Stop
        print("✅ Stopped. Transcribing...")

        # Debounce Stop Key
        while keyboard.is_pressed(HOTKEY): time.sleep(0.1)

        # Save File
        wf = wave.open(TEMP_FILENAME, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()

        # Send to Backend
        text = upload_and_transcribe(TEMP_FILENAME)

        if text:
            print(f"📝 Output: {text}")
            # Copy to Clipboard
            pyperclip.copy(text)
            # Simulate Paste (Ctrl+V)
            keyboard.send('ctrl+v')
            print("✨ Pasted successfully!")
        else:
            print("⚠️ No text received.")

if __name__ == "__main__":
    main()