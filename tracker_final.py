import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- CONFIGURARE API ---
BASE_API_URL = "https://sheetdb.io/api/v1/zjfuwwvgqximb"

st.set_page_config(page_title="Buget Dinamic Pro", layout="wide")

# --- FUNCȚII COMUNICARE ---
def incarca_date(nume_tab):
    url = f"{BASE_API_URL}?sheet={nume_tab}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            df = pd.DataFrame(response.json())
            return df
    except Exception as e:
        st.error(f"Eroare la citire: {e}")
    return pd.DataFrame()

def trimite_date(nume_tab, data, suma, desc):
    url = f"{BASE_API_URL}?sheet={nume_tab}"
    payload = {"data": [{"data": data, "suma": suma, "descriere": desc}]}
    res = requests.post(url, json=payload)
    return res.status_code == 201

def sterge_rand(nume_tab, coloana, valoare):
    # SheetDB permite stergerea dupa o valoare anume (ex: descriere sau suma)
    url = f"{BASE_API_URL}/{coloana}/{valoare}?sheet={nume_tab}"
    res = requests.delete(url)
    return res.status_code == 200

# --- INTERFAȚĂ ȘI INPUTURI ---
st.title("⚖️ Buget Recalibrat Automat")

with st.sidebar:
    st.header("⚙️ Setări Lună")
    nr_zile_luna = st.number_input("Număr total zile lună:", min_value=1, value=30)
    ziua_actuala = st.slider("În ce zi a lunii suntem?", 1, int(nr_zile_luna), datetime.now().day)
    
    st.divider()
    st.header("➕ Adaugă Tranzacție")
    tip = st.radio("Tip:", ["Cheltuială", "Venit"])
    with st.form("tranzactie_noua", clear_on_submit=True):
        f_suma = st.number_input("Suma (RON):", min_value=0.0)
        f_desc = st.text_input("Descriere:")
        if st.form_submit_button("Salvează"):
            tab = "cheltuieli" if tip == "Cheltuială" else "venituri"
            if trimite_date(tab, datetime.now().strftime("%Y-%m-%d"), f_suma, f_desc):
                st.success("Adăugat!")
                st.rerun()

# --- LOGICA DE CALCUL DINAMIC ---
df_v = incarca_date("venituri")
df_c = incarca_date("cheltuieli")

# Conversie date numerice
total_venituri = pd.to_numeric(df_v['suma'], errors='coerce').sum() if not df_v.empty else 0
total_cheltuieli = pd.to_numeric(df_c['suma'], errors='coerce').sum() if not df_c.empty else 0

# LOGICA SOLICITATĂ:
# Bugetul zilnic se recalculează ca: (Ce am rămas / Zile rămase)
zile_ramase = (nr_zile_luna - ziua_actuala) + 1 # +1 ca să includem și ziua de azi
sold_total_actual = total_venituri - total_cheltuieli
buget_zilnic_recalculat = sold_total_actual / zile_ramase if zile_ramase > 0 else 0

# --- AFIȘARE METRICI ---
c1, c2, c3 = st.columns(3)
c1.metric("Sold Total Rămas", f"{sold_total_actual:,.2f} RON")
c2.metric("Zile Rămase", f"{zile_ramase} zile")
c3.metric("BUGET DISPONIBIL AZI", f"{buget_zilnic_recalculat:,.2f} RON", 
          help="Acestă sumă se recalculează automat la fiecare venit/cheltuială nouă.")

st.divider()

# --- TABEL CHELTUIELI CU OPȚIUNE DE ȘTERGERE ---
st.subheader("💸 Gestionare Cheltuieli")
if not df_c.empty:
    # Creăm coloane pentru tabel (Descriere, Sumă, Acțiune)
    for i, row in df_c.iterrows():
        col_d, col_s, col_b = st.columns([3, 2, 1])
        col_d.write(row['descriere'])
        col_s.write(f"{float(row['suma']):,.2f} RON")
        # Buton de ștergere pentru fiecare rând
        if col_b.button("Șterge", key=f"del_{i}"):
            if sterge_rand("cheltuieli", "descriere", row['descriere']):
                st.warning(f"S-a șters: {row['descriere']}")
                st.rerun()
else:
    st.info("Nu sunt cheltuieli înregistrate.")

with st.expander("📊 Vezi Istoric Venituri"):
    st.table(df_v)
