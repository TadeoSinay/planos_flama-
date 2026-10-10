"""Esquemas de ensayo y recarga (láminas A3 con rótulo IRAM 4508).

  FL_ESQ_01  Banco de prueba hidráulica (PH) de recipientes y matafuegos.
  FL_ESQ_02  Línea de carga de polvo y presurización con nitrógeno + estanqueidad.
  FL_ESQ_03  Diagrama de flujo de recarga por tipo de agente.

Símbolos gráficos simplificados según la convención de ISO 1219-1 (válvulas,
bomba, manómetro, válvula de alivio) y bloques de proceso. Presiones y
criterios de aceptación: ver DOC-02 y DOC-03.
"""

import math

from .lamina import Hoja, nuevo_doc, A
from .planos import FECHA, DIBUJO, _tabla
from .catalogo import MODELOS

VIS, FIN, TXT = "01-VISIBLE", "08-FINA", "06-TEXTO"


def _hoja(codigo, titulo, sub):
    doc = nuevo_doc()
    h = Hoja(doc, "A3")
    h.formato()
    h.rotulo(dict(titulo=titulo, subtitulo=sub, codigo=codigo, hoja=1, hojas=1, escala="-",
                  material="-", edicion="0", fecha=FECHA, dibujo=DIBUJO, reviso="", aprobo="",
                  tipo_doc="Esquema", empresa="FLAMA S.A."))
    return doc, h


# ------------------------------------------------------------------ símbolos (centro c)
def valvula(h, c, vertical=False, rot=None):
    x, y = c
    a, b = 4.0, 2.5
    if vertical:
        pts = [(x - b, y - a), (x + b, y - a), (x - b, y + a), (x + b, y + a)]
    else:
        pts = [(x - a, y - b), (x - a, y + b), (x + a, y - b), (x + a, y + b)]
    h.msp.add_lwpolyline([pts[0], pts[1], pts[2], pts[3]], close=True, dxfattribs={"layer": VIS})


def retencion(h, c):
    x, y = c
    h.msp.add_circle((x, y), 2.0, dxfattribs={"layer": VIS})
    h.linea((x + 2.0, y - 3), (x + 2.0, y + 3), VIS)
    h.linea((x - 4, y), (x - 2, y), VIS)


def manometro(h, c, etiqueta="PI"):
    x, y = c
    h.linea((x, y), (x, y + 5), VIS)
    h.msp.add_circle((x, y + 9), 4.0, dxfattribs={"layer": VIS})
    h.linea((x - 2.5, y + 6.5), (x + 2.5, y + 11.5), VIS)
    h.texto(etiqueta, (x + 5.5, y + 9), 2.5, A.MIDDLE_LEFT)


def alivio(h, c):
    """Válvula de alivio (seguridad) tarada: cuadrado, flecha y resorte."""
    x, y = c
    h.linea((x, y), (x, y + 3), VIS)
    h.rect(x - 3.5, y + 3, x + 3.5, y + 10, VIS)
    h.linea((x, y + 4), (x, y + 9), VIS)
    h.linea((x, y + 9), (x - 1, y + 7.5), VIS)
    h.linea((x, y + 9), (x + 1, y + 7.5), VIS)
    zz = [(x + 3.5, y + 6.5)] + [(x + 4.5 + i, y + 5.5 + 2 * (i % 2)) for i in range(4)]
    h.msp.add_lwpolyline(zz, dxfattribs={"layer": VIS})


def bomba(h, c, r=6.0):
    x, y = c
    h.msp.add_circle((x, y), r, dxfattribs={"layer": VIS})
    h.msp.add_lwpolyline([(x - r * 0.3, y - r * 0.8), (x + r * 0.85, y), (x - r * 0.3, y + r * 0.8)], close=True,
                         dxfattribs={"layer": VIS})


def tanque(h, x0, y0, w, alto, rotulo):
    h.rect(x0, y0, x0 + w, y0 + alto, VIS)
    h.linea((x0 + 2, y0 + alto * 0.75), (x0 + w - 2, y0 + alto * 0.75), FIN)
    h.texto(rotulo, (x0 + w / 2, y0 + alto * 0.4), 2.5, A.MIDDLE_CENTER)


