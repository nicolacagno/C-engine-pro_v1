import ezdxf
import io

def load_dxf(file_bytes):
    try:
        stream = io.StringIO(file_bytes.decode('utf-8', errors='ignore'))
        doc = ezdxf.read(stream)
        entities = []

        def get_entities(layout):
            for e in layout:
                # Se è un blocco, esplodilo ricorsivamente
                if e.dxftype() == 'INSERT':
                    block = doc.blocks.get(e.dxf.name)
                    if block:
                        get_entities(block)
                else:
                    # Raccogliamo solo entità geometriche valide
                    if e.dxftype() in ('LINE', 'LWPOLYLINE', 'POLYLINE', 'ARC', 'CIRCLE'):
                        entities.append(e)
        
        get_entities(doc.modelspace())
        return entities
    except Exception as e:
        print(f"Errore: {e}")
        return []