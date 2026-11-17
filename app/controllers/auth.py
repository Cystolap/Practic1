from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.user import UserCreate, UserRead, UserLogin, Token
from app.services.auth_service import register_user, authenticate_user
from app.auth import create_token, decode_token
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter()
oauth2_scheme = HTTPBearer()


# Регистрация
@router.post("/register", response_model=UserRead, status_code=201, summary="Регистрация")
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    user = register_user(db, user_data)
    if not user:
        raise HTTPException(status_code=400, detail="Email уже занят")
    return user


# Вход
@router.post("/login", response_model=Token, summary="Вход в систему")
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, user_data.email, user_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Неверный email или пароль")

    
    token = create_token(user_id=user.id, email=user.email, role=user.role)
    return {"access_token": token, "token_type": "bearer"}


#Проверка токена 
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme)):
    token = credentials.credentials
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невалидный или просроченный токен",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Возвращаем данные, которые были зашиты в токен
    return {
        "id": int(payload.get("sub")),
        "email": payload.get("email"),
        "role": payload.get("role")
    }


# Проверка прав
def require_role(allowed_roles: list[str]):
    def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user["role"] not in allowed_roles:
            raise HTTPException(status_code=403, detail="Недостаточно прав (403 Forbidden)")
        return current_user

    return role_checker


# Проверка себя
@router.get("/me", summary="Получить данные о себе")
def read_users_me(current_user: dict = Depends(get_current_user)):
    return current_user

# Выход 
@router.post("/logout", summary="Выход из системы")
def logout(current_user: dict = Depends(get_current_user)):
    return {"message": "Успешный выход. Удалите токен на клиенте."}