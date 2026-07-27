from app.utils.auth import get_current_user
from app.models.user import User
from app.schemas.user import UserRegister, UserResponse, UserLogin, Token
from app.services.auth_service import login_user
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.services.user_service import register_user

router = APIRouter(prefix="/user", tags=["User"])


@router.post("/register", response_model=UserResponse)
def register(data: UserRegister, db: Session = Depends(get_db)):
    return register_user(db, data)


from fastapi.security import OAuth2PasswordRequestForm

@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    data = UserLogin(
        email=form_data.username,
        password=form_data.password
    )
    return login_user(db, data)

@router.get("/me", response_model=UserResponse)
def get_profile(current_user: User = Depends(get_current_user)):
    return current_user