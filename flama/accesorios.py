"""Accesorios de matafuegos FLAMA: modelos 3D y planos de fabricación.

  FL_ACC_01  Soporte de pared (gancho de chapa con cartelas) para 2,5 / 5 / 10 kg.
  FL_ACC_02  Soporte vehicular con dos abrazaderas de fleje (1 kg / 2,5 kg).
  FL_ACC_03  Gabinete metálico con puerta y visor para matafuegos de 5 y 10 kg.

Igual que los matafuegos, las vistas salen de proyectar el sólido con
eliminación de líneas ocultas (método ISO E, IRAM 4501), con isometría
(IRAM 4540), cotas IRAM 4513 y rótulo IRAM 4508.
"""

import cadquery as cq

from . import vistas as V
from .lamina import Hoja, nuevo_doc, A
from .planos import FECHA, DIBUJO, _tabla
from .catalogo import G_1KG, G_2K5, G_5KG, G_10KG

V3 = cq.Vector


def _caja(x0, y0, z0, x1, y1, z1):
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, V3(x0, y0, z0))


def _cil(r, h, p, d):
    return cq.Solid.makeCylinder(r, h, V3(*p), V3(*d))


# ------------------------------------------------------------------ modelos 3D
# Convención: pared en el plano y = 0 (atrás), el observador de la vista
# anterior mira desde -Y; Z hacia arriba.
def _prof_gancho(g):
    """Vuelo del gancho: eje del cuello a R + 2 mm de la pared, más 22 mm de apoyo."""
    return round(g["R"] + 2 + 22, 0)


def soporte_pared(g=G_10KG, e=2.0):
    Aa = _prof_gancho(g)
    yc = -(g["R"] + 2)             # eje del cuello
    ranura = g["cuello"][0] + 3    # ancho de la ranura = Ø cuello + 3
    placa = _caja(-30, 0, 0, 30, e, 180)
    for z in (30, 150):
        placa = placa.cut(_cil(4.25, 10, (0, 5, z), (0, -1, 0)))
    ala = _caja(-30, -Aa, 180 - e, 30, e, 180)
    ala = ala.cut(_caja(-ranura / 2, -Aa - 1, 170, ranura / 2, yc, 190))
    ala = ala.cut(_cil(ranura / 2, 20, (0, yc, 170), (0, 0, 1)))
    labio = _caja(-30, -Aa, 180, -ranura / 2 - 0, -Aa + e, 192)
    labio2 = _caja(ranura / 2, -Aa, 180, 30, -Aa + e, 192)
    cartelas = []
    for x in (-30, 30 - e):
        tri = (cq.Workplane("YZ", origin=(x, 0, 0))
               .polyline([(0, 180 - e), (-0.55 * Aa, 180 - e), (0, 180 - e - 0.55 * Aa)]).close().extrude(e).val())
        cartelas.append(tri)
    s = placa.fuse(ala).fuse(labio).fuse(labio2)
    for c in cartelas:
        s = s.fuse(c)
    return s.clean(), dict(A=Aa, ranura=ranura, yc=yc)


def soporte_vehicular(g=G_2K5, e=2.5):
    D = 2 * g["R"]
    W = 80.0
    Hb = float(round(0.62 * g["total"]))
    yc = -(D / 2 + e + 1)
    base = _caja(-W / 2, 0, 0, W / 2, e, Hb)
    for z in (25, Hb - 25):
        for x in (-W / 2 + 15, W / 2 - 15):
            base = base.cut(_cil(3.25, 10, (x, 5, z), (0, -1, 0)))
    piso = _caja(-W / 2, 2 * yc, 0, W / 2, 0, e)          # bandeja inferior
    piso = piso.fuse(_caja(-W / 2, 2 * yc, 0, W / 2, 2 * yc + e, 15))  # tope frontal
    s = base.fuse(piso)
    zs = (round(0.25 * Hb), round(0.8 * Hb))
    for z in zs:
        aro = _cil(D / 2 + 1.0, 25, (0, yc, z), (0, 0, 1)).cut(_cil(D / 2, 25, (0, yc, z), (0, 0, 1)))
        s = s.fuse(aro)
        s = s.fuse(_caja(-12, -2, z, 12, 0, z + 25))            # remache/estribo a la base
        cierre = _caja(D / 2 - 2, yc - 8, z + 2, D / 2 + 14, yc + 8, z + 23)  # hebilla de cierre rápido
        s = s.fuse(cierre)
    return s.clean(), dict(D=D, W=W, Hb=Hb, yc=yc, zs=zs)


