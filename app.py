import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import io
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

t = get_translations(st.session_state.lingua)

# Inizializzazione dati tabelle con ID stabili
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

# Helper per la conversione dei tipi
for k in ["magazzino_1d", "richieste_1d", "magazzino_2d", "richieste_2d"]:
    for col in ["LUNGHEZZA", "LARGHEZZA", "ALTEZZA", "QTY"]:
        if col in st.session_state[k].columns:
            st.session_state[k][col] = pd.to_numeric(st.session_state[k][col], errors='coerce').fillna(0)

# =============================================================================
# SIDEBAR - SELEZIONE LINGUA
# =============================================================================
with st.sidebar:
    st.header("🌍 Settings")
    lista_lingue = ["Italiano", "English", "Deutsch", "Français", "Español"]
    idx_corrente = lista_lingue.index(st.session_state.lingua) if st.session_state.lingua in lista_lingue else 0
    lingua_scelta = st.selectbox("Language", lista_lingue, index=idx_corrente)
    if lingua_scelta != st.session_state.lingua:
        st.session_state.lingua = lingua_scelta
        st.rerun()

st.markdown(f"<h1 style='color:#FF5722;'>{t['titolo']}</h1>", unsafe_allow_html=True)
st.caption(t["sottotitolo"])

tab_1d, tab_2d = st.tabs([t["tab_1d"], t["tab_2d"]])
config_colonne = {"CODICE": t["col_codice"], "LUNGHEZZA": t["col_lunghezza"], "LARGHEZZA": t["col_larghezza"], "ALTEZZA": t["col_altezza"], "QTY": t["col_qty"]}

# =============================================================================
# ALGORITMO DI NESTING 1D (GREEDY CUTTING STOCK)
# =============================================================================
def esegui_nesting_1d(df_mag, df_rich):
    richieste_esplose = []
    for _, r in df_rich.iterrows():
        for _ in range(int(r['QTY'])):
            richieste_esplose.append({"CODICE": r['CODICE'], "LUNGHEZZA": float(r['LUNGHEZZA'])})
    richieste_esplose.sort(key=lambda x: x['LUNGHEZZA'], reverse=True)
    
    barre_disponibili = []
    for _, r in df_mag.iterrows():
        for _ in range(int(r['QTY'])):
            barre_disponibili.append({"CODICE": r['CODICE'], "LUNGHEZZA_ORIGINALE": float(r['LUNGHEZZA']), "LUNGHEZZA_RESIDUA": float(r['LUNGHEZZA']), "TAGLI": []})
            
    piani_taglio = []
    for req in richieste_esplose:
        inserito = False
        for b_aperta in piani_taglio:
            if b_aperta["CODICE"] == req["CODICE"] and b_aperta["LUNGHEZZA_RESIDUA"] >= req["LUNGHEZZA"]:
                b_aperta["TAGLI"].append(req["LUNGHEZZA"])
                b_aperta["LUNGHEZZA_RESIDUA"] -= req["LUNGHEZZA"]
                inserito = True
                break
        if not inserito:
            for idx, b_disp in enumerate(barre_disponibili):
                if b_disp["CODICE"] == req["CODICE"] and b_disp["LUNGHEZZA_RESIDUA"] >= req["LUNGHEZZA"]:
                    nuova_barra = {
                        "ID_BARRA": len(piani_taglio) + 1,
                        "CODICE": b_disp["CODICE"],
                        "LUNGHEZZA_TOTALE": b_disp["LUNGHEZZA_ORIGINALE"],
                        "TAGLI": [req["LUNGHEZZA"]],
                        "LUNGHEZZA_RESIDUA": b_disp["LUNGHEZZA_ORIGINALE"] - req["LUNGHEZZA"]
                    }
                    piani_taglio.append(nuova_barra)
                    barre_disponibili.pop(idx)
                    inserito = True
                    break
    return piani_taglio

