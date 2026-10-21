"""Modelos 3D (sólidos B-rep, OpenCascade vía CadQuery) de la línea FLAMA.

Sistema de coordenadas del conjunto:
  Z hacia arriba, origen en el piso sobre el eje del recipiente.
  -Y = frente (lado del manómetro / etiqueta)  -> vista anterior.
  +X = palanca de accionamiento, -X = manguera / tobera.

Cada pieza se devuelve por separado (dict nombre -> cq.Shape) para poder
referenciarla en el despiece, y el conjunto es un Compound sin fusionar.
"""

import math
import cadquery as cq
import shapely.geometry as sg

from .perfiles_valvula import PERFILES

AX_Y = cq.Vector(0, 1, 0)


# ---------------------------------------------------------------- utilitarios
def _cyl(r, h, base=(0, 0, 0), d=(0, 0, 1)):
    return cq.Solid.makeCylinder(r, h, cq.Vector(*base), cq.Vector(*d))


def _tube(ro, ri, h, base=(0, 0, 0), d=(0, 0, 1)):
    return _cyl(ro, h, base, d).cut(_cyl(ri, h, base, d))


def _box(dx, dy, dz, cx, cy, z0):
    return cq.Solid.makeBox(dx, dy, dz, cq.Vector(cx - dx / 2, cy - dy / 2, z0))


def _torus(R, r, z, cx=0.0, cy=0.0, d=(0, 0, 1)):
    return cq.Solid.makeTorus(R, r, cq.Vector(cx, cy, z), cq.Vector(*d))


def _ell(cx, cz, a, b, t0, t1, n=16):
    """puntos (r,z) de un arco de elipse y tangentes extremas."""
    pts = [(cx + a * math.cos(t0 + (t1 - t0) * i / n), cz + b * math.sin(t0 + (t1 - t0) * i / n))
           for i in range(n + 1)]
    s = 1 if t1 > t0 else -1
    tg = lambda t: (-a * math.sin(t) * s, b * math.cos(t) * s)
    return pts, tg(t0), tg(t1)


class _Perfil:
    """Constructor de perfiles cerrados (r,z) a revolucionar sobre Z."""

    def __init__(self, p0):
        self.wp = cq.Workplane("XZ").moveTo(*p0)
        self.cur = p0

    def l(self, p):
        if (abs(p[0] - self.cur[0]) > 1e-6) or (abs(p[1] - self.cur[1]) > 1e-6):
            self.wp = self.wp.lineTo(*p)
            self.cur = p
        return self

    def e(self, cx, cz, a, b, t0, t1):
        pts, ta, tb = _ell(cx, cz, a, b, t0, t1)
        self.l(pts[0])
        self.wp = self.wp.spline(pts[1:], tangents=[ta, tb], includeCurrent=True)
        self.cur = pts[-1]
        return self

    def sp(self, pts):
        self.l(pts[0])
        self.wp = self.wp.spline(pts[1:], includeCurrent=True)
        self.cur = pts[-1]
        return self

    def revolve(self):
        return self.wp.close().revolve(360, (0, 0, 0), (0, 1, 0)).val()


def _sweep_circle(path_pts, r, arcs=True):
    """Barre un círculo de radio r a lo largo de una polilínea con esquinas
    redondeadas (radio de curvatura = path_pts[i][3] si se indica)."""
    wp = cq.Workplane("XY")
    edges = []
    P = [cq.Vector(*p[:3]) for p in path_pts]
    rad = [p[3] if len(p) > 3 else 0 for p in path_pts]
    cur = P[0]
    for i in range(1, len(P)):
        if i < len(P) - 1 and rad[i] > 0:
            a = (P[i - 1] - P[i]).normalized()
            b = (P[i + 1] - P[i]).normalized()
            ang = math.acos(max(-1, min(1, a.dot(b))))
            dist = rad[i] / math.tan(ang / 2)
            p1 = P[i] + a * dist
            p2 = P[i] + b * dist
            bis = (a + b).normalized()
            mid_c = P[i] + bis * (rad[i] / math.sin(ang / 2))
            pm = mid_c + (P[i] - mid_c).normalized() * rad[i]
            edges.append(cq.Edge.makeLine(cur, p1))
            edges.append(cq.Edge.makeThreePointArc(p1, pm, p2))
            cur = p2
        else:
            edges.append(cq.Edge.makeLine(cur, P[i]))
            cur = P[i]
    path = cq.Wire.assembleEdges(edges)
    d0 = (P[1] - P[0]).normalized()
    circ = cq.Wire.makeCircle(r, P[0], d0)
    return cq.Solid.sweep(circ, [], path, transitionMode="round")


def _tubo(path_pts, r):
    """Caño o manga de radio r por una poligonal con las esquinas redondeadas (radio path_pts[i][3]), armada con
    cilindros y toros exactos (las vistas con líneas ocultas salen limpias). Devuelve (sólido, largo del eje)."""
    P = [cq.Vector(*p[:3]) for p in path_pts]
    n = len(P)
    rad = [p[3] if len(p) > 3 else 0.0 for p in path_pts]
    ang, dist = [math.pi] * n, [0.0] * n
    for i in range(1, n - 1):
        if rad[i] > 0:
            a_ = (P[i - 1] - P[i]).normalized()
            b_ = (P[i + 1] - P[i]).normalized()
            ang[i] = math.acos(max(-1.0, min(1.0, a_.dot(b_))))
            if ang[i] < math.pi - 1e-3:
                dist[i] = rad[i] / math.tan(ang[i] / 2)
    for j in range(n - 1):                  # dos curvas vecinas se reparten el tramo que las une
        L_ = (P[j + 1] - P[j]).Length * 0.999
        if dist[j] + dist[j + 1] > L_:
            f_ = L_ / (dist[j] + dist[j + 1])
            dist[j] *= f_
            dist[j + 1] *= f_
    trozos, largo, cur = [], 0.0, P[0]

    def _recto(a_, b_):
        L_ = (b_ - a_).Length
        if L_ > 1e-6:
            trozos.append(cq.Solid.makeCylinder(r, L_, a_, (b_ - a_).normalized()))
        return L_

    for i in range(1, n):
        if i < n - 1 and dist[i] > 1e-6:
            a_ = (P[i - 1] - P[i]).normalized()
            b_ = (P[i + 1] - P[i]).normalized()
            rr = dist[i] * math.tan(ang[i] / 2)
            t1, t2 = P[i] + a_ * dist[i], P[i] + b_ * dist[i]
            c_ = P[i] + (a_ + b_).normalized() * (rr / math.sin(ang[i] / 2))
            largo += _recto(cur, t1)
            n_ = (t1 - c_).cross(t2 - c_).normalized()
            cara = cq.Face.makeFromWires(cq.Wire.makeCircle(r, t1, -a_))
            trozos.append(cq.Solid.revolve(cara, math.degrees(math.pi - ang[i]), c_, c_ + n_))
            largo += rr * (math.pi - ang[i])
            cur = t2
            continue
        largo += _recto(cur, P[i])
        cur = P[i]
    sol = trozos[0].fuse(*trozos[1:]).clean() if len(trozos) > 1 else trozos[0]
    from OCP.BRepLib import BRepLib
    BRepLib.EncodeRegularity_s(sol.wrapped, 0.03)   # uniones tangentes: aristas lisas (no se dibujan en las vistas)
    return sol, largo


# ---------------------------------------------------------------- recipientes
def _anillo(pts):
    """Sólido de revolución de un polígono cerrado (r, z)."""
    wp = cq.Workplane("XZ").moveTo(*pts[0])
    for q in pts[1:]:
        wp = wp.lineTo(*q)
    return wp.close().revolve(360, (0, 0, 0), (0, 1, 0)).val()


def encastre(g):
    """Encastres de las uniones circunferenciales (planos Fadesa de recipiente, detalles 2 y 3; proceso FLAMA).
    Manuales: el extremo del cuerpo lleva el bordón (escalón de un espesor, formado en la bordoneadora) y la cúpula
    (y en el 1 kg también el fondo) monta por fuera con una pollera recta; el labio del cuerpo entra 6 mm y el escalón
    ocupa 5 mm (medidos a escala 1:1 en los detalles 2 de los planos Fadesa de 1 y 5 kg: 5,5-5,8 y 4,5-5,2 mm).
    Rodantes: los casquetes vienen embutidos con el borde reducido y tope; el labio entra en el cuerpo 2,5·e (mín. 8)
    y el escalón ocupa 2·e (plano Fadesa 25 kg, detalles 2 y 3). Devuelve (labio, escalón)."""
    if g["tipo_fondo"] == "co2":
        return 0.0, 0.0
    if g["tipo_fondo"] == "cabezal":
        return max(8.0, 2.5 * g["t"]), 2.0 * g["t"]
    return 6.0, 5.0


def _lleno(dr):
    """Envolvente exterior maciza del recipiente (para recortar los accesorios soldados contra la chapa)."""
    R, zb, zu, hd, hf = dr["R"], dr["zb"], dr["z_union"], dr["hd"], dr["hf"]
    e_ = dr.get("encastre", (0.0, 0.0))[1]          # casquetes con escalón: la elipse arranca a «e_» de la unión
    s = _cyl(R, zu - zb + 2 * e_, (0, 0, zb - e_))
    for zc, b, t1 in ((zu + e_, hd - e_, math.pi / 2), (zb - e_, hf - e_, -math.pi / 2)):
        pts, _, _ = _ell(0, zc, R, b, 0, t1)
        s = s.fuse(cq.Workplane("XZ").moveTo(0, zc).polyline(pts, includeCurrent=True).close()
                   .revolve(360, (0, 0, 0), (0, 1, 0)).val())
    return s.clean()