def gabinete(W=300.0, P=220.0, H=750.0, e=0.9):
    cuerpo = _caja(-W / 2, 0, 0, W / 2, P, H).cut(_caja(-W / 2 + e, e, e, W / 2 - e, P + 1, H - e))
    cuerpo = cuerpo.translate(V3(0, -P, 0))   # fondo contra la pared (y = 0)
    ep = 20.0  # puerta de chapa plegada (bandeja de 20 mm)
    puerta = _caja(-W / 2, -P - ep, 0, W / 2, -P, H).cut(_caja(-W / 2 + e, -P - ep + e, e, W / 2 - e, -P + 1, H - e))
    puerta = puerta.cut(_caja(-W / 2 + 50, -P - ep - 1, 250, W / 2 - 50, -P + 1, 650))  # abertura del visor
    visor = _caja(-W / 2 + 45, -P - 4, 245, W / 2 - 45, -P - 1, 655)
    bisagra = _cil(4, H - 20, (-W / 2 - 4, -P - 4, 10), (0, 0, 1))
    manija = _caja(W / 2 - 30, -P - ep - 12, H / 2 - 40, W / 2 - 20, -P - ep, H / 2 + 40)
    s = cuerpo.fuse(puerta).fuse(visor).fuse(bisagra).fuse(manija)
    for z in (e, H - e):
        for x in (-60, 20):
            s = s.cut(_caja(x, -P / 2 - 2.5, z - 5, x + 40, -P / 2 + 2.5, z + 5))  # ranuras de ventilación
    return s.clean(), dict(W=W, P=P + ep, H=H)


# ------------------------------------------------------------------ lámina genérica
def _hoja(codigo, titulo, sub, escala, material, fmt="A3"):
    doc = nuevo_doc()
    h = Hoja(doc, fmt)
    h.formato()
    h.rotulo(dict(titulo=titulo, subtitulo=sub, codigo=codigo, hoja=1, hojas=1, escala=escala,
                  material=material, edicion="0", fecha=FECHA, dibujo=DIBUJO, reviso="", aprobo="",
                  tipo_doc="Plano de fabricación", empresa="FLAMA S.A."))
    return doc, h


def vistas_iso_e(h, solido, f, zona, gap=22.0, iso=True, iso_zona=None, iso_f=None):
    """Dispone anterior (A), superior (B, debajo) y lateral izquierda (C, a la
    derecha) según ISO E, centradas en `zona` (x0, y0, x1, y1). Devuelve
    transformaciones {vista: (ox, oy, f)} y extensiones reales."""
    proy = {v: V.proyectar(solido, v, tol=0.4, ocultas=(v != "iso")) for v in V.VISTAS}
    ex = {v: V.extension(proy[v]["vis"]) for v in proy}
    wa, ha = ex["anterior"][2] - ex["anterior"][0], ex["anterior"][3] - ex["anterior"][1]
    hb = ex["superior"][3] - ex["superior"][1]
    wc = ex["lat_izq"][2] - ex["lat_izq"][0]
    ancho = (wa + wc) * f + gap
    alto = (ha + hb) * f + gap
    x0, y0, x1, y1 = zona
    ax = x0 + ((x1 - x0) - ancho) / 2
    by = y0 + ((y1 - y0) - alto) / 2
    ay = by + hb * f + gap
    T = {"anterior": (ax - ex["anterior"][0] * f, ay - ex["anterior"][1] * f, f),
         "superior": (ax - ex["superior"][0] * f, by - ex["superior"][1] * f, f),
         "lat_izq": (ax + wa * f + gap - ex["lat_izq"][0] * f, ay - ex["lat_izq"][1] * f, f)}
    for v, t in T.items():
        h.prims(proy[v]["oc"], "02-OCULTA", t)
        h.prims(proy[v]["vis"], "01-VISIBLE", t)
    if iso:
        e = ex["iso"]
        fi = iso_f or f
        if iso_zona:
            cx, cy = (iso_zona[0] + iso_zona[2]) / 2, (iso_zona[1] + iso_zona[3]) / 2 + 3
        else:
            cx, cy = ax + wa * f + gap + wc * f / 2, by + hb * f / 2
        T["iso"] = (cx - (e[0] + e[2]) / 2 * fi, cy - (e[1] + e[3]) / 2 * fi, fi)
        h.prims(proy["iso"]["vis"], "01-VISIBLE", T["iso"])
        if iso_zona:
            esc = "" if fi == f else f" ({'1:' + str(round(1 / fi)) if fi < 1 else str(round(fi)) + ':1'})"
            h.texto("ISOMETRÍA" + esc, (cx, cy - (e[3] - e[1]) * fi / 2 - 6), 3.5, A.MIDDLE_CENTER)
    return T, ex


