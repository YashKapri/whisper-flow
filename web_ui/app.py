# web_ui/app.py
from datetime import datetime
from pathlib import Path
import os
import re
import tempfile

from flask import Flask, render_template, request, jsonify
import whisper

# Paths relative to project root (..)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
NOTES_DIR = PROJECT_ROOT / "notes"

WHISPER_MODEL_NAME = "small"

app = Flask(__name__, static_folder="static")
model = whisper.load_model(WHISPER_MODEL_NAME)


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
    unique = []
    for t in tasks:
        if t not in seen:
            seen.add(t)
            unique.append(t)
    return unique


def safe_title_from_filename(name: str) -> str:
    base = os.path.splitext(name)[0]
    base = base.replace("_", " ").replace("-", " ")
    return base.title() if base else "Untitled Note"


@app.route("/")
def index():
    NOTES_DIR.mkdir(exist_ok=True)
    notes = sorted(NOTES_DIR.glob("*.md"), reverse=True)
    return render_template("index.html", notes=[n.name for n in notes])


@app.route("/upload", methods=["POST"])
def upload():
    if "audio" not in request.files:
        return jsonify({"error": "No audio file uploaded"}), 400

    file = request.files["audio"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    # --- FIX: Retrieve form data correctly ---
    language_choice = request.form.get("language", "auto")
    task_choice = request.form.get("task", "transcribe")

    # Create temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        file.save(tmp.name)
        temp_path = tmp.name

    # --- FIX: Unified Transcribe/Translate logic ---
    try:
        # Prepare arguments for Whisper
        lang_arg = None if language_choice == "auto" else language_choice
        
        # Run model
        result = model.transcribe(
            temp_path, 
            task=task_choice, 
            language=lang_arg
        )
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return jsonify({"error": f"Transcription failed: {str(e)}"}), 500

    # Cleanup temp file
    if os.path.exists(temp_path):
        os.remove(temp_path)

    transcript = result.get("text", "").strip()
    detected_lang = result.get("language", None)

    if not transcript:
        return jsonify({"error": "Empty transcript"}), 500

    # --- Note Generation (Existing Logic) ---
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    filename_time = now.strftime("%Y-%m-%d_%H-%M-%S")
    title = safe_title_from_filename(file.filename)

    summary = make_summary(transcript)
    tasks = extract_action_items(transcript)

    NOTES_DIR.mkdir(exist_ok=True)
    md_path = NOTES_DIR / f"{filename_time}_{Path(file.filename).stem}.md"
    
    # Use the selected language if not auto, otherwise the detected one
    lang_label = language_choice if language_choice != "auto" else detected_lang

    with md_path.open("w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n")
        f.write(f"**Created:** {timestamp}\n\n")
        if lang_label:
            f.write(f"**Language:** `{lang_label}`  ")
            f.write(f"**Task:** `{task_choice}`\n\n")

        f.write("## Summary (auto-generated)\n\n")
        f.write(summary + "\n\n")

        f.write("## Action Items (auto-detected)\n\n")
        if tasks:
            for t in tasks:
                f.write(f"- [ ] {t}\n")
        else:
            f.write("_No clear action items detected._\n")

        f.write("\n\n## Full Transcript\n\n")
        f.write(transcript + "\n")

    return jsonify({
        "title": title,
        "summary": summary,
        "tasks": tasks,
        "transcript": transcript,
        "note_file": md_path.name,
        "language": lang_label,
    })

@app.route("/list-notes")
def list_notes():
    NOTES_DIR.mkdir(exist_ok=True)
    # Get list of note filenames
    notes = [n.name for n in sorted(NOTES_DIR.glob("*.md"), reverse=True)]
    return jsonify(notes)


if __name__ == "__main__":
    app.run(debug=True)
