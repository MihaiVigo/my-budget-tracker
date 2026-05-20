import streamlit as st
import pandas as pd
import requests
from datetime import datetime, date
import calendar

# --- CONFIGURARE API ---
BASE_API_URL = "https://sheetdb.io/api/v1/zjfuwwvgqximb"

st.set_page_config(page_title="Buget Pro - Resetabil", layout="wide")

# --- FUNCȚII COMUNICARE ---
def incarca_date(nume_tab):
    url = f"{BASE_API_URL}?sheet={nume_tab}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            date_json = response.json()
            if date_json:  # Verificăm dacă JSON-ul nu este gol
                return pd.DataFrame(date_json)
    except:
        pass
    return pd.DataFrame(columns=['data', 'suma', 'descriere'])

def trimite_date(nume_tab, data, suma, desc):
    url = f"{BASE_API_URL}?sheet={nume_tab}"
    payload = {"data": [{"data": data, "suma": int(suma), "descriere": desc}]}
    try:
        res = requests.post(url, json=payload, timeout=10)
        return res.status_code == 201
    except:
        return False

def curata_tot_tabelul(nume_tab):
    """Șterge toate datele dintr-un tab folosind un query de tip 'mai mare de -1'"""
    url = f"{BASE_API_URL}/suma/>/-1?sheet={nume_tab}"
    try:
        res = requests.delete(url, timeout=10)
        return res.status_code == 200
    except:
        return False

# --- CONFIGURARE TIMP (Inițializare timpurie și sigură) ---
# Setăm variabile implicite globale în caz că utilizatorul nu schimbă nimic în sidebar
data_selectata = date.today()
nr_zile_luna = calendar.monthrange(data_selectata.year, data_selectata.month)[1]

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Administrare")

    # 1. Configurare Timp
    with st.expander("📅 Configurare Timp", expanded=False):
        data_selectata = st.date_input("Data de azi:", date.today())
        ultimul_zi_luna = calendar.monthrange(data_selectata.year, data_selectata.month)[1]
        nr_zile_luna = st.number_input("Zile totale în lună:", min_value=1, value=ultimul_zi_luna)
    
    # 2. Adaugă Venit Nou
    with st.expander("💵 Adaugă Venit Nou", expanded=False):
        with st.form("venit_nou", clear_on_submit=True):
            v_suma = st.number_input("Sumă venit (RON):", min_value=0, step=100)
            v_desc = st.text_input("Sursă venit:")
            if st.form_submit_button("Salvează Venit"):
                if v_suma > 0:
                    trimite_date("venituri", data_selectata.strftime("%Y-%m-%d"), v_suma, v_desc)
                    st.rerun()

    # 3. Adaugă Cheltuială
    with st.expander("💸 Adaugă Cheltuială", expanded=True):
        with st.form("cheltuiala_noua", clear_on_submit=True):
            c_suma = st.number_input("Sumă (RON):", min_value=0, step=1)
            c_desc = st.text_input("Descriere:")
            if st.form_submit_button("Salvează Cheltuiala"):
                if c_suma > 0:
                    trimite_date("cheltuieli", data_selectata.strftime("%Y-%m-%d"), c_suma, c_desc)
                    st.rerun()

    st.divider()
    
    # 4. RESET TOTAL
    st.subheader("🚨 Resetare Date")
    if st.button("Șterge Toate VENITURILE"):
        if curata_tot_tabelul("venituri"):
            st.success("Tabelul de venituri a fost golit!")
            st.rerun()
            
    if st.button("Șterge Toate CHELTUIELILE"):
        if curata_tot_tabelul("cheltuieli"):
            st.success("Tabelul de cheltuieli a fost golit!")
            st.rerun()

# --- DESCĂRCARE ȘI FILTRARE DATE ---
df_v_raw = incarca_date("venituri")
df_c_raw = incarca_date("cheltuieli")

luna_tinta = data_selectata.month
an_tinta = data_selectata.year

def filtreaza_luna_curenta(df):
    # Dacă tabelul e complet gol sau nu are structura corectă, returnăm un df gol standardizat
    if df.empty or 'data' not in df.columns:
        return pd.DataFrame(columns=['data', 'suma', 'descriere'])
    
    # Ne asigurăm că eliminăm eventualele rânduri complet goale din Google Sheets
    df = df.dropna(subset=['data'])
    
    # Convertim coloana text în obiecte Datetime pentru a putea extrage luna/anul
    df['data_dt'] = pd.to_datetime(df['data'], errors='coerce')
    
    # Filtrare după luna și anul selectat
    masca = (df['data_dt'].dt.month == luna_tinta) & (df['data_dt'].dt.year == an_tinta)
    df_filtrat = df[masca].copy()
    
    # Ștergem coloana ajutătoare
    df_filtrat = df_filtrat.drop(columns=['data_dt'])
    return df_filtrat

# Aplicăm filtrarea
df_v = filtreaza_luna_curenta(df_v_raw)
df_c = filtreaza_luna_curenta(df_c_raw)

# --- CALCUL LOGIC (Cu conversie numerică obligatorie) ---
total_venituri_luna = int(pd.to_numeric(df_v['suma'], errors='coerce').sum()) if not df_v.empty else 0
total_cheltuieli_luna = int(pd.to_numeric(df_c['suma'], errors='coerce').sum()) if not df_c.empty else 0

ziua_nr = data_selectata.day
alocatie_zilnica = int(total_venituri_luna / nr_zile_luna) if total_venituri_luna > 0 else 0
buget_teoretic_pana_azi = alocatie_zilnica * ziua_nr
sold_disponibil_azi = buget_teoretic_pana_azi - total_cheltuieli_luna

# --- AFIȘARE REZULTATE ---
st.title("⚖️ Status Buget - Luna Curentă")

# Afișare buget principal
if sold_disponibil_azi >= 0:
    st.success(f"## Buget Disponibil Azi: {sold_disponibil_azi} RON")
else:
    st.error(f"## Buget Disponibil Azi: {sold_disponibil_azi} RON")

st.divider()

# Tabele de vizualizare pentru luna curentă
col1, col2 = st.columns(2)

with col1:
    st.subheader("📋 Venituri (Luna Curentă)")
    if not df_v.empty:
        st.dataframe(df_v[['data', 'descriere', 'suma']], use_container_width=True)
    else:
        st.caption("Niciun venit salvat în această lună.")

with col2:
    st.subheader("💸 Cheltuieli (Luna Curentă)")
    if not df_c.empty:
        st.dataframe(df_c[['data', 'descriere', 'suma']], use_container_width=True)
    else:
        st.caption("Nicio cheltuială salvată în această lună.")

st.divider()
st.caption(f"Venit lună: {total_venituri_luna} RON | Cheltuieli lună: {total_cheltuieli_luna} RON | Alocație fixă: {alocatie_zilnica} RON/zi")
