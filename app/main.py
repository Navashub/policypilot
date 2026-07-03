from fastapi import FastAPI

from app.auth.routes import router as auth_router
from app.core.config import settings
from app.documents.routes import router as documents_router

app = FastAPI(title=settings.APP_NAME)

app.include_router(auth_router)
app.include_router(documents_router)


@app.get("/health")
def health():
    return {"status": "alive", "env": settings.ENV}


# NOTE: table creation is handled by Alembic migrations (see /migrations),
# not by Base.metadata.create_all — that's the "real product" version of
# what main.py did in the course project. Run `alembic upgrade head`
# after the database is up (docker-compose handles this for local dev).
