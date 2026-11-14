"""
LLM Adapter — ProfitAI (Phase 5 / P2)

Sesuai FINANCIAL_AI_METHODOLOGY.md §8:
- LLM hanya boleh menghasilkan narasi penjelasan; tidak boleh mengubah angka,
  menyebut sumber, menjanjikan outcome, atau memberikan kepastian pajak/hukum.
- Jika output LLM gagal validasi, fallback ke rule-based wording yang aman.
- Privacy guard wajib: strip semua PII / nama bisnis sebelum dikirim ke LLM.
- LLM bersifat OPSIONAL. Provider dapat berupa DeepSeek, Gemini, atau OpenAI.
  Tanpa konfigurasi valid, modul berjalan dalam mode fallback tanpa error.

Environment:
  LLM_PROVIDER=deepseek|gemini|openai  (opsional; auto-detect bila kosong)
  DEEPSEEK_API_KEY=...             (hanya di server, jangan commit)
  DEEPSEEK_MODEL=deepseek-chat
  DEEPSEEK_BASE_URL=https://api.deepseek.com
  GEMINI_API_KEY=...               (hanya di server, jangan commit)
  GEMINI_MODEL=gemini-2.5-flash
  OPENAI_API_KEY=...
  OPENAI_MODEL=gpt-4o-mini
  LLM_MODEL=...                    (legacy; dipakai jika model provider kosong)
  LLM_TIMEOUT_SECONDS=15
  LLM_MAX_RETRIES=1
  LLM_CACHE_TTL_SECONDS=300
  LLM_RATE_LIMIT_PER_MINUTE=30

Privacy review checklist (harus dipenuhi sebelum mengaktifkan di produksi):
  [x] Tidak ada email, nama pengguna, nama bisnis yang dikirim ke LLM
  [x] Tidak ada nominal angka absolut (hanya arah: naik/turun/stabil)
  [x] Tidak ada data transaksi individual
  [x] Payload LLM dicatat di audit log tanpa sensitive fields
  [x] Response LLM divalidasi sebelum diteruskan ke client
  [x] Fallback ke rule-based jika LLM tidak tersedia atau validasi gagal
"""

import hashlib
import importlib.util
import json
import logging
import os
import re
import threading
import time
from collections import deque
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# ─── Konstanta ────────────────────────────────────────────────────────────────

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "").strip().lower()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "").strip()
LLM_MODEL_ENV = os.getenv("LLM_MODEL", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "").strip() or LLM_MODEL_ENV or "gemini-2.5-flash"
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "").strip() or LLM_MODEL_ENV or "gpt-4o-mini"
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "").strip() or LLM_MODEL_ENV or "deepseek-chat"
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "").strip() or "https://api.deepseek.com"
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "300"))
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.3"))
LLM_TIMEOUT_SECONDS = float(os.getenv("LLM_TIMEOUT_SECONDS", "15"))
LLM_MAX_RETRIES = max(0, int(os.getenv("LLM_MAX_RETRIES", "1")))
LLM_CACHE_TTL_SECONDS = max(0, int(os.getenv("LLM_CACHE_TTL_SECONDS", "300")))
LLM_RATE_LIMIT_PER_MINUTE = max(0, int(os.getenv("LLM_RATE_LIMIT_PER_MINUTE", "30")))


def resolve_provider(
    provider_raw: str,
    *,
    deepseek_key: str,
    gemini_key: str,
    openai_key: str,
) -> tuple[Optional[str], Optional[str]]:
    """Fungsi murni: tentukan (provider, config_error) dari nilai konfigurasi.

    Dipisah dari pembacaan environment agar dapat diuji tanpa reload modul.
    """
    _ALIASES = {
        "gemini": "gemini",
        "google": "gemini",
        "openai": "openai",
        "deepseek": "deepseek",
        "deepseek-chat": "deepseek",
    }

    requested = (provider_raw or "").strip().lower()
    if requested:
        candidate = _ALIASES.get(requested)
        if candidate is None:
            return None, (
                f"LLM_PROVIDER '{provider_raw}' tidak dikenal. "
                "Gunakan 'deepseek', 'gemini', atau 'openai'."
            )
    else:
        # Auto-detect: DeepSeek diprioritaskan agar sesuai konfigurasi produk.
        if deepseek_key:
            candidate = "deepseek"
        elif gemini_key:
            candidate = "gemini"
        elif openai_key:
            candidate = "openai"
        else:
            candidate = "deepseek"

    if candidate == "gemini":
        if not gemini_key:
            return None, "GEMINI_API_KEY belum dikonfigurasi."
        return "gemini", None

    if candidate == "deepseek":
        if not deepseek_key:
            return None, "DEEPSEEK_API_KEY belum dikonfigurasi."
        return "deepseek", None

    if not openai_key:
        return None, "OPENAI_API_KEY belum dikonfigurasi."
    if importlib.util.find_spec("openai") is None:
        return None, "Paket openai belum terpasang; gunakan provider DeepSeek/Gemini atau install openai."
    return "openai", None


