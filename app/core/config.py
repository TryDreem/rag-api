from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    GROQ_API_KEY: str
    REDIS_URL: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"


    model_config = SettingsConfigDict(
            env_file=".env",
            case_sensitive=True
        )

settings = Settings()
