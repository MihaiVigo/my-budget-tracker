import streamlit as st
import pandas as pd
from datetime import datetime
import calendar
import os

# --- CONFIGURARE FIȘIER ---
FILE_NAME = "date_cheltuieli.csv"

def incarca_date():
    if os.path.exists(FILE_NAME):
        return pd.read_csv(FILE_NAME)
    return pd.DataFrame(columns=['data', 'suma', 'descriere'])

def salveaza_date(df):
    df.to_csv(FILE_NAME, index=False)

# --- INTERFAȚA ---
st.set_page_config(page_title="Buget Tracker", layout="centered")
st.title("💰 Tracker Buget Zilnic")

# 1. SETĂRI BUGET (Închis implicit)
with st.expander("⚙️ Setări Buget Lună Curentă", expanded=False):
    col_a, col_b = st.columns(2)
    with col_a:
        venit_luna = st.number_input("Venituri / Suma disponibilă (RON):", value=5000.0)
    with col_b:
        data_now = datetime.now()
        zile_default = calendar.monthrange(data_now.year, data_now.month)[1]
        nr_zile = st.number_input("Număr zile lună:", value=zile_default)

    buget_zi = venit_luna / nr_zile
    st.info(f"Buget alocat fix: **{buget_zi:.2f} RON / zi**")

# 2. ÎNCĂRCARE DATE
df_cheltuieli = incarca_date()

# 3. FORMULAR INTRODUCERE
with st.form("adaugă_cheltuială", clear_on_submit=True):
    st.subheader("💳 Introdu cheltuială")
    suma_noua = st.number_input("Suma (RON):", min_value=0.0, step=1.0)
    desc_noua = st.text_input("Descriere:")
    submit = st.form_submit_button("Salvează")

    if submit and suma_noua > 0:
        noua_intrare = pd.DataFrame({
            'data': [data_now.strftime("%Y-%m-%d")],
            'suma': [suma_noua],
            'descriere': [desc_noua]
        })
        df_cheltuieli = pd.concat([df_cheltuieli, noua_intrare], ignore_index=True)
        salveaza_date(df_cheltuieli)
        st.success("Salvat!")
        st.rerun()

# 4. LOGICA DE CALCUL (Reportare sume)
zi_curenta = data_now.day
total_cheltuit_luna = df_cheltuieli['suma'].sum()

# Calculul corect solicitat:
# Bugetul cumulat pe care ar fi trebuit să îl ai până în acest moment al lunii
buget_total_pana_azi = buget_zi * zi_curenta

# Soldul disponibil pentru restul zilei de azi (include surplus/deficit din zilele trecute)
sold_disponibil_azi = buget_total_pana_azi - total_cheltuit_luna

# 5. AFIȘARE METRICI
st.divider()
col_metrica, col_info = st.columns([1, 1])

with col_metrica:
    if sold_disponibil_azi >= 0:
        st.metric("Sold Disponibil AZI", f"{sold_disponibil_azi:.2f} RON", delta_color="normal")
        st.success(f"Poți cheltui **{sold_disponibil_azi:.2f} RON** până la finalul zilei.")
    else:
        st.metric("Sold Disponibil AZI", f"{sold_disponibil_azi:.2f} RON", delta_color="inverse")
        st.error(f"Ai depășit bugetul cumulat! Ești pe minus cu **{abs(sold_disponibil_azi):.2f} RON**.")

with col_info:
    st.write(f"**Ziua curentă:** {zi_curenta} / {nr_zile}")
    st.write(f"**Total cheltuit lună:** {total_cheltuit_luna:.2f} RON")

# 6. ISTORIC ȘI ȘTERGERE
if not df_cheltuieli.empty:
    st.divider()
    st.subheader("📜 Istoric Cheltuieli")
    
    # Afișăm tabelul cu ID-ul vizibil
    df_with_id = df_cheltuieli.copy()
    df_with_id.index.name = 'ID'
    st.dataframe(df_with_id, use_container_width=True)

    with st.expander("🗑️ Șterge o înregistrare"):
        row_to_delete = st.number_input("Introdu ID-ul rândului de șters:", min_value=0, max_value=len(df_cheltuieli)-1, step=1)
        if st.button("Șterge rândul selectat"):
            df_cheltuieli = df_cheltuieli.drop(df_cheltuieli.index[row_to_delete])
            salveaza_date(df_cheltuieli)
            st.rerun()
