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
        # cuerpo con bordón arriba (y abajo en el 1 kg, caño con los dos extremos reducidos)
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
    if costura and tipo not in ("co2", "cupula"):
        # costura longitudinal (el 1 kg es caño comprado: sin costura de planta)
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


# Tren rodante soldado al recipiente (proceso FLAMA de carros, puesto 8): eje con sus soportes atrás y abajo, manija de
# caño atrás y arriba (sube por encima de la cúpula); adelante, los dos ganchos portamanguera (uno arriba y otro abajo)
# con la manga enrollada entre los dos, la tobera colgada al lado del rollo y la tercera pata en el fondo: el carro
# apoya en tres puntos. El proceso escrito pone los ganchos «en el costado derecho»; se corrigió: accesorios y manga van
# en la parte delantera, como en la imagen de la tercera pata frontal del mismo proceso y en los carros relevados
# (Georgia: manga al frente, etiqueta hacia la manija, del lado del operador). Ejes del modelo: -Y = atrás (manija,
# eje, etiqueta y manómetro: es la vista anterior del plano); +Y = adelante (ganchos, manga, tobera y pata).
# El eje pasa por un portaeje (caño) soldado a dos chapas triangulares que salen de la pared trasera; la manija se
# sujeta con dos orejas por pata y se dobla 30° hacia atrás por encima de la cúpula (plano Fadesa y carro relevado).
# Todo se suelda antes de la prueba hidráulica (IRAM 3550 6.1.1). Las piezas de chapa salen de orillas del corte del
# cuerpo; se compran el caño de la manija, el caño del portaeje, la barra del eje y las arandelas de tope. El puesto 8.1 fija sólo la
# tercera pata (80 × 60 en 25/50 kg y 100 × 80 en 70/100 kg, de la orilla de 3,2 mm de la hoja de 25 kg, puesto 2);
# las demás medidas son de diseño FLAMA, dimensionadas para que el kit pese 4,2-4,9 kg como dice el proceso.
CARRO = dict(
    banda={300: 60.0, 350: 60.0, 400: 100.0},  # ancho de rueda: IRAM 3550 tabla III ≥ 50 (Fadesa usa 49: no cumple);
                                 # Ruedar Ø300 / Ø350 × 60 y Escanort Ø400 × 100 (proveedores relevados)
    trocha_min=400.0,            # IRAM 3550 tabla III: trocha (entre centros de rueda) ≥ 400
    luz_rueda=20.0,              # luz entre la cara interna de la rueda y el cuerpo
    luz_eje=15.0,                # luz entre el eje y la pared trasera del cuerpo
    soporte=(80.0, 0.7),         # chapas triangulares del portaeje: alto sobre el eje del caño y posición ± 0,7·R
    eje=25.0,                    # barra SAE 1045 Ø25
    portaeje=(33.7, 3.25),       # caño SAE 1010 Ø33,7 × 3,25 (1"): Ø int. 27,2 para el eje Ø25
    arandela=(40.0, 13.0, 4.0),  # arandela de tope Ø40 × Ø26 × 4
    manija=(25.4, 1.6, 15.0, 40.0, 30.0),  # caño Ø25,4 × 1,6; luz de la oreja 15; radio de curvado 40; doblez 30°
    gancho=(40.0, 10.0, 30.0),   # ancho del gancho, holgura sobre 2 Ø de manga y alto del labio
    pata=((80.0, 60.0), (100.0, 80.0)),   # proceso FLAMA puesto 2: 80 × 60 (25 y 50 kg), 100 × 80 (70 y 100 kg)
    pata_e=3.2,                  # orilla de 3,2 mm de la hoja de 25 kg (todas las patas)
)


