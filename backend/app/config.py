from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str

    anthropic_api_key: str
    claude_model: str = "claude-sonnet-5"

    encryption_key: str
    jwt_secret: str

    smtp_host: str
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_address: str
    smtp_use_tls: bool = True

    frontend_origin: str = "http://localhost:5173"

    poll_interval_minutes: int = 3
    magic_link_ttl_minutes: int = 15
    session_ttl_days: int = 30
    digest_daily_hour: int = 8
    digest_weekly_day: str = "mon"
    digest_weekly_hour: int = 8

    cookie_secure: bool = True
    disable_scheduler: bool = False


settings = Settings()
