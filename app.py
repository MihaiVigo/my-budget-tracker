import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- CONFIGURARE ---
# AICI lipești URL-ul copiat de pe SheetDB la Pasul 2
BASE_API_URL = "https://sheetdb.io/api/v1/ID_UL_TAU_AICI"

st.set_page_config(page_title="Buget Tracker Multi-Sheet", layout="wide")

# --- FUNCȚII COMUNICARE ---
def incarca_date(nume_tab):
    """Citește datele dintr-un tab specific (venituri sau cheltuieli)"""
    url = f"{BASE_API_URL}?sheet={nume_tab}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return pd.DataFrame(response.json())
    except:
        pass
    return pd.DataFrame()

def trimite_date(nume_tab, data_str, suma_val, desc_val):
    """Trimite date noi către tab-ul specificat"""
    url = f"{BASE_API_URL}?sheet={nume_tab}"
    payload = {
        "data": [{
            "data": data_str,
            "suma": suma_val,
            "descriere": desc_val
        }]
    }
    res = requests.post(url, json=payload)
    return res.status_code == 201

# --- INTERFAȚĂ UTILIZATOR ---
st.title("💰 Gestiune Finanțe: Venituri și Cheltuieli")

# Sidebar pentru introducere date
with st.sidebar:
    st.header("Adaugă Tranzacție Nouă")
    tip_alest = st.radio("Ce dorești să adaugi?", ["Cheltuială", "Venit"])
    
    # Mapăm selecția pe numele tab-urilor din Google Sheets
    tab_destinatie = "cheltuieli" if tip_alest == "Cheltuială" else "venituri"
    
    with st.form("entry_form", clear_on_submit=True):
        f_data = st.date_input("Data:", datetime.now())
        f_suma = st.number_input("Suma (RON):", min_value=0.0, step=1.0)
        f_desc = st.text_input("Descriere:")
        
        if st.form_submit_button(f"Salvează în {tab_destinatie}"):
            if f_suma > 0:
                succes = trimite_date(tab_destinatie, f_data.strftime("%Y-%m-%d"), f_suma, f_desc)
                if succes:
                    st.success(f"Înregistrat cu succes în {tab_destinatie}!")
                    st.rerun()
                else:
                    st.error("Eroare la comunicarea cu Google Sheets.")
            else:
                st.warning("Te rugăm să introduci o sumă validă.")

# --- LOGICA DE CALCUL ȘI AFIȘARE ---
# Încărcăm datele din ambele tab-uri
df_venituri = incarca_date("venituri")
df_cheltuieli = incarca_date("cheltuieli")

# Calculăm totalurile (asigurându-ne că sumele sunt numere)
total_v = pd.to_numeric(df_venituri['suma'], errors='coerce').sum() if not df_venituri.empty else 0.0
total_c = pd.to_numeric(df_cheltuieli['suma'], errors='coerce').sum() if not df_cheltuieli.empty else 0.0
sold_actual = total_v - total_c

# Afișare panou indicatori
c1, c2, c3 = st.columns(3)
c1.metric("Venituri Totale", f"{total_v:,.2f} RON")
c2.metric("Cheltuieli Totale", f"{total_c:,.2f} RON", delta_color="inverse")
c3.metric("Sold Disponibil", f"{sold_actual:,.2f} RON")

st.divider()

# Afișare tabele în coloane
col_v, col_c = st.columns(2)

with col_v:
    st.subheader("📋 Istoric Venituri")
    if not df_venituri.empty:
        st.dataframe(df_venituri.iloc[::-1], use_container_width=True) # Ultimele adăugate apar primele
    else:
        st.info("Nu sunt venituri înregistrate.")

with col_c:
    st.subheader("💸 Istoric Cheltuieli")
    if not df_cheltuieli.empty:
        st.dataframe(df_cheltuieli.iloc[::-1], use_container_width=True)
    else:
        st.info("Nu sunt cheltuieli înregistrate.")

if st.button("🔄 Actualizează Datele"):
    st.rerun()
