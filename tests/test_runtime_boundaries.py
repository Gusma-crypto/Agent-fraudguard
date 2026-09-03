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


def test_phishing_otp_journey_extracts_chain_and_uses_url_skill() -> None:
    planner = DeterministicPlanner()

    plan = planner.plan(
        "Dia mengirim link, suruh isi formulir, lalu dapat OTP dan disuruh klik link",
        {},
    )

    assert plan.selected_skill == "malicious-url"
    assert plan.selected_tool == "fraud_analyze"
    assert plan.arguments["context"] == {
        "suspicious_url": True,
        "third_party_instruction": True,
        "credential_request": True,
        "link_click_instruction": True,
    }


def test_marketplace_prize_transfer_extracts_social_engineering_chain() -> None:
    planner = DeterministicPlanner()

    plan = planner.plan(
        "Telepon mengaku dari Shopee, saya dapat hadiah bila transfer dan harus ikuti instruksi",
        {},
    )

    assert plan.selected_skill == "social-engineering"
    assert plan.arguments["context"]["impersonation"] is True
    assert plan.arguments["context"]["authority_impersonation"] is True
    assert plan.arguments["context"]["prize_scam"] is True
    assert plan.arguments["context"]["payment_request"] is True
    assert plan.arguments["context"]["remote_guidance"] is True


def test_explicit_intelligence_lookup_routes_to_bounded_core_tool() -> None:
    planner = DeterministicPlanner()

    plan = planner.plan(
        "Cek nomor ini",
        {
            "intelligence_query": "0812-3456-7890",
            "entity_type": "PHONE",
            "deep_search": True,
        },
    )

    assert plan.intent is Intent.INTELLIGENCE_SEARCH
    assert plan.selected_tool == "intelligence_lookup"
    assert plan.arguments == {
        "query": "0812-3456-7890",
        "entity_type": "PHONE",
        "deep_search": True,
        "context": {},
    }


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
