from enum import StrEnum
from typing import Any, Protocol

from pydantic import BaseModel, Field


class Intent(StrEnum):
    FRAUD_ANALYSIS = "possible_scam"
    PAYMENT_SAFETY = "payment_safety"
    INTERVENTION_RESPONSE = "intervention_response"
    INCIDENT_LOOKUP = "incident_lookup"
    TRACE_LOOKUP = "trace_lookup"
    FRAUD_EDUCATION = "fraud_education"
    UNKNOWN = "unknown"


class Plan(BaseModel):
    intent: Intent
    missing_information: list[str] = Field(default_factory=list)
    selected_skill: str | None = None
    selected_tool: str | None = None
    arguments: dict[str, Any] = Field(default_factory=dict)
    rationale: str


class ReasoningProvider(Protocol):
    def plan(self, message: str, context: dict[str, Any]) -> Plan: ...


def candidate_facts(message: str) -> dict[str, bool]:
    text = message.lower()
    groups = {
        "impersonation": (
            "petugas bank", "bank officer", "bank employee", "pegawai bank", "polisi",
            "police", "polis", "courier", "kurir", "mengaku", "pretending",
            "banco", "policía", "policia", "police officer", "banque", "beamter",
        ),
        "urgent": (
            "segera", "sekarang", "mendesak", "urgent", "immediately", "now",
            "urgente", "ahora", "maintenant", "sofort",
        ),
        "safe_account_narrative": (
            "rekening aman", "safe account", "akaun selamat", "cuenta segura",
            "compte sécurisé", "sicheres konto",
        ),
        "payment_request": (
            "transfer", "kirim uang", "send money", "bayar", "pindahan", "hantar wang",
            "transferir", "enviar dinero", "pagar", "virement", "überweisen",
        ),
        "suspicious_url": (
            "http://", "https://", "tautan", "link", "pautan", "enlace", "lien",
            "link senden",
        ),
        "third_party_instruction": (
            "disuruh", "diminta", "instruksi", "instructed", "asked me", "arahan",
            "me dijeron", "me pidió", "on m'a demandé", "aufgefordert",
        ),
        "credential_request": (
            "minta otp", "meminta otp", "minta kode otp", "meminta kode otp",
            "kirim otp", "berikan otp", "minta pin", "meminta pin", "minta cvv",
            "meminta cvv", "minta password", "meminta password", "minta kata sandi",
            "meminta kata sandi", "asked for my otp", "asked me for otp",
            "send your otp", "share your otp", "give me your otp",
            "asked for my pin", "asked for my password", "share your password",
        ),
    }
    return {key: True for key, terms in groups.items() if any(term in text for term in terms)}


class DeterministicPlanner:
    fraud_terms = (
        "penipuan", "scam", "fraud", "ditipu", "mencurigakan", "suspicious",
        "phishing", "estafa", "fraude", "sospechoso", "arnaque", "betrug",
        "verdächtig",
    )

    def plan(self, message: str, context: dict[str, Any]) -> Plan:
        text = message.lower()
        if context.get("trace_id") and ("trace" in text or "audit" in text):
            return Plan(
                intent=Intent.TRACE_LOOKUP,
                selected_skill="case-investigation",
                selected_tool="get_trace_audit" if "audit" in text else "get_trace",
                arguments={"trace_id": context["trace_id"]},
                rationale="Riwayat authoritative harus dibaca dari Core.",
            )
        if context.get("intervention_id") and context.get("intervention_result"):
            return Plan(
                intent=Intent.INTERVENTION_RESPONSE,
                selected_skill="realtime-intervention",
                selected_tool="submit_intervention_response",
                arguments={
                    "intervention_id": context["intervention_id"],
                    "result": context["intervention_result"],
                    "status": context.get("intervention_status", "COMPLETED"),
                },
                rationale="Respons verifikasi harus dicatat oleh Core.",
            )
        if context.get("incident_id"):
            return Plan(
                intent=Intent.INCIDENT_LOOKUP,
                selected_skill="case-investigation",
                selected_tool="get_incident",
                arguments={"incident_id": context["incident_id"]},
                rationale="Status insiden authoritative berada di Core.",
            )
        payment_fields = {"external_payment_id", "amount", "currency", "recipient_ref"}
        if payment_fields.intersection(context):
            missing = sorted(payment_fields - set(context))
            if missing:
                return Plan(
                    intent=Intent.PAYMENT_SAFETY,
                    missing_information=missing,
                    selected_skill="safety-payment",
                    rationale="Data pembayaran non-sensitif belum lengkap.",
                )
            arguments = {key: context[key] for key in payment_fields}
            arguments.update(
                sender_ref=context.get("sender_ref"),
                recipient_is_new=bool(context.get("recipient_is_new", False)),
                context=context.get("fraud_context", {}),
            )
            return Plan(
                intent=Intent.PAYMENT_SAFETY,
                selected_skill="safety-payment",
                selected_tool="safety_payment",
                arguments=arguments,
                rationale="Policy pembayaran harus ditentukan oleh Core.",
            )
        facts = candidate_facts(message)
        if facts or any(term in text for term in self.fraud_terms):
            core_context = {**context, **facts}
            return Plan(
                intent=Intent.FRAUD_ANALYSIS,
                selected_skill="fraud-detection",
                selected_tool="fraud_analyze",
                arguments={"context": core_context},
                rationale="Narasi memiliki kandidat indikator yang perlu dinilai Core.",
            )
        if any(
            term in text
            for term in (
                "apa itu", "bagaimana", "tips", "edukasi", "what is", "how to",
                "education", "apakah itu", "bagaimana untuk",
            )
        ):
            return Plan(
                intent=Intent.FRAUD_EDUCATION,
                selected_skill="fraud-detection",
                rationale="Pertanyaan edukasi tidak memerlukan tool Core.",
            )
        return Plan(
            intent=Intent.UNKNOWN,
            missing_information=["jenis kejadian atau tujuan pemeriksaan"],
            rationale="Tujuan percakapan belum cukup jelas.",
        )
