"""Test ratio insights: alert (notifikasi), prediktif (tren/proyeksi), preskriptif.

Semua deterministik. Tidak ada LLM atau network.
"""

from app import ratio_insights


def _ratio(code, name, category, value, band, direction="higher"):
    return {
        "code": code,
        "name": name,
        "category": category,
        "value": value,
        "display": f"{value}",
        "status": "available",
        "band": band,
        "threshold": {"direction": direction},
    }


# ─── Alerts ───────────────────────────────────────────────────────────────────

def test_liquidity_alert_when_cr_and_qr_decline():
    previous = {"CR": "1.60", "QR": "1.10"}
    current = [
        _ratio("CR", "Current Ratio", "liquidity", "1.40", "between_target_warning"),
        _ratio("QR", "Quick Ratio", "liquidity", "0.90", "between_target_warning"),
    ]
    alerts = ratio_insights.compute_alerts(previous, current)
    assert len(alerts) == 1
    alert = alerts[0]
    assert alert["category"] == "liquidity"
    assert alert["level"] == "warning"
    assert alert["ratio_codes"] == ["CR", "QR"]
    assert "likuiditas" in alert["message"].lower()


def test_liquidity_alert_escalates_to_critical_on_below_critical_band():
    previous = {"CR": "1.50"}
    current = [_ratio("CR", "Current Ratio", "liquidity", "0.90", "below_critical")]
    alerts = ratio_insights.compute_alerts(previous, current)
    assert alerts[0]["level"] == "critical"


def test_no_alert_when_ratio_improves():
    previous = {"CR": "1.20"}
    current = [_ratio("CR", "Current Ratio", "liquidity", "1.60", "above_target")]
    assert ratio_insights.compute_alerts(previous, current) == []


def test_solvency_alert_when_debt_ratio_increases():
    previous = {"DER": "1.20"}
    current = [_ratio("DER", "Debt to Equity", "solvency", "1.60", "between_warning_critical", "lower")]
    alerts = ratio_insights.compute_alerts(previous, current)
    assert alerts[0]["category"] == "solvency"
    assert alerts[0]["level"] == "critical"


def test_activity_alert_mentions_dead_stock_or_collection():
    previous = {"INV_TURN": "6", "ACP": "30"}
    current = [
        _ratio("INV_TURN", "Inventory Turnover", "activity", "3", "between_target_warning"),
        _ratio("ACP", "Average Collection Period", "activity", "55", "between_target_warning", "lower"),
    ]
    alerts = ratio_insights.compute_alerts(previous, current)
    assert alerts[0]["category"] == "activity"
    assert "dead stock" in alerts[0]["message"].lower()


# ─── Prescriptive ─────────────────────────────────────────────────────────────

def test_prescriptive_npm_below_target_recommends_vendor_and_hpp():
    current = [_ratio("NPM", "Net Profit Margin", "profitability", "0.03", "below_critical")]
    recs = ratio_insights.compute_prescriptive(current)
    assert len(recs) == 1
    rec = recs[0]
    assert rec["rule_id"] == "RATIO-NPM"
    assert rec["priority"] == "high"
    actions = " ".join(rec["suggested_actions"]).lower()
    assert "hpp" in actions or "vendor" in actions


def test_prescriptive_tato_low_warns_idle_assets():
    current = [_ratio("TATO", "Total Asset Turnover", "activity", "0.20", "below_critical")]
    recs = ratio_insights.compute_prescriptive(current)
    actions = " ".join(recs[0]["suggested_actions"]).lower()
    assert "aset" in actions


def test_prescriptive_ignores_healthy_band():
    current = [_ratio("NPM", "Net Profit Margin", "profitability", "0.20", "above_target")]
    assert ratio_insights.compute_prescriptive(current) == []


# ─── Predictive ───────────────────────────────────────────────────────────────

def test_predictive_insufficient_with_too_few_points():
    history = [
        {"as_of": "2026-09-30", "ratios": {"DER": "1.0"}},
        {"as_of": "2026-10-31", "ratios": {"DER": "1.1"}},
    ]
    result = ratio_insights.compute_predictive(history, codes=["DER"])
    entry = result["series"][0]
    assert entry["status"] == "insufficient"
    assert "minimal" in entry["reason"]


def test_predictive_projects_rising_der_as_risk():
    history = [
        {"as_of": "2026-08-31", "ratios": {"DER": "1.00"}},
        {"as_of": "2026-09-30", "ratios": {"DER": "1.20"}},
        {"as_of": "2026-10-31", "ratios": {"DER": "1.40"}},
    ]
    result = ratio_insights.compute_predictive(history, codes=["DER"])
    entry = result["series"][0]
    assert entry["status"] == "available"
    assert entry["trend"] == "up"
    assert entry["risk"] is True
    assert "solvabilitas" in entry["note"].lower()


# ─── Orkestrasi ───────────────────────────────────────────────────────────────

def test_build_insights_combines_all_three_pillars():
    snapshot = {
        "period": {"from": "2026-10-01", "to": "2026-10-31"},
        "as_of": "2026-10-31",
        "currency": "IDR",
        "ratios": [
            _ratio("CR", "Current Ratio", "liquidity", "1.10", "below_critical"),
            _ratio("NPM", "Net Profit Margin", "profitability", "0.02", "below_critical"),
        ],
    }
    history = [
        {"as_of": "2026-08-31", "ratios": {"CR": "1.50", "NPM": "0.10"}},
        {"as_of": "2026-09-30", "ratios": {"CR": "1.30", "NPM": "0.08"}},
    ]
    result = ratio_insights.build_insights(snapshot, history)
    assert result["formula_version"] == "1.1.0"
    assert result["rules_version"] == ratio_insights.INSIGHT_RULES_VERSION
    assert result["has_previous_period"] is True
    assert any(a["category"] == "liquidity" for a in result["alerts"])
    assert any(r["rule_id"] == "RATIO-NPM" for r in result["prescriptive"])
    assert result["predictive"]["series"]
