"""Señalética de puestos de incendio y marcado de extintores FLAMA (láminas A3
con rótulo IRAM 4508), según IRAM 3517-2:2020 (capítulos 5, 7, 8 y 9).

  SEN-01  Chapas baliza verticales 350 × 870 y 260 × 870 (7.2.5, figura 3) y
          esquema de instalación del puesto (6.2.14, 7.3).
  SEN-02  Cartel tridimensional de señalización en altura (7.3, figura 5).
  SEN-03  Símbolos de tipos de fuego: letra y pictograma (7.2.2, figura 1).
  SEN-04  Etiquetas: control (8.3.3, figura 7), "fuera de servicio" (figura 8),
          oblea de servicio (9.4.14), numeración (7.2.3, figura 2), rótulo de
          manguera (9.7.1.4).
  SEN-05  Sistema de pictogramas de NFPA 10 (Anexo B), referencia internacional.
  SEN-06  Extintor de reserva (5.3) y sustituto (9.4.5); placa de instrucciones.
  SEN-07  Chapas baliza horizontales o de piso (7.2.6, figura 4) y de baldes
          (7.5, figura 6); balde (6.2.19).
  SEN-08  Marbete indicador (9.6, figura 9, tabla 4) y traba/precinto (9.4.13).

Colores según IRAM-DEF D 1054 (7.2.1, 7.2.2); los valores RGB son sólo para la
presentación en pantalla y PDF.
"""

import math
import shapely.geometry as sg
from shapely import affinity

from .lamina import Hoja, nuevo_doc, A
from .planos import FECHA, DIBUJO, _tabla
from .catalogo import MODELOS

# colores IRAM-DEF D 1054 (aproximación RGB para pantalla)
ROJO = (200, 30, 45)       # rojo 03-1-050
VERDE = (0, 145, 70)       # verde 01-1-150
AZUL = (0, 150, 215)       # azul 08-1-070
AMARILLO = (255, 222, 0)   # amarillo 05-1-040
NEGRO = (25, 25, 25)
BLANCO = (255, 255, 255)
FOTO = (205, 235, 90)      # borde fotoluminiscente
CELESTE = (120, 195, 235)
COLOR_CLASE = {"A": VERDE, "B": ROJO, "C": AZUL, "D": AMARILLO, "K": NEGRO}
CODIGO_COLOR = {"A": "verde 01-1-150", "B": "rojo 03-1-050", "C": "azul 08-1-070", "D": "amarillo 05-1-040",
                "K": "negro"}


def _hoja(codigo, titulo, sub, escala, fmt="A3", tipo="Plano de señalética"):
    doc = nuevo_doc()
    ds = doc.dimstyles.get("FLAMA-IRAM")  # cotas en negro: la lámina se imprime en color
    ds.dxf.dimclrd = ds.dxf.dimclre = ds.dxf.dimclrt = 7
    h = Hoja(doc, fmt)
    h.formato()
    h.rotulo(dict(titulo=titulo, subtitulo=sub, codigo=codigo, hoja=1, hojas=1, escala=escala,
                  material="Ver notas", edicion="1", fecha=FECHA, dibujo=DIBUJO, reviso="", aprobo="",
                  tipo_doc=tipo, empresa="FLAMA S.A."))
    return doc, h


def _sin_huecos(g):
    """Parte un polígono con huecos en franjas verticales sin huecos (el render de
    PDF no respeta las islas de los sombreados sólidos)."""
    if not g.interiors:
        return [g]
    x0, y0, x1, y1 = g.bounds
    xs = sorted({x0, x1} | {v for it in g.interiors for v in (sg.Polygon(it).bounds[0], sg.Polygon(it).bounds[2])})
    out = []
    for a, b in zip(xs[:-1], xs[1:]):
        q = g.intersection(sg.box(a, y0 - 1, b, y1 + 1))
        for p in (q.geoms if hasattr(q, "geoms") else [q]):
            if p.geom_type == "Polygon" and not p.is_empty and p.area > 1e-6:
                out.extend(_sin_huecos(p) if p.interiors else [p])
    return out


def _relleno(h, poly, rgb, capa="05-RAYADO"):
    geoms = poly.geoms if hasattr(poly, "geoms") else [poly]
    for g0 in geoms:
        if g0.is_empty or g0.geom_type != "Polygon":
            continue
        for g in _sin_huecos(g0):
            ht = h.msp.add_hatch(dxfattribs={"layer": capa})
            ht.set_solid_fill(rgb=rgb)
            ht.paths.add_polyline_path(list(g.exterior.coords)[:-1], is_closed=True, flags=1)


def _contorno(h, poly, capa="01-VISIBLE"):
    geoms = poly.geoms if hasattr(poly, "geoms") else [poly]
    for g in geoms:
        if g.is_empty or g.geom_type != "Polygon":
            continue
        h.msp.add_lwpolyline(list(g.exterior.coords), close=True, dxfattribs={"layer": capa})
        for it in g.interiors:
            h.msp.add_lwpolyline(list(it.coords), close=True, dxfattribs={"layer": capa})


def _texto_color(h, s, p, alt, rgb, al=A.MIDDLE_CENTER):
    t = h.texto(s, p, alt, al)
    t.rgb = rgb
    return t


def _notas(h, notas, y, x=None, paso=4.6):
    x = h.fx0 + 5 if x is None else x
    for i, t in enumerate(notas):
        h.texto(t, (x, y - paso * i), 2.5 if i else 3.5)


# ------------------------------------------------------------------ símbolos (figura 1)
def simbolo_iram(h, letra, c, alto):
    """Símbolo de tipo de fuego de IRAM 3517-2:2020 figura 1: forma de contorno
    de espesor e con la letra (altura 6e) en su interior, del color de la clase.
    `alto`: altura total en mm de papel (la norma fija un mínimo de 12 mm)."""
    cx, cy = c
    rgb = COLOR_CLASE[letra]
    if letra == "A":
        e = alto / 11.0
        L = alto * 2 / math.sqrt(3)
        ext = sg.Polygon([(cx - L / 2, cy - alto / 2), (cx + L / 2, cy - alto / 2), (cx, cy + alto / 2)])
        dy_letra = -alto * 0.17
    elif letra == "B":
        e = alto / 10.0
        ext = sg.box(cx - alto / 2, cy - alto / 2, cx + alto / 2, cy + alto / 2)
        dy_letra = 0
    elif letra == "C":
        e = alto / 14.0
        ext = sg.Point(cx, cy).buffer(alto / 2, 72)
        dy_letra = 0
    elif letra == "D":
        e = alto / 12.0
        r = alto / 2
        pts = []
        for i in range(10):
            ang = math.pi / 2 + i * math.pi / 5
            rr = r if i % 2 == 0 else r * 0.55
            pts.append((cx + rr * math.cos(ang), cy - r * 0.1 + rr * math.sin(ang)))
        ext = sg.Polygon(pts)
        dy_letra = -r * 0.12
    else:  # K
        e = alto / 11.0
        r = alto / 2
        ext = sg.Polygon([(cx + r * math.cos(math.radians(60 * i)), cy + r * math.sin(math.radians(60 * i)))
                          for i in range(6)])
        dy_letra = 0
    anillo = ext.difference(ext.buffer(-e, join_style=2))
    _relleno(h, anillo, rgb)
    _texto_color(h, letra, (cx, cy + dy_letra), 6 * e * (0.8 if letra in "AD" else 1.0), rgb)
    return ext, e


def _fuego(u, cx, cy, esc=1.0):
    k = u * esc
    return sg.Polygon([(cx - 1.2 * k, cy), (cx + 1.2 * k, cy), (cx + 1.4 * k, cy + 1.6 * k), (cx + 0.7 * k, cy + 3.0 * k),
                       (cx + 0.5 * k, cy + 1.8 * k), (cx, cy + 3.6 * k), (cx - 0.5 * k, cy + 2.0 * k),
                       (cx - 0.8 * k, cy + 2.6 * k), (cx - 1.4 * k, cy + 1.4 * k)])


