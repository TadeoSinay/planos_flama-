"""Planos de despiece FL_DES_<modelo>: vista isométrica explosionada por subconjunto con globos y lista
multinivel ligada al BOM (flama/bom.py, salida/bom/FLAMA_BOM.xlsx).

Separados de los planos de fabricación FL_MAT_* (no los reemplazan). Las piezas son los mismos sólidos del
modelo 3D; se desplazan por subconjunto: recipiente (S1) en su lugar con fondo, cúpula y cuello separados en
el eje; válvula (S2) arriba con sus piezas abiertas en altura y el caño de pesca al costado; dispositivo de
descarga (S3) a la izquierda; carro (S4) con ruedas hacia afuera y manija hacia atrás.

Globo = posición del plano FL_MAT (y sufijo del código BOM, p. ej. 07 -> ABC10-07). Lo que el modelo no
dibuja (juntas, resorte, carga, identificación, embalaje) figura en la lista con «—» en la columna globo.
"""

import os

import cadquery as cq

from . import modelo3d as M
from . import vistas as V
from . import bom as B
from .lamina import Hoja, nuevo_doc, A, ESCALAS
from .planos import FECHA, DIBUJO, _tabla
from .catalogo import MODELOS

NO_DIBUJAR = {"soldaduras"}
ESPEJO = {"rueda_izq": "rueda_der", "llanta_izq": "llanta_der"}   # se dibujan, el globo va en la derecha


def _bb(s):
    return s.BoundingBox()


def explotar(m, piezas):
    """Desplazamiento (dx, dy, dz) de cada pieza."""
    c = _bb(piezas["cuerpo"])
    R = (c.xmax - c.xmin) / 2
    g = max(25.0, 0.3 * R)
    d = {k: [0.0, 0.0, 0.0] for k in piezas}
    sub = {k: B.SUB.get(ESPEJO.get(k, k), 2) for k in piezas}
    # S1 recipiente
    top = c.zmax
    if "cupula" in piezas:
        d["cupula"][2] = c.zmax + g - _bb(piezas["cupula"]).zmin
        top = _bb(piezas["cupula"]).zmax + d["cupula"][2]
    if "cuello" in piezas:
        d["cuello"][2] = top + g - _bb(piezas["cuello"]).zmin
        top = _bb(piezas["cuello"]).zmax + d["cuello"][2]
    for k in ("fondo", "pie"):
        if k in piezas:
            d[k][2] = (c.zmin - g) - _bb(piezas[k]).zmax
    if "placas_refuerzo" in piezas:              # interior: se sacan hacia el frente para verlas
        d["placas_refuerzo"][1] = -(2.2 * R + g)
    # S2 válvula: arriba, abierta en altura
    val = [k for k in piezas if sub[k] == 2 and k != "cano_pesca" and k not in NO_DIBUJAR]
    if val:
        z0 = min(_bb(piezas[k]).zmin for k in val)
        base = top + 1.5 * g - z0
        for k in sorted(val, key=lambda k: _bb(piezas[k]).zmin):
            b = _bb(piezas[k])
            d[k][2] = base + (b.zmin - z0) * 0.9
        for k, (dx, dy, dz) in {"manometro": (0, -1.6, 0.3), "disco_seguridad": (0, -1.4, 0),
                                "pasador": (1.4, -0.6, 0), "manija_superior": (0.4, 0, 0.6),
                                "manija_inferior": (0.6, 0, 0), "eje": (-1.0, 0, 0.3),
                                "vastago": (0, 0, 0.25), "resorte": (0, 0, -0.3), "tuerca": (0, 0, 0.4),
                                "espiga": (0, 0, 0)}.items():
            if k in d:
                d[k][0] += dx * g
                d[k][1] += dy * g
                d[k][2] += dz * g
    if "cano_pesca" in piezas:
        d["cano_pesca"][0] = c.xmax + g - _bb(piezas["cano_pesca"]).xmin
    # S3 descarga: a la izquierda como subconjunto
    des = [k for k in piezas if sub[k] == 3]
    if des:
        xmax = max(_bb(piezas[k]).xmax for k in des)
        dx = (c.xmin - 1.2 * g) - xmax
        # carros: manga, válvula esférica y tobera van adelante (+Y), detrás del cuerpo en la isometría: se traen al
        # plano del eje y un poco hacia el observador para que se vean a la izquierda del recipiente
        y_rollo = ((_bb(piezas["manguera_enrollada"]).ymin + _bb(piezas["manguera_enrollada"]).ymax) / 2
                   if "manguera_enrollada" in piezas else None)
        for k in des:
            d[k][0] = dx
            if y_rollo is not None:
                d[k][1] = -y_rollo - g
        for k in ("racor",):
            if k in d:
                d[k][2] += 0.5 * g
    # S4 carro: el conjunto a la derecha del recipiente y del caño de pesca
    car = [k for k in piezas if sub[k] == 4]
    if car:
        x_lib = c.xmax + g + (_bb(piezas["cano_pesca"]).xlen + g if "cano_pesca" in piezas else 0)
        dx = x_lib + 0.6 * g - min(_bb(piezas[k]).xmin for k in car if k in ("rueda_izq", "llanta_izq", "manija_carro",
                                                                              "eje_ruedas", "soportes_eje"))
        for k in car:
            d[k][0] += dx
    for k in piezas:
        if sub[k] == 4:
            b = _bb(piezas[k])
            if k in ("rueda_der", "llanta_der", "rueda_izq", "llanta_izq"):
                d[k][0] = (1 if b.xmin > 0 else -1) * (1.8 if "rueda" in k else 0.9) * g
            elif k in ("manija_carro",):                 # manija y eje atrás (-Y); ganchos y pata adelante (+Y)
                d[k][0] += 1.2 * g
                d[k][1] = -1.2 * g
            elif k in ("soportes_eje",):
                d[k][1] = -1.1 * g
            elif k in ("arandelas_tope",):
                d[k][1] = -1.6 * g
            elif k in ("ganchos_manguera",):
                d[k][1] = 1.0 * g
            elif k in ("tercera_pata",):
                d[k][1] = 1.2 * g
    return d, sub, g