def extintor_rodante(m, cD=0.0):
    g = dict(m.geo)
    H, W, D = m.H, m.W, m.D
    Dw = float(m.spec["Diámetro de rueda (mm)"])           # catálogo (IRAM 3550 tabla III: Ø ≥ 300)
    Rw = Dw / 2
    bw_w = CARRO["banda"][int(Dw)]
    R = g["R"]
    t = g["t"]
    z0 = 45.0 + (g["hd"])  # el cabezal inferior queda a 45 mm del piso
    piezas, dr = recipiente(dict(g), z0 - g["hd"], costura=True)
    out = dict(piezas)
    info = dict(recipiente=dr)
    lleno = _lleno(dr)
    d_hose = 25.0
    # tercera pata (adelante, +Y): planchuela vertical apoyada de canto en el piso y soldada al fondo; se ubica donde
    # sus dos esquinas superiores todavía tocan el casquete (el recorte contra el recipiente la ajusta a la curva)
    pw, hp = CARRO["pata"][0 if R < 170 else 1]
    tp = CARRO["pata_e"]
    yp = 0.0
    for i in range(1, int(R)):
        if not lleno.isInside(cq.Vector(pw / 2, float(i), hp - 3.0)):
            break
        yp = float(i)
    out["tercera_pata"] = _box(pw, tp, hp, 0, yp, 0).cut(lleno).cut(out["fondo"]).clean()
    # ruedas al costado del cuerpo (trocha IRAM ≥ 400 y luz con el cuerpo) y eje recto detrás de la pared trasera (-Y),
    # a la altura del centro de rueda: el carro apoya en las dos ruedas y la tercera pata (IRAM 3550 3.12.3)
    da, dia, ea = CARRO["arandela"]
    track = max(CARRO["trocha_min"], math.ceil((2 * R + bw_w + 2 * CARRO["luz_rueda"]) / 10.0) * 10.0)
    xw = track / 2
    yw = -(R + CARRO["eje"] / 2 + CARRO["luz_eje"])
    # ruedas
    for sgn, suf in ((1, "der"), (-1, "izq")):
        c = cq.Vector(sgn * (xw - bw_w / 2), yw, Rw)              # cara interna; la rueda queda centrada en ±xw
        # neumático macizo (anillo de caucho) + llanta de chapa (disco con cubo)
        tire = _cyl(Rw, bw_w, (c.x, c.y, c.z), (sgn, 0, 0))
        tire = tire.cut(_cyl(Rw * 0.72, bw_w, (c.x, c.y, c.z), (sgn, 0, 0)))
        # llanta de chapa estampada: aro e = 2, disco e = 2,5
        llanta = _tube(Rw * 0.72, Rw * 0.72 - 2, bw_w - 6, (c.x + sgn * 3, c.y, c.z), (sgn, 0, 0))
        llanta = llanta.fuse(_cyl(Rw * 0.72 - 2, 2.5, (c.x + sgn * (bw_w / 2 - 1.25), c.y, c.z), (sgn, 0, 0)))
        llanta = llanta.fuse(_tube(30, 13, bw_w + 10, (c.x - sgn * 10, c.y, c.z), (sgn, 0, 0)))
        llanta = llanta.cut(_cyl(13, bw_w + 30, (c.x - sgn * 15, c.y, c.z), (sgn, 0, 0)))   # buje Ø26 para el eje
        out["rueda_" + suf] = tire
        out["llanta_" + suf] = llanta.clean()
    # eje, portaeje y arandelas de tope: el eje (barra Ø25) pasa por el portaeje (caño soldado a dos chapas
    # triangulares que salen de la pared trasera); entre cada punta del portaeje y el cubo de la rueda va una arandela,
    # y otra afuera de la rueda (como en el carro relevado: portaeje cruzado atrás con sus chapas triangulares)
    re = CARRO["eje"] / 2
    x_in, x_out = xw - bw_w / 2 - 10, xw + bw_w / 2
    out["eje_ruedas"] = _cyl(re, 2 * (x_out + ea + 6), (-(x_out + ea + 6), yw, Rw), (1, 0, 0))
    dpe, epe = CARRO["portaeje"]
    rpe = dpe / 2
    lpe = x_in - ea                           # medio largo del portaeje: llega a la arandela interior
    out["portaeje"] = _tube(rpe, rpe - epe, 2 * lpe, (-lpe, yw, Rw), (1, 0, 0))
    ar = None
    for sgn in (1, -1):
        for xx in (x_in - ea, x_out):
            a_ = _tube(da / 2, dia, ea, (sgn * xx if sgn > 0 else -xx - ea, yw, Rw), (1, 0, 0))
            ar = a_ if ar is None else ar.fuse(a_)
    out["arandelas_tope"] = ar.clean()
    # chapas triangulares del portaeje: en los planos x = ±0,7·R, con el cateto vertical soldado a la pared trasera,
    # el cateto horizontal a la altura de la base del portaeje y la punta redondeada abrazando el caño
    h_tri, xs_k = CARRO["soporte"]
    xs = xs_k * R
    y_in = -math.sqrt(R * R - xs * xs) + 15.0  # 15 mm dentro de la pared: el recorte la ajusta a la curva
    m_pe = rpe + 6.0
    tri = sg.Polygon([(y_in, Rw + h_tri), (y_in, Rw - m_pe), (yw - m_pe, Rw - m_pe)]).union(
        sg.Point(yw, Rw).buffer(m_pe, 32))
    pts = list(tri.exterior.coords)[:-1]
    sop = None
    for sgn in (1, -1):
        pl = cq.Workplane("YZ").polyline(pts).close().extrude(t).val().translate(cq.Vector(sgn * xs - t / 2, 0, 0))
        sop = pl if sop is None else sop.fuse(pl)
    sop = sop.cut(lleno).cut(out["fondo"]).cut(out["cuerpo"]).cut(_cyl(rpe + 0.3, 2 * R, (-R, yw, Rw), (1, 0, 0)))
    out["soportes_eje"] = sop.clean()
    # manija: caño en U con las patas a los costados del cuerpo (por encima de la etiqueta), sujetas por dos orejas
    # cada una; sube vertical hasta pasar la cúpula y ahí se dobla 30° hacia atrás hasta el agarre (plano Fadesa
    # «Rodante 50 kg 800 mm»), que queda a la altura del catálogo
    dm, em, luz, rb, ang = CARRO["manija"]
    rt = dm / 2
    xm = R + luz + rt                         # eje de las patas: luz de la oreja entre el cuerpo y el caño
    ym = 0.0
    zg = H - rt
    _, alto_et, z_et, _, _, _ = placa_dim(m, out)
    z_low = max(dr["zb"] + 0.45 * (dr["z_union"] - dr["zb"]), z_et + alto_et + 20.0)
    z_bend = dr["z_union"] + dr["hd"] + 20.0  # el doblez queda por encima de la cúpula
    yg = -(zg - z_bend) * math.tan(math.radians(ang))
    out["manija_carro"] = _sweep_circle([(-xm, ym, z_low), (-xm, ym, z_bend, rb), (-xm, yg, zg, 1.5 * rb),
                                         (xm, yg, zg, 1.5 * rb), (xm, ym, z_bend, rb), (xm, ym, z_low)], rt)
    # orejas: chapitas horizontales soldadas al cuerpo, con el agujero por donde pasa y se suelda la pata
    z_or = [z_low + 20.0, max(z_low + 60.0, dr["z_union"] - 20.0)]
    ore = None
    for sgn in (1, -1):
        g_ = sg.box(R - 12.0, ym - 20.0, xm, ym + 20.0).union(sg.Point(xm, ym).buffer(rt + 7.0, 32))
        if sgn < 0:
            g_ = sg.Polygon([(-x, y) for x, y in g_.exterior.coords])
        for zz in z_or:
            o_ = cq.Workplane("XY").polyline(list(g_.exterior.coords)[:-1]).close().extrude(t).val()
            o_ = o_.translate(cq.Vector(0, 0, zz - t / 2))
            ore = o_ if ore is None else ore.fuse(o_)
    for sgn in (1, -1):
        ore = ore.cut(_cyl(rt + 0.3, 2 * H, (sgn * xm, ym, -H / 2)))
    out["orejas_manija"] = ore.cut(lleno).clean()
    info.update(dict(portaeje=(dpe, epe, 2 * lpe), z_orejas=z_or, z_doblez=z_bend, y_agarre=yg, angulo_manija=ang,
                     soporte_tri=(h_tri, m_pe, y_in, xs)))
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
    # ganchos portamanguera adelante (+Y), sobre el eje del cuerpo, y manga enrollada entre los dos en un plano
    # paralelo al frente; el ancho del rollo deja llegar la manga desde la salida de la válvula con curvas suaves
    gw, gh, gl = CARRO["gancho"]
    vg = 2 * d_hose + gh                      # vuelo del gancho fuera del cuerpo
    yl = R + vg / 2 + 2                       # plano de la manga enrollada
    L_c = dr["z_union"] - dr["zb"]
    wl = max(0.45 * R, 16.0 - xsal + 45.0)
    ap = math.sqrt(wl * wl - (gw / 2) ** 2) - 1.0  # la manga apoya en los bordes del brazo de 40 de ancho
    z_lo = max(dr["zb"] + 0.12 * L_c, hp + 30.0 + wl + d_hose - ap + t / 2)   # el rollo pasa por encima de la pata
    z_hi = dr["zb"] + 0.90 * L_c
    gan = None
    for zz, sgl in ((z_hi, 1), (z_lo, -1)):
        brazo = _box(gw, vg + 20, t, 0, R + vg / 2 - 10, zz - t / 2)
        labio = _box(gw, t, gl, 0, R + vg - t / 2, zz - t / 2 if sgl > 0 else zz + t / 2 - gl)
        gan = brazo.fuse(labio) if gan is None else gan.fuse(brazo).fuse(labio)
    out["ganchos_manguera"] = gan.cut(lleno).clean()
    zt_l = z_hi + t / 2 + d_hose / 2 - ap     # centro del arco superior: la manga apoya sobre el brazo de arriba
    zb_l = z_lo - t / 2 - d_hose / 2 + ap     # centro del arco inferior: la manga pasa por debajo del brazo de abajo
    e1 = cq.Edge.makeLine(cq.Vector(-wl, yl, zb_l), cq.Vector(-wl, yl, zt_l))
    a1 = cq.Edge.makeThreePointArc(cq.Vector(-wl, yl, zt_l), cq.Vector(0, yl, zt_l + wl), cq.Vector(wl, yl, zt_l))
    e2 = cq.Edge.makeLine(cq.Vector(wl, yl, zt_l), cq.Vector(wl, yl, zb_l))
    a2 = cq.Edge.makeThreePointArc(cq.Vector(wl, yl, zb_l), cq.Vector(0, yl, zb_l - wl), cq.Vector(-wl, yl, zb_l))
    wire = cq.Wire.assembleEdges([e1, a1, e2, a2])
    out["manguera_enrollada"] = cq.Solid.sweep(
        cq.Wire.makeCircle(d_hose / 2, cq.Vector(-wl, yl, zb_l), cq.Vector(0, 0, 1)), [], wire,
        transitionMode="round")
    # tramo válvula -> rollo: sale hacia el costado, pasa por encima de la cúpula hacia adelante y baja pegado al lado
    # izquierdo del rollo (es la vuelta exterior) hasta el arco de abajo
    xb_ = -(wl + d_hose)
    out["manguera"] = _sweep_circle([(xsal - 16, 0, zsal), (xb_, 0, zsal, 35), (xb_, yl, zsal, 60), (xb_, yl, zb_l)],
                                    d_hose / 2)
    # punta de la manga: válvula esférica + tobera colgadas al costado del rollo, adelante
    xn = wl + d_hose / 2 + 38                 # tobera (boca Ø68) colgada al lado del rollo, sin tocarlo
    yn = yl
    zn_top = (zt_l + zb_l) / 2 + 60
    ve = _box(40, 40, 60, xn, yn, zn_top)
    ve = ve.fuse(_box(14, 90, 12, xn, yn + 45, zn_top + 24))         # palanca hacia adelante, sin sumar ancho
    out["valvula_esferica"] = ve.clean()
    if m.descarga == "lanza_espuma_rodante":
        # lanza espumígena de rodante: tubo Ø40 con 4 tomas de aire y boca expandida
        hn = 380.0
        tubo = _tube(20, 17.5, hn - 40, (xn, yn, zn_top - hn + 40))
        boca = cq.Solid.makeCone(20, 28, 40, cq.Vector(xn, yn, zn_top - hn + 40), cq.Vector(0, 0, -1))
        boca = boca.cut(cq.Solid.makeCone(17.5, 25.5, 40, cq.Vector(xn, yn, zn_top - hn + 40), cq.Vector(0, 0, -1)))
        lz = tubo.fuse(boca)
        for ang in (0, 90, 180, 270):
            dx, dy = math.cos(math.radians(ang)), math.sin(math.radians(ang))
            lz = lz.cut(_cyl(5, 12, (xn + dx * 14, yn + dy * 14, zn_top - 40), (dx, dy, 0)))
        out["lanza"] = lz.clean()
    else:
        hn = 200.0
        tb = cq.Solid.makeCone(16, 34, hn, cq.Vector(xn, yn, zn_top), cq.Vector(0, 0, -1))
        tb = tb.cut(cq.Solid.makeCone(13, 31, hn, cq.Vector(xn, yn, zn_top), cq.Vector(0, 0, -1)))
        out["tobera_campana"] = tb
    info["eje_tobera"] = (xn, zn_top - hn, zn_top + 60)
    info.update(dict(Rw=Rw, bw_w=bw_w, xw=xw, yw=yw, track=track, xm=xm, ym=ym, xs=xs, z_ganchos=(z_lo, z_hi),
                     tobera=(xn, zn_top - hn / 2), valv_esf=(xn, zn_top + 30), pata=(pw, hp, tp, yp)))
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
    # criterio FLAMA: el marcado va siempre en el cuerpo (también en el 1 kg y en los carros), nunca en la cúpula
    if m.capacidad == "1 kg":
        return ("cuerpo", "grabado en el cuerpo (puesto de numerado)",
                ["Grabado en el CUERPO (caño cortado a láser) en el puesto de numerado, antes",
                 "del encastre y el bordoneado; franja superior, opuesta a la etiqueta;"])
    if m.familia == "rodante":
        return ("cuerpo", "grabado en el cuerpo (puesto 11 de marcado, después de la PH y el secado)",
                ["Grabado en el CUERPO en el puesto 11 (marcado), después de la PH (9) y el",
                 "secado (10); franja superior, costado derecho (libre de manija y manga);"])
    return ("cuerpo", "grabado en el cuerpo (puesto de numerado)",
            ["Grabado en el CUERPO sobre el desarrollo plano (guillotina → numerado →",
             "cilindrado), número hacia afuera; franja superior, opuesta a la etiqueta;"])