def icono_fuego(clase, c, lado):
    """Figura blanca del pictograma de cada tipo de fuego (figura 1, esquemática):
    A cesto y leños, B recipiente derramando, C enchufe, D perfil metálico, K sartén."""
    cx, cy = c
    u = lado / 10
    b = cy - 3.4 * u
    if clase == "A":
        obj = sg.Polygon([(cx - 3.8 * u, b), (cx - 0.8 * u, b), (cx - 0.5 * u, b + 4.2 * u), (cx - 4.1 * u, b + 4.2 * u)])
        obj = obj.union(sg.box(cx - 4.3 * u, b + 4.2 * u, cx - 0.3 * u, b + 4.7 * u))
        lena = sg.LineString([(cx - 0.2 * u, b + 0.4 * u), (cx + 3.8 * u, b + 0.4 * u)]).buffer(0.4 * u)
        f = _fuego(u, cx + 1.8 * u, b + 0.8 * u, 1.2).union(_fuego(u, cx - 2.3 * u, b + 4.7 * u, 0.8))
        return obj.union(lena).union(f)
    if clase == "B":
        bid = affinity.rotate(sg.box(cx - 4.2 * u, b + 1.5 * u, cx - 1.2 * u, b + 5.5 * u), -25, origin=(cx - 2.7 * u, b + 3.5 * u))
        charco = sg.box(cx - 2.0 * u, b, cx + 3.8 * u, b + 0.5 * u)
        f = _fuego(u, cx + 1.8 * u, b + 0.5 * u, 1.3)
        return bid.union(charco).union(f)
    if clase == "C":
        ench = sg.box(cx - 3.6 * u, b + 2.4 * u, cx - 1.0 * u, b + 4.4 * u)
        pat = sg.box(cx - 1.0 * u, b + 2.8 * u, cx + 0.2 * u, b + 3.1 * u).union(
            sg.box(cx - 1.0 * u, b + 3.7 * u, cx + 0.2 * u, b + 4.0 * u))
        cable = sg.LineString([(cx - 3.6 * u, b + 3.4 * u), (cx - 4.4 * u, b + 3.4 * u), (cx - 4.4 * u, b)]).buffer(0.3 * u)
        f = _fuego(u, cx + 2.2 * u, b, 1.3)
        return ench.union(pat).union(cable).union(f)
    if clase == "D":
        viga = sg.box(cx - 4.0 * u, b, cx + 4.0 * u, b + 0.6 * u).union(
            sg.box(cx - 0.4 * u, b + 0.6 * u, cx + 0.4 * u, b + 2.6 * u)).union(
            sg.box(cx - 4.0 * u, b + 2.6 * u, cx + 4.0 * u, b + 3.2 * u))
        f = _fuego(u, cx, b + 3.2 * u, 1.2)
        return viga.union(f)
    sarten = sg.box(cx - 3.0 * u, b, cx + 2.0 * u, b + 1.0 * u).union(
        sg.box(cx + 2.0 * u, b + 0.4 * u, cx + 4.6 * u, b + 0.8 * u))
    f = _fuego(u, cx - 0.5 * u, b + 1.0 * u, 1.4)
    return sarten.union(f)


def pictograma_iram(h, clase, c, lado):
    """Pictograma de tipo de fuego: cuadrado del color de la clase con figura blanca."""
    cx, cy = c
    fondo = sg.box(cx - lado / 2, cy - lado / 2, cx + lado / 2, cy + lado / 2).buffer(-lado * 0.06).buffer(lado * 0.06)
    _relleno(h, fondo, COLOR_CLASE[clase])
    _relleno(h, icono_fuego(clase, c, lado).intersection(fondo.buffer(-lado * 0.04)), BLANCO)
    return fondo


def caja_tipos_fuego(h, x0, y0, lado, clases):
    """Recuadro de 'tipos de fuego' de la chapa baliza: letra y pictograma de
    cada clase (7.2.2: doble indicación)."""
    caja = sg.box(x0, y0, x0 + lado, y0 + lado)
    _relleno(h, caja, BLANCO)
    _contorno(h, caja, "08-FINA")
    n = len(clases)
    paso = lado / n
    t = min(paso * 0.72, lado * 0.36)
    for i, L in enumerate(clases):
        cx = x0 + paso * (i + 0.5)
        simbolo_iram(h, L, (cx, y0 + lado * 0.73), t * 0.9)
        pictograma_iram(h, L, (cx, y0 + lado * 0.28), t)
    return caja


# ------------------------------------------------------------------ chapas baliza
def _franjas(h, zona, s, franja=100.0, ang=45):
    """Franjas rojas y blancas de `franja` mm (real) de ancho a 45° en la zona (papel)."""
    x0, y0, x1, y1 = zona.bounds
    p = 2 * franja * s * math.sqrt(2)         # período horizontal
    alto = y1 - y0
    n = int((x1 - x0 + alto) / p) + 3
    for i in range(-n, n):
        a = x0 + i * p
        banda = sg.Polygon([(a, y0), (a + p / 2, y0), (a + p / 2 + alto, y1), (a + alto, y1)])
        q = banda.intersection(zona)
        if not q.is_empty:
            _relleno(h, q, ROJO)


def _borde_foto(h, rect, s, borde=15.0):
    anillo = rect.difference(rect.buffer(-borde * s, join_style=2))
    _relleno(h, anillo, FOTO)
    _contorno(h, rect)
    _contorno(h, rect.buffer(-borde * s, join_style=2), "08-FINA")


def _campo(h, caja, texto, alt):
    _relleno(h, caja, BLANCO)
    _contorno(h, caja, "08-FINA")
    lineas = texto.split("\n")
    c = caja.centroid
    for i, t in enumerate(lineas):
        h.texto(t, (c.x, c.y + (len(lineas) - 1) * alt * 0.7 - i * alt * 1.4), alt, A.MIDDLE_CENTER)


def chapa_vertical(h, x0, y0, s, w=350.0, clases="ABC", numero="12", leyenda=None):
    """Chapa baliza vertical (figura 3): w × 870, borde fotoluminiscente de 15,
    recuadro de tipos de fuego 140 × 140 arriba a la derecha y franja inferior
    de 60 con datos del PRS y número del puesto (80)."""
    H, b = 870.0, 15.0
    rect = sg.box(x0, y0, x0 + w * s, y0 + H * s)
    ix0, iy0, ix1, iy1 = x0 + b * s, y0 + b * s, x0 + (w - b) * s, y0 + (H - b) * s
    zona = sg.box(ix0, iy0 + 60 * s, ix1, iy1)
    _relleno(h, zona, BLANCO)
    _franjas(h, zona, s)
    caja_tipos_fuego(h, ix1 - 140 * s, iy1 - 140 * s, 140 * s, clases)
    _campo(h, sg.box(ix0, iy0, ix1 - 80 * s, iy0 + 60 * s), "FLAMA S.A.\ndatos del PRS", max(1.8, 14 * s))
    _campo(h, sg.box(ix1 - 80 * s, iy0, ix1, iy0 + 60 * s), numero, max(2.5, 32 * s))
    if leyenda:
        cy = iy0 + 110 * s
        cj = sg.box(ix0 + 10 * s, cy - 22 * s, ix1 - 10 * s, cy + 22 * s)
        _campo(h, cj, leyenda, max(1.8, 16 * s))
    _borde_foto(h, rect, s)
    return rect


def chapa_horizontal(h, x0, y0, s, L=800.0, clases="ABC", numero="12"):
    """Chapa baliza horizontal o de piso (figura 4): L × L (800 ó 500)."""
    b = 15.0
    rect = sg.box(x0, y0, x0 + L * s, y0 + L * s)
    ix0, iy0, ix1, iy1 = x0 + b * s, y0 + b * s, x0 + (L - b) * s, y0 + (L - b) * s
    caja = sg.box(ix1 - 140 * s, iy0, ix1, iy0 + 140 * s)
    zona = sg.box(ix0, iy0 + 60 * s, ix1, iy1).difference(caja)
    _relleno(h, zona, BLANCO)
    _franjas(h, zona, s)
    caja_tipos_fuego(h, ix1 - 140 * s, iy0, 140 * s, clases)
    _campo(h, sg.box(ix0, iy0, ix1 - 200 * s, iy0 + 60 * s), "datos del PRS", max(1.8, 14 * s))
    _campo(h, sg.box(ix1 - 200 * s, iy0, ix1 - 140 * s, iy0 + 60 * s), numero, max(2.0, 28 * s))
    _borde_foto(h, rect, s)
    return rect


