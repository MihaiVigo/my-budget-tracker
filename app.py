import streamlit as st
import pandas as pd
from datetime import datetime
import calendar

# CONFIGURARE PAGINA
st.set_page_config(page_title="Tracker Buget Zilnic", layout="centered")

st.title("💰 Tracker Buget Dinamic")

# 1. SETĂRI BUGET (În mod normal acestea s-ar salva într-o bază de date)
with st.sidebar:
    st.header("Configurare Lună")
    buget_luna = st.number_input("Suma totală pe lună (RON):", value=3000)
    data_azi = datetime.now()
    zile_in_luna = calendar.monthrange(data_azi.year, data_azi.month)[1]
    buget_zi = buget_luna / zile_in_luna
    st.info(f"Buget teoretic: {buget_zi:.2f} RON / zi")

# 2. LOGICA DE CALCUL (Simulăm o bază de date cu un fișier local pentru test)
if 'cheltuieli' not in st.session_state:
    st.session_state.cheltuieli = []

# Formular introducere cheltuială
with st.form("form_cheltuiala"):
    st.subheader("Introdu cheltuială nouă")
    suma = st.number_input("Suma (RON):", min_value=0.0, step=1.0)
    descriere = st.text_input("Descriere (ex: Supermarket, Benzina):")
    buton_save = st.form_submit_button("Salvează")

    if buton_save and suma > 0:
        st.session_state.cheltuieli.append({'data': data_azi.strftime("%d-%m-%Y"), 'suma': suma})
        st.success("Salvat!")

# 3. CALCULUL BUGETULUI DINAMIC
zi_curenta = data_azi.day
total_cheltuit = sum(item['suma'] for item in st.session_state.cheltuieli)

# Logica cerută de tine:
# Bugetul pe care ar fi trebuit să îl ai până azi inclusiv
buget_total_pana_azi = buget_zi * zi_curenta
# Soldul rămas (include reportările din zilele trecute)
sold_disponibil_azi = buget_total_pana_azi - total_cheltuit

# 4. AFIȘARE REZULTATE
col1, col2 = st.columns(2)
with col1:
    st.metric("Sold Disponibil AZI", f"{sold_disponibil_azi:.2f} RON")
with col2:
    st.metric("Total Cheltuit Lună", f"{total_cheltuit:.2f} RON")

if sold_disponibil_azi < 0:
    st.error(f"Atenție! Ai depășit bugetul cu {abs(sold_disponibil_azi):.2f} RON. Această sumă va fi retrasă din zilele următoare.")
else:
    st.success(f"Ești în grafic! Poți cheltui {sold_disponibil_azi:.2f} RON până diseară.")

# Afișare istoric scurt
if st.session_state.cheltuieli:
    st.subheader("Istoric azi")
    df = pd.DataFrame(st.session_state.cheltuieli)
    st.table(df)
