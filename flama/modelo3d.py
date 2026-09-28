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
def recipiente(g, z0=0.0, costura=True):
    """Recipiente soldado. Devuelve (dict piezas, datos geométricos)."""
    R, hc, hd, t, td, tf = g["R"], g["hc"], g["hd"], g["t"], g["td"], g["tf"]
    dn, hn, rosca, dh = g["cuello"]
    rh = dh / 2
    piezas = {}
    tipo = g["tipo_fondo"]

    # --- cuerpo (virola) + cúpula (casquete) --------------------------------
    Ri = R - td
    to = math.acos(min(1, rh / R))
    ti = math.acos(min(1, rh / Ri))
    if "total" in g:  # altura total del recipiente (piso a cara superior del cuello)
        hc = g["total"] - hn - hd * math.sin(to)
    zo = hc + hd * math.sin(to)
    zi = hc + (hd - td) * math.sin(ti)
    if tipo == "concavo":
        zb = 0.0
    elif tipo == "cupula":
        zb = g["hf"]
    elif tipo == "cabezal":
        zb = hd
    else:  # co2: fondo semiesférico
        zb = R + g.get("z_pie", 0.0)
    piezas["cuerpo"] = _tube(R, R - t, hc - zb, (0, 0, zb))
    p = _Perfil((R, hc)).e(0, hc, R, hd, 0, to).l((rh, zi))
    p.e(0, hc, Ri, hd - td, ti, 0)
    piezas["cupula"] = p.revolve()

    # --- fondo ------------------------------------------------------------
    if tipo == "concavo":
        zc, zr = g["zf_centro"], g["zf_borde"]
        rf = R - t
        lo = [(rf * i / 10, zc + (zr - zc) * (i / 10) ** 2) for i in range(11)]
        up = [(r, z + tf) for r, z in reversed(lo)]
        pf = _Perfil((0, zc)).sp(lo).l((rf, zr + tf)).sp(up)
        piezas["fondo"] = pf.revolve()
    else:
        hf = {"cupula": g.get("hf", hd), "cabezal": hd, "co2": R}[tipo]
        pf = _Perfil((0, zb - hf)).e(0, zb, R, hf, -math.pi / 2, 0).l((R - tf, zb))
        pf.e(0, zb, R - tf, hf - tf, 0, -math.pi / 2)
        piezas["fondo"] = pf.revolve()

    # --- cuello (anillo roscado) ------------------------------------------
    bore = {"M30x1,5": 28.376, "M22x1,5": 20.376}.get(rosca, dh - 7.8 if dh > 60 else dh - 6)
    ztop = zo + hn
    cu = _tube(dh / 2 + 0.01, bore / 2, zo - zi + 1.0, (0, 0, zi - 1.0))
    cu = cu.fuse(_tube(dn / 2, bore / 2, hn, (0, 0, zo)))
    piezas["cuello"] = cu.clean()

    # --- cordones de soldadura (MIG) ----------------------------------------
    sw = max(1.0, 0.8 * t)
    Rs = R - 0.5 * t          # cordón a tope, sobremonta exterior 0,3·t
    sold = []
    if tipo != "co2":
        sold.append(_torus(Rs, sw, hc))                       # cúpula-cuerpo
        if tipo in ("cupula", "cabezal"):
            sold.append(_torus(Rs, sw, zb))                   # fondo-cuerpo
        else:
            sold.append(_torus(R - t, sw, g["zf_borde"] + tf))  # filete interior del fondo
    if tipo != "co2":
        sold.append(_torus(dn / 2, max(1.0, 0.8 * td), zo))    # cuello-cúpula
    if costura and tipo != "co2":
        sold.append(_box(3.0, 0.8 * t, hc - zb - 2, 0, -R + 0.1 * t, zb + 1))  # costura longitudinal
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
    datos = dict(R=R, z_cuello=ztop + z0, z_cupula=zo + z0, z_union=hc + z0, zb=zb + z0,
                 rosca=rosca, dn=dn, bore=bore, z_fondo=z0 + (g.get("zf_centro", 0) if tipo == "concavo" else zb - {"cupula": g.get("hf", hd), "cabezal": hd, "co2": R}[tipo]))
    return piezas, datos


