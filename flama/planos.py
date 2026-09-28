"""Generación de las láminas de cada modelo:
  Hoja 1 - Plano de conjunto: vistas anterior, superior y lateral izquierda
           (ISO E), isometría, cotas generales, números de posición y lista
           de piezas.
  Hoja 2 - Corte A-A del recipiente y detalles ampliados (zoom).
  Hoja 3 - Especificaciones técnicas y normativa citada.
"""

import math
import datetime
import shapely.geometry as sg

from . import modelo3d as M
from . import vistas as V
from . import normas as N
from .lamina import (Hoja, nuevo_doc, ESCALAS, AMPLIAC, FORMATOS, ROT_W, ROT_H, A,
                     escala_txt, recortar_circulo, transformar, transformar_poly, ancho_medio)

FECHA = "28/09/2026"
DIBUJO = "T. Sinay"

# denominación, material, observaciones (por clave de pieza)
PIEZAS = {
    "cuerpo": ("Cuerpo (virola) del recipiente", None, "costura longitudinal MIG"),
    "cupula": ("Cúpula del recipiente", None, None),
    "fondo": ("Fondo del recipiente", None, None),
    "cuello": ("Cuello roscado", "Acero", None),
    "cano_pesca": ("Caño de pesca (sifón)", "A definir", None),
    "espiga": ("Espiga roscada de válvula", "Latón forjado", None),
    "tuerca": ("Collarín de válvula", "Latón forjado", None),
    "cuerpo_valvula": ("Cuerpo de válvula", "Latón forjado", None),
    "vastago": ("Vástago", "A definir", None),
    "eje": ("Eje de palanca", "A definir", None),
    "manija_superior": ("Manija superior (accionamiento)", "A definir", None),
    "manija_inferior": ("Manija inferior (transporte)", "A definir", None),
    "pasador": ("Pasador de seguridad con anilla", "A definir", "con precinto"),
    "manometro": ("Manómetro indicador de presión", "-", "comercial"),
    "disco_seguridad": ("Disco de seguridad con tapón", "A definir", None),
    "racor": ("Racor de manguera", "A definir", None),
    "manguera": ("Manguera", "Caucho sintético", None),
    "tobera": ("Tobera", "A definir", None),
    "brazo_difusor": ("Brazo giratorio del difusor", "A definir", None),
    "difusor": ("Difusor (bocina)", "A definir", "aislante térmico"),
    "suncho": ("Suncho portamanguera", "A definir", None),
    "pie": ("Pie de apoyo", "A definir", None),
    "rueda_der": ("Rueda", "A definir", None),
    "eje_ruedas": ("Eje de ruedas", "A definir", None),
    "bastidor": ("Bastidor (caño Ø25,4)", "Acero", None),
    "sunchos_bastidor": ("Sunchos de fijación al bastidor", "Acero", None),
    "apoyo": ("Apoyo delantero", "Acero", None),
    "manguera_enrollada": ("Manguera (tramo enrollado)", "Caucho sintético", None),
    "soportes_manguera": ("Soportes de manguera", "Acero", None),
    "valvula_esferica": ("Válvula esférica", "A definir", None),
    "tobera_campana": ("Tobera campana", "A definir", None),
}
NO_LISTAR = {"soldaduras", "rueda_izq"}
VALVULA = {"espiga", "tuerca", "cuerpo_valvula", "vastago", "eje", "manija_superior",
           "manija_inferior", "pasador", "manometro", "racor", "disco_seguridad"}


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


def colocar_globos(h, anclas, x_eje, x_izq, x_der, y_max, y_min, paso_min=9.0):
    izq = sorted([a for a in anclas if a[2] < x_eje], key=lambda a: -a[3])
    der = sorted([a for a in anclas if a[2] >= x_eje], key=lambda a: -a[3])
    for grupo, xg in ((izq, x_izq), (der, x_der)):
        if not grupo:
            continue
        ys = []
        for j, a in enumerate(grupo):
            yy = min(a[3], y_max) if not ys else min(a[3], ys[-1] - paso_min)
            ys.append(yy)
        if ys[-1] < y_min:
            dsh = y_min - ys[-1]
            ys = [y + dsh for y in ys]
            for j in range(len(ys) - 2, -1, -1):
                if ys[j] < ys[j + 1] + paso_min:
                    ys[j] = ys[j + 1] + paso_min
        for a, yy in zip(grupo, ys):
            h.globo(a[0], (a[2], a[3]), (xg, yy))