def P(T, v, x, y):
    ox, oy, f = T[v]
    return (ox + x * f, oy + y * f)


def _notas(h, notas, y):
    for i, t in enumerate(notas):
        h.texto(t, (h.fx0 + 5, y - 5 * i), 2.5 if i else 3.5)


# ------------------------------------------------------------------ láminas
def acc01():
    g = G_10KG
    sol, d = soporte_pared(g)
    doc, h = _hoja("FL_ACC_01", "Soporte de pared", "Gancho con cartelas - matafuegos 2,5 / 5 / 10 kg",
                   "1:2", "SAE 1010 e=2")
    f = 0.5
    T, ex = vistas_iso_e(h, sol, f, (h.fx0 + 10, h.fy0 + 75, h.fx0 + 215, h.fy1 - 24), gap=28,
                         iso_zona=(h.fx1 - 165, h.fy0 + 58, h.fx1 - 5, h.fy1 - 90))
    k = 1 / f
    Aa = d["A"]
    # anterior: ancho 60, alto 192, agujeros a 30 y 150
    h.cota_lineal(P(T, "anterior", -30, 192), P(T, "anterior", 30, 192), P(T, "anterior", -30, 192 + 14), 0, k)
    h.cota_lineal(P(T, "anterior", -30, 0), P(T, "anterior", -30, 192), P(T, "anterior", -30 - 16, 0), 90, k)
    h.cota_lineal(P(T, "anterior", 0, 0), P(T, "anterior", 0, 30), P(T, "anterior", 30 + 10, 0), 90, k)
    h.cota_lineal(P(T, "anterior", 0, 30), P(T, "anterior", 0, 150), P(T, "anterior", 30 + 10, 0), 90, k)
    h.nota_referencia("2 aguj. Ø8,5", P(T, "anterior", -3, 27), P(T, "anterior", -62, -22))
    h.eje(P(T, "anterior", 0, -4), P(T, "anterior", 0, 196))
    # lateral: vuelo A (la vista C tiene X = -Y)
    h.cota_lineal(P(T, "lat_izq", 0, 192), P(T, "lat_izq", Aa, 192), P(T, "lat_izq", 0, 192 + 14), 0, k,
                  texto="A")
    # superior: ranura
    r = d["ranura"]
    h.cota_lineal(P(T, "superior", -r / 2, -Aa), P(T, "superior", r / 2, -Aa), P(T, "superior", 0, -Aa - 12), 0, k,
                  texto="B")
    h.eje(P(T, "superior", 0, -Aa - 4), P(T, "superior", 0, 4))
    filas = [("Matafuego", "Ø recipiente", "A (vuelo)", "B (ranura)")]
    for nom, gg in (("2,5 kg", G_2K5), ("5 kg", G_5KG), ("10 kg", G_10KG)):
        filas.append((nom, f"{2 * gg['R']:.1f}".replace(".", ",").replace(",0", ""), f"{_prof_gancho(gg):.0f}",
                      f"{gg['cuello'][0] + 3:.0f}"))
    _tabla(h, h.fx1 - 150, h.fy1 - 12, filas, [40, 36, 37, 37], encabezado="MEDIDAS POR MODELO (dibujado: 10 kg)")
    datos = [("Material", "Chapa acero SAE 1010 laminada en frío, e = 2 mm"),
             ("Fabricación", "corte láser, plegado a 90° r = 2 mm, cartelas soldadas MIG (131)"),
             ("Terminación", "granallado/fosfatizado + polvo poliéster rojo 60-80 µm (DOC-01)"),
             ("Fijación", "2 tarugos nylon Ø8 + tornillo Ø5 × 50"),
             ("Ensayo", "carga estática 4 × peso cargado, 5 min, sin deformación permanente"),
             ("Montaje", "altura según FL_SEN_01 (≤ 1,50 m; NFPA 10 §6.1.3.8)")]
    _tabla(h, h.fx1 - 150, h.fy1 - 44, datos, [30, 120], alto=5.0, hs=(2.5, 1.8), encabezado="ESPECIFICACIÓN")
    _notas(h, ["NOTAS",
               "1) Tolerancias generales ISO 2768-m; aristas vivas matadas 0,3 × 45°.",
               "2) El cuello del matafuego entra en la ranura B y la válvula apoya sobre el ala;",
               "    el labio frontal impide que el matafuego se desenganche por golpe.",
               "3) Cotas A y B según tabla (dibujado el soporte para 10 kg).",
               "4) Sin fijaciones que impidan retirar el extintor (IRAM 3517-2 3.3.4): se levanta y sale."], h.fy0 + 55)
    return doc, sol


