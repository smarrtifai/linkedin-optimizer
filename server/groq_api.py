import os
import requests
import re

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama3-70b-8192"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

if not GROQ_API_KEY:
    raise EnvironmentError("❌ GROQ_API_KEY is not set in environment variables.")

headers = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json"
}

system_prompt = """
You are a LinkedIn profile optimization expert.
Your job is to evaluate the uploaded PDF text (extracted from a LinkedIn profile) and return a detailed analysis.

Output format:
Overall Score: <score>/100

About:
Score: <score>/10
Insight: <two-liner>
Suggestions:
- Suggestion 1: <tip>
- Suggestion 2: <tip>
- Suggestion 3: <tip>

Experience:
Score: <score>/10
Insight: <two-liner>
Suggestions:
- Suggestion 1: <tip>
- Suggestion 2: <tip>
- Suggestion 3: <tip>

Skills:
Score: <score>/10
Insight: <two-liner>
Suggestions:
- Suggestion 1: <tip>
- Suggestion 2: <tip>
- Suggestion 3: <tip>

Completeness:
Score: <score>/10
Insight: <two-liner>
Suggestions:
- Suggestion 1: <tip>
- Suggestion 2: <tip>
- Suggestion 3: <tip>
"""

def generate_groq_suggestions(text):
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text}
        ],
        "temperature": 0.7
    }

    try:
        response = requests.post(GROQ_API_URL, json=payload, headers=headers)
        response.raise_for_status()
        result = response.json()

        raw = result["choices"][0]["message"]["content"]
        print("[✅ GROQ RAW OUTPUT]:\n", raw[:500], "..." if len(raw) > 500 else "")
        return parse_response(raw)

    except requests.exceptions.HTTPError as http_err:
        print("❌ GROQ API HTTP error:", http_err)
        raise RuntimeError("Groq API request failed")
    except Exception as e:
        print("❌ GROQ API unknown error:", repr(e))
        raise RuntimeError("Groq API failed to generate suggestions")

def parse_response(raw_text):
    sections = {
        "overallscore": 0,
        "about": "",
        "experience": "",
        "skills": "",
        "completeness": ""
    }

    current_section = None
    buffer = []

    def flush_buffer():
        nonlocal current_section, buffer
        if current_section and buffer:
            sections[current_section] += "\n".join(buffer).strip() + "\n"
            buffer = []

    for line in raw_text.splitlines():
        line = line.strip()
        if not line:
            continue

        # Match overall score more flexibly
        overall_match = re.search(r"overall score[:\s]*([0-9]{1,3})", line, re.IGNORECASE)
        if overall_match:
            flush_buffer()
            sections["overallscore"] = int(overall_match.group(1))
            current_section = None
            continue

        # Section headers
        if re.match(r"(?i)^about[:\s]*$", line):
            flush_buffer()
            current_section = "about"
            continue
        if re.match(r"(?i)^experience[:\s]*$", line):
            flush_buffer()
            current_section = "experience"
            continue
        if re.match(r"(?i)^skills[:\s]*$", line):
            flush_buffer()
            current_section = "skills"
            continue
        if re.match(r"(?i)^(completeness|structure|formatting)[:\s]*$", line):
            flush_buffer()
            current_section = "completeness"
            continue

        if current_section:
            buffer.append(line)

    flush_buffer()

    # Fallback score logic
    if not sections["overallscore"]:
        total_sections = sum(bool(sections[k]) for k in ["about", "experience", "skills", "completeness"])
        sections["overallscore"] = total_sections * 25

    return sections
