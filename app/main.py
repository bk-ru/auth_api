from fastapi import FastAPI
from .internal import admin as internal_admin
from .routers import auth, resources, users

def create_app() -> FastAPI:
    app = FastAPI(title="Custom Auth Service")
    app.include_router(auth.router, prefix="/auth", tags=["auth"])
    app.include_router(users.router, prefix="/users", tags=["users"])
    app.include_router(resources.router, prefix="/resources", tags=["resources"])
    app.include_router(internal_admin.router)

    return app

app = create_app()
