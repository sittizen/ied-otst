from __future__ import annotations

from fastapi import FastAPI

from app.db import Base, engine
from app.routers.auth import router as auth_router


def create_app() -> FastAPI:
    app = FastAPI(title="Open Table RPG")

    @app.on_event("startup")
    def _startup() -> None:
        Base.metadata.create_all(bind=engine)

    app.include_router(auth_router)
    return app


app = create_app()
