from typing import Any

SUPPORTED_LANGUAGES = {"en", "id", "ms"}

LANGUAGE_MARKERS = {
    "id": {
        "anda",
        "apakah",
        "dengan",
        "dia",
        "disuruh",
        "hadiah",
        "ini",
        "jangan",
        "mengirim",
        "rekening",
        "saya",
        "suruh",
        "telepon",
        "tolong",
    },
    "ms": {
        "akaun",
        "anda",
        "dengan",
        "jangan",
        "pautan",
        "pemindahan",
        "saya",
        "tolong",
    },
}

MESSAGES = {
    "en": {
        "action_failed": (
            "Core analysis completed, but the protective action could not be recorded. "
            "The workflow was stopped and requires manual handling."
        ),
        "action_recorded": (
            " The protective action was recorded in Core; this does not execute or "
            "cancel a transaction in an external system."
        ),
        "allow": (
            "Core currently indicates low risk. This is not an absolute guarantee; "
            "verify the party and transaction purpose independently."
        ),
        "blocked": (
            "I cannot follow instructions that take over the agent, expose secrets, "
            "or approve a transaction."
        ),
        "budget_empty": "No execution budget is available; the action was stopped.",
        "budget_exhausted": (
            "Core requires a protective action, but the execution budget is exhausted. "
            "No action was taken and the case must be escalated."
        ),
        "clarify": (
            "Please clarify whether you want to check a suspicious message, payment, "
            "intervention, incident, or audit trace."
        ),
        "core_failed": (
            "Core is unavailable or rejected the request. I cannot declare this action "
            "safe; the protected workflow was stopped."
        ),
        "education": (
            "Watch for pressure to act quickly, impersonation of trusted parties, "
            "transfer requests, and unknown links. Verify through an official channel."
        ),
        "generic_result": "An authoritative result was received from Core.",
        "hold": (
            "Do not continue the current action. Core set a temporary hold and the case "
            "must be escalated."
        ),
        "loop": "The tool returned the same result repeatedly; the loop was stopped.",
        "phishing_stop": (
            " Close the page, do not use or share any OTP, and contact the provider "
            "through an independently located official channel."
        ),
        "social_stop": (
            " End the call and stop the transfer. Contact the claimed company through "
            "its official app, site, or a number you find independently."
        ),
        "missing": (
            "I need the following non-sensitive information: {fields}. Do not send a "
            "password, PIN, OTP, or CVV."
        ),
        "review": (
            "Core requires this case to be reviewed. Do not take a risky action until "
            "verification is complete."
        ),
        "secret": "Do not send a password, PIN, OTP, or CVV. FraudGuard does not need it.",
        "status": "Authoritative status from Core: {status}.",
        "turn_limit": "The conversation limit was reached. Start a new session or escalate.",
        "verify": "Core requires additional verification before continuing.{suffix}",
        "verify_suffix": " A verification intervention was created by Core.",
    },
    "id": {
        "action_failed": (
            "Analisis Core selesai, tetapi tindakan protektif tidak berhasil dicatat. "
            "Workflow dihentikan dan harus ditangani manual."
        ),
        "action_recorded": (
            " Tindakan protektif telah dicatat di Core; ini tidak mengeksekusi atau "
            "membatalkan transaksi pada sistem eksternal."
        ),
        "allow": (
            "Analisis Core saat ini menunjukkan risiko rendah. Ini bukan jaminan "
            "mutlak; tetap verifikasi pihak dan tujuan transaksi."
        ),
        "blocked": (
            "Saya tidak dapat mengikuti instruksi yang mengambil alih agent, membuka "
            "rahasia, atau menyetujui transaksi."
        ),
        "budget_empty": "Execution budget tidak tersedia; tindakan dihentikan.",
        "budget_exhausted": (
            "Core menetapkan tindakan protektif, tetapi execution budget habis. "
            "Tindakan tidak dijalankan dan kasus harus dieskalasikan."
        ),
        "clarify": (
            "Jelaskan apakah Anda ingin memeriksa pesan mencurigakan, pembayaran, "
            "intervensi, insiden, atau audit trace."
        ),
        "core_failed": (
            "Core tidak tersedia atau menolak permintaan. Saya tidak dapat menyatakan "
            "tindakan ini aman; protected workflow dihentikan."
        ),
        "education": (
            "Waspadai tekanan untuk bertindak cepat, penyamaran sebagai pihak resmi, "
            "permintaan transfer, dan tautan tidak dikenal. Verifikasi melalui kanal resmi."
        ),
        "generic_result": "Hasil authoritative berhasil diperoleh dari Core.",
        "hold": (
            "Jangan lanjutkan tindakan saat ini. Core menetapkan penahanan sementara "
            "dan kasus perlu dieskalasikan."
        ),
        "loop": "Tool mengembalikan hasil yang sama berulang kali; loop dihentikan.",
        "phishing_stop": (
            " Tutup halaman, jangan gunakan atau bagikan OTP, lalu hubungi penyedia "
            "melalui kanal resmi yang Anda cari sendiri."
        ),
        "social_stop": (
            " Akhiri telepon dan hentikan transfer. Hubungi perusahaan yang diklaim "
            "melalui aplikasi, situs, atau nomor resmi yang Anda cari sendiri."
        ),
        "missing": (
            "Saya memerlukan informasi non-sensitif berikut: {fields}. Jangan kirim "
            "password, PIN, OTP, atau CVV."
        ),
        "review": (
            "Core menetapkan bahwa kasus ini perlu ditinjau. Jangan mengambil tindakan "
            "berisiko sampai verifikasi selesai."
        ),
        "secret": "Jangan kirim password, PIN, OTP, atau CVV. FraudGuard tidak memerlukannya.",
        "status": "Status authoritative dari Core: {status}.",
        "turn_limit": "Batas percakapan tercapai. Silakan mulai sesi baru atau eskalasikan kasus.",
        "verify": "Core meminta verifikasi tambahan sebelum tindakan dilanjutkan.{suffix}",
        "verify_suffix": " Intervensi verifikasi telah dibuat oleh Core.",
    },
    "ms": {
        "action_failed": (
            "Analisis Core selesai, tetapi tindakan perlindungan tidak dapat direkodkan. "
            "Aliran kerja dihentikan dan memerlukan pengendalian manual."
        ),
        "action_recorded": (
            " Tindakan perlindungan telah direkodkan dalam Core; ini tidak melaksanakan "
            "atau membatalkan transaksi pada sistem luaran."
        ),
        "allow": (
            "Analisis Core kini menunjukkan risiko rendah. Ini bukan jaminan mutlak; "
            "sahkan pihak dan tujuan transaksi."
        ),
        "blocked": (
            "Saya tidak boleh mengikuti arahan yang mengambil alih ejen, mendedahkan "
            "rahsia, atau meluluskan transaksi."
        ),
        "budget_empty": "Tiada bajet pelaksanaan tersedia; tindakan dihentikan.",
        "budget_exhausted": (
            "Core memerlukan tindakan perlindungan, tetapi bajet pelaksanaan telah habis. "
            "Tiada tindakan diambil dan kes mesti dieskalasikan."
        ),
        "clarify": (
            "Jelaskan sama ada anda mahu menyemak mesej mencurigakan, pembayaran, "
            "intervensi, insiden, atau jejak audit."
        ),
        "core_failed": (
            "Core tidak tersedia atau menolak permintaan. Saya tidak boleh menyatakan "
            "tindakan ini selamat; aliran kerja dilindungi dihentikan."
        ),
        "education": (
            "Berwaspada terhadap tekanan untuk bertindak segera, penyamaran pihak "
            "dipercayai, permintaan pindahan, dan pautan tidak dikenali. Sahkan melalui "
            "saluran rasmi."
        ),
        "generic_result": "Keputusan berautoriti telah diterima daripada Core.",
        "hold": (
            "Jangan teruskan tindakan semasa. Core menetapkan penahanan sementara dan "
            "kes mesti dieskalasikan."
        ),
        "loop": "Tool mengembalikan keputusan sama berulang kali; gelung dihentikan.",
        "phishing_stop": (
            " Tutup halaman, jangan gunakan atau kongsi OTP, kemudian hubungi penyedia "
            "melalui saluran rasmi yang anda cari sendiri."
        ),
        "social_stop": (
            " Tamatkan panggilan dan hentikan pindahan. Hubungi syarikat melalui aplikasi, "
            "laman, atau nombor rasmi yang anda cari sendiri."
        ),
        "missing": (
            "Saya memerlukan maklumat bukan sensitif berikut: {fields}. Jangan hantar "
            "kata laluan, PIN, OTP, atau CVV."
        ),
        "review": (
            "Core menetapkan kes ini perlu disemak. Jangan ambil tindakan berisiko "
            "sehingga pengesahan selesai."
        ),
        "secret": "Jangan hantar kata laluan, PIN, OTP, atau CVV. FraudGuard tidak memerlukannya.",
        "status": "Status berautoriti daripada Core: {status}.",
        "turn_limit": "Had perbualan telah dicapai. Mulakan sesi baharu atau eskalasikan kes.",
        "verify": "Core memerlukan pengesahan tambahan sebelum meneruskan.{suffix}",
        "verify_suffix": " Intervensi pengesahan telah dibuat oleh Core.",
    },
}


def normalize_language(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    primary = value.strip().lower().replace("_", "-").split("-", 1)[0]
    return primary if primary in SUPPORTED_LANGUAGES else None


def detect_language(message: str, hint: object = None) -> str:
    if normalized := normalize_language(hint):
        return normalized
    words = {word.strip(".,!?;:()[]{}\"'") for word in message.lower().split()}
    scores = {
        language: len(words.intersection(markers))
        for language, markers in LANGUAGE_MARKERS.items()
    }
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "en"


def text(key: str, language: str, **values: Any) -> str:
    messages = MESSAGES.get(language, MESSAGES["en"])
    return messages[key].format(**values)
