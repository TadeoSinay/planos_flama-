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
MARGEN_IZQ, MARGEN = 25.0, 10.0          # IRAM 4504: 25 mm a la izquierda (archivo), 10 mm en los demás
ROT_W, ROT_H = 175.0, 51.0               # IRAM 4508: rótulo de 175 × 51 mm
ESCALAS = [(1, 1), (1, 2), (1, 5), (1, 10), (1, 20)]      # IRAM 4505 / ISO 5455
AMPLIAC = [(5, 1), (2, 1), (1, 1), (1, 2), (1, 5), (1, 10)]
ALTURAS = (1.8, 2.5, 3.5, 5.0, 7.0, 10.0, 14.0, 20.0)     # IRAM 4503 / ISO 3098, letra tipo B

A = TextEntityAlignment

# Grupo de líneas IRAM 4502 (relación gruesa : media : fina = 4 : 2 : 1 -> 0,7 / 0,35 / 0,18 mm)
G, M_, F = 70, 35, 18
CAPAS = {
    # nombre: (color ACI, espesor 1/100 mm, tipo de línea, línea IRAM 4502)
    "01-VISIBLE": (7, G, "CONTINUOUS", "A continua gruesa: contornos y aristas visibles"),
    "02-OCULTA": (4, M_, "IRAM-E-TRAZOS", "E de trazos media: contornos y aristas ocultos"),
    "03-EJE": (1, F, "IRAM-F-TRAZO-PUNTO", "F trazo largo y corto fina: ejes, simetrías, trayectorias"),
    "04-COTA": (3, F, "CONTINUOUS", "B continua fina: líneas de cota y auxiliares"),
    "05-RAYADO": (8, F, "CONTINUOUS", "B continua fina: rayados IRAM 4509"),
    "06-TEXTO": (7, 25, "CONTINUOUS", "Escritura IRAM 4503 tipo B (trazo h/10)"),
    "07-RECUADRO": (7, G, "CONTINUOUS", "Recuadro IRAM 4504"),
    "08-FINA": (5, F, "CONTINUOUS", "B continua fina: referencias, fondos de rosca, contornos de detalle"),
    "09-PLANO-CORTE": (1, F, "IRAM-F-TRAZO-PUNTO", "G trazo largo y corto fina con extremos gruesos: planos de corte"),
    "10-ROTULO": (7, M_, "CONTINUOUS", "Rótulo y lista de materiales IRAM 4508"),
    "11-TEXTO-ROTULO": (7, 25, "CONTINUOUS", "Escritura del rótulo"),
    "12-SOLDADURA": (6, F, "CONTINUOUS", "Símbolos de soldadura"),
    "13-GRAFICA": (30, F, "CONTINUOUS", "Gráfica impresa representada a escala (etiqueta, sellos, señales): "
                                         "textos del objeto, no anotación del plano"),
}


ANCHO_LETRA = 0.70      # ancho medio de carácter / altura, sólo si no se puede medir con la fuente
_FUENTES = {}


def ancho_texto(s, h):
    """ancho en mm del texto s a altura h con la fuente del estilo ISO3098 (isocpeur; en esta máquina se mide con
    osifont, de proporciones ISO 3098 equivalentes) + 4 % de margen."""
    try:
        from ezdxf.fonts import fonts
        if h not in _FUENTES:
            _FUENTES[h] = fonts.make_font("isocpeur.ttf", h)
        return _FUENTES[h].text_width(s) * 1.04
    except Exception:
        return len(s) * h * ANCHO_LETRA


