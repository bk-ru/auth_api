from typing import Optional
from pydantic import BaseModel


class PermissionResponse(BaseModel):
    """Возвращает код права и его описание."""
    code: str
    description: Optional[str]

    class Config:
        from_attributes = True