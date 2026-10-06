"""Planos de fabricación de recipientes ABC para venta como repuesto
(código FL_REC_ABC_<tamaño>).

Una lámina por recipiente, método ISO E:
  - vista anterior (A) acotada con tolerancias de fabricación,
  - CORTE A-A (plano de simetría) con espesores,
  - vista según flecha D (superior) con el cuello,
  - detalles B (cuello roscado y soldadura), C (unión cúpula-cuerpo) y
    D (fondo / unión fondo-cuerpo),
  - tabla de datos: capacidad, volumen, masa, espesores, material,
    presiones, rosca, tratamiento superficial y marcado.
"""

import math
import shapely.geometry as sg

from . import modelo3d as M
from . import vistas as V
from .catalogo import MODELOS
from .lamina import Hoja, nuevo_doc, ESCALAS, AMPLIAC, FORMATOS, ROT_W, ROT_H, A, escala_txt
from .lamina import recortar_circulo, transformar, transformar_poly, ancho_medio
from .planos import FECHA, DIBUJO, _roscas_y_soldaduras, _n, _tabla

PIEZAS_REC = ["cuerpo", "cupula", "fondo", "cuello", "varilla", "soldaduras"]
COLORES = {"cuerpo": 45, "cupula": 135, "fondo": 135, "cuello": 45}
ABC = ["FL_MAT_ABC_1kg", "FL_MAT_ABC_2.5kg", "FL_MAT_ABC_5kg", "FL_MAT_ABC_10kg",
       "FL_MAT_ABC_25kg", "FL_MAT_ABC_50kg", "FL_MAT_ABC_70kg", "FL_MAT_ABC_100kg"]


def codigo_rec(m):
    return m.codigo.replace("FL_MAT_", "FL_REC_")


def tolerancias(R, Htot, rodante):
    """Tolerancias de fabricación (criterio de los planos de recipiente de referencia)."""
    tD = "±0,5" if 2 * R <= 200 else ("±0,3" if 2 * R < 300 else "+3/-1")
    tH = "±0,5" if Htot <= 400 else ("±0,8" if Htot <= 800 else "±2")
    tC = "±0,3" if not rodante else "±0,5"
    return tD, tH, tC


