"""Generación de las láminas de cada modelo:
  Hoja 1 - Plano de conjunto: vistas anterior, superior y lateral izquierda
           (ISO E), isometría, cotas generales, números de posición y lista
           de piezas.
  Hoja 2 - Corte A-A del recipiente y detalles ampliados (zoom).
  Hoja 3 - Especificaciones técnicas y normativa citada.
"""

import math

import cadquery as cq
import datetime
import re
import shapely.geometry as sg

from . import modelo3d as M
from . import vistas as V
from . import normas as N
from . import materiales as MAT
from .lamina import (Hoja, nuevo_doc, ESCALAS, AMPLIAC, FORMATOS, ROT_W, ROT_H, A,
                     escala_txt, recortar_circulo, transformar, transformar_poly, ancho_medio,
                     altura_norm, partir, ancho_texto)

FECHA = "28/09/2026"
DIBUJO = "T. Sinay"

NO_LISTAR = {"soldaduras", "rueda_izq", "llanta_izq"}
VALVULA = {"espiga", "tuerca", "cuerpo_valvula", "vastago", "resorte", "eje", "manija_superior",
           "manija_inferior", "pasador", "manometro", "racor", "disco_seguridad"}


def ancla_lateral(key, piezas):
    """punto (-y, z) de referencia de la pieza en la vista lateral izquierda."""
    sb = piezas[key].BoundingBox()
    ay, az = (sb.ymin + sb.ymax) / 2, (sb.zmin + sb.zmax) / 2
    if key == "manija_superior":
        ay, az = sb.ymin + 0.6 * (sb.ymax - sb.ymin), sb.zmax - 4
    elif key == "manometro":
        ay = sb.ymin + 3
    elif key == "pasador":
        ay, az = sb.ymin + 2, sb.zmin + 1.5
    return -ay, az


def ancla(key, piezas, info):
    """punto (x, z) de referencia de la pieza en la vista anterior."""
    R = info["recipiente"]["R"]
    sb = piezas[key].BoundingBox()
    ax, az = (sb.xmin + sb.xmax) / 2, (sb.zmin + sb.zmax) / 2
    if key == "cuerpo":
        ax, az = -R * 0.55, (info["recipiente"]["zb"] + info["recipiente"]["z_union"]) * 0.55
    elif key == "cupula":
        ax, az = -R * 0.45, info["recipiente"]["z_union"] + (info["recipiente"]["z_cupula"] - info["recipiente"]["z_union"]) * 0.45
    elif key == "fondo":
        ax, az = R * 0.35, sb.zmin + (sb.zmax - sb.zmin) * 0.5
    elif key in ("manguera", "manguera_enrollada"):
        ax = sb.xmin + (4 if key == "manguera" else 6)
    elif key == "manija_superior":
        ax, az = sb.xmax - 10, sb.zmax - 4
    elif key == "manija_inferior":
        ax, az = sb.xmax - 25, sb.zmin + 2
    elif key == "pasador":
        ax, az = sb.xmin + 2, sb.zmin + 1.5
    elif key == "manometro":
        ax, az = ax - 4, az + 4
    return ax, az


def colocar_globos(h, anclas, x_eje, x_izq, x_der, y_max, y_min, paso_min=9.0, prohibidas=None, y_lim=None):
    """Globos en columna a cada lado de la vista, ordenados por altura, con paso
    mínimo y evitando las franjas `prohibidas` {'izq': [(y0, y1)], 'der': [...]}
    (cifras de cotas verticales). Si la columna no entra por debajo de `y_lim` (marco),
    los globos se escalonan en dos columnas separadas 10 mm (paso vertical a la mitad)."""
    prohibidas = prohibidas or {}
    izq = sorted([a for a in anclas if a[2] < x_eje], key=lambda a: -a[3])
    der = sorted([a for a in anclas if a[2] >= x_eje], key=lambda a: -a[3])

    def columna(grupo, bandas, paso):
        # franjas solapadas (cifras de cotas vecinas) se juntan en una sola
        bandas = sorted(bandas)
        juntas = []
        for b0, b1 in bandas:
            if juntas and b0 - 10 <= juntas[-1][1]:
                juntas[-1] = (juntas[-1][0], max(juntas[-1][1], b1))
            else:
                juntas.append((b0, b1))
        bandas = juntas
        ys = []
        for a in grupo:
            tope = y_max if not ys else ys[-1] - paso
            yy = min(a[3], tope)
            for (b0, b1) in bandas:
                if b0 - 5 < yy < b1 + 5:
                    # fuera de la cifra de la cota, del lado del ancla: así la línea de referencia no la cruza
                    yy = b1 + 5 if a[3] >= (b0 + b1) / 2 and b1 + 5 <= tope else b0 - 5
            ys.append(yy)
        if ys[-1] < y_min:
            # no entra abajo: se arma de abajo hacia arriba, esquivando otra vez las cifras de las cotas
            ys[-1] = y_min
            for (b0, b1) in bandas:
                if b0 - 5 < ys[-1] < b1 + 5:
                    ys[-1] = b1 + 5
            for j in range(len(ys) - 2, -1, -1):
                ys[j] = max(ys[j], ys[j + 1] + paso)
                for (b0, b1) in bandas:
                    if b0 - 5 < ys[j] < b1 + 5:
                        ys[j] = b1 + 5
        return ys

    for lado, grupo, xg in (("izq", izq, x_izq), ("der", der, x_der)):
        if not grupo:
            continue
        bandas = prohibidas.get(lado, [])
        ys = columna(grupo, bandas, paso_min)
        dx = [0.0] * len(ys)
        if y_lim is not None and ys[0] + 4 > y_lim:
            ys = columna(grupo, bandas, max(paso_min / 2, 5.0))
            sg = -1 if lado == "izq" else 1
            dx = [sg * 10.0 * (i % 2) for i in range(len(ys))]
            if ys[0] + 4 > y_lim:
                ys = [y - (ys[0] + 4 - y_lim) for y in ys]
        for a, yy, d in zip(grupo, ys, dx):
            h.globo(a[0], (a[2], a[3]), (xg + d, yy))


def _n(v, dec=1):
    s = f"{v:.{dec}f}"
    if "." in s:  # sólo ceros decimales: con dec=0 «420» no debe quedar «42»
        s = s.rstrip("0").rstrip(".")
    return s.replace(".", ",")


def codigo_pieza(m, pos):
    """Código de pieza: abreviatura del modelo + posición (p. ej. ABC10-01)."""
    base = re.sub(r"(kg|l)$", "", m.codigo.replace("FL_MAT_", "")).replace("_", "").replace("-", "")
    return f"{base}-{pos:02d}"


def lista(m, piezas):
    """Filas de la lista de materiales IRAM 4508:
    [pos, cant, denominación, código, material, peso kg, observaciones]."""
    filas, orden = [], []
    total = 0.0
    for k in piezas:
        if k in NO_LISTAR:
            continue
        esp = MAT.especificacion(m, k)
        if esp is None:
            continue
        nom, mat, rho, fac, obs = esp
        cant = 2 if k in ("rueda_der", "llanta_der") else 1
        kg = MAT.peso(piezas[k], rho, fac)
        orden.append(k)
        pos = len(orden)
        if kg is not None:
            total += kg * cant
        filas.append([pos, cant, nom, codigo_pieza(m, pos) if rho else "Comercial", mat,
                      ("<0,001" if kg < 0.0005 else _n(kg, 3 if kg < 1 else 2)) if kg is not None else "-", obs or ""])
    return filas, orden, total


# márgenes que ocupan cotas y números de posición alrededor de cada vista (mm de papel)
EXT_IZQ, EXT_DER, EXT_SUP, EXT_INF, NOTAS_H = 36.0, 24.0, 17.0, 15.0, 12.0


def _zona_vistas(fmt):
    """Zona libre para las vistas: a la izquierda de la columna de rótulo y lista."""
    Wf, Hf = FORMATOS[fmt]
    x0, x1 = 25.0 + 4, Wf - 10 - ROT_W - 8
    y0, y1 = 10.0 + NOTAS_H, Hf - 10 - 4
    return x0, y0, x1, y1


def _grupo(ext, k, gap_x, gap_y, rodante):
    """Ancho y alto del grupo de vistas (con cotas y globos) a escala 1:k."""
    f = 1 / k
    wF = (ext["anterior"][2] - ext["anterior"][0]) * f
    hF = (ext["anterior"][3] - ext["anterior"][1]) * f
    wL = (ext["lat_izq"][2] - ext["lat_izq"][0]) * f
    hT = (ext["superior"][3] - ext["superior"][1]) * f
    w = EXT_IZQ + wF + EXT_DER + gap_x + wL + 4
    h = EXT_SUP + hF + gap_y + hT + EXT_INF + (10 if rodante else 0)
    return w, h


