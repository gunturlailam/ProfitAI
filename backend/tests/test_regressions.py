"""Regression tests untuk defect audit ProfitAI.

Fokus pada invariant yang mudah rusak:
- laba bersih tidak boleh dibuat saat COGS belum lengkap;
- role dan audit pada write;
- rekomendasi period-scoped dan GET tanpa side effect default;
- period close menolak write;
- PATCH stok tidak boleh melewati movement;
- fallback LLM deterministik.
"""

from datetime import date
from decimal import Decimal
from types import SimpleNamespace

from app import llm_adapter, models
from app.financial_engine import calculate_profit_loss
from app.security import hash_password


def _tx(day, amount, tx_type="income", status="posted", reversal_of_id=None,
        category_id=1):
    return SimpleNamespace(
        transaction_date=day,
        amount=Decimal(amount),
        tx_type=tx_type,
        status=status,
        reversal_of_id=reversal_of_id,
        category_id=category_id,
    )


def _add_user_with_role(db_session, org_id, email, token, role):
    user = models.User(
        email=email,
        password_hash=hash_password("Password123!"),
        full_name=f"User {role}",
    )
    db_session.add(user)
    db_session.flush()
    db_session.add(models.Membership(
        organization_id=org_id, user_id=user.id, role=role
    ))
    db_session.add(models.Session(token=token, user_id=user.id))
    db_session.commit()
    return user, {"Authorization": f"Bearer {token}"}


def _post_transaction(client, headers, category_id, tx_type, amount,
                      tx_date="2026-11-05", description="Transaksi test"):
    return client.post(
        "/api/v1/transactions",
        headers=headers,
        json={
            "transaction_date": tx_date,
            "description": description,
            "amount": amount,
            "tx_type": tx_type,
            "category_id": category_id,
        },
    )


def test_profit_loss_net_profit_unavailable_without_cogs():
    transactions = [
        _tx(date(2026, 11, 1), "1000", "income"),
        _tx(date(2026, 11, 2), "250", "expense"),
    ]

    result = calculate_profit_loss(
        transactions, date(2026, 11, 1), date(2026, 11, 30)
    )

    assert result["items"]["operating_profit"]["value"] == "750.00"
    assert result["items"]["net_profit"]["status"] == "unavailable"
    assert result["items"]["net_profit"]["value"] is None
    assert result["ratios"]["net_margin"]["status"] == "unavailable"
    assert any("COGS belum diklasifikasikan" in w
               for w in result["data_quality"]["warnings"])


def test_viewer_cannot_write_but_member_can_create_transaction(
    client, db_session, org_a_setup
):
    org_id = org_a_setup["org"].id
    _, viewer_headers = _add_user_with_role(
        db_session, org_id, "viewer@profitai.test", "token_viewer_123", "viewer"
    )
    _, member_headers = _add_user_with_role(
        db_session, org_id, "member@profitai.test", "token_member_123", "member"
    )
    income_category = org_a_setup["cat_map"][("Penjualan", "income")]

    denied = _post_transaction(
        client, viewer_headers, income_category, "income", "1000.00"
    )
    assert denied.status_code == 403, denied.text

    allowed = _post_transaction(
        client, member_headers, income_category, "income", "1000.00"
    )
    assert allowed.status_code == 201, allowed.text


def test_transaction_write_records_audit_event(client, db_session, org_a_setup):
    headers = org_a_setup["headers"]
    income_category = org_a_setup["cat_map"][("Penjualan", "income")]

    response = _post_transaction(
        client, headers, income_category, "income", "1000.00",
        description="Audit test",
    )
    assert response.status_code == 201, response.text

    event = db_session.query(models.AuditEvent).filter_by(
        organization_id=org_a_setup["org"].id,
        action="TRANSACTION_CREATED",
    ).one()
    assert event.entity_type == "transactions"
    assert event.entity_id == response.json()["id"]
    assert event.payload["amount"] == "1000.00"


def test_closed_period_blocks_transaction_and_reversal(
    client, db_session, org_a_setup
):
    headers = org_a_setup["headers"]
    org_id = org_a_setup["org"].id
    income_category = org_a_setup["cat_map"][("Penjualan", "income")]

    created = _post_transaction(
        client, headers, income_category, "income", "1000.00",
        tx_date="2026-11-05",
    )
    assert created.status_code == 201, created.text
    tx_id = created.json()["id"]

    period = models.AccountingPeriod(
        organization_id=org_id,
        period_from=date(2026, 11, 1),
        period_to=date(2026, 11, 30),
        status="open",
    )
    db_session.add(period)
    db_session.commit()

    closed = client.post(
        f"/api/v1/accounting-periods/{period.id}/close", headers=headers
    )
    assert closed.status_code == 200, closed.text

    blocked_create = _post_transaction(
        client, headers, income_category, "income", "500.00",
        tx_date="2026-11-10",
    )
    assert blocked_create.status_code == 409, blocked_create.text

    blocked_reverse = client.post(
        f"/api/v1/transactions/{tx_id}/reverse", headers=headers
    )
    assert blocked_reverse.status_code == 409, blocked_reverse.text


