"""Extintores sustitutos: equipos de FLAMA (prestador del servicio) que quedan en el puesto del cliente mientras su
extintor está en mantenimiento o recarga. (En IRAM 3517-2 «reserva» es otra cosa: la dotación propia del cliente, 5.3.)

Requisitos (se citan apartados, no se transcriben):
  IRAM 3517-2:2020 9.4.5: igual clasificación y por lo menos igual capacidad que el retirado; con todos los requisitos
      de mantenimiento; si son del prestador: color normativo (casquetes pueden ser de otro color) y faja o cinta
      AMARILLA de 40 mm de alto como máximo en el borde inferior o pollera, con: 1) leyenda de extintor sustituto;
      2) leyenda de que reemplaza al equipo de ese puesto, en mantenimiento o recarga; 3) datos, logo o marca del
      prestador propietario.
  Res. 349/07 (PBA) art. 32: el recargador que repone matafuegos propios para mantener el potencial extintor
      (art. 33 Dto. 4992/90) puede usar en ellos una tarjeta de identificación DPS con un sello «sustituto
      habilitado», reutilizable en cada revisión de carga mientras esté legible; numeración asentada en el libro de
      actas.
  Res. AGC 32/15 anexo II (CABA): en el sistema de tarjetas, «Es sustituto» = venta / recarga de un extintor sin
      domicilio de instalación predefinido (no se carga domicilio).
  Mercado (Fullmat, Rodo, Eversafe, Biston): se deja el sustituto con un remito con membrete de la empresa.

Producto FL_SUS_<tipo>, unitario (el tamaño del parque se dimensiona aparte). Planos en salida/sustituto/:
FL_SUS_00 (equivalencias y ciclo) y FL_SUS_<tipo> por modelo (faja acotada, desarrollo de la faja, kit).
"""

import math
import os

import cadquery as cq
import shapely.geometry as sg

from . import modelo3d as M
from . import vistas as V
from .catalogo import MODELOS
from .lamina import Hoja, nuevo_doc, A, ROT_H
from .planos import FECHA, DIBUJO, _tabla

FAJA_MAX = 40.0       # IRAM 3517-2:2020 9.4.5 b): alto máximo de la faja amarilla
SOLAPE = 20.0         # solape de la cinta al cerrar el perímetro


def codigo(m):
    return m.codigo.replace("FL_MAT_", "FL_SUS_")


def _cap(m):
    return float(m.capacidad.split()[0].replace(",", "."))


def equivalencia(m):
    """(sustituto adoptado, clasificación, alternativa admisible por 9.4.5, criterio)."""
    from .rotulado import clases
    cls = "".join(clases(m))
    fam = m.codigo.rsplit("_", 1)[0]
    mayores = [x for x in MODELOS if x.codigo.rsplit("_", 1)[0] == fam and _cap(x) > _cap(m)
               and (x.familia == "rodante") == (m.familia == "rodante")]
    alt = ("mismo tipo de mayor capacidad: " + ", ".join(x.capacidad for x in mayores)) if mayores else "-"
    com = "igual clasificación e igual capacidad (mismo modelo)"
    if "HCFC" in m.codigo:
        com += "; agente limpio: no sustituir por polvo"
    return codigo(m), cls, alt, com


def faja(m, p):
    """(alto, largo desarrollado, z0, R) de la faja amarilla en la pollera, sin tapar la oblea PBA."""
    cb = p["cuerpo"].BoundingBox()
    R = (cb.xmax - cb.xmin) / 2
    W, H, z0, _, _, _ = M.placa_dim(m, p)
    zo = z0 - 3.0 - M.OBLEA_PBA
    alto = min(FAJA_MAX, zo - cb.zmin - 3.0)
    return alto, 2 * math.pi * R + SOLAPE, cb.zmin, R


