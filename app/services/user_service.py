from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User
from app.schemas.user import UserRegister
from app.auth.password import hash_password


def register_user(db: Session, data: UserRegister):

    # Check if email already exists
    old_user = db.query(User).filter(User.email == data.email).first()

    if old_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create new user
    new_user = User(
        full_name=data.full_name,
        email=data.email,
        hashed_password=hash_password(data.password)
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user