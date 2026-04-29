import streamlit as st
import pandas as pd
from datetime import datetime
import calendar
import os

# --- CONFIGURARE FIȘIER ---
FILE_NAME = "date_cheltuieli.csv"

def incarca_date():
    if os.path.exists(FILE_NAME):
        df = pd.read_csv(FILE_NAME)
        df['data'] = pd.to_datetime(df['data'])
        return df
    return pd.DataFrame(columns=['data', 'suma', 'descriere'])

def salveaza_date(df):
    df.to_csv(FILE_NAME, index=False)

# --- INTERFAȚA ---
st.set_page_config(page_title="Buget Tracker Secvențial", layout="centered")
st.title("💰 Tracker Buget cu Reportare")

# 1. SETĂRI BUGET
with st.expander("⚙️ Setări Buget", expanded=False):
    col_a, col_b = st.columns(2)
    with col_a:
        venit_luna = st.number_input("Suma totală lună (RON):", value=3100.0)
    with col_b:
        data_now = datetime.now()
        zile_luna = calendar.monthrange(data_now.year, data_now.month)[1]
        nr_zile = st.number_input("Zile în lună:", value=zile_luna)
    
    buget_fix_zi = venit_luna / nr_zile
    st.info(f"Buget fix alocat: **{buget_fix_zi:.2f} RON / zi**")

# 2. DATE
df_cheltuieli = incarca_date()

# 3. FORMULAR
with st.form("add_form", clear_on_submit=True):
    col_s, col_d = st.columns([1, 2])
    with col_s:
        suma = st.number_input("Suma:", min_value=0.0, step=1.0)
    with col_d:
        desc = st.text_input("Descriere:")
    
    # Opțiune de a alege data (pentru a putea introduce cheltuieli din zile trecute)
    data_input = st.date_input("Data cheltuielii:", data_now)
    submit = st.form_submit_button("Salvează cheltuiala")

    if submit and suma > 0:
        noua_intrare = pd.DataFrame({
            'data': [pd.to_datetime(data_input)],
            'suma': [suma],
            'descriere': [desc]
        })
        df_cheltuieli = pd.concat([df_cheltuieli, noua_intrare], ignore_index=True)
        salveaza_date(df_cheltuieli)
        st.rerun()

# 4. LOGICA DE CALCUL SECVENȚIALĂ (Logica ta)
# Calculăm soldul reportat de la ziua 1 până la ziua de ieri
ziua_curenta_nr = data_now.day
sold_reportat = 0.0

# Parcurgem fiecare zi de la începutul lunii până ieri
for zi in range(1, ziua_curenta_nr):
    data_zi = data_now.replace(day=zi).strftime('%Y-%m-%d')
    # Cheltuieli în acea zi specifică
    cheltuieli_zi = df_cheltuieli[df_cheltuieli['data'].dt.strftime('%Y-%m-%d') == data_zi]['suma'].sum()
    # Soldul zilei respective se adaugă la ce am reportat deja
    sold_reportat = (sold_reportat + buget_fix_zi) - cheltuieli_zi

# Soldul disponibil pentru ziua de azi
cheltuieli_azi = df_cheltuieli[df_cheltuieli['data'].dt.strftime('%Y-%m-%d') == data_now.strftime('%Y-%m-%d')]['suma'].sum()
sold_disponibil_azi = (buget_fix_zi + sold_reportat) - cheltuieli_azi

# 5. AFIȘARE
st.divider()
st.subheader(f"Statistici Ziua {ziua_curenta_nr}")

c1, c2 = st.columns(2)
c1.metric("Sold Disponibil AZI", f"{sold_disponibil_azi:.2f} RON")
c2.metric("Reportat din zile trecute", f"{sold_reportat:.2f} RON")

if sold_disponibil_azi < 0:
    st.error(f"Ai depășit bugetul! Diferența de {abs(sold_disponibil_azi):.2f} RON va fi trasă din ziua de mâine.")
else:
    st.success(f"Ești în grafic. Mâine vei începe cu {sold_disponibil_azi:.2f} + {buget_fix_zi:.2f} RON (dacă nu mai cheltuiești nimic azi).")

# 6. ISTORIC
if not df_cheltuieli.empty:
    st.divider()
    st.subheader("📜 Istoric")
    df_vis = df_cheltuieli.copy()
    df_vis['data'] = df_vis['data'].dt.strftime('%d-%m-%Y')
    st.dataframe(df_vis.sort_values(by='data', ascending=False), use_container_width=True)

    with st.expander("🗑️ Șterge înregistrare"):
        idx = st.number_input("ID rând:", min_value=0, max_value=len(df_cheltuieli)-1, step=1)
        if st.button("Confirmă ștergere"):
            df_cheltuieli = df_cheltuieli.drop(df_cheltuieli.index[idx])
            salveaza_date(df_cheltuieli)
            st.rerun()
