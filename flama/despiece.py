"""Planos de despiece FL_DES_<modelo>: vista isométrica explosionada por subconjunto con globos y lista
multinivel ligada al BOM (flama/bom.py, salida/bom/FLAMA_BOM.xlsx).

Separados de los planos de fabricación FL_MAT_* (no los reemplazan). Las piezas son los mismos sólidos del
modelo 3D; se desplazan por subconjunto y cada pieza sólo a lo largo de su eje de montaje: recipiente (S1) en su
lugar con fondo, cúpula y cuello separados en el eje; válvula (S2) arriba con sus piezas abiertas en altura y el
caño de pesca (con su filtro) al costado; dispositivo de descarga (S3) a la izquierda; carro (S4) a la derecha, con
portaeje, chapas, arandelas, llantas y cubiertas abiertas sobre el eje de las ruedas, la manija subiendo sobre sus
patas (con sus extremos aplastados), los ganchos hacia adelante y la pata a lo largo de su soldadura, lo justo para que
la rueda no la tape. Los grupos se separan midiendo su extensión en la isometría. El punto de cada globo cae sobre la
parte visible de su pieza (z-buffer), la guía evita cruzar otras piezas y dos guías nunca se cruzan. Los rótulos
S1-S4 van en el lugar libre más cercano a la pieza principal de cada grupo, sin tocar líneas, globos, guías ni otros
textos y más cerca de su grupo que de otro (en dos renglones si hace falta). A2, o A1 si a 1:5 no entra (carros).

Globo = posición del plano FL_MAT (y sufijo del código BOM, p. ej. 07 -> ABC10-07). Lo que el modelo no
dibuja (juntas, resorte, carga, identificación, embalaje) figura en la lista con «—» en la columna globo.
"""

import math
import os

import cadquery as cq
import shapely
import shapely.geometry as sg

from . import modelo3d as M
from . import vistas as V
from . import bom as B
from .lamina import Hoja, nuevo_doc, A, ESCALAS, ancho_texto
from .planos import FECHA, DIBUJO, _tabla
from .catalogo import MODELOS

NO_DIBUJAR = {"soldaduras"}
ESPEJO = {"rueda_izq": "rueda_der", "llanta_izq": "llanta_der"}   # se dibujan, el globo va en la derecha
ESPEJO_INV = {v: (k,) for k, v in ESPEJO.items()}


def _bb(s):
    return s.BoundingBox()


_RAIZ2 = math.sqrt(2.0)


def _pts(s):
    """vértices de la malla del sólido (para medir su extensión real en la isometría)."""
    return [(v.x, v.y) for v in s.tessellate(2.0, 0.6)[0]]


def _silueta(s, off):
    """Contorno del sólido desplazado `off` en la isometría (mm reales): unión de sus triángulos proyectados."""
    vs, tr = s.tessellate(2.0, 0.6)
    q = [V.proyectar_punto((v.x + off[0], v.y + off[1], v.z + off[2]), "iso") for v in vs]
    tri = [sg.Polygon([q[a], q[b], q[c]]) for a, b, c in tr]
    return shapely.union_all([t for t in tri if t.area > 1e-6]).buffer(0)


def _vx(keys, malla, d, extra=(0.0, 0.0)):
    """(mín, máx) de la coordenada horizontal de la isometría (x + y)/√2 de las piezas desplazadas."""
    vs = [(x + d[k][0] + extra[0] + y + d[k][1] + extra[1]) / _RAIZ2 for k in keys for x, y in malla[k]]
    return min(vs), max(vs)


