import os
import sys
# Sblocca il tracciamento dei moduli su sistemi operativi Linux (Streamlit Cloud)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from src.nesting.nesting_2d import render_nesting_2d

# 💡 ATTENZIONE: Rimuovi il commento (#) sotto solo se hai creato i relativi file!
# from src.nesting.nesting_1d import render_nesting_1d
# from src.translation.manager import render_translation

# Configurazione globale della pagina
st.set_page_config(page_title="C-Engine Pro v1", layout="wide", page_icon="🏗️")

st.title("🏗️ C-Engine Pro - Pannello Ingegnerizzazione")
st.write("Sistema integrato per l'ottimizzazione dei piani di taglio e nesting dei materiali.")

# Creazione dei Tab di navigazione principale
tab1, tab2, tab3 = st.tabs(["📊 Nesting 1D (Lineare)", "📐 Nesting 2D (Lamiere)", "🌐 Lingue & Traduzioni"])

with tab1:
    # Qui viene richiamato il modulo del Nesting 1D (Profili/Barre)
    # Se hai spostato il vecchio codice 1D nel file src/nesting/nesting_1d.py, sblocca questa riga:
    # render_nesting_1d()
    st.info("Modulo Nesting 1D Lineare attivo tramite file separato.")

with tab2:
    # Questo è il modulo 2D completo che include il tasto PDF con grafico
    render_nesting_2d()

with tab3:
    # Se hai un modulo per gestire il dizionario delle lingue, sblocca questa riga:
    # render_translation()
    st.info("Pannello di gestione traduzioni e dizionari di sistema.")
