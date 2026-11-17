from sqlalchemy.orm import Session
from app.models import User
from app.schemas.user import UserCreate
from app.auth import hash_password, verify_password


def register_user(db: Session, user_data: UserCreate):
    # Проверяем существование юзера
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        return None

        # Хешируем пароли
    new_user = User(
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        role=user_data.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def authenticate_user(db: Session, email: str, password: str):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user