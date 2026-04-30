import streamlit as st
import pandas as pd
import requests
from datetime import datetime, date
import calendar

# --- CONFIGURARE API ---
BASE_API_URL = "https://sheetdb.io/api/v1/zjfuwwvgqximb"

st.set_page_config(page_title="Buget Pro - Workflow Optimizat", layout="wide")

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

def sterge_rand(nume_tab, coloana, valoare):
    url = f"{BASE_API_URL}/{coloana}/{valoare}?sheet={nume_tab}"
    res = requests.delete(url)
    return res.status_code == 200

# --- LOGICA DE CALCUL DATE ---
df_v = incarca_date("venituri")
df_c = incarca_date("cheltuieli")

total_venituri = int(pd.to_numeric(df_v['suma'], errors='coerce').sum()) if not df_v.empty else 0
total_cheltuieli = int(pd.to_numeric(df_c['suma'], errors='coerce').sum()) if not df_c.empty else 0

# --- SIDEBAR CU EXPANDERE ---
with st.sidebar:
    st.title("⚙️ Panou Control")

    # 1. Configurare Lună - ASCUNS (By default)
    with st.expander("📅 Configurare Lună", expanded=False):
        data_selectata = st.date_input("Data de azi:", date.today())
        ultimul_zi_luna = calendar.monthrange(data_selectata.year, data_selectata.month)[1]
        nr_zile_luna = st.number_input("Zile totale în lună:", min_value=1, value=ultimul_zi_luna)
    
    # 2. Adaugă Venit Nou - ASCUNS (By default)
    with st.expander("💵 Adaugă Venit Nou", expanded=False):
        with st.form("venit_nou", clear_on_submit=True):
            v_suma = st.number_input("Sumă venit (RON):", min_value=0, step=100)
            v_desc = st.text_input("Sursă venit:")
            if st.form_submit_button("Salvează Venit"):
                if v_suma > 0:
                    trimite_date("venituri", data_selectata.strftime("%Y-%m-%d"), v_suma, v_desc)
                    st.rerun()

    # 3. Adaugă Cheltuială - DESCHIS (By default)
    with st.expander("💸 Adaugă Cheltuială", expanded=True):
        with st.form("cheltuiala_noua", clear_on_submit=True):
            c_suma = st.number_input("Sumă cheltuită (RON):", min_value=0, step=1)
            c_desc = st.text_input("Descriere:")
            if st.form_submit_button("Salvează Cheltuiala"):
                if c_suma > 0:
                    trimite_date("cheltuieli", data_selectata.strftime("%Y-%m-%d"), c_suma, c_desc)
                    st.rerun()

# --- CALCUL LOGIC RAPORT ---
ziua_nr = data_selectata.day
alocatie_zilnica = int(total_venituri / nr_zile_luna) if total_venituri > 0 else 0
buget_teoretic_pana_azi = alocatie_zilnica * ziua_nr
sold_disponibil_azi = buget_teoretic_pana_azi - total_cheltuieli

# --- AFIȘARE REZULTATE ---
st.title("⚖️ Status Buget Zilnic")

# Banner principal pentru Bugetul Zilei
if sold_disponibil_azi >= 0:
    st.success(f"## Buget Disponibil Azi: {sold_disponibil_azi} RON")
    st.caption(f"Ai o alocație de {alocatie_zilnica} RON/zi + economiile din zilele trecute.")
else:
    st.error(f"## Buget Disponibil Azi: {sold_disponibil_azi} RON")
    st.warning(f"Atenție! Ai depășit bugetul cumulat cu {abs(sold_disponibil_azi)} RON.")

st.divider()

# Statistici rapide
col_v, col_c, col_s = st.columns(3)
col_v.metric("Venituri Totale", f"{total_venituri} RON")
col_c.metric("Cheltuieli Totale", f"{total_cheltuieli} RON")
col_s.metric("Sold Total în Casă", f"{total_venituri - total_cheltuieli} RON")

st.divider()

# --- TABELE ȘI GESTIONARE ---
st.subheader("📋 Istoric Cheltuieli")
if not df_c.empty:
    # Sortăm cheltuielile să apară cele mai noi primele (opțional)
    for i, row in df_c.iterrows():
        c1, c2, c3, c4 = st.columns([2, 3, 2, 1])
        c1.write(row['data'])
        c2.write(row['descriere'])
        c3.write(f"**{int(float(row['suma']))} RON**")
        if c4.button("❌", key=f"del_c_{i}"):
            sterge_rand("cheltuieli", "descriere", row['descriere'])
            st.rerun()
else:
    st.info("Nu ai cheltuieli înregistrate.")

with st.expander("📊 Vezi Listă Venituri"):
    if not df_v.empty:
        st.dataframe(df_v, use_container_width=True)
    else:
        st.write("Niciun venit înregistrat.")