def test_inventory_patch_rejects_direct_stock_change(
    client, db_session, org_a_setup
):
    headers = org_a_setup["headers"]
    created = client.post(
        "/api/v1/inventory-items",
        headers=headers,
        json={
            "sku": "SKU-TEST-1",
            "name": "Item test",
            "unit": "pcs",
            "cost_price": "1000.00",
            "quantity_on_hand": "10",
            "reorder_point": "2",
        },
    )
    assert created.status_code == 201, created.text
    item_id = created.json()["id"]

    response = client.patch(
        f"/api/v1/inventory-items/{item_id}",
        headers=headers,
        json={"quantity_on_hand": "99"},
    )
    assert response.status_code == 422, response.text
    assert "movements" in response.text, response.text


def test_recommendations_are_period_scoped_and_get_is_read_only_by_default(
    client, db_session, org_a_setup
):
    headers = org_a_setup["headers"]
    org_id = org_a_setup["org"].id
    income_category = org_a_setup["cat_map"][("Penjualan", "income")]
    expense_category = org_a_setup["cat_map"][("Operasional", "expense")]

    for tx_date in ("2026-01-10", "2026-02-10"):
        assert _post_transaction(
            client, headers, income_category, "income", "1000.00", tx_date
        ).status_code == 201
        assert _post_transaction(
            client, headers, expense_category, "expense", "950.00", tx_date
        ).status_code == 201

    # GET default tidak menulis histori.
    read_only = client.get(
        "/api/v1/recommendations",
        headers=headers,
        params={"from": "2026-01-01", "to": "2026-01-31"},
    )
    assert read_only.status_code == 200, read_only.text
    assert read_only.json()["persisted"] is False
    assert all(rec["id"] is None for rec in read_only.json()["recommendations"])
    assert db_session.query(models.Recommendation).count() == 0

    january = client.get(
        "/api/v1/recommendations",
        headers=headers,
        params={"from": "2026-01-01", "to": "2026-01-31", "persist": "true"},
    )
    assert january.status_code == 200, january.text
    assert january.json()["persisted"] is True
    jan_recs = january.json()["recommendations"]
    assert jan_recs
    assert all(rec["id"] is not None for rec in jan_recs)
    assert all(rec["period"] == {"from": "2026-01-01", "to": "2026-01-31"}
               for rec in jan_recs)

    fixed = client.patch(
        f"/api/v1/recommendations/{jan_recs[0]['id']}",
        headers=headers,
        json={"status": "reviewed"},
    )
    assert fixed.status_code == 200, fixed.text

    january_again = client.get(
        "/api/v1/recommendations",
        headers=headers,
        params={"from": "2026-01-01", "to": "2026-01-31"},
    )
    assert january_again.status_code == 200
    assert january_again.json()["persisted"] is False
    assert january_again.json()["recommendations"][0]["status"] == "reviewed"
    assert db_session.query(models.Recommendation).count() == len(jan_recs)

    february = client.get(
        "/api/v1/recommendations",
        headers=headers,
        params={"from": "2026-02-01", "to": "2026-02-28", "persist": "true"},
    )
    assert february.status_code == 200, february.text
    feb_recs = february.json()["recommendations"]
    assert feb_recs
    assert all(rec["period"] == {"from": "2026-02-01", "to": "2026-02-28"}
               for rec in feb_recs)
    assert {rec["id"] for rec in feb_recs}.isdisjoint(
        {rec["id"] for rec in jan_recs}
    )
    assert db_session.query(models.Recommendation).filter_by(
        organization_id=org_id, period_from=date(2026, 1, 1)
    ).count() == len(jan_recs)


def test_get_health_and_ratios_do_not_persist_without_explicit_flag(
    client, db_session, org_a_setup
):
    headers = org_a_setup["headers"]

    health = client.get(
        "/api/v1/financial/health",
        headers=headers,
        params={"from": "2026-01-01", "to": "2026-01-31"},
    )
    assert health.status_code == 200, health.text
    assert db_session.query(models.RiskSignal).count() == 0

    ratios = client.get(
        "/api/v1/ratios",
        headers=headers,
        params={"from": "2026-01-01", "to": "2026-01-31"},
    )
    assert ratios.status_code == 200, ratios.text
    assert db_session.query(models.RatioSnapshot).count() == 0


def test_llm_fallback_always_available_and_maps_rule_ids(monkeypatch):
    monkeypatch.setattr(llm_adapter, "LLM_ENABLED", False)
    monkeypatch.setattr(llm_adapter, "LLM_PROVIDER", None)
    monkeypatch.setattr(
        llm_adapter, "LLM_CONFIG_ERROR", "GEMINI_API_KEY belum dikonfigurasi."
    )

    result = llm_adapter.generate_explanation({
        "rule_id": "RULE-CF-01",
        "priority": "high",
        "trigger_metrics": {"net_cash_flow": "-1000"},
        "evidence": ["Defisit kas Rp 1.000.000"],
        "suggested_actions": ["Tunda pengeluaran"],
    })

    assert result["source"] == "fallback"
    assert result["llm_enabled"] is False
    assert result["llm_available"] is False
    assert "Arus kas" in result["explanation"]
    assert result["fallback_reason"] == "GEMINI_API_KEY belum dikonfigurasi."