# medidas de identificación (ver flama/rotulado.py para las fuentes)
ARCO_PLACA = 108.0          # IRAM 3534 2.2.4.3 d) / 3523 5.2.6.3 d): longitud máxima de las instrucciones
ARCO_ALA = 54.0             # alas laterales de datos y mantenimiento (relevamiento de mercado: etiqueta ≈ 216°)
OBLEA_PBA = 46.0            # Res. OPDS 522/07 anexos 1 y 2: oblea de fabricación Ø 46 mm
ESTAMPILLA_IRAM = (60.0, 40.0)   # estampilla IRAM extintor nuevo (Anexo R + relevada, proporción 3:2; a confirmar)
TARJETA_CABA = (140.0, 55.0)     # tarjeta AGC autoadhesiva relevada en un 10 kg (a confirmar con la AGC)
ETIQUETA_SERIE = (45.0, 25.0)    # etiqueta GS1 de n° de serie con QR (relevada en Melisam)
FAJA_GARANTIA = (30.0, 40.0)     # faja de garantía rayada (relevada en la línea Georgia)
GAP_ID = 4.0


def arco_ala(R):
    """Arco de cada ala: 54° en general; 72° en cuerpos chicos (Ø < 100), donde el mercado envuelve casi todo."""
    return ARCO_ALA if R >= 50 else 72.0


