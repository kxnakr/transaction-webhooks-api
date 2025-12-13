from urllib.parse import quote
from pydantic_settings import BaseSettings

def _build_upstash_connection_link(*, host: str, port: int, password: str) -> str:
    encoded_password = quote(password, safe="")
    return f"rediss://:{encoded_password}@{host}:{port}?ssl_cert_reqs=required"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    APP_NAME: str = "wfg-transaction-webhooks-api"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # Redis (Upstash)
    UPSTASH_REDIS_HOST: str
    UPSTASH_REDIS_PORT: int
    UPSTASH_REDIS_PASSWORD: str

    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def UPSTASH_REDIS_CONNECTION_LINK(self) -> str:
        return _build_upstash_connection_link(
            host=self.UPSTASH_REDIS_HOST,
            port=self.UPSTASH_REDIS_PORT,
            password=self.UPSTASH_REDIS_PASSWORD,
        )


settings = Settings()