def recipiente(g, z0=0.0, costura=True):
    """Recipiente soldado. Devuelve (dict piezas, datos geométricos)."""
    R, hc, hd, t, td, tf = g["R"], g["hc"], g["hd"], g["t"], g["td"], g["tf"]
    dn, hn, rosca, dh = g["cuello"]
    rh = dh / 2
    piezas = {}
    tipo = g["tipo_fondo"]
    rod = tipo == "cabezal"
    lab, esc = encastre(g)
    # centro de la elipse de la cúpula sobre la línea de unión: pollera recta (manuales) o escalón del casquete (rodantes)
    c0 = 0.0 if tipo == "co2" else (esc if rod else lab)

    # --- cuerpo (virola) + cúpula (casquete) --------------------------------
    Ri = R - td
    to = math.acos(min(1, rh / R))
    ti = math.acos(min(1, rh / Ri))
    if "total" in g:  # altura total del recipiente (piso a cara superior del cuello)
        hc = g["total"] - hn - (c0 + (hd - c0) * math.sin(to))
    if rod:  # rodantes: hc = largo del cuerpo entre cabezales (planos Fadesa G690 493, G689 640)
        hc = hd + hc
    zo = hc + c0 + (hd - c0) * math.sin(to)
    zi = hc + c0 + (hd - c0 - td) * math.sin(ti)
    if tipo == "concavo":
        zb = 0.0
    elif tipo == "cupula":
        zb = g["hf"]
    elif rod:
        zb = hd
    else:  # co2: fondo semiesférico
        zb = R + g.get("z_pie", 0.0)
    hf = {"cupula": g.get("hf", hd), "cabezal": hd, "co2": R}.get(tipo, 0.0)

    if tipo in ("concavo", "cupula"):
        # cuerpo con bordón arriba (y abajo en el 1 kg, virola con los dos extremos reducidos)
        z_a = zb + (esc if tipo == "cupula" else 0.0)
        cu = _tube(R, R - t, hc - esc - z_a, (0, 0, z_a))
        cu = cu.fuse(_anillo([(R - t, hc - esc), (R, hc - esc), (R - t, hc), (R - 2 * t, hc)]))
        cu = cu.fuse(_tube(R - t, R - 2 * t, lab, (0, 0, hc)))
        if tipo == "cupula":
            cu = cu.fuse(_anillo([(R - 2 * t, zb), (R - t, zb), (R, zb + esc), (R - t, zb + esc)]))
            cu = cu.fuse(_tube(R - t, R - 2 * t, lab, (0, 0, zb - lab)))
        piezas["cuerpo"] = cu.clean()
        p = _Perfil((R, hc)).l((R, hc + c0)).e(0, hc + c0, R, hd - c0, 0, to).l((rh, zi))
        p.e(0, hc + c0, Ri, hd - c0 - td, ti, 0).l((Ri, hc))
        piezas["cupula"] = p.revolve()
    elif rod:
        piezas["cuerpo"] = _tube(R, R - t, hc - zb, (0, 0, zb))
        # casquete superior: elipse desde el escalón, escalón (borde reducido) y labio dentro del cuerpo
        p = _Perfil((R - t, hc - lab)).l((R - t, hc)).l((R, hc + esc)).e(0, hc + esc, R, hd - esc, 0, to).l((rh, zi))
        p.e(0, hc + esc, Ri, hd - esc - td, ti, 0).l((R - t - td, hc)).l((R - t - td, hc - lab))
        piezas["cupula"] = p.revolve()
    else:
        piezas["cuerpo"] = _tube(R, R - t, hc - zb, (0, 0, zb))
        p = _Perfil((R, hc)).e(0, hc, R, hd, 0, to).l((rh, zi))
        p.e(0, hc, Ri, hd - td, ti, 0)
        piezas["cupula"] = p.revolve()

    # --- fondo ------------------------------------------------------------
    if tipo == "concavo":
        # fondo cóncavo encastrado a presión dentro del cuerpo, con pestaña de 10 mm contra la pared (detalle 3 Fadesa)
        zc, zr = g["zf_centro"], g["zf_borde"]
        rf = R - t
        hp = 10.0
        lo = [(rf * i / 10, zc + (zr - zc) * (i / 10) ** 2) for i in range(11)]
        up = [(r * (rf - tf) / rf, z + tf) for r, z in reversed(lo)]
        pf = _Perfil((0, zc)).sp(lo).l((rf, zr + hp)).l((rf - tf, zr + hp)).sp(up)
        piezas["fondo"] = pf.revolve()
    elif tipo == "cupula":
        # 1 kg: fondo con pollera recta por fuera del bordón inferior del caño
        pf = _Perfil((0, zb - hf)).e(0, zb - lab, R, hf - lab, -math.pi / 2, 0).l((R, zb)).l((R - tf, zb))
        pf.l((R - tf, zb - lab)).e(0, zb - lab, R - tf, hf - lab - tf, 0, -math.pi / 2)
        piezas["fondo"] = pf.revolve()
    elif rod:
        pf = _Perfil((0, zb - hf)).e(0, zb - esc, R, hf - esc, -math.pi / 2, 0).l((R - t, zb)).l((R - t, zb + lab))
        pf.l((R - t - tf, zb + lab)).l((R - t - tf, zb)).l((R - tf, zb - esc))
        pf.e(0, zb - esc, R - tf, hf - esc - tf, 0, -math.pi / 2)
        piezas["fondo"] = pf.revolve()
    else:
        pf = _Perfil((0, zb - hf)).e(0, zb, R, hf, -math.pi / 2, 0).l((R - tf, zb))
        pf.e(0, zb, R - tf, hf - tf, 0, -math.pi / 2)
        piezas["fondo"] = pf.revolve()

    # --- cuello (anillo roscado) ------------------------------------------
    bore = {"M30x1,5": 28.376, "M22x1,5": 20.376}.get(rosca, dh - 7.8 if dh > 60 else dh - 6)
    ztop = zo + hn
    cu = _tube(dh / 2 + 0.01, bore / 2, zo - zi + 1.0, (0, 0, zi - 1.0))
    cu = cu.fuse(_tube(dn / 2, bore / 2, hn, (0, 0, zo)))
    if tipo in ("concavo", "cupula"):
        # muesca de referencia de altura (prensa Pannier, proceso FLAMA «preparación de cuello»): 2 × 1 × 2 mm, lado +X
        cu = cu.cut(_box(2.0, 2.0, 2.0, dn / 2, 0, zo + 2.0))
    piezas["cuello"] = cu.clean()

    # --- cordones de soldadura (MAG) ----------------------------------------
    sw = max(1.0, 0.8 * t)
    Rs = R - 0.5 * t          # cordón en el escalón, sobremonta exterior
    sold = []
    if tipo != "co2":
        sold.append(_torus(Rs, sw, hc + (esc / 2 if rod else -esc / 2)))       # cúpula-cuerpo
        if rod:
            sold.append(_torus(Rs, sw, zb - esc / 2))                         # fondo-cuerpo
        elif tipo == "cupula":
            sold.append(_torus(Rs, sw, zb + esc / 2))                         # fondo-cuerpo (1 kg)
        else:
            sold.append(_torus(R - t, sw, g["zf_borde"] - 0.5))                # filete del fondo, por debajo
    if tipo != "co2":
        sold.append(_torus(dn / 2, max(1.0, 0.8 * td), zo))    # cuello-cúpula
    if costura and tipo != "co2":
        # costura longitudinal (el 1 kg también: chapa de 0,9 cilindrada y soldada TIG)
        z_s0 = zb if tipo != "concavo" else 0.0
        sold.append(_box(3.0, 0.8 * t, hc - esc - z_s0 - 2 if not rod else hc - zb - 2, 0, -R + 0.1 * t, z_s0 + 1))
    if g.get("refuerzo"):
        # 70 y 100 kg: dos placas de refuerzo 200 × 100 × 4,75 curvadas al Ø interior, por dentro y sobre la costura
        # longitudinal, una en cada extremo a 100 mm del borde (proceso FLAMA de carros, punteo del cuerpo)
        la, lr, er = g["refuerzo"]
        ri = R - t
        pl = _sector(ri - er, ri, la, zb + 100.0, lr, 0, 0)
        piezas["placas_refuerzo"] = pl.fuse(_sector(ri - er, ri, la, hc - 100.0 - la, lr, 0, 0)).clean()
    if sold:
        s = sold[0]
        for x in sold[1:]:
            s = s.fuse(x)
        piezas["soldaduras"] = s.clean()
    if tipo == "co2":
        # cilindro sin costura: cuerpo, hombro, fondo y cuello forman una sola pieza
        piezas["cuerpo"] = (piezas["cuerpo"].fuse(piezas.pop("cupula")).fuse(piezas.pop("fondo"))
                            .fuse(piezas.pop("cuello")).clean())

    for k in piezas:
        piezas[k] = piezas[k].translate(cq.Vector(0, 0, z0))
    datos = dict(R=R, z_cuello=ztop + z0, z_cupula=zo + z0, z_union=hc + z0, zb=zb + z0, hd=hd, hf=hf,
                 encastre=(lab, esc), rosca=rosca, dn=dn, bore=bore,
                 z_fondo=z0 + (g.get("zf_centro", 0) if tipo == "concavo" else zb - hf))
    return piezas, datos


# ---------------------------------------------------------------- válvula
# Válvulas medidas a escala en los planos Fadesa de extintor completo (escala del rótulo verificada con el Ø
# del recipiente acotado en su plano de recipiente). Cotas en mm; z = 0 en la cara superior del cuello.
#   F510: 1 kg (plano «Extintor 1 kg Ø76 (válvula HZ) R1», esc. 1:2,5), espiga M22.
#   F192: 2,5 a 10 kg y rodante 25 kg (planos «Extintor 2,5 / 5 / 10 kg HZ R1» y «Extintor rodante 25 kg R1»), M30.
#   G763: rodantes 50 a 100 kg (planos «Extintor rodante 50 / 100 kg R1», esc. 1:7 y 1:8), cupla RBSP 2½".
VALVULAS = {
    "F510": dict(esp_d=21.0, esp_h=8.6, cuello_d=19.0, cuello_h=3.0, bw=26.0, bd=24.0, bh=15.0,
                 boss_d=16.8, sal_d=10.8, sal_l=7.3, sal_z=10.3, oreja=18.0, pasador=(15.5, 13.5),
                 sup_h=16.0, lev_w=27.0, man_d=36.0, man_e=11.0,
                 res=(9.8, 19.9), vas=(5.0, 21.0, 9.0, 5.0), oring=(24.8, 3.5)),
    "F192": dict(esp_d=29.8, esp_h=10.8, cuello_d=27.2, cuello_h=4.1, bw=36.0, bd=28.0, bh=12.8,
                 boss_d=15.0, sal_d=13.1, sal_l=8.9, sal_z=11.9, oreja=22.0, pasador=(21.0, 20.0),
                 sup_h=20.0, lev_w=31.0, man_d=36.0, man_e=11.0,
                 res=(17.3, 28.8), vas=(6.0, 30.7, 14.0, 14.0), oring=(32.7, 3.6)),
    "G763": dict(esp_d=75.0, esp_h=17.6, cuello_d=83.0, cuello_h=12.0, bw=49.0, bd=40.0, bh=67.0, piv_h=67.0,
                 boss_d=30.0, sal_d=26.0, sal_l=20.0, sal_z=40.0, sup_l=None, sup_h=16.0, sup_top=None,
                 inf=None, inf_h=8.0, lev_w=10.0, man_d=47.0, man_e=14.0,
                 torre=(30.0, 20.0, 37.0, 30.0), ranura=11.0, eje_d=8.0,
                 res=(27.0, 35.0), vas=(10.0, 36.0, 20.0, 8.0), oring=(81.0, 4.7)),
}


def tipo_valvula(m):
    """F510 (1 kg), F192 (M30: 2,5 a 25 kg y demás manuales), G763 (cupla RBSP 2½": 50 a 100 kg)."""
    rosca = m.geo["cuello"][2]
    if rosca.startswith("M22"):
        return "F510"
    if rosca.startswith("RBSP"):
        return "G763"
    return "F192"


def _caja_rot(x0, x1, z0, h, w, ang, eje_x, eje_z):
    """Placa de largo x0..x1, alto h (desde z0) y ancho w (Y), girada `ang` grados alrededor de (eje_x, eje_z)."""
    b = cq.Solid.makeBox(x1 - x0, w, h, cq.Vector(x0, -w / 2, z0))
    return b.rotate(cq.Vector(eje_x, 0, eje_z), cq.Vector(eje_x, 1, eje_z), ang) if ang else b


def _extruir_xz(pts, w, z0=0.0):
    """perfil (x, z) del plano lateral extruido w según Y, centrado en y = 0 y subido z0."""
    pts = [(x, z + z0) for x, z in list(pts)[:-1 if tuple(pts[0]) == tuple(pts[-1]) else None]]
    return cq.Workplane("XZ").polyline(pts).close().extrude(w / 2, both=True).val()


