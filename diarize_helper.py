# diarize_helper.py
# A small helper that saves audio to WAV and shows how to call pyannote later.
# You don't need to run this until you install pyannote.audio

from pathlib import Path
import soundfile as sf
import numpy as np
import torch

def save_array_to_wav(np_audio, sr, out_path):
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(out_path), np_audio, sr)
    print("Saved:", out_path)

# Example usage (after recording):
# save_array_to_wav(audio_np, 16000, "notes/for_diarize/example.wav")

# If you choose to install pyannote later, the docs/command is roughly:
# pip install pyannote.audio
# Then, from a script:
# from pyannote.audio import Pipeline
# pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization", use_auth_token="YOUR_HF_TOKEN")
# diarization = pipeline("notes/for_diarize/example.wav")
# print(diarization)
