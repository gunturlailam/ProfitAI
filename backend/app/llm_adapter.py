"""
LLM Adapter untuk ProfitAI - DeepSeek Integration
==================================================

Production-ready DeepSeek API integration untuk financial narrative generation.

Features:
- DeepSeek Chat dengan JSON output mode
- Structured output validation
- Automatic fallback ke rule-based narrative
- Rate limiting dan caching
- Privacy-first: no PII, no absolute numbers
- Comprehensive error handling

Environment Variables:
- DEEPSEEK_API_KEY: Ethereal Market API key (required)
- DEEPSEEK_BASE_URL: API endpoint (default: https://etherealmarket.my.id/v1)
- DEEPSEEK_MODEL: Model name (default: deepseek-chat)
- LLM_TEMPERATURE: Temperature 0-1 (default: 0.7)
- LLM_MAX_TOKENS: Max output tokens (default: 1024)
- LLM_TIMEOUT: Timeout in seconds (default: 30)
- LLM_MAX_RETRIES: Max retry attempts (default: 2)
"""

import os
import json
import time
import hashlib
import logging
from typing import Dict, Any, Optional, Tuple

# Try to import openai
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

logger = logging.getLogger(__name__)

# Configuration
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "").strip()
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://etherealmarket.my.id/v1").strip()
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "auto").strip()
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "1024"))
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "30"))
LLM_MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "2"))

# Initialize DeepSeek client if available
if OPENAI_AVAILABLE and DEEPSEEK_API_KEY:
    try:
        client = OpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_BASE_URL,
            timeout=LLM_TIMEOUT
        )
        LLM_ENABLED = True
        logger.info(f"DeepSeek client initialized - Base URL: {DEEPSEEK_BASE_URL}, Model: {DEEPSEEK_MODEL}")
    except Exception as e:
        logger.error(f"Failed to initialize DeepSeek client: {e}")
        LLM_ENABLED = False
        client = None
else:
    LLM_ENABLED = False
    client = None
    if not OPENAI_AVAILABLE:
        logger.warning("OpenAI package not installed - LLM features disabled")
    if not DEEPSEEK_API_KEY:
        logger.warning("DEEPSEEK_API_KEY not configured - LLM features disabled")

# Simple in-memory cache (for production, use Redis)
_CACHE: Dict[str, Tuple[str, float]] = {}
CACHE_TTL = 3600  # 1 hour

# System prompts
FINANCIAL_ANALYST_SYSTEM_PROMPT = """
Anda adalah CFO virtual ahli keuangan UMKM Indonesia.

TUGAS ANDA:
Analisis rasio keuangan dan berikan insight dalam Bahasa Indonesia yang:
1. Mudah dipahami pemilik usaha (bukan akuntan profesional)
2. Spesifik dengan konteks angka yang diberikan
3. Memberikan rekomendasi aksi konkret dan praktis
4. Jujur tentang keterbatasan data

ATURAN KETAT:
- Jangan mengarang angka atau data yang tidak diberikan
- Jangan buat klaim pasti tentang masa depan
- Jangan berikan saran pajak/hukum spesifik
- Fokus pada insight operasional yang actionable
- Gunakan bahasa yang ramah dan tidak menakutkan

OUTPUT FORMAT:
Berikan output dalam format JSON dengan struktur:
{
  "explanation": "Penjelasan kondisi rasio 2-3 paragraf dengan konteks",
  "action": "Rekomendasi tindakan konkret 2-3 poin",
  "warning": "Peringatan penting (optional)"
}
"""

RECOMMENDATION_SYSTEM_PROMPT = """
Anda adalah konsultan keuangan UMKM yang membantu pemilik usaha memahami kondisi keuangan mereka.

TUGAS ANDA:
Jelaskan rekomendasi keuangan dalam Bahasa Indonesia yang:
1. Kontekstual dengan kondisi bisnis
2. Praktis dan dapat dilakukan
3. Jelas tanpa jargon berlebihan

ATURAN:
- Fokus pada "mengapa" dan "bagaimana"
- Berikan contoh konkret jika relevan
- Jangan gunakan angka absolut kecuali dari context
- Jangan janjikan hasil pasti

OUTPUT FORMAT JSON:
{
  "explanation": "Penjelasan mengapa rekomendasi ini penting",
  "action": "Langkah konkret yang bisa dilakukan",
  "impact": "Dampak yang diharapkan (realistic)"
}
"""