# =============================================================================
# TAB 1D - INTERFACCIA E RISULTATI
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
        risultati_1d = esegui_nesting_1d(st.session_state.magazzino_1d, st.session_state.richieste_1d)
        
        if risultati_1d:
            st.markdown("## 📊 Risultati Ottimizzazione 1D")
            
            # Creazione Tabella di Riepilogo per l'utente
            dati_tabella = []
            for b in risultati_1d:
                dati_tabella.append({
                    "ID Barra": b["ID_BARRA"],
                    "Codice Materiale": b["CODICE"],
                    "Lunghezza Totale (mm)": b["LUNGHEZZA_TOTALE"],
                    "Tagli Configurate (mm)": str(b["TAGLI"]),
                    "Sfrido Residuo (mm)": round(b["LUNGHEZZA_RESIDUA"], 1)
                })
            df_report = pd.DataFrame(dati_tabella)
            st.dataframe(df_report, use_container_width=True)
            
            # --- GENERAZIONE GRAFICO MATPLOTLIB ---
            fig, ax = plt.subplots(figsize=(10, max(2, len(risultati_1d) * 0.6)))
            for idx, b in enumerate(risultati_1d):
                y_pos = idx
                start_x = 0
                # Disegna i segmenti di taglio utili
                for t_len in b["TAGLI"]:
                    ax.add_patch(patches.Rectangle((start_x, y_pos - 0.25), t_len, 0.5, facecolor="#FF5722", edgecolor="white", lw=1))
                    ax.text(start_x + t_len/2, y_pos, f"{int(t_len)}", ha="center", va="center", color="white", fontsize=8, weight="bold")
                    start_x += t_len
                # Disegna lo sfrido rimanente
                if b["LUNGHEZZA_RESIDUA"] > 0:
                    ax.add_patch(patches.Rectangle((start_x, y_pos - 0.25), b["LUNGHEZZA_RESIDUA"], 0.5, facecolor="#B0BEC5", edgecolor="white", lw=1))
                    ax.text(start_x + b["LUNGHEZZA_RESIDUA"]/2, y_pos, f"Sfrido\n{int(b['LUNGHEZZA_RESIDUA'])}", ha="center", va="center", color="#37474F", fontsize=7)
            
            ax.set_yticks(range(len(risultati_1d)))
            ax.set_yticklabels([f"Barra {b['ID_BARRA']}\n({b['CODICE']})" for b in risultati_1d], fontsize=8)
            ax.set_xlabel("Lunghezza Barra (mm)", fontsize=9)
            ax.set_xlim(0, max(b["LUNGHEZZA_TOTALE"] for b in risultati_1d) + 200)
            ax.set_ylim(-0.5, len(risultati_1d) - 0.5)
            ax.invert_yaxis()
            ax.grid(axis='x', linestyle=':', alpha=0.5)
            st.pyplot(fig)
            
            # --- ESPORTAZIONI DATI (Tasti Download dedicati) ---
            st.markdown("### 💾 Esporta Documentazione Tecnica")
            exp_col1, exp_col2, exp_col3 = st.columns(3)
            
            with exp_col1:
                csv_data = df_report.to_csv(index=False).encode('utf-8')
                st.download_button(label="📥 Scarica Elenco Tagli (CSV)", data=csv_data, file_name="piano_taglio_metalhub.csv", mime="text/csv")
                
            with exp_col2:
                output_excel = io.BytesIO()
                with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
                    df_report.to_excel(writer, index=False, sheet_name="Piano Taglio")
                st.download_button(label="📈 Scarica Distinta Excel", data=output_excel.getvalue(), file_name="piano_taglio_metalhub.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                
            with exp_col3:
                # Esportazione PDF nativa unificando Dati + Grafico in un unico foglio stampabile
                output_pdf = io.BytesIO()
                fig_report, (ax_t, ax_g) = plt.subplots(2, 1, figsize=(8.5, 11), gridspec_kw={'height_ratios': [1, 2]})
                ax_t.axis('off')
                
                # Tabella testuale nel PDF
                testo_pdf = "METALHUB SUITE V2 - REPORT TECNICO DI TAGLIO\n\n"
                for _, row in df_report.iterrows():
                    testo_pdf += f"Barra {row['ID Barra']} [{row['Codice Materiale']}] | Lunghezza: {row['Lunghezza Totale (mm)']}mm | Tagli: {row['Tagli Configurate (mm)']} | Sfrido: {row['Sfrido Residuo (mm)']}mm\n"
                ax_t.text(0.01, 0.95, testo_pdf, transform=ax_t.transAxes, fontsize=9, fontfamily='monospace', va='top')
                
                # Replichiamo il grafico sotto il testo nel PDF
                for idx, b in enumerate(risultati_1d):
                    y_pos = idx
                    start_x = 0
                    for t_len in b["TAGLI"]:
                        ax_g.add_patch(patches.Rectangle((start_x, y_pos - 0.25), t_len, 0.5, facecolor="#FF5722", edgecolor="white"))
                        start_x += t_len
                    if b["LUNGHEZZA_RESIDUA"] > 0:
                        ax_g.add_patch(patches.Rectangle((start_x, y_pos - 0.25), b["LUNGHEZZA_RESIDUA"], 0.5, facecolor="#B0BEC5", edgecolor="white"))
                ax_g.set_yticks(range(len(risultati_1d)))
                ax_g.set_yticklabels([f"B. {b['ID_BARRA']} ({b['CODICE']})" for b in risultati_1d], fontsize=8)
                ax_g.set_xlim(0, max(b["LUNGHEZZA_TOTALE"] for b in risultati_1d) + 100)
                ax_g.set_ylim(-0.5, len(risultati_1d) - 0.5)
                ax_g.invert_yaxis()
                
                fig_report.savefig(output_pdf, format='pdf', bbox_inches='tight')
                plt.close(fig_report)
                st.download_button(label="📄 Scarica Report con Grafico (PDF)", data=output_pdf.getvalue(), file_name="report_taglio_metalhub.pdf", mime="application/pdf")
                
            plt.close(fig)
        else:
            st.warning("Nessun accoppiamento possibile. Verifica i codici materiale tra magazzino e richieste.")

# =============================================================================
# TAB 2D - GESTIONE MULTI-FILE
# =============================================================================
with tab_2d:
    col_l2, col_r2 = st.columns([1, 1])
    with col_l2:
        st.subheader(t["magazzino_titolo"])
        st.session_state.magazzino_2d = st.data_editor(st.session_state.magazzino_2d, num_rows="dynamic", column_config=config_colonne, key="edit_mag_2d")
        
        st.markdown("---")
        st.subheader(t["dxf_titolo"])
        files_dxf = st.file_uploader("Upload .dxf (Multipli)", type=["dxf"], accept_multiple_files=True, key="uploader_dxf_2d")
        
        parti_dxf_caricate = {}
        if files_dxf:
            st.write(f"### 📦 Pezzi Rilevati ({len(files_dxf)} file):")
            for f_dxf in files_dxf:
                with st.container(border=True):
                    st.markdown(f"**📄 File: {f_dxf.name}**")
                    raw_entities = load_dxf(f_dxf.getvalue())
                    if raw_entities:
                        geometry = process_dxf_part(raw_entities)
                        if geometry and not geometry.is_empty:
                            minx, miny, maxx, maxy = geometry.bounds
                            w_pezzo = round(maxx - minx, 1)
                            h_pezzo = round(maxy - miny, 1)
                            st.success(f"✔️ Dimensioni rilevate: {w_pezzo} x {h_pezzo} mm")
                            
                            qty_specifica = st.number_input(f"Quantità da produrre per {f_dxf.name}:", min_value=1, value=1, step=1, key=f"qty_{f_dxf.name}")
                            
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
                            
                            parti_dxf_caricate[f_dxf.name] = {"geometry": geometry, "width": w_pezzo, "height": h_pezzo, "qty": qty_specifica}
                        else:
                            st.warning(t["msg_error_dxf"])
                    else:
                        st.error(f"❌ {t['msg_critico_dxf']}")

    with col_r2:
        st.subheader(t["richieste_titolo"])
        st.session_state.richieste_2d = st.data_editor(st.session_state.richieste_2d, num_rows="dynamic", column_config=config_colonne, key="edit_rich_2d")