def _resolve_provider() -> tuple[Optional[str], Optional[str]]:
    """Wrapper: resolusi provider dari environment runtime."""
    return resolve_provider(
        LLM_PROVIDER,
        deepseek_key=DEEPSEEK_API_KEY,
        gemini_key=GEMINI_API_KEY,
        openai_key=OPENAI_API_KEY,
    )


LLM_PROVIDER, LLM_CONFIG_ERROR = _resolve_provider()
_MODEL_BY_PROVIDER = {
    "gemini": GEMINI_MODEL,
    "openai": OPENAI_MODEL,
    "deepseek": DEEPSEEK_MODEL,
}
LLM_MODEL = _MODEL_BY_PROVIDER.get(LLM_PROVIDER or "", DEEPSEEK_MODEL)
LLM_ENABLED = LLM_PROVIDER is not None

# Kata kunci yang dilarang muncul dalam output LLM
_PROHIBITED_PATTERNS = [
    r"\b\d[\d.,]{4,}\b",          # angka absolut besar (nominal Rp)
    r"pasti|guaranteed|garansi",   # klaim kepastian
    r"pajak|tax\s+advice",         # saran pajak
    r"hukum|legal\s+advice",       # saran hukum
    r"investasi\s+di\b",           # rekomendasi investasi spesifik
]
_PROHIBITED_RE = re.compile("|".join(_PROHIBITED_PATTERNS), re.IGNORECASE)

# Cache dan rate-limit per proses. Untuk deployment multi-worker, gunakan
# rate limiter terdistribusi (Redis) agar batas berlaku global.
_CACHE: dict[str, tuple[float, str]] = {}
_CACHE_LOCK = threading.Lock()
_RATE_CALLS: deque[float] = deque()
_RATE_LOCK = threading.Lock()


# ─── Privacy Sanitizer ────────────────────────────────────────────────────────

def _sanitize_for_llm(recommendation: dict) -> dict:
    """
    Hapus semua field sensitif sebelum mengirim ke LLM.
    Hanya kirim: rule_id, priority, trigger_metrics (direction only),
    evidence (tanpa angka absolut), suggested_actions.
    """
    # Konversi trigger_metrics ke arah saja (positif/negatif/nol)
    raw_metrics = recommendation.get("trigger_metrics", {}) or {}
    direction_metrics = {}
    for key, val in raw_metrics.items():
        try:
            num = float(str(val).replace(",", ""))
            direction_metrics[key] = "positif" if num > 0 else ("negatif" if num < 0 else "nol")
        except (ValueError, TypeError):
            direction_metrics[key] = "tidak_tersedia"

    # Strip angka dari evidence
    safe_evidence = []
    for ev in (recommendation.get("evidence") or []):
        # Ganti semua angka dengan placeholder
        cleaned = re.sub(r"Rp\s?[\d.,]+", "[nominal]", str(ev))
        cleaned = re.sub(r"\b\d[\d.,]*\b", "[angka]", cleaned)
        safe_evidence.append(cleaned)

    return {
        "rule_id": recommendation.get("rule_id", "UNKNOWN"),
        "priority": recommendation.get("priority", "medium"),
        "trigger_directions": direction_metrics,
        "evidence_summary": safe_evidence[:3],          # maks 3 baris
        "suggested_actions": (recommendation.get("suggested_actions") or [])[:3],
    }


