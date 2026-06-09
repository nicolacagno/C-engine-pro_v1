import ezdxf

def load_dxf(file_bytes):
    try:
        # readbytes è il metodo nativo più sicuro per ezdxf per gestire i file in memoria
        doc = ezdxf.readbytes(file_bytes)
        return doc.modelspace()
    except Exception:
        return None