# ---------------------------------------------------------------- válvula
def valvula(z0, s=1.0, x_tip=110.0, h_total=None, man_d=38.0, dn=37.0, bore=28.4, tipo="HZ", co2=False):
    """Válvula de palanca tipo HZ (latón forjado) con manómetro y pasador.
    z0 = cara superior del cuello. Si h_total se indica, se ajusta la altura del
    cuerpo para que la cota superior de la palanca sea z0 + h_total."""
    bw, bd = 30 * s, 28 * s
    hcol = 10 * s
    lev_t, lev_w = 4 * s, 20 * s
    ang_up = math.radians(7)
    x_piv = -bw / 2 - 5 * s
    rise = (x_tip - x_piv) * math.tan(ang_up)
    if h_total is not None:
        bh = h_total - hcol - 3 * s - lev_t - rise
        bh = max(22 * s, min(bh, 75 * s))
    else:
        bh = 40 * s
    p = {}
    zc = z0
    p["tuerca"] = _cyl(dn / 2 + 3 * s, hcol, (0, 0, zc)).cut(_cyl(bore / 2 - 2, hcol, (0, 0, zc)))
    p["espiga"] = _tube(bore / 2, bore / 2 - 3 * s, 12 * s, (0, 0, zc - 12 * s))
    zb0 = zc + hcol
    cuerpo = cq.Solid.makeBox(bw, bd, bh, cq.Vector(-bw / 2, -bd / 2, zb0))
    cuerpo = cq.Workplane().add(cuerpo).edges("|Z").fillet(4 * s).val()
    # boca de salida (-X)
    zs = zb0 + bh * 0.35
    cuerpo = cuerpo.fuse(_cyl(7 * s, 14 * s, (-bw / 2 + 1, 0, zs), (-1, 0, 0)))
    # boca de manómetro (-Y)
    zm = zb0 + bh * 0.55
    cuerpo = cuerpo.fuse(_cyl(4.5 * s, 7 * s, (0, -bd / 2 + 1, zm), (0, -1, 0)))
    p["cuerpo_valvula"] = cuerpo.clean()
    y_man = -bd / 2 - 6 * s
    if co2:
        # CO2: sin manómetro (control por pesada); disco de seguridad con tapón hexagonal
        hexa = cq.Workplane("XZ", origin=(0, -bd / 2 + 1, zm)).polygon(6, 14 * s).extrude(9 * s).val()
        p["disco_seguridad"] = hexa
    else:
        gm = _cyl(man_d / 2, 11 * s, (0, y_man, zm), (0, -1, 0))
        gm = gm.fuse(_torus(man_d / 2 - 1.2 * s, 1.2 * s, 0, 0, 0, (0, 1, 0)).translate(cq.Vector(0, y_man - 11 * s, zm)))
        p["manometro"] = gm.clean()
    # palanca inferior (manija de transporte, fija)
    zi = zb0 + bh * 0.62
    li = cq.Solid.makeBox(x_tip - 12 * s - bw / 2 + 4, lev_w, lev_t,
                          cq.Vector(bw / 2 - 4, -lev_w / 2, zi))
    li = li.rotate(cq.Vector(bw / 2, 0, zi), cq.Vector(bw / 2, 1, zi), 6)
    p["manija_inferior"] = li
    # palanca superior (gatillo) con eje
    zt = zb0 + bh + 3 * s
    ls = cq.Solid.makeBox(x_tip - x_piv, lev_w, lev_t, cq.Vector(x_piv, -lev_w / 2, zt))
    ls = ls.rotate(cq.Vector(x_piv, 0, zt), cq.Vector(x_piv, 1, zt), -7)
    p["manija_superior"] = ls
    p["eje"] = _cyl(3 * s, bd + 8 * s, (x_piv + 3 * s, -bd / 2 - 4 * s, zt - 2 * s), (0, 1, 0))
    p["vastago"] = _cyl(4 * s, 3 * s + 1, (0, 0, zb0 + bh - 1))
    # pasador de seguridad + anilla
    xs = bw / 2 + 7 * s
    zp = zt - 4 * s
    p["pasador"] = _cyl(1.6 * s, bd + 16 * s, (xs, -bd / 2 - 12 * s, zp), (0, 1, 0)).fuse(
        _torus(9 * s, 1.4 * s, 0, 0, 0, (0, 1, 0)).translate(cq.Vector(xs, -bd / 2 - 12 * s, zp - 9 * s))).clean()
    info = dict(z_salida=zs, x_salida=-bw / 2 - 13 * s, bw=bw, bd=bd, bh=bh, z_top=zt + lev_t + rise,
                x_piv=x_piv, z_man=zm, y_man=y_man - 11 * s, man_d=man_d, zb0=zb0, s=s)
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

    # ancho: de la tobera/manguera (-X) a la punta de la palanca (+X)
    d_hose = 0 if chico else 16.0
    if fam == "co2":
        d_noz = 70.0 if R < 60 else 90.0
    elif fam == "inox":
        d_noz = 30.0 if "AFFF" in m.nombre else (26.0 if "K" in m.nombre else 22.0)
    else:
        d_noz = 22.0
    if chico:
        xmin = -(15 * s + 13 * s + 26)
    else:
        xh = -(R + 4 + max(d_hose, d_noz) / 2)
        xmin = xh - max(d_hose, d_noz) / 2
    x_tip = W + xmin + cW
    man_d = 28.0 if chico else 38.0
    val, vi = valvula(dr["z_cuello"], s=s, x_tip=x_tip, h_total=H - dr["z_cuello"] + cH,
                      man_d=man_d, dn=g["cuello"][0], bore=dr["bore"], co2=(fam == "co2"))
    out.update(val)
    info["valvula"] = vi

    # caño de pesca
    zf = dr["z_fondo"] + g["tf"] + 18
    zs0 = dr["z_cuello"] - 12 * s
    if fam != "co2":
        out["cano_pesca"] = _tube(6 * s, 4.5 * s, zs0 - zf, (0, 0, zf))
    else:
        out["cano_pesca"] = _tube(5, 3.5, zs0 - zf, (0, 0, zf))

    xs, zs = vi["x_salida"], vi["z_salida"]
    if chico:
        # tobera directa
        noz = cq.Solid.makeCone(6 * s, 4 * s, 26, cq.Vector(xs, 0, zs), cq.Vector(-1, 0, 0))
        out["tobera"] = noz
        info["tobera"] = (xs - 13, zs)
    elif fam == "co2" and R < 60:
        # brazo giratorio + difusor (sin manga, según catálogo)
        arm = _sweep_circle([(xs, 0, zs), (xh, 0, zs, 12), (xh, 0, zs - 60)], 6)
        out["brazo_difusor"] = arm
        hl = 180.0
        cone = cq.Solid.makeCone(12, d_noz / 2, hl, cq.Vector(xh, 0, zs - 60), cq.Vector(0, 0, -1))
        cone = cone.cut(cq.Solid.makeCone(10, d_noz / 2 - 2.5, hl, cq.Vector(xh, 0, zs - 60), cq.Vector(0, 0, -1)))
        out["difusor"] = cone
        info["tobera"] = (xh, zs - 60 - hl / 2)
    else:
        # manguera: horizontal, curva y bajada paralela al cuerpo
        rb = max(8.0, min(40.0, abs(xh - (xs - 12)) - 4))
        if fam == "co2":
            l_noz = 260.0
        elif fam == "inox":
            l_noz = 190.0 if "AFFF" in m.nombre else (230.0 if "K" in m.nombre else 90.0)
        else:
            l_noz = 70.0
        z_n_bot = max(0.18 * H, dr["z_fondo"] + 40)
        l_noz = min(l_noz, zs - rb - 25 - z_n_bot)
        z_n_top = z_n_bot + l_noz
        out["racor"] = cq.Solid.makeCylinder(9, 12, cq.Vector(xs, 0, zs), cq.Vector(-1, 0, 0))
        x1 = xs - 12
        pts = [(x1, 0, zs), (xh, 0, zs, rb), (xh, 0, z_n_top + 5)]
        out["manguera"] = _sweep_circle(pts, d_hose / 2)
        if fam == "co2":
            cone = cq.Solid.makeCone(10, d_noz / 2, l_noz, cq.Vector(xh, 0, z_n_top), cq.Vector(0, 0, -1))
            cone = cone.cut(cq.Solid.makeCone(8, d_noz / 2 - 2.5, l_noz, cq.Vector(xh, 0, z_n_top), cq.Vector(0, 0, -1)))
            out["difusor"] = cone
        else:
            noz = _cyl(d_noz / 2, l_noz, (xh, 0, z_n_bot))
            noz = noz.cut(_cyl(d_noz / 2 - 3, 10, (xh, 0, z_n_bot)))
            out["tobera"] = noz.clean()
        # suncho portamanguera
        zsu = z_n_bot + l_noz * 0.45
        band = _tube(R + 1.5, R - 0.2, 18, (0, 0, zsu - 9))
        clip = _box(abs(xh) - R + d_noz / 2 + 3, 12, 18, (xh + (-R)) / 2 - 1, 0, zsu - 9)
        clip = clip.cut(_cyl(d_noz / 2 + 0.2, 18, (xh, 0, zsu - 9)))
        out["suncho"] = band.fuse(clip).clean()
        info["tobera"] = (xh, (z_n_bot + z_n_top) / 2)
        info["suncho_z"] = zsu
    if fam == "co2":
        # pie de apoyo (base plástica)
        zb = dr["zb"] - R
        hp = 0.55 * R
        pie = _tube(R, R - 3.0, hp, (0, 0, 0)).fuse(_cyl(R, 4, (0, 0, 0)))
        out["pie"] = pie.clean()
        for k in list(piezas):
            out[k] = out[k].translate(cq.Vector(0, 0, 0))
    return out, info


