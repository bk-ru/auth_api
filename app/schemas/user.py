"""Pydantic-схемы для данных пользователя."""
from datetime import datetime
from typing import Optional, Sequence
from pydantic import BaseModel, EmailStr, Field, model_validator

class UserBase(BaseModel):
    """Базовый набор полей профиля пользователя."""
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    patronymic: Optional[str] = Field(None, max_length=50)


class UserCreate(UserBase):
    """Схема регистрации с повторным вводом пароля."""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    password_confirm: str = Field(..., min_length=8, max_length=128)

    @model_validator(mode="after")
    def passwords_match(cls, model: "UserCreate") -> "UserCreate":
        if model.password != model.password_confirm:
            raise ValueError("Passwords do not match.")
        return model

class UserUpdate(BaseModel):
    """Административное обновление профиля."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    patronymic: Optional[str] = Field(None, max_length=50)
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None

class UserSelfUpdate(BaseModel):
    """Изменение профиля самим пользователем."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    patronymic: Optional[str] = Field(None, max_length=50)
    email: Optional[EmailStr] = None

class UserAdminUpdate(UserUpdate):
    """Дополнительно позволяет управлять ролями пользователя."""
    role_ids: Optional[list[int]] = None

class UserProfile(UserBase):
    """Ответ с данными пользователя и назначенными ролями."""
    id: int
    email: EmailStr
    is_active: bool
    roles: Sequence[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True