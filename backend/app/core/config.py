from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db: str = "agrisense"
    jwt_secret: str = "development-only-secret-change-before-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_minutes: int = 60
    model_storage_path: str = "./ml/saved_models"

    @field_validator("mongodb_uri")
    @classmethod
    def mongodb_uri_must_not_be_blank(cls, value: str) -> str:
        return value.strip() or "mongodb://localhost:27017"

    @field_validator("jwt_secret")
    @classmethod
    def jwt_secret_must_not_be_blank(cls, value: str) -> str:
        return value.strip() or "development-only-secret-change-before-production"

    model_config = SettingsConfigDict(
        env_file=[".env", "../.env"],
        extra="ignore",
    )


settings = Settings()
