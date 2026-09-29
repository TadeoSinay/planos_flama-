"""Señalética y accesorios de matafuegos FLAMA (láminas 2D con rótulo IRAM 4508).

  SEN-01  Chapa baliza (IRAM 10005): franjas rojas y blancas a 45° de 100 mm,
          letras de clase de fuego arriba a la derecha; esquema de instalación
          con las alturas de IRAM 10005 y NFPA 10.
  SEN-02  Cartel de ubicación de matafuego (ISO 7010 F001) y tamaños por
          distancia de observación (ISO 3864-1, h = L / Z).
  SEN-03  Símbolos de clases de fuego A, B, C, D, K (IRAM 10005 / NFPA 10).
  SEN-04  Etiqueta de control celeste, oblea de servicio, disco marbete
          (IRAM 3517-2) y etiqueta de instrucciones.
  SEN-06  Extintor de reserva y sustituto (franja inferior de 40 mm).
  SEN-05  Sistema de pictogramas de NFPA 10 (Anexo B) por modelo.

Los accesorios (soportes, gabinete) están en accesorios.py.

Los colores se dan como referencia RAL; el color de seguridad rojo es el de
IRAM 10005.
"""

import math
import shapely.geometry as sg
from shapely import affinity

from .lamina import Hoja, nuevo_doc, FORMATOS, ROT_W, ROT_H, A
from .planos import FECHA, DIBUJO, _tabla

ROJO = (175, 43, 30)       # RAL 3000 (referencia del rojo de seguridad)
BLANCO = (255, 255, 255)
VERDE = (0, 135, 81)       # RAL 6032
AZUL = (0, 83, 135)        # RAL 5005
AMARILLO = (249, 168, 0)   # RAL 1003
NEGRO = (30, 30, 30)


def _hoja(codigo, titulo, sub, escala, fmt="A3", tipo="Plano de señalética"):
    doc = nuevo_doc()
    ds = doc.dimstyles.get("FLAMA-IRAM")  # cotas en negro: la lámina se imprime en color
    ds.dxf.dimclrd = ds.dxf.dimclre = ds.dxf.dimclrt = 7
    h = Hoja(doc, fmt)
    h.formato()
    h.rotulo(dict(titulo=titulo, subtitulo=sub, codigo=codigo, hoja=1, hojas=1, escala=escala,
                  material="Ver notas", edicion="0", fecha=FECHA, dibujo=DIBUJO, reviso="", aprobo="",
                  tipo_doc=tipo, empresa="FLAMA S.A."))
    return doc, h


def _relleno(h, poly, rgb, capa="05-RAYADO"):
    geoms = poly.geoms if hasattr(poly, "geoms") else [poly]
    for g in geoms:
        if g.is_empty:
            continue
        ht = h.msp.add_hatch(dxfattribs={"layer": capa})
        ht.set_solid_fill(rgb=rgb)
        ht.paths.add_polyline_path(list(g.exterior.coords)[:-1], is_closed=True, flags=1)
        for it in g.interiors:
            ht.paths.add_polyline_path(list(it.coords)[:-1], is_closed=True, flags=0)


def _contorno(h, poly, capa="01-VISIBLE"):
    geoms = poly.geoms if hasattr(poly, "geoms") else [poly]
    for g in geoms:
        h.msp.add_lwpolyline(list(g.exterior.coords), close=True, dxfattribs={"layer": capa})
        for it in g.interiors:
            h.msp.add_lwpolyline(list(it.coords), close=True, dxfattribs={"layer": capa})


def _texto_color(h, s, p, alt, rgb, al=A.MIDDLE_CENTER):
    t = h.texto(s, p, alt, al)
    t.rgb = rgb
    return t


