"""Маршруты для управления профилем и пользователями."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..dependencies import get_current_session, get_db, require_permissions
from ..models import AccessToken, User
from ..schemas import UserAdminUpdate, UserProfile, UserSelfUpdate
from ..services import (
    get_roles_by_ids,
    get_user_with_roles,
    list_users,
    serialize_user,
    soft_delete_user,
    update_user,
)

router = APIRouter()


@router.get("/me", response_model=UserProfile)
def get_profile(
    session_data: tuple[User, AccessToken] = Depends(get_current_session),
    db: Session = Depends(get_db),
):
    """Возвращает профиль текущего пользователя вместе с ролями."""

    user, _ = session_data
    db_user = get_user_with_roles(db, user.id)
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return serialize_user(db_user)


@router.patch("/me", response_model=UserProfile)
def update_profile(
    payload: UserSelfUpdate,
    session_data: tuple[User, AccessToken] = Depends(get_current_session),
    db: Session = Depends(get_db),
):
    """Позволяет пользователю обновить собственные данные."""

    user, _ = session_data
    db_user = get_user_with_roles(db, user.id)
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    updates = payload.model_dump(exclude_unset=True)
    update_user(db, db_user, updates)
    db.commit()
    db.refresh(db_user)
    return serialize_user(db_user)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_self(
    session_data: tuple[User, AccessToken] = Depends(get_current_session),
    db: Session = Depends(get_db),
):
    """Деактивирует учётную запись пользователя и отзывает его токены."""

    user, _ = session_data
    db_user = get_user_with_roles(db, user.id)
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    soft_delete_user(db, db_user)
    db.commit()
    return None


@router.get(
    "",
    response_model=list[UserProfile],
    dependencies=[Depends(require_permissions("view_users"))],
)
def list_all_users(db: Session = Depends(get_db)):
    """Возвращает список всех пользователей (требует право `view_users`)."""

    users = list_users(db)
    return [serialize_user(user) for user in users]


@router.patch(
    "/{user_id}",
    response_model=UserProfile,
    dependencies=[Depends(require_permissions("manage_users"))],
)
def admin_update_user(user_id: int, payload: UserAdminUpdate, db: Session = Depends(get_db)):
    """Позволяет администратору обновить данные пользователя и его роли."""

    user = get_user_with_roles(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    updates = payload.model_dump(exclude_unset=True)
    role_ids: list[int] | None = updates.pop("role_ids", None)  # type: ignore[assignment]

    update_user(db, user, updates)

    if role_ids is not None:
        roles = get_roles_by_ids(db, role_ids)
        found_ids = {role.id for role in roles}
        missing_ids = sorted({role_id for role_id in role_ids if role_id not in found_ids})
        if missing_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown role ids: {', '.join(map(str, missing_ids))}",
            )
        user.roles = roles

    db.commit()
    db.refresh(user)
    return serialize_user(user)
