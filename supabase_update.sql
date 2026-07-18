-- SQL untuk Update Tabel (Tanpa menghapus data lama)
-- Jalankan ini di Supabase SQL Editor

ALTER TABLE meteran_actual_logs
ADD COLUMN IF NOT EXISTS log_time TIME DEFAULT '00:00:00',
ADD COLUMN IF NOT EXISTS sisa_token NUMERIC,
ADD COLUMN IF NOT EXISTS is_topup BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS topup_amount NUMERIC DEFAULT 0;

-- Karena kita pakai timestamp sekarang, kita perlu merubah unique constraint
-- Supaya kita bisa nyatet beberapa kali dalam sehari (kalau mau)
-- Tapi buat amannya, kita keep log_date unique per hari aja biar gampang,
-- atau kita ganti jadi unique (user_key, log_date, log_time)?
-- Kita biarin constraint yang lama (user_key, log_date) biar 1 hari cuma ada 1 catatan akhir.
