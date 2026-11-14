"""Ratio insights — Descriptive, Predictive, dan Prescriptive (deterministik).

Prinsip (FINANCIAL_AI_METHODOLOGY.md + RATIO_CFO_SPEC.md):
- Semua angka dihitung di sini secara deterministik; LLM tidak menghitung.
- Arah membaik/memburuk mengikuti `direction` pada threshold (higher/lower).
- Data tidak cukup → status `insufficient` dengan alasan, bukan angka palsu.
- Setiap insight menyertakan kode rasio, periode, arah, dan bukti yang dapat
  ditelusuri. Tidak ada klaim kepastian atau saran pajak/hukum.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional

from .ratio_engine import DEFAULT_THRESHOLDS, RATIO_FORMULA_VERSION, RATIO_META

INSIGHT_RULES_VERSION = "1.0.0"

# Berapa titik historis minimal sebelum tren/proyeksi numerik dipublikasikan.
MIN_POINTS_FOR_TREND = 3
# Horizon proyeksi default (jumlah periode ke depan) untuk MVP.
DEFAULT_HORIZON = 1

CATEGORY_LABEL = {
    "liquidity": "Likuiditas",
    "solvency": "Solvabilitas",
    "activity": "Aktivitas",
    "profitability": "Profitabilitas",
    "growth": "Pertumbuhan",
}

# Pesan peringatan per kategori (Bahasa Indonesia, tanpa angka absolut).
ALERT_MESSAGE = {
    "liquidity": (
        "Likuiditas jangka pendek menurun. Usaha mungkin kesulitan menutupi "
        "kewajiban mendesak jika arus kas masuk terhambat."
    ),
    "solvency": (
        "Risiko solvabilitas meningkat: porsi utang naik mendekati batas aman. "
        "Batasi penambahan utang baru dan evaluasi beban bunga."
    ),
    "activity": (
        "Efisiensi aktivitas menurun: perputaran persediaan melambat dan/atau "
        "penagihan piutang memanjang. Ini dapat menjadi tanda awal dead stock "
        "atau keterlambatan pembayaran klien sebelum menjadi krisis arus kas."
    ),
    "profitability": (
        "Profitabilitas menurun. Tinjau harga jual, harga pokok penjualan, dan "
        "beban operasional terbesar untuk memperbaiki margin."
    ),
    "growth": (
        "Pertumbuhan pendapatan melambat dibanding periode sebelumnya. Tinjau "
        "strategi penjualan dan retensi pelanggan."
    ),
}

# Aksi preskriptif konkret per kode rasio. Kunci: kode rasio.
PRESCRIPTIVE_CATALOG = {
    "CR": {
        "priority": "high",
        "actions": [
            "Percepat penagihan piutang dan tunda belanja non-esensial.",
            "Negosiasikan ulang jatuh tempo utang jangka pendek.",
        ],
    },
    "QR": {
        "priority": "high",
        "actions": [
            "Fokus pada aset yang cepat menjadi kas; hindari menambah persediaan.",
            "Siapkan rencana likuiditas 30 hari.",
        ],
    },
    "CASH_RATIO": {
        "priority": "high",
        "actions": [
            "Jaga saldo kas minimum untuk operasional harian.",
            "Pisahkan kas usaha dari kas pribadi pemilik.",
        ],
    },
    "DER": {
        "priority": "high",
        "actions": [
            "Batasi utang baru dan prioritaskan pelunasan utang berbunga tinggi.",
            "Perkuat ekuitas melalui laba ditahan sebelum ekspansi.",
        ],
    },
    "DAR": {
        "priority": "high",
        "actions": [
            "Turunkan porsi aset yang dibiayai utang secara bertahap.",
            "Evaluasi kembali rencana belanja modal yang bergantung pada utang.",
        ],
    },
    "ICR": {
        "priority": "high",
        "actions": [
            "Naikkan laba operasi atau restrukturisasi beban bunga.",
            "Hindari komitmen cicilan baru sebelum coverage membaik.",
        ],
    },
    "INV_TURN": {
        "priority": "medium",
        "actions": [
            "Identifikasi stok lambat (dead stock) dan lakukan diskon terukur.",
            "Hentikan pembelian berlebih; sesuaikan pemesanan dengan penjualan.",
        ],
    },
    "ACP": {
        "priority": "medium",
        "actions": [
            "Tetapkan termin pembayaran dan pengingat jatuh tempo otomatis.",
            "Tinjau klien dengan keterlambatan berulang dan batasi limit kreditnya.",
        ],
    },
    "DPO": {
        "priority": "low",
        "actions": [
            "Manfaatkan termin pemasok secara sehat tanpa mengorbankan diskon awal.",
        ],
    },
    "TATO": {
        "priority": "medium",
        "actions": [
            "Ada indikasi aset (mis. peralatan/kendaraan) tidak produktif "
            "menghasilkan pendapatan; tinjau utilisasi aset.",
            "Pertimbangkan menjual atau menyewakan aset yang menganggur.",
        ],
    },
    "GPM": {
        "priority": "high",
        "actions": [
            "Evaluasi vendor suplai untuk menekan harga pokok penjualan (HPP).",
            "Tinjau harga jual dan bauran produk agar margin kotor membaik.",
        ],
    },
    "OPM": {
        "priority": "medium",
        "actions": [
            "Disiplin biaya operasional; hentikan pengeluaran yang tidak "
            "berkontribusi pada pendapatan.",
        ],
    },
    "NPM": {
        "priority": "high",
        "actions": [
            "Perbaiki margin bersih dengan menekan HPP dan beban operasional.",
            "Hentikan lini produk yang merugi dan fokus pada yang paling untung.",
        ],
    },
    "ROA": {
        "priority": "medium",
        "actions": [
            "Tingkatkan pendapatan dari aset yang sudah ada sebelum menambah aset.",
            "Kurangi aset menganggur yang tidak menghasilkan pendapatan.",
        ],
    },
    "ROE": {
        "priority": "medium",
        "actions": [
            "Perbaiki laba bersih dan jaga struktur ekuitas tetap sehat.",
        ],
    },
    "REV_GROWTH": {
        "priority": "medium",
        "actions": [
            "Analisis penyebab perlambatan dan fokus pada retensi pelanggan.",
            "Diversifikasi sumber pendapatan agar tidak bergantung satu kanal.",
        ],
    },
}

ADVERSE_BANDS = ("between_warning_critical", "below_critical")


def _dec(value) -> Optional[Decimal]:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    text = str(value).strip()
    if text == "":
        return None
    try:
        return Decimal(text)
    except Exception:  # noqa: BLE001
        return None


def _num(value: Optional[Decimal]) -> Optional[str]:
    if value is None:
        return None
    return str(value.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP))


def _direction_for(code: str, thresholds: Dict[str, tuple]) -> str:
    entry = thresholds.get(code) or DEFAULT_THRESHOLDS.get(code)
    if entry and len(entry) >= 4:
        return entry[3]
    return "higher"


def _is_adverse(code: str, prev: Decimal, curr: Decimal, direction: str) -> bool:
    if direction == "higher":
        return curr < prev
    return curr > prev


def _is_improving(code: str, prev: Decimal, curr: Decimal, direction: str) -> bool:
    if direction == "higher":
        return curr > prev
    return curr < prev


# ─── Descriptive alert events (untuk notifikasi/Toastr) ──────────────────────

def compute_alerts(
    previous_ratios: Dict[str, Optional[str]],
    current_ratios: List[dict],
    thresholds: Optional[Dict[str, tuple]] = None,
) -> List[dict]:
    """Deteksi penurunan/kenaikan adverse per kategori untuk memicu notifikasi.

    Hanya memakai nilai periode berjalan vs periode sebelumnya. Tidak ada
    klaim kausalitas; pesan menyebut arah dan tindakan, bukan angka absolut.
    """
    thresholds = thresholds or DEFAULT_THRESHOLDS
    adverse_by_category: Dict[str, List[str]] = {}
    severe_categories = set()

    for ratio in current_ratios:
        code = ratio.get("code")
        if ratio.get("status") != "available":
            continue
        current_value = _dec(ratio.get("value"))
        previous_value = _dec(previous_ratios.get(code))
        if current_value is None or previous_value is None:
            continue

        direction = (
            ratio["threshold"]["direction"]
            if ratio.get("threshold")
            else _direction_for(code, thresholds)
        )
        if not _is_adverse(code, previous_value, current_value, direction):
            continue

        category = ratio.get("category", "other")
        adverse_by_category.setdefault(category, []).append(code)
        if ratio.get("band") in ADVERSE_BANDS:
            severe_categories.add(category)

    alerts: List[dict] = []
    for category, codes in adverse_by_category.items():
        message = ALERT_MESSAGE.get(category)
        if not message:
            continue
        level = "critical" if category in severe_categories else "warning"
        alerts.append({
            "code": f"ALERT_{category.upper()}_DOWN",
            "category": category,
            "category_label": CATEGORY_LABEL.get(category, category),
            "level": level,
            "title": f"{CATEGORY_LABEL.get(category, category)} berubah ke arah kurang sehat",
            "message": message,
            "ratio_codes": sorted(codes),
            "direction": "down",
            "rule_version": INSIGHT_RULES_VERSION,
            "evidence": [
                f"{code} bergerak ke arah kurang sehat dibanding periode sebelumnya"
                for code in sorted(codes)
            ],
        })

    order = {"critical": 0, "warning": 1}
    alerts.sort(key=lambda a: order.get(a["level"], 2))
    return alerts


# ─── Predictive: tren + proyeksi sederhana ───────────────────────────────────

def _linear_projection(values: List[Decimal], steps: int = 1) -> Optional[Decimal]:
    """Regresi linear sederhana (indeks sebagai x). Deterministik, tanpa library."""
    n = len(values)
    if n < MIN_POINTS_FOR_TREND:
        return None
    xs = [Decimal(i) for i in range(n)]
    mean_x = sum(xs) / Decimal(n)
    mean_y = sum(values) / Decimal(n)
    denom = sum((x - mean_x) ** 2 for x in xs)
    if denom == 0:
        return None
    slope = sum((xs[i] - mean_x) * (values[i] - mean_y) for i in range(n)) / denom
    intercept = mean_y - slope * mean_x
    target_x = Decimal(n - 1 + steps)
    return intercept + slope * target_x


def compute_predictive(
    history: List[dict],
    thresholds: Optional[Dict[str, tuple]] = None,
    codes: Optional[List[str]] = None,
    horizon: int = DEFAULT_HORIZON,
) -> dict:
    """Proyeksi tren rasio kunci dan flag risiko solvabilitas/aktivitas.

    history: list of {"as_of": str, "ratios": {code: value}} diurutkan lama→baru.
    """
    thresholds = thresholds or DEFAULT_THRESHOLDS
    codes = codes or ["CR", "QR", "DER", "DAR", "INV_TURN", "ACP", "NPM", "ROA", "TATO"]

    series: Dict[str, List[Decimal]] = {code: [] for code in codes}
    for point in history:
        values = point.get("ratios") or {}
        for code in codes:
            value = _dec(values.get(code))
            if value is not None:
                series[code].append(value)

    results: List[dict] = []
    for code in codes:
        values = series[code]
        name, category, unit = RATIO_META.get(code, (code, "other", "x"))
        direction = _direction_for(code, thresholds)
        threshold_entry = thresholds.get(code) or DEFAULT_THRESHOLDS.get(code)
        warning = threshold_entry[1] if threshold_entry else None

        if len(values) < MIN_POINTS_FOR_TREND:
            results.append({
                "code": code,
                "name": name,
                "category": category,
                "status": "insufficient",
                "points": len(values),
                "reason": (
                    f"Butuh minimal {MIN_POINTS_FOR_TREND} periode data rasio "
                    "untuk memproyeksikan tren."
                ),
            })
            continue

        projected = _linear_projection(values, steps=horizon)
        current = values[-1]
        delta = projected - current if projected is not None else None
        direction_trend = "flat"
        if delta is not None:
            if delta > 0:
                direction_trend = "up"
            elif delta < 0:
                direction_trend = "down"

        risk = False
        note = "Tren stabil berdasarkan periode yang tersedia."
        if projected is not None and warning is not None:
            if direction == "higher" and projected < warning:
                risk = True
                note = "Proyeksi berada di bawah batas warning; perlu perhatian."
            elif direction == "lower" and projected > warning:
                risk = True
                note = "Proyeksi berada di atas batas warning; perlu perhatian."
        if risk and code in ("DER", "DAR"):
            note = "Proyeksi risiko solvabilitas mendekati/melewati batas aman."
        elif risk and code in ("INV_TURN", "ACP"):
            note = (
                "Proyeksi menunjukkan potensi dead stock (perputaran melambat) "
                "atau penagihan piutang memanjang."
            )

        results.append({
            "code": code,
            "name": name,
            "category": category,
            "unit": unit,
            "status": "available",
            "points": len(values),
            "current": _num(current),
            "projected": _num(projected),
            "horizon": horizon,
            "trend": direction_trend,
            "risk": risk,
            "note": note,
            "method": "linear_trend_v1",
        })

    return {
        "horizon": horizon,
        "min_points": MIN_POINTS_FOR_TREND,
        "method": "linear_trend_v1",
        "series": results,
    }


# ─── Prescriptive: rekomendasi tindakan konkret ──────────────────────────────

def compute_prescriptive(
    current_ratios: List[dict],
) -> List[dict]:
    """Ubah band rasio di bawah target menjadi tindakan konkret yang dapat ditindak."""
    out: List[dict] = []
    for ratio in current_ratios:
        band = ratio.get("band")
        if band not in ("between_target_warning", "between_warning_critical", "below_critical"):
            continue
        code = ratio.get("code")
        catalog = PRESCRIPTIVE_CATALOG.get(code)
        if not catalog:
            continue

        priority = catalog["priority"]
        if band == "below_critical":
            priority = "high"
        elif band == "between_warning_critical" and priority == "low":
            priority = "medium"

        out.append({
            "rule_id": f"RATIO-{code}",
            "rule_version": INSIGHT_RULES_VERSION,
            "ratio_code": code,
            "ratio_name": ratio.get("name"),
            "category": ratio.get("category"),
            "priority": priority,
            "band": band,
            "display": ratio.get("display"),
            "title": f"Perbaiki {ratio.get('name', code)}",
            "trigger_metrics": {code: ratio.get("display")},
            "suggested_actions": catalog["actions"],
            "evidence": [
                f"{code} berada pada band '{band}' untuk periode berjalan.",
            ],
            "assumptions": [
                "Data neraca dan laba-rugi periode ini dianggap lengkap dan final.",
            ],
            "limitations": [
                "Rekomendasi bersifat indikatif, bukan saran keuangan, pajak, atau hukum.",
            ],
            "confidence_label": "berbasis aturan",
        })

    order = {"high": 0, "medium": 1, "low": 2}
    out.sort(key=lambda r: order.get(r["priority"], 3))
    return out


# ─── Orkestrasi ──────────────────────────────────────────────────────────────

def build_insights(
    current_snapshot: dict,
    history: Optional[List[dict]] = None,
    thresholds: Optional[Dict[str, tuple]] = None,
) -> dict:
    """Rakit alert + predictive + prescriptive dari satu snapshot rasio.

    history: titik lama→baru; titik terakhir idealnya adalah periode berjalan.
    Jika history tidak mencakup periode berjalan, periode berjalan ditambahkan.
    """
    history = list(history or [])
    thresholds = thresholds or DEFAULT_THRESHOLDS
    current_ratios = current_snapshot.get("ratios", [])
    period = current_snapshot.get("period", {})

    current_values = {
        r["code"]: r.get("value")
        for r in current_ratios
        if r.get("status") == "available"
    }
    current_point = {
        "as_of": current_snapshot.get("as_of"),
        "period_from": period.get("from"),
        "period_to": period.get("to"),
        "ratios": current_values,
    }
    if not history or history[-1].get("as_of") != current_point["as_of"]:
        history = history + [current_point]

    previous_values = history[-2].get("ratios", {}) if len(history) >= 2 else {}

    alerts = compute_alerts(previous_values, current_ratios, thresholds)
    predictive = compute_predictive(history, thresholds)
    prescriptive = compute_prescriptive(current_ratios)

    return {
        "period": period,
        "as_of": current_snapshot.get("as_of"),
        "currency": current_snapshot.get("currency", "IDR"),
        "formula_version": RATIO_FORMULA_VERSION,
        "rules_version": INSIGHT_RULES_VERSION,
        "has_previous_period": len(history) >= 2,
        "history_points": len(history),
        "alerts": alerts,
        "predictive": predictive,
        "prescriptive": prescriptive,
    }