def chapa_balde(h, x0, y0, s, numero="12"):
    """Chapa baliza para baldes (figura 6): 500 × 500."""
    L, b = 500.0, 15.0
    rect = sg.box(x0, y0, x0 + L * s, y0 + L * s)
    ix0, iy0, ix1, iy1 = x0 + b * s, y0 + b * s, x0 + (L - b) * s, y0 + (L - b) * s
    zona = sg.box(ix0, iy0 + 60 * s, ix1, iy1)
    _relleno(h, zona, BLANCO)
    _franjas(h, zona, s)
    _campo(h, sg.box(ix0, iy0, ix1 - 80 * s, iy0 + 60 * s), "datos del PRS", max(1.8, 14 * s))
    _campo(h, sg.box(ix1 - 80 * s, iy0, ix1, iy0 + 60 * s), numero, max(2.0, 28 * s))
    _borde_foto(h, rect, s)
    return rect


def pictograma_extintor(h, c, alto, rgb=ROJO):
    """Extintor rojo con manguera y tobera (figura 5, esquemático)."""
    cx, cy = c
    u = alto / 10
    cuerpo = sg.box(cx - 1.4 * u, cy - 5 * u, cx + 1.4 * u, cy + 1.6 * u).union(
        sg.Point(cx, cy + 1.6 * u).buffer(1.4 * u, 40))
    valv = sg.box(cx - 0.45 * u, cy + 2.9 * u, cx + 0.45 * u, cy + 3.7 * u)
    palanca = sg.Polygon([(cx - 0.4 * u, cy + 3.7 * u), (cx + 2.8 * u, cy + 4.4 * u), (cx + 2.8 * u, cy + 4.9 * u),
                          (cx - 0.4 * u, cy + 4.3 * u)])
    mang = sg.LineString([(cx - 0.5 * u, cy + 3.4 * u), (cx - 2.4 * u, cy + 3.6 * u), (cx - 2.6 * u, cy - 1.0 * u)]).buffer(0.35 * u)
    tob = sg.Polygon([(cx - 2.9 * u, cy - 1.0 * u), (cx - 2.3 * u, cy - 1.0 * u), (cx - 2.0 * u, cy - 3.4 * u),
                      (cx - 3.2 * u, cy - 3.4 * u)])
    g = cuerpo.union(valv).union(palanca).union(mang).union(tob)
    _relleno(h, g, rgb)
    return g


# ------------------------------------------------------------------ SEN-01
def _clases(m):
    return {"FL_MAT_BC_5kg": "BC", "FL_MAT_AGUA_10l": "A", "FL_MAT_AFFF_10l": "AB", "FL_MAT_AFFF_50l": "AB",
            "FL_MAT_SALESK_6l": "AK", "FL_MAT_CO2_2kg": "BC", "FL_MAT_CO2_5kg": "BC",
            "FL_MAT_CLASED_9l": "D"}.get(m.codigo, "ABC")


def sen01():
    doc, h = _hoja("FL_SEN_01", "Chapa baliza vertical", "IRAM 3517-2:2020 - 7.2.1, 7.2.5 y figura 3", "1:5")
    s = 0.2
    y0 = h.fy0 + 84
    x1 = h.fx0 + 22
    chapa_vertical(h, x1, y0, s, 350, "ABC", "12")
    h.cota_lineal((x1, y0 + 174), (x1 + 70, y0 + 174), (x1, y0 + 182), 0, 5)
    h.cota_lineal((x1, y0), (x1, y0 + 174), (x1 - 9, y0), 90, 5)
    h.cota_lineal((x1 + 70 - 3, y0 + 174 - 3), (x1 + 70 - 3, y0 + 174 - 31), (x1 + 78, y0 + 150), 90, 5)
    h.cota_lineal((x1 + 3, y0 + 3), (x1 + 3, y0 + 15), (x1 - 5, y0 + 3), 90, 5)
    h.cota_lineal((x1 + 70 - 19, y0 + 3), (x1 + 70 - 3, y0 + 3), (x1 + 51, y0 - 6), 0, 5)
    h.cota_lineal((x1 + 67, y0 + 90), (x1 + 70, y0 + 90), (x1 + 75, y0 + 96), 0, 5)
    h.texto("CHAPA 350 × 870 (preferente)", (x1 + 35, y0 - 13), 3.5, A.MIDDLE_CENTER)
    x2 = x1 + 105
    chapa_vertical(h, x2, y0, s, 260, "BC", "13")
    h.cota_lineal((x2, y0 + 174), (x2 + 52, y0 + 174), (x2, y0 + 182), 0, 5)
    h.texto("CHAPA 260 × 870", (x2 + 26, y0 - 13), 3.5, A.MIDDLE_CENTER)
    h.texto("(sólo si no entra la de 350)", (x2 + 26, y0 - 18), 2.5, A.MIDDLE_CENTER)
    # esquema del puesto de incendio (1:20)
    si = 0.05
    xi, yi = h.fx0 + 215, h.fy0 + 84
    h.linea((xi - 5, yi), (xi + 115, yi), "01-VISIBLE")
    for i in range(15):
        h.linea((xi - 5 + 8 * i, yi), (xi - 9 + 8 * i, yi - 4), "08-FINA")
    h.linea((xi + 10, yi), (xi + 10, yi + 2700 * si), "01-VISIBLE")
    h.texto("muro", (xi + 8, yi + 2650 * si), 2.5, A.MIDDLE_RIGHT)
    # extintor de 10 kg: parte superior a 1,50 m; chapa detrás
    zc = 650.0
    chapa_vertical(h, xi + 25, yi + zc * si, si, 350, "ABC", "12")
    ex = sg.box(xi + 25 + 85 * si, yi + 850 * si, xi + 25 + 265 * si, yi + 1500 * si)
    _relleno(h, ex, ROJO)
    _contorno(h, ex)
    # cartel tridimensional a 2,0 - 2,5 m en la vertical de la baliza
    ct = sg.box(xi + 25 + 65 * si, yi + 2100 * si, xi + 25 + 285 * si, yi + 2380 * si)
    _relleno(h, ct, BLANCO)
    pictograma_extintor(h, (ct.centroid.x, ct.centroid.y + 1), 9)
    _contorno(h, ct)
    xd = xi + 25 + 350 * si
    h.cota_lineal((xd, yi), (xd, yi + 1500 * si), (xi + 62, yi), 90, 20, texto="≤ 1500")
    h.cota_lineal((xd, yi), (xd, yi + 2100 * si), (xi + 76, yi), 90, 20, texto="2000 a 2500")
    h.texto("cartel tridimensional (FL_SEN_02)", (xi + 25 + 290 * si, yi + 2440 * si), 2.5)
    h.texto("PUESTO DE INCENDIO (1:20)", (xi + 55, yi - 12), 3.5, A.MIDDLE_CENTER)
    _notas(h, ["NOTAS (IRAM 3517-2:2020)",
               "1) Franjas rojas y blancas de 100 mm a 45°; borde fotoluminiscente de 15 mm (7.2.1, 7.2.5).",
               "2) Contenido obligatorio: tipos de fuego (letra + pictograma, FL_SEN_03), número del puesto",
               "    y datos del prestador que instaló (7.2.1 a 7.2.4). Numeración del extintor: FL_SEN_04.",
               "3) Se instala siempre la de 350 mm; la de 260 mm sólo cuando el muro o la columna no lo permite.",
               "4) Extintor de hasta 20 kg: parte superior a ≤ 1,5 m; de más de 20 kg: ≤ 1,0 m; siempre",
               "    ≥ 0,10 m libre entre su base y el piso (6.2.14). Nunca en rampas ni escaleras (6.2.18).",
               "5) Cartel en altura a 2,0 m - 2,5 m sobre la vertical de la baliza (7.3). Colores s/ IRAM-DEF D 1054.",
               "6) Chapa de PAI o aluminio con tratamiento UV para exterior; colores firmes y resistentes a la limpieza.",
               "7) La norma no fija la altura de la chapa: se ubica detrás del extintor, visible por encima de él."],
           h.fy0 + 60, x=h.fx0 + 5, paso=4.4)
    return doc