def _anclaje(s, lado):
    """Vértice del sólido más hacia el lado del globo en la isometría (queda sobre el contorno)."""
    pts = [V.proyectar_punto((v.X, v.Y, v.Z), "iso") for v in s.Vertices()]
    if not pts:
        bb = s.BoundingBox()
        return V.proyectar_punto(((bb.xmin + bb.xmax) / 2, (bb.ymin + bb.ymax) / 2, (bb.zmin + bb.zmax) / 2), "iso")
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    # punto medio entre el centro y el extremo del lado: cae sobre la pieza en piezas macizas y anillos
    ext = max(pts, key=lambda p: lado * p[0] - 0.15 * abs(p[1] - cy))
    return (0.35 * cx + 0.65 * ext[0], 0.35 * cy + 0.65 * ext[1]) if len(pts) > 2 else ext


def _repartir(ys, ymin, ymax, paso):
    """Reparte globos en una columna conservando el orden y una separación mínima."""
    out = []
    for y in ys:
        out.append(max(ymin, y) if not out else max(y, out[-1] + paso))
    if out and out[-1] > ymax:
        exceso = out[-1] - ymax
        out = [y - exceso for y in out]
        for i in range(len(out) - 2, -1, -1):
            out[i] = min(out[i], out[i + 1] - paso)
    return out


