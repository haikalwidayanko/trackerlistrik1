# ⚡ Meteran — Tracker Listrik Harian

Aplikasi Streamlit untuk simulasi pemakaian peralatan listrik dan pencatatan kWh harian, dengan penyimpanan data permanen via Supabase.

**GitHub Repo:** `trackerlistrik1`

## Setup

### 1. Buat Supabase Project
1. Buka [supabase.com](https://supabase.com) → New Project
2. Masuk ke **SQL Editor** → jalankan semua isi file `supabase_setup.sql`
3. Catat **Project URL** dan **anon/public key** dari Settings → API

### 2. Jalankan Lokal
```powershell
py -m pip install -r requirements.txt
py -m streamlit run app.py
```
Edit `.streamlit/secrets.toml`, isi URL dan key Supabase kamu:
```toml
[supabase]
url = "https://xxxxx.supabase.co"
key  = "your-anon-key"
```

### 3. Deploy ke Streamlit Cloud
1. Push repo ini ke GitHub repo **`trackerlistrik1`** (pastikan `.streamlit/secrets.toml` ada di `.gitignore` ✅)
2. Buka [share.streamlit.io](https://share.streamlit.io) → **New App** → pilih repo `trackerlistrik1`
3. Di **Advanced settings → Secrets**, paste:
```toml
[supabase]
url = "https://xxxxx.supabase.co"
key  = "your-anon-key"
```
4. Deploy — app langsung bisa diakses dari mana saja! 🚀

## Fitur
- 📊 **Proyeksi**: Tambah peralatan dari database, hitung estimasi tagihan harian & bulanan
- 📅 **Aktual**: Catat kWh harian dari meteran/PLN Mobile, lihat tren & proyeksi bulanan
- ☁️ **Cloud Storage**: Data tersimpan permanen di Supabase, tidak hilang saat refresh
