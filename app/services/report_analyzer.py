import os
from typing import Optional
import fitz

from dotenv import load_dotenv
from google import genai
from app.config.settings import settings

load_dotenv()

_easyocr_reader = None


def get_ocr_reader():
    global _easyocr_reader
    if _easyocr_reader is None:
        import easyocr
        _easyocr_reader = easyocr.Reader(['en'])
    return _easyocr_reader


def get_genai_client() -> Optional[genai.Client]:
    api_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    try:
        return genai.Client(api_key=api_key)
    except Exception as e:
        print(f"Failed to initialize GenAI Client: {e}")
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

    client = get_genai_client()
    if not client:
        return """
⚠ GEMINI_API_KEY is not configured or invalid.

Please set a valid GEMINI_API_KEY in your environment variables to analyze medical reports.
"""

    try:
        model_name = settings.GEMINI_MODEL or "gemini-2.0-flash"
        if not model_name or "2.5" in model_name:
            model_name = "gemini-2.0-flash"
        models_to_try = [model_name]
        if "gemini-2.0-flash-lite" not in models_to_try:
            models_to_try.append("gemini-2.0-flash-lite")

        response = None
        last_exception = None
        for m in models_to_try:
            try:
                response = client.models.generate_content(
                    model=m,
                    contents=prompt
                )
                break
            except Exception as e:
                last_exception = e

        if not response and last_exception:
            raise last_exception

        if getattr(response, "text", None):
            return response.text

        elif (
            hasattr(response, "candidates")
            and response.candidates
            and response.candidates[0].content.parts
        ):
            return response.candidates[0].content.parts[0].text

        else:
            return "Unable to generate report analysis."

    except Exception as e:

        print(e)

        return f"Error while analyzing report:\n\n{str(e)}"