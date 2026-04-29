import streamlit as st
import pandas as pd
from datetime import datetime
import calendar
import os

# --- CONFIGURARE FIȘIERE ---
FILE_NAME = "date_cheltuieli.csv"
SETTINGS_FILE = "setari.csv"

def incarca_date():
    if os.path.exists(FILE_NAME):
        df = pd.read_csv(FILE_NAME)
        df['data'] = pd.to_datetime(df['data'])
        return df
    return pd.DataFrame(columns=['data', 'suma', 'descriere'])

def salveaza_date(df):
    df.to_csv(FILE_NAME, index=False)

def incarca_setari():
    if os.path.exists(SETTINGS_FILE):
        try:
            return int(pd.read_csv(SETTINGS_FILE).iloc[0]['venit_luna'])
        except:
            return 3100
    return 3100

def salveaza_setari(valoare):
    df_setari = pd.DataFrame({'venit_luna': [int(valoare)]})
    df_setari.to_csv(SETTINGS_FILE, index=False)

# --- INTERFAȚA ---
st.set_page_config(page_title="Buget Tracker", layout="centered")
st.title("💰 Tracker Buget")

# 1. SETĂRI BUGET
venit_memorat = incarca_setari()

with st.expander("⚙️ Setări", expanded=False):
    col_a, col_b = st.columns(2)
    with col_a:
        venit_luna = st.number_input("Suma totală lună (RON):", value=int(venit_memorat), step=1)
        if st.button("Salvează Suma"):
            salveaza_setari(venit_luna)
            st.success("Salvat!")
            st.rerun()
    with col_b:
        data_now = datetime.now()
        zile_luna = calendar.monthrange(data_now.year, data_now.month)[1]
        nr_zile = st.number_input("Zile în lună:", value=int(zile_luna), step=1)
    
    buget_fix_zi = int(venit_luna / nr_zile)
    st.info(f"Buget fix: **{buget_fix_zi} RON / zi**")

# 2. DATE
df_cheltuieli = incarca_date()

# 3. FORMULAR INTRODUCERE
with st.form("add_form", clear_on_submit=True):
    col_s, col_d = st.columns([1, 2])
    with col_s:
        suma = st.number_input("Suma cheltuită:", min_value=0, step=1)
    with col_d:
        desc = st.text_input("Descriere:")
    
    data_input = st.date_input("Data:", data_now)
    if st.form_submit_button("Adaugă"):
        if suma > 0:
            noua_intrare = pd.DataFrame({
                'data': [pd.to_datetime(data_input)],
                'suma': [int(suma)],
                'descriere': [desc]
            })
            df_cheltuieli = pd.concat([df_cheltuieli, noua_intrare], ignore_index=True)
            salveaza_date(df_cheltuieli)
            st.rerun()

# 4. LOGICA DE CALCUL (Numere întregi)
ziua_curenta_nr = data_now.day
sold_reportat = 0

for zi in range(1, ziua_curenta_nr):
    data_zi = data_now.replace(day=zi).strftime('%Y-%m-%d')
    cheltuieli_zi = int(df_cheltuieli[df_cheltuieli['data'].dt.strftime('%Y-%m-%d') == data_zi]['suma'].sum())
    sold_reportat = (sold_reportat + buget_fix_zi) - cheltuieli_zi

cheltuieli_azi = int(df_cheltuieli[df_cheltuieli['data'].dt.strftime('%Y-%m-%d') == data_now.strftime('%Y-%m-%d')]['suma'].sum())
sold_disponibil_azi = (buget_fix_zi + sold_reportat) - cheltuieli_azi

# 5. AFIȘARE FORMATATĂ
st.divider()

# Formatare vizuală specială pentru Soldul de azi
if sold_disponibil_azi >= 0:
    color = "inverse" # Verde în Streamlit metrics
    msg_type = "success"
    prefix = "✅"
else:
    color = "normal" # Roșu/Normal
    msg_type = "error"
    prefix = "⚠️"

# Caseta mare pentru Sold
st.markdown(f"""
<div style="background-color:{'#d4edda' if sold_disponibil_azi >= 0 else '#f8d7da'}; 
            padding:20px; 
            border-radius:10px; 
            border: 2px solid {'#c3e6cb' if sold_disponibil_azi >= 0 else '#f5c6cb'};
            text-align: center;">
    <h2 style="color:{'#155724' if sold_disponibil_azi >= 0 else '#721c24'}; margin:0;">
        SOLD DISPONIBIL AZI
    </h2>
    <h1 style="color:{'#155724' if sold_disponibil_azi >= 0 else '#721c24'}; font-size: 50px; margin:10px 0;">
        {int(sold_disponibil_azi)} RON
    </h1>
</div>
""", unsafe_allow_stdio=False, unsafe_allow_html=True)

st.write("") # Spațiu

col1, col2 = st.columns(2)
col1.metric("Reportat ieri", f"{int(sold_reportat)} RON")
col2.metric("Cheltuit azi", f"{int(cheltuieli_azi)} RON")

# 6. ISTORIC
if not df_cheltuieli.empty:
    st.divider()
    st.subheader("📜 Istoric")
    df_vis = df_cheltuieli.copy()
    df_vis['data'] = df_vis['data'].dt.strftime('%d-%m-%Y')
    # Forțăm suma să fie întreg și în tabel
    df_vis['suma'] = df_vis['suma'].astype(int)
    st.dataframe(df_vis.sort_values(by='data', ascending=False), use_container_width=True)

    with st.expander("🗑️ Șterge"):
        idx = st.number_input("ID:", min_value=0, max_value=len(df_cheltuieli)-1, step=1)
        if st.button("Confirmă ștergere"):
            df_cheltuieli = df_cheltuieli.drop(df_cheltuieli.index[idx])
            salveaza_date(df_cheltuieli)
            st.rerun()
