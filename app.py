import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from shapely.geometry import Polygon

# Importazioni stabili dai moduli interni
from src.dxf.importer import load_dxf
from src.dxf.converter import process_dxf_part
from src.translation.manager import get_translations

# =============================================================================
# CONFIGURAZIONE STRUTTURA PAGINA & STATO DELLA SESSIONE
# =============================================================================
st.set_page_config(page_title="MetalHub Suite V2", layout="wide")

if "lingua" not in st.session_state:
    st.session_state.lingua = "Italiano"

# Recupero traduzioni
t = get_translations(st.session_state.lingua)

# Inizializzazione dati tabelle con ID stabili
if "magazzino_1d" not in st.session_state:
    st.session_state.magazzino_1d = pd.DataFrame([
        {"CODICE": "HEA100", "LUNGHEZZA": 6000, "QTY": 12},
        {"CODICE": "TUB_40X40", "LUNGHEZZA": 6000, "QTY": 25}
    ])

if "richieste_1d" not in st.session_state:
    st.session_state.richieste_1d = pd.DataFrame([
        {"CODICE": "HEA100", "LUNGHEZZA": 1500, "QTY": 4},
        {"CODICE": "TUB_40X40", "LUNGHEZZA": 850, "QTY": 10}
    ])

if "magazzino_2d" not in st.session_state:
    st.session_state.magazzino_2d = pd.DataFrame([
        {"CODICE": "L_FE_6MM", "LARGHEZZA": 3000, "ALTEZZA": 1500, "QTY": 5},
        {"CODICE": "INOX_3MM", "LARGHEZZA": 2500, "ALTEZZA": 1250, "QTY": 3}
    ])

if "richieste_2d" not in st.session_state:
    st.session_state.richieste_2d = pd.DataFrame([
        {"CODICE": "L_FE_6MM", "LARGHEZZA": 400, "ALTEZZA": 300, "QTY": 15}
    ])

# =============================================================================
# SIDEBAR - SELEZIONE LINGUA (10 NAZIONALITÀ)
# =============================================================================
with st.sidebar:
    st.header("🌍 Settings")
    
    lista_lingue = [
        "Italiano", "English", "Deutsch", "Français", "Español", 
        "Polski", "Ελληνικά", "Português", "Čeština", "Magyar"
    ]
    
    idx_corrente = lista_lingue.index(st.session_state.lingua) if st.session_state.lingua in lista_lingue else 0

    lingua_scelta = st.selectbox(
        "Select Language / Scegli Lingua", 
        lista_lingue, 
        index=idx_corrente
    )
    
    if lingua_scelta != st.session_state.lingua:
        st.session_state.lingua = lingua_scelta
        st.rerun()

# =============================================================================
# INTERFACCIA PRINCIPALE
# =============================================================================
st.markdown(f"<h1 style='color:#FF5722;'>{t['titolo']}</h1>", unsafe_allow_html=True)
st.caption(t["sottotitolo"])

tab_1d, tab_2d = st.tabs([t["tab_1d"], t["tab_2d"]])

# Mappatura etichette colonne visive
config_colonne = {
    "CODICE": t["col_codice"],
    "LUNGHEZZA": t["col_lunghezza"],
    "LARGHEZZA": t["col_larghezza"],
    "ALTEZZA": t["col_altezza"],
    "QTY": t["col_qty"]
}

# =============================================================================
# TAB 1D
# =============================================================================
with tab_1d:
    col_l1, col_r1 = st.columns(2)
    with col_l1:
        st.subheader(t["magazzino_titolo"])
        st.session_state.magazzino_1d = st.data_editor(st.session_state.magazzino_1d, num_rows="dynamic", column_config=config_colonne, key="edit_mag_1d")
    with col_r1:
        st.subheader(t["richieste_titolo"])
        st.session_state.richieste_1d = st.data_editor(st.session_state.richieste_1d, num_rows="dynamic", column_config=config_colonne, key="edit_rich_1d")
        
    st.markdown("---")
    if st.button(t["btn_elabora"], key="btn_run_1d"):
        st.info(t["simulazione"])
        st.success("Ottimizzazione 1D completata.")

