from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from celery import Celery  # Sirf Celery import karenge, tasks nahi
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Configure Celery Client (Sirf message bhejne ke liye)
celery_client = Celery('tasks', broker=os.environ.get('CELERY_BROKER_URL'))

# --- Database Model ---
class Note(db.Model):
    __tablename__ = 'notes'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200))
    status = db.Column(db.String(50), default="Pending")
    transcript = db.Column(db.Text, nullable=True)

# --- Routes ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    try:
        if 'audio' not in request.files:
            return jsonify({"error": "No audio file part"}), 400
            
        file = request.files['audio']
        if file.filename == "":
            return jsonify({"error": "No selected file"}), 400

        # Ensure uploads directory exists
        upload_dir = "/app/uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        save_path = os.path.join(upload_dir, file.filename)
        file.save(save_path)

        # Create DB Entry
        new_note = Note(filename=file.filename)
        db.session.add(new_note)
        db.session.commit()

        # Send Task to Worker by Name (Lightweight way)
        # Ye line bina model load kiye task bhej degi
        celery_client.send_task('tasks.transcribe_audio', args=[save_path, new_note.id])

        return jsonify({"message": "Upload successful!", "job_id": new_note.id})

    except Exception as e:
        # Agar server crash ho, toh asli error dikhayein JSON mein
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/status/<job_id>')
def check_status(job_id):
    try:
        note = Note.query.get(job_id)
        if note:
            return jsonify({"status": note.status, "transcript": note.transcript})
        return jsonify({"error": "Not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Error Handlers (Taaki HTML error na aaye)
@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal Server Error"}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not Found"}), 404

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000)

# ... (Upar ka code same rahega)

# --- HISTORY API (New) ---
@app.route('/history')
def get_history():
    # Fetch last 50 records (Newest First)
    notes = Note.query.order_by(Note.id.desc()).limit(50).all()
    
    history_data = []
    for n in notes:
        history_data.append({
            "id": n.id,
            "filename": n.filename,
            "status": n.status,
            "transcript": n.transcript[:100] + "..." if n.transcript else "" # Preview only
        })
    
    return jsonify(history_data)

# ... (Neeche ka code same rahega)