def material_recipiente(m):
    g = m.geo
    if m.familia == "inox":
        return f"Chapa de acero inoxidable e={_n(g['t'])}"
    if m.familia == "co2":
        return f"Tubo de acero sin costura e={_n(g['t'])}"
    return f"Chapa de acero e={_n(g['t'])}"


def _n(v, dec=1):
    s = f"{v:.{dec}f}".rstrip("0").rstrip(".")
    return s.replace(".", ",")


def lista(m, piezas):
    filas, orden = [], []
    for k in piezas:
        if k in NO_LISTAR:
            continue
        nom, mat, obs = PIEZAS.get(k, (k, "A definir", None))
        cant = 2 if k == "rueda_der" else 1
        if k in ("cuerpo", "fondo", "cupula"):
            mat = material_recipiente(m)
            esp = {"cuerpo": m.geo["t"], "fondo": m.geo["tf"], "cupula": m.geo["td"]}[k]
            mat = mat.replace(f"e={_n(m.geo['t'])}", f"e={_n(esp, 2)}")
            if m.familia == "co2" and k == "cuerpo":
                nom, obs = "Cilindro sin costura con cuello integral", m.geo["cuello"][2].split(" (")[0]
        if k == "cuello":
            obs = m.geo["cuello"][2]
        orden.append(k)
        filas.append([len(orden), cant, nom, mat or "A definir", obs or ""])
    return filas, orden


def _elegir(m, piezas, info):
    """Elige formato y escala normalizada (ISO 5455) que permiten ubicar las
    tres vistas con sus cotas y globos."""
    H, W, D = m.H, m.W, m.D
    for e in ESCALAS:
        k = e[1] / e[0]
        for fmt in ("A3", "A2"):
            Wf, Hf = FORMATOS[fmt]
            ancho_disp = (Wf - 10 - ROT_W - 8) - (20 + 6)
            alto_disp = (Hf - 10 - 6) - (10 + 26)
            req_w = 40 + W / k + 22 + 20 + D / k + 6
            req_h = 14 + H / k + 26 + D / k + 18
            if req_w <= ancho_disp and req_h <= alto_disp:
                return fmt, e, k
    return "A1", ESCALAS[-1], ESCALAS[-1][1]


def rotulo_base(m, fmt, e, hoja, tipo, sub=""):
    return dict(titulo=m.nombre, subtitulo=sub or f"Agente: {m.agente}", codigo=m.codigo,
                hoja=hoja, hojas=3, escala=escala_txt(e) if e else "-", material="Ver lista de piezas",
                edicion="0", fecha=FECHA, dibujo=DIBUJO, reviso="", aprobo="",
                tipo_doc=tipo, empresa="FLAMA S.A.")


