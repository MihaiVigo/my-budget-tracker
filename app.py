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
        # Ne asigurăm că avem o coloană de index pentru ștergere
        return df
    return pd.DataFrame(columns=['data', 'suma', 'descriere'])

def salveaza_date(df):
    df.to_csv(FILE_NAME, index=False)

# --- INTERFAȚA ---
st.set_page_config(page_title="Buget Tracker", layout="centered")
st.title("💰 Tracker Buget Dinamic")

# 1. SETĂRI BUGET (Închis implicit conform cerinței)
with st.expander("⚙️ Setări Buget Lună Curentă", expanded=False):
    col_a, col_b = st.columns(2)
    with col_a:
        venit_luna = st.number_input("Venituri / Suma disponibilă (RON):", value=5000.0)
    with col_b:
        data_now = datetime.now()
        zile_default = calendar.monthrange(data_now.year, data_now.month)[1]
        nr_zile = st.number_input("Număr zile lună:", value=zile_default)

    buget_zi = venit_luna / nr_zile
    st.info(f"Buget zilnic alocat: **{buget_zi:.2f} RON / zi**")

# 2. ÎNCĂRCARE DATE
df_cheltuieli = incarca_date()

# 3. FORMULAR INTRODUCERE
with st.form("adaugă_cheltuială", clear_on_submit=True):
    st.subheader("💳 Introdu cheltuială")
    suma_noua = st.number_input("Suma (RON):", min_value=0.0, step=1.0)
    desc_noua = st.text_input("Descriere (ex: Factură, Mâncare):")
    submit = st.form_submit_button("Salvează")

    if submit and suma_noua > 0:
        noua_intrare = pd.DataFrame({
            'data': [data_now.strftime("%Y-%m-%d")],
            'suma': [suma_noua],
            'descriere': [desc_noua]
        })
        df_cheltuieli = pd.concat([df_cheltuieli, noua_intrare], ignore_index=True)
        salveaza_date(df_cheltuieli)
        st.success("Salvat!")
        st.rerun()

# 4. LOGICA DE CALCUL CORECTATĂ
zi_curenta = data_now.day
total_cheltuit = df_cheltuieli['suma'].sum()

# Calcul: Cât ar fi trebuit să am până azi (buget zilnic * nr zile trecute) MINUS tot ce am cheltuit
buget_cumulat_pana_azi = buget_zi * zi_curenta
sold_disponibil_azi = buget_cumulat_pana_azi - total_cheltuit

# 5. AFIȘARE METRICI
c1, c2 = st.columns(2)
with c1:
    st.metric("Sold Disponibil AZI", f"{sold_disponibil_azi:.2f} RON")
with c2:
    st.metric("Total Cheltuit Lună", f"{total_cheltuit:.2f} RON")

if sold_disponibil_azi < 0:
    st.error(f"Ești pe MINUS cu {abs(sold_disponibil_azi):.2f} RON.")
else:
    st.success(f"Ești pe PLUS. Poți cheltui {sold_disponibil_azi:.2f} RON azi.")

# 6. ISTORIC ȘI ȘTERGERE
if not df_cheltuieli.empty:
    st.divider()
    st.subheader("📜 Istoric Cheltuieli")
    
    # Adăugăm un index vizibil pentru utilizator
    df_afisare = df_cheltuieli.copy()
    df_afisare.index.name = "ID"
    st.dataframe(df_afisare, use_container_width=True)

    # Secțiune pentru ștergere
    with st.expander("🗑️ Șterge o cheltuială greșită"):
        id_de_sters = st.number_input("Introdu ID-ul rândului de șters:", min_value=0, max_value=len(df_cheltuieli)-1, step=1)
        if st.button("Confirmă Ștergerea"):
            df_cheltuieli = df_cheltuieli.drop(df_cheltuieli.index[id_de_sters])
            salveaza_date(df_cheltuieli)
            st.success(f"Rândul {id_de_sters} a fost șters!")
            st.rerun()