# ------------------------------------------------------------------ símbolos de clase
def simbolo_clase(h, letra, c, lado):
    """Símbolo de clase de fuego de lado `lado` (mm de papel) centrado en c."""
    cx, cy = c
    r = lado / 2
    if letra == "A":
        pts = [(cx - r, cy - r * 0.85), (cx + r, cy - r * 0.85), (cx, cy + r * 0.95)]
        forma, rgb = sg.Polygon(pts), VERDE
    elif letra == "B":
        forma, rgb = sg.box(cx - r, cy - r, cx + r, cy + r), ROJO
    elif letra == "C":
        forma, rgb = sg.Point(cx, cy).buffer(r, 64), AZUL
    elif letra == "D":
        pts = []
        for i in range(10):
            a = math.pi / 2 + i * math.pi / 5
            rr = r if i % 2 == 0 else r * 0.45
            pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
        forma, rgb = sg.Polygon(pts), AMARILLO
    else:  # K
        pts = [(cx + r * math.cos(math.radians(30 + 60 * i)), cy + r * math.sin(math.radians(30 + 60 * i))) for i in range(6)]
        forma, rgb = sg.Polygon(pts), NEGRO
    _relleno(h, forma, rgb)
    _contorno(h, forma)
    dy = -r * 0.12 if letra == "A" else 0
    _texto_color(h, letra, (cx, cy + dy), lado * (0.42 if letra in "AD" else 0.55), BLANCO)
    return forma


# ------------------------------------------------------------------ SEN-01 chapa baliza
FOTO = (190, 225, 70)      # fotoluminiscente (verde amarillento)


def chapa_baliza(h, x0, y0, w, alto, s, clases="ABC", franja=100.0, foto=15.0):
    """Chapa baliza de w × alto mm reales a escala s (mm papel / mm real) con
    esquina inferior izquierda en (x0, y0) del papel."""
    rect = sg.box(x0, y0, x0 + w * s, y0 + alto * s)
    paso = franja * math.sqrt(2) * s  # separación horizontal de franjas a 45°
    n = int((w + alto) * s / paso) + 3
    for i in range(-n, n):
        a = x0 + i * paso
        banda = sg.Polygon([(a, y0), (a + paso / 2, y0), (a + paso / 2 + alto * s, y0 + alto * s),
                            (a + alto * s, y0 + alto * s)])
        q = banda.intersection(rect)
        if not q.is_empty:
            _relleno(h, q, ROJO)
    if foto:
        for xa in (x0, x0 + (w - foto) * s):
            fr = sg.box(xa, y0, xa + foto * s, y0 + alto * s)
            _relleno(h, fr, FOTO)
            _contorno(h, fr, "08-FINA")
    _contorno(h, rect)
    # recuadro blanco con letras de clase, arriba a la derecha (letras rojas)
    txt = "".join(clases)
    bw = min(w - 30.0, 45.0 * len(txt) + 20.0)
    alt = min(50.0, (bw - 16.0) / (0.78 * len(txt)))
    bh = alt + 20.0
    caja = sg.box(x0 + (w - bw - 15) * s, y0 + (alto - bh - 15) * s, x0 + (w - 15) * s, y0 + (alto - 15) * s)
    _relleno(h, caja, BLANCO)
    _contorno(h, caja)
    cc = caja.centroid
    _texto_color(h, txt, (cc.x, cc.y), alt * s, ROJO)
    return rect