def valvula(z0, tipo="F192", dn=37.0, bore=28.4, co2=False, x_tip=None, man_d=None):
    """Válvula de descarga con sus piezas medidas en los planos Fadesa (ver VALVULAS).
    z0 = cara superior del cuello; la salida a la manguera queda hacia -X y las manijas hacia +X.
    x_tip sólo se usa en la G763 (palanca de accionamiento del rodante, sin cota en el plano Fadesa)."""
    V = VALVULAS[tipo]
    man_d = man_d or V["man_d"]
    bw, bd, bh = V["bw"], V["bd"], V["bh"]
    p = {}
    # espiga roscada (dentro del cuello) y cuello / brida de asiento
    p["espiga"] = _tube(V["esp_d"] / 2, max(bore / 2 - 2.5, V["esp_d"] / 2 - 4), V["esp_h"],
                        (0, 0, z0 - V["esp_h"]))
    p["tuerca"] = _tube(V["cuello_d"] / 2, max(bore / 2 - 2.5, V["esp_d"] / 2 - 4), V["cuello_h"], (0, 0, z0))
    zb0 = z0 + V["cuello_h"]
    # cuerpo forjado: bloque + horquilla del pivote (a la izquierda) + boca de manómetro (frente) + salida (-X)
    if tipo == "G763":
        # válvula de carro (plano Fadesa 50 / 100 kg): base 49 × 40, torre que se angosta a 37 × 30 y horquilla de dos
        # brazos con ranura de 11 para la palanca; el eje (tornillo F840 + buje + arandela) cruza la horquilla según X
        hb_, ht_, wt_, dt_ = V["torre"]
        cuerpo = cq.Solid.makeBox(bw, bd, hb_, cq.Vector(-bw / 2, -bd / 2, zb0))
        cuerpo = cq.Workplane().add(cuerpo).edges("|Z").fillet(5.0).val()
        torre = (cq.Workplane("XY").workplane(offset=zb0 + hb_).rect(bw, bd).workplane(offset=ht_).rect(wt_, dt_)
                 .loft().val())
        cuerpo = cuerpo.fuse(torre)
        hq = bh - hb_ - ht_
        a_ = (wt_ - V["ranura"]) / 2
        for sgn in (1, -1):
            cuerpo = cuerpo.fuse(_box(a_, dt_, hq, sgn * (V["ranura"] / 2 + a_ / 2), 0, zb0 + hb_ + ht_))
    else:
        cuerpo = cq.Solid.makeBox(bw, bd, bh, cq.Vector(-bw / 2, -bd / 2, zb0))
        cuerpo = cq.Workplane().add(cuerpo).edges("|Z").fillet(min(4.0, bd / 6)).val()
    if tipo != "G763":
        # oreja del pivote de la palanca (más angosta que el bloque), redondeada arriba
        xpv, zpv = PERFILES[tipo][2]
        tw = V["oreja"]
        ore = cq.Solid.makeBox(9.0, tw, z0 + zpv - (zb0 + bh), cq.Vector(xpv - 4.5, -tw / 2, zb0 + bh))
        cuerpo = cuerpo.fuse(ore).fuse(_cyl(4.5, tw, (xpv, -tw / 2, z0 + zpv), (0, 1, 0)))
    zm = zb0 + (max(V["torre"][0] * 0.55, man_d / 2 + 2) if tipo == "G763" else max(min(bh * 0.5, 6.4), V["boss_d"] / 2))
    cuerpo = cuerpo.fuse(_cyl(V["boss_d"] / 2, 5.0, (0, -bd / 2 + 1, zm), (0, -1, 0)))
    zs = zb0 + min(V["sal_z"], bh - V["sal_d"] / 2) if tipo != "G763" else zb0 + V["sal_z"]
    cuerpo = cuerpo.fuse(_cyl(V["sal_d"] / 2, V["sal_l"], (-bw / 2 + 1, 0, zs), (-1, 0, 0)))
    p["cuerpo_valvula"] = cuerpo.clean()
    y_man = -bd / 2 - 4.0
    if zm - man_d / 2 < zb0:                  # la esfera baja hasta la cupla: el vástago la adelanta para no tocarla
        y_man = min(y_man, -dn / 2 - 0.8)
    if co2:
        p["disco_seguridad"] = cq.Workplane("XZ", origin=(0, -bd / 2 - 4, zm)).polygon(6, 14).extrude(9).val()   # tapón
        # hexagonal del disco de rotura, enroscado en la cara del resalte
    else:
        gm = _cyl(man_d / 2, V["man_e"], (0, y_man, zm), (0, -1, 0))
        gm = gm.fuse(_cyl(3.0, -y_man - bd / 2 + 1.0, (0, -bd / 2 + 1, zm), (0, -1, 0)))   # vástago roscado
        gm = gm.fuse(_torus(man_d / 2 - 1.2, 1.2, 0, 0, 0, (0, 1, 0)).translate(cq.Vector(0, y_man - V["man_e"], zm)))
        p["manometro"] = gm.clean()
    # vástago (pasa por el cuerpo, asiento abajo) y resorte (debajo de la espiga, dentro del caño de pesca)
    vd, vl, ad, ah = V["vas"]
    # G763: el vástago apoya bajo la nariz de la palanca (pivote a bh - 6, palanca girada 8°)
    if tipo == "G763":
        z_vt = zb0 + bh - 6.0 - V["sup_h"] / 2 - 8.0 * math.sin(math.radians(8.0)) - 0.5
    else:   # el vástago toca la cara inferior de la palanca sobre el eje de la válvula (en todo su Ø)
        r_v = V["vas"][0] / 2 + 0.2
        z_vt = z0 + sg.Polygon(PERFILES[tipo][0]).intersection(sg.box(-r_v, -50, r_v, 90)).bounds[1] - 0.3
    vas = _cyl(vd / 2, vl, (0, 0, z_vt - vl))
    vas = vas.fuse(_cyl(ad / 2, ah * 0.35, (0, 0, z_vt - vl - ah * 0.35)))
    p["vastago"] = vas.clean()
    # agujero del vástago y rosca del manómetro en el cuerpo forjado
    p["cuerpo_valvula"] = p["cuerpo_valvula"].cut(_cyl(vd / 2 + 0.2, vl + 60, (0, 0, zb0 - 30)))
    if "manometro" in p:
        p["cuerpo_valvula"] = p["cuerpo_valvula"].cut(p["manometro"])
    rd, rl = V["res"]
    zr1 = z_vt - vl - ah * 0.35
    p["resorte"] = _tube(rd / 2, rd / 2 - 1.2, rl, (0, 0, zr1 - rl))
    lw = V["lev_w"]
    if tipo == "G763":
        # palanca en la ranura de la horquilla, pivote 8 mm detrás del vástago: al levantar la empuñadura (hacia
        # adelante, del lado de la manga; el manómetro queda atrás, hacia la manija) la nariz baja el vástago.
        # Largo = 0,75·R (sin cota en Fadesa).
        L_ = x_tip or 110.0
        y_pv, z_pv = 8.0, zb0 + bh - 6.0
        ang = 8.0
        hl = V["sup_h"]
        lev = cq.Solid.makeBox(lw, L_ + 12.0, hl, cq.Vector(-lw / 2, -12.0, z_pv - hl / 2))
        lev = lev.fuse(_cyl(11.0, 44.0, (-22.0, L_, z_pv), (1, 0, 0)))          # empuñadura Ø22 × 44
        p["manija_superior"] = lev.rotate(cq.Vector(0, y_pv, z_pv), cq.Vector(1, y_pv, z_pv), ang).clean()
        z_top = p["manija_superior"].BoundingBox().zmax
        x_piv = 0.0
        e_d = V["eje_d"]
        p["eje"] = _cyl(e_d / 2, V["torre"][2] + 10, (-(V["torre"][2] + 10) / 2, y_pv, z_pv), (1, 0, 0))
        # traba (IRAM 3550 3.4.2): pasador que cruza horquilla y nariz de la palanca, con anilla y precinto
        zp_, yp_ = z_pv - 1.0, -6.0
        p["pasador"] = _cyl(1.6, V["torre"][2] + 16, (-(V["torre"][2] + 16) / 2, yp_, zp_), (1, 0, 0)).fuse(
            _torus(9, 1.4, 0, 0, 0, (1, 0, 0)).translate(cq.Vector(V["torre"][2] / 2 + 8, yp_, zp_ - 9))).clean()
        # agujeros del eje y del pasador en horquilla y palanca; cámara del vástago y su asiento en el cuerpo
        cv = p["cuerpo_valvula"].cut(p["eje"]).cut(p["pasador"]).cut(p["vastago"])
        p["cuerpo_valvula"] = cv.clean()
        p["manija_superior"] = p["manija_superior"].cut(p["eje"]).cut(p["pasador"]).cut(p["vastago"]).clean()
    else:
        # manijas con el perfil real del plano Fadesa (perfiles_valvula.py): palanca de accionamiento con pivote atrás
        # (sobre la oreja del cuerpo) y manija fija de transporte que la abraza; chapa estampada en U, representada
        # maciza (la masa se corrige en materiales.py con el factor de chapa)
        p_sup, p_inf, (xpv, zpv) = PERFILES[tipo]
        wu, wl = bd + 3.0, bd + 7.0      # palanca a horcajadas del cuerpo; manija a horcajadas de la palanca
        sup = _extruir_xz(p_sup, wu, z0)
        inf = _extruir_xz(p_inf, wl, z0).cut(_extruir_xz(sg.Polygon(p_sup).buffer(0.6).exterior.coords, wu + 1.0, z0))
        z_top = z0 + max(z for _, z in p_sup)
        x_piv, x_eje, z_eje = xpv, xpv, z0 + zpv
        r_e = 1.8 if tipo == "F510" else 2.0
        p["eje"] = _cyl(r_e, wu + 2, (x_eje, -wu / 2 - 1, z_eje), (0, 1, 0))
        # pasador de seguridad (traba IRAM 3517-2 9.4.13) a través de la manija, bajo la palanca; anilla del lado de
        # atrás (+Y) para no tocar el manómetro, que mira hacia adelante
        xs_, zs_ = V["pasador"]
        zp = z0 + zs_
        p["pasador"] = _cyl(1.6, wl + 9.5, (xs_, -wl / 2 - 0.5, zp), (0, 1, 0)).fuse(
            _torus(9, 1.4, 0, 0, 0, (0, 1, 0)).translate(cq.Vector(xs_, wl / 2 + 9, zp - 9))).clean()
        # agujeros: eje en oreja y palanca; pasador en la manija; paso del vástago en la manija
        paso_v = _cyl(V["vas"][0] / 2 + 0.5, 60, (0, 0, zb0))
        p["cuerpo_valvula"] = p["cuerpo_valvula"].cut(_cyl(r_e + 0.1, wl + 10, (x_eje, -wl / 2 - 5, z_eje), (0, 1, 0)))
        p["manija_superior"] = sup.cut(p["cuerpo_valvula"]).cut(p["eje"]).cut(paso_v).clean()
        p["manija_inferior"] = inf.cut(p["cuerpo_valvula"]).cut(p["pasador"]).cut(paso_v).clean()
    y_tip = (x_tip or 110.0) + 11.0 if tipo == "G763" else bd / 2
    info = dict(z_salida=zs, x_salida=-bw / 2 - V["sal_l"] + 1, bw=bw, bd=bd, bh=bh, z_top=z_top, y_tip=y_tip,
                x_piv=x_piv, z_man=zm, y_man=y_man - V["man_e"], man_d=man_d, zb0=zb0,
                s=1.0 if tipo == "F192" else (0.8 if tipo == "F510" else 1.35), tipo=tipo,
                sal_d=V["sal_d"])
    return p, info


# ---------------------------------------------------------------- conjuntos
def extintor_manual(m, cW=0.0, cH=0.0):
    g = dict(m.geo)
    H, W = m.H, m.W
    piezas, dr = recipiente(g, 0.0, costura=(m.familia != "co2"))
    R = dr["R"]
    chico = g["cuello"][0] < 32
    s = 0.8 if chico else 1.0
    fam = m.familia
    out = dict(piezas)
    info = dict(recipiente=dr)

    # dispositivo de descarga propio de cada tipo (ver catalogo.DESCARGA)
    tipo = m.descarga
    d_hose = 0 if chico else (14.0 if fam == "co2" else 17.4)    # manguera Ø17,4 medida en Fadesa (2,5-10 kg)
    d_dev = {"tobera_polvo": 19.9, "tobera_chorro": 22.0, "lanza_espuma": 32.0, "lanza_k": 20.0,
             "lanza_d": 40.0, "difusor_brazo": 70.0, "difusor_manga": 90.0, "tobera_1kg": 0.0}[tipo]
    if chico:
        xmin = -(15 * s + 13 * s + 26)
    elif tipo == "tobera_polvo":
        xh = -(R + 20.0)              # eje de la manguera: suncho portamanguera F674 sobresale 28,8 (plano Fadesa)
    else:
        xh = -(R + 4 + max(d_hose, d_dev) / 2)
    tv = tipo_valvula(m)
    val, vi = valvula(dr["z_cuello"], tipo=tv, dn=g["cuello"][0], bore=dr["bore"], co2=(fam == "co2"))
    out.update(val)
    info["valvula"] = vi

    # caño de pesca
    zf = dr["z_fondo"] + g["tf"] + 18
    zs0 = dr["z_cuello"] - VALVULAS[tv]["esp_h"]
    if fam != "co2":
        # caño de pesca: Ø21,3 (F682, válvula F192) / Ø14,4 (1 kg, F003/617), medidos en los planos Fadesa
        dp = 14.4 if tv == "F510" else 21.3
        out["cano_pesca"] = _tube(dp / 2, dp / 2 - 1.5, zs0 - zf, (0, 0, zf))
        if fam == "inox":
            # agua / AFFF / acetato: filtro en la entrada del tubo interior (IRAM 3525 3.6.1), PP perforado
            out["filtro_pesca"] = _tube(dp / 2 + 1.5, dp / 2, 25.0, (0, 0, zf - 5.0))
    else:
        out["cano_pesca"] = _tube(5, 3.5, zs0 - zf, (0, 0, zf))

    if fam == "co2":
        # pie de apoyo (base de polietileno) del cilindro de fondo semiesférico
        out["pie"] = _tube(R, R - 3.0, 0.55 * R, (0, 0, 0)).fuse(_cyl(R, 4, (0, 0, 0))).clean()

    xs, zs = vi["x_salida"], vi["z_salida"]
    if tipo == "tobera_1kg":
        # F510: boquilla de descarga corta roscada en la salida (el plano Fadesa no muestra tobera aparte)
        noz = cq.Solid.makeCone(6.0, 4.5, 10, cq.Vector(xs, 0, zs), cq.Vector(-1, 0, 0))
        out["tobera"] = noz.cut(_cyl(2.5, 10, (xs, 0, zs), (-1, 0, 0)))
        info["tobera"] = (xs - 5, zs)
        return out, info

    if tipo == "difusor_brazo":
        # CO2 2 kg: brazo giratorio rígido + difusor aislante con empuñadura (sin manga)
        out["brazo_difusor"] = _sweep_circle([(xs, 0, zs), (xh, 0, zs, 12), (xh, 0, zs - 55)], 6)
        z0d, hl = zs - 55, 170.0
        cone = cq.Solid.makeCone(12, d_dev / 2, hl, cq.Vector(xh, 0, z0d), cq.Vector(0, 0, -1))
        cone = cone.cut(cq.Solid.makeCone(9.5, d_dev / 2 - 2.5, hl, cq.Vector(xh, 0, z0d), cq.Vector(0, 0, -1)))
        out["difusor"] = cone.clean()
        r_c = lambda dz: 12 + (d_dev / 2 - 12) * dz / hl                 # noqa: E731 (radio del cono a dz de la boca)
        g_o = cq.Solid.makeCone(r_c(2) + 5.2, r_c(32) + 5.2, 30, cq.Vector(xh, 0, z0d - 2), cq.Vector(0, 0, -1))
        g_i = cq.Solid.makeCone(r_c(2) + 0.2, r_c(32) + 0.2, 30, cq.Vector(xh, 0, z0d - 2), cq.Vector(0, 0, -1))
        out["empunadura"] = g_o.cut(g_i).clean()                          # manguito aislante sobre el difusor
        info["tobera"] = (xh, z0d - hl / 2)
        info["eje_tobera"] = (xh, z0d - hl, z0d)
        return out, info

    # manguera: salida horizontal, curva y bajada paralela al cuerpo
    l_dev = {"tobera_polvo": 73.5, "tobera_chorro": 85.0, "lanza_espuma": 210.0, "lanza_k": 300.0,
             "lanza_d": 360.0, "difusor_manga": 260.0}[tipo]
    z_bot = {"lanza_k": max(dr["z_fondo"] + 15, 20.0)}.get(tipo, max(0.16 * H, dr["z_fondo"] + 40))
    lr = 19.4 if tipo == "tobera_polvo" else 12
    rb = max(8.0, min(40.0, abs(xh - (xs - lr)) - 4))
    l_dev = min(l_dev, zs - rb - 25 - z_bot)
    z_top = z_bot + l_dev
    if tipo == "tobera_polvo":
        # racor (plano Fadesa): tuerca Ø18,8 × 5,9 + casquillo Ø16,9 × 13,5 sobre la manguera
        rc = _cyl(9.4, 5.9, (xs, 0, zs), (-1, 0, 0)).fuse(_cyl(8.45, 13.5, (xs - 5.9, 0, zs), (-1, 0, 0)))
        out["racor"] = rc.clean()
    else:
        out["racor"] = cq.Solid.makeCylinder(9, 12, cq.Vector(xs, 0, zs), cq.Vector(-1, 0, 0))
    ho = _sweep_circle([(xs - lr, 0, zs), (xh, 0, zs, rb), (xh, 0, z_top + 5)], d_hose / 2)
    out["manguera"] = ho
    if tipo == "tobera_polvo":
        # portatobera Ø18,8 × 13,4 + tobera Ø19,9 × 60,1 (medidas del plano Fadesa 2,5 / 5 / 10 kg)
        body = _cyl(9.4, 13.4, (xh, 0, z_top - 13.4))
        tip = _cyl(d_dev / 2, l_dev - 13.4, (xh, 0, z_bot))
        out["tobera"] = body.fuse(tip).cut(_cyl(4, l_dev, (xh, 0, z_bot))).clean()
    elif tipo == "tobera_chorro":
        # tobera de chorro pleno: cuerpo cilíndrico + cono convergente con orificio calibrado
        body = _cyl(d_dev / 2, l_dev * 0.55, (xh, 0, z_top - l_dev * 0.55))
        tip = cq.Solid.makeCone(d_dev / 2, 6, l_dev * 0.45, cq.Vector(xh, 0, z_bot + l_dev * 0.45), cq.Vector(0, 0, -1))
        out["tobera"] = body.fuse(tip).cut(_cyl(3, l_dev, (xh, 0, z_bot))).clean()
    elif tipo == "lanza_espuma":
        # lanza espumígena: tubo con 4 tomas de aire (venturi) y boca de salida
        tubo = _tube(d_dev / 2, d_dev / 2 - 2.5, l_dev, (xh, 0, z_bot))
        cab = _cyl(11, 22, (xh, 0, z_top - 22))
        lanza = tubo.fuse(cab)
        for ang in (0, 90, 180, 270):
            dx, dy = math.cos(math.radians(ang)), math.sin(math.radians(ang))
            lanza = lanza.cut(_cyl(3.5, 12, (xh + dx * (d_dev / 2 - 6), dy * (d_dev / 2 - 6), z_top - 45),
                                   (dx, dy, 0)))
        out["lanza"] = lanza.clean()
    elif tipo == "lanza_k":
        # lanza aplicadora clase K: tubo rígido largo + boquilla de niebla en abanico a 45°
        tubo = _tube(8, 6, l_dev - 30, (xh, 0, z_bot + 30))
        cab = cq.Solid.makeCone(8, 13, 30, cq.Vector(xh, 0, z_bot + 30), cq.Vector(0, 0, -1))
        fan = _box(26, 6, 6, xh, 0, z_bot)
        out["lanza"] = tubo.fuse(cab).fuse(fan).clean()
    elif tipo == "lanza_d":
        # lanza aplicadora de flujo suave (clase D): tubo + difusor de baja velocidad
        tubo = _tube(10, 8, l_dev - 60, (xh, 0, z_bot + 60))
        dif = cq.Solid.makeCone(10, d_dev / 2, 60, cq.Vector(xh, 0, z_bot + 60), cq.Vector(0, 0, -1))
        dif = dif.cut(cq.Solid.makeCone(8, d_dev / 2 - 2, 60, cq.Vector(xh, 0, z_bot + 60), cq.Vector(0, 0, -1)))
        grip = _tube(14, 10.1, 90, (xh, 0, z_top - 110))
        out["lanza"] = tubo.fuse(dif).clean()
        out["empunadura"] = grip
    elif tipo == "difusor_manga":
        # CO2 5 kg: manga de alta presión + difusor aislante con empuñadura
        cone = cq.Solid.makeCone(10, d_dev / 2, l_dev, cq.Vector(xh, 0, z_top), cq.Vector(0, 0, -1))
        cone = cone.cut(cq.Solid.makeCone(8, d_dev / 2 - 2.5, l_dev, cq.Vector(xh, 0, z_top), cq.Vector(0, 0, -1)))
        out["difusor"] = cone.clean()
        out["empunadura"] = _tube(18, 12.1, 40, (xh, 0, z_top - 5))
    # suncho con portatobera / soporte de difusor
    zsu = z_bot + l_dev * (0.45 if tipo != "lanza_k" else 0.8)
    r_dev = {"lanza_k": 8.0, "lanza_d": 10.0, "difusor_manga": 0.0}.get(tipo, d_dev / 2)
    if tipo == "difusor_manga":
        # radio exterior del cono a la altura del soporte
        r_dev = 10 + (d_dev / 2 - 10) * (z_top - zsu + 9.0) / l_dev   # radio en el borde inferior de la banda
    hb = 14.4 if tipo == "tobera_polvo" else 18.0       # suncho portamanguera F674: banda de 14,4 (plano Fadesa)
    band = _tube(R + 1.8, R + 0.3, hb, (0, 0, zsu - hb / 2))    # abraza el cuerpo por encima de las calcomanías
    clip = _box(abs(xh) - R + r_dev + 3, 12, hb, (xh + (-R)) / 2 - 1 + (d_dev / 2 - r_dev) / 2, 0, zsu - hb / 2)
    clip = clip.cut(_cyl(r_dev + 0.2, hb, (xh, 0, zsu - hb / 2))).cut(_cyl(R + 0.3, hb, (0, 0, zsu - hb / 2)))
    out["suncho"] = band.fuse(clip).clean()
    info["tobera"] = (xh, (z_bot + z_top) / 2)
    info["eje_tobera"] = (xh, z_bot, z_top)
    info["suncho_z"] = zsu
    return out, info


