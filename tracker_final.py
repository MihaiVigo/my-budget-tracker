import streamlit as st
import pandas as pd
import requests
from datetime import datetime, date
import calendar

# --- CONFIGURARE API ---
BASE_API_URL = "https://sheetdb.io/api/v1/zjfuwwvgqximb"

st.set_page_config(page_title="Buget Pro - Resetabil", layout="wide")

# --- FUNCȚII COMUNICARE ---
def incarca_date(nume_tab):
    url = f"{BASE_API_URL}?sheet={nume_tab}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return pd.DataFrame(response.json())
    except:
        pass
    return pd.DataFrame()

def trimite_date(nume_tab, data, suma, desc):
    url = f"{BASE_API_URL}?sheet={nume_tab}"
    payload = {"data": [{"data": data, "suma": int(suma), "descriere": desc}]}
    res = requests.post(url, json=payload)
    return res.status_code == 201

def curata_tot_tabelul(nume_tab):
    """Șterge toate datele dintr-un tab folosind un query de tip 'mai mare de -1'"""
    url = f"{BASE_API_URL}/suma/>/-1?sheet={nume_tab}"
    res = requests.delete(url)
    return res.status_code == 200

# --- LOGICA DE CALCUL DATE ---
df_v = incarca_date("venituri")
df_c = incarca_date("cheltuieli")

total_venituri = int(pd.to_numeric(df_v['suma'], errors='coerce').sum()) if not df_v.empty else 0
total_cheltuieli = int(pd.to_numeric(df_c['suma'], errors='coerce').sum()) if not df_c.empty else 0

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Administrare")

    # 1. Configurare Timp
    with st.expander("📅 Configurare Timp", expanded=False):
        data_selectata = st.date_input("Data de azi:", date.today())
        ultimul_zi_luna = calendar.monthrange(data_selectata.year, data_selectata.month)[1]
        nr_zile_luna = st.number_input("Zile totale în lună:", min_value=1, value=ultimul_zi_luna)
    
    # 2. Adaugă Venit Nou
    with st.expander("💵 Adaugă Venit Nou", expanded=False):
        with st.form("venit_nou", clear_on_submit=True):
            v_suma = st.number_input("Sumă venit (RON):", min_value=0, step=100)
            v_desc = st.text_input("Sursă venit:")
            if st.form_submit_button("Salvează Venit"):
                if v_suma > 0:
                    trimite_date("venituri", data_selectata.strftime("%Y-%m-%d"), v_suma, v_desc)
                    st.rerun()

    # 3. Adaugă Cheltuială - DESCHIS (Implicit)
    with st.expander("💸 Adaugă Cheltuială", expanded=True):
        with st.form("cheltuiala_noua", clear_on_submit=True):
            c_suma = st.number_input("Sumă (RON):", min_value=0, step=1)
            c_desc = st.text_input("Descriere:")
            if st.form_submit_button("Salvează Cheltuiala"):
                if c_suma > 0:
                    trimite_date("cheltuieli", data_selectata.strftime("%Y-%m-%d"), c_suma, c_desc)
                    st.rerun()

    st.divider()
    
    # 4. RESET TOTAL (Funcția care a confirmat că merge)
    st.subheader("🚨 Resetare Date")
    if st.button("Șterge Toate VENITURILE"):
        if curata_tot_tabelul("venituri"):
            st.success("Tabelul de venituri a fost golit!")
            st.rerun()
            
    if st.button("Șterge Toate CHELTUIELILE"):
        if curata_tot_tabelul("cheltuieli"):
            st.success("Tabelul de cheltuieli a fost golit!")
            st.rerun()

# --- CALCUL LOGIC ---
ziua_nr = data_selectata.day
alocatie_zilnica = int(total_venituri / nr_zile_luna) if total_venituri > 0 else 0
buget_teoretic_pana_azi = alocatie_zilnica * ziua_nr
sold_disponibil_azi = buget_teoretic_pana_azi - total_cheltuieli

# --- AFIȘARE REZULTATE ---
st.title("⚖️ Status Buget Zilnic")

# Afișare buget principal
if sold_disponibil_azi >= 0:
    st.success(f"## Buget Disponibil Azi: {sold_disponibil_azi} RON")
else:
    st.error(f"## Buget Disponibil Azi: {sold_disponibil_azi} RON")

st.divider()

# Tabele de vizualizare simplă
col1, col2 = st.columns(2)

with col1:
    st.subheader("📋 Venituri")
    if not df_v.empty:
        st.dataframe(df_v[['data', 'descriere', 'suma']], use_container_width=True)
    else:
        st.caption("Niciun venit salvat.")

with col2:
    st.subheader("💸 Cheltuieli")
    if not df_c.empty:
        st.dataframe(df_c[['data', 'descriere', 'suma']], use_container_width=True)
    else:
        st.caption("Nicio cheltuială salvată.")

st.divider()
st.caption(f"Venit total: {total_venituri} RON | Cheltuieli totale: {total_cheltuieli} RON | Alocație fixă: {alocatie_zilnica} RON/zi")