def recipiente(h, cx, y0, w, alto, rotulo, cuello=True):
    r = w / 2
    h.linea((cx - r, y0 + 3), (cx - r, y0 + alto - r), VIS)
    h.linea((cx + r, y0 + 3), (cx + r, y0 + alto - r), VIS)
    h.msp.add_arc((cx, y0 + alto - r), r, 0, 180, dxfattribs={"layer": VIS})
    h.linea((cx - r, y0 + 3), (cx - r + 3, y0), VIS)
    h.linea((cx + r, y0 + 3), (cx + r - 3, y0), VIS)
    h.linea((cx - r + 3, y0), (cx + r - 3, y0), VIS)
    if cuello:
        h.rect(cx - 2.5, y0 + alto, cx + 2.5, y0 + alto + 4, VIS)
    if rotulo:
        h.texto(rotulo, (cx, y0 + alto * 0.45), 2.5, A.MIDDLE_CENTER)
    return (cx, y0 + alto + 4)


def tubo(h, pts):
    h.msp.add_lwpolyline(pts, dxfattribs={"layer": VIS})


def caja(h, x, y, w, alto, t, hs=2.5):
    h.rect(x - w / 2, y - alto / 2, x + w / 2, y + alto / 2, VIS)
    lineas = t.split("\n")
    for i, l in enumerate(lineas):
        h.texto(l, (x, y + (len(lineas) - 1) * (hs + 1) / 2 - i * (hs + 1)), hs, A.MIDDLE_CENTER)


def rombo(h, x, y, w, alto, t, hs=2.5):
    h.msp.add_lwpolyline([(x - w / 2, y), (x, y + alto / 2), (x + w / 2, y), (x, y - alto / 2)], close=True,
                         dxfattribs={"layer": VIS})
    lineas = t.split("\n")
    for i, l in enumerate(lineas):
        h.texto(l, (x, y + (len(lineas) - 1) * (hs + 1) / 2 - i * (hs + 1)), hs, A.MIDDLE_CENTER)


def flecha(h, a, b):
    h.linea(a, b, FIN)
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    L, w = 3.0, 0.75
    p1 = (b[0] - L * math.cos(ang) + w * math.sin(ang), b[1] - L * math.sin(ang) - w * math.cos(ang))
    p2 = (b[0] - L * math.cos(ang) - w * math.sin(ang), b[1] - L * math.sin(ang) + w * math.cos(ang))
    hh = h.msp.add_hatch(dxfattribs={"layer": FIN})
    hh.set_solid_fill(color=7)
    hh.paths.add_polyline_path([b, p1, p2], is_closed=True)


def leyenda(h, x, y):
    h.texto("REFERENCIAS", (x, y), 3.5)
    items = [("valv", "Válvula de bloqueo"), ("ret", "Válvula de retención"), ("man", "Manómetro (PI)"),
             ("ali", "Válvula de alivio tarada"), ("bom", "Bomba")]
    for i, (k, t) in enumerate(items):
        yy = y - 10 - 11 * i
        c = (x + 6, yy)
        if k == "valv":
            valvula(h, c)
        elif k == "ret":
            retencion(h, c)
        elif k == "man":
            manometro(h, (x + 6, yy - 8), "")
        elif k == "ali":
            alivio(h, (x + 6, yy - 5))
        else:
            bomba(h, c, 4)
        h.texto(t, (x + 16, yy), 2.5, A.MIDDLE_LEFT)


def _notas(h, notas, y, x=None):
    x = h.fx0 + 5 if x is None else x
    for i, t in enumerate(notas):
        h.texto(t, (x, y - 4.6 * i), 2.5 if i else 3.5)