# Tren rodante soldado al recipiente (proceso FLAMA de carros v2, puesto 8 «Soldadura de accesorios» y kit del puesto
# 8.1). Ejes del modelo: -Y = atrás (costura longitudinal, triángulos y caño del eje, manija, etiqueta y manómetro: es la
# vista anterior del plano); +Y = adelante (flejes del soporte de manga, manga, tobera y pata).
#  - Triángulos con V (2), chapa 4,75, cateto 70 / 80 / 100: verticales y paralelos, con el cateto vertical de canto
#    contra el cuerpo, a 65 / 82 / 107 mm (medidos sobre el cuerpo) de la costura longitudinal y el borde de abajo a 20
#    de la costura del fondo; un cordón de cada lado. La V (90°) mira hacia atrás: el caño del eje se apoya en ella (no
#    lo envuelve) y se suelda en el flanco de arriba y en el de abajo, de las dos caras; la V lo deja a 20 mm del cuerpo.
#  - Medidas de conjunto: las de la hoja de especificaciones «Polvos carros» (alto, ancho, profundidad, Ø de rueda y
#    largo de manga; corrección del usuario). El ancho es el largo del eje; de ahí salen la trocha (≥ 400, IRAM 3550
#    tabla III) y el largo del caño del eje. El alto ubica la curva de 30° de la manija. La profundidad la marca la
#    palanca de la válvula esférica (o la boca de la tobera), orientada para llegar justo al frente.
#  - Caño del eje 1" / 1¼" / 1¼" × 2,0, centrado en la costura: no gira; por adentro pasa el eje (barra trefilada),
#    que va al montaje final con las ruedas, las arandelas y los pasadores.
#  - Manija de caño 1" × 2,0 (proceso final, 8.1): patas verticales separadas A = 304 / 348 / 418 entre ejes, curva de
#    30° hacia atrás a la altura B que da el alto de la hoja, tramo inclinado C = 180 (sube 156 y se corre 90 hacia
#    atrás) y dos curvas de 90° que cierran el puño; radio de matriz 100; corte = desarrollo redondeado a 10. Las
#    puntas se aplastan en lengüetas de 40 × 60 soldadas a los costados (filete en los dos lados largos y abajo), con
#    el borde de abajo 200 bajo la costura de la cúpula.
#  - Flejes del soporte de manga, chapa 3,2 × 40: U abierta hacia afuera (perfil sombrero), base recta soldada al
#    cuerpo por el centro con un cordón corto arriba y otro abajo, patas hasta delante de la última vuelta y orejas de
#    20 hacia los costados; el superior con su borde de arriba 40 bajo la costura de la cúpula y el inferior con su
#    borde de abajo 40 sobre la del fondo. La base sale del largo de manga de la hoja (vueltas enteras, curvas de radio
#    ≥ 100). El de 100 kg (12 m) lleva un tercero en el medio, el mismo fleje con las orejas hacia adentro: la manga
#    pasa por adentro de sus patas y queda tensada; en los de dos flejes se pandea hacia los costados.
#  - Pata delantera, chapa 3,2, 80 × 60 / 80 × 60 / 100 × 80, de canto en el frente del fondo, atravesada; su borde de
#    abajo es la línea del piso (112 / 135 / 155 bajo la costura del fondo), donde también apoyan las ruedas.
# Las alturas cierran: el centro del caño (20 + cateto/4 sobre la costura del fondo) queda justo a la altura del centro
# de la rueda. Todo se suelda antes de la prueba hidráulica (IRAM 3550 6.1.1).
CARRO = dict(
    banda={300: 50.0, 350: 60.0, 400: 60.0},   # ruedas de chapa y goma, buje liso (proceso final): Ø300 × 50 (agujero
                                 # 3/4"), Ø350 × 60 y Ø400 × 60 (agujero 1"); IRAM 3550 tabla III: banda ≥ 50
    trocha_min=400.0,            # IRAM 3550 tabla III: trocha (entre centros de rueda) ≥ 400 (la fija el caño)
    rueda=(300.0, 350.0, 400.0),  # Ø de rueda que cierra con la línea del piso del proceso (112 / 135 / 155 bajo el
                                  # fondo = Rw - 20 - cateto/4): el 70 kg lleva Ø400 como el 100 kg (catálogo: 350)
    # por tamaño de cuerpo: 0 = 25 kg (Ø276,5), 1 = 50 kg (Ø320), 2 = 70 y 100 kg (Ø390)
    triangulo=((70.0, 126.0), (80.0, 157.0), (100.0, 203.0)),   # cateto / separación entre los dos (recta)
    triangulo_e=4.75, triangulo_sobre_fondo=20.0,
    cano_eje=((25.4, 2.0, 354.0), (31.75, 2.0, 354.0), (31.75, 2.0, 434.0)),   # 1" / 1¼" / 1¼" × 2,0 × largo
    luz_cano=20.0,               # la V deja el caño a 20 mm del cuerpo (en la costura, atrás al centro)
    eje=(19.05, 25.4, 25.4),     # barra trefilada SAE 1045 3/4" / 1" (montaje final): entra en el caño (Ø int. 21,4 /
                                 # 27,75)
    eje_largo=(490.0, 510.0, 590.0),
    arandela=(40.0, 4.0),        # arandela de tope Ø40 × 4 (Ø int. = eje + 1)
    pasador=(4.0, 40.0),         # pasador partido Ø4 × 40 en cada punta del eje
    manija=(25.4, 2.0, 1.0, 100.0, 30.0),  # caño 1" × 2,0; luz 1 entre caño y cuerpo; radio de matriz 100; doblez 30°
    manija_B=(231.0, 249.0, 249.0),        # curva de 30° sobre la costura de la cúpula
    manija_C=180.0,                        # tramo inclinado (entre vértices)
    manija_corte=(1440.0, 1520.0, 1590.0),
    lengueta=(60.0, 15.0, 4.0, 40.0),      # lengüeta aplastada: largo 60, transición 15, e 4 (2 paredes), ancho 40
    lengueta_bajo_cupula=200.0,            # borde de abajo de la lengüeta bajo la costura de la cúpula
    fleje=(40.0, 3.2, 20.0),                # ancho de la chapa, espesor, orejas (por fuera, hacia los costados)
    fleje_base=(166.0, 192.0, 234.0),       # base por fuera de las patas
    fleje_estiramiento=6.0,                 # lo que se estira la chapa de 3,2 en cada doblez (r int. ≈ 3): se resta
                                            # del largo de corte; las patas salen del paquete de manga (FLEJE)
    fleje_bajo_cupula=40.0, fleje_sobre_fondo=40.0,
    pata=((80.0, 60.0), (80.0, 60.0), (100.0, 80.0)),   # 80 × 60 (25 y 50 kg), 100 × 80 (70 y 100 kg)
    pata_e=3.2,                  # orilla de 3,2 mm de la hoja de 25 kg (todas las patas)
)


def fleje_carro(cod):
    """(ancho, e, pata, oreja, base por fuera, corte) del fleje del soporte de manga del modelo (después del modelo 3D:
    las patas llegan hasta delante de la última vuelta de la manga)."""
    fa, fe, fo = CARRO["fleje"]
    lb, pata, corte, _ = FLEJE[cod]
    return fa, fe, pata, fo, lb, corte


def tam_carro(R):
    """0 = 25 kg, 1 = 50 kg, 2 = 70 y 100 kg (por el radio del cuerpo)."""
    return 0 if R < 150 else (1 if R < 180 else 2)


def rueda_d(m):
    """Ø de rueda del carro: el de la hoja de especificaciones del modelo; si no la tiene, el del proceso (CARRO)."""
    if m.spec.get("Diámetro de rueda (mm)"):
        return float(str(m.spec["Diámetro de rueda (mm)"]).replace(".", ""))
    return CARRO["rueda"][tam_carro(m.geo["R"])]