def sen01():
    doc, h = _hoja("FL_SEN_01", "Chapa baliza", "IRAM 10005 - franjas 45° roja/blanca 100 mm", "1:10", "A3")
    s = 0.1
    # vista frontal chapa de columna 350 × 870 y de pared 200 × 300
    x0, y0 = h.fx0 + 20, h.fy0 + 110
    r1 = chapa_baliza(h, x0, y0, 350, 870, s)
    h.cota_lineal((x0, y0 + 87), (x0 + 35, y0 + 87), (x0, y0 + 87 + 8), 0, 10)
    h.cota_lineal((x0, y0), (x0, y0 + 87), (x0 - 10, y0), 90, 10)
    h.texto("CHAPA DE COLUMNA 350 × 870", (x0 + 17.5, y0 - 8), 3.5, A.MIDDLE_CENTER)
    x1 = x0 + 80
    chapa_baliza(h, x1, y0 + 57, 200, 300, s, "ABC")
    h.cota_lineal((x1, y0 + 87), (x1 + 20, y0 + 87), (x1, y0 + 95), 0, 10)
    h.cota_lineal((x1 + 20, y0 + 57), (x1 + 20, y0 + 87), (x1 + 28, y0 + 57), 90, 10)
    h.texto("CHAPA DE PARED 200 × 300", (x1 + 10, y0 + 49), 3.5, A.MIDDLE_CENTER)
    # detalle de franjas (1:5)
    xd, yd, sd = x1 + 60, y0 + 40, 0.2
    chapa_baliza(h, xd, yd, 200, 300, sd, "ABC")
    h.texto("DETALLE (1:5)", (xd + 20, yd - 6), 3.5, A.MIDDLE_CENTER)
    h.nota_referencia("franjas a 45°, ancho 100", (xd + 8, yd + 20), (xd + 12, yd - 22))
    # esquema de instalación (1:20)
    xi, yi, si = h.fx0 + 250, h.fy0 + 110, 0.05
    h.linea((xi - 5, yi), (xi + 90, yi), "01-VISIBLE")
    for i in range(12):
        h.linea((xi - 5 + 8 * i, yi), (xi - 9 + 8 * i, yi - 4), "08-FINA")
    h.linea((xi + 20, yi), (xi + 20, yi + 2500 * si), "01-VISIBLE")  # pared
    zc = 700.0  # borde inferior de la chapa
    chapa_baliza(h, xi + 20, yi + zc * si, 350, 870, si)
    # matafuego delante de la chapa (esquemático, 10 kg): parte superior a 1,50 m máx.
    mx = xi + 20 + 175 * si
    h.rect(mx - 90 * si, yi + 850 * si, mx + 90 * si, yi + 1500 * si, "02-OCULTA")
    h.cota_lineal((mx + 90 * si, yi), (mx + 90 * si, yi + 1500 * si), (xi + 52, yi), 90, 20, texto="≤ 1500")
    h.cota_lineal((xi + 20, yi + zc * si), (xi + 20, yi + (zc + 870) * si), (xi + 5, yi), 90, 20)
    # señal tridimensional (prisma F001) a 2,0-2,5 m (rev. 2020)
    pr = sg.box(xi + 20, yi + 2100 * si, xi + 20 + 250 * si, yi + 2350 * si)
    _relleno(h, pr, ROJO)
    _contorno(h, pr)
    h.cota_lineal((xi + 20 + 250 * si, yi), (xi + 20 + 250 * si, yi + 2100 * si), (xi + 75, yi), 90, 20,
                  texto="2000 a 2500")
    h.texto("señal tridimensional", (xi + 20 + 260 * si, yi + 2230 * si), 2.5, A.MIDDLE_LEFT)
    h.texto("ESQUEMA DE INSTALACIÓN (1:20)", (xi + 40, yi - 10), 3.5, A.MIDDLE_CENTER)
    notas = [
        "NOTAS",
        "1) IRAM 10005-2: franjas inclinadas a 45°, rojas y blancas, de 100 mm; señalización según IRAM 3517-2 3.3.4.",
        "2) Matafuego delante de la chapa: parte superior a ≤ 1,50 m del piso (hasta 20 kg) y base a ≥ 10 cm del piso;",
        "    15 mm fotoluminiscentes a cada costado y datos del prestador en la chapa (IRAM 3517 rev. 2020, s/ resumen).",
        "3) Arriba a la derecha, letras de las clases de fuego del matafuego, rojas sobre fondo blanco (altura adoptada 50 mm).",
        "4) NFPA 10 §6.1.3.8: matafuego de hasta 18,14 kg (40 lb): parte superior a no más de 1,53 m (5 ft);",
        "    de más de 18,14 kg: a no más de 1,07 m (3,5 ft); separación mínima al piso 102 mm (4 in).",
        "5) Material: poliestireno de alto impacto 1,5 mm o chapa de acero 0,8 mm pintada; tinta resistente a UV.",
        "6) Color rojo de seguridad IRAM 10005 (referencia RAL 3000); blanco RAL 9016.",
    ]
    for i, t in enumerate(notas):
        h.texto(t, (h.fx0 + 5, h.fy0 + 90 - 5 * i), 2.5 if i else 3.5)
    return doc