# ------------------------------------------------------------------ ESQ-01 prueba hidráulica
def esq01():
    doc, h = _hoja("FL_ESQ_01", "Banco de prueba hidráulica", "Esquema - prueba de presión con agua (PH)")
    y = h.fy1 - 75
    x = h.fx0 + 15
    tanque(h, x, y - 12, 26, 24, "AGUA")
    tubo(h, [(x + 26, y - 8), (x + 38, y - 8)])
    h.texto("filtro", (x + 40, y - 16), 2.5, A.MIDDLE_CENTER)
    h.msp.add_lwpolyline([(x + 38, y - 8), (x + 42, y - 4), (x + 46, y - 8), (x + 42, y - 12)], close=True,
                         dxfattribs={"layer": VIS})
    tubo(h, [(x + 46, y - 8), (x + 56, y - 8)])
    bomba(h, (x + 62, y - 8))
    h.texto("bomba manual o", (x + 62, y - 19), 2.5, A.MIDDLE_CENTER)
    h.texto("eléctrica", (x + 62, y - 23), 2.5, A.MIDDLE_CENTER)
    tubo(h, [(x + 68, y - 8), (x + 80, y - 8)])
    retencion(h, (x + 84, y - 8))
    tubo(h, [(x + 86, y - 8), (x + 98, y - 8)])
    valvula(h, (x + 102, y - 8))
    h.texto("V1", (x + 102, y - 2), 2.5, A.MIDDLE_CENTER)
    tubo(h, [(x + 106, y - 8), (x + 150, y - 8)])
    alivio(h, (x + 116, y - 8))
    h.texto("PSV tarada", (x + 106, y + 10), 2.5, A.MIDDLE_RIGHT)
    h.texto("a 1,1 × Pe", (x + 106, y + 6), 2.5, A.MIDDLE_RIGHT)
    manometro(h, (x + 130, y - 8), "PI-1")
    tubo(h, [(x + 150, y - 8), (x + 150, y + 22), (x + 205, y + 22), (x + 205, y + 12)])
    valvula(h, (x + 175, y + 22))
    h.texto("V2", (x + 175, y + 28), 2.5, A.MIDDLE_CENTER)
    # recipiente dentro de jaula (protección) y purga
    recipiente(h, x + 205, y - 70, 34, 78, "")
    h.texto("RECIPIENTE", (x + 205, y - 34), 2.5, A.MIDDLE_CENTER)
    h.texto("lleno de agua", (x + 205, y - 39), 2.5, A.MIDDLE_CENTER)
    h.texto("sin aire", (x + 205, y - 44), 2.5, A.MIDDLE_CENTER)
    h.msp.add_lwpolyline([(x + 180, y - 75), (x + 230, y - 75), (x + 230, y + 16), (x + 180, y + 16)], close=True,
                         dxfattribs={"layer": "02-OCULTA"})
    h.texto("JAULA / CUBA DE PROTECCIÓN", (x + 205, y - 80), 2.5, A.MIDDLE_CENTER)
    tubo(h, [(x + 150, y - 8), (x + 150, y - 30), (x + 160, y - 30)])
    valvula(h, (x + 164, y - 30))
    h.texto("V3 purga", (x + 164, y - 36), 2.5, A.MIDDLE_CENTER)
    tubo(h, [(x + 168, y - 30), (x + 172, y - 30), (x + 172, y - 42)])
    h.texto("a desagüe", (x + 172, y - 46), 2.5, A.MIDDLE_CENTER)
    # retorno al tanque desde la PSV
    tubo(h, [(x + 116, y + 13), (x + 116, y + 34), (x + 13, y + 34), (x + 13, y + 12)])
    h.texto("retorno de la PSV", (x + 60, y + 37), 2.5, A.MIDDLE_CENTER)
    leyenda(h, h.fx1 - 60, h.fy1 - 12)
    # tabla de presiones de ensayo (catálogo)
    filas = [("Modelo", "Ps", "Pe fabr.", "PH recarga", "c/ años")]
    for m in MODELOS:
        ps = float(m.spec["Presión de servicio (MPa)"].replace(",", "."))
        rec = ("IRAM 2533" if m.familia == "co2" else "4,0" if m.familia == "rodante"
               else f"{2.5 * ps:.1f}".replace(".", ","))
        anos = "2" if (m.familia == "inox" or "AFFF" in m.codigo) else "5"
        filas.append((m.codigo.replace("FL_MAT_", ""), m.spec["Presión de servicio (MPa)"],
                      m.spec["Presión de ensayo (MPa)"], rec, anos))
    _tabla(h, h.fx1 - 128, h.fy1 - 82, filas, [32, 16, 22, 36, 22], alto=4.6, hs=(2.5, 2.5),
           encabezado="PRESIONES MPa (catálogo / 3517-2:2020)")
    _notas(h, ["PROCEDIMIENTO (IRAM 3517-2:2020, 9.7.4 y 9.7.5.2)",
               "1) Quitar válvula, accesorios y partes internas; eliminar el polvo. Recipiente en jaula o tras defensa.",
               "2) Llenar con agua purgando todo el aire (V2 abierta, V3 cerrada).",
               "3) Subir hasta la presión de prueba y MANTENERLA 1 min (cerrar V1; PI-1 sin caída).",
               "4) Satisfactorio sin caída de presión, rotura, pérdidas ni deformación permanente visible; si falla,",
               "    inutilizar (9.12: 2 orificios Ø ≥ 10 mm). CO2: IRAM 2533 / 2529-1, acuñar PH mes/año (9.7.7).",
               "5) Bomba ≥ 150 % de la presión de ensayo con retención; circuito cerrado de agua, pulmón ≥ 5 L (4.4.1).",
               "6) PH = 2,5 × Ps; rodantes 4 MPa; cada 5 años (polvo, CO2, gases limpios) o 2 años (agua, AFFF, K).",
               "7) Mangueras de rodantes y CO2: PH anual, 2 × Ps (≥ 2,8 MPa) / 12 MPa. Nunca con aire o gas (9.7.4.1)."],
           h.fy0 + 95)
    return doc


