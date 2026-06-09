import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import io

# Importazioni ReportLab per la generazione del PDF
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# FUNZIONE INTERNA: Generazione Report PDF Professionale
def genera_pdf_report(df, risultati_1d, fig):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor("#FF5722"),
        spaceAfter=15
    )
    story.append(Paragraph("🔥 MetalHub Suite V2 - Report Nesting 1D", title_style))
    story.append(Spacer(1, 10))
    
    data = [list(df.columns)] + df.values.tolist()
    table = Table(data, hAlign='LEFT')
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#FF5722")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#F9F9F9")),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor("#E0E0E0")),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(table)
    story.append(Spacer(1, 20))
    
    img_buf = io.BytesIO()
    fig.savefig(img_buf, format='png', bbox_inches='tight', dpi=200)
    img_buf.seek(0)
    
    fig_w, fig_h = fig.get_size_inches()
    aspect_ratio = fig_h / fig_w
    pdf_img_width = 535  
    pdf_img_height = pdf_img_width * aspect_ratio
    
    story.append(Image(img_buf, width=pdf_img_width, height=pdf_img_height))
    
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# FUNZIONE INTERNA: Algoritmo Nesting 1D lineare (First-Fit Decreasing)
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
    return piani_taglio if piani_taglio else None

# FUNZIONE PRINCIPALE: Render dell'interfaccia richiamata da app.py
def render_nesting_1d(t, config_colonne):
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
        
        st.markdown("### 💾 Operazioni e Download")
        exp_col1, exp_col2, exp_col3, exp_col4 = st.columns(4)
        
        with exp_col1:
            st.download_button(label="📥 Scarica Elenco Tagli (CSV)", data=df_report.to_csv(index=False).encode('utf-8'), file_name="piano_taglio_1d.csv", mime="text/csv", use_container_width=True)
        
        with exp_col2:
            output_excel = io.BytesIO()
            with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
                df_report.to_excel(writer, index=False, sheet_name="Piano Taglio")
            st.download_button(label="📈 Scarica Distinta Excel", data=output_excel.getvalue(), file_name="piano_taglio_1d.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        
        with exp_col3:
            pdf_data = genera_pdf_report(df_report, risultati_1d, fig)
            st.download_button(label="📄 Scarica Report PDF", data=pdf_data, file_name="piano_taglio_1d.pdf", mime="application/pdf", use_container_width=True)
            
        with exp_col4:
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
        plt.close(fig)