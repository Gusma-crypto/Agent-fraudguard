import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from .config import Settings
from .context import CaseFact, FactSource, SessionContext, SessionStore, ToolRecord
from .core_client import CoreClient, CoreError
from .guardrails import InputGuard, OutputGuard
from .localization import detect_language, text
from .models import ActionExecution, ChatResponse, ConversationState
from .reasoning import DeterministicPlanner, Intent, candidate_facts
from .tools import ToolRegistry

FRAUD_ACTIONS = {
    "REVIEW": "FRAUD_MANUAL_REVIEW",
    "STEP_UP_VERIFY": "FRAUD_STEP_UP_VERIFICATION",
    "TEMPORARY_HOLD": "FRAUD_HOLD_ESCALATION",
}

# These fields authorize one non-idempotent intervention response. They may shape the
# current plan, but must never become implicit input on a later conversation turn.
ONE_SHOT_CONTEXT_KEYS = frozenset({"intervention_result", "intervention_status"})


def extract_core_decision(data: dict[str, Any]) -> dict[str, Any]:
    policy = data.get("policy") if isinstance(data.get("policy"), dict) else {}
    risk = data.get("risk") if isinstance(data.get("risk"), dict) else {}
    score = data.get("score", risk.get("score"))
    return {
        "decision": data.get("decision") or policy.get("decision"),
        "severity": data.get("severity") or risk.get("severity"),
        "score": int(score) if isinstance(score, (int, float)) else None,
        "reason_codes": list(data.get("reason_codes") or policy.get("reason_codes") or []),
    }


def explain(
    decision: dict[str, Any], data: dict[str, Any], language: str
) -> tuple[str, ConversationState]:
    value = decision.get("decision")
    if value == "TEMPORARY_HOLD":
        return text("hold", language), ConversationState.ESCALATED
    if value == "STEP_UP_VERIFY":
        suffix = text("verify_suffix", language) if data.get("intervention_id") else ""
        return (
            text("verify", language, suffix=suffix),
            ConversationState.ACTION_REQUIRED,
        )
    if value == "REVIEW":
        return text("review", language), ConversationState.ACTION_REQUIRED
    if value == "ALLOW":
        return text("allow", language), ConversationState.RESOLVED
    if data.get("status"):
        return text("status", language, status=data["status"]), ConversationState.EXPLAINING
    return text("generic_result", language), ConversationState.EXPLAINING