# =================================================================== HOJA 1
def hoja1(m, piezas, info, proy):
    fmt, e, k = _elegir(m, piezas, info)
    f = 1.0 / k
    doc = nuevo_doc()
    h = Hoja(doc, fmt)
    h.formato()
    y_rot = h.rotulo(rotulo_base(m, fmt, e, 1, "Plano de conjunto"))
    filas, orden = lista(m, piezas)
    h_fila = 5.0 if len(filas) <= 16 else 4.5
    y_lst = h.lista_piezas(filas, y_rot, h_fila)

    ext = {v: V.extension(proy[v]["vis"]) for v in ("anterior", "superior", "lat_izq")}
    fx0 = h.fx0
    x_front = fx0 + 4 + 40 - ext["anterior"][0] * f
    y_front = h.fy1 - 6 - 14 - ext["anterior"][3] * f
    Tf = (x_front, y_front, f)
    gap_x = 20
    x_lat = x_front + ext["anterior"][2] * f + 16 + gap_x - ext["lat_izq"][0] * f
    Tl = (x_lat, y_front, f)
    y_top = y_front + ext["anterior"][1] * f - 26 - ext["superior"][3] * f
    Tt = (x_front, y_top, f)

    for v, T in (("anterior", Tf), ("superior", Tt), ("lat_izq", Tl)):
        h.prims(proy[v]["oc"], "02-OCULTA", T)
        h.prims(proy[v]["vis"], "01-VISIBLE", T)

    R = info["recipiente"]["R"]
    zc = info["recipiente"]["z_cuello"]
    # ejes (sobresalen 5 mm del contorno)
    h.eje((x_front, y_front - 5), (x_front, y_front + zc * f + 5))
    h.eje((x_lat, y_front - 5), (x_lat, y_front + zc * f + 5))
    h.eje((x_front - R * f - 5, y_top), (x_front + R * f + 5, y_top))
    h.eje((x_front, y_top - R * f - 5), (x_front, y_top + R * f + 5))

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
        # trocha (vista superior)
        xw, bw = info["xw"], info["bw_w"]
        h.cota_lineal((x_front - (xw - bw / 2) * f, y_top + yw * f), (x_front + (xw - bw / 2) * f, y_top + yw * f),
                      (x_front, y_top + yw * f + Rw * f + 10), 0, k)
    else:
        # posición del suncho / tobera
        if "suncho_z" in info:
            zs = info["suncho_z"]
            h.cota_lineal((x_front + R * f, yb), (x_front + R * f, y_front + zs * f), (xr + 10, yb), 90, k)

    # ---------------- plano de corte A-A en la vista superior
    h.plano_corte((x_front - R * f - 14, y_top), (x_front + R * f + 14, y_top), "A", (0, 1))

    # ---------------- detalles marcados en vista anterior (ver hoja 2)
    detalles = definir_detalles(m, info)
    for d in detalles:
        if d["origen"] != "anterior":
            continue
        c = (x_front + d["c"][0] * f, y_front + d["c"][1] * f)
        h.msp.add_circle(c, d["r"] * f, dxfattribs={"layer": "08-FINA"})
        ang = math.radians(d.get("ang_letra", 45))
        h.texto(d["letra"], (c[0] + (d["r"] * f + 4) * math.cos(ang), c[1] + (d["r"] * f + 4) * math.sin(ang)),
                5, A.MIDDLE_CENTER)

    # ---------------- números de posición (globos) en vista anterior
    # (los componentes de la válvula se referencian en el detalle A, hoja 2)
    anclas = []
    for i, key in enumerate(orden):
        if key in VALVULA:
            continue
        ax, az = ancla(key, piezas, info)
        anclas.append((i + 1, key, x_front + ax * f, y_front + az * f))
    colocar_globos(h, anclas, x_front, xl - 33, xr + 20, yt - 2, yb + 6)

    # ---------------- isometría (columna derecha, sobre la lista de piezas)
    exi = V.extension(proy["iso"]["vis"])
    wi, hi = exi[2] - exi[0], exi[3] - exi[1]
    zona_w = ROT_W - 10
    zona_h = h.fy1 - 6 - (y_lst + 12)
    ei = e
    for cand in ESCALAS:
        kk = cand[1] / cand[0]
        if cand[1] / cand[0] >= k and wi / kk <= zona_w and hi / kk <= zona_h:
            ei = cand
            break
    else:
        ei = ESCALAS[-1]
    ki = ei[1] / ei[0]
    fi = 1 / ki
    cx_iso = h.fx1 - ROT_W / 2
    ox = cx_iso - (exi[0] + exi[2]) / 2 * fi
    oy = y_lst + 12 - exi[1] * fi
    h.prims(proy["iso"]["vis"], "01-VISIBLE", (ox, oy, fi))
    lbl = "ISOMETRÍA" + ("" if ei == e else f" ({escala_txt(ei)})")
    h.texto(lbl, (cx_iso, y_lst + 5), 3.5, A.MIDDLE_CENTER)

    # ---------------- notas
    notas = ["NOTAS: 1) Cotas en mm, medidas reales del conjunto. 2) Método de proyección ISO E (IRAM 4501).",
             "3) Corte A-A y detalles A a E: hoja 2.  4) Especificaciones técnicas y normas: hoja 3."]
    for i, s_ in enumerate(notas):
        h.texto(s_, (h.fx0 + 4, h.fy0 + 8.5 - 5 * i), 2.5)
    return doc, dict(fmt=fmt, escala=e, k=k, T=Tf, detalles=detalles)


