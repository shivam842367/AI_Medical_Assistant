import os
import fitz
import easyocr

from dotenv import load_dotenv
from google import genai

load_dotenv()

def get_genai_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    try:
        return genai.Client(api_key=api_key)
    except Exception:
        return None

# OCR Reader (Lazy Loaded)
_ocr_reader = None

def get_ocr_reader():
    global _ocr_reader
    if _ocr_reader is None:
        _ocr_reader = easyocr.Reader(['en'], verbose=False)
    return _ocr_reader


def extract_text(file_path: str, ocr_reader=None):

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

        reader_inst = ocr_reader if ocr_reader is not None else get_ocr_reader()
        result = reader_inst.readtext(file_path)

        text = ""

        for item in result:
            text += item[1] + "\n"

        return text

    return ""


def analyze_report(file_path: str, ocr_reader=None):

    report_text = extract_text(file_path, ocr_reader=ocr_reader)

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

    try:
        client = get_genai_client()
        if not client:
            return "⚠ GEMINI_API_KEY environment variable is not configured. Please set your Gemini API key in .env or Streamlit secrets."

        response = client.models.generate_content(
            model="models/gemini-3.5-flash",
            contents=prompt
        )

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