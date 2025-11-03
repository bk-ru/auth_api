"""Внутренние маршруты для управления ролями и разрешениями."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..dependencies import get_db, require_permissions
from ..models import Role
from ..schemas import PermissionResponse, RoleCreateRequest, RoleResponse, RoleUpdateRequest
from ..services import (
    create_role,
    delete_role,
    get_permissions_by_codes,
    list_permissions,
    list_roles,
    update_role,
)

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get(
    "/permissions",
    response_model=list[PermissionResponse],
    dependencies=[Depends(require_permissions("manage_roles"))],
)
def list_permissions_view(db: Session = Depends(get_db)):
    """Возвращает перечень разрешений для административного интерфейса."""

    permissions = list_permissions(db)
    return [PermissionResponse.model_validate(permission) for permission in permissions]

@router.get(
    "/roles",
    response_model=list[RoleResponse],
    dependencies=[Depends(require_permissions("manage_roles"))],
)
def list_roles_view(db: Session = Depends(get_db)):
    """Возвращает роли вместе с привязанными правами."""

    roles = list_roles(db)
    return [RoleResponse.model_validate(role) for role in roles]

@router.post(
    "/roles",
    response_model=RoleResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permissions("manage_roles"))],
)
def create_role_view(payload: RoleCreateRequest, db: Session = Depends(get_db)):
    """Создаёт новую роль после проверки списка разрешений."""

    permissions = get_permissions_by_codes(db, payload.permission_codes)
    missing = set(payload.permission_codes) - {perm.code for perm in permissions}
    if missing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown permission codes: {', '.join(sorted(missing))}",
        )

    role = create_role(
        db,
        name=payload.name,
        description=payload.description,
        permissions=permissions,
    )
    db.commit()
    db.refresh(role)
    return RoleResponse.model_validate(role)

@router.patch(
    "/roles/{role_id}",
    response_model=RoleResponse,
    dependencies=[Depends(require_permissions("manage_roles"))],
)
def update_role_view(role_id: int, payload: RoleUpdateRequest, db: Session = Depends(get_db)):
    """Обновляет параметры роли и назначенные права."""

    role = db.get(Role, role_id)
    if role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found.")

    updates = payload.model_dump(exclude_unset=True)
    permission_codes = updates.pop("permission_codes", None)

    permissions = None
    if permission_codes is not None:
        permissions = get_permissions_by_codes(db, permission_codes)
        missing = set(permission_codes) - {perm.code for perm in permissions}
        if missing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown permission codes: {', '.join(sorted(missing))}",
            )

    update_role(
        db,
        role,
        name=updates.get("name"),
        description=updates.get("description"),
        permissions=permissions,
    )
    db.commit()
    db.refresh(role)
    return RoleResponse.model_validate(role)


@router.delete(
    "/roles/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permissions("manage_roles"))],
)
def delete_role_view(role_id: int, db: Session = Depends(get_db)):
    """Удаляет роль, кроме системной `admin`."""

    role = db.get(Role, role_id)
    if role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found.")
    if role.name == "admin":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete admin role.")

    delete_role(db, role)
    db.commit()
    return None