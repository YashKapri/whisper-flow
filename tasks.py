import whisper
from celery import Celery
import os
from sqlalchemy import create_engine, text

# Setup Celery and DB
celery = Celery('tasks', broker=os.environ.get('CELERY_BROKER_URL'))
db_engine = create_engine(os.environ.get('DATABASE_URL'))

# Global variable for lazy loading
model = None

def get_model():
    global model
    if model is None:
        print("Loading Whisper Model...")
        # Speed aur Accuracy ka best balance (Small)
        model = whisper.load_model("small")
        print("Model Loaded!")
    return model

# --- GARBAGE FILTER FUNCTION ---
def clean_hallucinations(text):
    """Remove known Whisper hallucinations"""
    garbage_phrases = [
        "transcribe your voice", "I'm Ashka", "Ashkabli", "Amara.org", 
        "coding", "subscribe", "my name is", "MBC", "copyright"
    ]
    
    cleaned_text = text
    for phrase in garbage_phrases:
        if phrase.lower() in text.lower():
            print(f"[Filter] Removed hallucination: {phrase}")
            if len(text) < 50: 
                return ""
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
        
        # 3. Run AI (Translation Mode)
        options = {
            "fp16": False,
            "task": "translate",
            "temperature": 0,
            "no_speech_threshold": 0.75,
            "logprob_threshold": -1.0,
            "condition_on_previous_text": False,
            "initial_prompt": "Hello." 
        }
        
        result = ai_model.transcribe(file_path, **options)
        raw_text = result.get("text", "").strip()

        # 4. Apply Garbage Filter
        final_text = clean_hallucinations(raw_text)
        if not final_text:
            final_text = "[Silence / No Speech Detected]"

        # 5. Save to DB
        with db_engine.connect() as conn:
            conn.execute(text("""
                UPDATE notes 
                SET transcript=:t, status='Completed' 
                WHERE id=:id
            """), {"t": final_text, "id": task_id_db})
            conn.commit()

        # --- 6. AUTO CLEANUP (DELETE AUDIO FILE) ---
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"[Cleanup] Successfully deleted: {file_path}")
        except Exception as cleanup_error:
            print(f"[Cleanup Warning] Could not delete file: {cleanup_error}")
            
        return "Done"
        
    except Exception as e:
        print(f"Error: {e}")
        with db_engine.connect() as conn:
            conn.execute(text("UPDATE notes SET status='Failed' WHERE id=:id"), {"id": task_id_db})
            conn.commit()
        
        # Error ke case mein bhi file delete kar deni chahiye taaki kachra na jama ho
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except:
            pass