# ------------------------------------------------------------------ SEN-02 cartel F001
def pictograma_matafuego(h, c, lado, rgb=BLANCO):
    """Pictograma simplificado de matafuego con llama (ISO 7010 F001: reproducir el
    pictograma normalizado de la norma para producción)."""
    cx, cy = c
    u = lado / 10
    cuerpo = sg.box(cx - 1.1 * u, cy - 3.6 * u, cx + 1.1 * u, cy + 1.6 * u).union(
        sg.Point(cx, cy + 1.6 * u).buffer(1.1 * u, 32))
    valv = sg.box(cx - 0.4 * u, cy + 2.6 * u, cx + 0.4 * u, cy + 3.3 * u)
    man = sg.box(cx - 0.2 * u, cy + 3.3 * u, cx + 2.2 * u, cy + 3.6 * u)
    mang = sg.LineString([(cx - 0.3 * u, cy + 3.0 * u), (cx - 2.2 * u, cy + 2.4 * u), (cx - 2.6 * u, cy)]).buffer(0.25 * u)
    llama = sg.Polygon([(cx + 2.4 * u, cy - 3.6 * u), (cx + 4.0 * u, cy - 3.6 * u), (cx + 4.1 * u, cy - 1.8 * u),
                        (cx + 3.5 * u, cy - 0.4 * u), (cx + 3.3 * u, cy - 1.6 * u), (cx + 2.9 * u, cy - 0.9 * u),
                        (cx + 2.4 * u, cy - 2.2 * u)])
    for g in (cuerpo, valv, man, mang, llama):
        _relleno(h, g, rgb)


def _cartel(h, x0, y0, w, alto, s, leyenda=None, flecha=False):
    c = sg.box(x0, y0, x0 + w * s, y0 + alto * s)
    _relleno(h, c, ROJO)
    _contorno(h, c)
    lado = min(w, alto if not leyenda else alto * 0.72) * s
    cy = y0 + alto * s - lado / 2 if leyenda else y0 + alto * s / 2
    if flecha:  # señal complementaria de dirección (flecha blanca a 45° hacia abajo-derecha)
        cx = x0 + w * s / 2
        u = lado / 10
        fl = sg.LineString([(cx - 2.5 * u, cy + 2.5 * u), (cx + 2.0 * u, cy - 2.0 * u)]).buffer(0.9 * u, cap_style=2)
        pu = sg.Polygon([(cx + 3.4 * u, cy - 3.4 * u), (cx + 3.4 * u, cy + 0.6 * u), (cx - 0.6 * u, cy - 3.4 * u)])
        _relleno(h, fl.union(pu), BLANCO)
    else:
        pictograma_matafuego(h, (x0 + w * s / 2, cy), lado * 0.8)
    if leyenda:
        _texto_color(h, leyenda, (x0 + w * s / 2, y0 + alto * s * 0.13),
                     min(alto * s * 0.09, w * s * 0.8 / (0.85 * len(leyenda))), BLANCO)
    return c


