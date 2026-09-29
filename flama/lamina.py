"""Elementos gráficos de lámina (ezdxf): formato, recuadro, zonas, rótulo,
lista de piezas, capas y tipos de línea, cotas, globos, rayados, detalles.

Todo se dibuja en espacio modelo en milímetros de papel (lámina a escala 1:1);
las vistas se dibujan reducidas a 1/k y las cotas usan DIMLFAC = k para que la
cifra de cota indique siempre la medida REAL de la pieza.
"""

import math
import ezdxf
from ezdxf.enums import TextEntityAlignment
import shapely.geometry as sg
from shapely.ops import unary_union

from . import vistas as V

FORMATOS = {"A3": (420.0, 297.0), "A2": (594.0, 420.0), "A1": (841.0, 594.0)}
MARGEN_IZQ, MARGEN = 20.0, 10.0          # ISO 5457 / IRAM 4504
ROT_W, ROT_H = 180.0, 56.0               # rótulo (ISO 7200: ancho máx. 180 mm)
ESCALAS = [(1, 1), (1, 2), (1, 5), (1, 10), (1, 20)]      # ISO 5455 / IRAM 4505
AMPLIAC = [(5, 1), (2, 1), (1, 1), (1, 2), (1, 5), (1, 10)]

A = TextEntityAlignment

CAPAS = {
    # nombre: (color ACI, espesor 1/100 mm, tipo de línea)
    "01-VISIBLE": (7, 50, "CONTINUOUS"),
    "02-OCULTA": (4, 25, "ISO02-TRAZOS"),
    "03-EJE": (1, 25, "ISO04-TRAZO-PUNTO"),
    "04-COTA": (3, 25, "CONTINUOUS"),
    "05-RAYADO": (8, 25, "CONTINUOUS"),
    "06-TEXTO": (7, 25, "CONTINUOUS"),
    "07-RECUADRO": (7, 70, "CONTINUOUS"),
    "08-FINA": (5, 25, "CONTINUOUS"),
    "09-PLANO-CORTE": (1, 50, "ISO04-TRAZO-PUNTO"),
    "10-ROTULO": (7, 35, "CONTINUOUS"),
    "11-TEXTO-ROTULO": (7, 25, "CONTINUOUS"),
    "12-SOLDADURA": (6, 25, "CONTINUOUS"),
}


def escala_txt(e):
    return f"{e[0]}:{e[1]}"


def nuevo_doc():
    doc = ezdxf.new("R2018", setup=False, units=4)
    doc.header["$MEASUREMENT"] = 1
    doc.header["$LWDISPLAY"] = 1
    doc.header["$LTSCALE"] = 1.0
    doc.header["$PSLTSCALE"] = 0
    doc.header["$DIMDSEP"] = 44  # separador decimal coma
    # ISO 128-20 (d = 0,25 mm): trazo 12d, espacio 3d; trazo largo 24d, punto 0,5d
    doc.linetypes.add("ISO02-TRAZOS", pattern=[3.75, 3.0, -0.75],
                      description="ISO 128 tipo 02 - trazos (d=0,25) __ __ __")
    doc.linetypes.add("ISO04-TRAZO-PUNTO", pattern=[7.625, 6.0, -0.75, 0.125, -0.75],
                      description="ISO 128 tipo 04 - trazo largo y punto (d=0,25) ____ . ____")
    for n, (c, lw, lt) in CAPAS.items():
        doc.layers.add(n, color=c, lineweight=lw, linetype=lt)
    doc.styles.add("ISO3098", font="isocpeur.ttf")
    ds = doc.dimstyles.new("FLAMA-ISO")
    ds.dxf.dimtxsty = "ISO3098"
    ds.dxf.dimtxt = 3.5
    ds.dxf.dimasz = 3.0
    ds.dxf.dimexe = 2.0
    ds.dxf.dimexo = 1.0
    ds.dxf.dimgap = 1.0
    ds.dxf.dimtad = 1
    ds.dxf.dimtih = 0
    ds.dxf.dimtoh = 0
    ds.dxf.dimdec = 1
    ds.dxf.dimzin = 8
    ds.dxf.dimdsep = 44
    ds.dxf.dimclrd = 3
    ds.dxf.dimclre = 3
    ds.dxf.dimclrt = 3
    ds.dxf.dimlwd = 25
    ds.dxf.dimlwe = 25
    ds.dxf.dimtix = 0
    ds.dxf.dimatfit = 3
    return doc


