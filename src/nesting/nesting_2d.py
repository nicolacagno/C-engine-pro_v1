import streamlit as st
import pandas as pd
import math
from src.dxf.importer import load_dxf
from src.dxf.converter import process_dxf_part

def render_nesting_2d(t, config_colonne):
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
                        st.success(f"✔️ Ingombro rilevato: {w_pezzo} x {h_pezzo} mm")
                        qty_spec = st.number_input(f"Quantità per {f_dxf.name}:", min_value=1, value=1, key=f"q_{f_dxf.name}")
                        parti_dxf_caricate[f_dxf.name] = {"width": w_pezzo, "height": h_pezzo, "qty": qty_spec}
                    else:
                        st.error(t["msg_error_dxf"])

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