def sen02():
    doc, h = _hoja("FL_SEN_02", "Cartel F001", "ISO 7010 F001 - cuadrado rojo, pictograma blanco", "1:5", "A3")
    s = 0.2
    y0 = h.fy1 - 30 - 420 * s
    xs = [h.fx0 + 25, h.fx0 + 115, h.fx0 + 205, h.fx0 + 265]
    _cartel(h, xs[0], y0, 300, 300, s)
    h.cota_lineal((xs[0], y0 + 60), (xs[0] + 60, y0 + 60), (xs[0], y0 + 69), 0, 5)
    h.cota_lineal((xs[0], y0), (xs[0], y0 + 60), (xs[0] - 9, y0), 90, 5)
    h.texto("F001 300 × 300", (xs[0] + 30, y0 - 8), 3.5, A.MIDDLE_CENTER)
    _cartel(h, xs[1], y0, 300, 420, s, "MATAFUEGO")
    h.cota_lineal((xs[1], y0 + 84), (xs[1] + 60, y0 + 84), (xs[1], y0 + 93), 0, 5)
    h.cota_lineal((xs[1] + 60, y0), (xs[1] + 60, y0 + 84), (xs[1] + 69, y0), 90, 5)
    h.texto("F001 CON LEYENDA 300 × 420", (xs[1] + 30, y0 - 8), 3.5, A.MIDDLE_CENTER)
    _cartel(h, xs[2], y0, 300, 300, s)
    _cartel(h, xs[3], y0, 300, 300, s, flecha=True)
    h.cota_lineal((xs[2], y0 + 60), (xs[3] + 60, y0 + 60), (xs[2], y0 + 69), 0, 5)
    h.texto("F001 + FLECHA DE DIRECCIÓN", ((xs[2] + xs[3] + 60) / 2, y0 - 8), 3.5, A.MIDDLE_CENTER)
    filas = [(f"{lado} × {lado}", f"{lado * 60 / 1000:.0f}", f"{lado * 100 / 1000:.0f}")
             for lado in (150, 200, 300, 400, 600)]
    _tabla(h, h.fx1 - 150, y0 - 25, [("Lado del cartel (mm)", "Dist. máx. (m) Z=60", "Z=100")] + filas,
           [60, 50, 40], encabezado="TAMAÑO SEGÚN DISTANCIA (ISO 3864-1)")
    notas = ["NOTAS",
             "1) Señal de equipo de lucha contra incendio: cuadrado rojo con pictograma blanco (ISO 7010 F001).",
             "2) El pictograma dibujado es esquemático: para producción reproducir el original de ISO 7010.",
             "3) Tamaño: h = L / Z (ISO 3864-1). Z = 60: criterio conservador; Z = 100: iluminación normal.",
             "    Se adopta 300 × 300 mm para distancias de observación de hasta 18 m.",
             "4) Ubicar sobre el matafuego, visible desde el acceso al local; complementa a la chapa baliza (FL_SEN_01).",
             "5) Flecha de dirección: señal complementaria cuando el matafuego no es visible desde el recorrido.",
             "6) Material: PAI 1,5 mm o aluminio 1 mm; fotoluminiscente donde se requiera señalización en oscuridad.",
             "7) Rojo de seguridad IRAM 10005 (referencia RAL 3000); blanco RAL 9016."]
    for i, t in enumerate(notas):
        h.texto(t, (h.fx0 + 5, h.fy0 + 90 - 5 * i), 2.5 if i else 3.5)
    return doc


# ------------------------------------------------------------------ SEN-03 símbolos de clase
def sen03():
    doc, h = _hoja("FL_SEN_03", "Símbolos clases de fuego", "IRAM 10005 / NFPA 10 - A B C D K", "1:1", "A3")
    lado = 40.0
    x = h.fx0 + 40
    y = h.fy1 - 50
    desc = {"A": ("Triángulo verde", "Sólidos combustibles comunes (madera, papel, textiles)", VERDE),
            "B": ("Cuadrado rojo", "Líquidos y gases inflamables", ROJO),
            "C": ("Círculo azul", "Equipos eléctricos energizados", AZUL),
            "D": ("Estrella amarilla", "Metales combustibles", AMARILLO),
            "K": ("Hexágono negro", "Aceites y grasas de cocina", NEGRO)}
    for i, L in enumerate("ABCDK"):
        cx = x + i * 65
        simbolo_clase(h, L, (cx, y), lado)
        h.cota_lineal((cx - lado / 2, y - lado / 2 - 4), (cx + lado / 2, y - lado / 2 - 4), (cx, y - lado / 2 - 12), 0, 1)
        h.texto(desc[L][0], (cx, y - lado / 2 - 20), 2.5, A.MIDDLE_CENTER)
    filas = [(f"Clase {L}", desc[L][0], desc[L][1]) for L in "ABCDK"]
    y2 = _tabla(h, h.fx0 + 20, y - 60, [("Clase", "Símbolo", "Fuego")] + filas, [25, 40, 110],
                encabezado="CLASES DE FUEGO")
    modelos = [("ABC 1 a 100 kg", "A B C"), ("BC 5 kg", "B C"), ("HCFC/HFC 5 kg", "A B C (según certificación)"),
               ("Agua 10 l", "A"), ("AFFF 10 l / 50 l", "A B"), ("Sales K 6 l", "A K"), ("CO2 2 / 5 kg", "B C"),
               ("Clase D 9 l", "D")]
    _tabla(h, h.fx0 + 210, y - 60, [("Modelo FLAMA", "Símbolos en etiqueta")] + modelos, [60, 60],
           encabezado="SÍMBOLOS POR MODELO (según catálogo)")
    notas = ["NOTAS",
             "1) IRAM 10005: clase A triángulo, B cuadrado, C círculo, D estrella, con la letra en su interior.",
             "2) Colores según el sistema de NFPA 10 (A verde, B rojo, C azul, D amarillo, K negro); letra blanca.",
             "3) Tamaño mínimo en la etiqueta del matafuego: 25 mm; en chapa baliza se usan letras rojas (FL_SEN_01).",
             "4) Referencias RAL: verde 6032, rojo 3000, azul 5005, amarillo 1003, negro 9005."]
    for i, t in enumerate(notas):
        h.texto(t, (h.fx0 + 5, h.fy0 + 45 - 5 * i), 2.5 if i else 3.5)
    return doc