def partir(s, w, h, max_lin=2):
    """reparte el texto s en renglones de ancho ≤ w a altura h; si no entra en max_lin renglones, el último
    termina en «…» (se avisa)."""
    if ancho_texto(s, h) <= w:
        return [s]
    lns, cur = [], ""
    for pal in s.split():
        prueba = (cur + " " + pal).strip()
        if ancho_texto(prueba, h) <= w or not cur:
            cur = prueba
        else:
            lns.append(cur)
            cur = pal
    lns.append(cur)
    if len(lns) > max_lin:
        AVISOS.append(f"texto recortado: {s!r}")
        lns = lns[:max_lin]
        while lns[-1] and ancho_texto(lns[-1] + "…", h) > w:
            lns[-1] = lns[-1][:-1]
        lns[-1] += "…"
    return lns


AVISOS = []


# colores de la gráfica impresa (IRAM-DEF D 10-54 aproximados a RGB; NFPA 10 anexo B para pictogramas)
ROJO = (200, 30, 45)          # rojo 03-1-050: cuadrado clase B, encabezados de etiqueta
VERDE = (0, 145, 70)          # verde 01-1-150: triángulo clase A
AZUL = (0, 94, 170)           # azul 08-1-070: círculo clase C; fondo de pictograma apto (NFPA 10 anexo B)
AMARILLO = (255, 210, 0)      # amarillo 05-1-040: estrella clase D, faja de sustituto
NEGRO = (25, 25, 25)
BLANCO = (255, 255, 255)
LILA = (215, 190, 235)        # oblea PBA (fondo guilloche lila)
ROSA = (247, 200, 215)        # estampilla IRAM (fondo guilloche rosa)
CELESTE = (200, 225, 245)


def altura_norm(h):
    """altura de letra normalizada (IRAM 4503): la mayor de la serie que no supera h; mínimo 1,8 mm."""
    return max([a for a in ALTURAS if a <= h + 0.05], default=ALTURAS[0])


def escala_txt(e):
    return f"{e[0]}:{e[1]}"


def nuevo_doc():
    doc = ezdxf.new("R2018", setup=False, units=4)
    doc.header["$MEASUREMENT"] = 1
    doc.header["$LWDISPLAY"] = 1
    doc.header["$LTSCALE"] = 1.0
    doc.header["$PSLTSCALE"] = 0
    doc.header["$DIMDSEP"] = 44  # separador decimal coma
    doc.linetypes.add("IRAM-E-TRAZOS", pattern=[5.0, 4.0, -1.0],
                      description="IRAM 4502 E - trazos __ __ __")
    doc.linetypes.add("IRAM-F-TRAZO-PUNTO", pattern=[20.0, 15.0, -2.0, 1.0, -2.0],
                      description="IRAM 4502 F - trazo largo y trazo corto ____ _ ____")
    doc.linetypes.add("ISO02-TRAZOS", pattern=[4.5, 3.0, -1.5],
                      description="ISO 2553 / ISO 128 tipo 02 - línea de identificación de trazos")
    for n, (c, lw, lt, desc) in CAPAS.items():
        ly = doc.layers.add(n, color=c, lineweight=lw, linetype=lt)
        ly.description = desc
    doc.styles.add("ISO3098", font="isocpeur.ttf")
    # flecha IRAM 4513: triángulo isósceles lleno, relación base : altura = 1 : 4
    blk = doc.blocks.new("IRAM_FLECHA")
    blk.add_solid([(0, 0), (-1, 0.125), (-1, -0.125)])
    ds = doc.dimstyles.new("FLAMA-IRAM")
    ds.dxf.dimtxsty = "ISO3098"
    ds.dxf.dimtxt = 3.5
    ds.dxf.dimblk = "IRAM_FLECHA"
    ds.dxf.dimblk1 = "IRAM_FLECHA"
    ds.dxf.dimblk2 = "IRAM_FLECHA"
    ds.dxf.dimsah = 0
    ds.dxf.dimasz = 3.5
    ds.dxf.dimexe = 2.0
    ds.dxf.dimexo = 1.5
    ds.dxf.dimgap = 1.0
    ds.dxf.dimtad = 1
    ds.dxf.dimtih = 0
    ds.dxf.dimtoh = 0
    ds.dxf.dimdec = 1
    ds.dxf.dimzin = 8
    ds.dxf.dimdsep = 44
    ds.dxf.dimclrd = 256           # por capa (en láminas a color se imprimen en negro)
    ds.dxf.dimclre = 256
    ds.dxf.dimclrt = 256
    ds.dxf.dimlwd = F
    ds.dxf.dimlwe = F
    ds.dxf.dimtix = 0
    ds.dxf.dimatfit = 3
    return doc