# ------------------------------------------------------------------ SEN-02
def sen02():
    doc, h = _hoja("FL_SEN_02", "Cartel en altura", "IRAM 3517-2:2020 - 7.3 y figura 5 (tridimensional)", "1:2")
    s = 0.5
    W, H = 220.0, 280.0
    x0, y0 = h.fx0 + 25, h.fy1 - 30 - H * s
    cara = sg.box(x0, y0, x0 + W * s, y0 + H * s)
    _relleno(h, cara, BLANCO)
    _contorno(h, cara)
    pictograma_extintor(h, (x0 + W * s / 2, y0 + H * s * 0.58), H * s * 0.6)
    _texto_color(h, "EXTINTOR", (x0 + W * s / 2, y0 + H * s * 0.1), 12, NEGRO)
    h.cota_lineal((x0, y0 + H * s), (x0 + W * s, y0 + H * s), (x0, y0 + H * s + 8), 0, 1 / s, texto="≥ 220")
    h.cota_lineal((x0, y0), (x0, y0 + H * s), (x0 - 9, y0), 90, 1 / s, texto="≥ 280")
    h.texto("CARA (vista frontal)", (x0 + W * s / 2, y0 - 8), 3.5, A.MIDDLE_CENTER)
    # planta en V: dos caras a 90° con aletas de fijación al muro
    xp, yp = x0 + W * s + 70, y0 + 30
    a = math.radians(45)
    ap = (xp, yp)
    izq = (xp - W * s * math.cos(a), yp + W * s * math.sin(a))
    der = (xp + W * s * math.cos(a), yp + W * s * math.sin(a))
    for p in (izq, der):
        h.linea(ap, p, "01-VISIBLE")
    h.linea((izq[0] - 15, izq[1]), (der[0] + 15, der[1]), "01-VISIBLE")
    h.texto("muro o columna", ((izq[0] + der[0]) / 2, izq[1] + 4), 2.5, A.MIDDLE_CENTER)
    h.texto("PLANTA (dos caras visibles)", (xp, yp - 10), 3.5, A.MIDDLE_CENTER)
    # variante de columna: una cara por lado libre
    h.texto("En columna con caras libres: un cartel en cada cara (7.3).", (xp - 60, yp - 20), 2.5)
    # referencia ISO 7010 F001 (sólo exportación)
    xf, yf, lf = h.fx1 - 80, h.fy1 - 80, 60.0
    f = sg.box(xf, yf, xf + lf, yf + lf)
    _relleno(h, f, ROJO)
    pictograma_extintor(h, (xf + lf / 2 - 4, yf + lf / 2), lf * 0.7, BLANCO)
    _contorno(h, f)
    h.texto("ISO 7010 F001 (referencia)", (xf + lf / 2, yf - 6), 2.5, A.MIDDLE_CENTER)
    h.texto("sólo para exportación", (xf + lf / 2, yf - 10), 2.5, A.MIDDLE_CENTER)
    _notas(h, ["NOTAS",
               "1) IRAM 3517-2:2020 7.3: para la señalización en altura se usan exclusivamente los carteles de la",
               "    figura 5: palabra EXTINTOR y pictograma simultáneos; caras de 280 mm × 220 mm como mínimo.",
               "2) Instalación en muros o columnas, sobre la vertical de la baliza, a 2,0 m - 2,5 m del solado (FL_SEN_01).",
               "3) Pictograma rojo 03-1-050 (IRAM-DEF D 1054) sobre fondo blanco; texto negro. Dibujo esquemático:",
               "    para producción reproducir la figura 5 de la norma.",
               "4) Material: PAI 2 mm o acrílico, con tratamiento UV para exterior (7.2.1).",
               "5) El cartel F001 (ISO 7010) se muestra como referencia para mercados que exigen ISO; en Argentina",
               "    rige la figura 5."], h.fy0 + 58, paso=4.4)
    return doc


# ------------------------------------------------------------------ SEN-03
def sen03():
    doc, h = _hoja("FL_SEN_03", "Tipos de fuego", "IRAM 3517-2:2020 - 7.2.2 y figura 1", "2:1")
    x0, y = h.fx0 + 30, h.fy1 - 40
    h.texto("SÍMBOLO (letra en forma de contorno, espesor e)", (h.fx0 + 10, h.fy1 - 12), 3.5)
    h.texto("PICTOGRAMA", (h.fx0 + 10, y - 45), 3.5)
    for i, L in enumerate("ABCDK"):
        cx = x0 + i * 70
        ext, e = simbolo_iram(h, L, (cx, y), 30)
        h.cota_lineal((cx + 18, y - 15), (cx + 18, y + 15), (cx + 24, y - 15), 90, 0.5, texto="≥ 12")
        pictograma_iram(h, L, (cx, y - 72), 36)
        h.texto(f"Clase {L}", (cx, y - 96), 3.5, A.MIDDLE_CENTER)
        h.texto(CODIGO_COLOR[L], (cx, y - 101), 2.5, A.MIDDLE_CENTER)
    filas = [("Modelo FLAMA", "Tipos de fuego", "Norma")]
    vistos = []
    for m in MODELOS:
        k = (m.nombre.replace("Extintor ", ""), " ".join(_clases(m)), "IRAM " + m.spec.get("Norma IRAM extintor", ""))
        vistos.append(k)
    _tabla(h, h.fx0 + 5, y - 110, filas + vistos[:9], [60, 30, 30], alto=4.4, encabezado="TIPOS DE FUEGO POR MODELO")
    _tabla(h, h.fx0 + 130, y - 110, [("Modelo FLAMA", "Tipos de fuego", "Norma")] + vistos[9:], [60, 30, 30],
           alto=4.4, encabezado="(continuación)")
    _notas(h, ["NOTAS (IRAM 3517-2:2020)",
               "1) Cada tipo de fuego se indica con la letra y el pictograma simultáneamente (7.2.2).",
               "2) A triángulo equilátero, B cuadrado, C círculo, D estrella, K hexágono, con la letra adentro;",
               "    dimensiones en función de e según figura 1 y la norma de fabricación; altura mínima 12 mm.",
               "3) Colores IRAM-DEF D 1054: A verde 01-1-150, B rojo 03-1-050, C azul 08-1-070, D amarillo 05-1-040,",
               "    K negro. Los RGB de esta lámina son sólo de presentación.",
               "4) Pictogramas esquemáticos: para producción reproducir la figura 1. NFPA 10: FL_SEN_05."],
           h.fy0 + 75, x=h.fx0 + 5, paso=4.4)
    return doc


