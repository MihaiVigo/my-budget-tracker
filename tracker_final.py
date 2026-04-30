import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- CONFIGURARE ---
# Pune aici URL-ul tău de la SheetDB.io
# Exemplu: https://sheetdb.io/api/v1/abcd123456789
BASE_API_URL = "https://sheetdb.io/api/v1/zjfuwwvgqximb"

st.set_page_config(page_title="Buget Tracker Pro", layout="wide")

# --- FUNCȚII COMUNICARE ---
def incarca_date(nume_tab):
    """Citeste datele dintr-un tab specific"""
    url = f"{BASE_API_URL}?sheet={nume_tab}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return pd.DataFrame(response.json())
    except Exception as e:
        st.error(f"Eroare la citire tab {nume_tab}: {e}")
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
    try:
        res = requests.post(url, json=payload, timeout=10)
        return res.status_code == 201
    except Exception as e:
        st.error(f"Eroare la trimitere: {e}")
        return False

# --- INTERFAȚĂ UTILIZATOR ---
st.title("💰 Manager Finanțe Personale")
st.info("Sistem conectat la Google Sheets via SheetDB")

# Sidebar pentru introducere date
with st.sidebar:
    st.header("Adaugă Tranzacție")
    tip_tranzactie = st.radio("Tipul operațiunii:", ["Cheltuială", "Venit"])
    
    # Mapare pe numele tab-urilor din Google Sheets
    tab_destinatie = "cheltuieli" if tip_tranzactie == "Cheltuială" else "venituri"
    
    with st.form("formular_intrare", clear_on_submit=True):
        f_data = st.date_input("Data:", datetime.now())
        f_suma = st.number_input("Suma (RON):", min_value=0.0, step=1.0)
        f_desc = st.text_input("Descriere / Sursă:")
        
        sub_buton = st.form_submit_button(f"Salvează în {tab_destinatie}")
        
        if sub_buton:
            if f_suma > 0:
                data_formatata = f_data.strftime("%Y-%m-%d")
                if trimite_date(tab_destinatie, data_formatata, f_suma, f_desc):
                    st.success(f"✅ {tip_tranzactie} înregistrată cu succes!")
                    st.rerun()
                else:
                    st.error("❌ Eroare la salvare. Verifică conexiunea SheetDB.")
            else:
                st.warning("⚠️ Introdu o sumă mai mare decât 0.")

# --- LOGICA DE CALCUL ȘI AFIȘARE ---
# Încărcăm datele din tab-urile specifice
df_v = incarca_date("venituri")
df_c = incarca_date("cheltuieli")

# Convertim coloanele de sumă la format numeric pentru calcule
v_val = pd.to_numeric(df_v['suma'], errors='coerce').sum() if not df_v.empty else 0.0
c_val = pd.to_numeric(df_c['suma'], errors='coerce').sum() if not df_c.empty else 0.0
sold_total = v_val - c_val

# Panou de control (Metrics)
m1, m2, m3 = st.columns(3)
m1.metric("Venituri Totale", f"{v_val:,.2f} RON")
m2.metric("Cheltuieli Totale", f"{c_val:,.2f} RON", delta_color="inverse")
m3.metric("Sold Actual", f"{sold_total:,.2f} RON")

st.divider()

# Tabele detaliate
col_venit, col_chelt = st.columns(2)

with col_venit:
    st.subheader("📋 Istoric Venituri")
    if not df_v.empty:
        st.dataframe(df_v.iloc[::-1], use_container_width=True)
    else:
        st.caption("Niciun venit înregistrat încă.")

with col_chelt:
    st.subheader("💸 Istoric Cheltuieli")
    if not df_c.empty:
        st.dataframe(df_c.iloc[::-1], use_container_width=True)
    else:
        st.caption("Nicio cheltuială înregistrată încă.")

# Buton de forțare actualizare
if st.button("🔄 Actualizează Tabelele"):
    st.rerun()
