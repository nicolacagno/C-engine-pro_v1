import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
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
# TAB 2D - ORA CON ANTEPRIMA GRAFICA MATPLOTLIB
# =============================================================================
with tab_2d:
    col_l2, col_r2 = st.columns([1, 1])
    with col_l2:
        st.subheader(t["magazzino_titolo"])
        st.session_state.magazzino_2d = st.data_editor(st.session_state.magazzino_2d, num_rows="dynamic", column_config=config_colonne, key="edit_mag_2d")
        
        st.subheader(t["dxf_titolo"])
        file_dxf = st.file_uploader("Upload .dxf", type=["dxf"], key="uploader_dxf_2d")
        
        w_pezzo, h_pezzo = 200.0, 200.0
        if file_dxf:
            raw_entities = load_dxf(file_dxf.getvalue())
            if raw_entities:
                geometry = process_dxf_part(raw_entities)
                if geometry and not geometry.is_empty:
                    # Calcolo ingombro massimo
                    minx, miny, maxx, maxy = geometry.bounds
                    w_pezzo = round(maxx - minx, 1)
                    h_pezzo = round(maxy - miny, 1)
                    st.success(f"{t['msg_success_dxf']} {w_pezzo} x {h_pezzo} mm")
                    
                    # ---------------------------------------------------------
                    # SEZIONE GENERAZIONE GRAFICO ANTEPRIMA
                    # ---------------------------------------------------------
                    st.write("### 👁️ Preview:")
                    fig, ax = plt.subplots(figsize=(6, 4))
                    
                    # Funzione interna ricorsiva per gestire Polygon o MultiPolygon
                    def renderizza_sagoma(geom):
                        if isinstance(geom, Polygon):
                            # 1. Disegna e colora il profilo esterno (colore arancione MetalHub)
                            x, y = geom.exterior.xy
                            ax.plot(x, y, color="#FF5722", linewidth=2, label="Profilo")
                            ax.fill(x, y, color="#FF5722", alpha=0.15)
                            
                            # 2. Disegna ed evidenzia i fori interni (in azzurro tratteggiato)
                            for interior in geom.interiors:
                                xi, yi = interior.xy
                                ax.plot(xi, yi, color="#00BCD4", linewidth=1.2, linestyle="--")
                                ax.fill(xi, yi, color="white") # Simula lo svuotamento del foro
                        elif hasattr(geom, "geoms"):
                            for sub_geom in geom.geoms:
                                renderizza_sagoma(sub_geom)

                    renderizza_sagoma(geometry)
                    
                    # Forzatura del rapporto 1:1 per evitare deformazioni visive
                    ax.set_aspect('equal', adjustable='box')
                    ax.grid(True, linestyle=':', alpha=0.5)
                    ax.set_xlabel("X (mm)", fontsize=8)
                    ax.set_ylabel("Y (mm)", fontsize=8)
                    
                    # Invio del grafico a Streamlit
                    st.pyplot(fig)
                    plt.close(fig) # Liberazione della memoria
                    # ---------------------------------------------------------
                    
                    qty_dxf = st.number_input(f"{t['col_qty']} DXF", min_value=1, value=5)
                else:
                    st.warning(t["msg_error_dxf"])
            else:
                st.error(t["msg_critico_dxf"])

    with col_r2:
        st.subheader(t["richieste_titolo"])
        st.session_state.richieste_2d = st.data_editor(st.session_state.richieste_2d, num_rows="dynamic", column_config=config_colonne, key="edit_rich_2d")
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        if st.button(t["btn_elabora"], key="btn_run_2d"):
            st.info(t["simulazione"])
            st.write("Esecuzione del piazzamento geometrico...")