def _elegir(m, ext):
    """Formato y escala (IRAM 4505): la mayor escala normalizada con la que el
    grupo de vistas entra en A3 o A2; a igual escala, el formato más chico."""
    for e in ESCALAS:
        k = e[1] / e[0]
        for fmt in ("A3", "A2"):
            x0, y0, x1, y1 = _zona_vistas(fmt)
            w, h = _grupo(ext, k, 20, 20, m.familia == "rodante")
            if w <= x1 - x0 and h <= y1 - y0:
                return fmt, e, k
    return "A2", ESCALAS[-1], ESCALAS[-1][1] / ESCALAS[-1][0]


def rotulo_base(m, fmt, e, hoja, tipo, sub=""):
    return dict(titulo=m.nombre, subtitulo=sub or f"Agente: {m.agente}", codigo=m.codigo,
                hoja=hoja, hojas=4, escala=escala_txt(e) if e else "-", material="Ver lista de piezas",
                edicion="0", fecha=FECHA, dibujo=DIBUJO, reviso="", aprobo="",
                tipo_doc=tipo, empresa="FLAMA S.A.")


# =================================================================== ejes (IRAM 4502 línea F)
def ejes(m, info, vista):
    """Segmentos de ejes y centros (coordenadas reales de la vista), sobresaliendo
    3 mm de cada contorno."""
    r = info["recipiente"]
    v = info["valvula"]
    R, e = r["R"], 3.0
    z0 = r["z_fondo"] - e if m.familia != "rodante" else r["z_fondo"] - e
    seg = []
    if vista in ("anterior", "lat_izq"):
        seg.append(((0, z0), (0, v["z_top"] + e)))                          # eje del recipiente y válvula
    if vista == "anterior":
        zs = v["z_salida"]
        seg.append(((v["x_salida"] - 14, zs), (v["bw"] / 2 + e, zs)))        # eje de la boca de salida
        if "man_d" in v and m.familia != "co2":
            rm = v["man_d"] / 2 + e
            seg += [((-rm, v["z_man"]), (rm, v["z_man"])), ((0, v["z_man"] - rm), (0, v["z_man"] + rm))]
        if "eje_tobera_3d" in info:                                          # tobera del carro, inclinada
            (xa, ya, za), (xb, yb, zb) = info["eje_tobera_3d"]
            seg.append(((xa, za), (xb, zb)))
        elif "eje_tobera" in info:
            xt, zb, zt = info["eje_tobera"]
            seg.append(((xt, zb - e), (xt, zt + e)))
        if m.familia == "rodante":
            seg.append(((-info["xw"] - e, info["Rw"]), (info["xw"] + e, info["Rw"])))
    if vista == "lat_izq" and m.familia == "rodante":
        Rw, yw = info["Rw"], info["yw"]
        seg += [((-yw - Rw - e, Rw), (-yw + Rw + e, Rw)), ((-yw, -e), (-yw, 2 * Rw + e))]
        if "eje_tobera_3d" in info:
            (xa, ya, za), (xb, yb, zb) = info["eje_tobera_3d"]
            seg.append(((-ya, za), (-yb, zb)))
    if vista == "superior":
        seg += [((-R - e, 0), (R + e, 0)), ((0, -R - e), (0, R + e))]
        if "eje_tobera_3d" in info:
            (xa, ya, za), (xb, yb, zb) = info["eje_tobera_3d"]
            seg.append(((xa, ya), (xb, yb)))
        elif "eje_tobera" in info:
            xt = info["eje_tobera"][0]
            seg += [((xt - 16, 0), (xt + 16, 0)), ((xt, -16), (xt, 16))]
        if m.familia == "rodante":
            yw = info["yw"]
            seg.append(((-info["xw"] - e, yw), (info["xw"] + e, yw)))
    return seg


