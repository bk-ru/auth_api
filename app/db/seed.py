"""Скрипт заполнения БД демонстрационными данными."""
from sqlalchemy import select
from ..core.config import get_settings
from ..core.security import hash_password
from ..db.session import Base, engine, session_scope
from ..models import Permission, Role, User

def seed_permissions(session) -> None:
    permissions = [
        ("manage_users", "Create, update, and deactivate users."),
        ("view_users", "View user directory."),
        ("manage_roles", "Manage role definitions and permissions."),
        ("view_projects", "Access project catalogue."),
        ("edit_projects", "Modify project records."),
        ("view_reports", "Access analytical reports."),
    ]

    for code, description in permissions:
        exists = session.execute(select(Permission).where(Permission.code == code)).scalar_one_or_none()
        if exists is None:
            session.add(Permission(code=code, description=description))

def seed_roles(session) -> None:
    role_matrix = {
        "admin": {
            "description": "Full administrative access.",
            "permissions": [
                "manage_users",
                "view_users",
                "manage_roles",
                "view_projects",
                "edit_projects",
                "view_reports",
            ],
        },
        "manager": {
            "description": "Manage and review projects.",
            "permissions": ["view_users", "view_projects", "edit_projects", "view_reports"],
        },
        "analyst": {
            "description": "View analytics only.",
            "permissions": ["view_projects", "view_reports"],
        },
        "basic_user": {
            "description": "Default role for newly registered users.",
            "permissions": ["view_projects"],
        },
    }

    for role_name, config in role_matrix.items():
        role = (
            session.execute(select(Role).where(Role.name == role_name)).unique().scalar_one_or_none()
        )
        if role is None:
            role = Role(name=role_name, description=config["description"])
            session.add(role)
            session.flush()

        perms = session.execute(
            select(Permission).filter(Permission.code.in_(config["permissions"]))
        ).scalars().all()
        role.permissions = list(perms)

def seed_admin_user(session) -> None:
    settings = get_settings()

    admin_user = session.execute(
        select(User).where(User.email == settings.seed_admin_email)
    ).unique().scalar_one_or_none()
    admin_role = (
        session.execute(select(Role).where(Role.name == "admin")).unique().scalar_one()
    )

    if admin_user is None:
        admin_user = User(
            first_name="System",
            last_name="Administrator",
            patronymic=None,
            email=settings.seed_admin_email,
            password_hash=hash_password(settings.seed_admin_password),
            is_active=True,
        )
        admin_user.roles = [admin_role]
        session.add(admin_user)
    elif admin_role not in admin_user.roles:
        admin_user.roles.append(admin_role)


def run_seed() -> None:
    Base.metadata.create_all(bind=engine)
    with session_scope() as session:
        seed_permissions(session)
        seed_roles(session)
        seed_admin_user(session)

if __name__ == "__main__":
    run_seed()