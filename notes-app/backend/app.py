import os
import time
from datetime import datetime

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import OperationalError

# ------------------------------------------------------------------
# Configuration -- كله من environment variables
# ------------------------------------------------------------------
DB_HOST = os.environ.get("DB_HOST", "db")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_USER = os.environ.get("DB_USER", "notes_user")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "notes_pass")
DB_NAME = os.environ.get("DB_NAME", "notes_db")

# ممكن كمان تدي DATABASE_URL مباشرة لو حابب، وهي هتاخد الأولوية
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
)

CORS_ORIGIN = os.environ.get("CORS_ORIGIN", "*")
PORT = int(os.environ.get("PORT", "5000"))
DB_CONNECT_RETRIES = int(os.environ.get("DB_CONNECT_RETRIES", "10"))
DB_CONNECT_RETRY_DELAY = int(os.environ.get("DB_CONNECT_RETRY_DELAY", "3"))

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

CORS(app, resources={r"/api/*": {"origins": CORS_ORIGIN}})

db = SQLAlchemy(app)


class Note(db.Model):
    __tablename__ = "notes"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=True, default="")
    is_done = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "is_done": self.is_done,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


def wait_for_db_and_init():
    """
    الـ backend container غالبًا هيتشغل قبل ما الـ database container
    يخلص initialization. الدالة دي بتحاول تتصل بالـ DB كذا مرة قبل ما
    تستسلم، بدل ما التطبيق يـ crash على طول.
    """
    attempt = 0
    while attempt < DB_CONNECT_RETRIES:
        try:
            with app.app_context():
                db.create_all()
            print("Database connected and tables created.")
            return
        except OperationalError:
            attempt += 1
            print(
                f"DB not ready yet (attempt {attempt}/{DB_CONNECT_RETRIES}), "
                f"retrying in {DB_CONNECT_RETRY_DELAY}s..."
            )
            time.sleep(DB_CONNECT_RETRY_DELAY)
    raise RuntimeError("Could not connect to the database after multiple retries.")


@app.route("/health")
def health():
    return jsonify(status="ok"), 200


@app.route("/api/notes", methods=["GET"])
def list_notes():
    notes = Note.query.order_by(Note.created_at.desc()).all()
    return jsonify([n.to_dict() for n in notes])


@app.route("/api/notes/<int:note_id>", methods=["GET"])
def get_note(note_id):
    note = Note.query.get_or_404(note_id)
    return jsonify(note.to_dict())


@app.route("/api/notes", methods=["POST"])
def create_note():
    data = request.get_json(silent=True) or {}
    title = data.get("title", "").strip()

    if not title:
        return jsonify(error="Title is required"), 400

    note = Note(title=title, content=data.get("content", ""))
    db.session.add(note)
    db.session.commit()
    return jsonify(note.to_dict()), 201


@app.route("/api/notes/<int:note_id>", methods=["PUT"])
def update_note(note_id):
    note = Note.query.get_or_404(note_id)
    data = request.get_json(silent=True) or {}

    if "title" in data:
        title = data["title"].strip()
        if not title:
            return jsonify(error="Title cannot be empty"), 400
        note.title = title

    if "content" in data:
        note.content = data["content"]

    db.session.commit()
    return jsonify(note.to_dict())


@app.route("/api/notes/<int:note_id>/toggle", methods=["PATCH"])
def toggle_note(note_id):
    note = Note.query.get_or_404(note_id)
    note.is_done = not note.is_done
    db.session.commit()
    return jsonify(note.to_dict())


@app.route("/api/notes/<int:note_id>", methods=["DELETE"])
def delete_note(note_id):
    note = Note.query.get_or_404(note_id)
    db.session.delete(note)
    db.session.commit()
    return jsonify(message="Deleted successfully"), 200


wait_for_db_and_init()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=False)
