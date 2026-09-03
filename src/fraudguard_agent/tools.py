import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .core_client import CoreClient
from .models import PaymentInput


class FraudInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    context: dict[str, Any] = Field(default_factory=dict)
    event_id: uuid.UUID | None = None


class AssessmentInput(FraudInput):
    assessment_type: str = Field(default="fraud", min_length=1, max_length=100)


class EventInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    external_id: str | None = Field(default=None, max_length=255)
    event_type: str = Field(min_length=1, max_length=100)
    source: str = Field(min_length=1, max_length=100)
    occurred_at: datetime
    payload: dict[str, Any] = Field(default_factory=dict)
    context: dict[str, Any] = Field(default_factory=dict)


class InterventionInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    payment_check_id: uuid.UUID | None = None
    type: str = Field(min_length=1, max_length=100)
    channel: str = Field(min_length=1, max_length=50)
    verification_context: dict[str, Any] = Field(default_factory=dict)


class InterventionResponseInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    intervention_id: uuid.UUID
    result: dict[str, Any]
    status: str = Field(pattern=r"^(COMPLETED|FAILED|CANCELLED)$")


class IdentifierInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    incident_id: uuid.UUID


class TraceInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    trace_id: uuid.UUID


class CapabilityInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=100, pattern=r"^[a-z0-9-]+$")


class IntelligenceInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query: str = Field(min_length=3, max_length=2000)
    entity_type: str | None = Field(
        default=None,
        pattern=r"^(PHONE|BANK_ACCOUNT|DOMAIN|URL|EMAIL|USERNAME|BRAND|MESSAGE)$",
    )
    deep_search: bool = False
    context: dict[str, Any] = Field(default_factory=dict)


Executor = Callable[[dict[str, Any], str | None], Awaitable[dict[str, Any]]]


@dataclass(frozen=True, slots=True)
class ToolDefinition:
    name: str
    description: str
    input_model: type[BaseModel]
    required_scope: str
    side_effect: bool
    protected_action: bool
    idempotency_required: bool
    executor: Executor


class ToolRegistry:
    def __init__(self, core: CoreClient) -> None:
        self.tools = {
            item.name: item
            for item in (
                ToolDefinition(
                    "fraud_analyze",
                    "Analyze suspected fraud through Core",
                    FraudInput,
                    "fraud:analyze",
                    True,
                    False,
                    False,
                    core.fraud_analyze,
                ),
                ToolDefinition(
                    "create_assessment",
                    "Create a typed assessment through Core",
                    AssessmentInput,
                    "assessments:write",
                    True,
                    False,
                    False,
                    core.create_assessment,
                ),
                ToolDefinition(
                    "ingest_event",
                    "Ingest a security event through Core",
                    EventInput,
                    "events:write",
                    True,
                    False,
                    True,
                    core.ingest_event,
                ),
                ToolDefinition(
                    "safety_payment",
                    "Check a payment through Core policy",
                    PaymentInput,
                    "payments:check",
                    True,
                    True,
                    True,
                    core.safety_payment,
                ),
                ToolDefinition(
                    "create_intervention",
                    "Create an approved intervention through Core",
                    InterventionInput,
                    "interventions:write",
                    True,
                    True,
                    True,
                    core.create_intervention,
                ),
                ToolDefinition(
                    "submit_intervention_response",
                    "Submit an intervention response to Core",
                    InterventionResponseInput,
                    "interventions:write",
                    True,
                    True,
                    False,
                    core.submit_intervention_response,
                ),
                ToolDefinition(
                    "get_incident",
                    "Read an incident from Core",
                    IdentifierInput,
                    "incidents:read",
                    False,
                    False,
                    False,
                    core.get_incident,
                ),
                ToolDefinition(
                    "get_trace",
                    "Read a trace from Core",
                    TraceInput,
                    "traces:read",
                    False,
                    False,
                    False,
                    core.get_trace,
                ),
                ToolDefinition(
                    "get_trace_audit",
                    "Read authoritative trace audit from Core",
                    TraceInput,
                    "audit:read",
                    False,
                    False,
                    False,
                    core.get_trace_audit,
                ),
                ToolDefinition(
                    "intelligence_lookup",
                    "Search tenant-scoped intelligence through Core",
                    IntelligenceInput,
                    "intelligence:search",
                    True,
                    False,
                    False,
                    core.intelligence_lookup,
                ),
                ToolDefinition(
                    "get_capability",
                    "Read a capability contract from Core",
                    CapabilityInput,
                    "capabilities:read",
                    False,
                    False,
                    False,
                    core.get_capability,
                ),
            )
        }

    async def execute(
        self, name: str, arguments: dict[str, Any], trace_id: str | None
    ) -> dict[str, Any]:
        definition = self.tools.get(name)
        if definition is None:
            raise ValueError(f"Tool is not allowlisted: {name}")
        validated = definition.input_model.model_validate(arguments).model_dump(mode="json")
        return await definition.executor(validated, trace_id)