# ------------------------------------------------------------------ ESQ-02 línea de carga
def esq02():
    doc, h = _hoja("FL_ESQ_02", "Línea de carga ABC", "Carga de polvo, presurización N2, estanqueidad")
    y = h.fy1 - 72
    x = h.fx0 + 12
    # estación 1: carga de polvo
    h.texto("1  CARGA DE POLVO", (x, y + 40), 3.5)
    h.msp.add_lwpolyline([(x, y + 12), (x + 30, y + 12), (x + 20, y - 5), (x + 10, y - 5)], close=True,
                         dxfattribs={"layer": VIS})
    h.texto("tolva polvo", (x + 15, y + 4), 2.5, A.MIDDLE_CENTER)
    h.texto("ABC IRAM 3569", (x + 15, y + 8), 1.8, A.MIDDLE_CENTER)
    h.rect(x + 12, y - 12, x + 18, y - 5, VIS)
    h.texto("dosificador", (x + 21, y - 9), 2.5, A.MIDDLE_LEFT)
    tubo(h, [(x + 15, y - 12), (x + 15, y - 20)])
    recipiente(h, x + 15, y - 62, 22, 38, "")
    h.rect(x, y - 68, x + 30, y - 62, VIS)
    h.texto("balanza (kg)", (x + 15, y - 72), 2.5, A.MIDDLE_CENTER)
    h.texto("secado previo del", (x + 15, y - 80), 2.5, A.MIDDLE_CENTER)
    h.texto("recipiente", (x + 15, y - 84), 2.5, A.MIDDLE_CENTER)
    flecha(h, (x + 36, y - 40), (x + 58, y - 40))
    # estación 2: colocación de válvula
    x2 = x + 64
    h.texto("2  VÁLVULA", (x2, y + 40), 3.5)
    recipiente(h, x2 + 15, y - 62, 22, 38, "")
    h.rect(x2 + 9, y - 20, x2 + 21, y - 14, VIS)
    h.texto("torque", (x2 + 15, y - 8), 2.5, A.MIDDLE_CENTER)
    h.texto("según DOC-02", (x2 + 15, y - 4), 2.5, A.MIDDLE_CENTER)
    h.texto("O-ring nuevo", (x2 + 15, y - 72), 2.5, A.MIDDLE_CENTER)
    h.texto("y sifón limpio", (x2 + 15, y - 76), 2.5, A.MIDDLE_CENTER)
    flecha(h, (x2 + 36, y - 40), (x2 + 58, y - 40))
    # estación 3: presurización N2
    x3 = x2 + 64
    h.texto("3  PRESURIZACIÓN N2", (x3, y + 40), 3.5)
    h.rect(x3, y - 62, x3 + 12, y + 8, VIS)
    h.msp.add_arc((x3 + 6, y + 8), 6, 0, 180, dxfattribs={"layer": VIS})
    h.texto("N2", (x3 + 6, y - 25), 3.5, A.MIDDLE_CENTER)
    tubo(h, [(x3 + 6, y + 14), (x3 + 6, y + 16), (x3 + 18, y + 16)])
    h.rect(x3 + 18, y + 12, x3 + 26, y + 20, VIS)
    h.linea((x3 + 18, y + 12), (x3 + 26, y + 20), VIS)
    h.texto("regulador", (x3 + 22, y + 24), 2.5, A.MIDDLE_CENTER)
    tubo(h, [(x3 + 26, y + 16), (x3 + 60, y + 16)])
    manometro(h, (x3 + 34, y + 16), "PI")
    alivio(h, (x3 + 46, y + 16))
    valvula(h, (x3 + 54, y + 16))
    tubo(h, [(x3 + 60, y + 16), (x3 + 60, y - 14)])
    h.texto("adaptador de carga", (x3 + 62, y + 2), 2.5, A.MIDDLE_LEFT)
    h.texto("por la válvula", (x3 + 62, y - 2), 2.5, A.MIDDLE_LEFT)
    recipiente(h, x3 + 60, y - 62, 22, 44, "")
    h.texto("P servicio a 20 °C", (x3 + 60, y - 72), 2.5, A.MIDDLE_CENTER)
    h.texto("(1,4 MPa ABC)", (x3 + 60, y - 76), 2.5, A.MIDDLE_CENTER)
    flecha(h, (x3 + 76, y - 40), (x3 + 96, y - 40))
    # estación 4: estanqueidad y control
    x4 = x3 + 102
    h.texto("4  ESTANQUEIDAD", (x4, y + 40), 3.5)
    h.rect(x4, y - 62, x4 + 44, y - 20, VIS)
    h.linea((x4 + 2, y - 26), (x4 + 42, y - 26), FIN)
    recipiente(h, x4 + 22, y - 60, 18, 30, "")
    h.texto("cuba de inmersión", (x4 + 22, y - 72), 2.5, A.MIDDLE_CENTER)
    h.texto("o detector de fugas", (x4 + 22, y - 76), 2.5, A.MIDDLE_CENTER)
    flecha(h, (x4 + 22, y - 84), (x4 + 22, y - 96))
    caja(h, x4 + 22, y - 104, 60, 14, "5  PESADA + MARBETE + PRECINTO\nOBLEA (FL_SEN_04)", 2.5)
    leyenda(h, h.fx1 - 62, h.fy1 - 12)
    _notas(h, ["NOTAS (criterios de aceptación en DOC-02 y DOC-03)",
               "1) Polvo IRAM 3569 certificado; PROHIBIDO mezclar ABC con BC (IRAM 3517-2:2020 9.9.1.6).",
               "2) Recinto HR ≤ 70 %, deshumidificado por condensación (sin estufas), ≥ 8 renov./h (9.4.8).",
               "3) Tolerancia de carga: 1-2,5 kg 0/+100 g; 5-10 kg 0/+300 g; rodantes ± 3 % (tabla 3).",
               "4) Presurizar con nitrógeno seco (tabla 2); secado verificado con cámara de video (9.8.2).",
               "5) Ensayo de pérdidas obligatorio (9.4.10), fuera del recinto si evapora agua; control a las 24 h (FLAMA).",
               "6) Rodantes: la misma secuencia con la botella/recipiente de 25 a 100 kg y su válvula."],
           h.fy0 + 80)
    return doc