def _get_cache_key(prompt: str, context: Dict[str, Any]) -> str:
    """Generate cache key from prompt and context."""
    key_str = f"{prompt}:{json.dumps(context, sort_keys=True)}"
    return hashlib.md5(key_str.encode()).hexdigest()


def _get_cached(cache_key: str) -> Optional[str]:
    """Get cached response if still valid."""
    if cache_key in _CACHE:
        response, expires_at = _CACHE[cache_key]
        if time.time() < expires_at:
            return response
        else:
            del _CACHE[cache_key]
    return None


def _set_cache(cache_key: str, response: str):
    """Cache response with TTL."""
    _CACHE[cache_key] = (response, time.time() + CACHE_TTL)


def _validate_json_response(response_text: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
    """
    Validate JSON response from LLM.
    Returns: (is_valid, parsed_data, error_message)
    """
    try:
        # Try to parse JSON
        data = json.loads(response_text)
        
        # Validate required fields
        if not isinstance(data, dict):
            return False, None, "Response is not a JSON object"
        
        if "explanation" not in data:
            return False, None, "Missing 'explanation' field"
        
        # Validate explanation length
        explanation = data.get("explanation", "")
        if len(explanation) < 50:
            return False, None, "Explanation too short (< 50 chars)"
        
        if len(explanation) > 2000:
            return False, None, "Explanation too long (> 2000 chars)"
        
        return True, data, None
        
    except json.JSONDecodeError as e:
        return False, None, f"Invalid JSON: {str(e)}"
    except Exception as e:
        return False, None, f"Validation error: {str(e)}"


def _call_deepseek(
    system_prompt: str,
    user_prompt: str,
    retries: int = LLM_MAX_RETRIES
) -> Tuple[Optional[str], Optional[str]]:
    """
    Call DeepSeek API with retry logic.
    Returns: (response_text, error_message)
    """
    if not LLM_ENABLED or not client:
        return None, "DeepSeek not configured (check DEEPSEEK_API_KEY)"
    
    for attempt in range(retries + 1):
        try:
            # Call DeepSeek Chat API
            response = client.chat.completions.create(
                model=DEEPSEEK_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=LLM_TEMPERATURE,
                max_tokens=LLM_MAX_TOKENS,
                response_format={"type": "json_object"}
            )
            
            # Extract text
            if response and response.choices and len(response.choices) > 0:
                message = response.choices[0].message
                if message and message.content:
                    return message.content.strip(), None
                else:
                    return None, "Empty response from DeepSeek"
            else:
                return None, "No choices in response"
                
        except Exception as e:
            error_msg = f"DeepSeek API error (attempt {attempt + 1}/{retries + 1}): {str(e)}"
            logger.warning(error_msg)
            
            if attempt < retries:
                # Exponential backoff
                wait_time = (2 ** attempt) * 0.5
                time.sleep(wait_time)
            else:
                return None, error_msg
    
    return None, "Max retries exceeded"


def generate_ratio_explanation(
    ratio_code: str,
    ratio_name: str,
    category: str,
    value: Optional[str],
    band: str,
    direction: Optional[str],
    data_quality: str,
    target: Optional[str] = None,
    warning_threshold: Optional[str] = None,
    critical_threshold: Optional[str] = None,
    unit: str = "x",
    period: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Generate explanation untuk single ratio menggunakan DeepSeek.
    
    Dengan automatic fallback jika:
    - DeepSeek not configured
    - API error
    - Invalid response
    """
    
    # Build context
    context = {
        "ratio_code": ratio_code,
        "ratio_name": ratio_name,
        "category": category,
        "value": value,
        "band": band,
        "direction": direction,
        "data_quality": data_quality,
        "target": target,
        "warning": warning_threshold,
        "critical": critical_threshold,
        "unit": unit,
        "period": period
    }
    
    # Check if unavailable
    if value is None or band == "insufficient":
        return {
            "explanation": f"{ratio_name} tidak dapat dihitung karena data tidak lengkap.",
            "action": "Lengkapi data transaksi dan saldo akun untuk analisis rasio.",
            "source": "fallback",
            "llm_enabled": LLM_ENABLED,
            "llm_available": False,
            "fallback_reason": "Insufficient data",
            "disclaimer": "Narasi ini bersifat informatif, bukan saran keuangan profesional."
        }
    
    # Check cache
    cache_key = _get_cache_key("ratio_explanation", context)
    cached_response = _get_cached(cache_key)
    if cached_response:
        result = json.loads(cached_response)
        result["source"] = "cache"
        return result
    
    # Build prompt
    user_prompt = f"""
Analisis rasio keuangan berikut untuk pemilik UMKM:

RASIO: {ratio_name} ({ratio_code})
KATEGORI: {category}
NILAI SAAT INI: {value} {unit}
STATUS BAND: {band}
KUALITAS DATA: {data_quality}
"""
    
    if target and warning_threshold and critical_threshold:
        user_prompt += f"""
THRESHOLD YANG DITETAPKAN:
- Target (bagus): {target} {unit}
- Warning (perlu perhatian): {warning_threshold} {unit}
- Critical (bahaya): {critical_threshold} {unit}
- Arah lebih baik: {direction}
"""
    
    if period:
        user_prompt += f"\nPERIODE ANALISIS: {period.get('from')} sampai {period.get('to')}\n"
    
    user_prompt += """
Berikan analisis dalam format JSON dengan:
1. explanation: Jelaskan kondisi rasio ini dan apa artinya untuk bisnis (150-300 kata)
2. action: 2-3 rekomendasi tindakan konkret yang bisa dilakukan pemilik usaha
3. warning: Peringatan penting jika ada (optional)

Fokus pada insight praktis yang actionable!
"""
    
    # Try DeepSeek
    if LLM_ENABLED:
        response_text, error = _call_deepseek(
            FINANCIAL_ANALYST_SYSTEM_PROMPT,
            user_prompt
        )
        
        if response_text:
            # Validate response
            is_valid, parsed_data, validation_error = _validate_json_response(response_text)
            
            if is_valid and parsed_data:
                result = {
                    "explanation": parsed_data.get("explanation", ""),
                    "action": parsed_data.get("action", ""),
                    "warning": parsed_data.get("warning"),
                    "source": "llm",
                    "llm_enabled": True,
                    "llm_available": True,
                    "model": DEEPSEEK_MODEL,
                    "disclaimer": "Narasi ini bersifat informatif, bukan saran keuangan profesional."
                }
                
                # Cache successful response
                _set_cache(cache_key, json.dumps(result))
                
                return result
            else:
                logger.warning(f"Invalid DeepSeek response: {validation_error}")
        else:
            logger.warning(f"DeepSeek call failed: {error}")
    
    # Fallback: Generate rule-based explanation
    fallback = _generate_fallback_ratio_explanation(
        ratio_code, ratio_name, band, value, unit
    )
    
    fallback.update({
        "source": "fallback",
        "llm_enabled": LLM_ENABLED,
        "llm_available": False,
        "fallback_reason": error if LLM_ENABLED else "DeepSeek not configured",
        "disclaimer": "Narasi ini bersifat informatif, bukan saran keuangan profesional."
    })
    
    return fallback


def generate_recommendation_explanation(
    recommendation: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate explanation untuk recommendation menggunakan DeepSeek.
    
    Args:
        recommendation: Dict containing rule_id, title, priority, evidence, etc.
    
    Returns:
        Dict with explanation, action, source, and metadata
    """
    
    rule_id = recommendation.get("rule_id", "UNKNOWN")
    
    # Check cache
    cache_key = _get_cache_key("recommendation_explanation", recommendation)
    cached_response = _get_cached(cache_key)
    if cached_response:
        result = json.loads(cached_response)
        result["source"] = "cache"
        return result
    
    # Build prompt
    user_prompt = f"""
Jelaskan rekomendasi keuangan berikut untuk pemilik UMKM:

REKOMENDASI: {recommendation.get('title', 'Untitled')}
PRIORITAS: {recommendation.get('priority', 'medium')}
RULE ID: {rule_id}

BUKTI/EVIDENCE:
"""
    
    for evidence in (recommendation.get("evidence", []) or [])[:3]:
        user_prompt += f"- {evidence}\n"
    
    user_prompt += "\nAKSI YANG DISARANKAN:\n"
    for action in (recommendation.get("suggested_actions", []) or [])[:3]:
        user_prompt += f"- {action}\n"
    
    user_prompt += """
Berikan penjelasan dalam format JSON:
1. explanation: Mengapa rekomendasi ini penting dan relevan (100-200 kata)
2. action: Langkah konkret yang bisa dilakukan segera
3. impact: Dampak positif yang diharapkan (realistic)

Gunakan bahasa yang mudah dipahami dan motivating!
"""
    
    # Try DeepSeek
    if LLM_ENABLED:
        response_text, error = _call_deepseek(
            RECOMMENDATION_SYSTEM_PROMPT,
            user_prompt
        )
        
        if response_text:
            is_valid, parsed_data, validation_error = _validate_json_response(response_text)
            
            if is_valid and parsed_data:
                result = {
                    "explanation": parsed_data.get("explanation", ""),
                    "action": parsed_data.get("action", ""),
                    "impact": parsed_data.get("impact"),
                    "source": "llm",
                    "llm_enabled": True,
                    "llm_available": True,
                    "model": DEEPSEEK_MODEL,
                    "disclaimer": "Narasi ini bersifat informatif, bukan saran keuangan profesional."
                }
                
                # Cache successful response
                _set_cache(cache_key, json.dumps(result))
                
                return result
    
    # Fallback
    fallback = _generate_fallback_recommendation_explanation(rule_id)
    fallback.update({
        "source": "fallback",
        "llm_enabled": LLM_ENABLED,
        "llm_available": False,
        "fallback_reason": error if LLM_ENABLED else "DeepSeek not configured",
        "disclaimer": "Narasi ini bersifat informatif, bukan saran keuangan profesional."
    })
    
    return fallback


def _generate_fallback_ratio_explanation(
    ratio_code: str,
    ratio_name: str,
    band: str,
    value: Optional[str],
    unit: str
) -> Dict[str, Any]:
    """Generate rule-based fallback explanation for ratio."""
    
    # Comprehensive fallback templates
    FALLBACK_TEMPLATES = {
        "CR": {
            "above_target": {
                "explanation": f"Current Ratio Anda saat ini di atas target yang menunjukkan posisi likuiditas yang sehat. Untuk setiap Rp 1 utang jangka pendek, Anda memiliki lebih dari Rp 1.5 aset lancar yang bisa segera dicairkan. Ini memberikan buffer yang baik untuk menghadapi kebutuhan kas mendadak.",
                "action": "Pertahankan buffer kas ini. Pastikan kas tidak menganggur terlalu banyak - sisihkan untuk investasi produktif atau pelunasan utang dengan bunga tinggi."
            },
            "between_target_warning": {
                "explanation": f"Current Ratio Anda di zona kuning, mulai menipis dari target ideal. Masih ada buffer likuiditas tapi perlu monitoring ketat agar tidak turun lebih jauh.",
                "action": "Tunda pembelian besar yang tidak mendesak. Percepat penagihan piutang usaha. Lakukan monitoring arus kas secara mingguan untuk deteksi dini masalah likuiditas."
            },
            "between_warning_critical": {
                "explanation": f"Current Ratio Anda mendekati zona bahaya. Buffer likuiditas menipis - risiko kesulitan membayar kewajiban jangka pendek meningkat signifikan.",
                "action": "PRIORITAS TINGGI: Tunda semua pengeluaran non-esensial. Tagih piutang secara agresif termasuk yang belum jatuh tempo dengan insentif early payment. Negosiasikan perpanjangan termin pembayaran dengan supplier."
            },
            "below_critical": {
                "explanation": f"Current Ratio di bawah 1.0x - kondisi KRITIS. Aset lancar Anda tidak cukup untuk menutupi utang jangka pendek. Risiko gagal bayar sangat tinggi dan bisa berdampak pada operasional.",
                "action": "DARURAT: Freeze semua pengeluaran diskresioner. Cari sumber kas segera (jual aset idle, ajukan pinjaman jangka pendek, inject modal pemilik). Renegosiasi jadwal pembayaran utang yang jatuh tempo."
            }
        },
        "QR": {
            "above_target": {
                "explanation": f"Quick Ratio solid menunjukkan likuiditas immediate Anda sangat baik. Bahkan tanpa menghitung inventory, Anda bisa menutupi semua utang jangka pendek dengan kas dan piutang.",
                "action": "Pertahankan disiplin cash management. Monitor aging piutang agar tetap tertagih tepat waktu."
            },
            "below_critical": {
                "explanation": f"Quick Ratio rendah menunjukkan ketergantungan tinggi pada penjualan inventory untuk membayar utang. Jika inventory stuck atau tidak laku, likuiditas akan bermasalah.",
                "action": "Percepat inventory turnover dengan strategi promosi. Fokus pada produk fast-moving. Kurangi pembelian inventory baru sampai QR membaik di atas 0.8x."
            }
        },
        "DER": {
            "above_target": {
                "explanation": f"Debt to Equity Ratio sehat - utang tidak terlalu dominan dibanding modal sendiri. Struktur permodalan Anda relatif aman dan tidak overleveraged.",
                "action": "Ruang untuk utang produktif masih ada jika diperlukan untuk ekspansi yang menguntungkan. Prioritaskan retention profit untuk memperkuat equity."
            },
            "below_critical": {
                "explanation": f"Debt to Equity Ratio sangat tinggi - utang jauh melebihi modal sendiri. Leverage berlebihan meningkatkan risiko solvabilitas dan beban bunga yang berat.",
                "action": "PRIORITAS: Stop akumulasi utang baru. Fokus pelunasan utang dengan bunga tertinggi terlebih dahulu. Pertimbangkan inject modal atau retain profit maksimal untuk strengthen equity."
            }
        },
        "GPM": {
            "above_target": {
                "explanation": f"Gross Profit Margin Anda sehat di atas 30%, menunjukkan markup produk yang baik dan efisiensi HPP. Anda punya ruang untuk menyerap kenaikan biaya operasional.",
                "action": "Pertahankan pricing strategy dan kontrol HPP. Monitor pergerakan harga supplier agar margin tetap terjaga."
            },
            "below_critical": {
                "explanation": f"Gross Profit Margin tipis di bawah 10% - hampir tidak ada ruang untuk profit setelah HPP. Sangat rentan terhadap kenaikan harga bahan atau kompetisi harga.",
                "action": "URGENT: Review pricing - pertimbangkan kenaikan harga 5-10% di produk non-sensitif. Negosiasi harga supplier atau cari alternatif lebih murah. Fokus pada produk margin tinggi."
            }
        },
        "NPM": {
            "above_target": {
                "explanation": f"Net Profit Margin solid di atas 10%. Bisnis Anda profitable dan efisien dalam mengkonversi revenue menjadi laba bersih.",
                "action": "Reinvestasi sebagian profit untuk growth yang sustainable. Maintain cost discipline."
            },
            "below_critical": {
                "explanation": f"Net Profit Margin sangat tipis atau negatif. Hampir tidak ada profit atau malah rugi setelah semua biaya. Tidak sustainable dalam jangka panjang.",
                "action": "Audit total cost structure. Identifikasi 3 pos biaya terbesar dan cari cara efisiensi 10-20%. Review pricing dan product mix."
            }
        }
    }
    
    # Get template
    ratio_templates = FALLBACK_TEMPLATES.get(ratio_code, {})
    band_template = ratio_templates.get(band, {
        "explanation": f"{ratio_name} berada di status {band}.",
        "action": "Monitor perkembangan rasio ini secara berkala untuk memastikan tetap di level yang sehat."
    })
    
    return {
        "explanation": band_template["explanation"],
        "action": band_template["action"],
    }


def _generate_fallback_recommendation_explanation(rule_id: str) -> Dict[str, Any]:
    """Generate rule-based fallback explanation for recommendation."""
    
    FALLBACK_REC_TEMPLATES = {
        "REC-CF-01": {
            "explanation": "Arus kas tercatat menunjukkan pengeluaran melebihi pemasukan pada periode ini. Kondisi defisit kas perlu segera diatasi karena bisa mengganggu operasional dan kemampuan membayar kewajiban tepat waktu.",
            "action": "Tinjau pos pengeluaran non-esensial dan tunda yang bisa ditunda. Percepat penagihan piutang terutama yang sudah jatuh tempo. Evaluasi termin pembayaran dengan supplier.",
            "impact": "Dengan tindakan ini, arus kas diharapkan kembali positif dalam 2-4 minggu."
        },
        "REC-EXP-01": {
            "explanation": "Rasio beban operasional terhadap pendapatan berada di level yang perlu diperhatikan. Beban yang terlalu tinggi menggerus profit margin dan mengurangi ketahanan finansial bisnis.",
            "action": "Periksa 3-5 pos biaya terbesar dan identifikasi peluang efisiensi. Pastikan tidak ada pengeluaran pribadi yang tercampur ke akun usaha. Review kontrak vendor untuk potensi negosiasi harga.",
            "impact": "Efisiensi 10-15% pada pos biaya utama bisa meningkatkan profit margin secara signifikan."
        },
        "REC-DQ-01": {
            "explanation": "Terdapat transaksi yang belum memiliki kategori yang tepat. Kategorisasi yang lengkap penting untuk akurasi laporan keuangan dan analisis yang reliable.",
            "action": "Lengkapi kategori untuk semua transaksi income dan expense. Gunakan kategori yang konsisten agar trend analysis bisa dilakukan dengan akurat.",
            "impact": "Dengan data yang complete, Anda akan mendapat insight yang lebih akurat dan rekomendasi yang lebih tepat."
        },
        "REC-SAV-01": {
            "explanation": "Bisnis Anda membukukan surplus dan arus kas positif - kondisi yang baik! Namun penting untuk mengalokasikan surplus dengan bijak agar siap menghadapi fluktuasi bisnis.",
            "action": "Sisihkan 10-20% surplus ke rekening cadangan terpisah sebagai dana darurat. Target saldo dana darurat minimal 3-6 bulan biaya operasional tetap.",
            "impact": "Dana darurat yang adequate memberikan peace of mind dan kemampuan menghadapi situasi tidak terduga tanpa mengganggu operasional."
        }
    }
    
    # Normalize rule ID
    normalized_id = rule_id.replace("RULE-", "REC-")
    
    template = FALLBACK_REC_TEMPLATES.get(normalized_id, {
        "explanation": "Berdasarkan data transaksi yang tercatat, terdapat kondisi keuangan yang memerlukan perhatian.",
        "action": "Silakan tinjau detail rekomendasi dan indikator terkait untuk langkah perbaikan yang sesuai.",
        "impact": "Dengan tindakan yang tepat, kondisi keuangan bisnis dapat diperbaiki secara bertahap."
    })
    
    return template


# Legacy compatibility function
def generate_explanation(recommendation: dict) -> dict:
    """
    Legacy function for backward compatibility.
    Calls generate_recommendation_explanation internally.
    """
    return generate_recommendation_explanation(recommendation)


# Module info for debugging
def get_llm_status() -> Dict[str, Any]:
    """Get current LLM configuration status."""
    return {
        "openai_available": OPENAI_AVAILABLE,
        "llm_enabled": LLM_ENABLED,
        "api_key_configured": bool(DEEPSEEK_API_KEY),
        "base_url": DEEPSEEK_BASE_URL if LLM_ENABLED else None,
        "model": DEEPSEEK_MODEL if LLM_ENABLED else None,
        "temperature": LLM_TEMPERATURE,
        "max_tokens": LLM_MAX_TOKENS,
        "cache_size": len(_CACHE)
    }
