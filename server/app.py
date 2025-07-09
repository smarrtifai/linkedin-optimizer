from flask import Flask, request, jsonify
from flask_cors import CORS
from pdf_reader import extract_text_from_pdf
from groq_api import generate_groq_suggestions
from urllib.parse import urlparse
from pymongo import MongoClient
from datetime import datetime
import os
import re

app = Flask(__name__)
CORS(app)

# ===============================
# MongoDB Configuration
# ===============================
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
client = MongoClient(MONGO_URI)
db = client["linkedin_optimizer"]
submissions_collection = db["submissions"]

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

        # Save to MongoDB
        submission = {
            "name": name,
            "email": email,
            "linkedin_url": linkedin_url,
            "filename": file.filename,
            "score": score,
            "raw_text": joined_text,
            "timestamp": datetime.utcnow()
        }
        submissions_collection.insert_one(submission)

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
    records = submissions_collection.find().sort("timestamp", -1)
    result = []
    for r in records:
        result.append({
            "name": r.get("name"),
            "email": r.get("email"),
            "linkedin": r.get("linkedin_url"),
            "filename": r.get("filename"),
            "score": r.get("score"),
            "timestamp": r.get("timestamp").isoformat() if r.get("timestamp") else ""
        })
    return jsonify(result)

@app.route("/")
def index():
    return "✅ LinkedIn Optimizer API (MongoDB version) is running."

# ===============================
# Run the app
# ===============================
if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000, debug=True, use_reloader=False)