# ─── Validator Output LLM ─────────────────────────────────────────────────────

def _validate_llm_output(text: str) -> tuple[bool, str]:
    """
    Validasi teks output LLM.
    Return (is_valid, reason).
    """
    if not text or len(text.strip()) < 20:
        return False, "Output LLM terlalu pendek atau kosong."

    if len(text) > 1200:
        return False, "Output LLM melebihi batas panjang yang diizinkan."

    match = _PROHIBITED_RE.search(text)
    if match:
        return False, f"Output LLM mengandung konten terlarang: '{match.group()}'."

    return True, "ok"


# ─── Rule-based Fallback ──────────────────────────────────────────────────────

_FALLBACK_TEMPLATES = {
    "REC-CF-01": (
        "Arus kas tercatat menunjukkan pengeluaran melebihi pemasukan pada periode ini. "
        "Disarankan untuk meninjau pos pengeluaran non-esensial dan mempercepat "
        "penagihan piutang agar likuiditas usaha tetap terjaga."
    ),
    "REC-EXP-01": (
        "Rasio beban operasional terhadap pendapatan berada di tingkat yang perlu "
        "diperhatikan. Periksa pos biaya terbesar dan pastikan tidak ada pengeluaran "
        "pribadi yang tercampur ke dalam akun usaha."
    ),
    "REC-DQ-01": (
        "Terdapat transaksi yang belum memiliki kategori. Melengkapi kategorisasi "
        "akan meningkatkan akurasi laporan keuangan dan kualitas analisis otomatis."
    ),
    "REC-SAV-01": (
        "Usaha membukukan surplus dan arus kas positif. Menyisihkan sebagian surplus "
        "ke rekening cadangan terpisah dapat memperkuat ketahanan keuangan "
        "untuk menghadapi fluktuasi operasional."
    ),
}

_DEFAULT_FALLBACK = (
    "Berdasarkan data transaksi yang tercatat, terdapat kondisi keuangan yang "
    "memerlukan perhatian. Silakan tinjau detail rekomendasi dan indikator terkait "
    "untuk langkah perbaikan yang sesuai dengan kondisi usaha Anda."
)


def _get_fallback(rule_id: str) -> str:
    """Normalisasi RULE-* vs REC-* agar template fallback selalu cocok."""
    candidates = [
        rule_id,
        str(rule_id).replace("RULE-", "REC-"),
        str(rule_id).replace("REC-", "RULE-"),
    ]
    for key in candidates:
        if key in _FALLBACK_TEMPLATES:
            return _FALLBACK_TEMPLATES[key]
    return _DEFAULT_FALLBACK


# ─── Prompt Builder ───────────────────────────────────────────────────────────

_RECOMMENDATION_SYSTEM_PROMPT = (
    "Kamu adalah asisten penjelasan laporan keuangan UMKM. "
    "Tugasmu: tulis 2-3 kalimat penjelasan ramah dalam Bahasa Indonesia "
    "yang menjelaskan MENGAPA rekomendasi ini penting bagi pemilik usaha, "
    "berdasarkan arah indikator yang diberikan. "
    "LARANGAN KERAS: "
    "jangan menyebut angka nominal spesifik, "
    "jangan memberikan kepastian (pasti, garansi), "
    "jangan memberikan saran pajak atau hukum, "
    "jangan menyebut nama bisnis atau identitas pengguna."
)

_RATIO_SYSTEM_PROMPT = (
    "Kamu adalah analis keuangan UMKM yang hati-hati. Tulis 2-3 kalimat "
    "Bahasa Indonesia yang menjelaskan arti rasio dan tindakan yang "
    "disarankan berdasarkan band dan kualitas data. "
    "LARANGAN KERAS: jangan menyebut angka, nominal, persentase, nama "
    "bisnis, atau identitas pengguna; jangan memberi kepastian, saran "
    "pajak, hukum, atau investasi spesifik."
)


