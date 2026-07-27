from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserRegister
from app.auth.password import hash_password
from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

def register_user(db: Session, data: UserRegister):

    # Check if email already exists
    old_user = db.query(User).filter(User.email == data.email).first()

    if old_user:
        return {
            "id": old_user.id,
            "full_name": old_user.full_name,
            "email": old_user.email
        }

    # Create new user
    new_user = User(
        full_name=data.full_name,
        email=data.email,
        hashed_password=pwd_context.hash(data.password)
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user