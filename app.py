import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import calendar

# --- CONFIGURARE PAGINĂ ---
st.set_page_config(page_title="Buget Tracker Privat", layout="centered")

# --- 1. SISTEM DE AUTENTIFICARE ---
def verifica_parola():
    if "autentificat" not in st.session_state:
        st.session_state["autentificat"] = False

    if not st.session_state["autentificat"]:
        st.title("🔒 Acces Restrâns")
        parola = st.text_input("Introdu parola:", type="password")
        if st.button("Logare"):
            if parola == "<vta2947>":  # SCHIMBĂ ACEASTĂ PAROLĂ
                st.session_state["autentificat"] = True
                st.rerun()
            else:
                st.error("Parolă incorectă!")
        return False
    return True

if verifica_parola():
    # --- 2. CONECTARE GOOGLE SHEETS ---
    # URL-ul foii tale (înlocuiește cu link-ul tău real)
    url_sheet = "https://docs.google.com/spreadsheets/d/180T57Mv1ba4Qt4X8XVjG6SwN7gg3tRcbHpEo6YPad2w/edit?usp=sharing"
    
    conn = st.connection("gsheets", type=GSheetsConnection)

    def incarca_date():
        try:
            return conn.read(spreadsheet=url_sheet, usecols=[0,1,2])
        except:
            return pd.DataFrame(columns=['data', 'suma', 'descriere'])

    df_cheltuieli = incarca_date()
    # Forțăm conversia datei
    df_cheltuieli['data'] = pd.to_datetime(df_cheltuieli['data'], errors='coerce')

    # --- INTERFAȚĂ ---
    st.title("💰 Tracker Buget (Google Sheets)")

    # Setări venit (le păstrăm în session_state sau poți face altă foaie)
    venit_luna = st.sidebar.number_input("Venit lunar (RON):", value=3100)
    data_now = datetime.now()
    zile_luna = calendar.monthrange(data_now.year, data_now.month)[1]
    buget_fix_zi = int(venit_luna / zile_luna)

    # --- 3. FORMULAR ADAUGARE ---
    with st.form("add_form", clear_on_submit=True):
        col_s, col_d = st.columns([1, 2])
        with col_s:
            suma = st.number_input("Suma:", min_value=0, step=1)
        with col_d:
            desc = st.text_input("Descriere:")
        data_input = st.date_input("Data:", data_now)
        submit = st.form_submit_button("Adaugă în Google Sheets")

        if submit and suma > 0:
            noua_intrare = pd.DataFrame({
                'data': [data_input.strftime('%Y-%m-%d')],
                'suma': [int(suma)],
                'descriere': [desc]
            })
            # Concatenăm și salvăm înapoi în Cloud
            updated_df = pd.concat([df_cheltuieli, noua_intrare], ignore_index=True)
            conn.update(spreadsheet=url_sheet, data=updated_df)
            st.success("Date salvate în Google Sheets!")
            st.rerun()

    # --- 4. LOGICA DE CALCUL ---
    ziua_curenta_nr = data_now.day
    sold_reportat = 0

    for zi in range(1, ziua_curenta_nr):
        data_zi = datetime(data_now.year, data_now.month, zi).date()
        if not df_cheltuieli.empty:
            cheltuieli_zi = int(df_cheltuieli[df_cheltuieli['data'].dt.date == data_zi]['suma'].sum())
        else:
            cheltuieli_zi = 0
        sold_reportat = (sold_reportat + buget_fix_zi) - cheltuieli_zi

    cheltuieli_azi = 0
    if not df_cheltuieli.empty:
        cheltuieli_azi = int(df_cheltuieli[df_cheltuieli['data'].dt.date == data_now.date()]['suma'].sum())

    sold_disponibil_azi = int((buget_fix_zi + sold_reportat) - cheltuieli_azi)

    # AFIȘARE REZULTATE
    st.divider()
    if sold_disponibil_azi >= 0:
        st.success(f"### SOLD DISPONIBIL AZI: {sold_disponibil_azi} RON")
    else:
        st.error(f"### SOLD DISPONIBIL AZI: {sold_disponibil_azi} RON")

    col1, col2 = st.columns(2)
    col1.metric("Din zile trecute", f"{sold_reportat} RON")
    col2.metric("Cheltuit azi", f"{cheltuieli_azi} RON")

    # ISTORIC
    if not df_cheltuieli.empty:
        st.divider()
        st.subheader("📜 Istoric din Cloud")
        df_vis = df_cheltuieli.copy()
        df_vis['data'] = df_vis['data'].dt.strftime('%d-%m-%Y')
        st.dataframe(df_vis.sort_index(ascending=False), use_container_width=True)
