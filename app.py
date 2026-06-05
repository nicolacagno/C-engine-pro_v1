import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
# Importiamo i nostri moduli dedicati
from src.dxf.importer import load_dxf
from src.dxf.converter import process_dxf_part

# =============================================================================
# STATO DELLA SESSIONE
# =============================================================================
if "magazzino_1d" not in st.session_state:
    st.session_state.magazzino_1d = pd.DataFrame([
        {"CODICE MATERIALE": "FE360", "LUNGHEZZA (mm)": 6000, "QTY": 10}
    ])
if "magazzino_2d" not in st.session_state:
    st.session_state.magazzino_2d = pd.DataFrame([
        {"CODICE MATERIALE": "L_FE_6MM", "LARGHEZZA X (mm)": 3000, "ALTEZZA Y (mm)": 1500, "QTY": 5}
    ])

# =============================================================================
# CONFIGURAZIONE INTERFACCIA
# =============================================================================
st.set_page_config(page_title="MetalHub Suite V2", layout="wide")

st.markdown("<h1 style='color:#FF5722;'>🔥 MetalHub Suite V2</h1>", unsafe_keyword=True)
tab_1d, tab_2d = st.tabs(["🪚 NESTING 1D", "📐 NESTING 2D"])

# =============================================================================
# TAB 2D - PIPELINE MODULARE
# =============================================================================
with tab_2d:
    col_l, col_r = st.columns([1, 2])
    
    with col_l:
        st.subheader("🛠️ Caricamento DXF Reale")
        file_dxf = st.file_uploader("Trascina il file .dxf", type=["dxf"])
        
        w_rilevata, h_rilevata = 500.0, 300.0
        
        if file_dxf:
            # 1. Utilizziamo il modulo importer
            raw_entities = load_dxf(file_dxf.getvalue())
            
            # 2. Utilizziamo il modulo converter (process_dxf_part)
            if raw_entities:
                geometry = process_dxf_part(raw_entities)
                if geometry and not geometry.is_empty:
                    minx, miny, maxx, maxy = geometry.bounds
                    w_rilevata = round(maxx - minx, 1)
                    h_rilevata = round(maxy - miny, 1)
                    st.success(f"✔️ Geometria Normalizzata: {w_rilevata}x{h_rilevata} mm")
                else:
                    st.warning("⚠️ DXF letto, ma nessuna geometria geometrica trovata.")
            else:
                st.error("⚠️ Errore critico nel parsing: il file potrebbe essere corrotto o vuoto.")

        st.subheader("📦 Magazzino Lamiere")
        # Protezione KeyError inserita
        if not st.session_state.magazzino_2d.empty and "CODICE MATERIALE" in st.session_state.magazzino_2d.columns:
            st.session_state.magazzino_2d = st.data_editor(st.session_state.magazzino_2d, num_rows="dynamic")
        else:
            st.error("Errore: Tabella magazzino non formattata correttamente.")

    with col_r:
        st.subheader("🚀 Simulazione Nesting")
        if st.button("Elabora e Visualizza"):
            st.info(f"Simulazione in corso per pezzo base: {w_rilevata}x{h_rilevata} mm...")
            # Qui si integrerà il modulo 'nesting/engine.py'
            st.write("Motore di nesting pronto per la logica di piazzamento.")

# =============================================================================
# TAB 1D
# =============================================================================
with tab_1d:
    st.subheader("Gestione Barre")
    st.session_state.magazzino_1d = st.data_editor(st.session_state.magazzino_1d, num_rows="dynamic")
    if st.button("Elabora 1D"):
        st.write("Esecuzione logica di taglio 1D...")