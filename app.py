import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- CONFIGURARE ---
# Pune aici URL-ul API de la SheetDB.io
BASE_API_URL = "https://sheetdb.io/api/v1/ID_UL_TAU_AICI"

st.set_page_config(page_title="Buget Tracker v2", layout="wide")

def incarca_date(nume_tab):
    url = f"{BASE_API_URL}?sheet={nume_tab}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return pd.DataFrame(response.json())
    except:
        pass
    return pd.DataFrame()

def trimite_date(nume_tab, data, suma, desc):
    url = f"{BASE_API_URL}?sheet={nume_tab}"
    payload = {"data": [{"data": data, "suma": suma, "descriere": desc}]}
    res = requests.post(url, json=payload)
    return res.status_code == 201

st.title("💰 Tracker Finanțe Personale")

# Meniu Lateral
with st.sidebar:
    st.header("Introducere Date")
    tip = st.radio("Tip tranzacție:", ["Cheltuială", "Venit"])
    tab_dest = "cheltuieli" if tip == "Cheltuială" else "venituri"
    
    with st.form("form_intrare", clear_on_submit=True):
        f_data = st.date_input("Data:", datetime.now())
        f_suma = st.number_input("Suma (RON):", min_value=0.0)
        f_desc = st.text_input("Descriere:")
        
        if st.form_submit_button("Salvează Datele"):
            if f_suma > 0:
                data_str = f_data.strftime("%Y-%m-%d")
                if trimite_date(tab_dest, data_str, f_suma, f_desc):
                    st.success(f"Înregistrat în {tab_dest}!")
                    st.rerun()
                else:
                    st.error("Eroare la API SheetDB.")

# Încărcare și Calcule
df_v = incarca_date("venituri")
df_c = incarca_date("cheltuieli")

v_total = pd.to_numeric(df_v['suma'], errors='coerce').sum() if not df_v.empty else 0.0
c_total = pd.to_numeric(df_c['suma'], errors='coerce').sum() if not df_c.empty else 0.0

# Afișare Metrics
c1, c2, c3 = st.columns(3)
c1.metric("Venituri", f"{v_total:,.2f} RON")
c2.metric("Cheltuieli", f"{c_total:,.2f} RON", delta_color="inverse")
c3.metric("Sold Actual", f"{v_total - c_total:,.2f} RON")

st.divider()

# Tabele
col_v, col_c = st.columns(2)
with col_v:
    st.subheader("📋 Istoric Venituri")
    st.dataframe(df_v, use_container_width=True)
with col_c:
    st.subheader("💸 Istoric Cheltuieli")
    st.dataframe(df_c, use_container_width=True)
