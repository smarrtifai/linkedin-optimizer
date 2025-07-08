from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from pdf_reader import extract_text_from_pdf
from groq_api import generate_groq_suggestions
import os
import re
from urllib.parse import urlparse

app = Flask(__name__)
CORS(app)

# ===============================
# Database Configuration
# ===============================
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL", "sqlite:///local.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ===============================
# Model
# ===============================
class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    email = db.Column(db.String(120))
    linkedin_url = db.Column(db.String(300))
    filename = db.Column(db.String(255), nullable=False)
    score = db.Column(db.Integer)
    raw_text = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=db.func.now())

# ===============================
# Routes
# ===============================
@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("pdf")
    if not file:
        return jsonify({"error": "No file provided"}), 400

    try:
        lines, hyperlinks = extract_text_from_pdf(file)
        joined_text = " ".join(lines + hyperlinks)

        # Extract name
        name = next(
            (line for line in lines if len(line.split()) >= 2 and line.lower() not in [
                "contact", "top skills", "experience", "education", "summary",
                "certifications", "languages", "projects", "publications"
            ]),
            "Unknown"
        )

        # Extract email
        email = "Not found"
        for link in hyperlinks:
            if "mailto:" in link:
                email = link.replace("mailto:", "").strip()
                break
        if email == "Not found":
            email_match = re.search(
                r"(?:mailto:)?([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
                joined_text, re.IGNORECASE
            )
            if email_match:
                email = email_match.group(1)

        # Extract LinkedIn URL
        linkedin_url = "Not found"
        for link in hyperlinks:
            if "linkedin.com/in/" in link or "linkedin.com/pub/" in link:
                linkedin_url = link.strip()
                break
        if linkedin_url == "Not found":
            linkedin_match = re.search(
                r"https?://(?:www\.)?linkedin\.com/(in|pub|profile)/[a-zA-Z0-9\-_/]+(?:\?[^\s]*)?",
                joined_text, re.IGNORECASE
            )
            if linkedin_match:
                linkedin_url = linkedin_match.group(0)

        # Clean LinkedIn URL (remove query params)
        if "linkedin.com" in linkedin_url:
            parsed = urlparse(linkedin_url)
            linkedin_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

        # Generate suggestions
        suggestions = generate_groq_suggestions(joined_text)
        score = suggestions.get("overallscore", 0)

        # Save to DB
        new_entry = Submission(
            name=name,
            email=email,
            linkedin_url=linkedin_url,
            filename=file.filename,
            score=score,
            raw_text=joined_text
        )
        db.session.add(new_entry)
        db.session.commit()

        return jsonify({
            "suggestions": suggestions,
            "meta": {
                "name": name,
                "email": email,
                "linkedin": linkedin_url
            }
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/submissions", methods=["GET"])
def get_submissions():
    records = Submission.query.order_by(Submission.timestamp.desc()).all()
    return jsonify([
        {
            "name": r.name,
            "email": r.email,
            "linkedin": r.linkedin_url,
            "filename": r.filename,
            "score": r.score,
            "timestamp": r.timestamp.isoformat()
        }
        for r in records
    ])

@app.route("/")
def index():
    return "✅ LinkedIn Optimizer API is running."

# ===============================
# Run the app
# ===============================
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        print("✅ Database initialized.")
    app.run(host='127.0.0.1', port=5000, debug=True)