def extintor_rodante(m, cD=0.0):
    g = dict(m.geo)
    H, W, D = m.H, m.W, m.D
    Dw = rueda_d(m)                                        # proceso (IRAM 3550 tabla III: Ø ≥ 300)
    Rw = Dw / 2
    bw_w = CARRO["banda"][int(Dw)]
    R = g["R"]
    t = g["t"]
    k = tam_carro(R)
    a_tri, sep_tri = CARRO["triangulo"][k]
    # altura del recipiente: la costura del fondo queda a Rw - 20 - cateto/4 del piso, así el centro del caño del eje
    # (apoyado en la V) coincide con el centro de la rueda y el carro apoya derecho en las ruedas y la pata
    _, dr0 = recipiente(dict(g), 0.0, costura=False)
    zb_obj = Rw - CARRO["triangulo_sobre_fondo"] - a_tri / 4
    piezas, dr = recipiente(dict(g), zb_obj - dr0["zb"], costura=True)
    out = dict(piezas)
    info = dict(recipiente=dr)
    lleno = _lleno(dr)
    d_hose = 23.5                             # manga: dos en fondo entre la base y la oreja del fleje (≈48)
    zb, zu = dr["zb"], dr["z_union"]
    # pata delantera (adelante, +Y): de canto, atravesada, apoyada en el piso y soldada al frente del fondo; se corre
    # hacia adentro hasta que su borde de arriba toca el casquete (el recorte la ajusta a la curva)
    pw, hp = CARRO["pata"][k]
    tp = CARRO["pata_e"]
    yp = 0.0
    for i in range(1, int(R)):
        if not lleno.isInside(cq.Vector(0.0, float(i) + tp, hp - 0.5)):   # el borde de arriba toca en el centro;
            break                                                          # en las puntas queda luz (proceso)
        yp = float(i)
    out["tercera_pata"] = _box(pw, tp, hp, 0, yp + tp / 2, 0).cut(lleno).cut(out["fondo"]).clean()
    # caño del eje apoyado en la V de los dos triángulos, a 20 del cuerpo en la costura (atrás al centro)
    dce, ece, lce = CARRO["cano_eje"][k]
    rce = dce / 2
    z_tri = zb + CARRO["triangulo_sobre_fondo"]
    zc = z_tri + a_tri / 4                     # centro del caño = vértice de la V = centro de la rueda (= Rw)
    yc = -(R + CARRO["luz_cano"] + rce)
    # triángulos con V: perfil en el plano del triángulo (u = distancia hacia atrás desde la pared, z)
    et = CARRO["triangulo_e"]
    xs = sep_tri / 2
    ys = -math.sqrt(R * R - xs * xs)          # pared del cuerpo en el plano del triángulo
    u_c = ys - yc                              # centro del caño, medido desde la pared
    u_a = u_c - rce * math.sqrt(2)            # vértice de la V: el caño toca los dos flancos (V de 90°)
    s_fl = 1.13 * rce                          # flanco de arriba (≈ 1,6 r): el caño apoya bien
    perfil = [(-8.0, z_tri), (-8.0, z_tri + a_tri), (0.0, z_tri + a_tri), (u_a + s_fl, zc + s_fl), (u_a, zc),
              (u_a + (zc - z_tri), z_tri)]
    pts = [(ys - u, z) for u, z in perfil]
    sop = None
    for sgn in (1, -1):
        pl = cq.Workplane("YZ").polyline(pts).close().extrude(et).val().translate(cq.Vector(sgn * xs - et / 2, 0, 0))
        sop = pl if sop is None else sop.fuse(pl)
    out["soportes_eje"] = sop.cut(lleno).cut(out["cuerpo"]).clean()
    # etiqueta del carro: si con las alas de 54° no entra entre los triángulos y las lengüetas de la manija, las alas
    # se acortan hasta terminar 4° antes de las lengüetas (que van a los costados, a 90° de la costura)
    from .rotulado import disposicion
    ALA_CARRO.pop(m.codigo, None)
    alto_et = disposicion(m, math.radians(ARCO_PLACA) * R, ala_dim(R))["H"]
    banda_et = (zu - CARRO["lengueta_bajo_cupula"] - 10.0) - (z_tri + a_tri + 10.0)
    if alto_et > banda_et:
        ALA_CARRO[m.codigo] = 90.0 - ARCO_PLACA / 2 - math.degrees(CARRO["lengueta"][3] / 2 / R) - 4.0
    # ruedas: el ancho total de la hoja de especificaciones es el largo del eje (las puntas, 7 más allá del pasador);
    # de ahí salen la trocha y el largo del caño (caño + arandela interior + medio ancho de rueda). La trocha no baja
    # de 400 (IRAM 3550 tabla III)
    de_ = CARRO["eje"][k]
    da, ea = CARRO["arandela"]
    dpa, lpa = CARRO["pasador"]
    xw = max(W / 2 - 7.0 - dpa / 2 - 1.0 - ea - bw_w / 2, CARRO["trocha_min"] / 2)
    lce = 2 * (xw - ea - bw_w / 2)
    track = 2 * xw
    out["portaeje"] = _tube(rce, rce - ece, lce, (-lce / 2, yc, zc), (1, 0, 0))
    yw = yc
    for sgn, suf in ((1, "der"), (-1, "izq")):
        c = cq.Vector(sgn * (xw - bw_w / 2), yw, zc)              # cara interna; la rueda queda centrada en ±xw
        # neumático macizo (anillo de caucho) + llanta de chapa (disco con cubo)
        tire = _cyl(Rw, bw_w, (c.x, c.y, c.z), (sgn, 0, 0))
        tire = tire.cut(_cyl(Rw * 0.72, bw_w, (c.x, c.y, c.z), (sgn, 0, 0)))
        # llanta de chapa estampada: aro e = 2, disco e = 2,5, cubo con buje para el eje
        llanta = _tube(Rw * 0.72, Rw * 0.72 - 2, bw_w - 6, (c.x + sgn * 3, c.y, c.z), (sgn, 0, 0))
        llanta = llanta.fuse(_cyl(Rw * 0.72 - 2, 2.5, (c.x + sgn * (bw_w / 2 - 1.25), c.y, c.z), (sgn, 0, 0)))
        llanta = llanta.fuse(_tube(de_ / 2 + 17, de_ / 2 + 0.5, bw_w, (c.x, c.y, c.z), (sgn, 0, 0)))
        llanta = llanta.cut(_cyl(de_ / 2 + 0.5, bw_w + 2, (c.x - sgn, c.y, c.z), (sgn, 0, 0)))   # buje para el eje
        out["rueda_" + suf] = tire
        out["llanta_" + suf] = llanta.clean()
    # eje (barra) por adentro del caño, arandela a cada lado de la rueda y pasador partido en cada punta
    x_out = xw + bw_w / 2
    x_pas = x_out + ea + dpa / 2 + 1.0        # pasador por fuera de la arandela exterior
    l_eje = 2 * (x_pas + 7.0)                 # barra cortada a largo en el puesto 8.1 (= ancho total)
    out["eje_ruedas"] = _cyl(de_ / 2, l_eje, (-l_eje / 2, yw, zc), (1, 0, 0)).cut(
        _cyl(dpa / 2 + 0.3, 2 * de_, (x_pas, yw, zc - de_), (0, 0, 1))).cut(
        _cyl(dpa / 2 + 0.3, 2 * de_, (-x_pas, yw, zc - de_), (0, 0, 1))).clean()
    ar = None
    for sgn in (1, -1):
        for xx in (lce / 2, x_out):
            a_ = _tube(da / 2, de_ / 2 + 0.5, ea, (sgn * xx if sgn > 0 else -xx - ea, yw, zc), (1, 0, 0))
            ar = a_ if ar is None else ar.fuse(a_)
    out["arandelas_tope"] = ar.clean()
    pas = None
    for sgn in (1, -1):
        p_ = _cyl(dpa / 2, lpa, (sgn * x_pas, yw, zc - lpa / 2 + de_ / 2 + 4), (0, 0, 1))
        p_ = p_.fuse(_torus(dpa * 1.2, dpa / 2, zc + de_ / 2 + 4 + dpa, sgn * x_pas, yw, (1, 0, 0)))
        pas = p_ if pas is None else pas.fuse(p_)
    out["pasadores_eje"] = pas.clean()
    # manija (proceso final): lengüetas aplastadas soldadas a los costados, patas verticales pegadas al cuerpo hasta la
    # curva de 30° (B sobre la costura de la cúpula), tramo inclinado C hacia atrás y dos curvas de 90° que cierran el
    # puño; todas las curvas con el radio de la matriz
    dm, em, luz, rb, ang = CARRO["manija"]
    lf, lt, tf, wf = CARRO["lengueta"]
    rt = dm / 2
    xm = R + luz + rt                         # eje de las patas (A = 2 xm)
    ym = 0.0
    z_low = zu - CARRO["lengueta_bajo_cupula"]    # borde de abajo de la lengüeta
    z_tubo = z_low + lf + lt                  # donde el caño sigue redondo
    cc_ = CARRO["manija_C"]
    z_bend = H - rt - cc_ * math.cos(math.radians(ang))   # vértice de la curva de 30°: el puño queda a la altura
    zg = z_bend + cc_ * math.cos(math.radians(ang))        # total de la hoja de especificaciones
    yg = -cc_ * math.sin(math.radians(ang))
    man = _sweep_circle([(-xm, ym, z_tubo), (-xm, ym, z_bend, rb), (-xm, yg, zg, rb),
                         (xm, yg, zg, rb), (xm, ym, z_bend, rb), (xm, ym, z_tubo)], rt)
    MANIJA_LARGO[m.codigo] = man.Volume() / (math.pi * rt * rt) + 2 * (lf + lt)   # largo desarrollado del caño
    corte = 10.0 * math.ceil(MANIJA_LARGO[m.codigo] / 10.0)                     # corte: desarrollo, a 10 mm
    CARRO_MOD[m.codigo] = dict(rueda=Dw, eje_largo=l_eje, cano_largo=lce, manija_B=z_bend - zu, manija_corte=corte,
                               trocha=track)
    for sgn in (1, -1):
        # transición redonda -> plana (se corre hacia el cuerpo) y lengüeta apoyada en la pared
        xf = sgn * (R + 0.2 + tf / 2)
        circ = cq.Wire.makeCircle(rt, cq.Vector(sgn * xm, ym, z_tubo), cq.Vector(0, 0, 1))
        rect = cq.Wire.makePolygon([cq.Vector(xf - tf / 2, ym - wf / 2, z_low + lf),
                                    cq.Vector(xf + tf / 2, ym - wf / 2, z_low + lf),
                                    cq.Vector(xf + tf / 2, ym + wf / 2, z_low + lf),
                                    cq.Vector(xf - tf / 2, ym + wf / 2, z_low + lf)], close=True)
        man = man.fuse(cq.Solid.makeLoft([circ, rect], True))
        man = man.fuse(_box(tf, wf, lf, xf, ym, z_low))
    out["manija_carro"] = man.cut(lleno).clean()
    info.update(dict(portaeje=(dce, ece, lce), aplastado=(z_low, lf, lt, tf, wf), z_doblez=z_bend,
                     z_doblez_inicio=z_bend - rb * math.tan(math.radians(ang / 2)), y_agarre=yg, angulo_manija=ang,
                     corte_manija=corte, soporte_tri=(a_tri, xs, z_tri, ys, u_a, s_fl, rce), tam_carro=k,
                     eje_d=de_, H_carro=zg + rt))
    # válvula: manómetro hacia atrás (lado de la etiqueta); palanca de la G763 hacia adelante, 0,75·R
    val, vi = valvula(dr["z_cuello"], tipo=tipo_valvula(m), dn=g["cuello"][0], bore=dr["bore"], x_tip=R * 0.75,
                      man_d=47.0)             # manómetro con cubremanómetro G711: Ø47 (plano Fadesa 25 / 50 kg)
    s = vi["s"]
    out.update(val)
    info["valvula"] = vi
    zf = dr["z_fondo"] + g["tf"] + 25
    out["cano_pesca"] = _tube(12, 9.5, dr["z_cuello"] - 12 * s - zf, (0, 0, zf))
    xsal, zsal = vi["x_salida"], vi["z_salida"]
    out["racor"] = _cyl(12, 16, (xsal, 0, zsal), (-1, 0, 0))
    # flejes del soporte de manga adelante (+Y), al centro: U de chapa abierta hacia afuera (perfil sombrero), base
    # recta que toca el cuerpo en el centro y ahí se suelda, patas derechas hacia adelante y orejas hacia los costados.
    # Las patas cubren todo el paquete de manga: la oreja queda por delante de la última vuelta y no la deja salirse.
    # El de 100 kg (12 m) lleva un tercero en el medio: el mismo fleje con las orejas dobladas hacia adentro; la manga
    # pasa por adentro de sus patas, más cerca del centro que en los de arriba y abajo, así que el paquete se cierra en
    # el medio y queda tensado (corrección del usuario: el del medio comprime y no la deja pandear)
    fa, fe, fo = CARRO["fleje"]
    lb = CARRO["fleje_base"][k]               # base por fuera de las patas (de partida: sale del largo de manga, abajo)
    z_fs = zu - CARRO["fleje_bajo_cupula"] - fa                  # fleje superior: borde de arriba 40 bajo la cúpula
    z_fi = zb + CARRO["fleje_sobre_fondo"]                       # fleje inferior: borde de abajo 40 sobre el fondo
    largo_cat = float(m.spec.get("Longitud de manga (m)", "5").replace(",", ".")) * 1000.0
    tres = largo_cat >= 8000.0

    def _fleje(zz, ancho, pata, adentro):
        """U de chapa: base recta contra el frente, patas hacia adelante y orejas hacia los costados (hacia afuera) o
        hacia el medio (hacia adentro: el fleje del medio del 100 kg, que encierra y cierra el paquete de manga)."""
        f_ = _box(ancho, fe, fa, 0, R + fe / 2, zz)                                    # base
        for sx in (1, -1):
            f_ = f_.fuse(_box(fe, pata, fa, sx * (ancho / 2 - fe / 2), R + pata / 2, zz))   # pata
            xo_ = ancho / 2 - fe - fo / 2 if adentro else ancho / 2 - fe + fo / 2
            f_ = f_.fuse(_box(fo, fe, fa, sx * xo_, R + pata - fe / 2, zz))           # oreja
        return f_
    # manga: una sola, continua. Sale de la válvula, baja en una curva sobre la cúpula y se enrolla en un lazo vertical
    # alrededor de los flejes, una vuelta delante de la otra (del cuerpo hacia adelante), por afuera de las patas y
    # por detrás de las orejas. Con dos flejes la manga, rígida, se pandea hacia los costados entre ellos; con tres va
    # tensa: de afuera de las patas (arriba y abajo) a adentro de las del medio. El giro de abajo cuelga bajo el fleje
    # inferior y el de arriba apoya sobre el superior
    V_ = cq.Vector
    rh = d_hose / 2
    z_ft = z_fs + fa
    paso_r = d_hose + 1.0
    filas = [R + fe + rh + 0.3 + i_ * paso_r for i_ in range(10)]   # una fila por vuelta, del cuerpo hacia adelante
    y_f = (filas[0], filas[1])
    x0 = lb / 2 + rh + 1.5                    # arriba y abajo: por afuera de las patas
    x_m = lb / 2 - fe - 1.5 - rh              # en el medio: por adentro de las patas del fleje hacia adentro
    lugar = [(x0, y_) for y_ in filas]
    # punta (corrección del usuario): baja derecha por la izquierda en la última fila, sigue de largo y abajo se abre
    # hacia afuera, al costado del paquete; la válvula esférica y la tobera siguen esa línea y apuntan hacia afuera y
    # abajo, con la palanca hacia adelante. Todo queda dentro del ancho y la profundidad de la hoja de especificaciones
    lanza = m.descarga == "lanza_espuma_rodante"
    hn = 380.0 if lanza else 200.0
    hv = 56.0                                 # cuerpo de la válvula esférica Ø40 × 56 con dos hexágonos de 46
    L_t = 12.0 + hv + hn                      # de la punta de la manga (espiga) a la boca
    r_boca = 28.0 if lanza else 34.0
    z_flejes = [z_fs, round((z_fs + z_fi) / 2), z_fi] if tres else [z_fs, z_fi]
    z_m = z_flejes[1]
    z_a = (z_m if tres else z_fs) - 2.0       # la punta deja el último fleje que atraviesa
    y_frente = D + yw - Rw                    # frente del carro: profundidad de la hoja desde atrás de las ruedas
    zc_f = sorted((zz + fa / 2 for zz in z_flejes), reverse=True)  # centros de los flejes, de arriba abajo
    xs_f = [x0, x_m, x0] if tres else [x0, x0]

    b_pand = min(40.0, max(16.0, 0.065 * (zc_f[0] - zc_f[-1])))   # dos flejes: flecha ≈ 6,5 % del tramo libre

    def _pandeo(i_, lado):
        """corrimiento hacia afuera de la manga en el medio, entre los dos flejes: la manga es rígida y se pandea."""
        return b_pand * (0.85 + 0.3 * (i_ % 2)) * (1.0 if lado < 0 else 0.85 + 0.2 * ((i_ + 1) % 2))

    def _z_ent():
        """altura a la que la bajada de la válvula entra al lazo (arriba a la izquierda), siempre bajando."""
        return max(z_ft + 30.0, min(z_ft + 4.0 + 0.97 * x0, zsal - 130.0))

    def _bajada(i_, y_, lado, sube):
        """vértices de un tramo vertical: derecho en cada fleje; entre ellos pandeado (dos flejes) o tenso (tres)."""
        v_ = []
        for t_, zc_ in enumerate(zc_f):
            v_ += [(lado * xs_f[t_], y_, zc_ + fa / 2 + 2.0) + ((250.0,) if t_ else ()),
                   (lado * xs_f[t_], y_, zc_ - fa / 2 - 2.0) + ((250.0,) if t_ < len(zc_f) - 1 else ())]
            if not tres and t_ < len(zc_f) - 1:
                # pandeo en un arco parejo: sale y llega derecho a los flejes (sen²), con curvas amplias
                za_, zb_ = zc_ - fa / 2 - 2.0, zc_f[t_ + 1] + fa / 2 + 2.0
                for k_ in range(1, 8):
                    u_ = k_ / 8.0
                    v_.append((lado * (xs_f[t_] + _pandeo(i_, lado) * math.sin(math.pi * u_) ** 2), y_,
                               za_ - u_ * (za_ - zb_), 400.0))
        return v_[::-1] if sube else v_

    def _rollo(n_):
        r_u0 = z_fi - 5.0 - (45.0 + rh)                          # el giro de abajo no llega al piso
        v_ = []
        for i_ in range(n_):
            x_, y_ = lugar[i_]
            xn_, yn_ = lugar[i_ + 1]
            r_t = 0.97 * min(x_, xn_)
            z_t = z_ft + 4.0 + r_t                               # el giro de arriba apoya sobre el fleje superior
            r_u = min(0.97 * x_, r_u0)
            z_u = z_fi - 5.0 - r_u                               # el giro de abajo cuelga bajo el fleje inferior
            if i_ == 0:
                v_.append((-x_, y_, _z_ent()))
            v_ += _bajada(i_, y_, -1, False)
            v_ += [(-x_, y_, z_u, r_u), (x_, y_, z_u, r_u)]
            v_ += _bajada(i_, y_, 1, True)
            v_ += [(x_, y_, z_t, r_t), (-xn_, yn_, z_t, r_t)]
        v_.append((-lugar[n_][0], lugar[n_][1], z_ft + 2.0))
        return v_

    def _largo(v_):
        L_ = 0.0
        for i_ in range(1, len(v_)):
            L_ += (V_(*v_[i_][:3]) - V_(*v_[i_ - 1][:3])).Length
        for i_ in range(1, len(v_) - 1):
            if len(v_[i_]) > 3:
                a_ = (V_(*v_[i_ - 1][:3]) - V_(*v_[i_][:3])).normalized()
                b_ = (V_(*v_[i_ + 1][:3]) - V_(*v_[i_][:3])).normalized()
                an_ = math.acos(max(-1.0, min(1.0, a_.dot(b_))))
                if an_ < math.pi - 1e-3:
                    L_ -= 2 * v_[i_][3] / math.tan(an_ / 2) - v_[i_][3] * (math.pi - an_)
        return L_

    # bajada de la válvula: sale de costado, se curva hacia adelante y abajo por encima de la cúpula (con luz sobre
    # la chapa) y entra vertical a la primera vuelta, arriba a la izquierda
    xr0 = xsal - 16.0

    def _libre(a_, b_):
        for t_ in range(1, 25):
            q_ = a_ + (b_ - a_) * (t_ / 25.0)
            for dx_, dy_, dz_ in ((0, 0, -1), (0.7, -0.7, 0), (0, -1, 0), (0.7, 0, -0.7), (0, -0.7, -0.7)):
                if lleno.isInside(V_(q_.x + dx_ * (rh + 6), q_.y + dy_ * (rh + 6), q_.z + dz_ * (rh + 6))):
                    return False
        return True

    def _ruta():
        """bajada de la válvula: sale de costado y baja siempre (sin ondas) en una curva amplia sobre la cúpula hasta
        entrar vertical a la primera vuelta."""
        x_0, y_0 = lugar[0]
        z_e = _z_ent()
        z_c = zsal - 10.0
        for _ in range(12):
            r_c = max(40.0, min(110.0, z_c - z_e - 5.0))
            r_ = [(xr0, 0.0, zsal), (xr0 - 30.0, 0.0, zsal, 25.0), (-x_0, y_0, z_c, r_c), (-x_0, y_0, z_e)]
            if _libre(V_(*r_[1][:3]), V_(*r_[2][:3])):
                break
            z_c += 5.0                        # no debería pasar: la cúpula queda por debajo
        return r_

    def _rot(v_, th_, ps_, ph_=0.0):
        """giro de la válvula: ph_ sobre su eje (la palanca de adelante hacia afuera), ps_ hacia adelante, th_ hacia
        afuera (-x). Con el eje local -z (la espiga arriba)."""
        x_, y_, z_ = v_
        x_, y_ = x_ * math.cos(ph_) - y_ * math.sin(ph_), x_ * math.sin(ph_) + y_ * math.cos(ph_)
        y_, z_ = y_ * math.cos(ps_) - z_ * math.sin(ps_), y_ * math.sin(ps_) + z_ * math.cos(ps_)
        return x_ * math.cos(th_) + z_ * math.sin(th_), y_, -x_ * math.sin(th_) + z_ * math.cos(th_)

    # palanca (respecto del centro de la válvula): chapa y empuñadura; cuello del vástago
    pal_pts = ([(x_, y_, z_) for x_ in (-35.0, -32.0) for y_ in (-7.5, 97.5) for z_ in (-8.0, 8.0)] +
               [(x_, y_, z_) for x_ in (-37.0, -30.0) for y_ in (42.5, 97.5) for z_ in (-10.0, 10.0)] +
               [(-32.0, 0.0, 7.0), (-32.0, 0.0, -7.0)])
    R_b = 350.0 if tres else 450.0                                # única curva de la punta, amplia y pareja

    def _fila_atras(n_, z_):
        """x de la fila de atrás de la punta (la n-1, del lado izquierdo) a la altura z_."""
        if tres:
            if z_ >= z_m:
                return x_m
            f_ = (z_m - 2.0 - z_) / max(1.0, (z_m - 2.0) - (z_fi + fa + 2.0))
            return x_m + (x0 - x_m) * min(1.0, max(0.0, f_))
        zt_, zb_ = zc_f[0] - fa / 2 - 2.0, zc_f[-1] + fa / 2 + 2.0
        b_ = b_pand * (0.85 + 0.3 * ((n_ - 1) % 2))
        if zb_ < z_ < zt_:
            return x0 + b_ * math.sin(math.pi * (zt_ - z_) / (zt_ - zb_)) ** 2
        return x0

    def _geo_punta(n_, th_, ps_, ph_):
        """punta derecha desde abajo del último fleje que atraviesa: la manga, la válvula y la tobera en una línea."""
        y_n = filas[n_]
        u0 = x_m if tres else x0
        a_ = _rot((0.0, 0.0, -1.0), th_, ps_)                     # eje (x, y, z); hacia afuera es -x
        tilt = math.acos(-a_[2])
        t_ = R_b * math.tan(tilt / 2)
        V_z = z_a - t_ - 2.0
        r_z0 = r_boca * math.sqrt(max(0.0, 1 - a_[2] ** 2))
        L_ = (V_z - (60.0 + r_z0)) / -a_[2]                       # sigue de largo: la boca cerca del piso
        L_h = max(L_ - L_t, t_ + 5.0)                             # tramo recto de manga hasta la espiga
        P_ = lambda d_: (-u0 + a_[0] * d_, y_n + a_[1] * d_, V_z + a_[2] * d_)   # noqa: E731
        vc = P_(L_h + 12.0 + hv / 2)
        M_ = P_(L_h + L_t)
        pal = [tuple(vc[i] + q[i] for i in range(3)) for q in (_rot(c_, th_, ps_, ph_) for c_ in pal_pts)]
        r_u = r_boca * math.sqrt(max(0.0, 1 - a_[0] ** 2))
        r_y = r_boca * math.sqrt(max(0.0, 1 - a_[1] ** 2))
        r_z = r_boca * math.sqrt(max(0.0, 1 - a_[2] ** 2))
        frente = max(max(q[1] for q in pal), M_[1] + r_y, vc[1] + 26.6)
        ancho = max(max(-q[0] for q in pal), -M_[0] + r_u, -vc[0] + 26.6)
        return dict(y_n=y_n, u0=u0, a=a_, V_z=V_z, L_h=L_h, vc=vc, M=M_, frente=frente, ancho=ancho, r_z=r_z,
                    r_u=r_u, r_y=r_y, tilt=tilt)

    def _ok_punta(n_, g_):
        """libre de las filas, del fleje de abajo y del piso, y dentro del ancho de la hoja."""
        if g_["ancho"] > W / 2 - 3.0 or g_["M"][2] - g_["r_z"] < 15.0:
            return False
        y_or = filas[n_] + rh + 0.5 + fe / 2                      # oreja del fleje de abajo (centro, en y)
        u_or = (lb / 2 - fe, lb / 2 - fe + fo)
        d_ = g_["L_h"] + 6.0
        while d_ <= g_["L_h"] + L_t:
            e_ = d_ - g_["L_h"] - 12.0
            rr_ = 14.0 if e_ < 0 else (26.6 if e_ <= hv else (16.0 + (r_boca - 16.0) * (e_ - hv) / hn))
            q_ = (-g_["u0"] + g_["a"][0] * d_, g_["y_n"] + g_["a"][1] * d_, g_["V_z"] + g_["a"][2] * d_)
            if math.hypot(-q_[0] - _fila_atras(n_, q_[2]), q_[1] - (g_["y_n"] - paso_r)) < rr_ + rh + 2.0:
                return False                                      # contra la fila de atrás
            if z_fi - rr_ - 2.0 < q_[2] < z_fi + fa + rr_ + 2.0 and u_or[0] - rr_ - 2.0 < -q_[0] < u_or[1] + rr_ + 2.0 \
                    and abs(q_[1] - y_or) < fe / 2 + rr_ + 2.0:
                return False                                      # contra la oreja del fleje de abajo
            d_ += 8.0
        return True

    def _punta(n_, exacta=True):
        """recorrido de la punta y orientación de la válvula: la palanca lo más hacia adelante que deja la profundidad
        de la hoja (girándola hacia afuera si hace falta), la tobera lo más hacia afuera que deja el ancho y hacia
        adelante lo justo para que el frente coincida con la profundidad (si no entra, lo que menos se pasa)."""
        sel = (math.radians(12.0), math.radians(5.0), math.radians(45.0))
        if exacta:
            mejor = None
            for ph_g in range(0, 80, 5):
                for th_g in range(25, -1, -1):
                    ph_, th_ = math.radians(ph_g), math.radians(th_g)
                    lo, hi = 0.0, math.radians(20.0)
                    if _geo_punta(n_, th_, lo, ph_)["frente"] > y_frente + 0.5:
                        ps0 = 0.0
                    elif _geo_punta(n_, th_, hi, ph_)["frente"] < y_frente:
                        ps0 = hi
                    else:
                        for _ in range(30):
                            md = (lo + hi) / 2
                            if _geo_punta(n_, th_, md, ph_)["frente"] < y_frente:
                                lo = md
                            else:
                                hi = md
                        ps0 = lo
                    for k_ in range(151):                         # si choca, un poco más hacia adelante
                        ps_ = ps0 + math.radians(0.1 * k_)
                        g_ = _geo_punta(n_, th_, ps_, ph_)
                        if _ok_punta(n_, g_):
                            exc = g_["frente"] - y_frente
                            exc = 0.0 if exc <= 0.5 else exc             # la profundidad de la hoja (± 0,5)
                            if mejor is None or exc < mejor[0] - 0.5:
                                mejor = (exc, (th_, ps_, ph_))
                            break
                    if mejor and mejor[0] == 0.0:
                        break
                if mejor and mejor[0] == 0.0:
                    break
            if mejor is None:
                AVISOS_CARRO.append(f"{m.codigo}: la punta no entra sin tocar el paquete")
                sel = (0.0, 0.0, math.radians(45.0))
            else:
                sel = mejor[1]
                av_ = f"{m.codigo}: la palanca / tobera pasa {mejor[0]:.0f} mm la profundidad"
                if mejor[0] > 0 and av_ not in AVISOS_CARRO:
                    AVISOS_CARRO.append(av_)
        th_, ps_, ph_ = sel
        g_ = _geo_punta(n_, th_, ps_, ph_)
        u0, y_n, a_ = g_["u0"], g_["y_n"], g_["a"]
        v_ = [(-x0, y_n, z_ft + 2.0)]
        if tres:                              # tensa hasta adentro de las patas del fleje del medio
            v_ += [(-x0, y_n, z_fs - 2.0, 250.0), (-x_m, y_n, z_m + fa + 2.0, 250.0)]
        v_ += [(-u0, y_n, g_["V_z"], R_b), (-u0 + a_[0] * g_["L_h"], y_n + a_[1] * g_["L_h"], g_["V_z"] + a_[2] * g_["L_h"])]
        return v_[-1][0], v_[-1][1], v_, (v_[-1][2], th_, ps_, ph_)

    # vueltas y base: la manga del catálogo da vueltas enteras. Se busca el menor número de vueltas y, con él, la base
    # más chica que alcanza el largo, entre la curva mínima de la manga (radio ≥ 100 en los giros) y el ancho del cuerpo
    # (el paquete no sale de la silueta). Menos vueltas = curvas más abiertas y patas más cortas
    L_r = _largo(_ruta())
    lb_min, lb_max = 2 * (100.0 - rh - 1.5), 2 * R - 2 * (1.5 + d_hose)
    elegido = None
    for n_v in range(1, 9):
        for i_ in range(int((lb_max - lb_min) / 2) + 1):
            lb = 2 * math.ceil(lb_min / 2) + 2 * i_
            x0, x_m = lb / 2 + rh + 1.5, lb / 2 - fe - 1.5 - rh
            lugar, xs_f = [(x0, y_) for y_ in filas], ([x0, x_m, x0] if tres else [x0, x0])
            if L_r + _largo(_rollo(n_v)) + _largo(_punta(n_v, False)[2]) >= largo_cat:
                elegido = (n_v, lb)
                break
        if elegido:
            break
    n_v, lb = elegido
    while True:                               # con el tramo de la válvula real (cambia un poco con la base)
        x0, x_m = lb / 2 + rh + 1.5, lb / 2 - fe - 1.5 - rh
        lugar, xs_f = [(x0, y_) for y_ in filas], ([x0, x_m, x0] if tres else [x0, x0])
        ruta = _ruta()
        if _largo(ruta) + _largo(_rollo(n_v)) + _largo(_punta(n_v)[2]) >= largo_cat or lb + 2 > lb_max:
            break
        lb += 2
    out["manguera_enrollada"], _ = _tubo(_rollo(n_v), rh)
    xn, yn, v_p, (z_S, th, psi, phi) = _punta(n_v)
    out["manguera"] = _tubo(ruta, rh)[0].fuse(_tubo(v_p, rh)[0]).clean()
    MANGA_CAPAS[m.codigo] = (n_v + 1, len(lugar), y_f[0], y_f[1])
    MANGA_LARGO[m.codigo] = _largo(ruta) + _largo(_rollo(n_v)) + _largo(v_p)
    # flejes: todos iguales (base, patas hasta delante de la última fila); el del medio del 100 kg con las orejas
    # hacia adentro
    pata = filas[n_v] + rh + 0.5 + fe - R
    FLEJE[m.codigo] = (lb, pata, lb + 2 * pata + 2 * fo - 4 * CARRO["fleje_estiramiento"], len(z_flejes))
    FLEJE_MEDIO[m.codigo] = (lb, pata) if tres else None
    gan = None
    for zz in z_flejes:
        medio = zz not in (z_flejes[0], z_flejes[-1])
        f_ = _fleje(zz, lb, pata, medio)
        gan = f_ if gan is None else gan.fuse(f_)
    out["ganchos_manguera"] = gan.cut(lleno).clean()
    # válvula esférica y tobera: armadas con el eje vertical (espiga arriba, en el origen) e inclinadas hacia afuera
    zv0 = -12.0 - hv                          # base de la válvula = boca de entrada de la tobera
    zm0 = -12.0 - hv / 2
    ve = _cyl(20, hv, (0, 0, zv0))
    for z_h in (zv0, zv0 + hv - 10):
        ve = ve.fuse(cq.Workplane("XY").polygon(6, 46).extrude(10).val().translate(cq.Vector(0, 0, z_h)))
    ve = ve.fuse(_cyl(7, 12, (-20, 0, zm0), (-1, 0, 0)))            # cuello del vástago, hacia afuera
    pal = _box(3, 105, 16, -33.5, 45, zm0 - 8)                     # palanca de chapa, cerrada (atravesada al
    pal = pal.fuse(_box(7, 55, 20, -33.5, 70, zm0 - 10))          # caño), hacia adelante; empuñadura (azul)
    ve = ve.fuse(_cyl(14, 12, (0, 0, -12.0)))                      # espiga de la manga con abrazadera
    ve = ve.fuse(pal).clean()
    if lanza:
        # lanza espumígena de rodante: tubo Ø40 con 4 tomas de aire y boca expandida
        tubo = _tube(20, 17.5, hn - 40, (0, 0, zv0 - hn + 40))
        boca = cq.Solid.makeCone(20, 28, 40, cq.Vector(0, 0, zv0 - hn + 40), cq.Vector(0, 0, -1))
        boca = boca.cut(cq.Solid.makeCone(17.5, 25.5, 40, cq.Vector(0, 0, zv0 - hn + 40), cq.Vector(0, 0, -1)))
        tb = tubo.fuse(boca)
        for ang in (0, 90, 180, 270):
            dx, dy = math.cos(math.radians(ang)), math.sin(math.radians(ang))
            tb = tb.cut(_cyl(5, 12, (dx * 14, dy * 14, zv0 - 40), (dx, dy, 0)))
        tb = tb.clean()
    else:
        tb = cq.Solid.makeCone(16, 34, hn, cq.Vector(0, 0, zv0), cq.Vector(0, 0, -1))
        tb = tb.cut(cq.Solid.makeCone(13, 31, hn, cq.Vector(0, 0, zv0), cq.Vector(0, 0, -1)))
    giro = lambda sh: sh.rotate(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), math.degrees(phi)).rotate(  # noqa: E731
        cq.Vector(0, 0, 0), cq.Vector(1, 0, 0), math.degrees(psi)).rotate(
        cq.Vector(0, 0, 0), cq.Vector(0, 1, 0), math.degrees(th)).translate(cq.Vector(xn, yn, z_S))
    out["valvula_esferica"] = giro(ve)
    out["lanza" if lanza else "tobera_campana"] = giro(tb)
    a_t = _rot((0.0, 0.0, -1.0), th, psi)                          # eje de la tobera (afuera, adelante y abajo)
    pt = lambda d_: (xn + a_t[0] * d_, yn + a_t[1] * d_, z_S + a_t[2] * d_)   # noqa: E731
    xv_, yv_, zm_v = pt(12.0 + hv / 2)
    pal_c = tuple(pt(12.0 + hv / 2)[i] + _rot((-33.5, 70.0, 0.0), th, psi, phi)[i] for i in range(3))   # empuñadura
    xb_, yb_, zb_ = pt(L_t)
    MANGA_PUNTA[m.codigo] = dict(afuera=math.degrees(th), adelante=math.degrees(psi), palanca=math.degrees(phi),
                                 espiga=(xn, yn, z_S),
                                 boca=(xb_, yb_, zb_))
    z_lo, z_hi = z_fi + fa / 2, z_fs + fa / 2
    MANGA_VUELTAS[m.codigo] = n_v
    info["eje_tobera"] = (xb_, zb_ - r_boca * math.sin(math.acos(-a_t[2])), z_S)
    info["eje_tobera_3d"] = (pt(-10.0), pt(L_t + 10.0))
    info.update(dict(Rw=Rw, bw_w=bw_w, xw=xw, yw=yw, track=track, xm=xm, ym=ym, xs=xs, z_ganchos=(z_lo, z_hi),
                     tobera=pt(12.0 + hv + hn / 2)[::2], valv_esf=(xv_, zm_v), valv_esf_y=yv_, palanca_c=pal_c, pata=(pw, hp, tp, yp),
                     z_flejes=z_flejes))
    return out, info


