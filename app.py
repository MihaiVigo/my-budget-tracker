import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import calendar

# --- CONFIGURARE PAGINĂ ---
st.set_page_config(page_title="Buget Tracker Cloud", layout="centered")

# --- 1. SISTEM DE AUTENTIFICARE ---
def verifica_parola():
    if "autentificat" not in st.session_state:
        st.session_state["autentificat"] = False

    if not st.session_state["autentificat"]:
        st.title("🔒 Acces Restrâns")
        parola = st.text_input("Introdu parola:", type="password")
        if st.button("Logare"):
            if parola == "secret123":  # SCHIMBĂ ACEASTĂ PAROLĂ ÎNAINTE DE DEPLOY
                st.session_state["autentificat"] = True
                st.rerun()
            else:
                st.error("Parolă incorectă!")
        return False
    return True

if verifica_parola():
    # --- 2. CONECTARE GOOGLE SHEETS ---
    # Înlocuiește cu URL-ul tău real
    url_sheet = "https://docs.google.com/spreadsheets/d/ID_UL_TAU_AICI/edit#gid=0"
    
    conn = st.connection("gsheets", type=GSheetsConnection)

    def incarca_date(nume_sheet):
        # ttl=0 forțează aplicația să ignore memoria cache și să ia datele REALE din Sheets
        return conn.read(spreadsheet=url_sheet, worksheet=nume_sheet, ttl=0)

    # Încărcăm datele proaspete
    try:
        df_cheltuieli = incarca_date("Sheet1")
        df_cheltuieli['data'] = pd.to_datetime(df_cheltuieli['data'], errors='coerce')
        
        df_setari = incarca_date("Setari")
        
        # Extragem venitul din tab-ul Setari
        if not df_setari.empty and 'venit_luna' in df_setari.columns:
            venit_actual = int(df_setari.iloc[0]['venit_luna'])
        else:
            venit_actual = 3100 # Sumă de rezervă dacă sheet-ul e gol
    except Exception as e:
        st.error(f"⚠️ Eroare la citirea datelor: {e}")
        df_cheltuieli = pd.DataFrame(columns=['data', 'suma', 'descriere'])
        venit_actual = 3100

    # --- INTERFAȚĂ PRINCIPALĂ ---
    st.title("💰 Tracker Buget Cloud")

    # 3. SETARE VENIT LUNAR (Salvare în Sheets)
    with st.expander("⚙️ Setări Venit Lunar", expanded=False):
        nou_venit = st.number_input("Suma totală (RON):", value=venit_actual, step=100)
        if st.button("Salvează Noul Venit"):
            df_setari_nou = pd.DataFrame({'venit_luna': [nou_venit]})
            conn.update(spreadsheet=url_sheet, worksheet="Setari", data=df_setari_nou)
            st.success(f"Venitul a fost actualizat la {nou_venit} RON!")
            st.rerun()

    data_now = datetime.now()
    zile_luna = calendar.monthrange(data_now.year, data_now.month)[1]
    buget_fix_zi = int(venit_actual / zile_luna)
    
    st.info(f"Buget bazat pe un venit de **{venit_actual} RON**: Zilnic poți cheltui **{buget_fix_zi} RON**.")

    # --- 4. FORMULAR ADAUGARE CHELTUIELI ---
    with st.form("add_form", clear_on_submit=True):
        col_s, col_d = st.columns([1, 2])
        with col_s:
            suma = st.number_input("Suma cheltuită:", min_value=0, step=1)
        with col_d:
            desc = st.text_input("Descriere (unde s-au dus banii?):")
        data_input = st.date_input("Data:", data_now)
        submit = st.form_submit_button("Înregistrează Cheltuiala")

        if submit and suma > 0:
            noua_intrare = pd.DataFrame({
                'data': [data_input.strftime('%Y-%m-%d')],
                'suma': [int(suma)],
                'descriere': [desc]
            })
            # Actualizăm Google Sheets
            updated_df = pd.concat([df_cheltuieli, noua_intrare], ignore_index=True)
            conn.update(spreadsheet=url_sheet, worksheet="Sheet1", data=updated_df)
            st.success("Cheltuială adăugată cu succes!")
            st.rerun()

    # --- 5. LOGICA DE CALCUL ---
    ziua_curenta_nr = data_now.day
    sold_reportat = 0

    # Calculăm soldul adunat din prima zi a lunii până ieri
    for zi in range(1, ziua_curenta_nr):
        data_zi = datetime(data_now.year, data_now.month, zi).date()
        if not df_cheltuieli.empty:
            # Filtrare sigură după dată
            mask = df_cheltuieli['data'].dt.date == data_zi
            cheltuieli_zi = int(df_cheltuieli[mask]['suma'].sum())
        else:
            cheltuieli_zi = 0
        sold_reportat = (sold_reportat + buget_fix_zi) - cheltuieli_zi

    # Calculăm cheltuielile de azi
    cheltuieli_azi = 0
    if not df_cheltuieli.empty:
        cheltuieli_azi = int(df_cheltuieli[df_cheltuieli['data'].dt.date == data_now.date()]['suma'].sum())

    sold_disponibil_azi = int((buget_fix_zi + sold_reportat) - cheltuieli_azi)

    # --- 6. AFIȘARE REZULTATE ---
    st.divider()
    if sold_disponibil_azi >= 0:
        st.success(f"### SOLD DISPONIBIL AZI: {sold_disponibil_azi} RON")
    else:
        st.error(f"### SOLD DISPONIBIL AZI: {sold_disponibil_azi} RON")

    col1, col2 = st.columns(2)
    col1.metric("Economii/Reportat", f"{sold_reportat} RON")
    col2.metric("Cheltuit azi", f"{cheltuieli_azi} RON")

    # --- 7. ISTORIC ---
    if not df_cheltuieli.empty:
        st.divider()
        st.subheader("📜 Istoric Tranzacții (Google Sheets)")
        df_vis = df_cheltuieli.copy()
        # Sortăm după dată descrescător pentru a vedea ultimele cheltuieli primele
        df_vis = df_vis.sort_values(by='data', ascending=False)
        df_vis['data'] = df_vis['data'].dt.strftime('%d-%m-%Y')
        st.dataframe(df_vis, use_container_width=True)
