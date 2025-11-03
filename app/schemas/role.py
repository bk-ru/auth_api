from typing import Optional, Sequence
from pydantic import BaseModel, Field
from .permission import PermissionResponse

class RoleResponse(BaseModel):
    """Представление роли и набора связанных разрешений."""
    id: int
    name: str
    description: Optional[str]
    permissions: Sequence[PermissionResponse]
    
    class Config:
        from_attributes = True

class RoleUpdateRequest(BaseModel):
    """Частичное обновление роли и её разрешений."""
    name: Optional[str] = Field(None, min_length=2, max_length=50)
    description: Optional[str] = Field(None, max_length=255)
    permission_codes: Optional[list[str]] = None


class RoleCreateRequest(BaseModel):
    """Создание новой роли с набором разрешений."""
    name: str = Field(..., min_length=2, max_length=50)
    description: Optional[str] = Field(None, max_length=255)
    permission_codes: list[str] = Field(default_factory=list)