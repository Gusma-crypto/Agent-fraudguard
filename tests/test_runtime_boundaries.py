import pytest

from fraudguard_agent.config import Settings
from fraudguard_agent.reasoning import DeterministicPlanner, Intent, candidate_facts


def test_multilingual_fraud_terms_route_to_analysis() -> None:
    planner = DeterministicPlanner()

    for message in ("Esto parece una estafa urgente", "C'est une arnaque", "Das ist Betrug"):
        plan = planner.plan(message, {})
        assert plan.intent is Intent.FRAUD_ANALYSIS


def test_multilingual_payment_claims_extract_candidate_facts() -> None:
    facts = candidate_facts("Me dijeron que debo transferir dinero a una cuenta segura ahora")

    assert facts["payment_request"] is True
    assert facts["safe_account_narrative"] is True
    assert facts["urgent"] is True


@pytest.mark.parametrize(
    "message",
    (
        "Ini ada WhatsApp minta OTP",
        "Petugas meminta kode OTP saya",
        "A bank officer asked for my OTP",
        "Please share your password",
    ),
)
def test_credential_request_routes_to_fraud_analysis_without_secret_value(
    message: str,
) -> None:
    planner = DeterministicPlanner()

    plan = planner.plan(message, {})

    assert plan.intent is Intent.FRAUD_ANALYSIS
    assert plan.selected_tool == "fraud_analyze"
    assert plan.arguments["context"]["credential_request"] is True
    assert "otp" not in plan.arguments["context"]


def test_in_memory_sessions_reject_horizontal_scaling() -> None:
    with pytest.raises(ValueError, match="shared Redis session store"):
        Settings(agent_replicas=2)


def test_explicit_audit_request_wins_over_stale_intervention_context() -> None:
    planner = DeterministicPlanner()
    trace_id = "00000000-0000-0000-0000-000000000001"

    plan = planner.plan(
        "Tampilkan audit untuk trace ini",
        {
            "trace_id": trace_id,
            "intervention_id": "00000000-0000-0000-0000-000000000002",
            "intervention_result": {"third_party_instruction_confirmed": True},
            "intervention_status": "COMPLETED",
        },
    )

    assert plan.intent is Intent.TRACE_LOOKUP
    assert plan.selected_tool == "get_trace_audit"
    assert plan.arguments == {"trace_id": trace_id}