# =================================================================== detalles
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
    D.append(dict(letra="A", origen="anterior", c=cA, r=rA, titulo=("Válvula, disco de seguridad y manijas" if m.familia == "co2" else "Válvula, manómetro y manijas"),
                  ang_letra=150))
    # B: cuello roscado y unión con la cúpula (corte)
    dn = r["dn"]
    cB = (dn / 2 * 0.6, (r["z_cuello"] + r["z_cupula"]) / 2 - 2)
    rB = max(dn * 0.5, (r["z_cuello"] - r["z_cupula"]) * 0.75 + 5)
    D.append(dict(letra="B", origen="corte", c=cB, r=rB, titulo="Cuello roscado"))
    # C: unión cúpula-cuerpo (corte)
    if m.familia != "co2":
        t = m.geo["t"]
        rC = max(4 * t, 6.0)
        D.append(dict(letra="C", origen="corte", c=(R - t, r["z_union"]), r=rC, titulo="Unión cúpula-cuerpo"))
    # D: fondo
    g = m.geo
    if g["tipo_fondo"] == "concavo":
        cD = (R - 6, g["zf_borde"] * 0.7)
        rD = max(g["zf_borde"] + 6, 16)
        tit = "Fondo y pollera"
    elif g["tipo_fondo"] == "co2":
        cD = (R * 0.75, g.get("z_pie", 0) + R * 0.35)
        rD = R * 0.55
        tit = "Fondo y pie de apoyo"
    else:
        cD = (R - m.geo["t"], r["zb"])
        rD = max(6 * m.geo["t"], 12)
        tit = "Unión fondo-cuerpo"
    D.append(dict(letra="D", origen="corte", c=cD, r=rD, titulo=tit))
    # E: tobera / difusor / rueda
    if m.familia == "rodante":
        xn, zn = info["valv_esf"]
        D.append(dict(letra="E", origen="anterior", c=(xn - 20, zn - 40), r=85, titulo="Válvula esférica y tobera",
                      ang_letra=200))
    elif "tobera" in info:
        xt, zt = info["tobera"]
        rr = 45 if m.familia != "co2" else 80
        if m.W < 100:
            rr = 20
        D.append(dict(letra="E", origen="anterior", c=(xt, zt), r=rr, titulo="Tobera", ang_letra=250))
    return D


