import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import streamlit as st
import pandas as pd
from src.translation.manager import get_translations

# Importazione dei moduli di nesting separati
from src.nesting.nesting_1d import render_nesting_1d
from src.nesting.nesting_2d import render_nesting_2d

# Configurazione di pagina iniziale
st.set_page_config(page_title="MetalHub Suite V2", layout="wide")

if "lingua" not in st.session_state:
    st.session_state.lingua = "Italiano"

t = get_translations(st.session_state.lingua)

# Inizializzazione Tabelle di Stato (Magazzino e Richieste)
if "magazzino_1d" not in st.session_state:
    st.session_state.magazzino_1d = pd.DataFrame([
        {"CODICE": "HEA100", "LUNGHEZZA": 6000.0, "QTY": 12},
        {"CODICE": "TUB_40X40", "LUNGHEZZA": 6000.0, "QTY": 25}
    ])

if "richieste_1d" not in st.session_state:
    st.session_state.richieste_1d = pd.DataFrame([
        {"CODICE": "HEA100", "LUNGHEZZA": 1500.0, "QTY": 4},
        {"CODICE": "HEA100", "LUNGHEZZA": 2200.0, "QTY": 3},
        {"CODICE": "TUB_40X40", "LUNGHEZZA": 850.0, "QTY": 14}
    ])

if "magazzino_2d" not in st.session_state:
    st.session_state.magazzino_2d = pd.DataFrame([
        {"CODICE": "L_FE_6MM", "LARGHEZZA": 3000.0, "ALTEZZA": 1500.0, "QTY": 5}
    ])

if "richieste_2d" not in st.session_state:
    st.session_state.richieste_2d = pd.DataFrame([
        {"CODICE": "L_FE_6MM", "LARGHEZZA": 400.0, "ALTEZZA": 300.0, "QTY": 15}
    ])

if "risultati_calcolo_1d" not in st.session_state:
    st.session_state.risultati_calcolo_1d = None

if "risultati_calcolo_2d" not in st.session_state:
    st.session_state.risultati_calcolo_2d = None

# Forzatura dati numerici per evitare crash imprevisti
for k in ["magazzino_1d", "richieste_1d", "magazzino_2d", "richieste_2d"]:
    for col in ["LUNGHEZZA", "LARGHEZZA", "ALTEZZA", "QTY"]:
        if col in st.session_state[k].columns:
            st.session_state[k][col] = pd.to_numeric(st.session_state[k][col], errors='coerce').fillna(0)

# Sidebar globale per la lingua
with st.sidebar:
    st.header("🌍 Settings")
    lingua_scelta = st.selectbox("Language", ["Italiano", "English"], index=0 if st.session_state.lingua == "Italiano" else 1)
    if lingua_scelta != st.session_state.lingua:
        st.session_state.lingua = lingua_scelta
        st.rerun()

# Titoli dell'applicazione
st.markdown(f"<h1 style='color:#FF5722;'>{t['titolo']}</h1>", unsafe_allow_html=True)
st.caption(t["sottotitolo"])

# Generazione dei Tab principali
tab_1d, tab_2d = st.tabs([t["tab_1d"], t["tab_2d"]])
config_colonne = {"CODICE": t["col_codice"], "LUNGHEZZA": t["col_lunghezza"], "LARGHEZZA": t["col_larghezza"], "ALTEZZA": t["col_altezza"], "QTY": t["col_qty"]}

# Chiamata ai moduli esterni delegati
with tab_1d:
    render_nesting_1d(t, config_colonne)

with tab_2d:
    render_nesting_2d(t, config_colonne)
