# src/dxf/converter.py
import ezdxf
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import polygonize, unary_union

def process_dxf_part(doc):
    """
    Scompone il documento DXF ed estrae una geometria Shapely Polygon pulita,
    riconoscendo automaticamente il perimetro esterno e i fori interni.
    """
    if doc is None:
        return None
    
    msp = doc.modelspace()
    segmenti = []
    
    # 1. Estrazione di Polilinee (LWPOLYLINE e POLYLINE) - Tipiche dei profili di taglio
    for poly in msp.query('LWPOLYLINE POLYLINE'):
        try:
            punti = [(p[0], p[1]) for p in poly.points()]
            if len(punti) >= 2:
                segmenti.append(LineString(punti))
        except Exception:
            pass
            
    # 2. Estrazione di Linee singole (LINE)
    for line in msp.query('LINE'):
        try:
            p1 = (line.dxf.start.x, line.dxf.start.y)
            p2 = (line.dxf.end.x, line.dxf.end.y)
            segmenti.append(LineString([p1, p2]))
        except Exception:
            pass
            
    # 3. Estrazione di Cerchi (CIRCLE) - Convertiti in poligoni ad alta precisione
    for circle in msp.query('CIRCLE'):
        try:
            centro = (circle.dxf.center.x, circle.dxf.center.y)
            raggio = circle.dxf.radius
            # Approssimazione geometrica fluida del cerchio (64 segmenti)
            cerchio_shapely = Point(centro).buffer(raggio, quad_segs=16)
            segmenti.append(LineString(cerchio_shapely.exterior.coords))
        except Exception:
            pass

    if not segmenti:
        return None
        
    try:
        # Unisce tutti i segmenti stradali grafici trovati nel CAD
        linee_unite = unary_union(segmenti)
        
        # Genera le aree chiuse (i poligoni effettivi)
        poligoni_rilevati = list(polygonize(linee_unite))
        
        if not poligoni_rilevati:
            return None
            
        # Ordina i poligoni dal più grande al più piccolo (il più grande è la lamiera esterna)
        poligoni_rilevati.sort(key=lambda p: p.area, reverse=True)
        profilo_esterno = poligoni_rilevati[0]
        
        # Identifica i fori interni: qualsiasi area minore contenuta nel profilo esterno
        fori = []
        for p in poligoni_rilevati[1:]:
            if profilo_esterno.contains(p):
                fori.append(p.exterior.coords)
                
        # Crea il pezzo meccanico finito (pieno esterno e vuoti interni)
        pezzo_finale = Polygon(profilo_esterno.exterior.coords, fori)
        return pezzo_finale
        
    except Exception:
        return None
