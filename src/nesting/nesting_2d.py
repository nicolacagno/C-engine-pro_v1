import io
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import streamlit as st

def genera_pdf_report_2d(fig, efficienza, lista_pezzi):
    """
    Riceve la figura Matplotlib (fig), la percentuale di efficienza 
    e la lista dei pezzi posizionati per generare un PDF in memoria.
    """
    # 1. Salva il grafico di Matplotlib in memoria come immagine PNG
    img_buf = io.BytesIO()
    fig.savefig(img_buf, format='png', bbox_inches='tight', dpi=200)
    img_buf.seek(0)

    # 2. Crea un buffer in memoria per il documento PDF
    pdf_buf = io.BytesIO()

    # 3. Configura il documento PDF (A4 con margini di 40 punti)
    doc = SimpleDocTemplate(pdf_buf, pagesize=A4, leftMargin=40, rightMargin=40, topMargin=40, bottomMargin=40)
    story = []
    styles = getSampleStyleSheet()

    # Titolo del Report
    stile_titolo = styles['Heading1']
    stile_titolo.textColor = colors.HexColor("#1E3A8A")  # Blu scuro aziendale
    story.append(Paragraph("Report Ottimizzazione Nesting 2D", stile_titolo))
    story.append(Spacer(1, 15))

    # Riepilogo dati generali
    story.append(Paragraph(f"<b>Rendimento Utilizzo Lamiera:</b> {efficienza}%", styles['Normal']))
    story.append(Spacer(1, 15))

    # Inserimento del Grafico/Mappa di Taglio
    story.append(Paragraph("<b>Mappa del Layout di Taglio:</b>", styles['Heading2']))
    story.append(Spacer(1, 8))
    
    # La larghezza massima utile su un A4 con questi margini è circa 515 punti
    immagine_pdf = Image(img_buf, width=480, height=300)
    story.append(immagine_pdf)
    story.append(Spacer(1, 20))

    # Tabella dei dettagli dei pezzi posizionati
    story.append(Paragraph("<b>Dettaglio Pezzi Posizionati nel Piano:</b>", styles['Heading2']))
    story.append(Spacer(1, 8))

    # Intestazione della tabella
    dati_tabella = [["ID Pezzo", "Larghezza (mm)", "Altezza (mm)", "Coordinate (X, Y)"]]
    
    # Popola la tabella con i tuoi pezzi reali
    for p in lista_pezzi:
        dati_tabella.append([
            str(p.get('id', 'N/D')),
            str(p.get('w', '-')),
            str(p.get('h', '-')),
            f"X: {p.get('x', 0)} , Y: {p.get('y', 0)}"
        ])

    # Crea la tabella e applica uno stile moderno ed elegante
    tabella = Table(dati_tabella, colWidths=[90, 110, 110, 150])
    tabella.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1E3A8A")), # Sfondo intestazione blu
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),                # Testo intestazione bianco
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#F9FAFB")), # Sfondo righe grigio chiaro
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),  # Linee di divisione sottili
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
    ]))
    story.append(tabella)

    # Costruisce il PDF inserendo tutti gli elementi
    doc.build(story)
    pdf_buf.seek(0)
    return pdf_buf
