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


def test_in_memory_sessions_reject_horizontal_scaling() -> None:
    with pytest.raises(ValueError, match="shared Redis session store"):
        Settings(agent_replicas=2)
