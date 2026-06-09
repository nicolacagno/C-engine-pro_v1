import ezdxf
from shapely.geometry import Polygon
from shapely import affinity
import numpy as np

def entities_to_shapely(entities):
    """
    Converte una lista di entità DXF in un oggetto Shapely Polygon.
    Assume che le entità formino un unico contorno chiuso (shell).
    """
    points = []
    
    for e in entities:
        # Se è una linea, prendi start e end
        if e.dxftype() == 'LINE':
            points.append((e.dxf.start.x, e.dxf.start.y))
            points.append((e.dxf.end.x, e.dxf.end.y))
            
        # Se è una polilinea, estrai i punti
        elif e.dxftype() in ('LWPOLYLINE', 'POLYLINE'):
            points.extend([(pt[0], pt[1]) for pt in e.get_points(format='xy')])
            
        # Se è un arco o cerchio, usiamo flattening per trasformarlo in segmenti
        elif e.dxftype() in ('ARC', 'CIRCLE', 'ELLIPSE'):
            # 0.25 è la tolleranza di approssimazione
            for p in e.flattening(distance=0.25):
                points.append((p.x, p.y))

    if len(points) < 3:
        return None

    # Crea il poligono Shapely
    poly = Polygon(points)
    
    # Se il poligono è invalido (es. auto-intersecante), prova a pulirlo
    if not poly.is_valid:
        poly = poly.buffer(0)
        
    return poly

def normalize_polygon(poly):
    """
    Trasla il poligono in modo che il suo punto minimo sia (0,0).
    """
    if poly is None or poly.is_empty:
        return poly
        
    minx, miny, maxx, maxy = poly.bounds
    return affinity.translate(poly, xoff=-minx, yoff=-miny)

def process_dxf_part(entities):
    """
    Funzione orchestratrice: converte ed esplode le entità in un Polygon pulito.
    """
    poly = entities_to_shapely(entities)
    return normalize_polygon(poly)