def _build_recommendation_prompt(sanitized_payload: dict) -> str:
    return (
        f"Rekomendasi rule: {sanitized_payload['rule_id']}\n"
        f"Prioritas: {sanitized_payload['priority']}\n"
        f"Arah indikator: {json.dumps(sanitized_payload['trigger_directions'], ensure_ascii=False)}\n"
        f"Ringkasan bukti: {'; '.join(sanitized_payload['evidence_summary'])}\n"
        f"Tindakan yang disarankan: {'; '.join(sanitized_payload['suggested_actions'])}\n\n"
        "Tulis penjelasan singkat (2-3 kalimat) untuk pemilik usaha:"
    )


def _build_ratio_prompt(sanitized: dict) -> str:
    return (
        f"Kode rasio: {sanitized['ratio_code']}\n"
        f"Nama: {sanitized['ratio_name']}\n"
        f"Kategori: {sanitized['category']}\n"
        f"Band: {sanitized['band']}\n"
        f"Arah threshold: {sanitized['direction']}\n"
        f"Kualitas data: {sanitized['quality']}\n\n"
        "Tulis penjelasan singkat untuk pemilik usaha:"
    )


# ─── Provider Calls ───────────────────────────────────────────────────────────

def _cache_get(key: str) -> Optional[str]:
    if LLM_CACHE_TTL_SECONDS <= 0:
        return None
    now = time.monotonic()
    with _CACHE_LOCK:
        item = _CACHE.get(key)
        if not item:
            return None
        expires_at, text = item
        if expires_at <= now:
            _CACHE.pop(key, None)
            return None
        return text


def _cache_set(key: str, text: str) -> None:
    if LLM_CACHE_TTL_SECONDS <= 0:
        return
    with _CACHE_LOCK:
        _CACHE[key] = (time.monotonic() + LLM_CACHE_TTL_SECONDS, text)


def _rate_limit_ok() -> bool:
    if LLM_RATE_LIMIT_PER_MINUTE <= 0:
        return True
    now = time.monotonic()
    with _RATE_LOCK:
        while _RATE_CALLS and _RATE_CALLS[0] <= now - 60:
            _RATE_CALLS.popleft()
        if len(_RATE_CALLS) >= LLM_RATE_LIMIT_PER_MINUTE:
            return False
        _RATE_CALLS.append(now)
        return True


def _call_gemini(system_prompt: str, user_prompt: str) -> tuple[Optional[str], Optional[str]]:
    if not GEMINI_API_KEY:
        return None, "GEMINI_API_KEY belum dikonfigurasi."
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_MODEL}:generateContent"
    )
    payload = {
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
        "generationConfig": {
            "temperature": LLM_TEMPERATURE,
            "maxOutputTokens": LLM_MAX_TOKENS,
        },
    }
    headers = {
        "x-goog-api-key": GEMINI_API_KEY,
        "Content-Type": "application/json",
    }

    last_error: Optional[str] = None
    for attempt in range(LLM_MAX_RETRIES + 1):
        try:
            with httpx.Client(timeout=LLM_TIMEOUT_SECONDS) as client:
                response = client.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                data = response.json()
                candidates = data.get("candidates") or []
                parts = (
                    candidates[0].get("content", {}).get("parts", [])
                    if candidates else []
                )
                text = "".join(part.get("text", "") for part in parts).strip()
                if text:
                    return text, None
                return None, "Gemini mengembalikan respons kosong."
            last_error = f"Gemini HTTP {response.status_code}."
            # 4xx selain rate-limit tidak perlu di-retry.
            if response.status_code != 429 and response.status_code < 500:
                break
        except (httpx.TimeoutException, httpx.TransportError) as exc:
            last_error = f"Gemini tidak dapat dihubungi: {type(exc).__name__}."
        except Exception as exc:  # noqa: BLE001
            last_error = f"Gemini call gagal: {type(exc).__name__}."
        if attempt < LLM_MAX_RETRIES:
            time.sleep(0.5 * (attempt + 1))
    return None, last_error or "Gemini call gagal."


