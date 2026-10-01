from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    jwt_secret: SecretStr
    demo_username: str = "reviewer"
    demo_password_hash: SecretStr
    ollama_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen3:4b"
    groq_api_key: SecretStr = SecretStr("")
    groq_model: str = "llama-3.3-70b-versatile"
    allow_cloud_fallback: bool = False
    requests_per_minute: int = Field(default=10, ge=1)
    daily_request_limit: int = Field(default=100, ge=1)
    inference_timeout: float = Field(default=90, gt=0)
    max_concurrent: int = Field(default=1, ge=1)

    @field_validator("jwt_secret")
    @classmethod
    def strong_secret(cls, value: SecretStr) -> SecretStr:
        if len(value.get_secret_value()) < 32 or "replace-with" in value.get_secret_value():
            raise ValueError("Generate a private JWT secret with scripts/setup_local.py")
        return value

    @field_validator("demo_password_hash")
    @classmethod
    def password_hash(cls, value: SecretStr) -> SecretStr:
        if not value.get_secret_value().startswith("$argon2id$"):
            raise ValueError("DEMO_PASSWORD_HASH must be an Argon2id hash")
        return value
