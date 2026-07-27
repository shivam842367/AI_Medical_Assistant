import os
from typing import Optional

from dotenv import load_dotenv
from groq import Groq
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.models.chat import ChatHistory
from app.schemas.ai import ChatResponse

load_dotenv()


def get_groq_client() -> Optional[Groq]:
    api_key = (
        getattr(settings, "GROQ_API_KEY", None)
        or os.getenv("GROQ_API_KEY")
    )
    if not api_key:
        # Fallback check if user put groq key into GEMINI_API_KEY
        gemini_key = getattr(settings, "GEMINI_API_KEY", None) or os.getenv("GEMINI_API_KEY")
        if gemini_key and str(gemini_key).strip('"\' ').startswith("gsk_"):
            api_key = gemini_key

    if not api_key:
        return None

    api_key = str(api_key).strip('"\' ')
    if not api_key or not api_key.startswith("gsk_"):
        return None

    try:
        return Groq(api_key=api_key)
    except Exception as e:
        print(f"Failed to initialize Groq Client: {e}")
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

    # ---------------- Medical Prompt ----------------
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

    client = get_groq_client()
    if not client:
        answer = """
⚠ GROQ_API_KEY is not configured or invalid.

Please configure a valid GROQ_API_KEY in your environment variables to enable AI chat functionality.

⚠ Medical Disclaimer:
This AI assistant provides general health information only.
Please consult a qualified healthcare professional for diagnosis and treatment.
"""
    else:
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
                                "content": "You are an AI Medical Assistant."
                            },
                            {
                                "role": "user",
                                "content": medical_prompt
                            }
                        ]
                    )
                    break
                except Exception as e:
                    last_exception = e

            if not response and last_exception:
                raise last_exception

            if response and response.choices and response.choices[0].message and response.choices[0].message.content:
                answer = response.choices[0].message.content.strip()
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
            err_str = str(e)
            print("\n============= GROQ ERROR =============")
            print(e)
            print("======================================\n")

            answer = f"""
⚠ Groq Service Error:

{err_str}

Please verify that a valid GROQ_API_KEY is configured in your environment variables.
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