# ------------------------------------------------------------------ SEN-04
def sen04():
    doc, h = _hoja("FL_SEN_04", "Etiquetas de servicio", "IRAM 3517-2:2020 - 7.2.3, 8.3.3, 9.4.14, 9.7.1.4", "2:1")
    k = 2.0
    # 1) etiqueta de control, celeste 35 × 50 (8.3.3.1, figura 7)
    x0, y0 = h.fx0 + 12, h.fy1 - 22 - 35 * k
    et = sg.box(x0, y0, x0 + 50 * k, y0 + 35 * k)
    _relleno(h, et, CELESTE)
    _contorno(h, et)
    for i, t in enumerate(["EQUIPO CONTROLADO POR:", "..................................",
                           "FRECUENCIA: [ ] Trimestral [ ] Mensual [ ] Otra", "FECHA: ...... / ......",
                           "EL PRÓXIMO CONTROL SE DEBE REALIZAR", "CONFORME A LA FRECUENCIA INDICADA"]):
        h.texto(t, (x0 + 25 * k, y0 + (30.5 - 5.2 * i) * k), 2.5 if i != 2 else 2.2, A.MIDDLE_CENTER)
    h.cota_lineal((x0, y0 + 35 * k), (x0 + 50 * k, y0 + 35 * k), (x0, y0 + 35 * k + 7), 0, 1 / k)
    h.cota_lineal((x0 + 50 * k, y0), (x0 + 50 * k, y0 + 35 * k), (x0 + 50 * k + 7, y0), 90, 1 / k)
    h.texto("1  ETIQUETA DE CONTROL - 8.3.3 (2:1)", (x0, y0 - 7), 3.5)
    # 2) oblea de servicio (9.4.14)
    xo = x0 + 50 * k + 22
    ob = sg.Point(xo + 30, y0 + 35).buffer(30, 72)
    _relleno(h, ob, BLANCO)
    _contorno(h, ob)
    for i, t in enumerate(["PRESTADOR: ..........", "PRÓX. MANTENIMIENTO: ../..", "N° SERIE RECIPIENTE: ......",
                           "VENC. P. HIDROSTÁTICA: ../.."]):
        h.texto(t, (xo + 30, y0 + 50 - 10 * i), 2.5, A.MIDDLE_CENTER)
    h.texto("2  OBLEA - 9.4.14 (2:1)", (xo, y0 - 7), 3.5)
    # 3) numeración (figura 2): dígitos blancos sobre negro
    xn = xo + 80
    num = sg.box(xn, y0 + 20, xn + 40, y0 + 50)
    _relleno(h, num, NEGRO)
    _texto_color(h, "12", (xn + 20, y0 + 35), 18, BLANCO)
    h.texto("3  NUMERACIÓN - 7.2.3", (xn - 5, y0 - 7), 3.5)
    h.texto("2 dígitos hasta 99; 3 hasta 999; 4 más", (xn - 5, y0 + 12), 2.5)
    # 4) fuera de servicio (figura 8): 110 × 150 (120 amarillo + 30 blanco) a 1:2
    s = 0.5
    xf, yf = h.fx0 + 12, h.fy0 + 70
    am = sg.box(xf, yf + 30 * s, xf + 110 * s, yf + 150 * s)
    bl = sg.box(xf, yf, xf + 110 * s, yf + 30 * s)
    _relleno(h, am, AMARILLO)
    _contorno(h, am)
    _campo(h, bl, "datos del PRS", 2.5)
    for i, (t, a) in enumerate([("ATENCIÓN", 5.0), ("NO USAR", 5.0), ("EXTINTOR", 3.5), ("FUERA DE", 3.5),
                                ("SERVICIO", 3.5)]):
        h.texto(t, (xf + 55 * s, yf + (135 - 20 * i) * s), a, A.MIDDLE_CENTER)
    h.cota_lineal((xf, yf + 150 * s), (xf + 110 * s, yf + 150 * s), (xf, yf + 150 * s + 7), 0, 1 / s)
    h.cota_lineal((xf + 110 * s, yf), (xf + 110 * s, yf + 30 * s), (xf + 110 * s + 7, yf), 90, 1 / s)
    h.cota_lineal((xf + 110 * s, yf + 30 * s), (xf + 110 * s, yf + 150 * s), (xf + 110 * s + 7, yf), 90, 1 / s)
    h.texto("4  FUERA DE SERVICIO - figura 8 (1:2)", (xf, yf - 7), 3.5)
    # 5) rótulo de manguera 20 × 30 (9.7.1.4)
    xr, yr = xf + 90, yf + 20
    r = sg.box(xr, yr, xr + 30 * k, yr + 20 * k)
    _relleno(h, r, BLANCO)
    _contorno(h, r)
    for i, t in enumerate(["EXTINTOR N° ....", "PH: mes/año (punzonado)", "PRS: ........"]):
        h.texto(t, (xr + 15 * k, yr + (15 - 5 * i) * k), 2.2, A.MIDDLE_CENTER)
    h.cota_lineal((xr, yr + 20 * k), (xr + 30 * k, yr + 20 * k), (xr, yr + 20 * k + 7), 0, 1 / k, texto="≥ 30")
    h.cota_lineal((xr + 30 * k, yr), (xr + 30 * k, yr + 20 * k), (xr + 30 * k + 7, yr), 90, 1 / k, texto="≥ 20")
    h.texto("5  RÓTULO DE MANGUERA - 9.7.1.4 (2:1)", (xr, yr - 7), 3.5)
    h.texto("plástico, fijado sin calor", (xr, yr - 12), 2.5)
    _notas(h, ["NOTAS (IRAM 3517-2:2020)",
               "1) Etiqueta celeste 35 × 50 en cada control, en zona visible del extintor, sin superponer;",
               "    se retiran en el próximo mantenimiento; nunca en el vidrio ni en el gabinete (8.3.3.1).",
               "2) Si el control detecta anomalías: etiqueta de la figura 8 tapando las instrucciones, y se",
               "    reemplaza por un extintor de reserva (8.3.3.2). Falta de precinto = retirar de servicio.",
               "3) Oblea con: próximo mantenimiento, n° de serie del recipiente, vencimiento de la PH y PRS (9.4.14).",
               "4) Extintor y puesto numerados con etiquetas autoadhesivas; número también en la chapa (7.2.3).",
               "5) Mangueras con cierre controlado y de CO2: PH anual y rótulo 20 × 30 mm mínimo (9.7.1.4).",
               "6) Diseños de oblea y rótulo: ilustrativos; su contenido mínimo es el indicado por la norma."],
           h.fy0 + 150, x=h.fx1 - 178, paso=4.4)
    return doc


# ------------------------------------------------------------------ SEN-06 reserva / sustituto
def _silueta(h, x, y0, D, H, franja_rgb, textos, s):
    r = D / 2 * s
    cuerpo = sg.box(x - r, y0, x + r, y0 + (H - D / 2) * s).union(sg.Point(x, y0 + (H - D / 2) * s).buffer(r, 48))
    _relleno(h, cuerpo, ROJO)
    fr = sg.box(x - r, y0, x + r, y0 + 40 * s)
    _relleno(h, fr, franja_rgb)
    _contorno(h, cuerpo)
    _contorno(h, fr, "08-FINA")
    h.rect(x - 8 * s, y0 + H * s, x + 8 * s, y0 + (H + 25) * s, "01-VISIBLE")
    h.cota_lineal((x + r, y0), (x + r, y0 + 40 * s), (x + r + 8, y0), 90, 1 / s, texto="≤ 40")
    for i, t in enumerate(textos):
        h.texto(t, (x + r + 14, y0 + 40 * s + 18 - 4 * i), 2.5)
    return cuerpo


def placa_instrucciones(h, x3, y3, we=110.0, he=160.0):
    h.rect(x3, y3, x3 + we, y3 + he, "01-VISIBLE")
    cab = sg.box(x3, y3 + he - 18, x3 + we, y3 + he)
    _relleno(h, cab, ROJO)
    _texto_color(h, "EXTINTOR ABC 10 kg", (x3 + we / 2, y3 + he - 7), 5.0, BLANCO)
    _texto_color(h, "FLAMA S.A.", (x3 + we / 2, y3 + he - 14), 2.5, BLANCO)
    for i, L in enumerate("ABC"):
        simbolo_iram(h, L, (x3 + 20 + i * 35, y3 + he - 32), 16)
        pictograma_iram(h, L, (x3 + 20 + i * 35, y3 + he - 52), 18)
    pasos = ["MODO DE USO", "1. Retirar el extintor del soporte.", "2. Quitar el precinto y la traba.",
             "3. Apuntar a la base del fuego.", "4. Apretar la palanca y barrer.", "5. Recargar después de cada uso."]
    for i, t in enumerate(pasos):
        h.texto(t, (x3 + 5, y3 + he - 70 - 5.5 * i), 3.5 if i == 0 else 2.5)
    datos = ["Agente: polvo ABC IRAM 3569 - 10 kg", "Gas impulsor: nitrógeno seco", "Ps: 1,4 MPa  -  Pe: 3,5 MPa",
             "Temperatura: -20 °C a +50 °C", "IRAM 3523 - placa según IRAM 3534"]
    h.linea((x3 + 4, y3 + 38), (x3 + we - 4, y3 + 38), "08-FINA")
    for i, t in enumerate(datos):
        h.texto(t, (x3 + 5, y3 + 32 - 6 * i), 2.5)


