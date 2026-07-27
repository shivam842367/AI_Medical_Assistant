from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.utils.auth import get_current_user
from app.models.user import User
from app.models.chat import ChatHistory

from app.database.database import get_db
from app.schemas.ai import ChatRequest, ChatResponse
from app.services.ai_service import chat_with_ai, delete_chat

router = APIRouter(
    prefix="/ai",
    tags=["AI"]
)


@router.post("/chat", response_model=ChatResponse)
def chat(
    data: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return chat_with_ai(
        db=db,
        message=data.message,
        user_id=current_user.id
    )


@router.get("/history")
def get_chat_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    chats = (
        db.query(ChatHistory)
        .filter(ChatHistory.user_id == current_user.id)
        .order_by(ChatHistory.created_at.desc())
        .all()
    )

    return [
        {
            "id": chat.id,
            "question": chat.question,
            "answer": chat.answer,
            "created_at": chat.created_at.strftime("%d-%m-%Y %I:%M %p") if chat.created_at else ""
        }
        for chat in chats
    ]


@router.delete("/delete/{chat_id}")
def delete_chat_api(
    chat_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return delete_chat(
        db=db,
        chat_id=chat_id,
        user_id=current_user.id
    )