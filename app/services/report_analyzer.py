import os
from typing import Optional
import fitz

from dotenv import load_dotenv
from groq import Groq
from app.config.settings import settings

load_dotenv()

_easyocr_reader = None


def get_ocr_reader():
    global _easyocr_reader
    if _easyocr_reader is None:
        import easyocr
        _easyocr_reader = easyocr.Reader(['en'])
    return _easyocr_reader


def get_groq_client() -> Optional[Groq]:
    api_key = (
        getattr(settings, "GROQ_API_KEY", None)
        or os.getenv("GROQ_API_KEY")
        or getattr(settings, "GEMINI_API_KEY", None)
        or os.getenv("GEMINI_API_KEY")
    )
    if not api_key:
        return None
    api_key = str(api_key).strip('"\' ')
    if not api_key:
        return None
    try:
        return Groq(api_key=api_key)
    except Exception as e:
        print(f"Failed to initialize Groq Client: {e}")
        return None


def extract_text(file_path: str):

    extension = os.path.splitext(file_path)[1].lower()

    # ---------------- PDF ----------------
    if extension == ".pdf":

        text = ""

        doc = fitz.open(file_path)

        for page in doc:
            text += page.get_text()

        doc.close()

        return text

    # ---------------- IMAGE ----------------
    elif extension in [".png", ".jpg", ".jpeg"]:

        reader = get_ocr_reader()
        result = reader.readtext(file_path)

        text = ""

        for item in result:
            text += item[1] + "\n"

        return text

    return ""


def analyze_report(file_path: str):

    report_text = extract_text(file_path)

    if not report_text.strip():

        return """
Unable to read the report.

Possible reasons:
• Report image is blurry.
• PDF contains only scanned images.
• Unsupported file.
"""

    prompt = f"""
You are an experienced AI Medical Report Analyzer.

Analyze the following medical report carefully.

Follow this exact format:

# 🩺 Overall Health Summary

Write a 3-4 line summary.

# 📋 Test Results

For every important test write:

• Test Name
• Patient Value
• Normal Range
• Status (Normal / Low / High)
• Explanation

# ⚠ Abnormal Findings

Mention only abnormal values.

# 🍎 Diet Recommendations

Give food suggestions.

# 🏃 Lifestyle Recommendations

Give healthy lifestyle advice.

# 👨‍⚕ When should the patient consult a doctor?

Mention warning signs.

Use very simple English.

Never diagnose with certainty.

Always recommend consulting a qualified doctor.

Medical Report:

{report_text}
"""

    client = get_groq_client()
    if not client:
        return """
⚠ GROQ_API_KEY is not configured or invalid.

Please set a valid GROQ_API_KEY in your environment variables to analyze medical reports.
"""

    try:
        model_name = (
            getattr(settings, "GROQ_MODEL", None)
            or os.getenv("GROQ_MODEL")
            or "llama-3.3-70b-versatile"
        )
        models_to_try = [model_name]
        for fallback in [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "llama3-70b-8192",
            "llama3-8b-8192"
        ]:
            if fallback not in models_to_try:
                models_to_try.append(fallback)

        response = None
        last_exception = None
        for m in models_to_try:
            try:
                response = client.chat.completions.create(
                    model=m,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an experienced AI Medical Report Analyzer."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                )
                break
            except Exception as e:
                last_exception = e

        if not response and last_exception:
            raise last_exception

        if response and response.choices and response.choices[0].message and response.choices[0].message.content:
            return response.choices[0].message.content.strip()

        else:
            return "Unable to generate report analysis."

    except Exception as e:

        print(e)

        return f"Error while analyzing report:\n\n{str(e)}"