def lamina(m):
    piezas, info = M.construir(m)
    filas = B.bom_producto(m)
    from .planos import lista
    _, orden, _ = lista(m, piezas)
    pos = {k: i + 1 for i, k in enumerate(orden)}
    d, sub, g = explotar(m, piezas)
    mov = {k: s.translate(cq.Vector(*d[k])) for k, s in piezas.items() if k not in NO_DIBUJAR}
    comp = cq.Compound.makeCompound(list(mov.values()))
    proy = V.proyectar(comp, "iso", tol=0.4, ocultas=False)
    ex = V.extension(proy["vis"])
    cod = "FL_DES_" + m.codigo[7:]
    doc = nuevo_doc()
    h = Hoja(doc, "A2")
    h.formato()
    tabla_w = 190.0
    zona = (h.fx0 + 40, h.fy0 + 10, h.fx1 - tabla_w - 42, h.fy1 - 19)
    zw, zh = zona[2] - zona[0], zona[3] - zona[1]
    w, hh = ex[2] - ex[0], ex[3] - ex[1]
    esc = next(e for e in ESCALAS if w * e[0] / e[1] <= zw and hh * e[0] / e[1] <= zh)
    f = esc[0] / esc[1]
    ox = (zona[0] + zona[2]) / 2 - (ex[0] + ex[2]) / 2 * f
    oy = (zona[1] + zona[3]) / 2 - (ex[1] + ex[3]) / 2 * f
    T = (ox, oy, f)
    h.prims(proy["vis"], "01-VISIBLE", T)

    def P2(p):
        return (ox + p[0] * f, oy + p[1] * f)

    # globos: columna izquierda y derecha
    xc = (zona[0] + zona[2]) / 2
    items = []
    for k, s in mov.items():
        if k in ESPEJO or k not in pos:
            continue
        bb = s.BoundingBox()
        c = P2(V.proyectar_punto(((bb.xmin + bb.xmax) / 2, (bb.ymin + bb.ymax) / 2, (bb.zmin + bb.zmax) / 2),
                                 "iso"))
        lado = -1 if c[0] < xc else 1
        a = P2(_anclaje(s, lado))
        items.append((lado, a, pos[k], k))
    for lado in (-1, 1):
        col = sorted([it for it in items if it[0] == lado], key=lambda it: it[1][1])
        xg = (h.fx0 + 22) if lado < 0 else (zona[2] + 22)
        ys = _repartir([it[1][1] for it in col], h.fy0 + 15, h.fy1 - 26, 11)
        for it, y in zip(col, ys):
            h.globo(it[2], it[1], (xg, y), r=4.5)
    # rótulos de subconjunto (texto junto al grupo)
    for s_ in (1, 2, 3, 4):
        ks = [k for k in mov if sub[k] == s_]
        if not ks:
            continue
        pts = []
        for k in ks:
            bb = mov[k].BoundingBox()
            for x in (bb.xmin, bb.xmax):
                for y in (bb.ymin, bb.ymax):
                    for z in (bb.zmin, bb.zmax):
                        pts.append(P2(V.proyectar_punto((x, y, z), "iso")))
        fs = next(r for r in filas if r["nivel"] == 1 and r["sub"] == s_)
        etiqueta = f"S{s_} {B.NOMBRE_SUB[s_].upper()}"
        if fs["codigo"].startswith("FL_REC"):
            etiqueta += f" ({fs['codigo']})"
        x = sum(p[0] for p in pts) / len(pts)
        y = min(p[1] for p in pts) - 5 if s_ != 2 else max(p[1] for p in pts) + 3
        if s_ == 1 and "pie" not in ks and "fondo" not in ks:
            y = min(p[1] for p in pts) - 5
        if s_ == 3:
            h.texto(etiqueta, (max(p[0] for p in pts), max(y, h.fy0 + 4)), 3.5, A.MIDDLE_RIGHT)
        else:
            h.texto(etiqueta, (x, max(y, h.fy0 + 4)), 3.5, A.MIDDLE_CENTER)
    h.texto(f"DESPIECE - {m.nombre.upper()}", ((zona[0] + zona[2]) / 2, h.fy1 - 8), 7, A.MIDDLE_CENTER)
    h.texto(f"Isometría explosionada por subconjunto, escala {esc[0]}:{esc[1]}. Globo = posición del plano "
            f"{m.codigo} = código {P_cod(m, 'NN')}", ((zona[0] + zona[2]) / 2, h.fy1 - 15), 3.5, A.MIDDLE_CENTER)
    # lista de piezas multinivel (niveles 1 y 2) ligada al BOM
    xt = h.fx1 - tabla_w - 2
    filas_t = [("Glo.", "Código BOM", "Denominación", "Cant.", "Material")]
    for r in filas:
        if r["nivel"] == 1:
            filas_t.append(("", r["codigo"], r["desc"].upper(), "", ""))
        elif r["nivel"] == 2:
            suf = r["codigo"].split("-")[-1]
            glo = str(int(suf)) if suf.isdigit() else "—"
            cant = r["cant"]
            ct = (f"{cant:g}".replace(".", ",") if isinstance(cant, (int, float)) else "—") + \
                 ("" if r["um"] == "u" else " " + r["um"])
            filas_t.append((glo, r["codigo"], r["desc"], ct, r["mat"] or ""))
    alto = min(5.0, (h.fy1 - 8 - (h.fy0 + 51 + 30)) / (len(filas_t) + 1))
    y = _tabla(h, xt, h.fy1 - 4, filas_t, [10, 26, 82, 18, 54], alto=alto, hs=(2.5, 2.2, 2.0, 2.2, 1.8),
               encabezado=f"LISTA DE DESPIECE - BOM {m.codigo}")
    notas = ["NOTAS",
             "1) Lista completa con medidas, pesos, origen, operación y norma:",
             "    salida/bom/FLAMA_BOM.xlsx, hoja BOM_" + m.codigo + ".",
             "2) «—» = ítem no dibujado (internos de válvula, carga, identificación, embalaje).",
             "3) S1 en los ABC = recipiente FL_REC (mismo plano que el cilindro de venta suelta).",
             "4) Ruedas: se dibujan ambas, el globo señala la derecha (cantidad 2)."
             if any(k in mov for k in ESPEJO) else
             "4) Piezas en posición relativa de montaje; desplazadas sólo para mostrarlas."]
    for i, t in enumerate(notas):
        h.texto(t, (xt, y - 6 - 4.2 * i), 2.5 if i else 3.5)
    h.rotulo(dict(titulo="Despiece " + m.nombre.replace("Extintor ", ""), subtitulo="Vista explosionada y lista "
                  "multinivel (BOM)", codigo=cod, hoja=1, hojas=1, escala=f"{esc[0]}:{esc[1]}",
                  material="Ver lista", edicion="0", fecha=FECHA, dibujo=DIBUJO, reviso="", aprobo="",
                  tipo_doc="Plano de despiece", empresa="FLAMA S.A."))
    return cod, doc


def P_cod(m, pos):
    from .planos import codigo_pieza
    return codigo_pieza(m, 0)[:-2] + str(pos)


def generar(carpeta, codigos=None):
    import pymupdf
    from . import exportar as X
    os.makedirs(carpeta, exist_ok=True)
    total = pymupdf.open()
    for m in MODELOS:
        if codigos and m.codigo not in codigos:
            continue
        cod, doc = lamina(m)
        hojas = [("Lamina", "A2", 0.0)]
        X.preparar_layouts(doc, hojas)
        doc.saveas(os.path.join(carpeta, f"{cod}.dxf"))
        p = X.pdf_hojas(doc, hojas)
        p.set_metadata({"title": f"{cod} - Despiece {m.nombre}", "author": "FLAMA S.A."})
        p.save(os.path.join(carpeta, f"{cod}.pdf"))
        total.insert_pdf(p)
        print(cod, flush=True)
    if not codigos:
        total.save(os.path.join(carpeta, "FLAMA_despieces.pdf"))
