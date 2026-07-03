from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- App ---
    APP_NAME: str = "PolicyPilot"
    ENV: str = "development"

    # --- Database ---
    DATABASE_URL: str = "postgresql://policypilot:policypilot@localhost:5432/policypilot"

    # --- Auth / JWT ---
    JWT_SECRET_KEY: str = "change-me-in-.env-this-is-not-safe-for-prod"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 14

    # --- Redis / Celery (used from Phase 4 onward) ---
    REDIS_URL: str = "redis://localhost:6379/0"

    # --- Vector store / LLM (used from Phase 2 onward) ---
    QDRANT_URL: str = "http://localhost:6333"
    GROQ_API_KEY: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
