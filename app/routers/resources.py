"""Имитационные ресурсы бизнес-домена для проверки механизма разрешений."""
from fastapi import APIRouter, Depends
from ..dependencies import require_permissions

router = APIRouter()

@router.get("/projects", dependencies=[Depends(require_permissions("view_projects"))])
def list_projects():
    """Возвращает демонстрационный список проектов."""

    return [
        {"id": 1, "name": "Unified Access Platform", "owner": "Infrastructure"},
        {"id": 2, "name": "Analytics Warehouse", "owner": "Data Office"},
    ]

@router.post("/projects", dependencies=[Depends(require_permissions("edit_projects"))])
def create_project():
    """Имитация создания проекта."""

    return {"detail": "Project creation simulated."}

@router.get("/reports", dependencies=[Depends(require_permissions("view_reports"))])
def list_reports():
    """Возвращает демонстрационный список отчётов."""

    return [
        {"code": "FIN-Q4", "title": "Financial Overview Q4"},
        {"code": "HR-ENG", "title": "Employee Engagement Report"},
    ]