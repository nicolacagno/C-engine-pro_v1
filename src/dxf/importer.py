# src/dxf/importer.py
import ezdxf

def load_dxf(file_bytes):
    """
    Legge in modo sicuro i byte di un file DXF provenienti da Streamlit.
    Gestisce automaticamente sia file ASCII che Binary e corregge le codifiche (Windows-1252/ISO).
    """
    try:
        # readbytes è il metodo nativo di ezdxf per digerire i file caricati via web
        doc = ezdxf.readbytes(file_bytes)
        return doc
    except Exception as e:
        try:
            # Fallback di emergenza: decodifica forzata ignorando caratteri CAD corrotti
            text = file_bytes.decode('utf-8', errors='ignore')
            return ezdxf.readstr(text)
        except Exception:
            return None
