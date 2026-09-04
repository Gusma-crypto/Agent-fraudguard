from functools import lru_cache

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    fraudguard_core_base_url: str = "http://host.docker.internal:8080/api/v1"
    fraudguard_core_api_key: str = ""
    agent_access_key: str = ""
    agent_runtime: str = "native"
    agent_model_provider: str = "deterministic"
    agent_model: str = "fraudguard-rules-v1"
    agent_temperature: float = Field(default=0, ge=0, le=2)
    agent_max_tool_steps: int = Field(default=8, ge=1, le=20)
    agent_max_turns: int = Field(default=20, ge=1, le=100)
    agent_core_timeout_seconds: float = Field(default=10, gt=0, le=60)
    agent_session_ttl_seconds: int = Field(default=3600, ge=60, le=86_400)
    agent_replicas: int = Field(default=1, ge=1, le=20)
    agent_cors_origins: str = "http://localhost:3000"
    openclaw_gateway_url: str = "http://host.docker.internal:18789"
    openclaw_gateway_token: str = ""
    openclaw_agent_id: str = "fraudguard"
    openclaw_timeout_seconds: float = Field(default=60, gt=0, le=180)
    telegram_enabled: bool = False
    telegram_bot_token: SecretStr = SecretStr("")
    telegram_webhook_secret: SecretStr = SecretStr("")
    telegram_subject_hmac_key: SecretStr = SecretStr("")
    telegram_bot_username: str = ""
    telegram_consent_policy_version: str = "telegram-consent-v1"
    telegram_rate_limit_per_minute: int = Field(default=10, ge=1, le=60)

    @property
    def production(self) -> bool:
        return self.app_env.lower() == "production"

    @property
    def cors_origins(self) -> list[str]:
        return [value.strip() for value in self.agent_cors_origins.split(",") if value.strip()]

    @model_validator(mode="after")
    def validate_production(self) -> "Settings":
        if self.production:
            internal_core = self.fraudguard_core_base_url.startswith(
                "http://fraudguard-core-api:"
            )
            if not self.fraudguard_core_base_url.startswith("https://") and not internal_core:
                raise ValueError(
                    "FRAUDGUARD_CORE_BASE_URL must use HTTPS or the private "
                    "fraudguard-core-api Docker hostname in production"
                )
            if not self.fraudguard_core_api_key:
                raise ValueError("FRAUDGUARD_CORE_API_KEY is required in production")
            if not self.agent_access_key:
                raise ValueError("AGENT_ACCESS_KEY is required in production")
        if self.agent_model_provider != "deterministic":
            raise ValueError("Only the deterministic provider is configured in this deployment")
        if self.agent_runtime == "openclaw" and self.production and not self.openclaw_gateway_token:
            raise ValueError("OPENCLAW_GATEWAY_TOKEN is required for the OpenClaw bridge")
        if self.telegram_enabled:
            secret_values = {
                "TELEGRAM_BOT_TOKEN": self.telegram_bot_token.get_secret_value(),
                "TELEGRAM_WEBHOOK_SECRET": self.telegram_webhook_secret.get_secret_value(),
                "TELEGRAM_SUBJECT_HMAC_KEY": self.telegram_subject_hmac_key.get_secret_value(),
            }
            missing = [name for name, value in secret_values.items() if not value]
            if missing:
                raise ValueError(f"Telegram integration requires: {', '.join(missing)}")
            if len(secret_values["TELEGRAM_WEBHOOK_SECRET"].encode()) < 32:
                raise ValueError("TELEGRAM_WEBHOOK_SECRET must contain at least 32 bytes")
            if len(secret_values["TELEGRAM_SUBJECT_HMAC_KEY"].encode()) < 32:
                raise ValueError("TELEGRAM_SUBJECT_HMAC_KEY must contain at least 32 bytes")
            if not self.telegram_bot_username:
                raise ValueError("TELEGRAM_BOT_USERNAME is required when Telegram is enabled")
        if self.agent_replicas > 1:
            raise ValueError(
                "Horizontal scaling requires a shared Redis session store; in-memory sessions "
                "support one replica only"
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
