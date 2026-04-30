import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import calendar

# --- CONFIGURARE ---
# 1. Link-ul către tabelul Google Sheets (format CSV pentru citire)
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/ID_TABEL/export?format=csv"

# 2. Link-ul către Google Form (pentru scriere)
# Înlocuiește 'entry.XXXXX' cu numerele tale din Pasul 2
FORM_URL = "https://docs.google.com/forms/d/e/ID_FORMULAR/formResponse"

def trimite_date(data, suma, descriere):
    payload = {
        "entry.11111": data,      # Pune ID-ul tău pentru dată
        "entry.22222": suma,      # Pune ID-ul tău pentru sumă
        "entry.33333": descriere  # Pune ID-ul tău pentru descriere
    }
    requests.post(FORM_URL, data=payload)

# --- INTERFAȚĂ ---
st.set_page_config(page_title="Buget Tracker Simplu", layout="centered")

# Parolă simplă
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    pwd = st.text_input("Parola:", type="password")
    if st.button("Logare"):
        if pwd == "secret123":
            st.session_state.auth = True
            st.rerun()
    st.stop()

# --- LOGICA APLICAȚIEI ---
st.title("💰 Buget Tracker Gratuit")

# Citire date (GRATIS)
df = pd.read_csv(SHEET_CSV_URL)
df['data'] = pd.to_datetime(df['data'], errors='coerce')

# Venit (îl putem lăsa momentan fix în cod sau într-un câmp)
venit_luna = st.sidebar.number_input("Venit lunar:", value=3100)

# Formular adăugare
with st.form("add_form", clear_on_submit=True):
    f_suma = st.number_input("Suma:", min_value=0)
    f_desc = st.text_input("Descriere:")
    f_data = st.date_input("Data:", datetime.now())
    
    if st.form_submit_button("Salvează Cheltuiala"):
        if f_suma > 0:
            trimite_date(f_data.strftime("%Y-%m-%d"), f_suma, f_desc)
            st.success("Trimis către Google Sheets! Durează câteva secunde să apară.")
            st.rerun()

# Calculele rămân aceleași (folosind df-ul citit de sus)
# ... (restul logicii de calcul sold disponibil)
