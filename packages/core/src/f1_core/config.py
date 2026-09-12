from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "F1 Race Intelligence AI"

    env: str = "local"
    debug: bool = False
    log_level: str = "INFO"

    api_v1_prefix: str = "/api/v1"

    # NOVO
    api_host: str = "localhost"
    api_port: int = 8000

    @property
    def api_base_url(self) -> str:
        return f"http://{self.api_host}:{self.api_port}"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()