def acc02():
    g = G_2K5
    sol, d = soporte_vehicular(g)
    doc, h = _hoja("FL_ACC_02", "Soporte vehicular", "Base con 2 abrazaderas de fleje - 1 kg / 2,5 kg",
                   "1:2", "SAE 1010 / AISI 304")
    f = 0.5
    T, ex = vistas_iso_e(h, sol, f, (h.fx0 + 10, h.fy0 + 75, h.fx0 + 215, h.fy1 - 24), gap=28,
                         iso_zona=(h.fx1 - 165, h.fy0 + 58, h.fx1 - 5, h.fy1 - 78))
    k = 1 / f
    W, Hb, D, yc = d["W"], d["Hb"], d["D"], d["yc"]
    h.cota_lineal(P(T, "anterior", -W / 2, Hb), P(T, "anterior", W / 2, Hb), P(T, "anterior", -W / 2, Hb + 12), 0, k)
    h.cota_lineal(P(T, "anterior", -D / 2 - 1, Hb), P(T, "anterior", -D / 2 - 1, 0),
                  P(T, "anterior", -D / 2 - 16, 0), 90, k, texto=f"{Hb:.0f}")
    h.cota_lineal(P(T, "superior", -D / 2, yc), P(T, "superior", D / 2, yc), P(T, "superior", 0, 2 * yc - 12), 0, k,
                  prefijo="%%c")
    h.eje(P(T, "superior", -D / 2 - 5, yc), P(T, "superior", D / 2 + 18, yc))
    h.eje(P(T, "superior", 0, 2 * yc - 4), P(T, "superior", 0, 6))
    for i, z in enumerate(d["zs"]):
        h.cota_lineal(P(T, "lat_izq", -2 * yc, 0), P(T, "lat_izq", -yc, z), P(T, "lat_izq", -2 * yc + 14 + 18 * i, 0), 90, k)
    filas = [("Matafuego", "Ø abrazadera", "Alto base", "Tornillos")]
    for nom, gg in (("1 kg", G_1KG), ("2,5 kg", G_2K5)):
        filas.append((nom, f"{2 * gg['R']:.1f}".replace(".", ","), f"{0.62 * gg['total']:.0f}", "4 × M6"))
    _tabla(h, h.fx1 - 150, h.fy1 - 12, filas, [40, 36, 37, 37], encabezado="MEDIDAS POR MODELO (dibujado: 2,5 kg)")
    datos = [("Base", "chapa acero SAE 1010 e = 2,5 mm plegada (bandeja y tope)"),
             ("Abrazaderas", "fleje inoxidable AISI 304 25 × 1 mm, forro de caucho 2 mm"),
             ("Cierre", "hebilla de palanca de apertura rápida, sin herramientas"),
             ("Terminación", "zincado + polvo poliéster negro (DOC-01)"),
             ("Fijación", "4 tornillos M6 con arandela y tuerca autofrenante"),
             ("Ensayo", "vibración vehicular: retiene el matafuego sin desplazamiento")]
    _tabla(h, h.fx1 - 150, h.fy1 - 38, datos, [30, 120], alto=5.0, hs=(2.5, 1.8), encabezado="ESPECIFICACIÓN")
    _notas(h, ["NOTAS",
               "1) Tolerancias generales ISO 2768-m.",
               "2) Montar con la válvula accesible y la manija hacia el operador; nunca en el habitáculo sin sujeción.",
               "3) Se ofrece para los modelos con 'Soporte vehicular' en el catálogo (1 kg, 2,5 kg; opcional 5 y 10 kg)."],
           h.fy0 + 55)
    return doc, sol