def sen06():
    doc, h = _hoja("FL_SEN_06", "Reserva y sustituto", "IRAM 3517-2:2020 - 5.3, 9.4.5 y 9.4.15", "1:5")
    s = 0.2
    y0 = h.fy0 + 110
    _silueta(h, h.fx0 + 30, y0, 181.5, 562.5, VERDE, ["faja verde:", "EXTINTOR DE RESERVA"], s)
    _silueta(h, h.fx0 + 130, y0, 181.5, 562.5, AMARILLO,
             ["faja amarilla:", "EXTINTOR SUSTITUTO", "REEMPLAZA AL EQUIPO DE", "ESTE PUESTO EN SERVICIO",
              "datos del PRS"], s)
    h.texto("EXTINTOR DE RESERVA (5.3)", (h.fx0 + 30, y0 - 10), 3.5, A.MIDDLE_CENTER)
    h.texto("EXTINTOR SUSTITUTO (9.4.5)", (h.fx0 + 130, y0 - 10), 3.5, A.MIDDLE_CENTER)
    placa_instrucciones(h, h.fx1 - 125, h.fy1 - 22 - 160)
    h.texto("PLACA E INSTRUCCIONES - IRAM 3534 (1:1)", (h.fx1 - 125, h.fy1 - 17), 3.5)
    _notas(h, ["NOTAS (IRAM 3517-2:2020)",
               "1) Reserva: ≥ 10 % de la dotación mínima (mínimo un ABC 5 kg si da menos de uno); igual tipo si",
               "    la dotación es homogénea, ABC 5 kg si es heterogénea; opcional con menos de 5 extintores (5.3).",
               "2) Reserva: faja verde de 40 mm como máximo en el borde inferior o pollera, sin tapar los datos",
               "    grabados; la misma leyenda en un lugar visible de la chapa baliza (5.3).",
               "3) Sustituto del PRS: color de su norma (casquete puede ser de otro color) y faja amarilla de 40 mm",
               "    máx. con: EXTINTOR SUSTITUTO, que reemplaza al equipo del puesto en mantenimiento, y datos del",
               "    PRS (9.4.5). Igual clasificación y al menos igual capacidad.",
               "4) Placa según IRAM 3534; si se reemplaza en el servicio: marca del PRS y leyenda",
               "    SERVICIO DE MANTENIMIENTO (9.4.15). Instrucciones legibles y dando cara al usuario (8.3.2)."],
           h.fy0 + 62, paso=4.4)
    return doc


# ------------------------------------------------------------------ SEN-07 chapas horizontales y baldes
def sen07():
    doc, h = _hoja("FL_SEN_07", "Chapas de piso y baldes", "IRAM 3517-2:2020 - 6.2.19, 7.2.6, 7.5, figuras 4 y 6", "1:10")
    s = 0.1
    y0 = h.fy1 - 30 - 80
    x1 = h.fx0 + 20
    chapa_horizontal(h, x1, y0, s, 800, "ABC", "21")
    h.cota_lineal((x1, y0 + 80), (x1 + 80, y0 + 80), (x1, y0 + 87), 0, 10)
    h.cota_lineal((x1, y0), (x1, y0 + 80), (x1 - 8, y0), 90, 10)
    h.texto("HORIZONTAL 800 × 800", (x1 + 40, y0 - 8), 3.5, A.MIDDLE_CENTER)
    h.texto("(rodantes y pedestal)", (x1 + 40, y0 - 13), 2.5, A.MIDDLE_CENTER)
    x2 = x1 + 105
    chapa_horizontal(h, x2, y0 + 30, s, 500, "ABC", "22")
    h.cota_lineal((x2, y0 + 80), (x2 + 50, y0 + 80), (x2, y0 + 87), 0, 10)
    h.texto("HORIZONTAL 500 × 500", (x2 + 25, y0 + 22), 3.5, A.MIDDLE_CENTER)
    x3 = x2 + 80
    chapa_balde(h, x3, y0 + 30, s, "21")
    h.cota_lineal((x3, y0 + 80), (x3 + 50, y0 + 80), (x3, y0 + 87), 0, 10)
    h.texto("BALDES 500 × 500", (x3 + 25, y0 + 22), 3.5, A.MIDDLE_CENTER)
    # balde con tapa y manija (esquema, 1:5)
    xb, yb, sb = x3 + 90, y0 + 30, 0.2
    cuerpo = sg.Polygon([(xb, yb), (xb + 200 * sb, yb), (xb + 230 * sb, yb + 220 * sb), (xb - 30 * sb, yb + 220 * sb)])
    _relleno(h, cuerpo, ROJO)
    _contorno(h, cuerpo)
    tapa = sg.box(xb - 35 * sb, yb + 220 * sb, xb + 235 * sb, yb + 235 * sb)
    _relleno(h, tapa, ROJO)
    _contorno(h, tapa)
    h.msp.add_arc((xb + 100 * sb, yb + 235 * sb), 110 * sb, 20, 160, dxfattribs={"layer": "01-VISIBLE"})
    h.texto("BALDE 5 a 7 L (1:5)", (xb + 100 * sb, yb - 8), 3.5, A.MIDDLE_CENTER)
    h.texto("con tapa y manijas", (xb + 100 * sb, yb - 13), 2.5, A.MIDDLE_CENTER)
    _notas(h, ["NOTAS (IRAM 3517-2:2020)",
               "1) Chapas horizontales o de piso para extintores rodantes y soportes pedestal: 800 × 800 ó 500 × 500,",
               "    franjas rojas y blancas de 100 mm a 45° respecto de los bordes, borde fotoluminiscente de 15 mm,",
               "    datos del PRS, número del puesto (60) y tipos de fuego (140 × 140) (7.2.6, figura 4).",
               "2) Colores firmes y resistentes a la abrasión del tránsito y la limpieza; UV en exteriores (7.2.1).",
               "3) Extintores para líquidos combustibles (garajes, grupos electrógenos, etc.): puesto con dos baldes",
               "    de 5 L a 7 L, con tapa y manijas, que permitan volcar su contenido; gránulos absorbentes",
               "    reemplazados anualmente en el mantenimiento del extintor (6.2.19).",
               "4) Chapa de baldes 500 × 500 con datos del PRS (390) y número del puesto (80) (7.5, figura 6).",
               "5) Soporte pedestal: sobre chapa horizontal, eventualmente fijado al solado (3.14)."],
           h.fy0 + 90, paso=4.4)
    return doc


# ------------------------------------------------------------------ SEN-08 marbete, traba y precinto
MARBETE = [("1", "NEGRO", (25, 25, 25)), ("2", "AMARILLO", (255, 222, 0)), ("3", "CELESTE", (120, 195, 235)),
           ("4", "VERDE OSCURO", (0, 100, 50)), ("5", "AZUL", (0, 60, 160)), ("6", "LILA", (185, 140, 215)),
           ("7", "BLANCO", (255, 255, 255)), ("8", "VERDE CLARO", (150, 220, 120)), ("9", "NARANJA", (245, 140, 30)),
           ("0", "MARRÓN CLARO", (190, 140, 90))]
D_MARBETE = (33, 36, 40, 50)


def marbete_para(m):
    """Menor diámetro interior de la serie que admite el cuello (9.6.5)."""
    cuello = m.geo["cuello"][0]
    for D in D_MARBETE:
        if D - 1 >= cuello:
            return D
    return None