class AgentRuntime:
    def __init__(
        self,
        settings: Settings,
        sessions: SessionStore,
        core: CoreClient,
    ) -> None:
        self.settings = settings
        self.sessions = sessions
        self.core = core
        self.planner = DeterministicPlanner()
        self.tools = ToolRegistry(core)
        self.input_guard = InputGuard()
        self.output_guard = OutputGuard(
            (settings.fraudguard_core_api_key, settings.agent_access_key)
        )

    async def chat(
        self,
        session: SessionContext,
        message: str,
        supplied_context: dict[str, Any],
    ) -> ChatResponse:
        language_hint = supplied_context.get("language", supplied_context.get("locale"))
        session.language = detect_language(message, language_hint)
        session.turn_count += 1
        session.state = ConversationState.UNDERSTANDING
        if session.turn_count > self.settings.agent_max_turns:
            session.state = ConversationState.ESCALATED
            return self._response(
                session,
                text("turn_limit", session.language),
            )
        guard = self.input_guard.check(message, session.language)
        if not guard.allowed:
            session.state = ConversationState.BLOCKED
            return self._response(session, guard.response)

        for key, value in supplied_context.items():
            if key in {"language", "locale"}:
                continue
            session.known_facts[key] = CaseFact(value=value, source=FactSource.USER_CLAIM)
        for key, value in candidate_facts(message).items():
            session.known_facts[key] = CaseFact(value=value, source=FactSource.AGENT_INFERENCE)
        merged = {key: fact.value for key, fact in session.known_facts.items()}
        plan = self.planner.plan(message, merged)
        for key in ONE_SHOT_CONTEXT_KEYS:
            session.known_facts.pop(key, None)
        session.intent = plan.intent.value
        session.missing_facts = plan.missing_information

        if plan.missing_information:
            session.state = ConversationState.COLLECTING_CONTEXT
            fields = ", ".join(plan.missing_information)
            return self._response(
                session,
                text("missing", session.language, fields=fields),
                selected_skill=plan.selected_skill,
            )
        if plan.selected_tool is None:
            session.state = ConversationState.EXPLAINING
            message_out = text(
                "education" if plan.intent == Intent.FRAUD_EDUCATION else "clarify",
                session.language,
            )
            return self._response(
                session, message_out, selected_skill=plan.selected_skill
            )
        if self.settings.agent_max_tool_steps < 1:
            session.state = ConversationState.ESCALATED
            return self._response(session, text("budget_empty", session.language))

        session.state = ConversationState.ANALYZING
        try:
            result = await self.tools.execute(plan.selected_tool, plan.arguments, session.trace_id)
        except CoreError:
            session.state = ConversationState.ESCALATED
            return self._response(
                session,
                text("core_failed", session.language),
                selected_skill=plan.selected_skill,
                tool_calls=[plan.selected_tool],
            )

        data = result["data"]
        result_digest = hashlib.sha256(
            json.dumps(data, sort_keys=True, default=str).encode()
        ).hexdigest()
        if any(
            record.name == plan.selected_tool and record.result_digest == result_digest
            for record in session.tool_history[-2:]
        ):
            session.state = ConversationState.ESCALATED
            return self._response(
                session,
                text("loop", session.language),
                selected_skill=plan.selected_skill,
                tool_calls=[plan.selected_tool],
            )
        session.trace_id = result["trace_id"]
        session.tool_step_count += 1
        session.tool_history.append(
            ToolRecord(
                name=plan.selected_tool,
                trace_id=session.trace_id,
                outcome="success",
                result_digest=result_digest,
            )
        )
        decision = extract_core_decision(data)
        if decision.get("decision"):
            session.last_core_decision = decision
            for key, value in decision.items():
                session.known_facts[f"core_{key}"] = CaseFact(
                    value=value, source=FactSource.CORE_FACT
                )
        tool_calls = [plan.selected_tool]
        actions: list[ActionExecution] = []
        action_type = FRAUD_ACTIONS.get(str(decision.get("decision")))
        if plan.selected_tool == "fraud_analyze" and action_type:
            if len(tool_calls) >= self.settings.agent_max_tool_steps:
                session.state = ConversationState.ESCALATED
                return self._response(
                    session,
                    text("budget_exhausted", session.language),
                    selected_skill=plan.selected_skill,
                    tool_calls=tool_calls,
                    decision=decision,
                )
            action_arguments = {
                "payment_check_id": None,
                "type": action_type,
                "channel": session.channel.upper(),
                "verification_context": {
                    "assessment_id": data.get("id"),
                    "policy_decision_id": (
                        data.get("policy", {}).get("id")
                        if isinstance(data.get("policy"), dict)
                        else None
                    ),
                    "decision": decision["decision"],
                    "reason_codes": decision["reason_codes"],
                },
            }
            try:
                action_result = await self.tools.execute(
                    "create_intervention", action_arguments, session.trace_id
                )
            except (CoreError, ValueError):
                session.state = ConversationState.ESCALATED
                return self._response(
                    session,
                    text("action_failed", session.language),
                    selected_skill=plan.selected_skill,
                    tool_calls=[*tool_calls, "create_intervention"],
                    decision=decision,
                    actions=[ActionExecution(action=action_type, status="FAILED")],
                )
            action_data = action_result["data"]
            action_digest = hashlib.sha256(
                json.dumps(action_data, sort_keys=True, default=str).encode()
            ).hexdigest()
            session.trace_id = action_result["trace_id"]
            session.tool_step_count += 1
            session.tool_history.append(
                ToolRecord(
                    name="create_intervention",
                    trace_id=session.trace_id,
                    outcome="success",
                    result_digest=action_digest,
                )
            )
            tool_calls.append("create_intervention")
            actions.append(
                ActionExecution(
                    action=action_type,
                    status=str(action_data.get("status", "PENDING")),
                    resource_id=(
                        str(action_data["id"]) if action_data.get("id") is not None else None
                    ),
                )
            )
            data = {**data, "intervention_id": action_data.get("id")}
        response_message, state = explain(decision, data, session.language)
        if actions:
            response_message += text("action_recorded", session.language)
        session.state = state
        return self._response(
            session,
            response_message,
            selected_skill=plan.selected_skill,
            tool_calls=tool_calls,
            decision=decision,
            actions=actions,
        )

    def _response(
        self,
        session: SessionContext,
        message: str,
        *,
        selected_skill: str | None = None,
        tool_calls: list[str] | None = None,
        decision: dict[str, Any] | None = None,
        actions: list[ActionExecution] | None = None,
    ) -> ChatResponse:
        session.updated_at = datetime.now(UTC)
        values = decision or {}
        return ChatResponse(
            message=self.output_guard.sanitize(message),
            language=session.language,
            session_id=session.session_id,
            trace_id=session.trace_id,
            state=session.state,
            intent=session.intent,
            selected_skill=selected_skill,
            tool_calls=tool_calls or [],
            decision=values.get("decision"),
            severity=values.get("severity"),
            score=values.get("score"),
            reason_codes=values.get("reason_codes", []),
            actions=actions or [],
        )