def acc03():
    sol, d = gabinete()
    doc, h = _hoja("FL_ACC_03", "Gabinete metálico", "Chapa plegada con puerta y visor - 5 kg / 10 kg",
                   "1:10", "SAE 1010 e=0,9")
    f = 0.1
    T, ex = vistas_iso_e(h, sol, f, (h.fx0 + 10, h.fy0 + 75, h.fx0 + 215, h.fy1 - 24), gap=25,
                         iso_zona=(h.fx1 - 165, h.fy0 + 58, h.fx1 - 5, h.fy1 - 60))
    k = 1 / f
    W, Pp, H = d["W"], d["P"], d["H"]
    h.cota_lineal(P(T, "anterior", -W / 2, H), P(T, "anterior", W / 2, H), P(T, "anterior", -W / 2, H + 80), 0, k)
    h.cota_lineal(P(T, "anterior", -W / 2 - 8, 0), P(T, "anterior", -W / 2 - 8, H), P(T, "anterior", -W / 2 - 110, 0), 90, k)
    h.cota_lineal(P(T, "lat_izq", 0, H), P(T, "lat_izq", Pp + 12, H), P(T, "lat_izq", 0, H + 80), 0, k)
    h.cota_lineal(P(T, "anterior", W / 2 - 50, 250), P(T, "anterior", W / 2 - 50, 650), P(T, "anterior", W / 2 + 90, 0), 90, k)
    h.nota_referencia("visor acrílico 3 mm", P(T, "anterior", 0, 450), P(T, "anterior", 250, 560))
    h.eje(P(T, "anterior", 0, -30), P(T, "anterior", 0, H + 30))
    datos = [("Cuerpo", "chapa acero SAE 1010 e = 0,9 mm, plegada y soldada por puntos"),
             ("Puerta", "bandeja de chapa e = 0,9, bisagra piano, cierre magnético sin llave"),
             ("Visor", "acrílico 3 mm (o vidrio de rotura con martillo)"),
             ("Terminación", "granallado/fosfatizado + polvo poliéster rojo (DOC-01)"),
             ("Interior", "soporte FL_ACC_01 para 10 kg; apto 5 kg"),
             ("Ventilación", "4 ranuras 40 × 5 en base y techo"),
             ("Leyenda", "\"MATAFUEGO\" en vinilo blanco sobre la puerta (FL_SEN_02)")]
    _tabla(h, h.fx1 - 150, h.fy1 - 12, datos, [30, 120], alto=5.0, hs=(2.5, 1.8), encabezado="ESPECIFICACIÓN")
    _notas(h, ["NOTAS",
               "1) Tolerancias generales ISO 2768-m.",
               "2) Medidas interiores útiles 298 × 218 × 748 mm: admite matafuego de 10 kg (Ø181,5 × 562,5 + válvula).",
               "3) Con vidrio: medio que asegure su rotura para extraer el extintor (IRAM 3517-2 3.3.4); martillo",
               "    junto al gabinete e interior con franjas rojas y blancas (IRAM 3517 rev. 2020, s/ resumen).",
               "4) Altura de montaje: parte superior del matafuego ≤ 1,50 m (FL_SEN_01)."], h.fy0 + 55)
    return doc, sol


LAMINAS = [("FL_ACC_01", acc01, "A3"), ("FL_ACC_02", acc02, "A3"), ("FL_ACC_03", acc03, "A3")]