def sen08():
    doc, h = _hoja("FL_SEN_08", "Marbete y precinto", "IRAM 3517-2:2020 - 9.4.13, 9.6, figura 9, tabla 4", "2:1")
    k = 1.0  # planta a 1:1
    D, a, e = 40.0, 10.0, 2.0
    color = MARBETE[5][2]  # 2026: último dígito 6 -> lila
    # vista en planta del anillo plano con 4 entallas
    c = (h.fx0 + 45, h.fy1 - 50)
    anillo = sg.Point(c).buffer((D / 2 + a) * k, 96).difference(sg.Point(c).buffer(D / 2 * k, 96))
    for ang in (0, 90, 180, 270):
        ent = affinity.rotate(sg.box(c[0] + D / 2 * k - 0.1, c[1] - 1.0, c[0] + (D / 2 + a * 0.6) * k, c[1] + 1.0),
                              ang, origin=c)
        anillo = anillo.difference(ent)
    _relleno(h, anillo, color)
    _contorno(h, anillo)
    h.eje((c[0] - (D / 2 + a) * k - 4, c[1]), (c[0] + (D / 2 + a) * k + 4, c[1]))
    h.eje((c[0], c[1] - (D / 2 + a) * k - 4), (c[0], c[1] + (D / 2 + a) * k + 4))
    h.cota_lineal((c[0] - D / 2 * k, c[1] + 8), (c[0] + D / 2 * k, c[1] + 8), (c[0], c[1] + 8), 0, 1 / k,
                  prefijo="%%c")
    h.texto("PLANTA - anillo plano (1:1)", (c[0] - 30, c[1] - (D / 2 + a) * k - 9), 3.5)
    h.texto("color 2026 (dígito 6): LILA", (c[0] - 30, c[1] - (D / 2 + a) * k - 14), 2.5)
    h.nota_referencia("4 entallas radiales a 90°", (c[0] + (D / 2 + 3) * k, c[1] + 1),
                      (c[0] + 12, c[1] + (D / 2 + a) * k + 6))
    k = 2.0  # cortes a 2:1
    # cortes: plano y cónico (figura 9)
    xs, ys = h.fx0 + 92, h.fy1 - 32
    for dx in (0, (D + a) * k):
        sec = sg.box(xs + dx, ys, xs + dx + a * k, ys + e * k)
        h.rayado(sec, 45, 1.0)
        _contorno(h, sec)
    h.linea((xs + a * k, ys), (xs + (D + a) * k, ys), "08-FINA")
    h.linea((xs + a * k, ys + e * k), (xs + (D + a) * k, ys + e * k), "08-FINA")
    h.cota_lineal((xs, ys - 2), (xs + a * k, ys - 2), (xs, ys - 9), 0, 1 / k, texto="a")
    h.cota_lineal((xs + a * k, ys - 2), (xs + (D + a) * k, ys - 2), (xs, ys - 9), 0, 1 / k, texto="%%cD")
    h.cota_lineal((xs + (D + 2 * a) * k, ys), (xs + (D + 2 * a) * k, ys + e * k), (xs + (D + 2 * a) * k + 7, ys), 90,
                  1 / k, texto="e")
    h.texto("CORTE - anillo plano", (xs, ys + 12), 3.5)
    yc = ys - 45
    for sgn, x_in in ((-1, xs + 4 * k), (1, xs + (D + 4) * k)):
        base = x_in
        if sgn < 0:
            pts = [(base - 2 * k, yc), (base, yc), (base + 4 * k, yc + 10 * k), (base + 2 * k, yc + 10 * k)]
        else:
            pts = [(base, yc), (base + 2 * k, yc), (base - 2 * k, yc + 10 * k), (base - 4 * k, yc + 10 * k)]
        sec = sg.Polygon(pts)
        h.rayado(sec, 45, 1.0)
        _contorno(h, sec)
    h.cota_lineal((xs + 6 * k, yc + 10 * k), (xs + (D + 2) * k, yc + 10 * k), (xs, yc + 10 * k + 7), 0, 1 / k,
                  texto="%%cD")
    h.cota_lineal((xs + (D + 6) * k, yc), (xs + (D + 6) * k, yc + 10 * k), (xs + (D + 6) * k + 7, yc), 90, 1 / k)
    h.cota_lineal((xs + 2 * k, yc - 2), (xs + 4 * k, yc - 2), (xs + 2 * k, yc - 8), 0, 1 / k)
    h.texto("CORTE - anillo cónico", (xs, yc - 14), 3.5)
    # tabla de medidas y colores
    _tabla(h, h.fx0 + 5, h.fy0 + 170, [("Medida", "Valor (figura 9)"), ("D interior", "33 - 36 - 40 - 50 ± 1 mm"),
                                        ("a (ancho)", "10 mm (1 kg: 5 mm)"), ("e (espesor)", "2 mm (CO2: 5 a 10 mm)"),
                                        ("Cónico", "altura 10, pared 2"), ("Entallas", "4 a 90°")],
           [28, 48], alto=4.6, encabezado="MEDIDAS DEL MARBETE")
    _tabla(h, h.fx0 + 5, h.fy0 + 135, [("Año terminado en", "Color")] + [(d, n) for d, n, _ in MARBETE], [38, 38],
           alto=4.4, encabezado="COLOR ANUAL (tabla 4)")
    for i, (_, _, rgb) in enumerate(MARBETE):
        m = sg.Point(h.fx0 + 86, h.fy0 + 135 - 4.4 * (i + 2) - 2.2).buffer(1.8, 24)
        _relleno(h, m, rgb)
        _contorno(h, m, "08-FINA")
    filas = [("Modelo", "Ø cuello", "Marbete D")]
    for m in MODELOS:
        d = marbete_para(m)
        filas.append((m.codigo.replace("FL_MAT_", ""), f"{m.geo['cuello'][0]:.0f}", str(d) if d else "grabar caño"))
    _tabla(h, h.fx0 + 100, h.fy0 + 170, filas, [34, 18, 26], alto=4.2, encabezado="MARBETE POR MODELO")
    # traba y precinto (9.4.13)
    xt, yt = h.fx1 - 125, h.fy1 - 75
    h.msp.add_circle((xt + 30, yt + 25), 16, dxfattribs={"layer": "01-VISIBLE"})
    h.msp.add_circle((xt + 30, yt + 25), 16 - 3 * 0.5 * 2, dxfattribs={"layer": "01-VISIBLE"})
    h.linea((xt + 46, yt + 25), (xt + 100, yt + 25), "01-VISIBLE")
    h.linea((xt + 46, yt + 22), (xt + 100, yt + 22), "01-VISIBLE")
    h.cota_lineal((xt + 14, yt + 45), (xt + 46, yt + 45), (xt + 14, yt + 52), 0, 1 / k, texto="%%c ≥ 30 (paso)")
    h.cota_lineal((xt + 90, yt + 22), (xt + 90, yt + 25), (xt + 98, yt + 10), 90, 1 / k, texto="%%c 2,5 a 3,5")
    h.texto("TRABA (pasador de alambre) - 9.4.13", (xt, yt - 5), 3.5)
    _notas(h, ["NOTAS (IRAM 3517-2:2020)",
               "1) Marbete entre válvula y cuello en cada intervención (retiro de válvula), manuales y rodantes;",
               "    no se puede colocar ni quitar sin retirar la válvula o romperlo (9.6.1, 9.6.2).",
               "2) Material coloreado en su masa: baquelita, urea o melamina formaldehído o termoplástico (9.6.3).",
               "3) Grabado visible e indeleble: fabricante del marbete y n° de serie o lote (9.6.4).",
               "4) Rotura total antes de 20 mm de separación de extremos a 20 °C ± 5 °C (9.6.5).",
               "5) Se usa el menor D que admita el cuello; si no hay medida posible (rodantes), grabar en el caño",
               "    de pesca la fecha del servicio y de la PH (figura 9).",
               "6) Precinto con identificación del fabricante, del PRS y n° de lote; rompe entre 30 N y 90 N en",
               "    la dirección de extracción; no más de un enlazado (9.4.13)."],
           h.fy0 + 110, x=h.fx1 - 178, paso=4.4)
    return doc


