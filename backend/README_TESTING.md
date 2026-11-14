# Backend Testing

**Status terakhir:** 2026-11-14 (setelah audit defect)

Dokumen ini menggantikan klaim status sebelumnya. Isinya hanya yang benar-benar
dijalankan dan diverifikasi.

## Prasyarat

```bash
cd backend
..\venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Menjalankan test backend

```bash
cd backend
..\venv\Scripts\python.exe -m pytest tests -q
```

Hasil terakhir:

```text
40 passed, 3 warnings in 24.30s
```

Warning yang tersisa berasal dari deprecation `on_event` FastAPI/Starlette dan
`httpx` di TestClient; bukan kegagalan test.

Test yang tersedia:

- `tests/test_transactions.py`
  - reversal tidak menghasilkan efek negatif;
  - forecast mengabaikan baris reversal;
  - create → list → update → reverse → summary;
  - filter `tx_type`, `category_id`, `search`;
  - tenant isolation.
- `tests/test_ratio_engine.py`
  - 16 rasio dengan hitungan manual;
  - threshold/band;
  - input hilang → `unavailable`;
  - denominator nol tidak menjadi 0;
  - ekuitas negatif → DER/ROE tidak bermakna;
  - saldo awal hilang → rata-rata memakai saldo akhir + `partial`;
  - annualisasi `INV_TURN`, `TATO`, `ROA`, `ROE`;
  - validasi field input.
- `tests/test_ratio_service.py`
  - mapping DB → `RatioInputs`;
  - snapshot persist/upsert;
  - balance sheet dan `unavailable` + alasan;
  - threshold efektif dan validasi role/urutan.
- `tests/test_ratios_api.py`
  - auth dan validasi tanggal;
  - endpoint ratios/neraca/threshold/explain;
  - tenant isolation.
- `tests/test_ratio_narrative.py`
  - fallback tanpa API key;
  - sanitasi payload;
  - validasi output LLM;
  - tidak ada kegagalan saat LLM tidak tersedia.
- `tests/test_regressions.py`
  - `net_profit`/`net_margin` unavailable tanpa COGS lengkap;
  - viewer read-only, member boleh transaksi;
  - audit event transaksi tersimpan;
  - period close memblokir create dan reversal;
  - PATCH stok langsung ditolak;
  - rekomendasi period-scoped, GET default read-only, `persist=true` eksplisit;
  - GET health/ratios tanpa `persist` tidak menulis;
  - fallback LLM dan mapping `RULE-*` → template `REC-*`.

Test memakai SQLite sementara (`test_profitai.db`) dan **tidak** menyentuh
database PostgreSQL aplikasi.

## Menjalankan backend

```bash
cd backend
..\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## Alembic

Baseline: `migrations/versions/15249a199165_baseline_schema_with_ratio_cfo.py`.
Head saat ini: `migrations/versions/b7c1e5d9f2a1_recommendation_period_scope.py`
(kolom periode + index rekomendasi). Keduanya sudah diterapkan ke PostgreSQL
lokal dan `alembic check` melaporkan tidak ada operasi baru.

Baseline lama yang rusak disimpan di
`migrations/legacy/64b8ce576449_create_profitai_all_17_tables.py.bak`.

```bash
cd backend
..\venv\Scripts\python.exe -m alembic upgrade head
..\venv\Scripts\python.exe -m alembic check
```

Database PostgreSQL demo yang sudah berisi data direkonsiliasi secara aditif:

```bash
cd backend
..\venv\Scripts\python.exe scripts\reconcile_schema.py
```

Script tersebut menambah kolom/tabel yang belum ada, tidak menghapus data, lalu
melakukan `alembic stamp` ke head. Jangan jalankan tanpa backup pada database
produksi.

## Data demo

Database PostgreSQL berisi:

- data historis 2024 (dari `seed_demo.py` / CSV demo);
- 161 transaksi demo 2025-12 s/d 2026-11 (dari `seed_demo_2026.py`);
- 13 balance snapshot dan data pendukung rasio (dari
  `seed_balance_sheet_2026.py`);
- total 273 transaksi, 1 organisasi, 1 user demo.

Seed idempotent:

```bash
cd backend
..\venv\Scripts\python.exe seed_demo_2026.py
..\venv\Scripts\python.exe seed_balance_sheet_2026.py
```

Kredensial demo:

- Email: `demo@profitai.local`
- Password: `Demo12345!`

## Status frontend (terkait kontrak backend)

```bash
cd frontend
npm run lint
npm run typecheck
npm run test:ci
npm run build
```

Hasil terakhir: lint tanpa error/warning, typecheck lulus, build lulus,
45 test frontend lulus (8 suite).

## Batasan yang masih terbuka

- Halaman `/ratios` sudah terhubung ke API. Halaman detail rasio, form neraca,
  tutup/buka periode, tren, aging, proyeksi, dan UI threshold belum ada.
- Endpoint `GET /ratios` default tidak menulis. `persist=true` menyimpan
  `ratio_snapshots` sebagai cache/audit; nilai tetap dihitung ulang setiap
  request. `GET /recommendations` mengikuti aturan yang sama.
- `INV_TURN`, `TATO`, `ROA`, dan `ROE` disetahunkan (`365 / hari`), sehingga
  periode pendek bisa fluktuatif dan selalu diberi warning.
- Bulan berjalan (November MTD) dapat berstatus `partial` karena
  `REV_GROWTH` tidak punya pembanding pendapatan yang cukup.
- `net_profit` formal tetap `unavailable` sampai COGS, pendapatan lain, biaya
  keuangan, dan pajak terklasifikasi lengkap. `operating_profit` pada P&L
  adalah surplus sederhana dan wajib diberi label estimasi di UI.
- LLM bersifat opsional. Provider yang didukung: Gemini (REST/`httpx`, default
  bila `GEMINI_API_KEY` ada) dan OpenAI (jika paket `openai` terpasang).
  Tanpa API key atau saat provider gagal, narasi fallback tetap berfungsi dan
  alasan fallback dikembalikan ke client.