def generar_recipiente(m, hojas=1):
    g = dict(m.geo)
    piezas, dr = M.recipiente(g, 0.0, costura=True)
    piezas = {k: v for k, v in piezas.items() if k in PIEZAS_REC}
    info = {"recipiente": dr}
    comp = M.compuesto(piezas)
    proy_a = V.proyectar(comp, "anterior", tol=0.4)
    proy_s = V.proyectar(comp, "superior", tol=0.4, ocultas=False)
    proy_c, secc = V.corte_por_plano_xz(piezas, PIEZAS_REC)
    exa = V.extension(proy_a["vis"])
    R = dr["R"]
    Htot = dr["z_cuello"] - dr["z_fondo"] if g["tipo_fondo"] != "concavo" else dr["z_cuello"]
    rod = m.familia == "rodante"

    # ---- escala y formato: vista A + corte + vista D en fila, detalles en columna derecha
    w_det = 120.0
    elegido = None
    for e in ESCALAS:
        k = e[1] / e[0]
        for fmt in ("A3", "A2"):
            W, H = FORMATOS[fmt]
            w_need = 3 * (2 * R / k) + 3 * 48 + w_det + 25
            h_need = (exa[3] - exa[1]) / k + 45 + 72
            if w_need <= W - 35 and h_need <= H - 20:
                elegido = (fmt, e, k)
                break
        if elegido:
            break
    fmt, e, k = elegido
    f = 1 / k
    doc = nuevo_doc()
    h = Hoja(doc, fmt)
    h.formato()
    W, H = FORMATOS[fmt]
    rot = dict(titulo=f"Recipiente {m.nombre.replace('Extintor ', '').replace(' sobre ruedas', ' rodante')}", subtitulo="Repuesto - recipiente vacío sin válvula",
               codigo=codigo_rec(m), hoja=1, hojas=hojas, escala=escala_txt(e),
               material="Chapa LAF IRAM-IAS U 500-05" if not rod else "Chapa LAC IRAM-IAS U 500-04",
               edicion="0", fecha=FECHA, dibujo=DIBUJO, reviso="", aprobo="", tipo_doc="Plano de fabricación",
               empresa="FLAMA S.A.")
    h.rotulo(rot)

    # ---- zona de vistas (a la izquierda de la columna de detalles), centrada
    zx0, zx1 = h.fx0 + 6, h.fx1 - w_det - 12
    zy0, zy1 = h.fy0 + 76, h.fy1 - 6
    wv = 2 * R * f
    hv = (exa[3] - exa[1]) * f
    gap = (zx1 - zx0 - 3 * wv) / 4
    cy0 = zy0 + (zy1 - zy0 - hv) / 2 - exa[1] * f          # piso de las vistas A y corte
    xA = zx0 + gap + wv / 2
    xC = xA + wv + gap
    xD = xC + wv + gap

    # vista anterior
    TA = (xA, cy0, f)
    h.prims(proy_a["oc"], "02-OCULTA", TA)
    h.prims(proy_a["vis"], "01-VISIBLE", TA)
    h.eje((xA, cy0 + (dr["z_fondo"] - 4) * f), (xA, cy0 + (dr["z_cuello"] + 4) * f))
    # corte A-A
    TC = (xC, cy0, f)
    h.prims(proy_c["vis"], "01-VISIBLE", TC)
    for k_, polys in secc.items():
        for p in polys:
            pp = transformar_poly(p, (0, 0), f, (xC, cy0))
            sol = k_ == "soldaduras" or ancho_medio(pp) < 1.2
            h.rayado(pp, angulo=0 if COLORES.get(k_, 45) == 45 else 90, esp=2.0, solido=sol)
    h.eje((xC, cy0 + (dr["z_fondo"] - 4) * f), (xC, cy0 + (dr["z_cuello"] + 4) * f))
    h.texto("CORTE A-A", (xC, cy0 + exa[3] * f + 20), 5, A.MIDDLE_CENTER)
    # vista según flecha D (superior)
    exs = V.extension(proy_s["vis"])
    yD = cy0 + (dr["z_cuello"] * f) - (exs[3]) * f
    TD = (xD, yD, f)
    h.prims(proy_s["vis"], "01-VISIBLE", TD)
    h.eje((xD - R * f - 4, yD), (xD + R * f + 4, yD))
    h.eje((xD, yD - R * f - 4), (xD, yD + R * f + 4))
    h.texto("D", (xD, yD + R * f + 10), 5, A.MIDDLE_CENTER)
    # flecha D sobre la vista anterior y traza del corte A-A
    ytop = cy0 + (dr["z_cuello"] + 6) * f
    h.linea((xA - wv * 0.35, ytop + 12), (xA - wv * 0.35, ytop + 2), "08-FINA")
    h._flecha((xA - wv * 0.35, ytop + 2), (0, -1))
    h.texto("D", (xA - wv * 0.35 - 3, ytop + 14), 5, A.MIDDLE_RIGHT)
    h.plano_corte((xD - R * f - 12, yD), (xD + R * f + 12, yD), "A", (0, 1))

    # ---- cotas con tolerancias (medidas reales)
    tD, tH, tC = tolerancias(R, Htot, rod)
    zf = dr["z_fondo"]
    yb = cy0 + zf * f
    ytc = cy0 + dr["z_cuello"] * f
    yu = cy0 + dr["z_union"] * f
    xl = xA - R * f
    h.cota_lineal((xl, yb), (xA - dr["dn"] / 2 * f, ytc), (xl - 18, yb), 90, k, texto=f"<>{tH}")
    if zf > 0.5:  # fondo cóncavo: altura total desde el apoyo
        h.cota_lineal((xl, cy0), (xA - dr["dn"] / 2 * f, ytc), (xl - 27, cy0), 90, k, texto=f"<>{tH}")
    h.cota_lineal((xl, yu), (xA - dr["dn"] / 2 * f, ytc), (xl - 9, yb), 90, k, texto=f"<>{tC}")
    h.cota_lineal((xl, yb - 2), (xA + R * f, yb - 2), (xA, yb - 10), 0, k, texto=f"%%c<>{tD}")
    h.cota_lineal((xA - dr["dn"] / 2 * f, ytc), (xA + dr["dn"] / 2 * f, ytc), (xA, ytc + 8), 0, k, prefijo="%%c")
    if g["tipo_fondo"] == "concavo":
        h.cota_lineal((xA + R * f, cy0), (xA + R * f, cy0 + (g["zf_borde"] + g["tf"]) * f), (xA + R * f + 9, cy0), 90, k,
                      texto="<>±0,2")
    else:
        h.cota_lineal((xA + R * f, yb), (xA + R * f, yu - (dr["z_union"] - dr["zb"]) * f), (xA + R * f + 9, yb), 90, k,
                      texto=f"<>{tC}")
        h.cota_lineal((xA + R * f, cy0 + dr["zb"] * f), (xA + R * f, yu), (xA + R * f + 18, yb), 90, k,
                      texto=f"<>{tH}")
    h.cota_lineal((xD - R * f, yD), (xD + R * f, yD), (xD, yD - R * f - 10), 0, k, texto=f"%%c<>{tD}")

    # ---- detalles en la columna derecha, sobre el rótulo
    detalles = [
        dict(letra="B", c=(dr["dn"] / 2 * 0.6, (dr["z_cuello"] + dr["z_cupula"]) / 2 - 2),
             r=max(dr["dn"] * 0.45, (dr["z_cuello"] - dr["z_cupula"]) * 0.75 + 5), titulo="Cuello roscado"),
        dict(letra="C", c=(R - g["t"], dr["z_union"]), r=max(4 * g["t"], 6.0), titulo="Unión cúpula-cuerpo"),
    ]
    if g["tipo_fondo"] == "concavo":
        detalles.append(dict(letra="D", c=(R - 6, g["zf_borde"] * 0.7), r=max(g["zf_borde"] + 6, 16),
                             titulo="Fondo y pollera"))
    else:
        detalles.append(dict(letra="D", c=(R - g["t"], dr["zb"]), r=max(6 * g["t"], 12), titulo="Unión fondo-cuerpo"))
    col_x = h.fx1 - w_det / 2 - 2
    col_y0, col_y1 = h.fy0 + ROT_H + 4, h.fy1 - 4
    ch = (col_y1 - col_y0) / 3
    rp = min(w_det / 2 - 8, ch / 2 - 13)
    pl_c = V.a_polilineas(proy_c["vis"], 0.1)
    for i, d in enumerate(detalles):
        sd = AMPLIAC[-1]
        for cand in AMPLIAC:
            if d["r"] * cand[0] / cand[1] <= rp:
                sd = cand
                break
        s = sd[0] / sd[1]
        d["r"] = rp / s
        dest = (col_x, col_y1 - ch * (i + 0.5) + 5)
        vis = recortar_circulo(pl_c, d["c"], d["r"])
        h.polilineas(transformar(vis, d["c"], s, dest), "01-VISIBLE")
        circ = sg.Point(d["c"]).buffer(d["r"], resolution=64)
        for k_, polys in secc.items():
            for p in polys:
                q = p.intersection(circ)
                if q.is_empty:
                    continue
                qq = transformar_poly(q, d["c"], s, dest)
                h.rayado(qq, angulo=0 if COLORES.get(k_, 45) == 45 else 90, esp=2.0,
                         solido=(k_ == "soldaduras" or ancho_medio(qq) < 1.2))
        ej = [[(0, dr["z_fondo"] - 3), (0, dr["z_cuello"] + 3)]]
        h.polilineas(transformar(recortar_circulo(ej, d["c"], d["r"]), d["c"], s, dest), "03-EJE")
        _roscas_y_soldaduras(h, m, info, d, s, dest)
        h.msp.add_circle(dest, rp, dxfattribs={"layer": "08-FINA"})
        h.texto(f"DETALLE {d['letra']} ({escala_txt(sd)})", (col_x, dest[1] - rp - 5), 3.5, A.MIDDLE_CENTER)
        h.texto(d["titulo"], (col_x, dest[1] - rp - 9.5), 2.5, A.MIDDLE_CENTER)
        # marca en el corte
        rr = d["r"] * f
        c0 = (xC + d["c"][0] * f, cy0 + d["c"][1] * f)
        h.msp.add_circle(c0, rr, dxfattribs={"layer": "08-FINA"})
        h.texto(d["letra"], (c0[0] + rr * 0.75 + 4, c0[1] + rr * 0.75 + 4), 5, A.MIDDLE_CENTER)

    # ---- datos del recipiente (tabla sobre el rótulo, a la izquierda)
    masa = sum(v.Volume() for kk, v in piezas.items()) * 1e-6 * 7.85
    s_ = m.spec
    datos = [("Capacidad nominal de agente", m.capacidad),
             ("Volumen interior", f"{_n(g['vol_dm3'], 2)} dm³"),
             ("Masa del recipiente (calculada)", f"{_n(masa, 2)} kg"),
             ("Espesor cuerpo / cúpula / fondo", f"{_n(g['t'], 2)} / {_n(g['td'], 2)} / {_n(g['tf'], 2)} mm"),
             ("Material", "Chapa LAF IRAM-IAS U 500-05" if not rod else "Chapa LAC IRAM-IAS U 500-04 (σf ≥ 265 MPa)"),
             ("Soldadura", "MAG 135, Arcal 21 (Ar + 8 % CO₂, M20)"),
             ("Presión de servicio / ensayo", f"{s_['Presión de servicio (MPa)']} / {s_['Presión de ensayo (MPa)']} MPa"),
             ("Rosca de cuello", g["cuello"][2]),
             ("Norma IRAM extintor", s_["Norma IRAM extintor"]),
             ("Tratamiento superficial", "según DOC-01 FLAMA"),
             ("Ensayo 100 %", "prueba hidráulica según DOC-02"),
             ("Marcado en cúpula", "FLAMA S.A. - N° serie - año" + (" - PE" if rod else "")),
             ("Verificación normativa", "hoja 2" if hojas > 1 else "-")]
    xt = h.fx0 + 4
    _tabla(h, xt, h.fy0 + 4 + 5.0 * len(datos), datos, [80, 70], alto=5.0, hs=(2.5, 2.5))
    notas = ["NOTAS:", "1) Cotas en mm; tolerancias no indicadas", "    según ISO 2768-m.",
             "2) Recipiente sin válvula ni agente.", "3) Cordones MAG continuos y estancos.",
             "4) Prueba hidráulica 100 % antes de pintar."]
    for i, t in enumerate(notas):
        h.texto(t, (xt + 158, h.fy0 + 60 - 5 * i), 2.5)
    return doc, fmt, dict(masa=masa, escala=e, piezas=piezas)


def modelos_abc():
    return [m for m in MODELOS if m.codigo in ABC]