# ------------------------------------------------------------------ ESQ-03 flujo de recarga
def esq03():
    doc, h = _hoja("FL_ESQ_03", "Flujo de recarga", "Servicio de recarga por tipo (IRAM 3517-2)")
    cx = h.fx0 + 55
    y = h.fy1 - 14
    pasos = ["RECEPCIÓN E IDENTIFICACIÓN\n(n° de serie, tarjeta)", "INSPECCIÓN EXTERNA\n(corrosión, golpes, marcado)",
             "DESPRESURIZAR Y VACIAR\n(recuperar agente)", "INSPECCIÓN INTERNA\n(corrosión, polvo apelmazado)"]
    for i, t in enumerate(pasos):
        caja(h, cx, y - 16 * i, 70, 11, t)
        flecha(h, (cx, y - 16 * i - 5.5), (cx, y - 16 * (i + 1) + 5.5))
    yr = y - 16 * 4 - 2
    rombo(h, cx, yr, 64, 18, "¿PH vencida o\nrecipiente dudoso?")
    h.linea((cx + 32, yr), (cx + 50, yr), FIN)
    h.texto("SÍ", (cx + 36, yr + 2.5), 2.5)
    caja(h, cx + 68, yr, 36, 12, "PRUEBA\nHIDRÁULICA\n(FL_ESQ_01)", 2.5)
    rombo(h, cx + 68, yr - 22, 36, 16, "¿aprueba?")
    flecha(h, (cx + 68, yr - 6), (cx + 68, yr - 14))
    h.linea((cx + 86, yr - 22), (cx + 100, yr - 22), FIN)
    caja(h, cx + 114, yr - 22, 28, 12, "INUTILIZAR\n2 aguj. Ø10\nNO APTO", 2.5)
    h.texto("NO", (cx + 88, yr - 19.5), 2.5)
    h.linea((cx + 68, yr - 30), (cx + 68, yr - 36), FIN)
    h.texto("SÍ", (cx + 70, yr - 33), 2.5)
    flecha(h, (cx + 68, yr - 36), (cx + 3, yr - 36))
    h.texto("NO", (cx + 2, yr - 12), 2.5)
    flecha(h, (cx, yr - 9), (cx, yr - 36 - 4))
    y2 = yr - 46
    caja(h, cx, y2, 70, 11, "SECADO (polvo) / LIMPIEZA\nREEMPLAZO de O-ring y precinto")
    flecha(h, (cx, y2 - 5.5), (cx, y2 - 12))
    caja(h, cx, y2 - 17, 70, 10, "CARGA SEGÚN TIPO (tabla derecha)")
    flecha(h, (cx, y2 - 22), (cx, y2 - 28))
    caja(h, cx, y2 - 33, 70, 10, "ESTANQUEIDAD + PESADA FINAL")
    flecha(h, (cx, y2 - 38), (cx, y2 - 44))
    caja(h, cx, y2 - 49, 70, 10, "MARBETE, OBLEA, PRECINTO, ENTREGA")
    filas = [("Tipo", "Agente", "Carga", "Presurización / control"),
             ("ABC / BC", "polvo IRAM 3569", "por peso, recipiente seco", "N2 a 1,4 MPa; manómetro en verde"),
             ("Rodantes ABC", "polvo IRAM 3569", "por peso", "N2 a P servicio; manguera y tobera"),
             ("CO2", "CO2 IRAM 41170", "trasvase por peso", "autopresurizado; antirretroceso"),
             ("Agua", "agua potable", "cambio anual, lavar", "N2 o aire; PH c/2 años"),
             ("AFFF", "solución AFFF IRAM 3515", "cambio anual, lavar", "N2 o aire; PH c/2 años"),
             ("Sales K", "solución IRAM 3697", "cambio anual, lavar", "N2 o aire; recip. inox"),
             ("HCFC/HFC", "IRAM 3526", "recuperación cerrada", "N2 o argón (Mezcla B: argón)"),
             ("Clase D", "polvo clase D", "por peso, seco", "N2 a 1,4 MPa")]
    _tabla(h, h.fx0 + 150, h.fy1 - 14, filas, [26, 42, 46, 60], alto=5.5, hs=(2.5, 2.5, 1.8, 1.8),
           encabezado="CARGA SEGÚN TIPO")
    h.bloque_libre(["NOTAS",
                    "1) IRAM 3517-2:2020: control trimestral, mantenimiento anual, PH 5 años (polvo, CO2) / 2 años (agua).",
                    "2) Presiones de servicio: catálogo FLAMA (Hoja 3 de cada plano FL_MAT).",
                    "3) El agente descargado se recupera; halogenados: prohibido liberarlos a la atmósfera.",
                    "4) Inutilización (9.12): 2 orificios Ø ≥ 10 mm, mangueras cortadas, acta del anexo G.",
                    "5) Gas impulsor según tabla 2; registro de trazabilidad 6 años (9.4.16); marbete por año (9.6)."],
                   h.fx0 + 150, [h.fy1 - 75 - 4 * k for k in range(30)])
    return doc


LAMINAS = [("FL_ESQ_01", esq01, "A3"), ("FL_ESQ_02", esq02, "A3"), ("FL_ESQ_03", esq03, "A3")]
