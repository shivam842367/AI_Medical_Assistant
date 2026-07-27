from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User
from app.schemas.user import UserLogin
from app.auth.password import verify_password
from app.utils.jwt import create_access_token


def login_user(db: Session, data: UserLogin):

    user = db.query(User).filter(
        User.email == data.email
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Email or Password"
        )

    is_valid = verify_password(
        data.password,
        user.hashed_password
    )

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Email or Password"
        )

    access_token = create_access_token(
        {"sub": user.email}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }