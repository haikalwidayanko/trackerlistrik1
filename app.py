import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date, datetime
from supabase import create_client, Client

st.set_page_config(page_title="Meteran ⚡", page_icon="⚡", layout="wide")

# ── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Manrope:wght@400;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Manrope', sans-serif; }
.stApp { background: linear-gradient(135deg,#0D1420 0%,#111c2d 100%); }
.metric-card {
    background:#151F2F; border:1px solid #28344a; border-radius:14px;
    padding:16px 20px; margin-bottom:10px;
}
.metric-card .label {
    font-family:'Space Mono',monospace; font-size:10px; letter-spacing:.12em;
    text-transform:uppercase; color:#8592A6; margin-bottom:4px;
}
.metric-card .value { font-size:22px; font-weight:800; }
.amber { color:#FFB020; }
.teal  { color:#34D6B4; }
.item-row {
    background:#1B2738; border:1px solid #28344a; border-radius:10px;
    padding:10px 14px; margin-bottom:8px; display:flex;
    align-items:center; justify-content:space-between;
}
.item-name { font-weight:700; font-size:14px; }
.item-meta { font-family:'Space Mono',monospace; font-size:11px; color:#8592A6; margin-top:2px; }
.item-cost { font-family:'Space Mono',monospace; color:#34D6B4; font-size:13px; }
.proj-banner {
    background:linear-gradient(135deg,rgba(255,176,32,.12),rgba(52,214,180,.08));
    border:1px solid #7a5a1f; border-radius:12px; padding:18px; margin-top:14px;
}
.proj-banner .big { font-size:28px; font-weight:800; color:#FFB020; }
.section-title {
    font-family:'Space Mono',monospace; font-size:11px; letter-spacing:.14em;
    text-transform:uppercase; color:#8592A6; margin:18px 0 10px;
}
div[data-testid="stTabs"] button { font-family:'Manrope',sans-serif; font-weight:700; }
</style>
""", unsafe_allow_html=True)

# ── Supabase ─────────────────────────────────────────────────────────────────
@st.cache_resource
def get_supabase() -> Client:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

db = get_supabase()
USER_KEY = "default"

# ── Data Appliances ───────────────────────────────────────────────────────────
CATEGORIES = [
    {"category":"AC / Pendingin Ruangan","items":[
        {"name":"AC 1/2 PK Non-Inverter","watt":380},{"name":"AC 1/2 PK Inverter","watt":350},
        {"name":"AC 3/4 PK Standar","watt":600},{"name":"AC 1 PK Non-Inverter","watt":870},
        {"name":"AC 1 PK Inverter","watt":650},{"name":"AC 1.5 PK","watt":1010},{"name":"AC 2 PK","watt":1500}]},
    {"category":"Kulkas","items":[
        {"name":"Kulkas 1 Pintu Hemat","watt":40},{"name":"Kulkas 1 Pintu Standar","watt":65},
        {"name":"Kulkas 2 Pintu Inverter","watt":70},{"name":"Kulkas 2 Pintu Standar","watt":140},
        {"name":"Kulkas 2 Pintu Besar","watt":220}]},
    {"category":"TV","items":[
        {"name":"TV LED 32\"","watt":48},{"name":"TV LED 43\"","watt":80},
        {"name":"TV LED 50\" Smart","watt":85},{"name":"TV LED 55\"","watt":145}]},
    {"category":"Rice Cooker","items":[
        {"name":"Rice Cooker (memasak)","watt":375},{"name":"Rice Cooker (menghangatkan)","watt":60}]},
    {"category":"Mesin Cuci","items":[
        {"name":"Mesin Cuci 2 Tabung","watt":300},{"name":"Mesin Cuci Top Loading","watt":350},
        {"name":"Mesin Cuci Front Loading","watt":300}]},
    {"category":"Kipas Angin","items":[
        {"name":"Kipas Meja Mini","watt":20},{"name":"Kipas Berdiri 16\"","watt":55},
        {"name":"Exhaust Fan","watt":15}]},
    {"category":"Pompa Air","items":[
        {"name":"Pompa 125W","watt":125},{"name":"Pompa 200W","watt":200},
        {"name":"Pompa Jet 250W","watt":250}]},
    {"category":"Water Heater","items":[
        {"name":"Water Heater 10L","watt":200},{"name":"Water Heater 30L","watt":350}]},
    {"category":"Elektronik & Lainnya","items":[
        {"name":"Lampu LED","watt":10},{"name":"Lampu Pijar","watt":40},
        {"name":"Charger HP","watt":10},{"name":"Laptop / PC","watt":65},
        {"name":"Router WiFi","watt":10},{"name":"Lainnya (isi manual)","watt":100}]},
]

TARIF_PRESETS = [
    {"label":"450 VA (Subsidi)","tarif":415},
    {"label":"900 VA (Subsidi)","tarif":605},
    {"label":"900 VA (Non-subsidi)","tarif":1352},
    {"label":"1300 VA","tarif":1444},
    {"label":"2200 VA","tarif":1444},
    {"label":"3500–5500 VA","tarif":1699},
    {"label":"6600 VA ke atas","tarif":1699},
]

# ── DB helpers ────────────────────────────────────────────────────────────────
def load_items():
    res = db.table("meteran_items").select("*").eq("user_key", USER_KEY).order("id").execute()
    return res.data or []

def load_logs():
    res = db.table("meteran_actual_logs").select("*").eq("user_key", USER_KEY).order("log_date").execute()
    return res.data or []

def load_settings():
    res = db.table("meteran_settings").select("*").eq("user_key", USER_KEY).execute()
    if res.data:
        return res.data[0]
    return {"daya_index": 3, "tarif": 1444}

def save_settings(daya_index, tarif):
    db.table("meteran_settings").upsert({
        "user_key": USER_KEY, "daya_index": daya_index,
        "tarif": float(tarif), "updated_at": datetime.utcnow().isoformat()
    }, on_conflict="user_key").execute()

def add_item(name, watt, qty, hours):
    db.table("meteran_items").insert({
        "user_key": USER_KEY, "name": name,
        "watt": float(watt), "qty": float(qty), "hours": float(hours)
    }).execute()

def delete_item(item_id):
    db.table("meteran_items").delete().eq("id", item_id).execute()

def upsert_log(log_date: str, log_time: str, sisa_token: float, kwh: float, is_topup: bool, topup_amount: float):
    data = {
        "user_key": USER_KEY, "log_date": log_date, "kwh": float(kwh)
    }
    if sisa_token is not None:
        data["log_time"] = log_time
        data["sisa_token"] = float(sisa_token)
        data["is_topup"] = is_topup
        data["topup_amount"] = float(topup_amount)
        
    db.table("meteran_actual_logs").upsert(data, on_conflict="user_key,log_date").execute()

def delete_log(log_id):
    db.table("meteran_actual_logs").delete().eq("id", log_id).execute()

def reset_items():
    db.table("meteran_items").delete().eq("user_key", USER_KEY).execute()

def reset_logs():
    db.table("meteran_actual_logs").delete().eq("user_key", USER_KEY).execute()

# ── Format helpers ────────────────────────────────────────────────────────────
def fmt_rp(n):
    return "Rp{:,.0f}".format(n).replace(",", ".")

def fmt_kwh(n):
    return f"{n:.2f} kWh"

# ── Load initial data ─────────────────────────────────────────────────────────
if "app_loaded" not in st.session_state:
    st.session_state.app_loaded = True
    st.session_state.appliances = load_items()
    st.session_state.logs = load_logs()
    cfg = load_settings()
    st.session_state.daya_index = cfg.get("daya_index", 3)
    st.session_state.tarif = float(cfg.get("tarif", 1444))

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="border-bottom:1px solid #28344a;padding-bottom:18px;margin-bottom:18px;">
  <p style="font-family:'Space Mono',monospace;font-size:11px;letter-spacing:.18em;text-transform:uppercase;color:#FFB020;margin:0 0 4px;">
    Simulasi & Pemantauan Konsumsi Daya
  </p>
  <h1 style="margin:0;font-size:32px;font-weight:800;letter-spacing:-.02em;">⚡ Meteran</h1>
  <p style="color:#8592A6;margin:6px 0 0;font-size:14px;">
    Simulasikan pemakaian peralatan, atau catat kWh harian untuk proyeksi tagihan bulanan.
  </p>
</div>
""", unsafe_allow_html=True)

# ── Settings bar ──────────────────────────────────────────────────────────────
col_s1, col_s2, col_s3 = st.columns([2, 1, 3])
with col_s1:
    daya_labels = [t["label"] for t in TARIF_PRESETS]
    new_daya = st.selectbox("Daya Terpasang", daya_labels,
                            index=st.session_state.daya_index, key="daya_sel")
    new_daya_idx = daya_labels.index(new_daya)
    if new_daya_idx != st.session_state.daya_index:
        st.session_state.daya_index = new_daya_idx
        st.session_state.tarif = float(TARIF_PRESETS[new_daya_idx]["tarif"])
        save_settings(new_daya_idx, st.session_state.tarif)
        st.rerun()

with col_s2:
    new_tarif = st.number_input("Tarif (Rp/kWh)", value=st.session_state.tarif,
                                 step=1.0, key="tarif_inp")
    if new_tarif != st.session_state.tarif:
        st.session_state.tarif = new_tarif
        save_settings(st.session_state.daya_index, new_tarif)

tarif = st.session_state.tarif

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["📊 Proyeksi Peralatan", "📅 Aktual Pemakaian Harian"])

# ════════════════════════════════════════════════════════════════════════════════
# TAB 1 — PROYEKSI
# ════════════════════════════════════════════════════════════════════════════════
with tab1:
    left, right = st.columns([1.2, 0.9], gap="large")

    with left:
        st.markdown('<div class="section-title">Tambah Peralatan</div>', unsafe_allow_html=True)

        cat_names = [c["category"] for c in CATEGORIES]
        sel_cat = st.selectbox("Kategori", cat_names, key="cat_sel")
        cat_idx = cat_names.index(sel_cat)
        items_in_cat = CATEGORIES[cat_idx]["items"]
        item_labels = [f"{i['name']} (~{i['watt']}W)" for i in items_in_cat]

        sel_item_label = st.selectbox("Merk / Model", item_labels, key="item_sel")
        sel_item_idx = item_labels.index(sel_item_label)
        auto_watt = items_in_cat[sel_item_idx]["watt"]

        c1, c2, c3 = st.columns(3)
        with c1:
            watt_in = st.number_input("Daya (Watt)", value=float(auto_watt), min_value=1.0, step=10.0)
        with c2:
            qty_in = st.number_input("Jumlah Unit", value=1, min_value=1, step=1)
        with c3:
            hours_in = st.number_input("Jam / Hari", value=1.0, min_value=0.5, step=0.5)

        if st.button("➕ Tambahkan ke Daftar", use_container_width=True, type="primary"):
            name = items_in_cat[sel_item_idx]["name"]
            add_item(name, watt_in, qty_in, hours_in)
            st.session_state.appliances = load_items()
            st.rerun()

        if st.button("🗑️ Hapus Semua Peralatan", use_container_width=True):
            if st.session_state.get("confirm_reset_items"):
                reset_items()
                st.session_state.appliances = []
                st.session_state.confirm_reset_items = False
                st.rerun()
            else:
                st.session_state.confirm_reset_items = True
                st.warning("Klik sekali lagi untuk konfirmasi hapus semua peralatan.")

        st.markdown('<div class="section-title">Daftar Peralatan</div>', unsafe_allow_html=True)
        items_data = st.session_state.get("appliances", [])
        if not items_data:
            st.info("Belum ada peralatan. Tambahkan peralatan di atas untuk mulai simulasi.")
        else:
            for it in items_data:
                kwh = (it["watt"] * it["qty"] * it["hours"]) / 1000
                cost = kwh * tarif
                qty_label = f" ×{int(it['qty'])}" if it["qty"] > 1 else ""
                col_a, col_b = st.columns([5, 1])
                with col_a:
                    st.markdown(f"""
                    <div class="item-row">
                      <div>
                        <div class="item-name">🔌 {it['name']}{qty_label}</div>
                        <div class="item-meta">{it['watt']}W · {it['hours']}j/hari · {kwh:.2f} kWh</div>
                      </div>
                      <div class="item-cost">{fmt_rp(cost)}/hari</div>
                    </div>
                    """, unsafe_allow_html=True)
                with col_b:
                    if st.button("✕", key=f"del_{it['id']}"):
                        delete_item(it["id"])
                        st.session_state.appliances = load_items()
                        st.rerun()

    with right:
        st.markdown('<div class="section-title">Estimasi Meteran</div>', unsafe_allow_html=True)
        items_data = st.session_state.get("appliances", [])
        total_watt = sum(it["watt"] * it["qty"] for it in items_data)
        total_kwh_day = sum((it["watt"] * it["qty"] * it["hours"]) / 1000 for it in items_data)
        cost_day = total_kwh_day * tarif
        cost_month = cost_day * 30

        st.markdown(f"""
        <div class="metric-card">
          <div class="label">Total kWh / Hari</div>
          <div class="value amber">{total_kwh_day:.2f} kWh</div>
        </div>
        """, unsafe_allow_html=True)

        m1, m2 = st.columns(2)
        with m1:
            st.markdown(f"""
            <div class="metric-card">
              <div class="label">Biaya / Hari</div>
              <div class="value amber">{fmt_rp(cost_day)}</div>
            </div>""", unsafe_allow_html=True)
        with m2:
            st.markdown(f"""
            <div class="metric-card">
              <div class="label">Biaya / Bulan</div>
              <div class="value teal">{fmt_rp(cost_month)}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown(f"""
        <div class="metric-card">
          <div class="label">Total Daya Terpakai</div>
          <div class="value">{total_watt:,.0f} Watt</div>
        </div>""", unsafe_allow_html=True)

        if items_data:
            st.markdown('<div class="section-title">Breakdown Biaya</div>', unsafe_allow_html=True)
            breakdown = []
            for it in items_data:
                kwh = (it["watt"] * it["qty"] * it["hours"]) / 1000
                breakdown.append({"name": it["name"], "cost": kwh * tarif})
            breakdown.sort(key=lambda x: x["cost"], reverse=True)
            max_cost = max(b["cost"] for b in breakdown) or 1

            fig_bar = go.Figure(go.Bar(
                x=[b["cost"] for b in breakdown],
                y=[b["name"] for b in breakdown],
                orientation="h",
                marker=dict(
                    color=[b["cost"] for b in breakdown],
                    colorscale=[[0, "#34D6B4"], [1, "#FFB020"]],
                    showscale=False
                ),
                text=[fmt_rp(b["cost"]) for b in breakdown],
                textposition="outside",
                textfont=dict(color="#EDF1F7", size=11)
            ))
            fig_bar.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=0, r=60, t=10, b=0),
                height=max(160, len(breakdown) * 36),
                xaxis=dict(showticklabels=False, showgrid=False, zeroline=False),
                yaxis=dict(tickfont=dict(color="#8592A6", size=11), autorange="reversed"),
                font=dict(family="Space Mono, monospace")
            )
            st.plotly_chart(fig_bar, use_container_width=True)

# ════════════════════════════════════════════════════════════════════════════════
# TAB 2 — AKTUAL PEMAKAIAN
# ════════════════════════════════════════════════════════════════════════════════
with tab2:
    left2, right2 = st.columns([1.1, 1], gap="large")

    with left2:
        st.markdown('<div class="section-title">Catat Sisa Token Hari Ini</div>', unsafe_allow_html=True)
        st.caption("Masukkan angka sisa kWh di meteran. Sistem otomatis menghitung pemakaianmu.")

        c1, c2 = st.columns(2)
        with c1:
            date_in = st.date_input("Tanggal", value=date.today(), key="log_date")
        with c2:
            time_in = st.time_input("Jam", value=datetime.now().time(), key="log_time")
            
        sisa_token_in = st.number_input("Sisa Token di Meteran (kWh)", min_value=0.0, step=0.1, format="%.2f", key="log_token")
        
        is_topup = st.checkbox("Saya isi/beli token baru hari ini", key="log_is_topup")
        topup_amount = 0.0
        if is_topup:
            topup_amount = st.number_input("Jumlah Beli Token (kWh)", min_value=0.0, step=0.1, format="%.2f")

        if st.button("➕ Catat Token", use_container_width=True, type="primary"):
            logs = st.session_state.logs
            # Cari data token sebelumnya
            prev_logs = [l for l in logs if l["log_date"] < str(date_in) and l.get("sisa_token") is not None]
            
            kwh_calc = 0.0
            if prev_logs:
                prev_log = sorted(prev_logs, key=lambda x: x["log_date"])[-1]
                prev_token = prev_log.get("sisa_token", 0)
                if is_topup:
                    kwh_calc = (prev_token + topup_amount) - sisa_token_in
                else:
                    kwh_calc = prev_token - sisa_token_in
                
                # Cegah minus jika user salah ketik
                if kwh_calc < 0: kwh_calc = 0.0
            else:
                st.warning("Catatan token pertama! Pemakaian kWh hari ini dicatat 0, akan dihitung normal besok.")

            upsert_log(str(date_in), str(time_in)[:8], sisa_token_in, kwh_calc, is_topup, topup_amount)
            st.session_state.logs = load_logs()
            st.success(f"✅ Tersimpan! Pemakaian dihitung: {kwh_calc:.2f} kWh")
            st.rerun()

        if st.button("🗑️ Hapus Semua Riwayat", use_container_width=True):
            if st.session_state.get("confirm_reset_logs"):
                reset_logs()
                st.session_state.logs = []
                st.session_state.confirm_reset_logs = False
                st.rerun()
            else:
                st.session_state.confirm_reset_logs = True
                st.warning("Klik sekali lagi untuk konfirmasi hapus semua riwayat.")

        st.markdown('<div class="section-title">Riwayat Pemakaian</div>', unsafe_allow_html=True)
        logs = st.session_state.logs
        if not logs:
            st.info("Belum ada catatan. Mulai catat dari hari ini!")
        else:
            sorted_logs = sorted(logs, key=lambda x: x["log_date"], reverse=True)
            for lg in sorted_logs:
                cost = lg["kwh"] * tarif
                d = datetime.strptime(lg["log_date"], "%Y-%m-%d")
                date_label = d.strftime("%d %b %Y")
                time_label = lg.get("log_time", "")
                if time_label: time_label = time_label[:5] # "HH:MM"
                
                sisa_str = f"Sisa: {lg['sisa_token']} kWh" if lg.get("sisa_token") is not None else "Data Lama"
                if lg.get("is_topup"): sisa_str += f" (+{lg.get('topup_amount')} kWh)"
                
                c_a, c_b = st.columns([5, 1])
                with c_a:
                    st.markdown(f"""
                    <div class="item-row">
                      <div>
                        <div class="item-name">📅 {date_label} {time_label}</div>
                        <div class="item-meta">{lg['kwh']:.2f} kWh terpakai · {sisa_str}</div>
                      </div>
                      <div class="item-cost">{fmt_rp(cost)}</div>
                    </div>""", unsafe_allow_html=True)
                with c_b:
                    if st.button("✕", key=f"del_log_{lg['id']}"):
                        delete_log(lg["id"])
                        st.session_state.logs = load_logs()
                        st.rerun()

    with right2:
        logs = st.session_state.logs
        if logs:
            sorted_asc = sorted(logs, key=lambda x: x["log_date"])
            dates_label = [datetime.strptime(l["log_date"], "%Y-%m-%d").strftime("%d/%m") for l in sorted_asc]
            kwh_vals = [l["kwh"] for l in sorted_asc]

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=dates_label, y=kwh_vals, mode="lines+markers",
                line=dict(color="#FFB020", width=2.5),
                marker=dict(color="#FFB020", size=7),
                fill="tozeroy",
                fillcolor="rgba(255,176,32,0.12)",
                name="kWh/hari"
            ))
            fig.update_layout(
                paper_bgcolor="rgba(21,31,47,1)", plot_bgcolor="rgba(21,31,47,1)",
                margin=dict(l=10, r=10, t=20, b=10),
                height=220,
                xaxis=dict(tickfont=dict(color="#8592A6", size=10, family="Space Mono"),
                           gridcolor="#28344a", zeroline=False),
                yaxis=dict(tickfont=dict(color="#8592A6", size=10, family="Space Mono"),
                           gridcolor="#28344a", zeroline=False, title="kWh"),
                showlegend=False,
                font=dict(color="#EDF1F7")
            )
            st.markdown('<div class="section-title">Tren Pemakaian Harian</div>', unsafe_allow_html=True)
            st.plotly_chart(fig, use_container_width=True)

            total_kwh = sum(l["kwh"] for l in logs)
            avg_kwh = total_kwh / len(logs)
            now = date.today()
            import calendar
            days_in_month = calendar.monthrange(now.year, now.month)[1]
            proj_kwh = avg_kwh * days_in_month
            proj_cost = proj_kwh * tarif

            st.markdown(f"""
            <div class="proj-banner">
              <div class="label" style="font-family:'Space Mono',monospace;font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:#8592A6;">
                Proyeksi Biaya Bulan Ini
              </div>
              <div class="big">{fmt_rp(proj_cost)}</div>
              <div style="color:#8592A6;font-size:12px;margin-top:6px;line-height:1.6;">
                Berdasarkan rata-rata <strong style="color:#EDF1F7;">{avg_kwh:.2f} kWh/hari</strong>
                dari {len(logs)} catatan × {days_in_month} hari bulan ini,
                tarif {fmt_rp(tarif)}/kWh.
              </div>
            </div>""", unsafe_allow_html=True)

            st.markdown("")
            m1, m2 = st.columns(2)
            with m1:
                st.markdown(f"""
                <div class="metric-card">
                  <div class="label">Rata-rata / Hari</div>
                  <div class="value teal">{avg_kwh:.2f} kWh</div>
                </div>""", unsafe_allow_html=True)
            with m2:
                st.markdown(f"""
                <div class="metric-card">
                  <div class="label">Total Tercatat</div>
                  <div class="value">{total_kwh:.2f} kWh</div>
                </div>""", unsafe_allow_html=True)
        else:
            st.info("Chart & proyeksi akan muncul setelah ada data tercatat.")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<p style="text-align:center;color:#8592A6;font-family:'Space Mono',monospace;font-size:11px;margin-top:40px;">
  Database watt disusun dari spesifikasi merk populer per Juli 2026.
  Angka aktual bisa beda tipis per model — kolom watt tetap bisa diedit manual.
</p>""", unsafe_allow_html=True)