# ------------------------------------------------------------------ SEN-05 pictogramas NFPA 10
def _fuego(u, cx, cy, esc=1.0):
    """Llama estilizada de base en (cx, cy)."""
    k = u * esc
    return sg.Polygon([(cx - 1.2 * k, cy), (cx + 1.2 * k, cy), (cx + 1.4 * k, cy + 1.6 * k), (cx + 0.7 * k, cy + 3.0 * k),
                       (cx + 0.5 * k, cy + 1.8 * k), (cx, cy + 3.6 * k), (cx - 0.5 * k, cy + 2.0 * k),
                       (cx - 0.8 * k, cy + 2.6 * k), (cx - 1.4 * k, cy + 1.4 * k)])


def pictograma_nfpa(h, clase, c, lado, apto=True):
    """Sistema de pictogramas de NFPA 10 (Anexo B), dibujo esquemático:
    A cesto de residuos y fuego, B bidón y fuego, C enchufe y fuego, K sartén y fuego.
    Apto: fondo azul, figuras blancas. No apto: fondo negro y barra diagonal roja."""
    cx, cy = c
    u = lado / 10
    fondo = sg.box(cx - lado / 2, cy - lado / 2, cx + lado / 2, cy + lado / 2)
    _relleno(h, fondo, AZUL if apto else NEGRO)
    _contorno(h, fondo)
    b = cy - 3.2 * u
    if clase == "A":
        obj = sg.Polygon([(cx - 3.6 * u, b), (cx - 0.4 * u, b), (cx - 0.1 * u, b + 3.4 * u), (cx - 3.9 * u, b + 3.4 * u)])
        f = _fuego(u, cx - 2.0 * u, b + 3.4 * u, 0.9).union(_fuego(u, cx + 2.2 * u, b, 1.3))
    elif clase == "B":
        obj = sg.box(cx - 3.8 * u, b, cx - 0.8 * u, b + 4.2 * u).union(
            sg.box(cx - 3.2 * u, b + 4.2 * u, cx - 2.4 * u, b + 5.0 * u)).difference(
            sg.box(cx - 3.3 * u, b + 3.0 * u, cx - 1.3 * u, b + 3.6 * u))
        f = _fuego(u, cx + 2.0 * u, b, 1.4)
    elif clase == "C":
        obj = sg.box(cx - 4.0 * u, b + 1.2 * u, cx - 1.2 * u, b + 3.2 * u).union(
            sg.box(cx - 1.2 * u, b + 1.6 * u, cx - 0.2 * u, b + 1.9 * u)).union(
            sg.box(cx - 1.2 * u, b + 2.5 * u, cx - 0.2 * u, b + 2.8 * u)).union(
            sg.LineString([(cx - 4.0 * u, b + 2.2 * u), (cx - 4.6 * u, b + 2.2 * u), (cx - 4.6 * u, b)]).buffer(0.2 * u))
        f = _fuego(u, cx + 2.2 * u, b, 1.3)
    else:  # K
        obj = sg.box(cx - 3.2 * u, b, cx + 1.8 * u, b + 1.0 * u).union(
            sg.box(cx - 4.8 * u, b + 0.4 * u, cx - 3.2 * u, b + 0.8 * u))
        f = _fuego(u, cx - 0.7 * u, b + 1.0 * u, 1.3)
    _relleno(h, obj.union(f), BLANCO)
    if not apto:
        barra = sg.LineString([(cx - lado / 2, cy + lado / 2), (cx + lado / 2, cy - lado / 2)]).buffer(0.55 * u, cap_style=2)
        _relleno(h, barra.intersection(fondo), ROJO)
    return fondo


PICTO_MODELOS = [  # (modelo, {clase: apto}) según las clases del catálogo
    ("ABC 1 a 100 kg", {"A": True, "B": True, "C": True}),
    ("BC 5 kg", {"A": False, "B": True, "C": True}),
    ("HCFC/HFC 5 kg", {"A": True, "B": True, "C": True}),
    ("Agua 10 l", {"A": True, "B": False, "C": False}),
    ("AFFF 10 l / 50 l", {"A": True, "B": True, "C": False}),
    ("Sales K 6 l", {"A": True, "B": False, "C": False, "K": True}),
    ("CO2 2 / 5 kg", {"A": False, "B": True, "C": True}),
]


def sen05():
    doc, h = _hoja("FL_SEN_05", "Pictogramas NFPA", "NFPA 10 Anexo B - sistema de pictogramas", "1:1", "A3")
    lado = 22.0
    # fila superior: significado de cada pictograma (apto / no apto)
    x0, y0 = h.fx0 + 30, h.fy1 - 30
    h.texto("SISTEMA DE PICTOGRAMAS (NFPA 10, ANEXO B)", (x0 - 10, y0 + 12), 3.5)
    signif = {"A": "Combustibles comunes", "B": "Líquidos inflamables", "C": "Equipos eléctricos", "K": "Cocinas comerciales"}
    for i, L in enumerate("ABCK"):
        cx = x0 + i * 62 + lado / 2
        pictograma_nfpa(h, L, (cx, y0 - lado / 2 - 4), lado, True)
        pictograma_nfpa(h, L, (cx + lado + 4, y0 - lado / 2 - 4), lado, False)
        h.texto(f"Clase {L}: {signif[L]}", (cx + lado / 2 + 2, y0 - lado - 10), 2.5, A.MIDDLE_CENTER)
    h.texto("azul = apto", (x0 + 4 * 62 + 5, y0 - 8), 2.5)
    h.texto("negro con barra roja = NO apto", (x0 + 4 * 62 + 5, y0 - 14), 2.5)
    h.cota_lineal((x0, y0 - lado - 18), (x0 + lado, y0 - lado - 18), (x0, y0 - lado - 24), 0, 1)
    # etiqueta de cada modelo
    y = y0 - 70
    h.texto("PICTOGRAMAS EN LA ETIQUETA DE CADA MODELO FLAMA", (x0 - 10, y + 8), 3.5)
    for j, (mod, cl) in enumerate(PICTO_MODELOS):
        col, fil = j % 2, j // 2
        xm, ym = x0 - 10 + col * 190, y - fil * 32
        h.texto(mod, (xm, ym - 14), 2.5)
        for i, L in enumerate(cl):
            pictograma_nfpa(h, L, (xm + 55 + i * (lado + 3), ym - 14), lado, cl[L])
    notas = ["NOTAS",
             "1) NFPA 10 admite dos sistemas de marcado: letra-forma (FL_SEN_03) y pictogramas (esta lámina, Anexo B).",
             "2) Los pictogramas se ubican en el frente del matafuego, visibles a 0,9 m (3 ft).",
             "3) Si el agente no es apto para una clase, se muestra el pictograma con fondo negro y barra roja;",
             "    para matafuegos de agua y espuma es obligatorio mostrar el de clase C tachado (riesgo eléctrico).",
             "4) La clase D no tiene pictograma en este sistema: se usa la estrella amarilla (FL_SEN_03).",
             "5) Dibujos esquemáticos: para producción reproducir las figuras de la edición vigente de NFPA 10.",
             "6) El rombo NFPA 704 (salud, inflamabilidad, reactividad) identifica riesgos de materiales almacenados;",
             "    no se aplica a la etiqueta del matafuego."]
    for i, t in enumerate(notas):
        h.texto(t, (h.fx0 + 5, h.fy0 + 50 - 5 * i), 2.5 if i else 3.5)
    return doc


LAMINAS = [("FL_SEN_01", sen01, "A3"), ("FL_SEN_02", sen02, "A3"), ("FL_SEN_03", sen03, "A3"),
           ("FL_SEN_04", sen04, "A3"), ("FL_SEN_05", sen05, "A3"), ("FL_SEN_06", sen06, "A3"),
           ("FL_SEN_07", sen07, "A3"), ("FL_SEN_08", sen08, "A3")]