def ala_dim(R):
    return math.radians(arco_ala(R)) * R


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
    alto = disposicion(m, ancho, ala_dim(R))["H"]      # alto que pide el contenido (IRAM 3534 + mercado)
    fila = OBLEA_PBA + 3 + (0 if lleva_tarjeta(m, p) != "debajo" else TARJETA_CABA[1] + GAP_ID)
    libre = hb - 20.0 - fila
    z0 = cb.zmin + 10.0 + fila + max(0.0, (libre - alto) / 2)
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
    alto = disposicion(m, math.radians(ARCO_PLACA) * R, ala_dim(R))["H"]
    return "debajo" if alto + OBLEA_PBA + 3 + TARJETA_CABA[1] + GAP_ID + 20 <= cb.zmax - cb.zmin else ""


def identificacion(m, p):
    """Identificación del extintor nuevo que el plano debe mostrar:
    etiqueta (IRAM 3534) de frente, sobre el eje del manómetro: panel central de 108° y alas de 54° (72° si Ø < 100); oblea de
    fabricación de la Provincia de Buenos Aires Ø 46 inmediatamente debajo (Res. OPDS 522/07 anexo 6);
    estampilla IRAM de conformidad al costado; tarjeta AGC (CABA) al otro costado o debajo; etiqueta de serie
    GS1 a 180°; junta tórica de asiento de la válvula; precinto de la traba y faja de garantía válvula-cuello."""
    ancho, alto, z0, R, xc, yc = placa_dim(m, p)
    p["etiqueta"] = _sector(R, R + 0.3, alto, z0, ancho + 2 * ala_dim(R), xc, yc)
    zo = z0 - 3.0 - OBLEA_PBA
    p["oblea_pba"] = _sector(R, R + 0.3, OBLEA_PBA, zo, OBLEA_PBA, xc, yc)
    ew, eh = ESTAMPILLA_IRAM
    ang_e = -90.0 + math.degrees((OBLEA_PBA / 2 + GAP_ID + ew / 2) / R)
    p["sello_iram"] = _sector(R, R + 0.3, eh, zo + (OBLEA_PBA - eh) / 2, ew, xc, yc, ang_e)
    tw, th = TARJETA_CABA
    lt = lleva_tarjeta(m, p)
    if lt == "costado":
        ang_t = -90.0 - math.degrees((OBLEA_PBA / 2 + GAP_ID + tw / 2) / R)
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
    # faja de garantía: tira vertical que pasa de la cupla a la válvula; se ubica del lado donde queda más pegada sin
    # pisar manómetro, palancas ni pasador (radio = lo que sobresale cada pieza en esa dirección + 0,4)
    fw, fh = FAJA_GARANTIA
    z_f = eb.zmax - fh * 0.6
    zona = _box(1000, 1000, fh, ex, ey, z_f)
    recip = ("cuerpo", "cupula", "fondo", "soldaduras", "cano_pesca", "etiqueta", "oblea_pba", "sello_iram",
             "tarjeta_caba", "etiqueta_serie")
    secs = []
    for k, sol in p.items():
        if k in recip:
            continue
        bb_ = sol.BoundingBox()
        if bb_.zmax < z_f or bb_.zmin > z_f + fh or bb_.xmin > ex + 80 or bb_.xmax < ex - 80 or \
                bb_.ymin > ey + 80 or bb_.ymax < ey - 80:
            continue
        s_ = sol.intersect(zona)
        if s_.Volume() > 1e-6:
            secs.append(s_)
    mejor = None
    for a in (-90.0, -45.0, -135.0, 0.0, 180.0, 45.0, 135.0, 90.0):
        rf = ro + 0.5
        for _ in range(3):                    # la ventana angular depende del radio: se itera
            med = math.degrees(min(fw, math.pi * rf) / 2 / rf) + 3
            rf_n = ro + 0.5
            for s_ in secs:
                for fi in range(int(-med), int(med) + 1, 4):
                    rf_n = max(rf_n, s_.rotate(cq.Vector(ex, ey, 0), cq.Vector(ex, ey, 1), -(a + fi))
                               .BoundingBox().xmax - ex + 0.4)
            rf = rf_n
        if mejor is None or rf < mejor[0] - 0.5:
            mejor = (rf, a)
    rf, a = mejor
    faja = _sector(rf, rf + 0.2, fh, z_f, min(fw, math.pi * rf), ex, ey, a)
    for k in ("cupula", "cuerpo"):            # la tira no se apoya sobre el casquete: se sube hasta despegarla
        n_ = 0
        while k in p and n_ < 30 and faja.intersect(p[k]).Volume() > 1e-6:
            faja = faja.translate(cq.Vector(0, 0, 1.0))
            n_ += 1
    p["faja_garantia"] = faja
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