# =================================================================== HOJA 2
def hoja2(m, piezas, info, res1):
    doc = nuevo_doc()
    fmt = "A2"
    h = Hoja(doc, fmt)
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
        if (ext[3] - ext[1]) / kk <= alto_disp and (ext[2] - ext[0]) / kk <= 190:
            ec = cand
            break
    kc = ec[1] / ec[0]
    fc = 1 / kc
    y_rot = h.rotulo(rotulo_base(m, fmt, ec, 2, "Corte y detalles", "Corte A-A del recipiente y detalles"))
    cx = h.fx0 + 30 + (-ext[0]) * fc
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
    h.texto("A-A" + ("" if ec == res1["escala"] else f" ({escala_txt(ec)})"),
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
    pl_vis_c = V.a_polilineas(proy_c["vis"], 0.1)
    x_zona0 = max(cx + (ext[2]) * fc + 50, h.fx0 + 200)
    x_zona1 = h.fx1 - 2
    y_zona1 = h.fy1 - 4
    y_zona0 = y_rot + 2
    n = len(detalles)
    ncol, nfil = 3, 2
    cw = (x_zona1 - x_zona0) / ncol
    ch = (y_zona1 - y_zona0) / nfil
    # el detalle A (válvula) ocupa dos columnas de la fila superior
    celdas, anchos = [], []
    slots = [(0, 0, 2), (2, 0, 1), (0, 1, 1), (1, 1, 1), (2, 1, 1), (1, 0, 1)]
    for i in range(n):
        c0, fi, nc = slots[i]
        celdas.append((x_zona0 + cw * (c0 + nc / 2), y_zona1 - ch * (fi + 0.5)))
        anchos.append(cw * nc)
    for d, (xc, yc), cwi in zip(detalles, celdas, anchos):
        rmax = min(cwi / 2 - 8, ch / 2 - 16)
        sd = AMPLIAC[-1]
        for cand in AMPLIAC:
            if d["r"] * cand[0] / cand[1] <= rmax:
                sd = cand
                break
        s = sd[0] / sd[1]
        rp = d["r"] * s
        dest = (xc, yc + 5)
        if d["origen"] == "anterior":
            vis = recortar_circulo(pl_vis_f, d["c"], d["r"])
            oc = recortar_circulo(pl_oc_f, d["c"], d["r"])
        else:
            vis = recortar_circulo(pl_vis_c, d["c"], d["r"])
            oc = []
            h.msp.add_circle((cx + d["c"][0] * fc, cy + d["c"][1] * fc), d["r"] * fc,
                             dxfattribs={"layer": "08-FINA"})
            if d["letra"] == "B":
                pl = (cx + d["c"][0] * fc + d["r"] * fc + 5, cy + d["c"][1] * fc + d["r"] * fc * 0.6)
            else:
                pl = (cx + (d["c"][0] - d["r"]) * fc - 5, cy + d["c"][1] * fc)
            h.texto(d["letra"], pl, 5, A.MIDDLE_CENTER)
        h.polilineas(transformar(oc, d["c"], s, dest), "02-OCULTA")
        h.polilineas(transformar(vis, d["c"], s, dest), "01-VISIBLE")
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
            _, orden = lista(m, piezas)
            anc = []
            for i, key in enumerate(orden):
                if key not in VALVULA:
                    continue
                ax, az = ancla(key, piezas, info)
                if math.hypot(ax - d["c"][0], az - d["c"][1]) > d["r"] * 0.95:
                    continue
                anc.append((i + 1, key, dest[0] + (ax - d["c"][0]) * s, dest[1] + (az - d["c"][1]) * s))
            colocar_globos(h, anc, dest[0], dest[0] - rp - 7, dest[0] + rp + 7, dest[1] + rp, dest[1] - rp, 8.5)
        h.msp.add_circle(dest, rp, dxfattribs={"layer": "08-FINA"})
        h.texto(f"{d['letra']} ({escala_txt(sd)})", (xc, dest[1] - rp - 5), 5, A.MIDDLE_CENTER)
        h.texto(d["titulo"], (xc, dest[1] - rp - 10.5), 2.5, A.MIDDLE_CENTER)
    return doc


def _roscas_y_soldaduras(h, m, info, d, s, dest):
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
        # soldadura cuello-cúpula (filete, todo alrededor, MIG = 131)
        if m.familia != "co2":
            pw = T(r["dn"] / 2 + 0.6, r["z_cupula"] + 0.6)
            h.simbolo_soldadura(pw, (pw[0] + 14, pw[1] - 16), lado=1)
    elif d["letra"] == "C":
        pw = T(r["R"] + 0.3, r["z_union"] + 0.8)
        h.simbolo_soldadura(pw, (pw[0] + 12, pw[1] + 14), lado=1)
        t = m.geo["t"]
        h.texto(f"e = {_n(t)}", T(r["R"] - t / 2 - 2.5 * t, r["z_union"] - 4 * t), 2.5, A.MIDDLE_CENTER)
    elif d["letra"] == "D" and m.familia != "co2":
        g = m.geo
        if g["tipo_fondo"] == "concavo":
            pw = T(r["R"] - g["t"] - 0.3, g["zf_borde"] + g["tf"] + 0.3)
            h.simbolo_soldadura(pw, (pw[0] - 10, pw[1] + 14), lado=-1)
        else:
            pw = T(r["R"] + 0.3, r["zb"] - 0.8)
            h.simbolo_soldadura(pw, (pw[0] + 12, pw[1] - 14), lado=1)


# =================================================================== HOJA 3
def hoja3(m, info):
    doc = nuevo_doc()
    h = Hoja(doc, "A3")
    h.formato()
    y_rot = h.rotulo(rotulo_base(m, "A3", None, 3, "Especificaciones y normas",
                                 "Datos técnicos y normativa aplicable"))
    # escala no aplicable en hoja de datos: se indica "-"
    x0 = h.fx0 + 8
    y = h.fy1 - 12
    h.texto(f"{m.nombre.upper()} - ESPECIFICACIONES", (x0, y), 5)
    y -= 10
    filas = [(k, str(v)) for k, v in m.spec.items()]
    g = m.geo
    filas.append(("Volumen interior del recipiente (dm³)", _n(g["vol_dm3"], 2)))
    filas.append(("Diámetro exterior del recipiente (mm)", _n(2 * g["R"])))
    filas.append(("Rosca de cuello", g["cuello"][2]))
    col1, col2 = 95, 80
    for i, (a, b) in enumerate(filas):
        yy = y - 6 * i
        h.rect(x0, yy - 6, x0 + col1, yy, "10-ROTULO")
        h.rect(x0 + col1, yy - 6, x0 + col1 + col2, yy, "10-ROTULO")
        h.texto(a, (x0 + 1.5, yy - 3), 2.5, A.MIDDLE_LEFT)
        h.texto(b, (x0 + col1 + col2 / 2, yy - 3), 2.5 if len(b) < 30 else 2.0, A.MIDDLE_CENTER)
    y_fin_tabla = y - 6 * len(filas)
    yy = y_fin_tabla - 8
    lineas = ["Fuente de especificaciones: catálogo técnico de referencia, " + m.fuente.replace("Catálogo ", "") + ".",
              "Geometría del recipiente: " + (m.geo_fuente + "." if m.geo_fuente != "derivado"
                                              else "derivada de capacidad y dimensiones totales.")]
    lineas += ["OBSERVACIÓN: " + o for o in m.observaciones]
    for ln in lineas:
        for parte in _partir(ln, 78):
            h.texto(parte, (x0, yy), 2.5)
            yy -= 4.5
        yy -= 1.5

    # columna derecha: normativa
    xn = x0 + col1 + col2 + 12
    y = h.fy1 - 12
    h.texto("NORMAS DE PRODUCTO (según tabla de especificaciones)", (xn, y), 3.5)
    y -= 7
    for a, b in N.normas_producto(m):
        h.texto(f"{a}: IRAM {b}", (xn + 2, y), 2.5)
        y -= 5
    y -= 4
    h.texto("NORMAS DE DIBUJO TÉCNICO APLICADAS", (xn, y), 3.5)
    y -= 7
    for num, tit, iso, aplica in N.DIBUJO:
        h.texto(f"{num} ({iso}) - {tit}", (xn + 2, y), 2.5)
        y -= 4.2
        for linea in _partir(aplica, 88):
            h.texto(linea, (xn + 6, y), 2.0)
            y -= 3.4
        y -= 1.2
    for num, tit, apl in (N.SOLDADURA, N.TOLERANCIAS):
        h.texto(f"{num} - {tit}: {apl}", (xn + 2, y), 2.5 if len(apl) < 60 else 2.0)
        y -= 5
    y -= 2
    for linea in _partir(N.AVISO_NORMAS, 95):
        h.texto(linea, (xn + 2, y), 2.0)
        y -= 3.4
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
def generar(m):
    piezas, info = M.construir(m)
    comp = M.compuesto(piezas)
    proy = {v: V.proyectar(comp, v, tol=0.5, ocultas=(v != "iso")) for v in V.VISTAS}
    d1, res1 = hoja1(m, piezas, info, proy)
    res1["proy"] = proy
    d2 = hoja2(m, piezas, info, res1)
    d3 = hoja3(m, info)
    return piezas, info, [d1, d2, d3], res1