# =============================================================================
# TAB 2D - GESTIONE MULTI-FILE & QUANTITÀ INDIPENDENTI
# =============================================================================
with tab_2d:
    col_l2, col_r2 = st.columns([1, 1])
    with col_l2:
        st.subheader(t["magazzino_titolo"])
        st.session_state.magazzino_2d = st.data_editor(st.session_state.magazzino_2d, num_rows="dynamic", column_config=config_colonne, key="edit_mag_2d")
        
        st.markdown("---")
        st.subheader(t["dxf_titolo"])
        
        # AGGIORNATO: accept_multiple_files=True permette il caricamento in blocco
        files_dxf = st.file_uploader("Upload .dxf (Multipli)", type=["dxf"], accept_multiple_files=True, key="uploader_dxf_2d")
        
        # Dizionario di riepilogo per passare i dati al motore di nesting 2D
        parti_dxf_caricate = {}
        
        if files_dxf:
            st.write(f"### 📦 Pezzi Rilevati ({len(files_dxf)} file):")
            
            # Ciclo di lettura per ogni singolo file caricato
            for f_dxf in files_dxf:
                # Creiamo un box visivo pulito per ogni pezzo
                with st.container(border=True):
                    st.markdown(f"**📄 File: {f_dxf.name}**")
                    
                    raw_entities = load_dxf(f_dxf.getvalue())
                    if raw_entities:
                        geometry = process_dxf_part(raw_entities)
                        if geometry and not geometry.is_empty:
                            # Calcolo dimensioni ingombro pezzo
                            minx, miny, maxx, maxy = geometry.bounds
                            w_pezzo = round(maxx - minx, 1)
                            h_pezzo = round(maxy - miny, 1)
                            
                            st.success(f"✔️ Dimensioni rilevate: {w_pezzo} x {h_pezzo} mm")
                            
                            # Input della quantità specifico per QUESTO file (chiave unica generata col nome del file)
                            qty_specifica = st.number_input(
                                f"Quantità da produrre per {f_dxf.name}:", 
                                min_value=1, 
                                value=1, 
                                step=1, 
                                key=f"qty_{f_dxf.name}"
                            )
                            
                            # Mostra il grafico dell'anteprima 1:1
                            fig, ax = plt.subplots(figsize=(4, 2.5))
                            
                            def renderizza_sagoma(geom):
                                if isinstance(geom, Polygon):
                                    x, y = geom.exterior.xy
                                    ax.plot(x, y, color="#FF5722", linewidth=2)
                                    ax.fill(x, y, color="#FF5722", alpha=0.15)
                                    for interior in geom.interiors:
                                        xi, yi = interior.xy
                                        ax.plot(xi, yi, color="#00BCD4", linewidth=1.2, linestyle="--")
                                        ax.fill(xi, yi, color="white")
                                elif hasattr(geom, "geoms"):
                                    for sub_geom in geom.geoms:
                                        renderizza_sagoma(sub_geom)

                            renderizza_sagoma(geometry)
                            ax.set_aspect('equal', adjustable='box')
                            ax.grid(True, linestyle=':', alpha=0.4)
                            
                            st.pyplot(fig)
                            plt.close(fig)
                            
                            # Salva i dati pronti per l'algoritmo di ottimizzazione
                            parti_dxf_caricate[f_dxf.name] = {
                                "geometry": geometry,
                                "width": w_pezzo,
                                "height": h_pezzo,
                                "qty": qty_specifica
                            }
                        else:
                            st.warning(t["msg_error_dxf"])
                    else:
                        # Se il file specifico fallisce (come il file 1977.002.201.DXF), l'errore rimane isolato qui dentro!
                        st.error(f"❌ {t['msg_critico_dxf']} Controlla che il file non contenga Spline non convertite o che sia salvato in formato DXF AutoCAD R12/LT2.")

    with col_r2:
        st.subheader(t["richieste_titolo"])
        st.session_state.richieste_2d = st.data_editor(st.session_state.richieste_2d, num_rows="dynamic", column_config=config_colonne, key="edit_rich_2d")
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        if st.button(t["btn_elabora"], key="btn_run_2d"):
            st.info(t["simulazione"])
            
            # Log di verifica nel terminale/interfaccia per vedere che le quantità siano corrette
            if parti_dxf_caricate:
                st.write("📊 **Riepilogo pezzi DXF inviati al Nesting:**")
                for nome, dati in parti_dxf_caricate.items():
                    st.write(f"- Pezzo `{nome}`: dimensioni {dati['width']}x{dati['height']} mm → **Quantità: {dati['qty']}**")
            
            st.write("Esecuzione del piazzamento geometrico...")
