from functools import lru_cache

from pydantic import Field, model_validator
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

    @property
    def production(self) -> bool:
        return self.app_env.lower() == "production"

    @property
    def cors_origins(self) -> list[str]:
        return [value.strip() for value in self.agent_cors_origins.split(",") if value.strip()]

    @model_validator(mode="after")
    def validate_production(self) -> "Settings":
        if self.production:
            if not self.fraudguard_core_base_url.startswith("https://"):
                raise ValueError("FRAUDGUARD_CORE_BASE_URL must use HTTPS in production")
            if not self.fraudguard_core_api_key:
                raise ValueError("FRAUDGUARD_CORE_API_KEY is required in production")
            if not self.agent_access_key:
                raise ValueError("AGENT_ACCESS_KEY is required in production")
        if self.agent_model_provider != "deterministic":
            raise ValueError("Only the deterministic provider is configured in this deployment")
        if self.agent_replicas > 1:
            raise ValueError(
                "Horizontal scaling requires a shared Redis session store; in-memory sessions "
                "support one replica only"
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
