-- =========================================================
-- Meteran — Supabase Schema Setup
-- Jalankan SQL ini di Supabase > SQL Editor
-- =========================================================

-- 1. Daftar peralatan untuk tab Proyeksi
CREATE TABLE IF NOT EXISTS meteran_items (
    id          BIGSERIAL PRIMARY KEY,
    user_key    TEXT NOT NULL DEFAULT 'default',
    name        TEXT NOT NULL,
    watt        NUMERIC NOT NULL,
    qty         NUMERIC NOT NULL DEFAULT 1,
    hours       NUMERIC NOT NULL DEFAULT 1,
    created_at  TIMESTAMPTZ DEFAULT now()
);

-- 2. Log pemakaian kWh harian (tab Aktual)
CREATE TABLE IF NOT EXISTS meteran_actual_logs (
    id          BIGSERIAL PRIMARY KEY,
    user_key    TEXT NOT NULL DEFAULT 'default',
    log_date    DATE NOT NULL,
    kwh         NUMERIC NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT now(),
    UNIQUE(user_key, log_date)
);

-- 3. Settings tarif per user
CREATE TABLE IF NOT EXISTS meteran_settings (
    user_key    TEXT PRIMARY KEY DEFAULT 'default',
    daya_index  INT NOT NULL DEFAULT 3,
    tarif       NUMERIC NOT NULL DEFAULT 1444,
    updated_at  TIMESTAMPTZ DEFAULT now()
);

-- Row Level Security (biarkan open untuk app personal)
ALTER TABLE meteran_items         ENABLE ROW LEVEL SECURITY;
ALTER TABLE meteran_actual_logs   ENABLE ROW LEVEL SECURITY;
ALTER TABLE meteran_settings      ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow all for anon" ON meteran_items         FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all for anon" ON meteran_actual_logs   FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all for anon" ON meteran_settings      FOR ALL USING (true) WITH CHECK (true);
