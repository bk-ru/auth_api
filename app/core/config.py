from functools import lru_cache
from pydantic import AnyUrl
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Определяет конфигурационные параметры, считываемые из окружения."""
    app_name: str = "Custom Auth Service"
    environment: str = "development"
    debug: bool = True
    database_url: str = "postgresql+psycopg://auth_user:auth_pass@localhost:5432/auth_db"

    access_token_expire_minutes: int = 60
    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"

    seed_admin_email: str = "admin@example.com"
    seed_admin_password: str = "Admin123!"

    class Config:
        env_file = ".env"

@lru_cache
def get_settings() -> Settings:
    return Settings()
