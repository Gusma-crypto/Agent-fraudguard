import pytest
from pydantic import ValidationError

from fraudguard_agent.config import Settings
from fraudguard_agent.models import ChatRequest, ToolExecutionRequest


def test_openclaw_bridge_defaults_to_isolated_fraudguard_agent() -> None:
    assert Settings().openclaw_agent_id == "fraudguard"


def test_chat_rejects_secret_fields() -> None:
    with pytest.raises(ValidationError, match="sensitive credential"):
        ChatRequest(message="cek", context={"otp": "123456"})


def test_chat_rejects_tenant_authority_from_user() -> None:
    with pytest.raises(ValidationError, match="authority"):
        ChatRequest(message="cek", context={"tenant_id": "other-tenant"})


def test_direct_tool_request_rejects_secret_fields() -> None:
    with pytest.raises(ValidationError, match="sensitive credential"):
        ToolExecutionRequest(arguments={"recipient": {"pin": "123456"}})
