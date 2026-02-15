from __future__ import annotations

import uvicorn
from fastapi import FastAPI

from app.db import Base, engine
from app.routers.auth import router as auth_router
from app.routers.lobbies import router as lobbies_router


def create_app() -> FastAPI:
    app = FastAPI(title="Open Table RPG")

    @app.on_event("startup")
    def _startup() -> None:
        Base.metadata.create_all(bind=engine)

    app.include_router(auth_router)
    app.include_router(lobbies_router)
    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True, workers=1)