def bom_sustituto(m):
    from .bom import PROPIOS
    rows = []
    base = codigo(m).replace("FL_SUS_", "SUS-")
    p, _ = M.construir(m)
    alto, largo, _, _ = faja(m, p)

    def add(nivel, cod, desc, cant, um, mat="", med="", ori="", norma="", fte="", obs=""):
        rows.append(dict(nivel=nivel, codigo=cod, desc=desc, cant=cant, um=um, mat=mat, med=med, peso=None, ori=ori,
                         op="", norma=norma, fte=fte, plano=codigo(m), obs=obs, sub=0))

    add(0, codigo(m), f"Extintor sustituto para {m.nombre}", 1, "u", norma="IRAM 3517-2:2020 9.4.5", fte="N",
        obs="Unitario: el tamaño del parque de sustitutos se dimensiona aparte")
    add(1, m.codigo, f"Extintor base: {m.nombre} (mismo modelo)", 1, "u",
        ori=("Stock FLAMA (fabricación propia)" if m.codigo in PROPIOS else "Stock FLAMA (comprado terminado)"),
        norma="IRAM 3517-2:2020 9.4.5", fte="N",
        obs="Igual clasificación y capacidad; mantenimiento vigente. BOM: hoja " + m.codigo)
    add(1, f"{base}-K", "Identificación de extintor sustituto", 1, "u", ori="Compra", fte="N")
    add(2, f"{base}-01", "Faja amarilla de sustituto en la pollera (3 leyendas)", 1, "u",
        "Cinta vinílica autoadhesiva amarilla", f"{alto:.0f} × {largo:.0f} (alto ≤ 40; perímetro + {SOLAPE:.0f} de "
        "solape)", "Compra", norma="IRAM 3517-2:2020 9.4.5 b)", fte="N",
        obs="Leyendas: extintor sustituto / reemplaza al equipo de este puesto en mantenimiento o recarga / FLAMA "
            "S.A. (datos y logo). Proveedor a cotizar")
    add(2, f"{base}-02", "Tarjeta de identificación DPS con sello «SUSTITUTO HABILITADO»", 1, "u",
        "Tarjeta oficial DPS (PBA)", "formato oficial", "Compra (organismo)", norma="Res. 349/07 art. 32", fte="N",
        obs="Sólo PBA; reutilizable en cada revisión de carga; n° del extintor asentado en el libro de actas")
    add(2, f"{base}-03", "Tarjeta AGC con «Es sustituto» (sin domicilio de instalación)", 1, "u",
        "Etiqueta autoadhesiva AGC", "formato oficial", "Compra (organismo)", norma="Res. AGC 32/15 anexo II",
        fte="N", obs="Sólo CABA")
    add(2, f"{base}-04", "Remito de préstamo con membrete (n° de extintor, puesto, equipo retirado, fechas)", 1,
        "u/préstamo", "Papel", "A5 duplicado", "Compra", fte="I",
        obs="Práctica de mercado relevada (Fullmat, Rodo, Eversafe)")
    return rows


# ------------------------------------------------------------------ planos
def _rot(cod, tipo, sub, esc="-"):
    return dict(titulo="Extintor sustituto", subtitulo=sub, codigo=cod, hoja=1, hojas=1, escala=esc,
                material="Ver lista", edicion="0", fecha=FECHA, dibujo=DIBUJO, reviso="", aprobo="", tipo_doc=tipo,
                empresa="FLAMA S.A.")