def extintor_rodante(m, cD=0.0):
    g = dict(m.geo)
    H, W, D = m.H, m.W, m.D
    Dw = float(m.spec["Diámetro de rueda (mm)"])
    Rw = Dw / 2
    bw_w = 55.0 if Dw <= 300 else (70.0 if Dw <= 350 else 80.0)
    R = g["R"]
    z0 = 45.0 + (g["hd"])  # el cabezal inferior queda a 45 mm del piso
    piezas, dr = recipiente(dict(g), z0 - g["hd"], costura=True)
    out = dict(piezas)
    info = dict(recipiente=dr)
    d_hose = 25.0
    y_loop = -(R + 22 + d_hose / 2)
    y_min = y_loop - d_hose / 2 - 3
    yw = y_min + D - Rw + cD
    track = W - bw_w
    xw = track / 2
    # ruedas
    for sgn, nom in ((1, "rueda_der"), (-1, "rueda_izq")):
        c = cq.Vector(sgn * (xw - bw_w / 2), yw, Rw)
        tire = _cyl(Rw, bw_w, (c.x, c.y, c.z), (sgn, 0, 0))
        tire = tire.cut(_cyl(Rw * 0.55, bw_w, (c.x, c.y, c.z), (sgn, 0, 0)))
        rim = _cyl(Rw * 0.55, bw_w - 10, (c.x + sgn * 5, c.y, c.z), (sgn, 0, 0))
        hub = _cyl(30, bw_w + 10, (c.x - sgn * 10, c.y, c.z), (sgn, 0, 0))
        out[nom] = tire.fuse(rim).fuse(hub).clean()
    out["eje_ruedas"] = _cyl(12.5, track - bw_w + 20, (-(xw - bw_w / 2) + 10 - 10, yw, Rw), (1, 0, 0))
    # bastidor: dos parantes + arco superior (caño Ø25,4)
    rt = 12.7
    xa = min(R + 45, xw - bw_w / 2 - 20)
    ztop_arc = H - rt
    zc = ztop_arc - xa
    ya = yw
    arco = _sweep_circle([(-xa, ya, Rw + 30), (-xa, ya, zc), ], rt)
    arco = arco.fuse(_sweep_circle([(xa, ya, Rw + 30), (xa, ya, zc)], rt))
    semi = cq.Edge.makeThreePointArc(cq.Vector(-xa, ya, zc), cq.Vector(0, ya, ztop_arc), cq.Vector(xa, ya, zc))
    semi_s = cq.Solid.sweep(cq.Wire.makeCircle(rt, cq.Vector(-xa, ya, zc), cq.Vector(0, 0, 1)), [],
                            cq.Wire.assembleEdges([semi]), transitionMode="round")
    out["bastidor"] = arco.fuse(semi_s).clean()
    # brazos de sujeción recipiente-bastidor y sunchos
    zs1 = dr["zb"] + 0.25 * g["hc"]
    zs2 = dr["zb"] + 0.85 * g["hc"]
    sun = None
    for zz in (zs1, zs2):
        b = _tube(R + 4, R + 0.1, 40, (0, 0, zz - 20))
        for sg in (1, -1):
            if xa > R:
                b = b.fuse(_box(xa - R + 10, 25, 40, sg * (R + xa) / 2, 0, zz - 20))
                y0 = 0.0
            else:
                y0 = math.sqrt(R * R - xa * xa) - 2
            b = b.fuse(_box(25, ya - y0 + 10, 40, sg * xa, (ya + y0) / 2, zz - 20))
        sun = b if sun is None else sun.fuse(b)
    out["sunchos_bastidor"] = sun.clean()
    # apoyo delantero
    out["apoyo"] = _box(70, 50, dr["zb"] - dr["z_fondo"] + 10 - (dr["zb"] - dr["z_fondo"] - 45) + 0.0, 0, -R * 0.35, 0) \
        if False else _box(70, 50, 55, 0, -R * 0.30, 0)
    # válvula
    s = 1.35
    val, vi = valvula(dr["z_cuello"], s=s, x_tip=R * 0.75, h_total=None, man_d=50.0,
                      dn=g["cuello"][0], bore=dr["bore"])
    out.update(val)
    info["valvula"] = vi
    zf = dr["z_fondo"] + g["tf"] + 25
    out["cano_pesca"] = _tube(12, 9.5, dr["z_cuello"] - 12 * s - zf, (0, 0, zf))
    # manguera enrollada al frente (lazo) + tramo a la tobera
    z_lo = dr["zb"] + 0.12 * g["hc"]
    z_hi = dr["zb"] + g["hc"] * 0.95
    wl = 0.55 * R
    lazo = [(-wl, y_loop, z_lo + wl), (-wl, y_loop, z_hi - wl)]
    e1 = cq.Edge.makeLine(cq.Vector(-wl, y_loop, z_lo + wl), cq.Vector(-wl, y_loop, z_hi - wl))
    a1 = cq.Edge.makeThreePointArc(cq.Vector(-wl, y_loop, z_hi - wl), cq.Vector(0, y_loop, z_hi), cq.Vector(wl, y_loop, z_hi - wl))
    e2 = cq.Edge.makeLine(cq.Vector(wl, y_loop, z_hi - wl), cq.Vector(wl, y_loop, z_lo + wl))
    a2 = cq.Edge.makeThreePointArc(cq.Vector(wl, y_loop, z_lo + wl), cq.Vector(0, y_loop, z_lo), cq.Vector(-wl, y_loop, z_lo + wl))
    wire = cq.Wire.assembleEdges([e1, a1, e2, a2])
    out["manguera_enrollada"] = cq.Solid.sweep(
        cq.Wire.makeCircle(d_hose / 2, cq.Vector(-wl, y_loop, z_lo + wl), cq.Vector(0, 0, 1)), [], wire,
        transitionMode="round")
    # soportes de manguera
    sop = None
    for zz in (z_lo + wl * 0.4, z_hi - wl * 0.4, (z_lo + z_hi) / 2):
        b = _box(2 * wl + d_hose + 16, 8, 30, 0, y_loop, zz - 15)
        b = b.fuse(_box(20, abs(y_loop) - R + 4, 30, 0, (y_loop - R) / 2, zz - 15))
        sop = b if sop is None else sop.fuse(b)
    out["soportes_manguera"] = sop.clean()
    # tramo válvula -> tobera
    xs, zs = vi["x_salida"], vi["z_salida"]
    xn = -(R + 30)
    zn_top = dr["zb"] + 0.45 * g["hc"]
    out["racor"] = _cyl(12, 16, (xs, 0, zs), (-1, 0, 0))
    out["manguera"] = _sweep_circle([(xs - 16, 0, zs), (xn, 0, zs, 60), (xn, 0, zn_top + 60)], d_hose / 2)
    # válvula esférica + tobera campana
    ve = _box(40, 40, 60, xn, 0, zn_top)
    ve = ve.fuse(_box(14, 90, 12, xn, -65, zn_top + 24))
    out["valvula_esferica"] = ve.clean()
    hn = 200.0
    tb = cq.Solid.makeCone(16, 34, hn, cq.Vector(xn, 0, zn_top), cq.Vector(0, 0, -1))
    tb = tb.cut(cq.Solid.makeCone(13, 31, hn, cq.Vector(xn, 0, zn_top), cq.Vector(0, 0, -1)))
    out["tobera_campana"] = tb
    info.update(dict(Rw=Rw, bw_w=bw_w, xw=xw, yw=yw, track=track, xa=xa, y_loop=y_loop,
                     tobera=(xn, zn_top - hn / 2), valv_esf=(xn, zn_top + 30)))
    return out, info


def construir(m):
    """Construye el conjunto y corrige (2 iteraciones) para que la caja
    envolvente coincida con altura/ancho/profundidad del catálogo."""
    if m.familia == "rodante":
        p, i = extintor_rodante(m)
        bb = bbox(p)
        p, i = extintor_rodante(m, cD=m.D - bb.ylen)
        return p, i
    cW = cH = 0.0
    for _ in range(3):
        p, i = extintor_manual(m, cW, cH)
        bb = bbox(p)
        cW += m.W - bb.xlen
        cH += m.H - bb.zmax
        if abs(m.W - bb.xlen) < 0.05 and abs(m.H - bb.zmax) < 0.05:
            break
    return p, i


def compuesto(piezas):
    return cq.Compound.makeCompound(list(piezas.values()))


def bbox(piezas):
    # caja exacta sobre la geometría B-rep (no sobre la triangulación)
    from OCP.Bnd import Bnd_Box
    from OCP.BRepBndLib import BRepBndLib
    b = Bnd_Box()
    BRepBndLib.AddOptimal_s(compuesto(piezas).wrapped, b, False, False)
    return cq.occ_impl.geom.BoundBox(b)
