import os
from typing import Optional

from dotenv import load_dotenv
from google import genai
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.models.chat import ChatHistory
from app.schemas.ai import ChatResponse

load_dotenv()


def get_genai_client() -> Optional[genai.Client]:
    api_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    try:
        return genai.Client(api_key=api_key)
    except Exception as e:
        print(f"Failed to initialize GenAI Client: {e}")
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

    client = get_genai_client()
    if not client:
        answer = """
⚠ GEMINI_API_KEY is not configured or invalid.

Please configure a valid GEMINI_API_KEY in your environment variables to enable AI chat functionality.

⚠ Medical Disclaimer:
This AI assistant provides general health information only.
Please consult a qualified healthcare professional for diagnosis and treatment.
"""
    else:
        try:
            model_name = settings.GEMINI_MODEL or "gemini-2.0-flash"
            response = client.models.generate_content(
                model=model_name,
                contents=medical_prompt
            )

            if getattr(response, "text", None):
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

If the issue persists, please check your internet connection or API key.
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