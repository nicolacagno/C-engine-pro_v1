import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import io
import math
from shapely.geometry import Polygon

# Importazioni dei moduli locali separati
from src.dxf.importer import load_dxf
from src.dxf.converter import process_dxf_part
from src.translation.manager import get_translations

# Configurazione di pagina
st.set_page_config(page_title="MetalHub Suite V2", layout="wide")

if "lingua" not in st.session_state:
    st.session_state.lingua = "Italiano"

t = get_translations(st.session_state.lingua)

# Inizializzazione Tabelle di Stato
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

# Correzione formati dati numerici
for k in ["magazzino_1d", "richieste_1d", "magazzino_2d", "richieste_2d"]:
    for col in ["LUNGHEZZA", "LARGHEZZA", "ALTEZZA", "QTY"]:
        if col in st.session_state[k].columns:
            st.session_state[k][col] = pd.to_numeric(st.session_state[k][col], errors='coerce').fillna(0)

# Sidebar
with st.sidebar:
    st.header("🌍 Settings")
    lingua_scelta = st.selectbox("Language", ["Italiano", "English"], index=0 if st.session_state.lingua == "Italiano" else 1)
    if lingua_scelta != st.session_state.lingua:
        st.session_state.lingua = lingua_scelta
        st.rerun()

# FIX: Parametro corretto è unsafe_allow_html
st.markdown(f"<h1 style='color:#FF5722;'>{t['titolo']}</h1>", unsafe_allow_html=True)
st.caption(t["sottotitolo"])

tab_1d, tab_2d = st.tabs([t["tab_1d"], t["tab_2d"]])
config_colonne = {"CODICE": t["col_codice"], "LUNGHEZZA": t["col_lunghezza"], "LARGHEZZA": t["col_larghezza"], "ALTEZZA": t["col_altezza"], "QTY": t["col_qty"]}

# Algoritmo Nesting 1D lineare
def esegui_nesting_1d(df_mag, df_rich):
    richieste_esplose = []
    for _, r in df_rich.iterrows():
        for _ in range(int(r['QTY'])):
            richieste_esplose.append({"CODICE": r['CODICE'], "LUNGHEZZA": float(r['LUNGHEZZA'])})
    richieste_esplose.sort(key=lambda x: x['LUNGHEZZA'], reverse=True)
    
    barre_disponibili = []
    for _, r in df_mag.iterrows():
        for _ in range(int(r['QTY'])):
            barre_disponibili.append({"CODICE": r['CODICE'], "LUNGHEZZA_ORIGINALE": float(r['LUNGHEZZA'])})
            
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
                if b_disp["CODICE"] == req["CODICE"] and b_disp["LUNGHEZZA_ORIGINALE"] >= req["LUNGHEZZA"]:
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
    # FIX: Corretto il typo da pianos_taglio a piani_taglio
    return piani_taglio if piani_taglio else None

