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
        try:
            df = pd.read_csv(FILE_NAME)
            # Conversie de bază la încărcare
            df['data'] = pd.to_datetime(df['data'], errors='coerce')
            return df.dropna(subset=['data'])
        except:
            return pd.DataFrame(columns=['data', 'suma', 'descriere'])
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
data_now = datetime.now()

with st.expander("⚙️ Setări", expanded=False):
    col_a, col_b = st.columns(2)
    with col_a:
        venit_luna = st.number_input("Suma totală lună (RON):", value=int(venit_memorat), step=1)
        if st.button("Salvează Suma"):
            salveaza_setari(venit_luna)
            st.success("Salvat!")
            st.rerun()
    with col_b:
        zile_luna = calendar.monthrange(data_now.year, data_now.month)[1]
        nr_zile = st.number_input("Zile în lună:", value=int(zile_luna), step=1)
    
    buget_fix_zi = int(venit_luna / nr_zile) if nr_zile > 0 else 0
    st.info(f"Buget fix: {buget_fix_zi} RON / zi")

# 2. DATE
df_cheltuieli = incarca_date()

# 3. FORMULAR INTRODUCERE
with st.form("add_form", clear_on_submit=True):
    col_s, col_d = st.columns([1, 2])
    with col_s:
        suma = st.number_input("Suma:", min_value=0, step=1)
    with col_d:
        desc = st.text_input("Descriere:")
    
    data_input = st.date_input("Data:", data_now)
    submit = st.form_submit_button("Adaugă")

    if submit and suma > 0:
        # Creăm intrarea nouă asigurându-ne că data este datetime
        noua_intrare = pd.DataFrame({
            'data': [pd.to_datetime(data_input)],
            'suma': [int(suma)],
            'descriere': [desc]
        })
        df_cheltuieli = pd.concat([df_cheltuieli, noua_intrare], ignore_index=True)
        salveaza_date(df_cheltuieli)
        st.rerun()

# --- 4. LOGICA DE CALCUL (SOLUȚIA FINALĂ PENTRU EROARE) ---
ziua_curenta_nr = data_now.day
sold_reportat = 0

# ASIGURARE CRITICĂ: Forțăm coloana să fie datetime înainte de orice calcul .dt
df_cheltuieli['data'] = pd.to_datetime(df_cheltuieli['data'], errors='coerce')

# Calculăm soldul reportat (zilele trecute)
for zi in range(1, ziua_curenta_nr):
    data_zi_target = datetime(data_now.year, data_now.month, zi).date()
    # Verificăm dacă df nu e gol pentru a evita erori la filtrare
    if not df_cheltuieli.empty:
        mask = df_cheltuieli['data'].dt.date == data_zi_target
        cheltuieli_zi = int(df_cheltuieli[mask]['suma'].sum())
    else:
        cheltuieli_zi = 0
    sold_reportat = (sold_reportat + buget_fix_zi) - cheltuieli_zi

# Calculăm cheltuielile de azi
if not df_cheltuieli.empty:
    cheltuieli_azi = int(df_cheltuieli[df_cheltuieli['data'].dt.date == data_now.date()]['suma'].sum())
else:
    cheltuieli_azi = 0

sold_disponibil_azi = int((buget_fix_zi + sold_reportat) - cheltuieli_azi)

# 5. AFIȘARE
st.divider()

if sold_disponibil_azi >= 0:
    st.success(f"### SOLD DISPONIBIL AZI: {sold_disponibil_azi} RON")
else:
    st.error(f"### SOLD DISPONIBIL AZI: {sold_disponibil_azi} RON")

col1, col2 = st.columns(2)
col1.metric("Din zile trecute", f"{int(sold_reportat)} RON")
col2.metric("Cheltuit azi", f"{int(cheltuieli_azi)} RON")

# 6. ISTORIC
if not df_cheltuieli.empty:
    st.divider()
    st.subheader("📜 Istoric")
    df_vis = df_cheltuieli.copy()
    df_vis['data'] = df_vis['data'].dt.strftime('%d-%m-%Y')
    st.dataframe(df_vis.sort_index(ascending=False), use_container_width=True)

    with st.expander("🗑️ Șterge"):
        idx = st.number_input("ID de șters:", min_value=0, max_value=int(df_cheltuieli.index.max()), step=1)
        if st.button("Confirmă"):
            df_cheltuieli = df_cheltuieli.drop(idx)
            salveaza_date(df_cheltuieli)
            st.rerun()
