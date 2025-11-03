from pydantic import BaseModel, EmailStr

class LoginRequest(BaseModel):
    """Запрос на вход по адресу электронной почты и паролю."""
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    """Ответ с access-токеном и временем его жизни."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int