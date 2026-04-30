import streamlit as st
import pandas as pd
import requests
from datetime import datetime, date
import calendar

# --- CONFIGURARE API ---
BASE_API_URL = "https://sheetdb.io/api/v1/zjfuwwvgqximb"

st.set_page_config(page_title="Buget Zilnic Fix + Rollover", layout="wide")

# --- FUNCȚII COMUNICARE ---
def incarca_date(nume_tab):
    url = f"{BASE_API_URL}?sheet={nume_tab}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return pd.DataFrame(response.json())
    except Exception as e:
        st.error(f"Eroare la citire: {e}")
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

# --- INTERFAȚĂ ---
st.title("⚖️ Buget Fix cu Reportare Zilnică")

with st.sidebar:
    st.header("📅 Configurare")
    data_selectata = st.date_input("Data de azi:", date.today())
    
    # Input pentru Venit/Buget lunar pentru a calcula ratia zilnica
    venit_lunar = st.number_input("Venit lunar total (RON):", min_value=0, value=3000, step=100)
    ultimul_zi_luna = calendar.monthrange(data_selectata.year, data_selectata.month)[1]
    nr_zile_luna = st.number_input("Zile în lună:", min_value=1, value=ultimul_zi_luna)
    
    # Calculăm alocația fixă pe zi
    alocatie_zilnica_fixa = int(venit_lunar / nr_zile_luna)
    st.info(f"Alocația ta fixă este de: **{alocatie_zilnica_fixa} RON / zi**")
    
    st.divider()
    st.header("➕ Adaugă Tranzacție")
    with st.form("tranzactie_noua", clear_on_submit=True):
        f_suma = st.number_input("Suma cheltuită (RON):", min_value=0, step=1)
        f_desc = st.text_input("Descriere cheltuială:")
        if st.form_submit_button("Salvează Cheltuiala"):
            if trimite_date("cheltuieli", data_selectata.strftime("%Y-%m-%d"), f_suma, f_desc):
                st.success("Înregistrat!")
                st.rerun()

# --- LOGICA DE CALCUL (LOGICA SOLICITATĂ) ---
df_c = incarca_date("cheltuieli")
total_cheltuieli = int(pd.to_numeric(df_c['suma'], errors='coerce').sum()) if not df_c.empty else 0

# Ziua curentă (din calendar)
ziua_nr = data_selectata.day

# 1. Bugetul total acumulat până azi (ex: Ziua 2 = 100 + 100 = 200)
buget_total_pana_azi = alocatie_zilnica_fixa * ziua_nr

# 2. Soldul zilei = Bugetul cumulat minus TOT ce s-a cheltuit până în prezent
sold_disponibil_azi = buget_total_pana_azi - total_cheltuieli

# --- AFIȘARE METRICI ---
st.subheader(f"Statistici pentru Ziua {ziua_nr} din {nr_zile_luna}")
c1, c2 = st.columns(2)

with c1:
    st.metric("Alocație Zilnică Fixă", f"{alocatie_zilnica_fixa} RON")

with c2:
    # Colorare în funcție de soldul reportat
    if sold_disponibil_azi >= 0:
        color_hex = "#d4edda" # verde deschis
        text_color = "#155724"
        st.markdown(f"""
            <div style="background-color: {color_hex}; padding: 20px; border-radius: 10px; border: 2px solid {text_color};">
                <h2 style="color: {text_color}; margin: 0;">💰 Buget Disponibil Azi: {sold_disponibil_azi} RON</h2>
                <p style="margin: 0;">(Include cei {alocatie_zilnica_fixa} RON de azi + economiile reportate)</p>
            </div>
        """, unsafe_allow_html=True)
    else:
        color_hex = "#f8d7da" # rosu deschis
        text_color = "#721c24"
        st.markdown(f"""
            <div style="background-color: {color_hex}; padding: 20px; border-radius: 10px; border: 2px solid {text_color};">
                <h2 style="color: {text_color}; margin: 0;">⚠️ Buget Disponibil Azi: {sold_disponibil_azi} RON</h2>
                <p style="margin: 0;">(Ești pe minus cu {abs(sold_disponibil_azi)} RON față de planul tău)</p>
            </div>
        """, unsafe_allow_html=True)

st.divider()

# --- GESTIONARE CHELTUIELI ---
st.subheader("💸 Istoric și Ștergere")
if not df_c.empty:
    for i, row in df_c.iterrows():
        col_dat, col_des, col_sum, col_btn = st.columns([2, 3, 2, 1])
        col_dat.write(row['data'])
        col_des.write(row['descriere'])
        col_sum.write(f"**{int(float(row['suma']))} RON**")
        if col_btn.button("❌", key=f"del_{i}"):
            if sterge_rand("cheltuieli", "descriere", row['descriere']):
                st.rerun()
else:
    st.info("Nicio cheltuială înregistrată.")