_SUBINDICES = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")


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
        if not str(s).strip():
            return None                    # sin TEXT vacíos: AutoCAD puede rechazar el DXF («DXF read error»)
        if capa != "13-GRAFICA":
            h = altura_norm(h)             # anotación: sólo alturas de la serie IRAM 4503
        s = str(s).translate(_SUBINDICES)  # la letra ISO 3098 (isocpeur) no tiene ₂ ₃: CO2, N2, NaHCO3
        t = self.msp.add_text(s, height=h, rotation=rot,
                              dxfattribs={"layer": capa, "style": "ISO3098"})
        t.set_placement(p, align=al)
        return t

    # ------------------------------------------------------------ textos sin superposición
    def _indice(self):
        """líneas del dibujo (visibles y ocultas) y cajas de los textos ya escritos, para no pisarlos."""
        import shapely
        from ezdxf import bbox as _bbox
        n = len(self.msp)
        if getattr(self, "_idx_n", None) == n:
            return self._idx
        geo = []
        for e in self.msp:
            ly, t = e.dxf.layer, e.dxftype()
            try:
                if ly in ("01-VISIBLE", "02-OCULTA"):
                    if t == "LINE":
                        geo.append(sg.LineString([e.dxf.start[:2], e.dxf.end[:2]]))
                    elif t == "LWPOLYLINE":
                        pts = [q[:2] for q in e.get_points("xy")] + ([e.get_points("xy")[0][:2]] if e.closed else [])
                        if len(pts) > 1:
                            geo.append(sg.LineString(pts))
                    elif t in ("ARC", "CIRCLE"):
                        pts = [v[:2] for v in e.flattening(0.3)]
                        if len(pts) > 1:
                            geo.append(sg.LineString(pts))
                elif t == "TEXT":                  # también la gráfica impresa: una anotación no va encima
                    b = _bbox.extents([e], fast=True)
                    if b.has_data:
                        geo.append(sg.box(b.extmin.x, b.extmin.y, b.extmax.x, b.extmax.y))
                elif t == "HATCH":                 # rellenos de color y rayados
                    for pth in e.paths:
                        vs = getattr(pth, "vertices", None)
                        if vs and len(vs) >= 3:
                            pg = sg.Polygon([(v[0], v[1]) for v in vs])
                            if pg.is_valid and pg.area > 0.5:
                                geo.append(pg)
            except Exception:
                pass
        self._idx = (geo, shapely.STRtree(geo) if geo else None)
        self._idx_n = n
        return self._idx

    def libre(self, caja):
        geo, arbol = self._indice()
        if any(caja.intersects(c) for c in getattr(self, "_cotas", ())):
            return False                   # texto de una cota ya puesta
        return arbol is None or not any(caja.intersects(geo[i]) for i in arbol.query(caja))

    def texto_libre(self, s, cands, h=3.5, al=A.MIDDLE_CENTER, capa="06-TEXTO"):
        """escribe s en el primer punto de cands donde no pisa líneas del dibujo ni otros textos (si ninguno está
        libre, en el primero)."""
        hh = altura_norm(h)
        w = ancho_texto(s, hh)
        for p in cands:
            x, y = p
            # caja real de la letra ISO 3098 (medida con ezdxf): de 0,8 h debajo a 0,5 h encima del medio
            if al == A.MIDDLE_CENTER:
                caja = sg.box(x - w / 2 - 0.6, y - hh * 0.85, x + w / 2 + 0.6, y + hh * 0.6)
            elif al == A.MIDDLE_LEFT:
                caja = sg.box(x - 0.6, y - hh * 0.85, x + w + 0.6, y + hh * 0.6)
            elif al == A.MIDDLE_RIGHT:
                caja = sg.box(x - w - 0.6, y - hh * 0.85, x + 0.6, y + hh * 0.6)
            else:
                caja = sg.box(x - 0.6, y - hh * 0.35, x + w + 0.6, y + hh * 1.1)
            if self.libre(caja):
                return self.texto(s, p, h, al, capa)
        return self.texto(s, cands[0], h, al, capa)

    def bloque_libre(self, lineas, x, ys, paso=4.6, h0=3.5, h=2.5):
        """notas de varios renglones (el primero de altura h0) en el primer punto donde ningún renglón pisa el
        dibujo ni otro texto: (x, y) para cada y de ys, o los puntos (x, y) que vengan en ys si x es None. Si no hay
        lugar libre, en el primero. Devuelve el punto elegido."""
        puntos = list(ys) if x is None else [(x, y) for y in ys]
        elegido = puntos[0]
        for x, y in puntos:
            ok = True
            for i, t in enumerate(lineas):
                hh = altura_norm(h0 if i == 0 else h)
                yy = y - paso * i
                if t.strip() and not self.libre(sg.box(x - 0.5, yy - hh * 0.35, x + ancho_texto(t, hh) + 0.5,
                                                       yy + hh * 1.1)):
                    ok = False
                    break
            if ok:
                elegido = (x, y)
                break
        for i, t in enumerate(lineas):
            self.texto(t, (elegido[0], elegido[1] - paso * i), h0 if i == 0 else h)
        return elegido

    def grafica(self, s, p, h, al=A.BOTTOM_LEFT, rot=0, rgb=None):
        """texto que forma parte del objeto dibujado (impresión de etiqueta, sello, señal) a su escala."""
        t = self.texto(s, p, h, al, "13-GRAFICA", rot)
        if t is not None and rgb is not None:
            t.rgb = rgb
        return t

    def relleno(self, poly, rgb, capa="13-GRAFICA"):
        """relleno sólido de color verdadero (gráfica impresa). poly: shapely (Multi)Polygon en mm de papel; los
        huecos se resuelven en franjas, porque el render de PDF no respeta islas en sombreados sólidos."""
        geoms = poly.geoms if hasattr(poly, "geoms") else [poly]
        for g0 in geoms:
            if g0.is_empty or g0.geom_type != "Polygon":
                continue
            partes = [g0]
            if g0.interiors:
                x0, y0, x1, y1 = g0.bounds
                xs = sorted({x0, x1} | {v for it in g0.interiors for v in (sg.Polygon(it).bounds[0],
                                                                            sg.Polygon(it).bounds[2])})
                partes = []
                for a_, b_ in zip(xs[:-1], xs[1:]):
                    q = g0.intersection(sg.box(a_, y0 - 1, b_, y1 + 1))
                    partes += [r for r in (q.geoms if hasattr(q, "geoms") else [q])
                               if r.geom_type == "Polygon" and r.area > 1e-6]
            for g in partes:
                ht = self.msp.add_hatch(dxfattribs={"layer": capa})
                ht.set_solid_fill(rgb=rgb)
                ht.paths.add_polyline_path(list(g.exterior.coords)[:-1], is_closed=True, flags=1)
                for it in g.interiors:
                    ht.paths.add_polyline_path(list(it.coords)[:-1], is_closed=True, flags=0)

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
        """Rótulo IRAM 4508 (175 × 51 mm) en el ángulo inferior derecho.
        r: dict con titulo, subtitulo, codigo, hoja, hojas, escala, material,
        edicion, fecha, dibujo, reviso, aprobo, tipo_doc, empresa, formato."""
        x0, y0 = self.fx1 - ROT_W, self.fy0
        x1, y1 = self.fx1, self.fy0 + ROT_H
        C = self._celda
        c1, c2 = x0 + 55, x0 + 125
        # ---- columna 1: firmas, escala y método, tolerancias y formato
        yF = y0 + 28
        C("", None, x0, y1 - 5, x0 + 14, y1)
        C("", "Fecha", x0 + 14, y1 - 5, x0 + 30, y1, 2.5)
        C("", "Nombre", x0 + 30, y1 - 5, c1, y1, 2.5)
        filas = [("Dibujó", r.get("fecha", ""), r.get("dibujo", "")),
                 ("Revisó", r.get("fecha_rev", ""), r.get("reviso", "")),
                 ("Aprobó", r.get("fecha_apr", ""), r.get("aprobo", ""))]
        for i, (a, fch, nom) in enumerate(filas):
            ya = y1 - 5 - 6 * (i + 1)
            C("", a, x0, ya, x0 + 14, ya + 6, 2.5, "l")
            C("", fch[:6] + fch[-2:] if len(fch) == 10 else fch, x0 + 14, ya, x0 + 30, ya + 6, 2.5)
            C("", nom, x0 + 30, ya, c1, ya + 6, 2.5)
        C("Escala", r["escala"], x0, y0 + 14, x0 + 20, yF, 5.0)
        C("Método de proyección", None, x0 + 20, y0 + 14, c1, yF)
        self.simbolo_primer_diedro(x0 + 27.5, y0 + 19.5, 2.5)
        self.texto("ISO E", (x0 + 51.5, y0 + 19.5), 2.5, A.MIDDLE_RIGHT, "11-TEXTO-ROTULO")
        C("Tolerancias generales", "ISO 2768-m", x0, y0, x0 + 33, y0 + 14, 3.5)
        C("Formato", self.fmt, x0 + 33, y0, c1, y0 + 14, 3.5)
        # ---- columna 2: propietario, denominación, tipo de documento
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
        self.texto(r.get("subtitulo", ""), ((c1 + c2) / 2, y0 + 15.5), 1.8, A.MIDDLE_CENTER, "11-TEXTO-ROTULO")
        C("Tipo de documento", r.get("tipo_doc", ""), c1, y0, c2, y0 + 12, 3.5)
        # ---- columna 3: reemplazos, material, edición, hoja, número de plano
        cm = c2 + 22
        C("Reemplaza a / Reemplazado por", r.get("reemplaza", "-"), c2, y1 - 8, x1, y1, 1.8)
        C("Material", r.get("material", ""), c2, y1 - 18, x1, y1 - 8, 2.5)
        C("Edición", r.get("edicion", "0"), c2, y0 + 23, cm, y1 - 18, 3.5)
        C("Fecha de emisión", r.get("fecha", ""), cm, y0 + 23, x1, y1 - 18, 2.5)
        C("Hoja", f"{r['hoja']} / {r['hojas']}", c2, y0 + 13, cm, y0 + 23, 3.5)
        C("Idioma", "es", cm, y0 + 13, x1, y0 + 23, 3.5)
        cod = r["codigo"]
        C("N° de plano", cod, c2, y0, x1, y0 + 13, 5.0 if len(cod) <= 11 else (3.5 if len(cod) <= 16 else 3.0))
        self.rect(x0, y0, x1, y1, "07-RECUADRO")
        return y1

    # ------------------------------------------------------------ lista de piezas
    COLS_LISTA = [("Pos.", 9), ("Cant.", 9), ("Denominación", 44), ("Código", 19),
                  ("Material", 55), ("kg", 12), ("Observ.", 27)]

    def lista_piezas(self, filas, y_base, h_fila=5.0):
        """Lista de materiales IRAM 4508: mismo ancho que el rótulo, apoyada sobre
        él, encabezado abajo y numeración creciente hacia arriba."""
        x0, x1 = self.fx1 - ROT_W, self.fx1
        cols = self.COLS_LISTA
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
        # una sola altura por columna (IRAM 4503): 2,5 si entran todas las filas, si no 1,8
        h_col = [2.5 if all(ancho_texto(str(f[j]), 2.5) <= w - 2 for f in filas) else 1.8
                 for j, (_, w) in enumerate(cols)]
        for i, f in enumerate(filas):
            yy = y_base + h_fila * (i + 1) + h_fila / 2
            for j, (val, (nom, w)) in enumerate(zip(f, cols)):
                centrado = j in (0, 1, 3, 5)
                al = A.MIDDLE_CENTER if centrado else A.MIDDLE_LEFT
                px = xs[j] + (w / 2 if centrado else 1.2)
                s = str(val)
                hh = h_col[j]
                lns = partir(s, w - 2, hh, 2 if h_fila >= 4.4 else 1)
                for k, ln in enumerate(lns):
                    # si no entra en un renglón: dos renglones de 1,8 (IRAM 4503) dentro de la fila, sin achicar la letra
                    self.texto(ln, (px, yy + (len(lns) - 1) * 1.15 - k * 2.3), hh, al, "11-TEXTO-ROTULO")
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

    def rayado(self, poly, angulo=0, esp=2.5, solido=False, capa="05-RAYADO", rgb=None):
        """poly: shapely (Multi)Polygon en coordenadas de papel. rgb: color verdadero (etiquetas en láminas a color)."""
        geoms = poly.geoms if hasattr(poly, "geoms") else [poly]
        for g in geoms:
            if g.is_empty or g.area < 1e-3:
                continue
            h = self.msp.add_hatch(color=7 if solido else 8, dxfattribs={"layer": capa})
            if rgb is not None:
                h.rgb = rgb
            if solido:
                h.set_solid_fill(color=7)
            else:
                h.set_pattern_fill("ANSI31", scale=esp / 3.175, angle=angulo)
            h.paths.add_polyline_path(list(g.exterior.coords)[:-1], is_closed=True, flags=1)
            for it in g.interiors:
                h.paths.add_polyline_path(list(it.coords)[:-1], is_closed=True, flags=0)

    # ------------------------------------------------------------ cotas
    def cota_lineal(self, p1, p2, base, ang, k, prefijo="", texto=None):
        """Cota lineal. Si su texto pisa el dibujo, un relleno u otro texto, o es más largo que la cota, se aleja la
        línea de cota de la pieza (3, 6 y 9 mm) y, si no alcanza (texto encima de un rayado, cota chica), el texto sale
        al costado sobre la prolongación de la línea de cota; si nada queda libre se deja la posición original."""
        ov = {"dimlfac": k}
        if prefijo:
            ov["dimpost"] = prefijo + "<>"
        vert = abs(ang % 180 - 90) < 1
        i = 0 if vert else 1                        # coordenada en la que se aleja la línea de cota
        ref = (p1[i] + p2[i]) / 2
        sgn = 1 if base[i] >= ref else -1
        cands = [(base, None)]
        for dd in (3.0, 6.0, 9.0):
            b2 = list(base)
            b2[i] += sgn * dd
            cands.append((tuple(b2), None))
        j = 1 - i                                   # coordenada a lo largo de la línea de cota
        lo, hi = min(p1[j], p2[j]), max(p1[j], p2[j])
        for lado in (1, -1):
            for dd in (0.0, 3.0):
                b2 = list(base)
                b2[i] += sgn * dd
                cands.append((tuple(b2), lado))     # texto al costado: se ubica con su largo medido
        primero, largo = None, 10.0
        asz = self.doc.dimstyles.get("FLAMA-IRAM").dxf.get("dimasz", 2.5)
        for b, loc in cands:
            if loc is not None:                     # centro: medio largo + flecha exterior + 1,5 de la línea auxiliar
                q = list(b)
                sep = largo / 2 + asz + 1.5
                q[j] = (hi + sep) if loc > 0 else (lo - sep)
                loc = tuple(q)
            d = self.msp.add_linear_dim(base=b, p1=p1, p2=p2, angle=ang, dimstyle="FLAMA-IRAM",
                                        override=dict(ov, dimtmove=0) if loc else ov, location=loc,
                                        text=texto if texto else "<>", dxfattribs={"layer": "04-COTA"})
            d.render()
            if primero is None:
                primero = (b, loc)
            caja = self._caja_cota(d.dimension)
            if primero == (b, loc) and caja is not None:
                largo = caja.bounds[j + 2] - caja.bounds[j] + 0.5
            # el texto entre las líneas auxiliares sólo si cabe; si es más largo que la cota, al costado
            cabe = loc is not None or caja is None or (caja.bounds[j] >= lo - 0.5 and caja.bounds[j + 2] <= hi + 0.5)
            if caja is None or (cabe and self.libre(caja)):
                if caja is not None:
                    self._cotas = getattr(self, "_cotas", []) + [caja]
                return d
            self._borrar_cota(d.dimension)
        b, loc = primero
        d = self.msp.add_linear_dim(base=b, p1=p1, p2=p2, angle=ang, dimstyle="FLAMA-IRAM",
                                    override=ov, text=texto if texto else "<>", dxfattribs={"layer": "04-COTA"})
        d.render()
        caja = self._caja_cota(d.dimension)
        if caja is not None:
            self._cotas = getattr(self, "_cotas", []) + [caja]
        return d

    @staticmethod
    def _caja_cota(dim):
        """caja del texto de la cota; ezdxf la mide sin girar, así que se gira acá (cotas verticales)."""
        from ezdxf import bbox as _bbox
        from shapely import affinity
        for v in dim.virtual_entities():
            if v.dxftype() == "MTEXT":
                b = _bbox.extents([v], fast=False)
                if b.has_data:
                    c = sg.box(b.extmin.x + 0.25, b.extmin.y + 0.25, b.extmax.x - 0.25, b.extmax.y - 0.25)
                    rot = v.dxf.get("rotation", 0.0) or 0.0
                    ins = v.dxf.insert
                    return affinity.rotate(c, rot, origin=(ins.x, ins.y)) if rot else c
        return None

    def _borrar_cota(self, dim):
        blk = dim.dxf.get("geometry")
        self.msp.delete_entity(dim)
        if blk and blk in self.doc.blocks:
            self.doc.blocks.delete_block(blk, safe=False)

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

    def _flecha(self, tip, d, L=3.5, w=0.875):  # IRAM 4513: base : altura = 1 : 4
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
        """flecha + codo + texto. Si el texto saliera del recuadro va del otro lado del punto; si pisa el dibujo u otro
        texto, el codo se corre en altura (hasta ±24 mm) al primer lugar libre."""
        m = self.msp
        w0 = len(texto) * h * 0.72
        ld = 1 if codo[0] >= punto[0] else -1
        x_fin = codo[0] + ld * w0
        if hasattr(self, "fx0") and not (self.fx0 + 2 <= x_fin <= self.fx1 - 2):
            codo = (2 * punto[0] - codo[0], codo[1])   # el texto saldría del recuadro: va del otro lado del punto
        for dy in (0, 5, -5, 10, -10, 15, -15, 20, -20, 24, -24):
            c_ = (codo[0], codo[1] + dy)
            ld = 1 if c_[0] >= punto[0] else -1
            x0_, x1_ = sorted((c_[0], c_[0] + ld * w0))
            if self.libre(sg.box(x0_ - 0.5, c_[1] + 0.8 - h * 0.4, x1_ + 0.5, c_[1] + 0.8 + h * 1.1)):
                codo = c_
                break
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