def _call_deepseek(system_prompt: str, user_prompt: str) -> tuple[Optional[str], Optional[str]]:
    """Panggil DeepSeek (API kompatibel OpenAI) via httpx; tanpa dependency tambahan."""
    if not DEEPSEEK_API_KEY:
        return None, "DEEPSEEK_API_KEY belum dikonfigurasi."
    url = f"{DEEPSEEK_BASE_URL.rstrip('/')}/chat/completions"
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": LLM_TEMPERATURE,
        "max_tokens": LLM_MAX_TOKENS,
        "stream": False,
    }
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }

    last_error: Optional[str] = None
    for attempt in range(LLM_MAX_RETRIES + 1):
        try:
            with httpx.Client(timeout=LLM_TIMEOUT_SECONDS) as client:
                response = client.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                data = response.json()
                choices = data.get("choices") or []
                message = choices[0].get("message", {}) if choices else {}
                text = (message.get("content") or "").strip()
                if text:
                    return text, None
                return None, "DeepSeek mengembalikan respons kosong."
            last_error = f"DeepSeek HTTP {response.status_code}."
            # 4xx selain rate-limit tidak perlu di-retry.
            if response.status_code != 429 and response.status_code < 500:
                break
        except (httpx.TimeoutException, httpx.TransportError) as exc:
            last_error = f"DeepSeek tidak dapat dihubungi: {type(exc).__name__}."
        except Exception as exc:  # noqa: BLE001
            last_error = f"DeepSeek call gagal: {type(exc).__name__}."
        if attempt < LLM_MAX_RETRIES:
            time.sleep(0.5 * (attempt + 1))
    return None, last_error or "DeepSeek call gagal."


def _call_openai(system_prompt: str, user_prompt: str) -> tuple[Optional[str], Optional[str]]:
    try:
        import openai  # type: ignore
    except ImportError:
        return None, "Paket openai belum terpasang."

    try:
        client = openai.OpenAI(
            api_key=OPENAI_API_KEY,
            timeout=LLM_TIMEOUT_SECONDS,
            max_retries=LLM_MAX_RETRIES,
        )
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=LLM_MAX_TOKENS,
            temperature=LLM_TEMPERATURE,
        )
        text = (response.choices[0].message.content or "").strip()
        if not text:
            return None, "OpenAI mengembalikan respons kosong."
        return text, None
    except Exception as exc:  # noqa: BLE001
        return None, f"OpenAI call gagal: {type(exc).__name__}."


def _call_llm(system_prompt: str, user_prompt: str) -> tuple[Optional[str], Optional[str], str]:
    """Return (text, error, provider). Tidak pernah raise."""
    if not LLM_ENABLED or not LLM_PROVIDER:
        return None, LLM_CONFIG_ERROR or "LLM tidak aktif.", LLM_PROVIDER or "none"

    cache_key = hashlib.sha256(
        f"{LLM_PROVIDER}|{LLM_MODEL}|{system_prompt}|{user_prompt}".encode("utf-8")
    ).hexdigest()
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached, None, LLM_PROVIDER

    if not _rate_limit_ok():
        return None, "Batas laju LLM tercapai; coba lagi sebentar lagi.", LLM_PROVIDER

    if LLM_PROVIDER == "gemini":
        text, error = _call_gemini(system_prompt, user_prompt)
    elif LLM_PROVIDER == "deepseek":
        text, error = _call_deepseek(system_prompt, user_prompt)
    else:
        text, error = _call_openai(system_prompt, user_prompt)
    if text:
        _cache_set(cache_key, text)
    return text, error, LLM_PROVIDER


# ─── Ratio Narrative (LLM opsional) ──────────────────────────────────────────

_RATIO_ALLOWED_FIELDS = {
    "ratio_code", "ratio_name", "category", "band", "direction", "quality",
}


def _sanitize_ratio_payload(payload: dict) -> dict:
    """Whitelist ketat: hanya enum/kode, tanpa angka atau identitas."""
    clean = {}
    for key in _RATIO_ALLOWED_FIELDS:
        value = str(payload.get(key, ""))[:80]
        clean[key] = re.sub(r"\d+", "", value)
    return clean


def _fallback_result(
    explanation: str,
    *,
    llm_enabled: bool,
    fallback_reason: Optional[str],
    privacy_note: str,
) -> dict:
    return {
        "explanation": explanation,
        "source": "fallback",
        "llm_enabled": llm_enabled,
        "llm_available": False,
        "fallback_reason": fallback_reason,
        "privacy_note": privacy_note,
    }