def _desarrollo(h, x, y, largo, alto, e):
    """Desarrollo de la faja (rayado = amarillo) con las 3 leyendas en tamaño real repetidas a lo largo."""
    h.rect(x, y, x + largo * e, y + alto * e, "01-VISIBLE")
    h.rayado(sg.box(x, y, x + largo * e, y + alto * e), 45, 4.0)
    textos = ("EXTINTOR SUSTITUTO", "REEMPLAZA AL EQUIPO DE ESTE PUESTO, EN MANTENIMIENTO O RECARGA",
              "FLAMA S.A. - logo - tel.")
    k = alto / FAJA_MAX
    hs = [9.0 * k, 4.6 * k, 4.6 * k]                         # alturas reales de letra (mm)
    paso = max(len(t) * a * 0.86 for t, a in zip(textos, hs)) * 1.12
    n = max(1, int(largo // paso))
    for i in range(n):
        cx = x + (i + 0.5) * largo / n * e
        for j, (t, a) in enumerate(zip(textos, hs)):
            h.texto(t, (cx, y + alto * e * (0.72 - 0.3 * j)), a * e, A.MIDDLE_CENTER)


def plano_modelo(m, doc):
    cod = codigo(m)
    p, _ = M.construir(m)
    alto, largo, zb, R = faja(m, p)
    cb = p["cuerpo"].BoundingBox()
    xc, yc = (cb.xmax + cb.xmin) / 2, (cb.ymax + cb.ymin) / 2
    p["faja_sustituto"] = M._sector(R, R + 0.3, alto, zb, 2 * math.pi * R * 0.999, xc, yc)
    h = Hoja(doc, "A3", 0.0)
    h.formato()
    X0, Y0, X1, Y1 = h.fx0, h.fy0, h.fx1, h.fy1
    h.texto(f"EXTINTOR SUSTITUTO PARA {m.nombre.upper()} (IRAM 3517-2:2020 9.4.5)", ((X0 + X1) / 2, Y1 - 6), 4,
            A.MIDDLE_CENTER)
    vis = {k: v for k, v in p.items() if k != "soldaduras"}
    pa = V.proyectar(cq.Compound.makeCompound(list(vis.values())), "anterior", tol=0.5, ocultas=False)
    ea = V.extension(pa["vis"])
    zx0, zx1, zy0, zy1 = X0 + 6, X0 + 150, Y0 + 132, Y1 - 16
    f = next(s for s in (1 / 2, 1 / 5, 1 / 10, 1 / 20) if (ea[2] - ea[0]) * s + 40 <= zx1 - zx0 and
             (ea[3] - ea[1]) * s <= zy1 - zy0 - 12)
    xa = (zx0 + zx1) / 2 - 10 - (ea[0] + ea[2]) / 2 * f
    ya = (zy0 + zy1) / 2 - (ea[1] + ea[3]) / 2 * f
    h.prims(pa["vis"], "01-VISIBLE", (xa, ya, f))
    x0b, x1b = xa + (xc - R) * f, xa + (xc + R) * f
    h.rayado(sg.box(x0b, ya + zb * f, x1b, ya + (zb + alto) * f), 45, 1.0)
    h.cota_lineal((x1b, ya + zb * f), (x1b, ya + (zb + alto) * f), (x1b + 10, ya), 90, 1 / f)
    h.cota_lineal((x0b, ya + zb * f), (x1b, ya + zb * f), (x0b, ya + zb * f - 8), 0, 1 / f, prefijo="%%c")
    h.nota_referencia("1 Faja amarilla de sustituto", ((x0b + x1b) / 2, ya + (zb + alto / 2) * f),
                      (x0b - 4, ya + (zb + alto) * f + 22), 2.2)
    h.texto(f"VISTA ANTERIOR (esc. 1:{1 / f:.0f})", ((zx0 + zx1) / 2, zy1 - 2), 2.8, A.MIDDLE_CENTER)
    h.texto(f"Faja en el borde inferior del cuerpo (pollera), alto {alto:.0f} mm (≤ 40, sin tapar la oblea PBA); "
            "rodea todo el perímetro.", (zx0, zy0 - 3), 1.9)
    # isometría
    mov = dict(vis)
    mov["faja_sustituto"] = vis["faja_sustituto"].translate(cq.Vector(0, 0, -max(30.0, 0.25 * R)))
    pi = V.proyectar(cq.Compound.makeCompound(list(mov.values())), "iso", tol=0.6, ocultas=False)
    ei = V.extension(pi["vis"])
    ix0, ix1, iy0, iy1 = X0 + 156, X0 + 262, Y1 - 150, Y1 - 14
    fi = next(s for s in (1 / 2, 1 / 5, 1 / 10, 1 / 20) if (ei[2] - ei[0]) * s <= ix1 - ix0 - 18 and
              (ei[3] - ei[1]) * s <= iy1 - iy0 - 8)
    oxi = (ix0 + ix1) / 2 - 8 - (ei[0] + ei[2]) / 2 * fi
    oyi = (iy0 + iy1) / 2 - (ei[1] + ei[3]) / 2 * fi
    h.prims(pi["vis"], "01-VISIBLE", (oxi, oyi, fi))
    bb = mov["faja_sustituto"].BoundingBox()
    c = V.proyectar_punto((bb.xmax, (bb.ymin + bb.ymax) / 2, (bb.zmin + bb.zmax) / 2), "iso")
    h.globo(1, (oxi + c[0] * fi, oyi + c[1] * fi), (ix1 - 4, oyi + c[1] * fi - 8), r=4.0)
    h.texto(f"ISOMETRÍA, FAJA DESPLAZADA (esc. 1:{1 / fi:.0f})", ((ix0 + ix1) / 2, iy1 + 1), 2.6, A.MIDDLE_CENTER)
    # requisitos y tarjetas
    tx, ty = X0 + 268, Y1 - 20
    lin = ["REQUISITOS (se citan apartados):",
           "· IRAM 3517-2:2020 9.4.5: igual clasificación y por lo menos",
           "  igual capacidad que el retirado; mantenimiento vigente;",
           "  color normativo (los casquetes pueden ir de otro color);",
           "  faja o cinta amarilla ≤ 40 mm en la pollera con 3 leyendas.",
           "· Res. 349/07 art. 32 (PBA): tarjeta DPS con sello",
           "  «SUSTITUTO HABILITADO», reutilizable mientras sea",
           "  legible; n° del extintor en el libro de actas.",
           "· Res. AGC 32/15 anexo II (CABA): tarjeta con «Es",
           "  sustituto», sin domicilio de instalación.",
           "· Remito de préstamo con membrete (práctica de mercado).",
           "· El sustituto conserva su placa, oblea / tarjeta y",
           "  precinto; la faja no debe tapar ninguno."]
    for i, t in enumerate(lin):
        h.texto(t, (tx, ty - 4.3 * i), 2.0 if i else 2.4)
    # desarrollo de la faja
    e = next(s for s in (1.0, 0.5, 0.4, 0.2, 0.1) if largo * s <= X1 - X0 - 20)
    dx, dy = X0 + 8, Y0 + 98
    h.texto(f"DETALLE 1 - DESARROLLO DE LA FAJA {alto:.0f} × {largo:.0f} (esc. {'1:1' if e == 1 else '1:' + format(1 / e, 'g').replace('.', ',')})"
            " - amarillo; leyendas negras repetidas", (dx, dy + alto * e + 4), 2.6)
    _desarrollo(h, dx, dy, largo, alto, e)
    h.cota_lineal((dx, dy), (dx + largo * e, dy), (dx, dy - 6), 0, 1 / e)
    # lista
    base = cod.replace("FL_SUS_", "SUS-")
    sus, cls, alt, com = equivalencia(m)
    filas = [("Glo.", "Código BOM", "Denominación", "Cant."),
             ("1", f"{base}-01", f"Faja amarilla de sustituto {alto:.0f} × {largo:.0f}", "1"),
             ("—", f"{base}-02", "Tarjeta DPS con sello «SUSTITUTO HABILITADO» (PBA)", "1"),
             ("—", f"{base}-03", "Tarjeta AGC «Es sustituto» (CABA)", "1"),
             ("—", f"{base}-04", "Remito de préstamo con membrete", "1/préstamo"),
             ("—", m.codigo, "Extintor base del mismo modelo (BOM: hoja " + m.codigo + ")", "1")]
    y = _tabla(h, X0 + 6, Y0 + ROT_H + 34, filas, [9, 32, 112, 18], alto=4.4, hs=(2.0, 1.9, 1.8, 1.9),
               encabezado=f"LISTA - BOM {cod}")
    h.texto(f"Clasificación {cls} · alternativa admisible: {alt}", (X0 + 6, Y0 + 4), 1.8)
    h.rotulo(_rot(cod, "Extintor sustituto", f"Identificación sobre {m.nombre.replace('Extintor ', '')}",
                  f"1:{1 / f:.0f}"))
    return h


def hoja_general(doc):
    h = Hoja(doc, "A3", 0.0)
    h.formato()
    h.rotulo(_rot("FL_SUS_00", "Equivalencias y ciclo", "Tabla por tipo y ciclo de préstamo"))
    X0, Y0, X1, Y1 = h.fx0, h.fy0, h.fx1, h.fy1
    h.texto("EXTINTOR SUSTITUTO - EQUIVALENCIAS (IRAM 3517-2:2020 9.4.5) Y CICLO DE PRÉSTAMO", ((X0 + X1) / 2, Y1 - 6),
            4, A.MIDDLE_CENTER)
    filas = [("Equipo del cliente", "Sustituto", "Clase", "Alternativa admisible (≥ capacidad)", "Criterio")]
    for m in MODELOS:
        sus, cls, alt, com = equivalencia(m)
        filas.append((m.nombre.replace("Extintor ", ""), sus, cls, alt, com))
    _tabla(h, X0 + 4, Y1 - 12, filas, [52, 42, 16, 110, 162], alto=5.0, hs=(1.9, 1.9, 1.9, 1.7, 1.6),
           encabezado="TABLA DE EQUIVALENCIAS")
    from .esquemas import caja, flecha
    y = Y0 + 140
    pasos = ["1 Pedido de\nmantenimiento", "2 Retiro del equipo\n+ entrega del sustituto", "3 Remito + tarjeta\n"
             "DPS / AGC sustituto", "4 Mantenimiento del\nequipo del cliente", "5 Devolución +\nretiro del sustituto",
             "6 Inspección del\nsustituto", "7 Stock de\nsustitutos"]
    xs = [X0 + 22 + i * 50 for i in range(len(pasos))]
    for i, (x, t) in enumerate(zip(xs, pasos)):
        caja(h, x, y, 42, 16, t, hs=2.0)
        if i:
            flecha(h, (xs[i - 1] + 21, y), (x - 21, y))
    yd, yr = y - 30, y - 58
    caja(h, xs[5], yd, 42, 14, "¿Precinto roto o\ncarga fuera de rango?", hs=2.0)
    flecha(h, (xs[5], y - 8), (xs[5], yd + 7))
    h.linea((xs[5] + 21, yd), (xs[6], yd), "08-FINA")
    flecha(h, (xs[6], yd), (xs[6], y - 8))
    h.texto("no", (xs[5] + 25, yd + 2), 2.0, A.BOTTOM_LEFT)
    caja(h, xs[5], yr, 42, 14, "Recarga del sustituto\n(proceso de recarga)", hs=2.0)
    flecha(h, (xs[5], yd - 7), (xs[5], yr + 7))
    h.texto("sí", (xs[5] + 2, (yd + yr) / 2), 2.0, A.MIDDLE_LEFT)
    h.linea((xs[5] + 21, yr), (xs[6] + 6, yr), "08-FINA")
    h.linea((xs[6] + 6, yr), (xs[6] + 6, yd), "08-FINA")
    flecha(h, (xs[6] + 6, yd), (xs[6] + 6, y - 8))
    h.texto("CICLO DE PRÉSTAMO (unitario; el tamaño del parque de sustitutos se dimensiona aparte)", (X0 + 4, y + 16), 3)
    return h


def generar(base):
    """salida/sustituto/: FL_SUS_00 + FL_SUS_<tipo> por modelo + FLAMA_sustitutos.pdf."""
    import pymupdf
    from . import exportar as X
    d = os.path.join(base, "sustituto")
    os.makedirs(d, exist_ok=True)
    total = pymupdf.open()
    hj = [("Lamina", "A3", 0.0)]
    for cod, fn in [("FL_SUS_00", lambda doc: hoja_general(doc))] + \
                   [(codigo(m), (lambda mm: lambda doc: plano_modelo(mm, doc))(m)) for m in MODELOS]:
        doc = nuevo_doc()
        fn(doc)
        X.preparar_layouts(doc, hj)
        doc.saveas(os.path.join(d, f"{cod}.dxf"))
        p = X.pdf_hojas(doc, hj)
        p.set_metadata({"title": f"{cod} - Extintor sustituto", "author": "FLAMA S.A."})
        p.save(os.path.join(d, f"{cod}.pdf"))
        total.insert_pdf(p)
        print(cod, flush=True)
    total.save(os.path.join(d, "FLAMA_sustitutos.pdf"))
    return total
