import streamlit as st
import pandas as pd
from datetime import datetime
import calendar
import os

# --- CONFIGURARE ---
FILE_NAME = "date_cheltuieli.csv"

def incarca_date():
    if os.path.exists(FILE_NAME):
        return pd.read_csv(FILE_NAME)
    return pd.DataFrame(columns=['data', 'suma', 'descriere'])

def salveaza_date(df):
    df.to_csv(FILE_NAME, index=False)

# --- INTERFAȚA ---
st.set_page_config(page_title="Buget Tracker CSV", layout="centered")
st.title("💰 Tracker Buget Dinamic (CSV)")

# 1. INTRODUCERE BUGET LUNAR
with st.expander("⚙️ Setări Buget Lună Curentă", expanded=True):
    col_a, col_b = st.columns(2)
    with col_a:
        venit_luna = st.number_input("Venituri / Suma disponibilă (RON):", value=5000)
    with col_b:
        data_now = datetime.now()
        zile_default = calendar.monthrange(data_now.year, data_now.month)[1]
        nr_zile = st.number_input("Număr zile lună:", value=zile_default)

    buget_zi = venit_luna / nr_zile
    st.info(f"Buget calculat: **{buget_zi:.2f} RON / zi**")

# 2. LOGICA DE DATE
df_cheltuieli = incarca_date()

with st.form("adaugă_cheltuială"):
    st.subheader("💳 Introdu cheltuială")
    suma_noua = st.number_input("Suma cheltuită (RON):", min_value=0.0, step=5.0)
    desc_noua = st.text_input("Descriere:")
    submit = st.form_submit_button("Salvează în CSV")

    if submit and suma_noua > 0:
        noua_intrare = pd.DataFrame({
            'data': [data_now.strftime("%Y-%m-%d")],
            'suma': [suma_noua],
            'descriere': [desc_noua]
        })
        df_cheltuieli = pd.concat([df_cheltuieli, noua_intrare], ignore_index=True)
        salveaza_date(df_cheltuieli)
        st.success("Date salvate cu succes!")

# 3. CALCUL DINAMIC
zi_curenta = data_now.day
total_cheltuit = df_cheltuieli['suma'].sum()

# Logica de reportare: (Buget zi * zile trecute) - tot ce s-a cheltuit
buget_teoretic_pana_azi = buget_zi * zi_curenta
sold_disponibil_azi = buget_teoretic_pana_azi - total_cheltuit

# 4. AFIȘARE METRICI
c1, c2 = st.columns(2)
c1.metric("Sold Disponibil AZI", f"{sold_disponibil_azi:.2f} RON")
c2.metric("Total Cheltuit", f"{total_cheltuit:.2f} RON")

if sold_disponibil_azi < 0:
    st.warning(f"Atenție! Esti pe minus cu {abs(sold_disponibil_azi):.2f} RON.")

# Afișare istoric
if not df_cheltuieli.empty:
    st.subheader("Istoric Cheltuieli")
    st.dataframe(df_cheltuieli.sort_values(by='data', ascending=False), use_container_width=True)
    
    if st.button("Șterge tot istoricul (Reset)"):
        if os.path.exists(FILE_NAME):
            os.remove(FILE_NAME)
            st.rerun()