def _sector(r_in, r_out, h, z0, ancho, xc, yc, ang_c=-90.0):
    """Lámina curva sobre el cuerpo: sector de anillo de `ancho` mm de arco centrado en ang_c (grados)."""
    ang = math.degrees(ancho / r_in)
    ext = cq.Solid.makeCylinder(r_out, h, cq.Vector(xc, yc, z0), cq.Vector(0, 0, 1), ang)
    inn = cq.Solid.makeCylinder(r_in, h, cq.Vector(xc, yc, z0), cq.Vector(0, 0, 1), ang)
    sec = ext.cut(inn)
    return sec.rotate(cq.Vector(xc, yc, 0), cq.Vector(xc, yc, 1), ang_c - ang / 2)


def marcado(m):
    """Dónde y cuándo se graba el marcado del recipiente (IRAM 3523 / 3550 5.1), según los procesos FLAMA.
    Devuelve (pieza, texto corto, texto de proceso en líneas)."""
    # proceso FLAMA de manuales, «numerado de cúpula»: fabricante, n° y año estampados en frío en la CÚPULA, en arco
    # alrededor del cuello (micropercusión), con el cuño DPS al lado; el mismo criterio en los carros (ver marca_cupula)
    if m.familia == "rodante":
        return ("cupula", "estampado en la cúpula, en arco junto al cuello (puesto 11, después de la PH y el secado)",
                ["Estampado en la CÚPULA, en arco alrededor del cuello, en el puesto 11 (marcado),",
                 "después de la PH (9) y el secado (10); centrado al costado derecho (libre de manija y manga);"])
    return ("cupula", "estampado en la cúpula, en arco junto al cuello (puesto de numerado de cúpula)",
            ["Estampado en la CÚPULA, en arco alrededor del cuello (micropercusión), después del",
             "embutido y antes de soldar el cuello; centrado al frente, sobre la etiqueta;"])