# --- VISTA 1D ---
with tab_1d:
    col_l1, col_r1 = st.columns(2)
    with col_l1:
        st.subheader(t["magazzino_titolo"])
        st.session_state.magazzino_1d = st.data_editor(st.session_state.magazzino_1d, num_rows="dynamic", column_config=config_colonne, key="edit_mag_1d")
    with col_r1:
        st.subheader(t["richieste_titolo"])
        st.session_state.richieste_1d = st.data_editor(st.session_state.richieste_1d, num_rows="dynamic", column_config=config_colonne, key="edit_rich_1d")
        
    st.markdown("---")
    c_opt1, c_opt2, c_opt3 = st.columns([1, 1, 1])
    with c_opt1:
        soglia_1d = st.number_input("Soglia minima rientro sfrido (mm):", min_value=0.0, value=500.0, step=50.0)
    with c_opt2:
        btn_calcola_1d = st.button("🚀 Elabora Ottimizzazione 1D", use_container_width=True)
    with c_opt3:
        btn_reset_1d = st.button("🗑️ Reset Calcoli 1D", use_container_width=True)
        
    if btn_calcola_1d:
        st.session_state.risultati_calcolo_1d = esegui_nesting_1d(st.session_state.magazzino_1d, st.session_state.richieste_1d)
        st.rerun()
        
    if btn_reset_1d:
        st.session_state.risultati_calcolo_1d = None
        st.rerun()
        
    if st.session_state.risultati_calcolo_1d:
        risultati_1d = st.session_state.risultati_calcolo_1d
        st.markdown("## 📊 Risultati Ottimizzazione 1D")
        
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
        
        fig, ax = plt.subplots(figsize=(10, max(2, len(risultati_1d) * 0.6)))
        for idx, b in enumerate(risultati_1d):
            y_pos = idx
            start_x = 0
            for t_len in b["TAGLI"]:
                ax.add_patch(patches.Rectangle((start_x, y_pos - 0.25), t_len, 0.5, facecolor="#FF5722", edgecolor="white", lw=1))
                ax.text(start_x + t_len/2, y_pos, f"{int(t_len)}", ha="center", va="center", color="white", fontsize=8, weight="bold")
                start_x += t_len
            if b["LUNGHEZZA_RESIDUA"] > 0:
                colore_sfrido = "#4CAF50" if b["LUNGHEZZA_RESIDUA"] >= soglia_1d else "#B0BEC5"
                label_sfrido = f"Rilavorabile\n{int(b['LUNGHEZZA_RESIDUA'])}" if b["LUNGHEZZA_RESIDUA"] >= soglia_1d else f"Scarto\n{int(b['LUNGHEZZA_RESIDUA'])}"
                ax.add_patch(patches.Rectangle((start_x, y_pos - 0.25), b["LUNGHEZZA_RESIDUA"], 0.5, facecolor=colore_sfrido, edgecolor="white", lw=1))
                ax.text(start_x + b["LUNGHEZZA_RESIDUA"]/2, y_pos, label_sfrido, ha="center", va="center", color="white" if b["LUNGHEZZA_RESIDUA"] >= soglia_1d else "#37474F", fontsize=7, weight="bold" if b["LUNGHEZZA_RESIDUA"] >= soglia_1d else "normal")
        
        ax.set_yticks(range(len(risultati_1d)))
        ax.set_yticklabels([f"Barra {b['ID_BARRA']}\n({b['CODICE']})" for b in risultati_1d], fontsize=8)
        ax.set_xlim(0, max(b["LUNGHEZZA_TOTALE"] for b in risultati_1d) + 200)
        ax.set_ylim(-0.5, len(risultati_1d) - 0.5)
        ax.invert_yaxis()
        st.pyplot(fig)
        plt.close(fig)
        
        st.markdown("### 💾 Operazioni e Download")
        exp_col1, exp_col2, exp_col3 = st.columns(3)
        with exp_col1:
            st.download_button(label="📥 Scarica Elenco Tagli (CSV)", data=df_report.to_csv(index=False).encode('utf-8'), file_name="piano_taglio_1d.csv", mime="text/csv", use_container_width=True)
        with exp_col2:
            output_excel = io.BytesIO()
            with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
                df_report.to_excel(writer, index=False, sheet_name="Piano Taglio")
            st.download_button(label="📈 Scarica Distinta Excel", data=output_excel.getvalue(), file_name="piano_taglio_1d.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        with exp_col3:
            if st.button("✅ CONFERMA E AGGIORNA MAGAZZINO", type="primary", use_container_width=True):
                df_mag_attuale = st.session_state.magazzino_1d.copy()
                sfridi_aggiunti = 0
                for b in risultati_1d:
                    idx_match = df_mag_attuale[(df_mag_attuale['CODICE'] == b['CODICE']) & (df_mag_attuale['LUNGHEZZA'] == b['LUNGHEZZA_TOTALE'])].index
                    if len(idx_match) > 0:
                        df_mag_attuale.loc[idx_match[0], 'QTY'] -= 1
                    if b["LUNGHEZZA_RESIDUA"] >= soglia_1d:
                        idx_sfrido = df_mag_attuale[(df_mag_attuale['CODICE'] == b['CODICE']) & (df_mag_attuale['LUNGHEZZA'] == b['LUNGHEZZA_RESIDUA'])].index
                        if len(idx_sfrido) > 0:
                            df_mag_attuale.loc[idx_sfrido[0], 'QTY'] += 1
                        else:
                            nuovo_sfrido = pd.DataFrame([{"CODICE": b['CODICE'], "LUNGHEZZA": b['LUNGHEZZA_RESIDUA'], "QTY": 1}])
                            df_mag_attuale = pd.concat([df_mag_attuale, nuovo_sfrido], ignore_index=True)
                        sfridi_aggiunti += 1
                df_mag_attuale = df_mag_attuale[df_mag_attuale['QTY'] > 0].reset_index(drop=True)
                st.session_state.magazzino_1d = df_mag_attuale
                st.session_state.risultati_calcolo_1d = None
                st.success(f"Magazzino 1D aggiornato. Ritornati {sfridi_aggiunti} pezzi utili.")
                st.rerun()

# --- VISTA 2D ---
with tab_2d:
    col_l2, col_r2 = st.columns(2)
    with col_l2:
        st.subheader(t["magazzino_titolo"])
        st.session_state.magazzino_2d = st.data_editor(st.session_state.magazzino_2d, num_rows="dynamic", column_config=config_colonne, key="edit_mag_2d")
        
        st.markdown("---")
        st.subheader(t["dxf_titolo"])
        files_dxf = st.file_uploader("Upload .dxf (Multipli)", type=["dxf"], accept_multiple_files=True, key="uploader_dxf_2d")
        
        parti_dxf_caricate = {}
        if files_dxf:
            for f_dxf in files_dxf:
                with st.container(border=True):
                    st.markdown(f"**📄 File: {f_dxf.name}**")
                    raw_entities = load_dxf(f_dxf.getvalue())
                    geom = process_dxf_part(raw_entities)
                    if geom:
                        minx, miny, maxx, maxy = geom.bounds
                        w_pezzo = round(maxx - minx, 1)
                        h_pezzo = round(maxy - miny, 1)
                        st.success(f"✔️ Ingombro: {w_pezzo} x {h_pezzo} mm")
                        qty_spec = st.number_input(f"Quantità per {f_dxf.name}:", min_value=1, value=1, key=f"q_{f_dxf.name}")
                        parti_dxf_caricate[f_dxf.name] = {"width": w_pezzo, "height": h_pezzo, "qty": qty_spec}
                    else:
                        st.error("❌ Errore lettura geometria.")

    with col_r2:
        st.subheader(t["richieste_titolo"])
        st.session_state.richieste_2d = st.data_editor(st.session_state.richieste_2d, num_rows="dynamic", column_config=config_colonne, key="edit_rich_2d")
        
        st.markdown("---")
        soglia_2d = st.number_input("Soglia minima rientro sfrido lamiera (m²):", min_value=0.0, value=0.20, step=0.05)
        
        c_btn1, c_btn2 = st.columns(2)
        with c_btn1:
            btn_calcola_2d = st.button("🚀 Elabora Ottimizzazione 2D", use_container_width=True)
        with c_btn2:
            btn_reset_2d = st.button("🗑️ Reset Calcoli 2D", use_container_width=True)
            
        if btn_calcola_2d:
            if (parti_dxf_caricate or len(st.session_state.richieste_2d) > 0) and len(st.session_state.magazzino_2d) > 0:
                mat = st.session_state.magazzino_2d.iloc[0]
                area_lastra = (mat['LARGHEZZA'] * mat['ALTEZZA']) / 1000000.0
                
                area_pezzi = 0.0
                for _, p in parti_dxf_caricate.items():
                    area_pezzi += ((p['width'] * p['height']) / 1000000.0) * p['qty']
                for _, r in st.session_state.richieste_2d.iterrows():
                    area_pezzi += ((r['LARGHEZZA'] * r['ALTEZZA']) / 1000000.0) * r['QTY']
                    
                lastre_req = max(1, math.ceil(area_pezzi / (area_lastra * 0.78)))
                sfrido_singolo = round(((lastre_req * area_lastra) - area_pezzi) / lastre_req, 3)
                
                st.session_state.risultati_calcolo_2d = {
                    "codice": mat['CODICE'], "w": mat['LARGHEZZA'], "h": mat['ALTEZZA'],
                    "lastre": lastre_req, "sfrido_m2": sfrido_singolo
                }
            st.rerun()
            
        if btn_reset_2d:
            st.session_state.risultati_calcolo_2d = None
            st.rerun()
            
        if st.session_state.risultati_calcolo_2d:
            res = st.session_state.risultati_calcolo_2d
            st.markdown("### 📊 Risultati Ottimizzazione 2D")
            df_rep_2d = pd.DataFrame([{
                "Materiale": res["codice"], "Dimensioni (mm)": f"{res['w']}x{res['h']}",
                "Lastre Tagliate": res["lastre"], "Sfrido per Lastra (m²)": res["sfrido_m2"]
            }])
            st.dataframe(df_rep_2d, use_container_width=True)
            
            if st.button("✅ CONFERMA E AGGIORNA MAGAZZINO 2D", type="primary", use_container_width=True):
                df_mag2d = st.session_state.magazzino_2d.copy()
                idx_m = df_mag2d[(df_mag2d['CODICE'] == res['codice']) & (df_mag2d['LARGHEZZA'] == res['w'])].index
                if len(idx_m) > 0:
                    df_mag2d.loc[idx_m[0], 'QTY'] -= res['lastre']
                    
                sfridi_2d_aggiunti = 0
                if res['sfrido_m2'] >= soglia_2d:
                    w_sfrido = res['w']
                    h_sfrido = round((res['sfrido_m2'] * 1000000.0) / w_sfrido, 1)
                    nuovo_pezzo = pd.DataFrame([{"CODICE": res['codice'], "LARGHEZZA": w_sfrido, "ALTEZZA": h_sfrido, "QTY": res['lastre']}])
                    df_mag2d = pd.concat([df_mag2d, nuovo_pezzo], ignore_index=True)
                    sfridi_2d_aggiunti = res['lastre']
                    
                df_mag2d = df_mag2d[df_mag2d['QTY'] > 0].reset_index(drop=True)
                st.session_state.magazzino_2d = df_mag2d
                st.session_state.risultati_calcolo_2d = None
                st.success(f"Magazzino 2D aggiornato. Recuperate {sfridi_2d_aggiunti} lamiere residue.")
                st.rerun()
