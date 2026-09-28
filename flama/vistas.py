"""Proyecciones ortogonales con eliminación de líneas ocultas (HLR de
OpenCascade) según el método de proyección ISO E (primer diedro,
IRAM 4501 / ISO 5456-2).

Cada vista devuelve listas de primitivas 2D en milímetros reales:
  ("L", (x1,y1), (x2,y2))               recta
  ("C", (cx,cy), r)                     circunferencia completa
  ("A", (cx,cy), r, a0, a1)             arco (grados, antihorario)
  ("P", [(x,y), ...])                   polilínea (curvas libres)
"""

import math
import numpy as np
import cadquery as cq
from OCP.HLRBRep import HLRBRep_Algo, HLRBRep_HLRToShape
from OCP.HLRAlgo import HLRAlgo_Projector
from OCP.gp import gp_Ax2, gp_Pnt, gp_Dir

# (dirección hacia el observador, dirección X de la imagen)
VISTAS = {
    "anterior": ((0, -1, 0), (1, 0, 0)),     # vista A: desde el frente
    "superior": ((0, 0, 1), (1, 0, 0)),      # vista B: desde arriba (se ubica DEBAJO)
    "lat_izq": ((-1, 0, 0), (0, -1, 0)),     # vista C: desde la izquierda (se ubica a la DERECHA)
    "iso": ((1, -1, 1), (1, 1, 0)),          # isométrica (ISO 5456-3)
}


def _prim(edge, tol):
    e = cq.Edge(edge)
    gt = e.geomType()
    if gt == "LINE":
        a, b = e.startPoint(), e.endPoint()
        return ("L", (a.x, a.y), (b.x, b.y))
    if gt == "CIRCLE":
        c = e.arcCenter()
        r = e.radius()
        a, b = e.startPoint(), e.endPoint()
        if (a - b).Length < 1e-6:
            return ("C", (c.x, c.y), r)
        # sentido: comprobar con punto medio
        m = e.positionAt(0.5)
        a0 = math.degrees(math.atan2(a.y - c.y, a.x - c.x))
        a1 = math.degrees(math.atan2(b.y - c.y, b.x - c.x))
        am = math.degrees(math.atan2(m.y - c.y, m.x - c.x))
        def inside(x0, x1, x):
            return (x - x0) % 360 <= (x1 - x0) % 360
        if not inside(a0, a1, am):
            a0, a1 = a1, a0
        return ("A", (c.x, c.y), r, a0, a1)
    L = e.Length()
    n = max(6, min(400, int(L / tol)))
    pts = [e.positionAt(t) for t in np.linspace(0, 1, n + 1)]
    return ("P", [(p.x, p.y) for p in pts])


def proyectar(shape, vista, tol=0.8, ocultas=True):
    n, xd = VISTAS[vista]
    algo = HLRBRep_Algo()
    algo.Add(shape.wrapped)
    algo.Projector(HLRAlgo_Projector(gp_Ax2(gp_Pnt(0, 0, 0), gp_Dir(*n), gp_Dir(*xd))))
    algo.Update()
    algo.Hide()
    h = HLRBRep_HLRToShape(algo)
    out = {"vis": [], "oc": []}
    for key, comps in (("vis", (h.VCompound(), h.OutLineVCompound())),
                       ("oc", (h.HCompound(), h.OutLineHCompound()) if ocultas else ())):
        for c in comps:
            if c is None or c.IsNull():
                continue
            for e in cq.Shape.cast(c).Edges():
                try:
                    out[key].append(_prim(e.wrapped, tol))
                except Exception:
                    pass
    return out


def a_polilineas(prims, tol=0.5):
    """Convierte primitivas a listas de puntos (para recortes y extensiones)."""
    res = []
    for p in prims:
        if p[0] == "L":
            res.append([p[1], p[2]])
        elif p[0] == "P":
            res.append(p[1])
        elif p[0] in ("C", "A"):
            c, r = p[1], p[2]
            a0, a1 = (0, 360) if p[0] == "C" else (p[3], p[4])
            span = (a1 - a0) % 360 or 360
            n = max(12, int(2 * math.pi * r * span / 360 / tol))
            res.append([(c[0] + r * math.cos(math.radians(a0 + span * i / n)),
                         c[1] + r * math.sin(math.radians(a0 + span * i / n))) for i in range(n + 1)])
    return res


def extension(prims):
    xs, ys = [], []
    for pl in a_polilineas(prims, 2.0):
        for x, y in pl:
            xs.append(x)
            ys.append(y)
    return min(xs), min(ys), max(xs), max(ys)


def proyectar_punto(p, vista):
    n, xd = VISTAS[vista]
    n = np.array(n, float) / np.linalg.norm(n)
    xd = np.array(xd, float) / np.linalg.norm(xd)
    yd = np.cross(n, xd)
    p = np.array(p, float)
    return float(p @ xd), float(p @ yd)


# ------------------------------------------------------------------ cortes
def corte_por_plano_xz(piezas, nombres):
    """Corte A-A: plano XZ (y = 0), se retira la mitad anterior (y < 0) y se
    observa desde el frente. Devuelve (proyección, polígonos de sección por pieza)."""
    import shapely.geometry as sg
    big = 5000
    keep = cq.Solid.makeBox(2 * big, big, 2 * big, cq.Vector(-big, 0, -big))
    mitades = {}
    for k in nombres:
        if k in piezas:
            mitades[k] = piezas[k].intersect(keep)
    comp = cq.Compound.makeCompound(list(mitades.values()))
    proy = proyectar(comp, "anterior", tol=0.3, ocultas=False)
    secciones = {}
    for k, s in mitades.items():
        polys = []
        for f in s.Faces():
            if f.geomType() != "PLANE":
                continue
            nrm = f.normalAt()
            c = f.Center()
            if abs(nrm.y + 1) > 1e-6 or abs(c.y) > 1e-4:
                continue
            ext = _wire_poly(f.outerWire())
            holes = [_wire_poly(w) for w in f.innerWires()]
            poly = ext
            for hh in holes:
                poly = poly.difference(hh)
            if not poly.is_valid:
                poly = poly.buffer(0)
            polys.append(poly)
        secciones[k] = polys
    return proy, secciones


def _wire_poly(w, tol=0.2):
    import shapely.geometry as sg
    from shapely.ops import polygonize, unary_union
    lines = []
    for e in w.Edges():
        L = e.Length()
        n = 1 if e.geomType() == "LINE" else max(4, min(400, int(L / tol)))
        ps = [e.positionAt(t) for t in np.linspace(0, 1, n + 1)]
        lines.append(sg.LineString([(round(p.x, 6), round(p.z, 6)) for p in ps]))
    polys = list(polygonize(unary_union(lines)))
    if not polys:
        return sg.Polygon()
    return unary_union(polys)
