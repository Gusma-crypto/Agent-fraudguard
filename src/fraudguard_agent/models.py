import uuid
from decimal import Decimal
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

SENSITIVE_KEYS = {
    "accesstoken",
    "apikey",
    "authtoken",
    "bearertoken",
    "clientsecret",
    "cvv",
    "onetimepassword",
    "otp",
    "password",
    "pin",
    "recoveryphrase",
    "refreshtoken",
    "secretkey",
    "seedphrase",
}


def reject_sensitive_fields(value: object) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            normalized = "".join(char for char in str(key).lower() if char.isalnum())
            if normalized in SENSITIVE_KEYS:
                raise ValueError(f"sensitive credential field is not accepted: {key}")
            reject_sensitive_fields(nested)
    elif isinstance(value, list):
        for nested in value:
            reject_sensitive_fields(nested)


class ConversationState(StrEnum):
    NEW = "NEW"
    UNDERSTANDING = "UNDERSTANDING"
    COLLECTING_CONTEXT = "COLLECTING_CONTEXT"
    ANALYZING = "ANALYZING"
    ACTION_REQUIRED = "ACTION_REQUIRED"
    EXPLAINING = "EXPLAINING"
    RESOLVED = "RESOLVED"
    ESCALATED = "ESCALATED"
    BLOCKED = "BLOCKED"


class SessionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    channel: Literal["web", "api", "openclaw", "mobile", "telegram", "whatsapp"] = "web"


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    session_id: uuid.UUID | None = None
    message: str = Field(min_length=1, max_length=10_000)
    context: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def reject_credentials(self) -> "ChatRequest":
        reject_sensitive_fields(self.context)
        forbidden_authority = {"tenant_id", "application_id"}.intersection(self.context)
        if forbidden_authority:
            raise ValueError("tenant/application authority cannot come from chat context")
        return self


class ToolExecutionRequest(BaseModel):
    """Direct bounded tool invocation for OpenClaw skills.

    This endpoint bypasses the native planner; OpenClaw owns orchestration.
    """

    model_config = ConfigDict(extra="forbid")
    arguments: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def reject_credentials(self) -> "ToolExecutionRequest":
        reject_sensitive_fields(self.arguments)
        return self


class PaymentInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    external_payment_id: str = Field(min_length=1, max_length=255)
    amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2)
    currency: str = Field(min_length=3, max_length=3)
    sender_ref: str | None = Field(default=None, max_length=255)
    recipient_ref: str = Field(min_length=1, max_length=255)
    recipient_is_new: bool = False
    context: dict[str, Any] = Field(default_factory=dict)

    @field_validator("currency")
    @classmethod
    def currency_code(cls, value: str) -> str:
        if not value.isalpha():
            raise ValueError("currency must be an ISO 4217 alpha code")
        return value.upper()

    @model_validator(mode="after")
    def reject_credentials(self) -> "PaymentInput":
        reject_sensitive_fields(self.context)
        return self


class ActionExecution(BaseModel):
    action: str
    status: str
    resource_id: str | None = None


class ChatResponse(BaseModel):
    message: str
    language: str
    session_id: uuid.UUID
    trace_id: str | None = None
    state: ConversationState
    intent: str
    selected_skill: str | None = None
    tool_calls: list[str] = Field(default_factory=list)
    decision: str | None = None
    severity: str | None = None
    score: int | None = None
    reason_codes: list[str] = Field(default_factory=list)
    actions: list[ActionExecution] = Field(default_factory=list)
    intelligence: dict[str, Any] | None = None


class SessionView(BaseModel):
    session_id: uuid.UUID
    state: ConversationState
    intent: str
    trace_id: str | None
    language: str
    turn_count: int
    tool_step_count: int
    created_at: str
    updated_at: str
