import re
from dataclasses import dataclass

from .localization import text

INJECTION_PATTERNS = (
    r"ignore (all |the )?(previous|prior) instructions",
    r"abaikan (semua )?instruksi (sebelumnya|di atas)",
    r"reveal (your |the )?(api key|secret|system prompt)",
    r"tampilkan (api key|rahasia|system prompt)",
    r"call this url",
    r"approve (this |the )?(transaction|payment)",
    r"setujui (transaksi|pembayaran)",
)
SECRET_VALUE = re.compile(
    r"\b(?:otp|pin|cvv)\s*[:=]?\s*\d{3,8}\b|"
    r"\b(?:password|kata\s+sandi)\s*[:=]\s*\S+",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class GuardResult:
    allowed: bool
    response: str = ""


class InputGuard:
    def check(self, message: str, language: str = "en") -> GuardResult:
        lowered = message.lower()
        if any(re.search(pattern, lowered) for pattern in INJECTION_PATTERNS):
            return GuardResult(False, text("blocked", language))
        if SECRET_VALUE.search(message):
            return GuardResult(False, text("secret", language))
        return GuardResult(True)


class OutputGuard:
    def __init__(self, secrets: tuple[str, ...]) -> None:
        self.secrets = tuple(value for value in secrets if value)

    def sanitize(self, message: str) -> str:
        safe = message
        for value in self.secrets:
            safe = safe.replace(value, "[REDACTED]")
        replacements = {
            "100% aman": "berisiko rendah berdasarkan analisis saat ini",
            "100% safe": "low risk based on the current analysis",
            "100% selamat": "berisiko rendah berdasarkan analisis semasa",
        }
        for claim, replacement in replacements.items():
            safe = safe.replace(claim, replacement)
        return safe
