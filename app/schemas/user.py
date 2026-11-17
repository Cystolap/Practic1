from pydantic import BaseModel, EmailStr, Field
from typing import Literal


class UserCreate(BaseModel):
    email: EmailStr = Field(..., description="Email пользователя")
    password: str = Field(..., min_length=6, description="Пароль (мин. 6 символов)")
    role: Literal["admin", "master", "client"] = Field(default="client", description="Роль")


class UserRead(BaseModel):
    id: int
    email: EmailStr
    role: str

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
