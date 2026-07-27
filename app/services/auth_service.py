from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app.models.user import User
from app.schemas.user import UserLogin
from app.utils.jwt import create_access_token
try:
    from fastapi import HTTPException, status
except ImportError:
    class status:
        HTTP_401_UNAUTHORIZED = 401
    class HTTPException(Exception):
        def __init__(self, status_code: int = 401, detail: str = ""):
            self.status_code = status_code
            self.detail = detail
            super().__init__(detail)

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


def login_user(db: Session, data: UserLogin):

    print("Email entered:", data.email)

    user = db.query(User).filter(
        User.email == data.email
    ).first()

    print("User found:", user)


    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Email or Password"
        )

    print("Stored Hash:", user.hashed_password)

    is_valid = pwd_context.verify(
        data.password,
        user.hashed_password
    )

    print("Password Match:", is_valid)

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