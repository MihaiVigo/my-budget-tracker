import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- CONFIGURARE ---
BASE_API_URL = "https://sheetdb.io/api/v1/zjfuwwvgqximb"

st.set_page_config(page_title="Buget Tracker Multi-Sheet", layout="wide")

# --- FUNCȚII COMUNICARE ---
def incarca_date(nume_tab):
    """Citeste datele dintr-un tab specific"""
    url = f"{BASE_API_URL}?sheet={nume_tab}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return pd.DataFrame(response.json())
    except:
        pass
    return pd.DataFrame()

def trimite_date(nume_tab, data, suma, desc):
    """Trimite date catre un tab specific"""
    url = f"{BASE_API_URL}?sheet={nume_tab}"
    payload = {
        "data": [{
            "data": data,
            "suma": suma,
            "descriere": desc
        }]
    }
    res = requests.post(url, json=payload)
    return res.status_code == 201

# --- INTERFAȚĂ ---
st.title("💰 Gestiune Finanțe (2 Tab-uri)")

# Sidebar pentru Input
with st.sidebar:
    st.header("Adaugă Tranzacție")
    tip_tranzactie = st.radio("Tip tranzacție:", ["Cheltuială", "Venit"])
    
    # Mapăm alegerea utilizatorului pe numele tab-urilor din Google Sheets
    tab_destinatie = "cheltuieli" if tip_tranzactie == "Cheltuială" else "venituri"
    
    with st.form("entry_form", clear_on_submit=True):
        f_data = st.date_input("Data:", datetime.now())
        f_suma = st.number_input("Suma (RON):", min_value=0.0, step=10.0)
        f_desc = st.text_input("Descriere:")
        
        if st.form_submit_button(f"Salvează în {tab_destinatie}"):
            if f_suma > 0:
                succes = trimite_date(tab_destinatie, f_data.strftime("%Y-%m-%d"), f_suma, f_desc)
                if succes:
                    st.success("Salvat!")
                    st.rerun()
                else:
                    st.error("Eroare la salvare.")

# --- LOGICA DE CALCUL ---
df_venituri = incarca_date("venituri")
df_cheltuieli = incarca_date("cheltuieli")

# Calculăm sumele
total_v = pd.to_numeric(df_venituri['suma'], errors='coerce').sum() if not df_venituri.empty else 0.0
total_c = pd.to_numeric(df_cheltuieli['suma'], errors='coerce').sum() if not df_cheltuieli.empty else 0.0
sold = total_v - total_c

# Display Metrics
c1, c2, c3 = st.columns(3)
c1.metric("Total Venituri", f"{total_v:,.2f} RON")
c2.metric("Total Cheltuieli", f"{total_c:,.2f} RON", delta_color="inverse")
c3.metric("Sold Disponibil", f"{sold:,.2f} RON")

st.divider()

# Afișare Tabele
col_v, col_c = st.columns(2)

with col_v:
    st.subheader("Istoric Venituri")
    st.dataframe(df_venituri, use_container_width=True)

with col_c:
    st.subheader("Istoric Cheltuieli")
    st.dataframe(df_cheltuieli, use_container_width=True)