MARCA_H = 5.0               # letra del marcado estampado (IRAM 4503; proceso «numerado de cúpula»)
CUNO_DPS = (15.0, 7.0)      # cuño DPS junto al n° (Res. 349/07 anexo IV)
MARCA_ARCO_MAX = 270.0      # el arco no da la vuelta entera: el cuño queda separado del comienzo del texto


def marca_cupula(m):
    """Franja del marcado estampado en la cúpula, en arco alrededor del cuello: radios (desde el eje), texto, paso
    entre caracteres y ángulos en grados (0° = costado derecho, -90° = frente). La franja arranca 4 mm afuera del
    cuello (cordón cuello-cúpula + 2 mm libres) y tiene el alto del cuño DPS; si el arco pasara de 270° se aleja del
    cuello hasta que entre."""
    rod = m.familia == "rodante"
    txt = "FLAMA S.A.  N° 000001  " + (f"PE {m.spec['Presión de ensayo (MPa)']} MPa  " if rod else "") + "26"
    paso = 0.72 * MARCA_H
    largo = len(txt) * paso + 4.0 + CUNO_DPS[0]
    rc = max(m.geo["cuello"][0] / 2 + 4.0 + CUNO_DPS[1] / 2, largo / math.radians(MARCA_ARCO_MAX))
    a_txt = math.degrees(len(txt) * paso / rc)
    a_tot = math.degrees(largo / rc)
    centro = 0.0 if rod else -90.0
    a0 = centro - a_tot / 2                  # el texto avanza en sentido antihorario visto desde arriba
    return dict(r_in=rc - CUNO_DPS[1] / 2, r_out=rc + CUNO_DPS[1] / 2, rc=rc, texto=txt, paso=paso, a0=a0,
                a_tot=a_tot, a_dps0=a0 + a_txt + math.degrees(4.0 / rc), a_dps=math.degrees(CUNO_DPS[0] / rc),
                centro=centro)


def z_cupula_en(dr, r, rod=False):
    """Altura de la cara exterior de la cúpula a la distancia r del eje: elipse de semiejes R y hd − c0 centrada c0
    sobre la unión (c0 = pollera recta en los manuales, escalón del casquete en los carros; ver recipiente())."""
    lab, esc = dr["encastre"]
    c0 = esc if rod else lab
    u = min(1.0, r / dr["R"])
    return dr["z_union"] + c0 + (dr["hd"] - c0) * math.sqrt(1.0 - u * u)


# medidas de identificación (ver flama/rotulado.py para las fuentes)
ARCO_PLACA = 108.0          # IRAM 3534 2.2.4.3 d) / 3523 5.2.6.3 d): longitud máxima de las instrucciones
ARCO_ALA = 54.0             # alas laterales de datos y mantenimiento (relevamiento de mercado: etiqueta ≈ 216°)
OBLEA_PBA = 46.0            # Res. OPDS 522/07 anexos 1 y 2: oblea de fabricación Ø 46 mm
ESTAMPILLA_IRAM = (60.0, 40.0)   # estampilla IRAM extintor nuevo (Anexo R + relevada, proporción 3:2; a confirmar)
TARJETA_CABA = (140.0, 55.0)     # tarjeta AGC autoadhesiva relevada en un 10 kg (a confirmar con la AGC)
ETIQUETA_SERIE = (45.0, 25.0)    # etiqueta GS1 de n° de serie con QR (relevada en Melisam)
FAJA_GARANTIA = (30.0, 40.0)     # faja de garantía rayada (relevada en la línea Georgia)
GAP_ID = 4.0


MANGA_VUELTAS = {}               # código -> vueltas del rollo de la manga del carro
MANGA_CAPAS = {}                 # código -> (capas usadas, lugares, fila 0, fila 1)
FLEJE_MEDIO = {}                 # código -> (base por fuera, pata) del fleje del medio hacia adentro (100 kg) o None
FLEJE = {}                       # código -> (base por fuera, pata, largo de corte, cantidad) de los flejes de manga
MANGA_LARGO = {}                 # código -> largo de la manga del modelo (eje), mm
ALA_CARRO = {}                   # código -> arco de cada ala (carro donde la etiqueta no entra bajo las lengüetas)


def arco_ala(R, m=None):
    """Arco de cada ala: 54° en general; 72° en cuerpos chicos (Ø < 100), donde el mercado envuelve casi todo. En un
    carro cuya etiqueta no entra entre los triángulos del eje y las lengüetas de la manija, las alas se acortan hasta
    terminar antes de las lengüetas (ver extintor_rodante)."""
    if m is not None and m.codigo in ALA_CARRO:
        return ALA_CARRO[m.codigo]
    return ARCO_ALA if R >= 50 else 72.0


def ala_dim(R, m=None):
    return math.radians(arco_ala(R, m)) * R


