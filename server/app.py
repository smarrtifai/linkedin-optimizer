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
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# ===============================
# MongoDB Configuration
# ===============================
MONGO_URI = os.environ.get("MONGO_URI")
if not MONGO_URI:
    raise RuntimeError("❌ MONGO_URI not set in environment variables")

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.server_info()  # Trigger actual connection
except Exception as mongo_err:
    raise RuntimeError(f"❌ MongoDB connection failed: {mongo_err}")

db = client["linkedin_optimizer"]
submissions_collection = db["submissions"]

# ===============================
# Upload Route
# ===============================
@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("pdf")
    if not file:
        print("❌ No file uploaded")
        return jsonify({"error": "No file provided"}), 400

    try:
        lines, hyperlinks = extract_text_from_pdf(file)
        joined_text = " ".join(lines + hyperlinks)

        if not joined_text.strip():
            print("❌ Empty or unreadable PDF content")
            return jsonify({"error": "No readable text found in the PDF."}), 400

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

        # Clean LinkedIn URL
        if "linkedin.com" in linkedin_url:
            parsed = urlparse(linkedin_url)
            linkedin_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

        print("✅ Extracted name:", name)
        print("✅ Extracted email:", email)
        print("✅ Extracted LinkedIn:", linkedin_url)

        # Generate suggestions
        suggestions = generate_groq_suggestions(joined_text)
        score = suggestions.get("overallscore", 0)
        print("✅ Groq score:", score)

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

        try:
            submissions_collection.insert_one(submission)
            print("✅ Submission saved to MongoDB")
        except Exception as db_error:
            print("❌ MongoDB insert error:", db_error)

        return jsonify({
            "suggestions": suggestions,
            "meta": {
                "name": name,
                "email": email,
                "linkedin": linkedin_url
            }
        })

    except Exception as e:
        print("❌ [UPLOAD ERROR]", repr(e))
        return jsonify({"error": str(e)}), 500

# ===============================
# View Submissions
# ===============================
@app.route("/submissions", methods=["GET"])
def get_submissions():
    try:
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
    except Exception as e:
        print("❌ [FETCH SUBMISSIONS ERROR]", repr(e))
        return jsonify({"error": str(e)}), 500

# ===============================
# Health Check
# ===============================
@app.route("/")
def index():
    return "✅ LinkedIn Optimizer API (MongoDB version) is running."

# ===============================
# Run App (Render-compatible)
# ===============================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