# ------------------------------------------------------------------ SEN-04 tarjeta de control
CELESTE = (120, 190, 235)
MARBETE = [("VERDE CLARO", (150, 220, 120)), ("NARANJA", (245, 140, 30)), ("MARRÓN CLARO", (190, 140, 90)),
           ("NEGRO", (30, 30, 30)), ("AMARILLO", (250, 215, 0)), ("CELESTE", (120, 190, 235)),
           ("VERDE OSCURO", (0, 100, 50)), ("AZUL", (0, 60, 160)), ("LILA", (180, 140, 210)),
           ("BLANCO", (255, 255, 255))]


def sen04():
    doc, h = _hoja("FL_SEN_04", "Etiquetas y marbete", "IRAM 3517-2:2005 - 3.3.6, 3.6.1, 3.10 y tabla 1", "2:1", "A3")
    k = 2.0  # escala 2:1
    # 1) etiqueta de control periódico, celeste 35 × 50 (3.3.6)
    x0, y0 = h.fx0 + 15, h.fy1 - 25 - 35 * k
    et = sg.box(x0, y0, x0 + 50 * k, y0 + 35 * k)
    _relleno(h, et, CELESTE)
    _contorno(h, et)
    lin = ["EQUIPO CONTROLADO POR:", "........................................", "FECHA: ......... / .........",
           "EL PRÓXIMO CONTROL SE DEBE REALIZAR", "ANTES DE CUMPLIRSE LOS TRES MESES", "DE LA FECHA INDICADA"]
    for i, t in enumerate(lin):
        h.texto(t, (x0 + 25 * k, y0 + (30 - 5.2 * i) * k), 1.8 * k * 0.72, A.MIDDLE_CENTER)
    h.cota_lineal((x0, y0 + 35 * k), (x0 + 50 * k, y0 + 35 * k), (x0, y0 + 35 * k + 8), 0, 1 / k)
    h.cota_lineal((x0 + 50 * k, y0), (x0 + 50 * k, y0 + 35 * k), (x0 + 50 * k + 8, y0), 90, 1 / k)
    h.texto("1  ETIQUETA DE CONTROL - 3.3.6 (2:1)", (x0, y0 - 7), 3.5)
    # 2) oblea de mantenimiento y recarga (3.6.1)
    x1 = x0 + 50 * k + 30
    ob = sg.Point(x1 + 32, y0 + 35).buffer(32, 64)
    _relleno(h, ob, BLANCO)
    _contorno(h, ob)
    cx, cy = ob.centroid.x, ob.centroid.y
    for i, t in enumerate(["RECARGADOR INSCRIPTO", "..............................", "PRÓX. MANT./RECARGA: ../..",
                           "VENC. P. HIDRÁULICA: ../..", "N° SERIE: ............"]):
        h.texto(t, (cx, cy + 20 - 10 * i), 2.5, A.MIDDLE_CENTER)
    h.texto("2  OBLEA - 3.6.1 (2:1)", (x1, y0 - 7), 3.5)
    # 3) disco marbete (3.10, figura 1): D interior 40 ó 50, 4 entallas a 90°
    x2 = x1 + 95
    k = 1.0  # disco a 1:1
    Di, De = 40.0, 60.0
    c = (x2 + De / 2 + 5, y0 + 35)
    disco = sg.Point(c).buffer(De * k / 2, 96).difference(sg.Point(c).buffer(Di * k / 2, 96))
    for ang in (0, 90, 180, 270):
        ent = affinity.rotate(sg.box(c[0] + Di * k / 2 - 0.1, c[1] - 1.2, c[0] + Di * k / 2 + 4 * k, c[1] + 1.2),
                              ang, origin=c)
        disco = disco.difference(ent)
    _relleno(h, disco, MARBETE[8][1])
    _contorno(h, disco)
    h.eje((c[0] - De * k / 2 - 4, c[1]), (c[0] + De * k / 2 + 4, c[1]))
    h.eje((c[0], c[1] - De * k / 2 - 4), (c[0], c[1] + De * k / 2 + 4))
    h.cota_lineal((c[0] - Di * k / 2, c[1]), (c[0] + Di * k / 2, c[1]), (c[0], c[1] - De / 2 - 8), 0, 1 / k,
                  texto="%%cD = 40 ó 50")
    h.nota_referencia("4 entallas radiales a 90°", (c[0] + Di * k / 2 + 3 * k, c[1] + 1),
                      (c[0] + De * k / 2 + 12, c[1] + De * k / 2))
    h.texto("3  DISCO MARBETE - 3.10 (1:1)", (x2, y0 - 7), 3.5)
    h.texto("muestra: color 2026 LILA (ver tabla)", (x2, y0 - 12), 2.5)
    # tabla de colores (tabla 1 repetida cada 10 años)
    filas = [("Año (serie desde 2008)", "Color")]
    for i, (n, _) in enumerate(MARBETE):
        filas.append((f"{2018 + i} / {2028 + i}", n))
    _tabla(h, h.fx0 + 15, y0 - 25, filas, [45, 35], alto=4.6, encabezado="COLOR ANUAL DEL DISCO (tabla 1)")
    for i, (_, rgb) in enumerate(MARBETE):
        yy = y0 - 25 - 4.6 * (i + 2) + 2.3
        m = sg.Point(h.fx0 + 102, yy).buffer(1.8, 24)
        _relleno(h, m, rgb)
        _contorno(h, m, "08-FINA")
    notas = ["NOTAS (IRAM 3517-2:2005)",
             "1) Etiqueta celeste 35 × 50 mm en cada control; se adhieren una a continuación de otra en el",
             "    costado del extintor, nunca en el gabinete ni en su vidrio (3.3.6).",
             "2) Oblea firmemente adherida: próximo mantenimiento y recarga, vencimiento de la PH, n° de",
             "    serie y responsable inscripto (3.6.1). Diseño de la oblea: ilustrativo.",
             "3) Disco de fenol formaldehído coloreado en su masa, entre válvula y cuello; no se puede retirar",
             "    sin romperlo; rotura antes de 20 mm de deformación (3.10, fig. 1). Diámetro exterior: adoptado.",
             "4) Tabla 1 terminó en 2007 con la indicación de repetir la serie: colores calculados; confirmar",
             "    el cronograma vigente (rev. 2020). Etiqueta de instrucciones: FL_SEN_06."]
    for i, t in enumerate(notas):
        h.texto(t, (h.fx0 + 135, h.fy0 + 150 - 5 * i), 2.5 if i else 3.5)
    return doc