def placa_dim(m, p):
    """(ancho del panel central, alto, z0, R, xc, yc) de la etiqueta sobre el cuerpo. Debajo de la etiqueta
    va la fila de la oblea PBA (con la estampilla IRAM al costado y, si entra en el perímetro, la tarjeta AGC
    al otro costado); si la tarjeta no entra, va en una segunda fila debajo."""
    cb = p["cuerpo"].BoundingBox()
    R = (cb.xmax - cb.xmin) / 2
    xc, yc = (cb.xmax + cb.xmin) / 2, (cb.ymax + cb.ymin) / 2
    hb = cb.zmax - cb.zmin
    ancho = math.radians(ARCO_PLACA) * R
    from .rotulado import disposicion
    alto = disposicion(m, ancho, ala_dim(R, m))["H"]   # alto que pide el contenido (IRAM 3534 + mercado)
    fila = OBLEA_PBA + 3 + (0 if lleva_tarjeta(m, p) != "debajo" else TARJETA_CABA[1] + GAP_ID)
    libre = hb - 20.0 - fila
    z0 = cb.zmin + 10.0 + fila + max(0.0, (libre - alto) / 2)
    if "soportes_eje" in p and m.familia == "rodante":
        # carro: la etiqueta queda por encima de los triángulos del eje y, si sus alas llegan a los costados, debajo de
        # las lengüetas de la manija (proceso de carros, puesto 8); la oblea, debajo de la etiqueta, entre los dos
        # triángulos, y la estampilla y la tarjeta, por fuera de ellos
        lo = max(cb.zmin + 10.0 + fila, p["soportes_eje"].BoundingBox().zmax + 10.0)
        hi = cb.zmax - 10.0 - (0.0 if m.codigo in ALA_CARRO else CARRO["lengueta_bajo_cupula"])
        z0 = max(lo, min(lo + max(0.0, (hi - lo - alto) / 2), hi - alto))
    return ancho, alto, z0, R, xc, yc


def tarjeta_al_costado(R):
    ocupa = OBLEA_PBA + ESTAMPILLA_IRAM[0] + TARJETA_CABA[0] + 4 * GAP_ID
    return ocupa <= 2 * math.pi * R * 0.92


def lleva_tarjeta(m, p):
    """'costado', 'debajo' o '' (no entra en el cuerpo: matafuego de 1 kg de uso vehicular, a confirmar con la AGC)."""
    cb = p["cuerpo"].BoundingBox()
    R = (cb.xmax - cb.xmin) / 2
    if tarjeta_al_costado(R):
        return "costado"
    from .rotulado import disposicion
    alto = disposicion(m, math.radians(ARCO_PLACA) * R, ala_dim(R, m))["H"]
    return "debajo" if alto + OBLEA_PBA + 3 + TARJETA_CABA[1] + GAP_ID + 20 <= cb.zmax - cb.zmin else ""


FAJA_MEDIDA = {}                 # código -> (ancho, largo desarrollado) de la faja dibujada
MANIJA_LARGO = {}                # código -> largo desarrollado del caño de la manija del carro
AVISOS_CARRO = []                # avisos del armado de los carros (lo que no entra en la hoja de especificaciones)
MANGA_PUNTA = {}                 # código -> inclinación de la tobera, espiga y boca (carros)
CARRO_MOD = {}                   # código -> medidas del carro que salen de la hoja de especificaciones del modelo


def _faja(p, ex, ey):
    """Faja de garantía válvula-cuello (ver identificacion): perfil en el plano radial (u, z) a un ángulo a, extruido
    al ancho de la faja; se toma el ángulo en que la tira queda libre y más pegada (menor salto entre válvula y cuello)."""
    fw, fh = FAJA_GARANTIA
    eb = p["espiga"].BoundingBox()
    abajo = p.get("cuello") or p["cuerpo"]
    vb = p["cuerpo_valvula"].BoundingBox()
    zc = eb.zmax                              # cara de apoyo de la válvula (tope del cuello)
    z_vb = vb.zmin                            # base del cuerpo de la válvula (arriba de la tuerca)
    piso = max([p[k].BoundingBox().zmax for k in ("cupula",) if k in p] + [zc - 40.0])
    libres = ("espiga", "tuerca", "junta_cuello", "cuello", "cupula", "cuerpo", "cuerpo_valvula", "etiqueta",
              "oblea_pba", "sello_iram", "tarjeta_caba", "etiqueta_serie", "soldaduras", "cano_pesca")
    cerca = [k for k, so in p.items() if k not in libres and so.BoundingBox().zmax > zc - 40 and
             so.BoundingBox().zmin < z_vb + 40 and abs(so.BoundingBox().center.x - ex) < 150 and
             abs(so.BoundingBox().center.y - ey) < 150]

    def alcance(sol, a, w, z0, z1):
        """lo que sobresale `sol` en la dirección a, dentro de la franja |v| <= w/2 y z0..z1 (None si nada)."""
        caja = _box(400, w, z1 - z0, ex + 200, ey, z0).rotate(cq.Vector(ex, ey, 0), cq.Vector(ex, ey, 1), a)
        q = sol.intersect(caja)
        if q.Volume() < 1e-6:
            return None
        return q.rotate(cq.Vector(ex, ey, 0), cq.Vector(ex, ey, 1), -a).BoundingBox().xmax - ex

    mejor = None
    w0 = min(fw, (abajo.BoundingBox().xmax - abajo.BoundingBox().xmin) * 0.6)
    for a, w in [(a_, w_) for w_ in (w0, 0.6 * w0) for a_ in range(-90, 270, 15)]:   # primero el frente, más ancha
        if mejor is not None and w < w0 and mejor[2] >= w0:
            break
        h_max = min(fh / 2, zc - piso - 0.5)
        for h_lo in [h_max - 3.0 * k for k in range(8) if h_max - 3.0 * k >= 6.0] or [h_max]:
            r_c = alcance(abajo, a, w, zc - h_lo, zc - 0.2)
            r_v = alcance(p["cuerpo_valvula"], a, w, z_vb + 0.2, z_vb + fh / 2)
            if r_c is None or r_v is None:
                break
            r_t = alcance(p["tuerca"], a, w, zc + 0.2, z_vb - 0.2) if "tuerca" in p else None
            h_up = 8.0                            # agarre sobre el cuerpo de la válvula, debajo de manijas y manómetro
            r_v = max(r_v, alcance(p["cuerpo_valvula"], a, w, z_vb + 0.2, z_vb + h_up) or r_v)
            # la cinta tensa sigue la envolvente convexa exterior de válvula, tuerca y cuello en el plano (u, z)
            pts = [(r_v, z_vb + h_up), (r_v, z_vb), (r_c, zc), (r_c, zc - h_lo)]
            if r_t is not None:
                pts += [(r_t, z_vb), (r_t, zc)]
            hull = sg.MultiPoint(pts + [(0.0, z_vb + h_up), (0.0, zc - h_lo)]).convex_hull
            cad = [q for q in list(hull.exterior.coords)[:-1] if q[0] > 0.5]
            i_top = max(range(len(cad)), key=lambda i: (cad[i][1], cad[i][0]))
            cad = cad[i_top:] + cad[:i_top]
            if len(cad) > 2 and cad[1][1] < cad[-1][1]:   # recorrer de arriba hacia abajo por el lado exterior
                cad = [cad[0]] + cad[1:][::-1]
            e_ = 0.2
            # espesor hacia afuera (a la izquierda de la cinta, que se recorre hacia abajo)
            poly = sg.LineString([(u + 0.03, z) for u, z in cad]).buffer(e_, single_sided=True, cap_style=2,
                                                                          join_style=2)
            pl = cq.Plane(origin=(ex, ey, 0), xDir=(1, 0, 0), normal=(0, -1, 0))
            tira = cq.Workplane(pl).polyline(list(poly.exterior.coords)[:-1]).close().extrude(w / 2, both=True).val()
            tira = tira.rotate(cq.Vector(ex, ey, 0), cq.Vector(ex, ey, 1), a)
            choca = [k for k in cerca + ["cuerpo_valvula", "tuerca", "soldaduras"]
                     if k in p and tira.intersect(p[k]).Volume() > 1e-3]
            if choca == ["soldaduras"]:
                continue                      # pisa el cordón de la cupla: se acorta la parte de abajo
            if choca:
                break
            salto = abs(r_v - r_c)
            if mejor is None or salto < mejor[0] - 1.0:
                mejor = (salto, tira, w, sg.LineString(cad).length)
            break
    if mejor is None:                         # no debería pasar: tira chica pegada al cuello, adelante
        r0 = (abajo.BoundingBox().xmax - abajo.BoundingBox().xmin) / 2
        return _sector(r0 + 0.05, r0 + 0.25, 12.0, zc - 12.0, min(fw, r0), ex, ey, -90.0), (min(fw, r0), 12.0)
    return mejor[1], (mejor[2], mejor[3])


def identificacion(m, p):
    """Identificación del extintor nuevo que el plano debe mostrar:
    etiqueta (IRAM 3534) de frente, sobre el eje del manómetro: panel central de 108° y alas de 54° (72° si Ø < 100); oblea de
    fabricación de la Provincia de Buenos Aires Ø 46 inmediatamente debajo (Res. OPDS 522/07 anexo 6);
    estampilla IRAM de conformidad al costado; tarjeta AGC (CABA) al otro costado o debajo; etiqueta de serie
    GS1 a 180°; junta tórica de asiento de la válvula; precinto de la traba y faja de garantía válvula-cuello."""
    ancho, alto, z0, R, xc, yc = placa_dim(m, p)
    p["etiqueta"] = _sector(R, R + 0.3, alto, z0, ancho + 2 * ala_dim(R, m), xc, yc)
    zo = z0 - 3.0 - OBLEA_PBA
    p["oblea_pba"] = _sector(R, R + 0.3, OBLEA_PBA, zo, OBLEA_PBA, xc, yc)
    ew, eh = ESTAMPILLA_IRAM
    base = OBLEA_PBA / 2                  # estampilla y tarjeta a los costados de la oblea
    if "soportes_eje" in p:               # carro: por fuera de los triángulos del eje (la oblea queda entre los dos)
        xt_ = p["soportes_eje"].BoundingBox().xmax
        base = max(base, R * math.asin(min(1.0, xt_ / R)) + 1.0)
    ang_e = -90.0 + math.degrees((base + GAP_ID + ew / 2) / R)
    p["sello_iram"] = _sector(R, R + 0.3, eh, zo + (OBLEA_PBA - eh) / 2, ew, xc, yc, ang_e)
    tw, th = TARJETA_CABA
    lt = lleva_tarjeta(m, p)
    if lt == "costado":
        ang_t = -90.0 - math.degrees((base + GAP_ID + tw / 2) / R)
        p["tarjeta_caba"] = _sector(R, R + 0.3, th, zo + OBLEA_PBA - th, tw, xc, yc, ang_t)   # arriba a ras de la oblea
    elif lt == "debajo":
        p["tarjeta_caba"] = _sector(R, R + 0.3, th, zo - GAP_ID - th, tw, xc, yc)
    gw, gh = ETIQUETA_SERIE
    p["etiqueta_serie"] = _sector(R, R + 0.3, gh, z0 + alto / 2 - gh / 2, gw, xc, yc, 90.0)
    eb = p["espiga"].BoundingBox()
    ro = (eb.xmax - eb.xmin) / 2 + 1.5
    ex, ey = (eb.xmax + eb.xmin) / 2, (eb.ymax + eb.ymin) / 2
    p["junta_cuello"] = _cyl(ro, 3.0, (ex, ey, eb.zmax - 3.0), (0, 0, 1)).cut(
        _cyl(ro - 3.0, 3.0, (ex, ey, eb.zmax - 3.0), (0, 0, 1)))
    # faja de garantía: autoadhesivo destructible que puentea la unión roscada: la mitad de arriba pegada al costado
    # del cuerpo de la válvula y la de abajo al cuello (o al cuello del cilindro de CO2), pasando por encima de la
    # tuerca; si se desenrosca la válvula se rompe. Es una tira plana tangente a las dos superficies (no se despega de
    # ellas) y va del lado donde no la tapan manómetro, palancas, tobera, salida ni pasador.
    p["faja_garantia"], FAJA_MEDIDA[m.codigo] = _faja(p, ex, ey)
    pb = p["pasador"].BoundingBox()
    x_p = pb.xmax
    pre = _cyl(2.5, 10.0, (x_p, (pb.ymin + pb.ymax) / 2, (pb.zmin + pb.zmax) / 2), (1, 0, 0))
    for _ in range(25):                       # el precinto cuelga del ojal del pasador, fuera de las palancas
        if not any(k in p and pre.intersect(p[k]).Volume() > 1e-6 for k in ("manija_superior", "manija_inferior",
                                                                             "cuerpo_valvula")):
            break
        pre = pre.translate(cq.Vector(0, 0, -2.0))
    p["precinto"] = pre
    return p


def construir(m):
    """Construye el conjunto y corrige (2 iteraciones) para que la caja
    envolvente coincida con altura/ancho/profundidad del catálogo."""
    if m.familia == "rodante":
        # rodantes: tren de rodaje con criterio IRAM 3550 (trocha, banda, eje detrás del cuerpo); alto = catálogo
        # (agarre de la manija); ancho y profundidad resultan del diseño y se comparan con el catálogo en la hoja 3
        p, i = extintor_rodante(m)
        return identificacion(m, p), i
    # manuales: piezas con sus medidas reales (planos Fadesa); la envolvente resulta de ellas y se compara con
    # el catálogo en la hoja 3 (no se estira la válvula para alcanzar la altura del catálogo)
    p, i = extintor_manual(m)
    return identificacion(m, p), i


def compuesto(piezas):
    return cq.Compound.makeCompound(list(piezas.values()))


def bbox(piezas):
    # caja exacta sobre la geometría B-rep (no sobre la triangulación)
    from OCP.Bnd import Bnd_Box
    from OCP.BRepBndLib import BRepBndLib
    b = Bnd_Box()
    BRepBndLib.AddOptimal_s(compuesto(piezas).wrapped, b, False, False)
    return cq.occ_impl.geom.BoundBox(b)
