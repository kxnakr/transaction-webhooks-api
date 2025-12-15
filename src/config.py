from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    APP_NAME: str = "wfg-transaction-webhooks-api"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_POOL_PRE_PING: bool = False
    DATABASE_POOL_RECYCLE: int = 600
    DATABASE_POOL_TIMEOUT: int = 30

    # Redis
    REDIS_URL: str

    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def REDIS_CONNECTION_URL(self) -> str:
        """Return broker/backend URL."""
        return self.REDIS_URL


settings = Settings()