# ------------------------------------------------------------------ SEN-06 reserva / sustituto
def _silueta(h, x, y0, D, H, franja_rgb, leyenda, s):
    r = D / 2 * s
    cuerpo = sg.box(x - r, y0, x + r, y0 + (H - D / 2) * s).union(sg.Point(x, y0 + (H - D / 2) * s).buffer(r, 48))
    _relleno(h, cuerpo, ROJO)
    fr = sg.box(x - r, y0, x + r, y0 + 40 * s)
    _relleno(h, fr, franja_rgb)
    _contorno(h, cuerpo)
    _contorno(h, fr, "08-FINA")
    h.rect(x - 8 * s, y0 + H * s, x + 8 * s, y0 + (H + 25) * s, "01-VISIBLE")
    h.cota_lineal((x + r, y0), (x + r, y0 + 40 * s), (x + r + 8, y0), 90, 1 / s)
    for i, t in enumerate(leyenda.split(" ", 1)):
        _texto_color(h, t, (x, y0 + H * s * 0.5 - 4 * i), 2.5, BLANCO)
    return cuerpo


def sen06():
    doc, h = _hoja("FL_SEN_06", "Reserva y sustituto", "Franja 40 mm (rev. 2020) y etiqueta de instrucciones",
                   "1:5", "A3")
    s = 0.2
    y0 = h.fy0 + 100
    xs = (h.fx0 + 45, h.fx0 + 135)
    _silueta(h, xs[0], y0, 181.5, 562.5, VERDE, "EXTINTOR DE RESERVA", s)
    _silueta(h, xs[1], y0, 181.5, 562.5, AMARILLO, "EXTINTOR SUSTITUTO", s)
    h.texto("EXTINTOR DE RESERVA", (xs[0], y0 - 10), 3.5, A.MIDDLE_CENTER)
    h.texto("40 mm inferiores VERDES", (xs[0], y0 - 16), 2.5, A.MIDDLE_CENTER)
    h.texto("EXTINTOR SUSTITUTO", (xs[1], y0 - 10), 3.5, A.MIDDLE_CENTER)
    h.texto("40 mm inferiores AMARILLOS", (xs[1], y0 - 16), 2.5, A.MIDDLE_CENTER)
    notas = ["NOTAS",
             "1) Reserva: se mantiene en condiciones un 10 % de la dotación para reemplazar equipos",
             "    despresurizados, usados o con anomalías (IRAM 3517 rev. 2020, según resumen publicado).",
             "2) Sustituto: el que deja el prestador mientras retira equipos para mantenimiento; misma",
             "    clasificación y potencial que el retirado (IRAM 3517-2:2005 3.4.3; franja: rev. 2020).",
             "3) Franja: pintura en polvo verde RAL 6032 / amarillo RAL 1003 (DOC-01); leyenda en vinilo.",
             "4) Confirmar colores y leyendas con el texto de la revisión 2020 (fuente secundaria)."]
    for i, t in enumerate(notas):
        h.texto(t, (h.fx0 + 5, h.fy0 + 62 - 5 * i), 2.5 if i else 3.5)
    # 4) etiqueta de identificación e instrucciones (ejemplo ABC 10 kg, esc. 1:1 reducida)
    x3, we, he = h.fx0 + 215, 110.0, 160.0
    y3 = h.fy1 - 22 - he
    h.rect(x3, y3, x3 + we, y3 + he, "01-VISIBLE")
    cab = sg.box(x3, y3 + he - 15, x3 + we, y3 + he)
    _relleno(h, cab, ROJO)
    _texto_color(h, "MATAFUEGO ABC 10 kg", (x3 + we / 2, y3 + he - 6), 4.0, BLANCO)
    _texto_color(h, "FLAMA S.A.", (x3 + we / 2, y3 + he - 12), 2.0, BLANCO)
    for i, L in enumerate("ABC"):
        simbolo_clase(h, L, (x3 + 18 + i * 26, y3 + he - 27), 16)
    pasos = ["MODO DE USO", "1. Retirar el matafuego del soporte.", "2. Quitar el precinto y el seguro.",
             "3. Apuntar a la base del fuego.", "4. Apretar la palanca, barrer en zig-zag.",
             "5. Recargar después de cada uso."]
    for i, t in enumerate(pasos):
        h.texto(t, (x3 + 4, y3 + he - 42 - 5 * i), 2.5 if i == 0 else 2.0)
    datos = ["Agente: polvo ABC (IRAM 3569)  Carga: 10 kg", "Propelente: N2  Ps: 1,4 MPa  Pe: 3,5 MPa",
             "Temperatura: -20 °C a +50 °C", "Norma IRAM 3523 - placa según IRAM 3534",
             "No apto para metales (clase D)."]
    for i, t in enumerate(datos):
        h.texto(t, (x3 + 4, y3 + 38 - 6 * i), 2.0)
    h.texto("ETIQUETA DE INSTRUCCIONES (ej. ABC 10 kg, 1:1)", (x3, y3 + he + 4), 3.5)
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
           ("FL_SEN_04", sen04, "A3"), ("FL_SEN_05", sen05, "A3"),
           ("FL_SEN_06", sen06, "A3")]
