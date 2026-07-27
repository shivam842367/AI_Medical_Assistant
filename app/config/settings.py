from dotenv import load_dotenv
import os

load_dotenv()


class Settings:
    PROJECT_NAME = "AI Medical Assistant"

    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./medical_assistant.db")
    SECRET_KEY = os.getenv("SECRET_KEY", "medical_assistant_secret_key_2026")
    ALGORITHM = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")
    )


settings = Settings()