# =================================================================== HOJA 1
def hoja1(m, piezas, info, proy, doc, ox=0.0):
    ext = {v: V.extension(proy[v]["vis"]) for v in ("anterior", "superior", "lat_izq")}
    fmt, e, k = _elegir(m, ext)
    f = 1.0 / k
    h = Hoja(doc, fmt, ox)
    h.formato()
    y_rot = h.rotulo(rotulo_base(m, fmt, e, 1, "Plano de conjunto"))
    filas, orden, masa_vacio = lista(m, piezas)
    h_fila = 5.0 if len(filas) <= 18 else 4.5
    y_lst = h.lista_piezas(filas, y_rot, h_fila)

    # ---- composición: grupo de vistas centrado en la zona libre, separaciones iguales
    zx0, zy0, zx1, zy1 = _zona_vistas(fmt)
    zx0, zx1 = zx0 + ox, zx1 + ox
    rod = m.familia == "rodante"
    w0, h0 = _grupo(ext, k, 0, 0, rod)
    gap_x = min(45.0, max(20.0, (zx1 - zx0 - w0) / 3))
    gap_y = min(40.0, max(20.0, (zy1 - zy0 - h0) / 3))
    wg, hg = _grupo(ext, k, gap_x, gap_y, rod)
    gx0 = zx0 + (zx1 - zx0 - wg) / 2
    gy1 = zy1 - (zy1 - zy0 - hg) / 2
    x_front = gx0 + EXT_IZQ - ext["anterior"][0] * f
    y_front = gy1 - EXT_SUP - ext["anterior"][3] * f
    Tf = (x_front, y_front, f)
    x_lat = x_front + ext["anterior"][2] * f + EXT_DER + gap_x - ext["lat_izq"][0] * f
    Tl = (x_lat, y_front, f)
    y_top = y_front + ext["anterior"][1] * f - gap_y - ext["superior"][3] * f
    Tt = (x_front, y_top, f)

    for v, T in (("anterior", Tf), ("superior", Tt), ("lat_izq", Tl)):
        h.prims(proy[v]["oc"], "02-OCULTA", T)
        h.prims(proy[v]["vis"], "01-VISIBLE", T)

    R = info["recipiente"]["R"]
    zc = info["recipiente"]["z_cuello"]
    # placa de características como superficie rayada (detalle en hoja 4)
    import shapely.geometry as _sg
    Wp, Hp, z0p, Rp, xcp, _ = M.placa_dim(m, piezas)
    cu = 2 * Rp * math.sin(math.radians(M.ARCO_PLACA / 2))
    ap = Rp * min(1.0, math.sin(math.radians(M.ARCO_PLACA / 2 + M.arco_ala(Rp, m))))
    h.rayado(_sg.box(x_front + (xcp - ap) * f, y_front + z0p * f, x_front + (xcp + ap) * f,
                     y_front + (z0p + Hp) * f), 45, 3.0)
    h.rayado(_sg.box(x_front + (xcp - cu / 2) * f, y_front + z0p * f, x_front + (xcp + cu / 2) * f,
                     y_front + (z0p + Hp) * f), 45, 1.2)
    # ejes y centros (IRAM 4502 línea F)
    for v, (ox_, oy_) in (("anterior", (x_front, y_front)), ("lat_izq", (x_lat, y_front)), ("superior", (x_front, y_top))):
        for (a1, b1), (a2, b2) in ejes(m, info, v):
            h.eje((ox_ + a1 * f, oy_ + b1 * f), (ox_ + a2 * f, oy_ + b2 * f))

    # ---------------- cotas generales (medidas reales del modelo)
    bb = M.bbox(piezas)
    xl, xr = x_front + bb.xmin * f, x_front + bb.xmax * f
    yb, yt = y_front + bb.zmin * f, y_front + bb.zmax * f
    # altura total (izquierda)
    h.cota_lineal((xl, yb), (xl, yt), (xl - 22, yb), 90, k)
    # altura del recipiente con cuello
    h.cota_lineal((x_front - R * f, yb), (x_front - 3, y_front + zc * f), (xl - 11, yb), 90, k)
    # ancho total (arriba)
    h.cota_lineal((xl, yt), (xr, yt), (xl, yt + 9), 0, k)
    # diámetro del recipiente (en la vista superior, debajo de la vista)
    yd = y_top + ext["superior"][1] * f - 10
    h.cota_lineal((x_front - R * f, y_top), (x_front + R * f, y_top), (x_front, yd), 0, k, prefijo="%%c")
    # profundidad (vista lateral, arriba)
    lx0, lx1 = x_lat + (-bb.ymax) * f, x_lat + (-bb.ymin) * f
    h.cota_lineal((lx0, yt), (lx1, yt), (lx0, yt + 9), 0, k)
    if m.familia == "rodante":
        Rw = info["Rw"]
        yw = info["yw"]
        # diámetro de rueda en vista lateral
        cxw = x_lat - yw * f
        h.cota_lineal((cxw - Rw * f, y_front + Rw * f), (cxw + Rw * f, y_front + Rw * f),
                      (cxw, y_front - 9), 0, k, prefijo="%%c")
        h.eje((cxw - Rw * f - 4, y_front + Rw * f), (cxw + Rw * f + 4, y_front + Rw * f))
        h.eje((cxw, y_front - 4), (cxw, y_front + 2 * Rw * f + 4))
        # trocha entre centros de rueda (IRAM 3550 tabla III: ≥ 400) en la vista superior
        xw = info["xw"]
        h.cota_lineal((x_front - xw * f, y_top + yw * f), (x_front + xw * f, y_top + yw * f),
                      (x_front, yd - 9), 0, k, prefijo="trocha ")
    else:
        # posición del suncho / tobera
        if "suncho_z" in info:
            zs = info["suncho_z"]
            h.cota_lineal((x_front + R * f, yb), (x_front + R * f, y_front + zs * f), (xr + 10, yb), 90, k)

    # ---------------- plano de corte A-A en la vista superior
    h.plano_corte((x_front - R * f - 14, y_top), (x_front + R * f + 14, y_top), "A", (0, 1))

    # ---------------- detalles marcados en vista anterior (ver hoja 2)
    detalles = definir_detalles(m, info)
    letras = []                    # las letras van después de los globos, en un lugar que no pise ninguno
    for d in detalles:
        org = d.get("marca", d["origen"])
        if org not in ("anterior", "lateral"):
            continue
        cc = d.get("c_marca", d["c"])
        c = ((x_front if org == "anterior" else x_lat) + cc[0] * f, y_front + cc[1] * f)
        r_m = d.get("r_marca", d["r"])            # los cortes horizontales marcan sólo el fleje en la lateral
        h.msp.add_circle(c, r_m * f, dxfattribs={"layer": "08-FINA"})
        a0 = d.get("ang_letra", 45)
        cands = [(c[0] + (r_m * f + rr) * math.cos(math.radians(a0 + da)),
                  c[1] + (r_m * f + rr) * math.sin(math.radians(a0 + da)))
                 for rr in (4.0, 6.5, 9.0, 12.0, 15.0) for da in (0, 25, -25, 50, -50, 75, -75, 100, -100, 135, -135, 180)]
        letras.append((d["letra"], cands))

    # ---------------- números de posición (globos) en vista anterior
    # (los componentes de la válvula se referencian en el detalle A, hoja 2)
    anclas = []
    for i, key in enumerate(orden):
        if key in VALVULA:
            continue
        ax, az = ancla(key, piezas, info)
        anclas.append((i + 1, key, x_front + ax * f, y_front + az * f))
    y_zc = y_front + zc * f
    banda_izq = [((yb + yt) / 2 - 7, (yb + yt) / 2 + 7), ((yb + y_zc) / 2 - 7, (yb + y_zc) / 2 + 7)]
    banda_der = []
    if "suncho_z" in info and m.familia != "rodante":
        ysu = y_front + info["suncho_z"] * f
        banda_der.append(((yb + ysu) / 2 - 7, (yb + ysu) / 2 + 7))
    colocar_globos(h, anclas, x_front, xl - 31, xr + 19, yt - 2, yb + 6, 10.0,
                   {"izq": banda_izq, "der": banda_der}, y_lim=h.fy1 - 6)
    for letra, cands in letras:
        h.texto_libre(letra, cands, 5, A.MIDDLE_CENTER)

    # ---------------- isometría: en la zona libre donde resulte más grande
    #   (a) columna derecha, sobre la lista de materiales
    #   (b) cuadrante libre bajo la vista lateral izquierda, a la derecha de la superior
    exi = V.extension(proy["iso"]["vis"])
    wi, hi = exi[2] - exi[0], exi[3] - exi[1]
    zonas = [(h.fx1 - ROT_W, y_lst + 14, h.fx1, h.fy1 - 6)]
    x_q0 = max(x_front + (ext["superior"][2]) * f + 30, x_lat + ext["lat_izq"][0] * f - 10)
    y_q1 = y_front + ext["lat_izq"][1] * f - (22 if rod else 12)
    if zx1 - x_q0 > 60 and y_q1 - zy0 > 60:
        zonas.append((x_q0, zy0, zx1, y_q1))
    mejor = None
    for (a0, b0, a1, b1) in zonas:
        for cand in ESCALAS:
            kk = cand[1] / cand[0]
            if kk >= k and wi / kk <= (a1 - a0) - 12 and hi / kk <= (b1 - b0) - 12:
                if mejor is None or kk <= mejor[0][1] / mejor[0][0]:  # a igual escala, el cuadrante libre
                    mejor = (cand, (a0, b0, a1, b1))
                break
    ei, (a0, b0, a1, b1) = mejor if mejor else (ESCALAS[-1], zonas[0])
    fi = ei[0] / ei[1]
    cx_iso = (a0 + a1) / 2
    cy_iso = (b0 + b1) / 2 + 3
    oxi = cx_iso - (exi[0] + exi[2]) / 2 * fi
    oyi = cy_iso - (exi[1] + exi[3]) / 2 * fi
    h.prims(proy["iso"]["vis"], "01-VISIBLE", (oxi, oyi, fi))
    lbl = "ISOMETRÍA" + ("" if ei == e else f" (ESC. {escala_txt(ei)})")
    h.texto(lbl, (cx_iso, cy_iso - hi * fi / 2 - 6), 3.5, A.MIDDLE_CENTER)

    # ---------------- notas
    notas = ["NOTAS: 1) Cotas en mm, medidas reales del conjunto. 2) Método de proyección ISO E (IRAM 4501).",
             "3) Corte A-A y detalles: hoja 2.  4) Especificaciones: hoja 3.  5) Rayado = etiqueta (fino: panel de",
             "instrucciones 108°; ancho: alas); oblea, estampilla IRAM, tarjeta AGC, faja, precinto y marcado: hoja 4."]
    for i, s_ in enumerate(notas):
        h.texto(s_, (h.fx0 + 4, h.fy0 + 12.5 - 4.5 * i), 2.5)
    return doc, dict(fmt=fmt, escala=e, k=k, T=Tf, detalles=detalles, masa=masa_vacio)


# =================================================================== detalles
# Hoja 2 (A2): columna del corte a la izquierda; grilla de detalles 3 × 2 a la derecha,
# el detalle A (válvula) ocupa dos celdas. Todos los círculos de un mismo tipo de celda
# tienen el mismo diámetro; cada detalle toma la mayor escala normalizada que entra.
H2_X_CORTE = 190.0
H2_W, H2_H = FORMATOS["A2"]


