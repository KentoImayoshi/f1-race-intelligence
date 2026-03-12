from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "F1 Race Intelligence AI"
    env: str = "local"

    class Config:
        env_file = ".env"


settings = Settings()