def explotar(m, piezas):
    """Desplazamiento (dx, dy, dz) de cada pieza. Los grupos se separan midiendo su extensión en la isometría
    (no sólo en X), así ningún subconjunto se monta sobre otro."""
    c = _bb(piezas["cuerpo"])
    R = (c.xmax - c.xmin) / 2
    g = max(25.0, 0.3 * R)
    d = {k: [0.0, 0.0, 0.0] for k in piezas}
    sub = {k: B.SUB.get(ESPEJO.get(k, k), 2) for k in piezas}
    malla = {k: _pts(s_) for k, s_ in piezas.items() if k not in NO_DIBUJAR}
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
    # S2 válvula: arriba, abierta en altura (el caño de pesca y su filtro, que van dentro del cuerpo, al costado)
    interiores = ("cano_pesca", "filtro_pesca")
    val = [k for k in piezas if sub[k] == 2 and k not in interiores and k not in NO_DIBUJAR]
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
    s1 = [k for k in malla if sub[k] == 1]
    ints = [k for k in interiores if k in malla]
    if ints:                                      # a la derecha del recipiente, con el filtro en su punta
        dxi = (_vx(s1, malla, d)[1] + 0.6 * g - _vx(ints, malla, d)[0]) * _RAIZ2
        for k in ints:
            d[k][0] += dxi
    # S3 descarga: a la izquierda como subconjunto
    des = [k for k in piezas if sub[k] == 3 and k in malla]
    if des:
        # carros: manga, válvula esférica y tobera van adelante (+Y), detrás del cuerpo en la isometría: se traen al
        # plano del eje y un poco hacia el observador para que se vean a la izquierda del recipiente
        y_rollo = ((_bb(piezas["manguera_enrollada"]).ymin + _bb(piezas["manguera_enrollada"]).ymax) / 2
                   if "manguera_enrollada" in piezas else None)
        for k in des:
            if y_rollo is not None:
                d[k][1] = -y_rollo - g
        for k in ("racor",):
            if k in d:
                d[k][2] += 0.5 * g
        dx3 = (_vx(s1, malla, d)[0] - 0.8 * g - _vx(des, malla, d)[1]) * _RAIZ2
        for k in des:
            d[k][0] += dx3
    # S4 carro: el conjunto a la derecha del recipiente y del caño de pesca. Dentro del grupo, todo lo que va sobre el
    # eje se abre sólo a lo largo del eje (X): portaeje y chapas en su lugar, arandela interior, llanta, cubierta y
    # arandela exterior hacia afuera; la manija sube a lo largo de sus patas (sale de sus extremos soldados),
    # los ganchos salen hacia adelante a lo largo de sus brazos y la pata baja.
    car = [k for k in piezas if sub[k] == 4]
    if car:
        loc = {k: [0.0, 0.0, 0.0] for k in car}
        for k in car:
            sx = 1 if _bb(piezas[k]).xmin > 0 else -1
            if k.startswith("llanta"):
                loc[k][0] = sx * 1.3 * g
            elif k.startswith("rueda"):
                loc[k][0] = sx * 2.0 * g
            elif k == "manija_carro":
                loc[k][2] = 0.8 * g
            elif k == "ganchos_manguera":
                loc[k][1] = 0.8 * g
            elif k == "tercera_pata":
                loc[k][2] = -0.8 * g
        if "tercera_pata" in loc:
            # la pata se abre a lo largo de su soldadura (vertical); como va adelante y abajo, en la isometría la tapa
            # la rueda derecha: se toma el menor corrimiento (vertical y, si hace falta, hacia adelante, su normal)
            # con el que se ve entera, sin tocar ninguna otra pieza del carro
            otras = shapely.union_all([_silueta(piezas[k], loc[k]) for k in car
                                       if k != "tercera_pata" and k not in NO_DIBUJAR]).buffer(0.25 * g)
            cands = sorted(((fy, fz) for fz in (-0.8, -1.5, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0)
                            for fy in (0.0, 0.5, 1.0, 1.5, 2.0)), key=lambda c: (abs(c[0]) + abs(c[1]), -c[1]))
            for fy, fz in cands:
                cand = [0.0, fy * g, fz * g]
                if not _silueta(piezas["tercera_pata"], cand).intersects(otras):
                    loc["tercera_pata"] = cand
                    break
            else:
                from .lamina import AVISOS
                AVISOS.append(f"{m.codigo}: la tercera pata queda tapada en el despiece")
        for k in car:
            d[k] = list(loc[k])
        resto = s1 + ints                          # el carro va abajo: se separa del recipiente y del caño de pesca
        v_min = _vx([k for k in car if k in malla], malla, d)[0]
        if "arandelas_tope" in malla:
            v_min = min(v_min, _vx(["arandelas_tope"], malla, d, (-2.8 * g, 0.0))[0])
        dx4 = (_vx(resto, malla, d)[1] + 0.8 * g - v_min) * _RAIZ2
        for k in car:
            d[k][0] += dx4
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


def _anclaje_visible(reg, lado, margen):
    """Punto del globo dentro de la parte visible de la pieza (mm reales de la isometría): en la parte visible más
    grande, retirado `margen` del contorno y corrido hacia el lado del globo; None si la pieza no se ve."""
    if reg is None or reg.is_empty:
        return None
    from shapely.ops import polylabel
    parte = max(getattr(reg, "geoms", [reg]), key=lambda q: q.area)
    adentro = parte.buffer(-margen)
    if adentro.is_empty:
        adentro = parte
    adentro = max(getattr(adentro, "geoms", [adentro]), key=lambda q: q.area)
    c = polylabel(adentro, tolerance=margen / 4)
    pts = list(adentro.exterior.coords)
    ext = max(pts, key=lambda p: lado * p[0] - 0.15 * abs(p[1] - c.y))
    for t in (0.65, 0.5, 0.35, 0.2, 0.0):
        q = sg.Point(c.x + t * (ext[0] - c.x), c.y + t * (ext[1] - c.y))
        if adentro.contains(q):
            return (q.x, q.y)
    return (c.x, c.y)


