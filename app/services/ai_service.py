import os

from dotenv import load_dotenv
from google import genai
from sqlalchemy.orm import Session

from app.models.chat import ChatHistory
from app.schemas.ai import ChatResponse
#from app.services.symptom_service import get_symptom_prompt

load_dotenv()

def get_genai_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    try:
        return genai.Client(api_key=api_key)
    except Exception:
        return None

def chat_with_ai(
    db: Session,
    message: str,
    user_id: int
):

    # ---------------- Emergency Detection ----------------
    emergency_keywords = [
        "chest pain",
        "difficulty breathing",
        "can't breathe",
        "heart attack",
        "stroke",
        "blood vomiting",
        "unconscious",
        "severe bleeding",
        "seizure",
        "fainted",
        "suicidal"
    ]

    if any(word in message.lower() for word in emergency_keywords):

        answer = """
🚨 MEDICAL EMERGENCY

Your symptoms may indicate a serious medical emergency.

• Please call your local emergency services immediately.
• Visit the nearest hospital as soon as possible.
• Do not rely only on this AI assistant.

⚠ This assistant cannot replace professional medical care.
"""

        chat = ChatHistory(
            user_id=user_id,
            question=message,
            answer=answer
        )

        db.add(chat)
        db.commit()
        db.refresh(chat)

        return ChatResponse(response=answer)

    # ---------------- Gemini Prompt ----------------
    medical_prompt = f"""
You are an AI Medical Assistant.

Rules:
- Answer ONLY medical and healthcare-related questions.
- If the question is not medical, politely refuse and say that you only answer medical questions.
- Never claim to be a real doctor.
- Never provide dangerous or harmful advice.
- Recommend consulting a healthcare professional whenever necessary.
- If it is an emergency, advise the user to seek immediate medical attention.
- Use simple English.
- Use bullet points whenever possible.
- Keep the answer between 100 and 150 words.
- Never exceed 150 words.
- Do not write unnecessary introductions.

User Question:
{message}
"""

    try:
        client = get_genai_client()
        response = None
        if not client:
            answer = "⚠ GEMINI_API_KEY environment variable is not configured. Please set your Gemini API key in .env or Streamlit secrets."
        else:
            response = client.models.generate_content(
                model="models/gemini-3.5-flash",
                contents=medical_prompt
            )

        if response is not None:
            print("\n================ GEMINI RESPONSE ================")
            print(response)
            print("=================================================\n")

        if response and getattr(response, "text", None):
            answer = response.text

        elif (
            hasattr(response, "candidates")
            and response.candidates
            and response.candidates[0].content.parts
        ):
            answer = response.candidates[0].content.parts[0].text

        else:
            answer = "Sorry! I couldn't generate a response."

        # Medical Disclaimer
        answer += """

---------------------------------------

⚠ Medical Disclaimer

This AI assistant provides general health information only.

Please consult a qualified healthcare professional for diagnosis and treatment.
"""

    except Exception as e:

        print("\n============= GEMINI ERROR =============")
        print(e)
        print("========================================\n")

        answer = """
        ⚠ AI service is temporarily unavailable.

        Please try again in a few moments.

        If the issue persists, please check your internet connection or try again later.
        """

    chat = ChatHistory(
        user_id=user_id,
        question=message,
        answer=answer
    )

    db.add(chat)
    db.commit()
    db.refresh(chat)

    return ChatResponse(
        response=answer
    )


def delete_chat(
    db: Session,
    chat_id: int,
    user_id: int
):

    chat = (
        db.query(ChatHistory)
        .filter(
            ChatHistory.id == chat_id,
            ChatHistory.user_id == user_id
        )
        .first()
    )

    if not chat:
        return {
            "message": "Chat not found."
        }

    db.delete(chat)
    db.commit()

    return {
        "message": "Chat deleted successfully."
    }