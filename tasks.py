from faster_whisper import WhisperModel
from celery import Celery
import os
from sqlalchemy import create_engine, text

# Setup Celery and DB
celery = Celery('tasks', broker=os.environ.get('CELERY_BROKER_URL'))
db_engine = create_engine(os.environ.get('DATABASE_URL'))

# Global variable
model = None

def get_model():
    global model
    if model is None:
        print("Loading Faster-Whisper Model...")
        # OPTIMIZATION 1: 'medium' model with 'int8'
        # Accuracy: High | Speed: Fast | VRAM: ~1.5GB (Perfect for GTX 1650)
        model = WhisperModel("medium", device="cuda", compute_type="int8")
        print("Model Loaded!")
    return model

# --- GARBAGE FILTER ---
def clean_hallucinations(text):
    garbage_phrases = [
        "transcribe your voice", "I'm Ashka", "Ashkabli", "Amara.org", 
        "coding", "subscribe", "my name is", "MBC", "copyright"
    ]
    cleaned_text = text
    for phrase in garbage_phrases:
        if phrase.lower() in text.lower():
            if len(text) < 50: return ""
            cleaned_text = cleaned_text.replace(phrase, "")
    return cleaned_text.strip()

@celery.task(bind=True)
def transcribe_audio(self, file_path, task_id_db, language="auto"):
    try:
        # 1. Update Status
        with db_engine.connect() as conn:
            conn.execute(text("UPDATE notes SET status='Processing' WHERE id=:id"), {"id": task_id_db})
            conn.commit()

        # 2. Get AI
        ai_model = get_model()
        
        # 3. Run AI (ULTIMATE SETTINGS)
        segments, info = ai_model.transcribe(
            file_path, 
            
            # Accuracy Settings
            beam_size=5,            # High precision search
            task="translate",       # Force English
            condition_on_previous_text=False, # Reduces loops
            
            # PERFORMANCE BOOSTER (VAD)
            vad_filter=True,        # Ignore silence! (Speed++ & Accuracy++)
            vad_parameters=dict(min_silence_duration_ms=500),
            
            # Thresholds
            no_speech_threshold=0.6
        )

        # Combine Segments
        full_text = " ".join([segment.text for segment in segments]).strip()

        # 4. Apply Filter
        final_text = clean_hallucinations(full_text)
        if not final_text: final_text = "[Silence / Unclear]"

        # 5. Save
        with db_engine.connect() as conn:
            conn.execute(text("""
                UPDATE notes 
                SET transcript=:t, status='Completed' 
                WHERE id=:id
            """), {"t": final_text, "id": task_id_db})
            conn.commit()

        # 6. Cleanup (Save Space)
        try:
            if os.path.exists(file_path): os.remove(file_path)
        except: pass
            
        return "Done"
        
    except Exception as e:
        print(f"Error: {e}")
        with db_engine.connect() as conn:
            conn.execute(text("UPDATE notes SET status='Failed' WHERE id=:id"), {"id": task_id_db})
            conn.commit()
        try:
            if os.path.exists(file_path): os.remove(file_path)
        except: pass