class Hoja:
    def __init__(self, doc, formato, ox=0.0):
        """ox: desplazamiento en X de la lámina dentro del espacio modelo (varias
        hojas del mismo plano quedan una al lado de la otra)."""
        self.doc = doc
        self.msp = doc.modelspace()
        self.fmt = formato
        self.ox = ox
        self.W, self.H = FORMATOS[formato]
        self.fx0, self.fy0 = ox + MARGEN_IZQ, MARGEN
        self.fx1, self.fy1 = ox + self.W - MARGEN, self.H - MARGEN

    # ------------------------------------------------------------ básicos
    def texto(self, s, p, h=3.5, al=A.BOTTOM_LEFT, capa="06-TEXTO", rot=0):
        t = self.msp.add_text(s, height=h, rotation=rot,
                              dxfattribs={"layer": capa, "style": "ISO3098"})
        t.set_placement(p, align=al)
        return t

    def linea(self, a, b, capa="08-FINA"):
        return self.msp.add_line(a, b, dxfattribs={"layer": capa})

    def rect(self, x0, y0, x1, y1, capa="10-ROTULO"):
        self.msp.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], close=True,
                                dxfattribs={"layer": capa})

    # ------------------------------------------------------------ formato
    def formato(self):
        W, H, o = self.W, self.H, self.ox
        # borde de corte (línea fina)
        self.rect(o, 0, o + W, H, capa="08-FINA")
        # recuadro
        self.rect(self.fx0, self.fy0, self.fx1, self.fy1, capa="07-RECUADRO")
        # marcas de centrado: desde el borde de corte hasta 5 mm dentro del recuadro
        cx, cy = o + W / 2, H / 2
        self.linea((cx, 0), (cx, self.fy0 + 5), "07-RECUADRO")
        self.linea((cx, H), (cx, self.fy1 - 5), "07-RECUADRO")
        self.linea((o, cy), (self.fx0 + 5, cy), "07-RECUADRO")
        self.linea((o + W, cy), (self.fx1 - 5, cy), "07-RECUADRO")
        # sistema de zonas (campos de 50 mm a partir de las marcas de centrado)
        xs = sorted(set([cx + 50 * i for i in range(-20, 21) if self.fx0 < cx + 50 * i < self.fx1]))
        ys = sorted(set([cy + 50 * i for i in range(-20, 21) if self.fy0 < cy + 50 * i < self.fy1]))
        for x in xs:
            if abs(x - cx) > 1e-6:
                self.linea((x, self.fy0), (x, self.fy0 - 5), "08-FINA")
                self.linea((x, self.fy1), (x, self.fy1 + 5), "08-FINA")
        for y in ys:
            if abs(y - cy) > 1e-6:
                self.linea((self.fx0, y), (self.fx0 - 5, y), "08-FINA")
                self.linea((self.fx1, y), (self.fx1 + 5, y), "08-FINA")
        bx = [self.fx0] + xs + [self.fx1]
        by = [self.fy0] + ys + [self.fy1]
        for i in range(len(bx) - 1):
            xm = (bx[i] + bx[i + 1]) / 2
            self.texto(str(i + 1), (xm, self.fy0 - 5), 3.5, A.MIDDLE_CENTER)
            self.texto(str(i + 1), (xm, self.fy1 + 5), 3.5, A.MIDDLE_CENTER)
        letras = "ABCDEFGHJKLMNP"
        for j in range(len(by) - 1):
            ym = (by[j] + by[j + 1]) / 2
            L = letras[len(by) - 2 - j]
            self.texto(L, (self.fx0 - 10, ym), 3.5, A.MIDDLE_CENTER)
            self.texto(L, (self.fx1 + 5, ym), 3.5, A.MIDDLE_CENTER)

    # ------------------------------------------------------------ símbolo ISO E
    def simbolo_primer_diedro(self, x, y, h=3.5):
        """Símbolo del método de proyección ISO E (ISO 5456-2): vista del
        tronco de cono (trapezio, extremo menor a la derecha) y, a su izquierda,
        su vista desde la derecha (dos circunferencias)."""
        D, d = 2 * h, h
        L = 2 * h
        m = self.msp
        cxc = x + D / 2
        m.add_circle((cxc, y), D / 2, dxfattribs={"layer": "01-VISIBLE"})
        m.add_circle((cxc, y), d / 2, dxfattribs={"layer": "01-VISIBLE"})
        x0 = x + D + h
        m.add_lwpolyline([(x0, y - D / 2), (x0 + L, y - d / 2), (x0 + L, y + d / 2), (x0, y + D / 2)],
                         close=True, dxfattribs={"layer": "01-VISIBLE"})
        self.linea((x - 1.5, y), (x0 + L + 1.5, y), "03-EJE")
        self.linea((cxc, y - D / 2 - 1.5), (cxc, y + D / 2 + 1.5), "03-EJE")

    # ------------------------------------------------------------ rótulo
    def _celda(self, lab, val, x0, y0, x1, y1, hv=3.5, al="c"):
        self.rect(x0, y0, x1, y1, "10-ROTULO")
        if lab:
            self.texto(lab, (x0 + 1.0, y1 - 1.0), 1.8, A.TOP_LEFT, "11-TEXTO-ROTULO")
        if val is not None and val != "":
            yv = y0 + (y1 - y0 - (2.8 if lab else 0)) / 2
            if al == "c":
                self.texto(str(val), ((x0 + x1) / 2, yv), hv, A.MIDDLE_CENTER, "11-TEXTO-ROTULO")
            else:
                self.texto(str(val), (x0 + 1.5, yv), hv, A.MIDDLE_LEFT, "11-TEXTO-ROTULO")

    def rotulo(self, r):
        """Rótulo (IRAM 4508 / ISO 7200). r: dict con titulo, subtitulo, codigo,
        hoja, hojas, escala, material, edicion, fecha, dibujo, reviso, aprobo,
        tipo_doc, empresa."""
        x0, y0 = self.fx1 - ROT_W, self.fy0
        x1, y1 = self.fx1, self.fy0 + ROT_H
        C = self._celda
        c1, c2 = x0 + 56, x0 + 128
        # ---- columna izquierda
        yF = y0 + 32
        C("", None, x0, y1 - 6, x0 + 14, y1)
        C("", "Fecha", x0 + 14, y1 - 6, x0 + 33, y1, 2.2)
        C("", "Nombre", x0 + 33, y1 - 6, c1, y1, 2.2)
        filas = [("Dibujó", r.get("fecha", ""), r.get("dibujo", "")),
                 ("Revisó", r.get("fecha_rev", ""), r.get("reviso", "")),
                 ("Aprobó", r.get("fecha_apr", ""), r.get("aprobo", ""))]
        for i, (a, fch, nom) in enumerate(filas):
            ya = y1 - 6 * (i + 2)
            C("", a, x0, ya, x0 + 14, ya + 6, 2.2, "l")
            C("", fch, x0 + 14, ya, x0 + 33, ya + 6, 2.2)
            C("", nom, x0 + 33, ya, c1, ya + 6, 2.2)
        C("Escala", r["escala"], x0, y0 + 18, x0 + 22, yF, 5.0)
        C("Método de proyección", None, x0 + 22, y0 + 18, c1, yF)
        self.simbolo_primer_diedro(x0 + 30.5, y0 + 23.5)
        C("Tolerancias generales", "ISO 2768-m", x0, y0 + 8, c1, y0 + 18, 3.5)
        C("Formato", self.fmt, x0, y0, c1, y0 + 8, 3.5)
        # ---- columna central
        C("Propietario", r.get("empresa", "FLAMA S.A."), c1, y1 - 12, c2, y1, 5.0)
        C("Denominación", None, c1, y0 + 12, c2, y1 - 12)
        tit = r["titulo"]
        if len(tit) <= 19:
            self.texto(tit, ((c1 + c2) / 2, y0 + 25), 5.0, A.MIDDLE_CENTER, "11-TEXTO-ROTULO")
        elif len(tit) <= 27:
            self.texto(tit, ((c1 + c2) / 2, y0 + 25), 3.5, A.MIDDLE_CENTER, "11-TEXTO-ROTULO")
        else:
            corte = tit.rfind(" ", 0, 20)
            self.texto(tit[:corte], ((c1 + c2) / 2, y0 + 28), 5.0, A.MIDDLE_CENTER, "11-TEXTO-ROTULO")
            self.texto(tit[corte + 1:], ((c1 + c2) / 2, y0 + 21.5), 3.5, A.MIDDLE_CENTER, "11-TEXTO-ROTULO")
        self.texto(r.get("subtitulo", ""), ((c1 + c2) / 2, y0 + 15.5), 2.2, A.MIDDLE_CENTER, "11-TEXTO-ROTULO")
        C("Tipo de documento", r.get("tipo_doc", ""), c1, y0, c2, y0 + 12, 3.5)
        # ---- columna derecha
        cm = c2 + 24
        cod = r["codigo"]
        C("N° de plano", cod, c2, y0, x1, y0 + 14, 5.0 if len(cod) <= 11 else (3.5 if len(cod) <= 16 else 3.0))
        C("Hoja", f"{r['hoja']} / {r['hojas']}", c2, y0 + 14, cm, y0 + 24, 3.5)
        C("Idioma", "es", cm, y0 + 14, x1, y0 + 24, 3.5)
        C("Edición", r.get("edicion", "0"), c2, y0 + 24, cm, y0 + 34, 3.5)
        C("Fecha de emisión", r.get("fecha", ""), cm, y0 + 24, x1, y0 + 34, 2.5)
        C("Material", r.get("material", ""), c2, y0 + 34, x1, y0 + 45, 2.5)
        C("Reemplaza a / Reemplazado por", r.get("reemplaza", "-"), c2, y0 + 45, x1, y1, 2.5)
        self.rect(x0, y0, x1, y1, "07-RECUADRO")
        return y1

    # ------------------------------------------------------------ lista de piezas
    def lista_piezas(self, filas, y_base, h_fila=5.0):
        """IRAM 4508 / ISO 7573: sobre el rótulo, encabezado abajo, lectura hacia arriba."""
        x0, x1 = self.fx1 - ROT_W, self.fx1
        cols = [("Pos.", 10), ("Cant.", 10), ("Denominación", 66), ("Material", 50), ("Observaciones", 44)]
        xs = [x0]
        for _, w in cols:
            xs.append(xs[-1] + w)
        n = len(filas)
        y_top = y_base + h_fila * (n + 1)
        self.rect(x0, y_base, x1, y_top, "10-ROTULO")
        for i in range(1, n + 1):
            self.linea((x0, y_base + h_fila * i), (x1, y_base + h_fila * i), "10-ROTULO")
        for x in xs[1:-1]:
            self.linea((x, y_base), (x, y_top), "10-ROTULO")
        for (nom, w), x in zip(cols, xs):
            self.texto(nom, (x + w / 2, y_base + h_fila / 2), 2.5, A.MIDDLE_CENTER, "11-TEXTO-ROTULO")
        for i, f in enumerate(filas):
            yy = y_base + h_fila * (i + 1) + h_fila / 2
            for j, (val, (nom, w)) in enumerate(zip(f, cols)):
                al = A.MIDDLE_CENTER if j < 2 else A.MIDDLE_LEFT
                px = xs[j] + (w / 2 if j < 2 else 1.2)
                s = str(val)
                hh = 2.5 if len(s) * 1.9 < w or j < 2 else 2.0
                self.texto(s, (px, yy), hh, al, "11-TEXTO-ROTULO")
        return y_top

    # ------------------------------------------------------------ geometría
    def prims(self, prims, capa, T):
        """dibuja primitivas de vistas.py transformadas por T=(ox, oy, f)."""
        ox, oy, f = T
        m = self.msp
        at = {"layer": capa}
        for p in prims:
            if p[0] == "L":
                a = (ox + p[1][0] * f, oy + p[1][1] * f)
                b = (ox + p[2][0] * f, oy + p[2][1] * f)
                if math.hypot(a[0] - b[0], a[1] - b[1]) > 1e-4:
                    m.add_line(a, b, dxfattribs=at)
            elif p[0] == "C":
                m.add_circle((ox + p[1][0] * f, oy + p[1][1] * f), p[2] * f, dxfattribs=at)
            elif p[0] == "A":
                m.add_arc((ox + p[1][0] * f, oy + p[1][1] * f), p[2] * f, p[3], p[4], dxfattribs=at)
            elif p[0] == "P":
                pts = [(ox + x * f, oy + y * f) for x, y in p[1]]
                m.add_lwpolyline(pts, dxfattribs=at)

    def polilineas(self, pls, capa):
        for pl in pls:
            if len(pl) >= 2:
                self.msp.add_lwpolyline(pl, dxfattribs={"layer": capa})

    def rayado(self, poly, angulo=0, esp=2.5, solido=False, capa="05-RAYADO"):
        """poly: shapely (Multi)Polygon en coordenadas de papel."""
        geoms = poly.geoms if hasattr(poly, "geoms") else [poly]
        for g in geoms:
            if g.is_empty or g.area < 1e-3:
                continue
            h = self.msp.add_hatch(color=7 if solido else 8, dxfattribs={"layer": capa})
            if solido:
                h.set_solid_fill(color=7)
            else:
                h.set_pattern_fill("ANSI31", scale=esp / 3.175, angle=angulo)
            h.paths.add_polyline_path(list(g.exterior.coords)[:-1], is_closed=True, flags=1)
            for it in g.interiors:
                h.paths.add_polyline_path(list(it.coords)[:-1], is_closed=True, flags=0)

    # ------------------------------------------------------------ cotas
    def cota_lineal(self, p1, p2, base, ang, k, prefijo="", texto=None):
        ov = {"dimlfac": k}
        if prefijo:
            ov["dimpost"] = prefijo + "<>"
        d = self.msp.add_linear_dim(base=base, p1=p1, p2=p2, angle=ang, dimstyle="FLAMA-ISO",
                                    override=ov, text=texto if texto else "<>",
                                    dxfattribs={"layer": "04-COTA"})
        d.render()
        return d

    def eje(self, a, b):
        self.linea(a, b, "03-EJE")

    # ------------------------------------------------------------ globos
    def globo(self, n, anc, pos, r=4.0):
        m = self.msp
        m.add_circle(pos, r, dxfattribs={"layer": "08-FINA"})
        self.texto(str(n), pos, 3.5, A.MIDDLE_CENTER, "06-TEXTO")
        dx, dy = anc[0] - pos[0], anc[1] - pos[1]
        L = math.hypot(dx, dy)
        if L > r:
            p0 = (pos[0] + dx / L * r, pos[1] + dy / L * r)
            m.add_line(p0, anc, dxfattribs={"layer": "08-FINA"})
        # punto de referencia (ISO 6433: extremo dentro del contorno)
        h = m.add_hatch(color=7, dxfattribs={"layer": "08-FINA"})
        h.set_solid_fill(color=7)
        h.paths.add_edge_path().add_arc(anc, 0.6, 0, 360)

    # ------------------------------------------------------------ corte
    def plano_corte(self, a, b, letra, sentido):
        """Traza del plano de corte (ISO 128-44): extremos gruesos trazo-punto,
        flechas indicando el sentido de observación y letras."""
        m = self.msp
        ux, uy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(ux, uy)
        ux, uy = ux / L, uy / L
        self.linea(a, b, "03-EJE")
        for p, sgn in ((a, 1), (b, -1)):
            q = (p[0] + sgn * ux * 8, p[1] + sgn * uy * 8)
            m.add_line(p, q, dxfattribs={"layer": "07-RECUADRO"})
            tail = (p[0] + sgn * ux * 3, p[1] + sgn * uy * 3)
            tip = (tail[0] + sentido[0] * 9, tail[1] + sentido[1] * 9)
            m.add_line(tail, tip, dxfattribs={"layer": "08-FINA"})
            self._flecha(tip, sentido)
            self.texto(letra, (tip[0] + sentido[0] * 2 - sgn * ux * 3, tip[1] + sentido[1] * 2 - sgn * uy * 3),
                       5, A.MIDDLE_CENTER)

    def _flecha(self, tip, d, L=3.0, w=1.0):
        px, py = -d[1], d[0]
        b = (tip[0] - d[0] * L, tip[1] - d[1] * L)
        pts = [tip, (b[0] + px * w / 2 * 1, b[1] + py * w / 2), (b[0] - px * w / 2, b[1] - py * w / 2)]
        h = self.msp.add_hatch(color=7, dxfattribs={"layer": "08-FINA"})
        h.set_solid_fill(color=7)
        h.paths.add_polyline_path(pts, is_closed=True)

    # ------------------------------------------------------------ soldadura (ISO 2553)
    def simbolo_soldadura(self, flecha, codo, lado=1, todo_alrededor=True, proceso="131", a=None):
        m = self.msp
        L_ref = 16.0
        m.add_line(codo, flecha, dxfattribs={"layer": "12-SOLDADURA"})
        dx, dy = flecha[0] - codo[0], flecha[1] - codo[1]
        LL = math.hypot(dx, dy)
        self._flecha(flecha, (dx / LL, dy / LL))
        end = (codo[0] + lado * L_ref, codo[1])
        m.add_line(codo, end, dxfattribs={"layer": "12-SOLDADURA"})
        # línea de identificación (trazos) — sistema A
        m.add_line((codo[0], codo[1] + 1.5), (end[0], end[1] + 1.5),
                   dxfattribs={"layer": "12-SOLDADURA", "linetype": "ISO02-TRAZOS"})
        # símbolo de filete del lado de la flecha (bajo la línea de referencia llena)
        xs = codo[0] + lado * 5
        m.add_lwpolyline([(xs, codo[1]), (xs, codo[1] - 3.5), (xs + lado * 3.5, codo[1])], close=True,
                         dxfattribs={"layer": "12-SOLDADURA"})
        if a:
            self.texto(a, (xs - lado * 0.8, codo[1] - 1.8), 2.5,
                       A.MIDDLE_RIGHT if lado > 0 else A.MIDDLE_LEFT, "12-SOLDADURA")
        if todo_alrededor:
            m.add_circle(codo, 1.5, dxfattribs={"layer": "12-SOLDADURA"})
        # cola con número de proceso ISO 4063
        m.add_line(end, (end[0] + lado * 2.5, end[1] + 2.5), dxfattribs={"layer": "12-SOLDADURA"})
        m.add_line(end, (end[0] + lado * 2.5, end[1] - 2.5), dxfattribs={"layer": "12-SOLDADURA"})
        self.texto(proceso, (end[0] + lado * 3.5, end[1]), 2.5,
                   A.MIDDLE_LEFT if lado > 0 else A.MIDDLE_RIGHT, "12-SOLDADURA")

    def nota_referencia(self, texto, punto, codo, h=2.5):
        m = self.msp
        m.add_line(punto, codo, dxfattribs={"layer": "08-FINA"})
        dx, dy = punto[0] - codo[0], punto[1] - codo[1]
        L = math.hypot(dx, dy) or 1
        self._flecha(punto, (dx / L, dy / L), 2.5, 0.8)
        lado = 1 if codo[0] >= punto[0] else -1
        w = len(texto) * h * 0.72
        m.add_line(codo, (codo[0] + lado * w, codo[1]), dxfattribs={"layer": "08-FINA"})
        self.texto(texto, (codo[0] + lado * w / 2, codo[1] + 0.8), h, A.BOTTOM_CENTER)


# ------------------------------------------------------------------ recortes
def recortar_circulo(pls, c, r):
    circ = sg.Point(c).buffer(r, resolution=64)
    out = []
    for pl in pls:
        if len(pl) < 2:
            continue
        ls = sg.LineString(pl)
        if not ls.intersects(circ):
            continue
        g = ls.intersection(circ)
        for gg in (g.geoms if hasattr(g, "geoms") else [g]):
            if gg.geom_type == "LineString" and len(gg.coords) >= 2:
                out.append(list(gg.coords))
    return out


def transformar(pls, c, s, destino):
    return [[(destino[0] + (x - c[0]) * s, destino[1] + (y - c[1]) * s) for x, y in pl] for pl in pls]


def transformar_poly(poly, c, s, destino):
    from shapely import affinity
    p = affinity.translate(poly, -c[0], -c[1])
    p = affinity.scale(p, s, s, origin=(0, 0))
    return affinity.translate(p, destino[0], destino[1])


def ancho_medio(poly):
    per = poly.length
    return 2 * poly.area / per if per > 0 else 0