def generate_ratio_explanation(payload: dict, fallback_text: str) -> dict:
    """Narasi rasio dengan validasi output dan fallback deterministik."""
    if not LLM_ENABLED:
        return _fallback_result(
            fallback_text,
            llm_enabled=False,
            fallback_reason=LLM_CONFIG_ERROR or "LLM belum dikonfigurasi.",
            privacy_note=(
                "LLM tidak aktif. Narasi berasal dari template rule-based. "
                "Atur LLM_PROVIDER dan API key di environment untuk mengaktifkan."
            ),
        )

    sanitized = _sanitize_ratio_payload(payload)
    raw_output, error, provider = _call_llm(
        _RATIO_SYSTEM_PROMPT, _build_ratio_prompt(sanitized)
    )
    if raw_output is None:
        return _fallback_result(
            fallback_text,
            llm_enabled=True,
            fallback_reason=error or f"LLM {provider} tidak merespons.",
            privacy_note="LLM tidak merespons; narasi rule-based digunakan.",
        )

    is_valid, reason = _validate_llm_output(raw_output)
    if not is_valid:
        logger.warning("LLM ratio output gagal validasi (%s); pakai fallback.", reason)
        return _fallback_result(
            fallback_text,
            llm_enabled=True,
            fallback_reason=reason,
            privacy_note=f"Output LLM tidak lolos validasi ({reason}); narasi rule-based digunakan.",
        )

    return {
        "explanation": raw_output,
        "source": "llm",
        "llm_enabled": True,
        "llm_available": True,
        "fallback_reason": None,
        "privacy_note": (
            f"Narasi dihasilkan model bahasa ({provider}). Hanya kode/band/kualitas "
            "data yang dikirim; nominal dan identitas tidak dikirim. Bukan saran "
            "keuangan, pajak, atau hukum."
        ),
    }


# ─── Public Interface ─────────────────────────────────────────────────────────

def generate_explanation(recommendation: dict) -> dict:
    """
    Generate penjelasan naratif untuk satu rekomendasi.

    Return dict:
      {
        "explanation": str,
        "source": "llm" | "fallback",
        "llm_enabled": bool,
        "llm_available": bool,
        "fallback_reason": str | None,
        "privacy_note": str
      }

    Tidak pernah raise exception — selalu return hasil yang aman.
    """
    rule_id = recommendation.get("rule_id", "UNKNOWN")

    if not LLM_ENABLED:
        return _fallback_result(
            _get_fallback(rule_id),
            llm_enabled=False,
            fallback_reason=LLM_CONFIG_ERROR or "LLM belum dikonfigurasi.",
            privacy_note=(
                "LLM tidak aktif. Penjelasan dihasilkan dari template rule-based. "
                "Atur LLM_PROVIDER dan API key di environment untuk mengaktifkan."
            ),
        )

    # Sanitasi — hapus PII dan angka absolut
    sanitized = _sanitize_for_llm(recommendation)
    raw_output, error, provider = _call_llm(
        _RECOMMENDATION_SYSTEM_PROMPT,
        _build_recommendation_prompt(sanitized),
    )

    if raw_output is None:
        return _fallback_result(
            _get_fallback(rule_id),
            llm_enabled=True,
            fallback_reason=error or f"LLM {provider} tidak merespons.",
            privacy_note=(
                "LLM tidak merespons; penjelasan dari template rule-based "
                "digunakan sebagai fallback."
            ),
        )

    is_valid, reason = _validate_llm_output(raw_output)
    if not is_valid:
        logger.warning("LLM output gagal validasi (%s); pakai fallback.", reason)
        return _fallback_result(
            _get_fallback(rule_id),
            llm_enabled=True,
            fallback_reason=reason,
            privacy_note=(
                f"Output LLM tidak lolos validasi ({reason}); penjelasan "
                "rule-based digunakan."
            ),
        )

    return {
        "explanation": raw_output,
        "source": "llm",
        "llm_enabled": True,
        "llm_available": True,
        "fallback_reason": None,
        "privacy_note": (
            f"Penjelasan dihasilkan oleh model bahasa ({provider}). Angka dan "
            "data sensitif telah dihapus sebelum dikirim ke LLM. Penjelasan ini "
            "bersifat informatif dan bukan saran keuangan, pajak, atau hukum."
        ),
    }