def _punto_guia(a0, reg, k, ks_v, vis_p, arbol_v, guias, fin, mismo=()):
    """Punto de la guía sobre la pieza (mm de papel): entre el anclaje propuesto y otros puntos de su parte visible,
    el que deja la guía hasta el globo (`fin`) sin cruzar otras piezas ni otras guías; a igualdad, el más cercano al
    propuesto."""
    if reg is None or reg.is_empty:
        return a0
    adentro = reg.buffer(-0.6)
    if adentro.is_empty:
        adentro = reg
    x0, y0, x1, y1 = adentro.bounds
    paso = max(1.5, math.sqrt(max(adentro.area, 1.0) / 80.0))
    cand = [a0]
    yy = y0 + paso / 2
    while yy < y1:
        xx = x0 + paso / 2
        while xx < x1:
            cand.append((xx, yy))
            xx += paso
        yy += paso
    from shapely.prepared import prep
    pre = prep(adentro)
    cand = [a0] + [c for c in cand[1:] if pre.contains(sg.Point(c))]

    borde = reg.boundary

    def costo(p):
        # cruzar una pieza se admite (es habitual en una explosionada) pero cuesta; cruzar otra guía, mucho más;
        # alejarse del punto propuesto o quedar sobre el borde de la pieza, poco
        ln = sg.LineString([p, fin])
        c = 0.0
        for i in arbol_v.query(ln):
            kk = ks_v[i]
            if kk == k or kk in mismo:
                continue
            lx = ln.intersection(vis_p[kk]).length
            if lx > 0.05:
                c += 25.0 + lx
        c += sum(60.0 for gl in guias if ln.crosses(gl))
        return c + 0.4 * math.dist(p, a0) + 3.0 * (3.0 - min(3.0, borde.distance(sg.Point(p))))
    return min(cand, key=costo)


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
    if "arandelas_tope" in piezas:
        # las 4 arandelas se abren por separado sobre el eje: la interior junto al portaeje, la exterior afuera
        xw_ = info.get("xw", 0.0)
        partes = []
        for so in piezas["arandelas_tope"].Solids():
            bx = so.BoundingBox()
            xc_ = (bx.xmin + bx.xmax) / 2
            k_ = (2.8 if abs(xc_) > xw_ else 0.6) * g * (1 if xc_ > 0 else -1)
            partes.append(so.translate(cq.Vector(d["arandelas_tope"][0] + k_, d["arandelas_tope"][1],
                                                 d["arandelas_tope"][2])))
        mov["arandelas_tope"] = cq.Compound.makeCompound(partes)
    comp = cq.Compound.makeCompound(list(mov.values()))
    proy = V.proyectar(comp, "iso", tol=0.4, ocultas=False)
    ex = V.extension(proy["vis"])
    cod = "FL_DES_" + m.codigo[7:]
    doc = nuevo_doc()
    tabla_w = 190.0
    w, hh = ex[2] - ex[0], ex[3] - ex[1]
    # A2 si la isometría entra a 1:5 o mayor; si no (carros con el tren rodante abierto), A1
    for fmt in ("A2", "A1"):
        h = Hoja(doc, fmt)
        zona = (h.fx0 + 40, h.fy0 + 10, h.fx1 - tabla_w - 42, h.fy1 - 19)
        zw, zh = zona[2] - zona[0], zona[3] - zona[1]
        esc = next(e for e in ESCALAS if w * e[0] / e[1] <= zw and hh * e[0] / e[1] <= zh)
        if esc[1] / esc[0] <= 5:
            break
    h.formato()
    f = esc[0] / esc[1]
    ox = (zona[0] + zona[2]) / 2 - (ex[0] + ex[2]) / 2 * f
    oy = (zona[1] + zona[3]) / 2 - (ex[1] + ex[3]) / 2 * f
    T = (ox, oy, f)
    h.prims(proy["vis"], "01-VISIBLE", T)

    def P2(p):
        return (ox + p[0] * f, oy + p[1] * f)

    # lo ya dibujado (líneas de la isometría) para ubicar rótulos sin pisar nada
    ocupado = []
    for pl in V.a_polilineas(proy["vis"], 1.0):
        if len(pl) >= 2:
            ocupado.append(sg.LineString([P2(q) for q in pl]))
    # globos: columna izquierda y derecha
    xc = (zona[0] + zona[2]) / 2
    # parte realmente visible de cada pieza (z-buffer): el punto del globo cae siempre sobre la pieza que nombra,
    # nunca en el aire entre dos sólidos de un mismo ítem ni sobre otra pieza que la tapa
    vis = V.regiones_visibles(mov, list(mov), "iso", res=max(0.5, 0.2 / f), tol=0.6)
    items = []
    for k, s in mov.items():
        if k in ESPEJO or k not in pos:
            continue
        bb = s.BoundingBox()
        c = P2(V.proyectar_punto(((bb.xmin + bb.xmax) / 2, (bb.ymin + bb.ymax) / 2, (bb.zmin + bb.zmax) / 2),
                                 "iso"))
        lado = -1 if c[0] < xc else 1
        a = _anclaje_visible(vis.get(k), lado, 0.6 / f)
        a = P2(a if a is not None else _anclaje(s, lado))
        items.append((lado, a, pos[k], k))
    # partes visibles en mm de papel, para que la guía de cada globo no cruce otra pieza ni otra guía
    from shapely import affinity
    vis_p = {k: affinity.affine_transform(r, [f, 0, 0, f, ox, oy]) for k, r in vis.items()}
    ks_v = list(vis_p)
    arbol_v = shapely.STRtree([vis_p[k] for k in ks_v])
    guias = []
    for lado in (-1, 1):
        col = sorted([it for it in items if it[0] == lado], key=lambda it: it[1][1])
        xg = (h.fx0 + 22) if lado < 0 else (zona[2] + 22)
        ys = _repartir([it[1][1] for it in col], h.fy0 + 15, h.fy1 - 26, 11)
        an = []
        for it, y in zip(col, ys):
            an.append(_punto_guia(it[1], vis_p.get(it[3]), it[3], ks_v, vis_p, arbol_v,
                                  guias + [sg.LineString([q, (xg - lado * 4.5, yq)]) for q, yq in zip(an, ys)],
                                  (xg - lado * 4.5, y), mismo=ESPEJO_INV.get(it[3], ())))
        # dos guías que se cruzan intercambian sus globos (la suma de largos baja: termina)
        for _ in range(200):
            cambio = False
            for i in range(len(an)):
                for j in range(i + 1, len(an)):
                    li = sg.LineString([an[i], (xg - lado * 4.5, ys[i])])
                    lj = sg.LineString([an[j], (xg - lado * 4.5, ys[j])])
                    if li.crosses(lj):
                        ys[i], ys[j] = ys[j], ys[i]
                        cambio = True
            if not cambio:
                break
        for it, a, y in zip(col, an, ys):
            h.globo(it[2], a, (xg, y), r=4.5)
            guias.append(sg.LineString([a, (xg - lado * 4.5, y)]))
            ocupado.append(guias[-1])
            ocupado.append(sg.Point(xg, y).buffer(4.5))
    # rótulos de subconjunto: el lugar libre más cercano al grupo (abajo, arriba o a los costados), dentro de la zona
    # de dibujo y sin tocar líneas, globos, guías ni otro rótulo
    arbol = shapely.STRtree(ocupado)
    rotulos = []
    principal = {1: ("cuerpo",), 2: ("cuerpo_valvula",), 3: ("manguera_enrollada", "manguera", "difusor", "lanza"),
                 4: ("eje_ruedas", "portaeje")}
    for s_ in (1, 2, 3, 4):
        ks = [k for k in mov if sub[k] == s_]
        if not ks:
            continue
        # el rótulo va junto a la pieza principal del grupo (no al recuadro de todo el grupo, que en S2 incluye el
        # caño de pesca y en S3 el tramo de manga hasta la válvula)
        kp = next((k for k in principal[s_] if k in ks), None) or max(ks, key=lambda k: mov[k].Volume())
        # en el carro, el eje con sus dos ruedas: el rótulo va debajo del tren rodante, no entre las guías
        kps = [kp] + ([k for k in ("rueda_izq", "rueda_der") if k in ks] if s_ == 4 else [])
        pts = []
        for k in kps:
            bb = mov[k].BoundingBox()
            for x in (bb.xmin, bb.xmax):
                for y in (bb.ymin, bb.ymax):
                    for z in (bb.zmin, bb.zmax):
                        pts.append(P2(V.proyectar_punto((x, y, z), "iso")))
        fs = next(r for r in filas if r["nivel"] == 1 and r["sub"] == s_)
        etiqueta = f"S{s_} {B.NOMBRE_SUB[s_].upper()}"
        if fs["codigo"].startswith("FL_REC"):
            etiqueta += f" ({fs['codigo']})"
        gx0, gx1 = min(p[0] for p in pts), max(p[0] for p in pts)
        gy0, gy1 = min(p[1] for p in pts), max(p[1] for p in pts)
        gxc, gyc = (gx0 + gx1) / 2, (gy0 + gy1) / 2
        wt = ancho_texto(etiqueta, 3.5)
        # el lugar libre más cercano a la pieza principal (prefiriendo debajo), dentro de la zona de dibujo, sin tocar
        # líneas, globos, guías ni otro rótulo, y más cerca de su grupo que de cualquier otro subconjunto; si en un
        # renglón no hay lugar, en dos
        import numpy as np
        propio = shapely.union_all([vis_p[k] for k in kps if k in vis_p])
        if propio.is_empty:
            propio = sg.box(gx0, gy0, gx1, gy1)
        grupo = shapely.union_all([vis_p[k] for k in ks if k in vis_p])
        otros = shapely.union_all([r for k, r in vis_p.items() if sub.get(k) != s_])
        pal = etiqueta.split(" ")
        corte = min(range(1, len(pal)), key=lambda c: abs(len(" ".join(pal[:c])) - len(" ".join(pal[c:])))) \
            if len(pal) > 1 else 1
        renglones = [[etiqueta], [" ".join(pal[:corte]), " ".join(pal[corte:])]] if len(pal) > 1 else [[etiqueta]]
        paso_r = 3.5 * 1.6
        elegido = None
        for estricto in (True, False):
            for lineas in renglones:
                hw = max(ancho_texto(t_, 3.5) for t_ in lineas) / 2 + 1.2
                y_lo, y_hi = 3.5 * 0.85 + 0.6 + paso_r * (len(lineas) - 1), 3.5 * 0.6 + 0.6
                X, Y = np.meshgrid(np.arange(gx0 - 140, gx1 + 140, 2.0), np.arange(gy0 - 140, gy1 + 140, 2.0))
                X, Y = X.ravel(), Y.ravel()
                ok = (X - hw >= zona[0]) & (X + hw <= zona[2]) & (Y - y_lo >= h.fy0 + 3) & (Y + y_hi <= h.fy1 - 19)
                X, Y = X[ok], Y[ok]
                cajas = shapely.box(X - hw, Y - y_lo, X + hw, Y + y_hi)
                dist = shapely.distance(cajas, propio)
                for n_ in np.argsort(dist + np.where(Y > gyc, 2.0, 0.0)):
                    caja = cajas[n_]
                    if dist[n_] < 1.5:
                        continue
                    if not estricto and dist[n_] > 40:
                        break
                    if any(caja.intersects(ocupado[i]) for i in arbol.query(caja)) or \
                            any(caja.intersects(r) for r in rotulos):
                        continue
                    do, dg = (caja.distance(otros) if not otros.is_empty else 1e9), caja.distance(grupo)
                    if (estricto and do < dg + 2.0) or (not estricto and do < 3.0):
                        continue
                    elegido = (float(X[n_]), float(Y[n_]), caja, lineas)
                    break
                if elegido:
                    break
            if elegido:
                break
        if elegido is None:                       # no debería pasar: se avisa y se usa debajo de la pieza principal
            from .lamina import AVISOS
            AVISOS.append(f"{m.codigo}: rótulo S{s_} sin lugar libre en el despiece")
            x, y = gxc, gy0 - 4.5
            elegido = (x, y, sg.box(x - wt / 2, y - 2, x + wt / 2, y + 2), [etiqueta])
        rotulos.append(elegido[2])
        for n_, t_ in enumerate(elegido[3]):
            h.texto(t_, (elegido[0], elegido[1] - n_ * paso_r), 3.5, A.MIDDLE_CENTER)
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
    return cod, doc, fmt


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
        cod, doc, fmt = lamina(m)
        hojas = [("Lamina", fmt, 0.0)]
        X.preparar_layouts(doc, hojas)
        doc.saveas(os.path.join(carpeta, f"{cod}.dxf"))
        p = X.pdf_hojas(doc, hojas)
        p.set_metadata({"title": f"{cod} - Despiece {m.nombre}", "author": "FLAMA S.A."})
        p.save(os.path.join(carpeta, f"{cod}.pdf"))
        total.insert_pdf(p)
        print(cod, flush=True)
    if not codigos:
        total.save(os.path.join(carpeta, "FLAMA_despieces.pdf"))
