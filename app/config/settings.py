from dotenv import load_dotenv
import os

load_dotenv()


class Settings:
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "AI Medical Assistant")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./medical_assistant.db")
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY", "medical_assistant_secret_key_2026_default"
    )
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")
    )
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


settings = Settings()