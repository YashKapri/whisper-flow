import argparse
import os
import re
from datetime import datetime
from pathlib import Path

import whisper

# ---------- SETTINGS ----------
# Choose model size: tiny, base, small, medium, large
WHISPER_MODEL_NAME = "small"  # good for your Ryzen 5 + GTX 1650
INPUT_DIR = Path("input_audio")
OUTPUT_DIR = Path("notes")
# ------------------------------


def load_model():
    print(f"[+] Loading Whisper model: {WHISPER_MODEL_NAME}")
    model = whisper.load_model(WHISPER_MODEL_NAME)
    print("[+] Model loaded.")
    return model


def simple_sentence_split(text: str):
    sentences = re.split(r'(?<=[.!?।?])\s+', text.strip())
    sentences = [s.strip() for s in sentences if s.strip()]
    return sentences


def make_summary(text: str, max_sentences: int = 5):
    sentences = simple_sentence_split(text)
    if not sentences:
        return "(No content for summary.)"

    n = min(max_sentences, max(1, len(sentences) // 3))
    return " ".join(sentences[:n])


def extract_action_items(text: str):
    # This is basic and works best for English.
    sentences = simple_sentence_split(text)
    keywords = [
        "need to", "have to", "must", "should", "let's", "we will",
        "i will", "to do", "todo", "remember to", "plan to"
    ]
    tasks = []

    for s in sentences:
        lower = s.lower()
        if any(k in lower for k in keywords):
            tasks.append(s.strip())

    seen = set()
    unique_tasks = []
    for t in tasks:
        if t not in seen:
            seen.add(t)
            unique_tasks.append(t)

    return unique_tasks


def transcribe_file(model, audio_path: Path, language: str = "auto"):
    print(f"[+] Transcribing: {audio_path.name}")
    if language == "auto":
        # Let Whisper detect language
        result = model.transcribe(str(audio_path))
    else:
        # Force specific language: 'en' or 'hi'
        result = model.transcribe(str(audio_path), language=language)

    text = result.get("text", "").strip()
    detected_lang = result.get("language", None)
    if detected_lang:
        print(f"[+] Detected language: {detected_lang}")
    return text, detected_lang


def safe_title_from_filename(name: str) -> str:
    base = os.path.splitext(name)[0]
    base = base.replace("_", " ").replace("-", " ")
    return base.title() if base else "Untitled Note"


def save_note(audio_path: Path, transcript: str, language_used: str | None):
    OUTPUT_DIR.mkdir(exist_ok=True)

    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    filename_time = now.strftime("%Y-%m-%d_%H-%M-%S")

    title = safe_title_from_filename(audio_path.name)

    summary = make_summary(transcript)
    tasks = extract_action_items(transcript)

    md_path = OUTPUT_DIR / f"{filename_time}_{audio_path.stem}.md"

    with md_path.open("w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n")
        f.write(f"**Created:** {timestamp}\n\n")
        if language_used:
            f.write(f"**Language (detected or set):** `{language_used}`\n\n")

        f.write("## Summary (auto-generated)\n\n")
        f.write(summary + "\n\n")

        f.write("## Action Items (auto-detected, mostly English-aware)\n\n")
        if tasks:
            for t in tasks:
                f.write(f"- [ ] {t}\n")
        else:
            f.write("_No clear action items detected._\n")

        f.write("\n\n## Full Transcript\n\n")
        f.write(transcript + "\n")

    print(f"[+] Note saved to: {md_path}")
    return md_path


def process_single_file(model, audio_path: Path, language: str):
    transcript, detected_lang = transcribe_file(model, audio_path, language)
    if not transcript:
        print("[!] Empty transcript, skipping note creation.")
        return None
    lang_label = language if language != "auto" else detected_lang
    note_path = save_note(audio_path, transcript, lang_label)
    return note_path


def process_folder(model, language: str):
    INPUT_DIR.mkdir(exist_ok=True)
    audio_files = sorted(
        [
            p for p in INPUT_DIR.iterdir()
            if p.is_file() and not p.name.endswith(".processed")
        ]
    )

    if not audio_files:
        print("[!] No audio files found in input_audio/")
        return

    for audio_path in audio_files:
        try:
            note_path = process_single_file(model, audio_path, language)
            if note_path:
                processed_name = audio_path.with_suffix(audio_path.suffix + ".processed")
                audio_path.rename(processed_name)
                print(f"[+] Marked as processed: {processed_name.name}")
        except Exception as e:
            print(f"[!] Error processing {audio_path.name}: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Whisper Flow Pro (local, free) - EN/HIN speech to markdown notes."
    )
    parser.add_argument(
        "audio",
        nargs="?",
        help="Path to a single audio file (optional). If not given, processes input_audio/ folder.",
    )
    parser.add_argument(
        "--language",
        "-l",
        choices=["auto", "en", "hi"],
        default="auto",
        help="Language for transcription: auto (default), en (English), hi (Hindi).",
    )
    args = parser.parse_args()

    model = load_model()

    if args.audio:
        audio_path = Path(args.audio)
        if not audio_path.exists():
            print(f"[!] File not found: {audio_path}")
            return
        process_single_file(model, audio_path, args.language)
    else:
        process_folder(model, args.language)


if __name__ == "__main__":
    main()
