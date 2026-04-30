import streamlit as st
import pandas as pd
import requests
from datetime import datetime, date
import calendar

# --- CONFIGURARE API ---
BASE_API_URL = "https://sheetdb.io/api/v1/zjfuwwvgqximb"

st.set_page_config(page_title="Buget Stabil", layout="wide")

# --- FUNCȚII ---
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

# --- LOGICA DE CALCUL ---
df_v = incarca_date("venituri")
df_c = incarca_date("cheltuieli")

total_venituri = int(pd.to_numeric(df_v['suma'], errors='coerce').sum()) if not df_v.empty else 0
total_cheltuieli = int(pd.to_numeric(df_c['suma'], errors='coerce').sum()) if not df_c.empty else 0

# --- INTERFAȚĂ ---
st.title("💰 Buget cu Memorare și Venituri Multiple")

with st.sidebar:
    st.header("⚙️ Configurare Lună")
    data_selectata = st.date_input("Data de azi:", date.today())
    ultimul_zi_luna = calendar.monthrange(data_selectata.year, data_selectata.month)[1]
    nr_zile_luna = st.number_input("Zile totale în lună:", min_value=1, value=ultimul_zi_luna)
    
    st.divider()
    st.header("💵 Adaugă Venit Nou")
    with st.form("venit_nou", clear_on_submit=True):
        v_suma = st.number_input("Sumă venit (RON):", min_value=0, step=100)
        v_desc = st.text_input("Sursa (ex: Salariu, Bonus):")
        if st.form_submit_button("Salvează Venit"):
            trimite_date("venituri", data_selectata.strftime("%Y-%m-%d"), v_suma, v_desc)
            st.rerun()

    st.header("💸 Adaugă Cheltuială")
    with st.form("cheltuiala_noua", clear_on_submit=True):
        c_suma = st.number_input("Sumă cheltuită (RON):", min_value=0, step=1)
        c_desc = st.text_input("Descriere:")
        if st.form_submit_button("Salvează Cheltuială"):
            trimite_date("cheltuieli", data_selectata.strftime("%Y-%m-%d"), c_suma, c_desc)
            st.rerun()

# --- CALCUL LOGIC ---
ziua_nr = data_selectata.day

# Alocația zilnică medie se calculează din TOTALUL veniturilor introduse până acum
alocatie_zilnica_medie = int(total_venituri / nr_zile_luna) if total_venituri > 0 else 0

# Bugetul cumulat până în prezent
buget_teoretic_pana_azi = alocatie_zilnica_medie * ziua_nr

# Soldul disponibil AZI (include reportarea)
sold_disponibil_azi = buget_teoretic_pana_azi - total_cheltuieli

# --- AFIȘARE ---
st.info(f"Venit total înregistrat: **{total_venituri} RON** | Alocație: **{alocatie_zilnica_medie} RON / zi**")

if sold_disponibil_azi >= 0:
    st.success(f"### ✅ Buget Disponibil Azi: {sold_disponibil_azi} RON")
else:
    st.error(f"### ⚠️ Buget Disponibil Azi: {sold_disponibil_azi} RON (Ești pe minus!)")

st.divider()

# Tabele pentru vizibilitate
col1, col2 = st.columns(2)
with col1:
    st.subheader("📋 Istoric Venituri")
    st.dataframe(df_v, use_container_width=True)
with col2:
    st.subheader("💸 Istoric Cheltuieli")
    st.dataframe(df_c, use_container_width=True)
