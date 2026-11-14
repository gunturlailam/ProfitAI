# 🚀 GEMINI AI SETUP GUIDE

## Step 1: Get Gemini API Key (5 menit)

1. **Buka Google AI Studio**: https://aistudio.google.com/
2. **Login** dengan Google account Anda
3. **Klik "Get API Key"** di menu kiri
4. **Create API Key** → Pilih project atau buat baru
5. **Copy API Key** yang dihasilkan

## Step 2: Configure API Key

Edit file `backend/.env` dan tambahkan:

```env
# Gemini AI Configuration
GEMINI_API_KEY=AIzaSy...your_actual_key_here
```

**PENTING:** 
- Ganti `your_actual_key_here` dengan API key yang sudah di-copy
- Jangan commit API key ke Git!
- File `.env` sudah ada di `.gitignore`

## Step 3: Verify Installation

Jalankan test:

```bash
cd backend
python test_gemini_integration.py
```

Jika berhasil, Anda akan melihat:
```
✓ LLM Adapter works!
✓ Explanation generated from LLM
```

## Step 4: Test API Endpoint

### A. Jalan backend dulu:
```bash
cd backend
uvicorn app.main:app --reload
```

### B. Register user (di terminal baru):
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "demo@profitai.id",
    "password": "demo123456",
    "full_name": "Demo User",
    "organization_name": "Demo Business",
    "industry": "F&B"
  }'
```

### C. Test explain endpoint:

1. **Login:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "demo@profitai.id", "password": "demo123456"}'
```

Copy `access_token` dari response.

2. **Call explain endpoint:**
```bash
curl -X POST "http://localhost:8000/api/v1/ratios/CR/explain?from=2026-10-01&to=2026-10-31" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## Expected Response

Jika berhasil, response akan seperti:

```json
{
  "ratio_code": "CR",
  "ratio_name": "Current Ratio",
  "category": "liquidity",
  "value": "4.7032",
  "display": "4.70x",
  "band": "above_target",
  "status": "available",
  "explanation": "Current Ratio Anda saat ini sangat baik di 4.70x...",
  "action": "1. Pertahankan buffer kas... 2. Evaluasi...",
  "source": "llm",
  "llm_enabled": true,
  "llm_available": true,
  "model": "gemini-1.5-flash",
  "disclaimer": "Narasi ini bersifat informatif..."
}
```

## Troubleshooting

### ❌ Error: "Gemini not configured"
- **Cause:** API key belum diset
- **Fix:** Pastikan `GEMINI_API_KEY` ada di `.env` dan valuenya benar

### ❌ Error: "Invalid API key"
- **Cause:** API key salah atau expired
- **Fix:** Generate API key baru di Google AI Studio

### ❌ Error: "Quota exceeded"
- **Cause:** Free tier limit tercapai
- **Fix:** Tunggu reset (daily limit) atau upgrade plan

### ❌ Warning: "FutureWarning deprecated package"
- **Cause:** Package `google-generativeai` deprecated
- **Fix:** Ini hanya warning, masih berfungsi normal untuk sekarang
- **Note:** Google merekomendasikan migrate ke `google-genai` package di future

### ✓ Fallback Mode
Jika Gemini error, system otomatis fallback ke rule-based narrative.
Check field `source`:
- `"source": "llm"` → AI-generated
- `"source": "fallback"` → Rule-based
- `"source": "cache"` → From cache

## Free Tier Limits

Google AI Studio free tier (as of 2024):
- **15 requests per minute (RPM)**
- **1 million tokens per minute (TPM)**  
- **1,500 requests per day (RPD)**

Ini **CUKUP** untuk:
- Demo dan testing
- Early users (< 100 user aktif/hari)
- Development environment

Untuk production dengan user lebih banyak, pertimbangkan:
- Implement rate limiting per user
- Cache aggressive (current: 1 hour)
- Monitor usage di Google Cloud Console

## Next Steps

Setelah Gemini berfungsi:
1. ✅ Test endpoint explain untuk semua rasio (CR, QR, DER, dll)
2. ✅ Implement toast notification di frontend
3. ✅ Build AI Agent UI component
4. ✅ Add WebSocket for real-time updates

Happy coding! 🚀