def _grilla_detalles(n=5):
    x0 = 25.0 + H2_X_CORTE
    x1 = H2_W - 10 - 4
    y0 = 10.0 + ROT_H + 4
    y1 = H2_H - 10 - 4
    filas = 2 if n <= 5 else 3
    cw, ch = (x1 - x0) / 3, (y1 - y0) / filas
    if n > 8:
        # 100 kg (fleje del medio): 3 × 3, A del mismo tamaño (con 3 filas la altura ya lo limita)
        slots = [(i % 3, i // 3, 1) for i in range(n)]
    else:
        # fila superior: A (doble) + B; las demás centradas según la cantidad restante (de a 3)
        resto = list(range(max(0, n - 2)))
        slots = [(0, 0, 2), (2, 0, 1)]
        for fi in range(1, filas):
            fila = resto[(fi - 1) * 3:fi * 3]
            slots += [((3 - len(fila)) / 2 + i, fi, 1) for i in range(len(fila))]
    celdas = [(x0 + cw * (c0 + nc / 2), y1 - ch * (fi + 0.5), cw * nc) for c0, fi, nc in slots]
    r_norm = min(cw / 2 - 12, ch / 2 - 20)
    r_doble = min(cw - 12, ch / 2 - 20) if n <= 8 else r_norm
    return celdas, r_norm, r_doble


def _escalar_detalles(D):
    celdas, r_norm, r_doble = _grilla_detalles(len(D))
    for i, d in enumerate(D):
        rp = r_doble if i == 0 else r_norm
        sd = AMPLIAC[-1]
        for cand in AMPLIAC:
            if d["r"] * cand[0] / cand[1] <= rp:
                sd = cand
                break
        d["escala"] = sd
        d["r"] = rp * sd[1] / sd[0]      # recorte ampliado para llenar el círculo
        d["rp"] = rp
        d["celda"] = celdas[i]
    return D


def definir_detalles(m, info):
    """Zonas a ampliar. origen: 'anterior' (vista de hoja 1) o 'corte' (hoja 2)."""
    r = info["recipiente"]
    v = info["valvula"]
    R = r["R"]
    D = []
    # A: válvula, manómetro y manijas
    xs0 = v["x_salida"] - 6
    xs1 = v["x_piv"] + (m.W + 0) * 0 + 0
    x_tip = max(xs1, 0)
    z0 = r["z_cuello"] - 4
    z1 = v["z_top"] + 2
    xa0 = min(v["x_salida"] - 10, -v["bw"] / 2 - 20)
    xa1 = min(R * 1.25, v["bw"] / 2 + 60 * v["s"])
    cA = ((xa0 + xa1) / 2, (z0 + z1) / 2)
    rA = max((xa1 - xa0) / 2, (z1 - z0) / 2) + 6
    if v["tipo"] == "G763":
        # válvula de carro: la palanca gira según X y se ve entera en la vista lateral
        y0, y1 = v["y_man"] - 4, v["y_tip"] + 4
        cA = (-(y0 + y1) / 2, (z0 + z1) / 2)
        rA = max((y1 - y0) / 2, (z1 - z0) / 2) + 6
        D.append(dict(letra="A", origen="lateral", c=cA, r=rA, titulo="Válvula, manómetro y palanca (vista lateral)",
                      ang_letra=150))
    else:
        D.append(dict(letra="A", origen="anterior", c=cA, r=rA, titulo=("Válvula, disco de seguridad y manijas" if m.familia == "co2" else "Válvula, manómetro y manijas"),
                      ang_letra=150))
    # B: cuello roscado y unión con la cúpula (corte)
    dn = r["dn"]
    cB = (dn / 2 * 0.6, (r["z_cuello"] + r["z_cupula"]) / 2 - 2)
    rB = max(dn * 0.5, (r["z_cuello"] - r["z_cupula"]) * 0.75 + 5)
    D.append(dict(letra="B", origen="corte", c=cB, r=rB,
                  titulo="Cuello roscado con muesca" if m.geo["tipo_fondo"] in ("concavo", "cupula") else
                  ("Cupla soldada" if m.familia == "rodante" else "Cuello roscado")))
    # C: unión cúpula-cuerpo (corte)
    if m.familia != "co2":
        t = m.geo["t"]
        rC = max(4 * t, 6.0)
        D.append(dict(letra="C", origen="corte", c=(R - t, r["z_union"]), r=rC,
                      titulo="Casquete con borde reducido y tope" if m.familia == "rodante" else "Bordón del cuerpo y cúpula"))
    # D: fondo
    g = m.geo
    if g["tipo_fondo"] == "concavo":
        cD = (R - 6, g["zf_borde"] * 0.7)
        rD = max(g["zf_borde"] + 6, 16)
        tit = "Fondo encastrado y pollera"
    elif g["tipo_fondo"] == "co2":
        cD = (R * 0.75, g.get("z_pie", 0) + R * 0.35)
        rD = R * 0.55
        tit = "Fondo y pie de apoyo"
    else:
        cD = (R - m.geo["t"], r["zb"])
        rD = max(6 * m.geo["t"], 12)
        tit = "Casquete inferior con borde reducido" if m.familia == "rodante" else "Bordón inferior y fondo"
    D.append(dict(letra="D", origen="corte", c=cD, r=rD, titulo=tit))
    # E: tobera / difusor / rueda
    if m.familia == "rodante":
        # vista propia de la punta de la manga (sin el cuerpo ni el rollo, que la tapan en la vista anterior):
        # válvula esférica con su palanca (cerrada, atravesada al caño) y tobera / lanza
        # vista lateral: la palanca de la válvula esférica apunta hacia adelante
        xn, zn = -info["valv_esf_y"], info["valv_esf"][1]
        z_bot = info["eje_tobera"][1]
        z_top = zn + 28 + 12
        D.append(dict(letra="E", origen="local", vista="lat_izq", marca="lateral", c_marca=(xn, zn),
                      c=(xn - 35, (z_bot + z_top) / 2), r=(z_top - z_bot) / 2 + 12,
                      piezas=("valvula_esferica", "tobera_campana", "lanza"), corte=None,
                      titulo="Válvula esférica con palanca y tobera", ang_letra=200))
    elif "tobera" in info:
        xt, zt = info["tobera"]
        rr = 45 if m.familia != "co2" else 80
        if m.W < 100:
            rr = 20
        tit = {"tobera_polvo": "Tobera y portatobera", "tobera_chorro": "Tobera de chorro pleno",
               "lanza_espuma": "Lanza espumígena", "lanza_k": "Lanza aplicadora clase K",
               "lanza_d": "Lanza de flujo suave", "difusor_brazo": "Difusor", "difusor_manga": "Difusor y soporte",
               "tobera_1kg": "Tobera"}.get(m.descarga, "Tobera")
        D.append(dict(letra="E", origen="anterior", c=(xt, zt), r=rr, titulo=tit, ang_letra=250))
    if m.familia == "rodante" and "soporte_tri" in info:
        # F: corte por el plano de un triángulo (vista lateral): la V con el caño del eje apoyado y el eje adentro;
        # G: lengüeta de la manija soldada al costado del cuerpo (vista anterior); H: fleje del soporte de manga
        # (corte horizontal, vista superior) con la manga apoyada
        a_t, xs, z_t, ys, u_a, s_fl, rce = info["soporte_tri"]
        u_max = u_a + (a_t / 4)
        cF = (-ys + u_max / 2 + 6, z_t + a_t / 2)
        D.append(dict(letra="F", origen="local", vista="lat_izq", marca="lateral", c_marca=cF, c=cF,
                      r=max(u_max + 14, a_t) / 2 + 12,
                      piezas=("soportes_eje", "portaeje", "eje_ruedas", "cuerpo", "fondo"), corte=("x", -xs - 3, -xs + 3),
                      titulo="Corte por el triángulo: caño del eje apoyado en la V", ang_letra=210))
        xm, R_ = info["xm"], info["recipiente"]["R"]
        z0, lf, lt, tf, wf = info["aplastado"]
        cG = ((R_ + xm) / 2 + 2, z0 + (lf + lt) / 2 + 6)
        D.append(dict(letra="G", origen="local", vista="anterior", marca="anterior", c_marca=cG, c=cG,
                      r=(lf + lt) / 2 + 22, piezas=("manija_carro", "cuerpo"), corte=None,
                      titulo="Lengüeta de la manija soldada al cuerpo", ang_letra=20))
        # H (e I en el 100 kg): perfil del fleje soldado al cuerpo, cortado por el centro (plano x = 0) y visto de
        # costado: base contra el cuerpo con un cordón corto arriba y otro abajo, la pata y la manga detrás
        fa, fe, fl_, fo, lb, _ = M.fleje_carro(m.codigo)
        rebanada = ("x", 0.0, lb / 2 + 32.0)          # mitad derecha: el corte (x = 0) queda adelante
        for letra, zz, tit in [("H", info["z_flejes"][0], "Fleje hacia afuera: soldadura (perfil)")] + \
                ([("I", sorted(info["z_flejes"])[1], "Fleje hacia adentro: soldadura (perfil)")]
                 if M.FLEJE_MEDIO.get(m.codigo) else []):
            cP = (-(R_ + 12.0), zz + fa / 2)
            D.append(dict(letra=letra, origen="local", vista="lat_izq", marca="lateral", c_marca=cP, c=cP, r=34.0,
                          piezas=("ganchos_manguera", "cuerpo"), corte=rebanada,
                          titulo=tit, ang_letra=160 if letra == "H" else 200, z_fleje=zz))
    return _escalar_detalles(D)


# =================================================================== HOJA 2
def hoja2(m, piezas, info, res1, doc, ox=0.0):
    fmt = "A2"
    h = Hoja(doc, fmt, ox)
    h.formato()
    nombres = ["cuerpo", "cupula", "fondo", "cuello", "soldaduras", "cano_pesca"]
    if m.familia == "co2":
        nombres.append("pie")
    proy_c, secc = V.corte_por_plano_xz(piezas, nombres)
    ext = V.extension(proy_c["vis"])
    alto_disp = h.fy1 - 30 - (h.fy0 + 24)
    ec = ESCALAS[-1]
    for cand in ESCALAS:
        kk = cand[1] / cand[0]
        if (ext[3] - ext[1]) / kk <= alto_disp and (ext[2] - ext[0]) / kk <= H2_X_CORTE - 70:
            ec = cand
            break
    kc = ec[1] / ec[0]
    fc = 1 / kc
    y_rot = h.rotulo(rotulo_base(m, fmt, ec, 2, "Corte y detalles", "Corte A-A del recipiente y detalles"))
    w_sec = (ext[2] - ext[0]) * fc + 14 + 34      # cota izquierda + dos cotas a la derecha
    cx = h.fx0 + (H2_X_CORTE - w_sec) / 2 + 14 - ext[0] * fc
    cy = h.fy0 + 24 + (alto_disp - (ext[3] - ext[1]) * fc) / 2 - ext[1] * fc
    Tc = (cx, cy, fc)
    h.prims(proy_c["vis"], "01-VISIBLE", Tc)
    colores = {"cuerpo": 45, "cupula": 135, "fondo": 135, "cuello": 45, "cano_pesca": 45, "pie": 135}
    for k_, polys in secc.items():
        for p in polys:
            pp = transformar_poly(p, (0, 0), fc, (cx, cy))
            solido = (k_ == "soldaduras") or ancho_medio(pp) < 1.2
            h.rayado(pp, angulo=0 if colores.get(k_, 45) == 45 else 90, esp=2.0, solido=solido)
    r = info["recipiente"]
    h.eje((cx, cy + ext[1] * fc - 5), (cx, cy + r["z_cuello"] * fc + 5))
    h.texto("CORTE A-A" + ("" if ec == res1["escala"] else f" ({escala_txt(ec)})"),
            (cx, cy + ext[3] * fc + 20), 7, A.MIDDLE_CENTER)
    # cotas del recipiente en el corte
    R = r["R"]
    zmin = ext[1]
    h.cota_lineal((cx - R * fc, cy + zmin * fc), (cx + R * fc, cy + zmin * fc),
                  (cx, cy + zmin * fc - 9), 0, kc, prefijo="%%c")
    xr_ = cx + R * fc
    h.cota_lineal((xr_, cy + zmin * fc), (cx + r["dn"] / 2 * fc, cy + r["z_cuello"] * fc),
                  (xr_ + 22, cy), 90, kc)
    h.cota_lineal((xr_, cy + r["z_union"] * fc), (cx + r["dn"] / 2 * fc, cy + r["z_cuello"] * fc),
                  (xr_ + 11, cy), 90, kc)
    if m.geo["tipo_fondo"] == "concavo":
        h.cota_lineal((cx - R * fc, cy + zmin * fc), (cx - (R - m.geo["t"]) * fc, cy + (m.geo["zf_borde"] + m.geo["tf"]) * fc),
                      (cx - R * fc - 9, cy), 90, kc)
    else:
        h.cota_lineal((cx - R * fc, cy + zmin * fc), (cx - R * fc, cy + r["zb"] * fc),
                      (cx - R * fc - 9, cy), 90, kc)
    h.cota_lineal((cx - r["dn"] / 2 * fc, cy + r["z_cuello"] * fc), (cx + r["dn"] / 2 * fc, cy + r["z_cuello"] * fc),
                  (cx, cy + r["z_cuello"] * fc + 5), 0, kc, prefijo="%%c")

    # ---------------- detalles
    detalles = res1["detalles"]
    proy_f = res1["proy"]["anterior"]
    pl_vis_f = V.a_polilineas(proy_f["vis"], 0.2)
    pl_oc_f = V.a_polilineas(proy_f["oc"], 0.2)
    proy_l = res1["proy"]["lat_izq"]
    pl_vis_l = V.a_polilineas(proy_l["vis"], 0.2)
    pl_oc_l = V.a_polilineas(proy_l["oc"], 0.2)
    pl_vis_c = V.a_polilineas(proy_c["vis"], 0.1)
    for d in detalles:
        xc, yc, cwi = d["celda"]
        xc += ox
        sd = d["escala"]
        s = sd[0] / sd[1]
        rp = d["rp"]
        dest = (xc, yc + 5)
        if d["origen"] == "anterior":
            vis = recortar_circulo(pl_vis_f, d["c"], d["r"])
            oc = recortar_circulo(pl_oc_f, d["c"], d["r"])
        elif d["origen"] == "lateral":
            vis = recortar_circulo(pl_vis_l, d["c"], d["r"])
            oc = recortar_circulo(pl_oc_l, d["c"], d["r"])
        elif d["origen"] == "local":
            # vista propia del detalle: sólo las piezas que importan (sin la rueda que las tapa) y, si corresponde,
            # una rebanada horizontal si el detalle la pide
            sols = []
            for k_ in d["piezas"]:
                if k_ not in piezas:
                    continue
                so = piezas[k_]
                if d["corte"] and d["corte"][0] == "x":              # rebanada vertical (plano de un triángulo)
                    _, xa, xb_ = d["corte"]
                    so = so.intersect(cq.Solid.makeBox(xb_ - xa, 4000, 4000, cq.Vector(xa, -2000, -2000)))
                elif d["corte"]:
                    za, zb_ = d["corte"]
                    so = so.intersect(cq.Solid.makeBox(4000, 4000, zb_ - za, cq.Vector(-2000, -2000, za)))
                if so.Volume() > 1e-6:
                    sols.append(so)
            pl_ = V.proyectar(cq.Compound.makeCompound(sols), d["vista"], tol=0.3, ocultas=True)
            vis = recortar_circulo(V.a_polilineas(pl_["vis"], 0.2), d["c"], d["r"])
            oc = recortar_circulo(V.a_polilineas(pl_["oc"], 0.2), d["c"], d["r"])
        else:
            vis = recortar_circulo(pl_vis_c, d["c"], d["r"])
            oc = []
            h.msp.add_circle((cx + d["c"][0] * fc, cy + d["c"][1] * fc), d["r"] * fc,
                             dxfattribs={"layer": "08-FINA"})
            rr_ = d["r"] * fc
            cc_ = (cx + d["c"][0] * fc, cy + d["c"][1] * fc)
            a0 = 45 if d["letra"] == "B" else 135
            cands = [(cc_[0] + (rr_ + rr) * math.cos(math.radians(a0 + da)),
                      cc_[1] + (rr_ + rr) * math.sin(math.radians(a0 + da)))
                     for rr in (4.0, 6.5, 9.0, 12.0, 15.0, 19.0, 24.0, 30.0) for da in range(0, 360, 20)]
            h.texto_libre(d["letra"], cands, 5, A.MIDDLE_CENTER)
        h.polilineas(transformar(oc, d["c"], s, dest), "02-OCULTA")
        h.polilineas(transformar(vis, d["c"], s, dest), "01-VISIBLE")
        if d["origen"] == "local" and d["letra"] == "E":
            (xa, ya, za), (xb, yb, zb) = info["eje_tobera_3d"]
            ej = [[(-ya, za), (-yb, zb)]]                                     # eje de la válvula y la tobera
        elif d["origen"] == "local" and d["letra"] in ("H", "I"):
            ej = []
        elif d["origen"] == "local" and d["letra"] == "G":
            ej = []
        elif d["origen"] == "local":
            c0 = (-info["yw"], info["Rw"])
            rr0 = info["portaeje"][0] / 2 + 8
            ej = [[(c0[0] - rr0, c0[1]), (c0[0] + rr0, c0[1])], [(c0[0], c0[1] - rr0), (c0[0], c0[1] + rr0)]]
        else:
            ej = [[a, b] for a, b in ejes(m, info, "anterior")] if d["origen"] == "anterior" else \
                ([[a, b] for a, b in ejes(m, info, "lat_izq")] if d["origen"] == "lateral" else
                 [[(0, info["recipiente"]["z_fondo"] - 3), (0, info["recipiente"]["z_cuello"] + 3)]])
        h.polilineas(transformar(recortar_circulo(ej, d["c"], d["r"]), d["c"], s, dest), "03-EJE")
        if d["origen"] == "local" and d["letra"] == "I":
            _fleje_medio_detalle(h, m, info, d, s, dest)
        elif d["origen"] == "local":
            _carro_detalle(h, m, info, d, s, dest)
        if d["origen"] == "corte":
            circ = sg.Point(d["c"]).buffer(d["r"], resolution=64)
            for k_, polys in secc.items():
                for p in polys:
                    q = p.intersection(circ)
                    if q.is_empty:
                        continue
                    qq = transformar_poly(q, d["c"], s, dest)
                    solido = (k_ == "soldaduras") or ancho_medio(qq) < 1.2
                    h.rayado(qq, angulo=0 if colores.get(k_, 45) == 45 else 90, esp=2.0, solido=solido)
            _roscas_y_soldaduras(h, m, info, d, s, dest)
        if d["letra"] == "A":
            # números de posición de los componentes de la válvula
            _, orden, _ = lista(m, piezas)
            anc = []
            for i, key in enumerate(orden):
                if key not in VALVULA:
                    continue
                lat = d["origen"] == "lateral"
                ax, az = ancla(key, piezas, info) if not lat else ancla_lateral(key, piezas)
                if math.hypot(ax - d["c"][0], az - d["c"][1]) > d["r"] * 0.95:
                    # pieza larga que sale del círculo (palanca, manija): vértice propio más alejado dentro del detalle
                    pts = [(-v.Y if lat else v.X, v.Z) for v in piezas[key].Vertices()]
                    pts = [q for q in pts if math.hypot(q[0] - d["c"][0], q[1] - d["c"][1]) < d["r"] * 0.8]
                    if not pts:
                        continue
                    ax, az = max(pts, key=lambda q: math.hypot(q[0] - d["c"][0], q[1] - d["c"][1]))
                anc.append((i + 1, key, dest[0] + (ax - d["c"][0]) * s, dest[1] + (az - d["c"][1]) * s))
            colocar_globos(h, anc, dest[0], dest[0] - rp - 7, dest[0] + rp + 7, dest[1] + rp, dest[1] - rp, 8.5)
        h.msp.add_circle(dest, rp, dxfattribs={"layer": "08-FINA"})
        h.texto(f"DETALLE {d['letra']} ({escala_txt(sd)})", (xc, dest[1] - rp - 6), 5, A.MIDDLE_CENTER)
        h.texto(d["titulo"], (xc, dest[1] - rp - 12), 3.5, A.MIDDLE_CENTER)
    return doc


def _carro_detalle(h, m, info, d, s, dest):
    """notas y símbolos de soldadura de los detalles F (portaeje) y G (extremo aplastado de la manija) del carro."""
    T = lambda x, z: (dest[0] + (x - d["c"][0]) * s, dest[1] + (z - d["c"][1]) * s)   # noqa: E731
    t = m.geo["t"]
    rp = d["rp"]
    if d["letra"] == "F":
        a_t, xs, z_t, ys, u_a, s_fl, rce = info["soporte_tri"]
        yw, Rw = info["yw"], info["Rw"]
        dpe, epe, lpe = info["portaeje"]
        # cordones (proceso de carros): el triángulo contra el cuerpo con un filete de cada lado a lo largo de todo el
        # cateto, y el caño en los flancos de arriba y de abajo de la V, de las dos caras (relleno negro, como B, C, D)
        cat = 4.0                                                # cateto del filete (chapa 4,75)
        cx0, cz0 = -yw, Rw                                       # centro del caño
        bead = [sg.box(-ys - 0.3, z_t, -ys + cat, z_t + a_t)]
        for ang in (135.0, 225.0):                               # puntos de apoyo del caño en los dos flancos
            da = math.degrees(cat / rce)
            arco = [(cx0 + rr * math.cos(math.radians(ang + k_ * da / 6)), cz0 + rr * math.sin(math.radians(ang + k_ * da / 6)))
                    for rr, ks in ((rce, range(-6, 7)), (rce + cat, range(6, -7, -1))) for k_ in ks]
            bead.append(sg.Polygon(arco))
        for b_ in bead:
            h.rayado(sg.Polygon([T(x_, z_) for x_, z_ in b_.exterior.coords]), solido=True)
        pw = T(-ys + cat / 2, z_t + a_t * 0.7)                   # cateto vertical de canto contra el cuerpo
        h.simbolo_soldadura(pw, (dest[0] - rp - 4, pw[1] + 10), lado=-1, proceso="135", todo_alrededor=False,
                            ambos=True)
        pt = T(cx0 + (rce + cat / 2) * math.cos(math.radians(135)), cz0 + (rce + cat / 2) * math.sin(math.radians(135)))
        pb = T(cx0 + (rce + cat / 2) * math.cos(math.radians(225)), cz0 + (rce + cat / 2) * math.sin(math.radians(225)))
        h.simbolo_soldadura(pt, (dest[0] - rp * 0.75, dest[1] - rp * 0.85), lado=-1, proceso="135",
                            todo_alrededor=False, ambos=True, flechas=(pb,))   # desde abajo: no cruza el caño
        pulg = '1"' if info.get("tam_carro") == 0 else '1¼"'
        h.nota_referencia(f"Caño {pulg} × {epe:.1f}".replace(".", ","), T(-yw + rce * 0.7, Rw - rce * 0.7),
                          (dest[0] + rp * 0.72, dest[1] - rp * 0.78), 2.5)   # a la derecha, lejos del título
        h.nota_referencia(f"Eje {'3/4' if info.get('eje_d', 25.4) < 20 else '1'}\" (montaje final)", T(-yw, Rw),
                          (dest[0] + rp * 0.35, dest[1] + rp + 5), 2.5)
        h.nota_referencia("Triángulo con V 90°, e4,75 (2)", T(-ys + u_a * 0.4, z_t + a_t * 0.45),
                          (dest[0] - rp * 0.95, dest[1] - rp * 0.3), 2.5)
    elif d["letra"] == "E":
        xn, zn = -info["valv_esf_y"], info["valv_esf"][1]          # vista lateral: x de la vista = -y
        h.nota_referencia("Válvula esférica", T(xn + 12, zn + 6), (dest[0] + rp * 0.6, dest[1] + rp * 0.95), 2.5)
        pc_ = info.get("palanca_c", (0.0, -(xn - 80), zn + 4))
        h.nota_referencia("Palanca (cerrada)", T(-pc_[1], pc_[2]), (dest[0] - rp * 0.3, dest[1] + rp * 0.95), 2.5)
        z_bot = info["eje_tobera"][1]
        h.nota_referencia("Lanza espumígena" if m.descarga == "lanza_espuma_rodante" else "Tobera cónica",
                          T(xn + 10, (zn + z_bot) / 2 - 20),
                          (dest[0] + rp * 0.55, dest[1] - rp * 0.6), 2.5)
    elif d["letra"] == "G":
        xm = info["xm"]
        R = info["recipiente"]["R"]
        z0, lf, lt, tf, wf = info["aplastado"]
        cat = 4.0
        h.rayado(sg.Polygon([T(R - 0.3, z0), T(R + tf, z0), T(R - 0.3, z0 - cat)]), solido=True)   # cordón de abajo
        pw = T(R + tf + 0.3, z0 + lf * 0.35)                      # lengüeta: filete en los dos lados largos y abajo
        h.simbolo_soldadura(pw, (dest[0] + rp * 0.75, dest[1] - rp * 0.95), lado=1, proceso="135",
                            todo_alrededor=False, ambos=True, flechas=(T(R + tf / 3, z0 - cat / 3),))
        h.nota_referencia(f"Lengüeta aplastada {_n(wf, 0)} × {_n(lf, 0)} × {_n(tf, 0)}",
                          T(R + tf / 2, z0 + lf * 0.7), (dest[0] + rp * 0.5, dest[1] - rp * 0.45), 2.5)
        h.nota_referencia(f"Transición {_n(lt, 0)}", T((R + tf + xm) / 2, z0 + lf + lt * 0.5),
                          (dest[0] + rp * 0.6, dest[1] + rp * 0.15), 2.5)
        h.nota_referencia('Manija 1" × 2,0', T(xm + 12.7 * 0.7, z0 + lf + lt + 12),
                          (dest[0] + rp * 0.45, dest[1] + rp * 0.85), 2.5)
        h.nota_referencia("Cuerpo", T(R - 3, z0 + lf + lt + 10), (dest[0] - rp * 0.9, dest[1] + rp * 0.6), 2.5)


    if d["letra"] == "H":
        _fleje_perfil_detalle(h, m, info, d, s, dest, adentro=False)


def _fleje_perfil_detalle(h, m, info, d, s, dest, adentro):
    """notas de los detalles H / I: perfil del fleje por el centro, con los dos cordones (arriba y abajo)."""
    T = lambda x, z: (dest[0] + (x - d["c"][0]) * s, dest[1] + (z - d["c"][1]) * s)   # noqa: E731
    rp = d["rp"]
    R = info["recipiente"]["R"]
    fa, fe, fl_, fo, lb, corte_f = M.fleje_carro(m.codigo)
    zz = d["z_fleje"]
    t_c = m.geo["t"]
    circ_ = sg.Point(d["c"]).buffer(d["r"] * 0.995)
    for poly_, ang_ in ((sg.box(-(R + fe), zz, -R, zz + fa), 0), (sg.box(-R, zz - 200, -R + t_c, zz + fa + 200), 90)):
        pc_ = poly_.intersection(circ_)                           # caras cortadas: fleje y pared del cuerpo
        if not pc_.is_empty:
            h.rayado(sg.Polygon([T(*q) for q in pc_.exterior.coords]), angulo=ang_, esp=1.5)
    cat = 3.0                                                     # cateto del cordón (chapa de 3,2)
    for z0, sg_ in ((zz + fa, 1.0), (zz, -1.0)):                  # cordón corto arriba y otro abajo, al centro
        h.rayado(sg.Polygon([T(-R, z0), T(-R, z0 + sg_ * cat), T(-(R + cat), z0)]), solido=True)
    pa, pb = T(-(R + cat / 3), zz + fa + cat / 3), T(-(R + cat / 3), zz - cat / 3)
    h.simbolo_soldadura(pa, (dest[0] + rp * 0.55, dest[1] + rp * 0.95), lado=1, proceso="135", todo_alrededor=False,
                        ambos=True, flechas=(pb,))
    h.nota_referencia("Cordones de 40, al centro", pb, (dest[0] + rp * 0.7, dest[1] - rp * 0.75), 2.5)
    h.nota_referencia(f"Fleje 40 × {_n(fe, 1)}, corte {_n(corte_f, 0)}", T(-(R + fe / 2), zz + fa * 0.3),
                      (dest[0] - rp - 3, dest[1] + rp * 0.8), 2.5)
    h.nota_referencia(f"Pata {_n(fl_, 0)}, oreja {_n(fo, 0)} hacia {'adentro' if adentro else 'afuera'}",
                      T(-(R + 22.0), zz + fa), (dest[0] - rp - 3, dest[1] + rp * 0.3), 2.5)
    h.nota_referencia("Cuerpo", T(-R + 1.0, zz + fa + 14.0), (dest[0] + rp * 0.8, dest[1] + rp * 0.45), 2.5)


def _fleje_medio_detalle(h, m, info, d, s, dest):
    """notas del detalle I: fleje del medio del 100 kg, hacia adentro (mismo perfil y la misma soldadura)."""
    _fleje_perfil_detalle(h, m, info, d, s, dest, adentro=True)


def _roscas_y_soldaduras(h, m, info, d, s, dest):
    proc = m.soldadura[0]
    r = info["recipiente"]
    T = lambda x, z: (dest[0] + (x - d["c"][0]) * s, dest[1] + (z - d["c"][1]) * s)
    circ = sg.Point(d["c"]).buffer(d["r"] * 0.999)
    if d["letra"] == "B":
        rosca = r["rosca"]
        mayor = {"M30x1,5": 30.0, "M22x1,5": 22.0}.get(rosca, None)
        if rosca.startswith("RBSP"):
            mayor = 75.184
        z0 = r["z_cupula"]
        z1 = r["z_cuello"]
        if mayor:
            # fondo de rosca interior: línea fina en el diámetro mayor (ISO 6410-1)
            for sx in (1,):
                ls = sg.LineString([(sx * mayor / 2, z0 - 1), (sx * mayor / 2, z1 - 1.0)]).intersection(circ)
                if not ls.is_empty:
                    cs = list(ls.coords)
                    h.linea(T(*cs[0]), T(*cs[-1]), "08-FINA")
        pt = T(r["bore"] / 2, z1 - (z1 - z0) * 0.35)
        h.nota_referencia(rosca.replace("x", "×"), pt, (pt[0] - 22, pt[1] + 16))
        # soldadura cuello-cúpula (filete, todo alrededor, MAG = 135)
        if m.familia != "co2":
            pw = T(r["dn"] / 2 + 0.6, r["z_cupula"] + 0.6)
            h.simbolo_soldadura(pw, (pw[0] + 14, pw[1] - 16), lado=1, proceso=proc)
    elif d["letra"] == "C":
        pw = T(r["R"] + 0.3, r["z_union"] + 0.8)
        h.simbolo_soldadura(pw, (pw[0] + 12, pw[1] + 14), lado=1, proceso=proc)
        t = m.geo["t"]
        x0_, y0_ = T(r["R"] - t / 2 - 2.5 * t, r["z_union"] - 4 * t)
        h.texto_libre(f"e = {_n(t)}", [(x0_ + dx_, y0_ + dy_) for dy_ in (0, -4, -8, -12, 4, 8)
                                       for dx_ in (0, -6, -12, -18)], 2.5, A.MIDDLE_CENTER)
    elif d["letra"] == "D" and m.familia != "co2":
        g = m.geo
        if g["tipo_fondo"] == "concavo":
            pw = T(r["R"] - g["t"] - 0.3, g["zf_borde"] + g["tf"] + 0.3)
            h.simbolo_soldadura(pw, (pw[0] - 10, pw[1] + 14), lado=-1, proceso=proc)
        else:
            pw = T(r["R"] + 0.3, r["zb"] - 0.8)
            h.simbolo_soldadura(pw, (pw[0] + 12, pw[1] - 14), lado=1, proceso=proc)


# =================================================================== HOJA 3
def _tabla(h, x0, y, filas, anchos, alto=5.5, hs=(2.5, 2.5), encabezado=None, max_lin=3, fondo=None, fondo_txt=None):
    """Tabla simple con celdas de línea media; devuelve la y inferior.
    Letra sólo de la serie IRAM 4503 (hs se lleva a la normalizada inferior, mínimo 1,8): lo que no entra en un
    renglón se parte en renglones de 1,8 y la fila crece lo necesario (nunca se achica ni se condensa la letra).
    fondo: color del título y de la fila de encabezado (láminas a color), con letra fondo_txt."""
    if encabezado:
        if fondo:
            h.relleno(sg.box(x0, y - alto, x0 + sum(anchos), y), fondo)
        h.rect(x0, y - alto, x0 + sum(anchos), y, "10-ROTULO")
        t = h.texto(encabezado, (x0 + sum(anchos) / 2, y - alto / 2), 3.5 if alto >= 4.9 else 2.5, A.MIDDLE_CENTER)
        if fondo and fondo_txt and t is not None:
            t.rgb = fondo_txt
        y -= alto
    for nf, fila in enumerate(filas):
        celdas = []
        for j, (val, w) in enumerate(zip(fila, anchos)):
            t = str(val)
            hj = altura_norm(hs[min(j, len(hs) - 1)])
            if ancho_texto(t, hj) > w - 3 and hj > 1.8:
                hj = 1.8 if ancho_texto(t, 2.5) > w - 3 else 2.5
            celdas.append((partir(t, w - 3, hj, max_lin), hj))
        alto_f = max([alto] + [(len(l) - 1) * hj * 1.3 + hj + 1.2 for l, hj in celdas])
        if fondo and nf == 0:
            h.relleno(sg.box(x0, y - alto_f, x0 + sum(anchos), y), (232, 232, 232))
        x = x0
        for j, ((lns, hj), w) in enumerate(zip(celdas, anchos)):
            h.rect(x, y - alto_f, x + w, y, "10-ROTULO")
            paso = hj * 1.3
            for k, ln in enumerate(lns):
                yy = y - alto_f / 2 + (len(lns) - 1) * paso / 2 - k * paso
                if j == 0:
                    h.texto(ln, (x + 1.5, yy), hj, A.MIDDLE_LEFT)
                else:
                    h.texto(ln, (x + w / 2, yy), hj, A.MIDDLE_CENTER)
            x += w
        y -= alto_f
    return y


FADESA_EXT = {"1 kg": "Extintor 1 kg Ø76 (válvula HZ) R1", "2,5 kg": "Extintor 2,5 kg válvula HZ R1",
              "5 kg": "Extintor 5 kg válvula HZ R1", "10 kg": "Extintor 10 kg HZ R1", "25 kg": "Extintor rodante 25 kg R1",
              "50 kg": "Extintor rodante 50 kg R1", "100 kg": "Extintor rodante 100 kg R1"}


def _fuente_valvula(m):
    tv = M.tipo_valvula(m)
    plano = FADESA_EXT.get(m.capacidad) if m.codigo.startswith("FL_MAT_ABC") else None
    plano = plano or {"F510": FADESA_EXT["1 kg"], "F192": FADESA_EXT["5 kg"], "G763": FADESA_EXT["50 kg"]}[tv]
    if m.familia == "rodante":
        return (f"Válvula {tv} y manómetro con cubremanómetro medidos a escala en el plano Fadesa «{plano}». "
                f"Tren de rodaje según IRAM 3550 tabla III (Fadesa no cumple la banda ≥ 50): ancho y profundidad "
                f"resultan de la trocha; altura del catálogo (catálogo entre paréntesis).")
    return (f"Válvula {tv}, manómetro, resorte, vástago, racor, manguera, tobera, suncho y caño de pesca medidos a "
            f"escala en el plano Fadesa «{plano}». Altura, ancho y profundidad resultan de esas piezas (catálogo "
            f"entre paréntesis).")


def hoja3(m, info, doc, ox=0.0, masa_vacio=None, piezas=None):
    h = Hoja(doc, "A3", ox)
    h.formato()
    h.rotulo(rotulo_base(m, "A3", None, 3, "Especificaciones y normas", "Datos técnicos y normativa aplicable"))
    ancho_izq, gut, ancho_der = 175.0, 12.0, 190.0
    x0 = h.fx0 + (h.fx1 - h.fx0 - (ancho_izq + gut + ancho_der)) / 2
    xn = x0 + ancho_izq + gut
    ytop = h.fy1 - 8
    h.texto(m.nombre.upper(), (x0 + ancho_izq / 2, ytop), 5, A.MIDDLE_CENTER)
    g = m.geo
    from . import agentes as AG
    ag = AG.agente(m)
    filas = []
    env = info.get("envolvente", {})
    for k, v in m.spec.items():
        if k == "Norma IRAM agente extintor" and ag["norma"].split()[-1] not in str(v):
            v = f"{ag['norma'].replace('IRAM ', '')} (catálogo: {v})"
        if k in env:
            # medida real del plano y la del catálogo: manuales con las piezas medidas en Fadesa; rodantes con el tren
            # de rodaje de la IRAM 3550 (trocha ≥ 400, banda ≥ 50; la altura es la del catálogo)
            vc = re.sub(r"(\d)\.(\d{3})\b", r"\1\2", str(v))  # «1.210» → «1210», como la medida del plano
            v = f"{_n(env[k], 0)} (catálogo: {vc})"
        filas.append((k, str(v)))
    if m.familia == "rodante":
        filas.append(("Trocha entre centros de rueda (mm)", f"{_n(info['track'], 0)} (IRAM 3550 tabla III: ≥ 400)"))
        filas.append(("Ancho de banda de la rueda (mm)", f"{_n(info['bw_w'], 0)} (IRAM 3550 tabla III: ≥ 50)"))
    if "Norma IRAM agente extintor" not in m.spec and ag["norma"] != "-":
        filas.append(("Norma IRAM agente extintor", ag["norma"].replace("IRAM ", "")))
    grado = ag["grado"] if len(ag["grado"]) < 40 else ag["grado"][:ag["grado"].find("(")].strip()
    filas.append(("Agente extintor (grado)", grado))
    filas.append(("Potencial extintor", ag["potencial"] if ag["potencial"] != "-" else "según ensayo de tipo"))
    filas.append(("Gas impulsor", ag["gas"]))
    filas.append(("Volumen interior del recipiente (dm³)", _n(g["vol_dm3"], 2)))
    filas.append(("Diámetro exterior del recipiente (mm)", _n(2 * g["R"])))
    filas.append(("Rosca de cuello", g["cuello"][2]))
    filas.append(("Soldadura del recipiente", "sin costura (cilindro)" if m.familia == "co2"
                  else f"{m.soldadura[1]}, proceso {m.soldadura[0]} (ISO 4063)"))
    y = _tabla(h, x0, ytop - 6, filas, [100, 75], encabezado="ESPECIFICACIONES TÉCNICAS")
    # verificación de masa
    if masa_vacio is not None:
        cap = float(m.capacidad.split()[0].replace(",", "."))
        cat = float(m.spec["Peso cargado (kg)"].replace(".", "").replace(",", "."))
        carga = cap  # polvo en kg; líquidos a 1 kg/l
        dif = 100 * (masa_vacio + carga - cat) / cat
        fm = [("Equipo vacío (suma de la lista de materiales)", f"{_n(masa_vacio, 2)} kg"),
              ("Carga nominal de agente" + (" (1 kg/l)" if m.capacidad.endswith("l") else ""), f"{_n(carga, 2)} kg"),
              ("Masa cargada calculada", f"{_n(masa_vacio + carga, 2)} kg"),
              ("Peso cargado según catálogo", f"{_n(cat, 2)} kg"),
              ("Diferencia", f"{dif:+.1f} %".replace(".", ","))]
        y = _tabla(h, x0, y - 6, fm, [100, 75], encabezado="VERIFICACIÓN DE MASA")
    yy = y - 6
    lineas = ["Fuente de especificaciones: catálogo técnico de referencia, " + m.fuente.replace("Catálogo ", "") + ".",
              "Geometría del recipiente: " + (m.geo_fuente + "." if m.geo_fuente != "derivado"
                                              else "derivada de capacidad y dimensiones totales."),
              "Masas calculadas con el volumen de cada sólido y la densidad del material de la lista.",
              _fuente_valvula(m)]
    lineas += ["OBSERVACIÓN: " + o for o in m.observaciones]
    for ln in lineas:
        for parte in _partir(ln, 80):
            h.texto(parte, (x0, yy), 2.5)
            yy -= 4.2
        yy -= 1.0
    # verificación contra la norma de producto (cláusula, requisito resumido, valor del plano, estado)
    if piezas is not None:
        from . import verificacion as VF
        tit, fv = VF.filas(m, info, piezas)
        fv = [("Cláusula", "Requisito (resumen)", "En el plano", "Estado")] + fv
        alto_v = min(4.2, max(3.1, (yy - 2 - (h.fy0 + 2)) / (len(fv) + 1)))    # nunca por debajo del recuadro
        _tabla(h, x0, yy - 2, fv, [22, 62, 70, 21], alto=alto_v, hs=(1.8, 1.8, 1.8, 1.8),
               encabezado=f"VERIFICACIÓN - {tit.upper()}")

    # columna derecha: normativa
    y = ytop
    h.texto("NORMATIVA APLICADA", (xn + ancho_der / 2, y), 5, A.MIDDLE_CENTER)
    y -= 9
    h.texto("Normas de producto (tabla de especificaciones)", (xn, y), 3.5)
    y -= 6
    for a, b in N.normas_producto(m):
        h.texto(f"{a}: IRAM {b}", (xn + 3, y), 2.5)
        y -= 4.5
    y -= 3
    h.texto("Normas de dibujo técnico", (xn, y), 3.5)
    y -= 6
    for num, tit, iso, aplica in N.DIBUJO:
        h.texto(f"{num} - {tit} ({iso})", (xn + 3, y), 2.5)
        y -= 4.0
        for linea in _partir(aplica, 100):
            h.texto(linea, (xn + 7, y), 1.8)
            y -= 3.0
        y -= 1.2
    proc = "sin soldadura: cilindro sin costura" if m.familia == "co2" else \
        f"símbolo de filete, todo alrededor; proceso {m.soldadura[0]} ({m.soldadura[1]}, ISO 4063)"
    h.texto(f"ISO 2553 - Representación simbólica de soldaduras: {proc}", (xn + 3, y), 1.8)
    y -= 4
    h.texto("ISO 2768-1 - Tolerancias generales: clase m (media) salvo indicación", (xn + 3, y), 1.8)
    y -= 5
    for linea in _partir(N.AVISO_NORMAS, 105):
        h.texto(linea, (xn + 3, y), 1.8)
        y -= 3.0
    return doc


def _partir(s, n):
    out, cur = [], ""
    for w in s.split():
        if len(cur) + len(w) + 1 > n:
            out.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        out.append(cur)
    return out


# =================================================================== todo
SEPARACION = 60.0  # mm entre láminas en el espacio modelo


def generar(m):
    """Un único dibujo por modelo: las 3 láminas lado a lado en el espacio modelo.
    Devuelve (piezas, info, doc, hojas, res1) con hojas = [(nombre, formato, ox)]."""
    piezas, info = M.construir(m)
    _bb = M.bbox(piezas)
    info["envolvente"] = {"Altura (mm)": _bb.zmax - _bb.zmin, "Ancho (mm)": _bb.xlen, "Profundidad (mm)": _bb.ylen}
    comp = M.compuesto(piezas)
    proy = {v: V.proyectar(comp, v if (v != "iso" or m.familia != "rodante") else "iso_carro", tol=0.5,
                           ocultas=(v != "iso")) for v in V.PLANO}
    doc = nuevo_doc()
    _, res1 = hoja1(m, piezas, info, proy, doc, 0.0)
    ox2 = FORMATOS[res1["fmt"]][0] + SEPARACION
    ox3 = ox2 + FORMATOS["A2"][0] + SEPARACION
    res1["proy"] = proy
    hoja2(m, piezas, info, res1, doc, ox2)
    hoja3(m, info, doc, ox3, res1["masa"], piezas)
    from .rotulado import hoja4
    ox4 = ox3 + FORMATOS["A3"][0] + SEPARACION
    hoja4(m, piezas, info, proy, doc, ox4)
    hojas = [("Hoja1_Conjunto", res1["fmt"], 0.0), ("Hoja2_Corte_Detalles", "A2", ox2),
             ("Hoja3_Especificaciones", "A3", ox3), ("Hoja4_Rotulado", "A2", ox4)]
    return piezas, info, doc, hojas, res1
