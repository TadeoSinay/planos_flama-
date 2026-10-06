"""Hoja 4 de cada plano FL_MAT: rotulado e identificación del extintor nuevo.

Fuentes (se citan apartados, no se transcriben las normas):
  IRAM 3534:1983 placas de características: contenido 2.2.1 (1° prominente: símbolos/pictogramas e
      instrucciones; 2° marca del fabricante; 3° datos), símbolos fig. 1 (mín. 12 mm), colores 2.2.2.3,
      pictogramas 2.2.3 (mín. 18 mm), letras 2.2.4.3 (altura según masa total, proporciones fig. 2,
      longitud máxima arco 108°), ensayos de adherencia y abrasión (cap. 3 y 5).
  IRAM 3523:1983 cap. 5 (polvo manual): marcado del recipiente 5.1, leyendas propias 5.2.4 (tipo, contenido
      bajo presión, mes/año, n° de recipiente, etiqueta del polvo n, nitrógeno seco o, Sello IRAM p), 7.13 e).
  IRAM 3550:1981 cap. 5 (polvo sobre ruedas): marcado 5.1 (incluye presión de ensayo), leyendas 5.2.4.
  IRAM 3504:2001 cap. 6 (gases limpios): leyendas de uso en espacios cerrados y gas según IRAM 3526.
  IRAM Anexo R (DC-PG-129 rev. 12, 2025): estampilla de conformidad de extintor nuevo, provista por IRAM.
  Res. OPDS 522/07 anexos 1, 2 y 6 (Provincia de Buenos Aires): oblea de fabricación Ø 46.
  Ordenanza 40.473 art. 6 (CABA): tarjeta oficial de vigencia.
  IRAM 3517-2:2020 9.4.13: traba y precinto (identificación del fabricante y del lote).
"""

import math
import textwrap

import shapely.geometry as sg

from . import modelo3d as M
from . import vistas as V
from . import agentes as AG
from .lamina import Hoja, A
from .planos import _tabla, rotulo_base

PROPIOS_ROT = {"3523", "3550"}     # extintores que fabrica FLAMA: placa diseñada por FLAMA


def _n(v, d=1):
    s = f"{v:.{d}f}".replace(".", ",")
    return s.rstrip("0").rstrip(",") if "," in s else s


def clases(m):
    ag = AG.agente(m)["grado"]
    if m.codigo.startswith("FL_MAT_ABC") or "HCFC" in m.codigo:
        return ["A", "B", "C"]
    if "_BC_" in m.codigo:
        return ["B", "C"]
    if "CLASED" in m.codigo:
        return ["D"]
    if "CO2" in m.codigo:
        return ["B", "C"]
    if "AFFF" in m.codigo:
        return ["A", "B"]
    if "SALESK" in m.codigo:
        return ["A", "K"]
    return ["A"] if ag else []


def pictogramas(m):
    """IRAM 3534 2.2.3: (fuego A, fuego B, fuego C) -> True apto / False tachado; None si la norma no lo prevé."""
    c = clases(m)
    if "D" in c or "K" in c:
        return None
    return [x in c for x in ("A", "B", "C")]


def _mpa(v):
    return f"{_n(float(v.replace(',', '.')), 1)} MPa ({_n(float(v.replace(',', '.')) * 1000, 0)} kPa)"


def contenido(m):
    """Filas (zona, ítem, texto de la placa, referencia) para el modelo."""
    s = m.spec
    n_ext = s["Norma IRAM extintor"]
    ag = AG.agente(m)
    rod = m.familia == "rodante"
    alc = str(s.get("Alcance (m)", "")).split("/")[0].replace(",", ".")
    cls = clases(m)
    filas = [
        ("1", "Símbolos de clase", " · ".join(cls) + " (fig. 1, mín. 12 mm; verde/rojo/azul/amarillo IRAM-DEF D 10-54)",
         "3534 2.2.2"),
    ]
    pic = pictogramas(m)
    filas.append(("1", "Pictogramas", ("A " + ("apto" if pic[0] else "tachado") + " · B " + ("apto" if pic[1] else
                  "tachado") + " · C " + ("apto" if pic[2] else "tachado") + " (mín. 18 × 18 mm)") if pic else
                  "Clase " + "/".join(c for c in cls if c in "DK") + ": símbolo según norma del producto",
                  "3534 2.2.3"))
    filas.append(("1", "Instrucciones", "1 RETIRE EL PASADOR (ROMPE EL PRECINTO) · 2 APUNTE A LA BASE DEL FUEGO · "
                  "3 APRIETE LA MANIJA" + (f" · INICIE LA DESCARGA A {alc} m DEL FUEGO" if alc else ""),
                  "3534 2.2.4"))
    from .bom import PROPIOS
    filas.append(("2", "Fabricante", "FLAMA S.A. (marca registrada) y domicilio" if m.codigo in PROPIOS else
                  "MARCA DEL FABRICANTE CERTIFICADO · COMERCIALIZA FLAMA S.A.", "3534 2.2.1 2°"))
    tipo = {"3523": "MATAFUEGO A POLVO BAJO PRESIÓN", "3550": "MATAFUEGO DE POLVO BAJO PRESIÓN",
            "3504": "MATAFUEGO A BASE DE AGENTE LIMPIO BAJO PRESIÓN"}.get(n_ext, f"MATAFUEGO DE {m.agente.upper()}")
    filas.append(("3", "a) Tipo", tipo, f"{n_ext} 5.2.4 / 3534 2.2.1 3° a"))
    filas.append(("3", "b) Capacidad", m.capacidad.replace(" Ø3", "").replace(".", ","), "3534 3° b"))
    if m.familia != "co2":
        filas.append(("3", "c) Presión de servicio", _mpa(s["Presión de servicio (MPa)"]) + " a 20 °C", "3534 3° c"))
    filas.append(("3", "d) Presión de ensayo hidrostático", _mpa(s["Presión de ensayo (MPa)"]), "3534 3° d"))
    filas.append(("3", "e) Inspección y mantenimiento", "CONTROL PERIÓDICO, MANTENIMIENTO Y RECARGA SEGÚN IRAM 3517-2",
                  "3534 3° e"))
    filas.append(("3", "f) Leyenda", "EL MATAFUEGO DEBE SER INSTALADO Y MANTENIDO SEGÚN LA NORMA IRAM 3517", "3534 3° f"))
    filas.append(("3", "g) Leyenda", "RECARGAR INMEDIATAMENTE DESPUÉS DE CUALQUIER USO", "3534 3° g"))
    filas.append(("3", "h) Temperaturas", f"APTO DE {s['Rango temperatura (°C)']} °C", "3534 3° h"))
    pot = ag["potencial"] if ag["potencial"] != "-" else "(según ensayo de tipo IRAM 3542/3543)"
    filas.append(("3", "i) Potencial extintor", f"{pot} + ADVERTENCIA: EL POTENCIAL SE GARANTIZA SÓLO EN LAS "
                  "CONDICIONES ORIGINALES", "3534 3° i"))
    if n_ext in ("3523", "3550"):
        filas.append(("3", "Fecha", "MES Y AÑO DE FABRICACIÓN (MM/AA)", f"{n_ext} 5.2.4"))
        filas.append(("3", "Número", "N° DE " + ("SERIE" if rod else "RECIPIENTE") + " (igual al estampado)",
                      f"{n_ext} 5.2.4"))
    if n_ext == "3523":
        filas.append(("3", "Leyenda", "EL CONTENIDO DE ESTE MATAFUEGO ESTÁ BAJO PRESIÓN", "3523 5.2.4 j"))
        filas.append(("3", "Gas", "PRESURIZAR ÚNICAMENTE CON NITRÓGENO SECO", "3523 5.2.4 o"))
    if n_ext in ("3523", "3550") and ag["grado"] in AG.GRADOS_ABC:
        filas.append(("3", "Etiqueta del polvo", f"POLVO {ag['grado']} - DEMSA - SELLO IRAM 3569 · ATENCIÓN: RECARGAR "
                      "SÓLO CON POLVO ABC IRAM 3569 · LA MEZCLA DE POLVOS PUEDE ORIGINAR GRAVES INCONVENIENTES",
                      "3523 5.2.4 n · 7.13 e"))
    elif "_BC_" in m.codigo:
        filas.append(("3", "Etiqueta del polvo", "POLVO BC SÓDICO - DEMSA - SELLO IRAM 3566 · ATENCIÓN: NO RECARGAR CON "
                      "POLVO ABC · LA MEZCLA DE POLVOS PUEDE ORIGINAR GRAVES INCONVENIENTES", "3523 5.2.4 n · 7.13 e"))
    elif "CLASED" in m.codigo:
        filas.append(("3", "Etiqueta del polvo", "POLVO CLASE D (NaCl > 90 %) - DEMSA · APLICAR SUAVEMENTE SOBRE EL "
                      "METAL; NO MEZCLAR CON OTROS POLVOS", "3523 7.13 e"))
    if n_ext == "3504":
        filas.append(("1", "Leyendas 3504", "PRECAUCIÓN AL USAR EN ESPACIOS CERRADOS · NO USAR EN ESPACIOS CONFINADOS · "
                      "EL CONTENIDO ESTÁ BAJO PRESIÓN", "3504 6.2.2 a-c"))
        filas.append(("3", "Gas", "PRESURIZAR ÚNICAMENTE CON EL GAS INDICADO EN IRAM 3526 (ARGÓN)", "3504 6.2.2"))
    filas.append(("3", "Sello IRAM", "SELLO IRAM DE CONFORMIDAD (versión placa, DC-P-XXXX) si el fabricante es licenciatario",
                  f"{n_ext} 5.2.4 · Anexo R"))
    if n_ext not in PROPIOS_ROT and n_ext != "3504":
        filas.append(("-", "Nota", f"Producto revendido: placa provista por el fabricante certificado (IRAM {n_ext}); "
                      "FLAMA verifica estos campos en recepción", "IRAM 3534"))
    return filas


# ------------------------------------------------------------------ dibujo de símbolos
def _poly(h, pts, capa="01-VISIBLE"):
    h.msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": capa})


def simbolo(h, letra, c, alto):
    """Símbolo de clase IRAM 3534 fig. 1 centrado en c, de `alto` mm de papel."""
    x, y = c
    if letra == "A":
        ln = alto / math.sin(math.radians(60))
        _poly(h, [(x - ln / 2, y - alto / 2), (x + ln / 2, y - alto / 2), (x, y + alto / 2)])
        _poly(h, [(x - ln / 2 * 0.8, y - alto / 2 * 0.85), (x + ln / 2 * 0.8, y - alto / 2 * 0.85), (x, y + alto / 2 * 0.65)])
        h.texto("A", (x, y - alto * 0.12), alto * 0.42, A.MIDDLE_CENTER)
    elif letra == "B":
        for k in (1.0, 0.84):
            a = alto / 2 * k
            _poly(h, [(x - a, y - a), (x + a, y - a), (x + a, y + a), (x - a, y + a)])
        h.texto("B", (x, y), alto * 0.5, A.MIDDLE_CENTER)
    elif letra == "C":
        for k in (1.0, 0.86):
            h.msp.add_circle((x, y), alto / 2 * k, dxfattribs={"layer": "01-VISIBLE"})
        h.texto("C", (x, y), alto * 0.5, A.MIDDLE_CENTER)
    elif letra == "D":
        pts = []
        for i in range(10):
            r = alto / 2 if i % 2 == 0 else alto / 2 * 0.5
            a = math.radians(90 + 36 * i)
            pts.append((x + r * math.cos(a), y + r * math.sin(a)))
        _poly(h, pts)
        h.texto("D", (x, y), alto * 0.38, A.MIDDLE_CENTER)
    elif letra == "K":
        a = alto / 2
        _poly(h, [(x - a, y - a), (x + a, y - a), (x + a, y + a), (x - a, y + a)])
        h.texto("K", (x, y), alto * 0.5, A.MIDDLE_CENTER)


def pictograma(h, c, lado, fuego, apto):
    x, y = c
    a = lado / 2
    _poly(h, [(x - a, y - a), (x + a, y - a), (x + a, y + a), (x - a, y + a)])
    h.texto({"A": "sólido", "B": "líquido", "C": "eléctrico"}[fuego], (x, y), max(1.2, lado * 0.16), A.MIDDLE_CENTER)
    if not apto:
        h.linea((x - a, y + a), (x + a, y - a), "01-VISIBLE")


def _texto_ajustado(h, txt, x, y, w, alto):
    """Escribe `txt` envuelto al ancho w (mm de papel); devuelve la y siguiente."""
    por_linea = max(8, int(w / (alto * 0.82)))
    for ln in textwrap.wrap(txt, por_linea):
        h.texto(ln, (x, y), alto, A.TOP_LEFT)
        y -= alto * 1.45
    return y


# ------------------------------------------------------------------ placa desarrollada
INSTR = ("1 RETIRE EL PASADOR", "2 APUNTE A LA BASE DEL FUEGO", "3 APRIETE LA MANIJA")
CW = 0.86          # ancho medio de carácter / altura (letra tipo B IRAM 4503 en mayúsculas)


def disposicion(m, W):
    """Medidas reales de la placa de ancho W (arco 108°): letras según IRAM 3534 2.2.4.3, símbolos 12 mm mín.,
    pictogramas 18 mm mín.; devuelve el alto necesario para todo el contenido obligatorio."""
    masa = float(m.spec["Peso cargado (kg)"].replace(",", "."))
    lo, hi = (3.0, 8.0) if masa < 9 else (6.5, 10.0)
    hl = max(lo, min(hi, (W - 6) / (CW * max(len(t) for t in INSTR))))
    ht = 1.8 if masa < 9 else 2.5                     # otras indicaciones: serie IRAM 4503
    ncls = len(clases(m))
    pic = pictogramas(m)
    sym = max(12.0, min(24.0, (W - 6) / 6.5))
    pz = max(18.0, min(28.0, (W - 6) / 4.2))
    dos_filas = pic is not None and ncls * sym * 1.25 + 3 * pz * 1.1 > W - 6
    instr = [p for ln in INSTR for p in textwrap.wrap(ln, max(6, int((W - 6) / (CW * hl))))]
    datos = [d for f in contenido(m) if f[0] == "3" for d in textwrap.wrap(f[2], max(8, int((W - 6) / (CW * ht))))]
    z1 = 5 + max(sym, 0 if dos_filas or pic is None else pz) + (pz + 3 if dos_filas else 0) + 3 + len(instr) * hl * 1.5 + 2
    z2 = hl * 1.8
    z3 = 6 + len(datos) * ht * 1.45 + 3
    return dict(hl=hl, ht=ht, sym=sym, pz=pz, dos_filas=dos_filas, instr=instr, datos=datos,
                z1=z1, z2=z2, z3=z3, H=z1 + z2 + z3, rango=(lo, hi))


def placa(h, m, zona, W, H):
    """Dibuja la placa desarrollada (W × H mm reales) dentro de zona (x0, y0, x1, y1) a la mayor escala normal."""
    d = disposicion(m, W)
    x0, y0, x1, y1 = zona
    esc = next(s for s in (1.0, 0.5, 0.4, 0.2, 0.1) if W * s <= x1 - x0 - 16 and H * s <= y1 - y0 - 18)
    w, hh = W * esc, H * esc
    ox, oy = (x0 + x1) / 2 - w / 2, (y0 + y1 - 10) / 2 - hh / 2
    h.rect(ox, oy, ox + w, oy + hh, "01-VISIBLE")
    h.texto(f"R1 PLACA DE CARACTERÍSTICAS DESARROLLADA {_n(W, 0)} × {_n(H, 0)} mm (arco 108°) - "
            f"ESC. {'1:1' if esc == 1 else '1:' + _n(1 / esc, 1)}", ((x0 + x1) / 2, y1 - 3), 3.5, A.MIDDLE_CENTER)
    top = oy + hh
    z1 = top - d["z1"] * esc
    z2 = z1 - d["z2"] * esc
    h.linea((ox, z1), (ox + w, z1), "08-FINA")
    h.linea((ox, z2), (ox + w, z2), "08-FINA")
    h.texto("ZONA 1 PROMINENTE", (ox + 1, top - 1), 1.5, A.TOP_LEFT, "08-FINA")
    sym, pz = d["sym"] * esc, d["pz"] * esc
    fila = top - 5 * esc - max(sym, pz if not d["dos_filas"] else 0) / 2
    xx = ox + 3 * esc + sym / 2
    for c in clases(m):
        simbolo(h, c, (xx, fila), sym)
        xx += sym * 1.25
    pic = pictogramas(m)
    if pic:
        if d["dos_filas"]:
            fila = fila - sym / 2 - 3 * esc - pz / 2
            xp = ox + 3 * esc + pz / 2
        else:
            xp = ox + w - 3 * esc - pz / 2 - 2 * pz * 1.1
        for f, ok in zip("ABC", pic):
            pictograma(h, (xp, fila), pz, f, ok)
            xp += pz * 1.1
        base = fila - pz / 2
    else:
        base = fila - sym / 2
    yi = base - 3 * esc
    for ln in d["instr"]:
        h.texto(ln, (ox + 3 * esc, yi), d["hl"] * esc, A.TOP_LEFT)
        yi -= d["hl"] * esc * 1.5
    from .bom import PROPIOS
    h.texto("FLAMA S.A." if m.codigo in PROPIOS else "FABRICANTE / COMERCIALIZA FLAMA S.A.",
            (ox + w / 2, (z1 + z2) / 2), d["hl"] * esc * (0.9 if m.codigo in PROPIOS else 0.4), A.MIDDLE_CENTER)
    h.texto("ZONA 3 NO PROMINENTE", (ox + 1, z2 - 1), 1.5, A.TOP_LEFT, "08-FINA")
    y = z2 - max(5 * esc, 3.4)
    for ln in d["datos"]:
        h.texto(ln, (ox + 3 * esc, y), d["ht"] * esc, A.TOP_LEFT)
        y -= d["ht"] * esc * 1.45
    h.cota_lineal((ox, oy), (ox + w, oy), (ox, oy - 7), 0, 1 / esc)
    h.cota_lineal((ox + w, oy), (ox + w, oy + hh), (ox + w + 7, oy), 90, 1 / esc)
    h.cota_lineal((ox, z2), (ox, top), (ox - 7, z2), 90, 1 / esc)
    return esc, d["hl"]


# ------------------------------------------------------------------ hoja 4
def hoja4(m, piezas, info, proy, doc, ox):
    from .bom import PROPIOS
    rev = m.codigo not in PROPIOS
    h = Hoja(doc, "A2", ox)
    h.formato()
    r = rotulo_base(m, "A2", None, 4, "Rotulado e identificación", "Placa, sellos, oblea, precinto y marcado")
    h.rotulo(r)
    X0, Y0, X1, Y1 = h.fx0, h.fy0, h.fx1, h.fy1
    h.texto(f"ROTULADO E IDENTIFICACIÓN - {m.nombre.upper()}", ((X0 + X1) / 2, Y1 - 7), 5, A.MIDDLE_CENTER)
    if rev:
        h.texto("PRODUCTO REVENDIDO: placa, estampado y precinto los aplica el fabricante certificado; esta hoja es la "
                "especificación de RECEPCIÓN de FLAMA (lo que el equipo debe traer).", ((X0 + X1) / 2, Y1 - 12.5), 2.5,
                A.MIDDLE_CENTER)
    W, H, z0, R, xc, yc = M.placa_dim(m, piezas)
    # R1 placa
    esc, hl = placa(h, m, (X0 + 8, Y0 + 195, X0 + 290, Y1 - 14), W, H)
    # R2 ubicación (vista anterior)
    ex = V.extension(proy["anterior"]["vis"])
    zx0, zy0, zx1, zy1 = X0 + 300, Y0 + 195, X0 + 430, Y1 - 14
    f = min((zx1 - zx0 - 30) / (ex[2] - ex[0]), (zy1 - zy0 - 22) / (ex[3] - ex[1]))
    f = next(s for s in (1 / 2, 1 / 5, 1 / 10, 1 / 20) if s <= f)
    Tx = (zx0 + zx1) / 2 - (ex[0] + ex[2]) / 2 * f
    Ty = zy0 + 24 - ex[1] * f
    h.prims(proy["anterior"]["vis"], "01-VISIBLE", (Tx, Ty, f))
    cuerda = 2 * R * math.sin(math.radians(54))
    poly = sg.box(Tx + (xc - cuerda / 2) * f, Ty + z0 * f, Tx + (xc + cuerda / 2) * f, Ty + (z0 + H) * f)
    h.rayado(poly, 45, 1.5)
    zo = z0 - 3 - M.OBLEA_PBA
    h.cota_lineal((Tx + (xc + cuerda / 2) * f, Ty), (Tx + (xc + cuerda / 2) * f, Ty + z0 * f),
                  (Tx + (xc + R) * f + 10, Ty), 90, 1 / f)
    h.cota_lineal((Tx + (xc + cuerda / 2) * f, Ty + z0 * f), (Tx + (xc + cuerda / 2) * f, Ty + (z0 + H) * f),
                  (Tx + (xc + R) * f + 10, Ty), 90, 1 / f)
    h.cota_lineal((Tx + (xc - cuerda / 2) * f, Ty + z0 * f), (Tx + (xc + cuerda / 2) * f, Ty + z0 * f),
                  (Tx, Ty - 8), 0, 1 / f)
    h.texto(f"cuerda {_n(cuerda, 0)} = arco 108° de {_n(W, 0)} mm desarrollados", ((zx0 + zx1) / 2, Ty - 14), 1.8,
            A.MIDDLE_CENTER)
    h.nota_referencia("Oblea PBA Ø46", (Tx + xc * f, Ty + (zo + M.OBLEA_PBA / 2) * f),
                      (Tx + (xc - R) * f - 14, Ty + (zo - 10) * f), 2.2)
    h.eje((Tx + xc * f, Ty - 3), (Tx + xc * f, Ty + (z0 + H) * f + 3))
    h.texto("R2 UBICACIÓN (vista anterior, esc. 1:" + _n(1 / f, 0) + ")", ((zx0 + zx1) / 2, zy1 - 3), 3.5,
            A.MIDDLE_CENTER)
    h.texto("Placa sobre el eje del manómetro, de frente; oblea inmediatamente debajo, sin otra identificación entre "
            "ambas (Res. 522/07 an. 6)", ((zx0 + zx1) / 2, zy0 + 3), 1.8, A.MIDDLE_CENTER)
    # R3 símbolos acotados
    sx0, sy0, sx1, sy1 = X0 + 436, Y0 + 290, X1 - 4, Y1 - 14
    h.texto("R3 SÍMBOLOS Y PICTOGRAMAS (IRAM 3534)", ((sx0 + sx1) / 2, sy1 - 3), 2.8, A.MIDDLE_CENTER)
    cls = clases(m)
    xs = sx0 + 14
    for c in cls:
        simbolo(h, c, (xs, sy1 - 26), 14)
        h.texto({"A": "verde 01-1-150", "B": "rojo 03-1-050", "C": "azul 08-1-070", "D": "amarillo 05-1-040",
                 "K": "IRAM 3694"}[c], (xs, sy1 - 38), 1.8, A.MIDDLE_CENTER)
        xs += 26
    h.texto("Alto mín. 12 mm; trazo e = alto/13 (A), alto/12 (B, D), alto/14 (C)", (sx0 + 2, sy1 - 46), 1.8)
    pic = pictogramas(m)
    if pic:
        xs = sx0 + 14
        for fz, ok in zip("ABC", pic):
            pictograma(h, (xs, sy0 + 22), 18, fz, ok)
            xs += 24
        h.texto("Pictogramas mín. 18 × 18 mm; tachado = no apto", (sx0 + 2, sy0 + 8), 1.8)
    else:
        h.texto("Clases D/K: símbolo del producto (IRAM 3534 no prevé pictograma)", (sx0 + 2, sy0 + 20), 1.8)
    # R4 oblea PBA
    ox_, oy_ = X0 + 436, Y0 + 195
    h.texto("R4 OBLEA FABRICACIÓN PBA (Res. 522/07)", ((ox_ + X1 - 4) / 2, oy_ + 90), 2.8, A.MIDDLE_CENTER)
    c4 = (ox_ + 30, oy_ + 45)
    for rr in (23, 17):
        h.msp.add_circle(c4, rr, dxfattribs={"layer": "01-VISIBLE"})
    h.texto("PRÓXIMA REVISIÓN", (c4[0], c4[1] + 6), 1.6, A.MIDDLE_CENTER)
    h.texto("DE CARGA", (c4[0], c4[1] + 3.5), 1.6, A.MIDDLE_CENTER)
    h.texto("A0000001", (c4[0], c4[1] - 4), 2.2, A.MIDDLE_CENTER)
    h.cota_lineal((c4[0] - 23, c4[1] - 25), (c4[0] + 23, c4[1] - 25), (c4[0] - 23, c4[1] - 30), 0, 1, prefijo="%%c")
    for i, t in enumerate(["Autoadhesiva, autodestructible (troquel", "magnético), fondo guilloche, imagen latente",
                           "«válido», numerada; textos negros.", "Ubicación: frente, eje del manómetro,",
                           "inmediatamente debajo de la placa.", "Campo «próxima revisión» completado.",
                           "Rige para venta en Prov. de Bs. As."]):
        h.texto(t, (ox_ + 57, oy_ + 70 - 5 * i), 1.6)
    # R5 estampilla IRAM
    ex_, ey_ = X0 + 385, Y0 + 125
    ew, eh = M.ESTAMPILLA_IRAM
    h.texto("R5 ESTAMPILLA IRAM EXTINTOR NUEVO", (ex_ + 42, ey_ + 66), 2.8, A.MIDDLE_CENTER)
    sx, sy = ex_ + 10, ey_ + 12
    h.rect(sx, sy, sx + ew, sy + eh, "01-VISIBLE")
    h.rect(sx, sy, sx + 8, sy + eh, "08-FINA")
    h.texto("A 26 000000", (sx + 4, sy + eh / 2), 2.2, A.MIDDLE_CENTER, rot=90)
    h.texto("leyenda de conformidad", (sx + 10, sy + eh - 4), 1.6)
    h.texto("y advertencia", (sx + 10, sy + eh - 7), 1.6)
    h.msp.add_circle((sx + ew - 11, sy + eh - 11), 8, dxfattribs={"layer": "08-FINA"})
    h.texto("logo", (sx + ew - 11, sy + eh - 11), 1.6, A.MIDDLE_CENTER)
    h.rect(sx + ew - 18, sy + 2, sx + ew - 4, sy + 16, "08-FINA")
    h.texto("QR", (sx + ew - 11, sy + 9), 1.6, A.MIDDLE_CENTER)
    h.texto(f"≈ {_n(ew, 0)} × {_n(eh, 0)} (proporción del Anexo R; medida exacta = estampilla", (ex_ + 2, ey_ + 7), 1.6)
    h.texto("provista por IRAM). N° identifica extintor y fabricante. Sólo licenciatarios.", (ex_ + 2, ey_ + 4), 1.6)
    # R6 precinto de fábrica
    px, py = X0 + 472, Y0 + 125
    h.texto("R6 PRECINTO DE FÁBRICA", (px + 42, py + 66), 2.8, A.MIDDLE_CENTER)
    fab = "del fabricante" if rev else "FLAMA"
    h.msp.add_circle((px + 22, py + 38), 15, dxfattribs={"layer": "01-VISIBLE"})
    h.linea((px + 37, py + 38), (px + 78, py + 38), "01-VISIBLE")
    h.rect(px + 54, py + 33, px + 66, py + 43, "01-VISIBLE")
    h.texto("FAB." if rev else "FLAMA", (px + 60, py + 39.5), 1.5, A.MIDDLE_CENTER)
    h.texto("L 0000", (px + 60, py + 36), 1.5, A.MIDDLE_CENTER)
    for i, t in enumerate(["Pasador alambre Ø 2,5-3,5 con ojal que deja pasar", "un cilindro Ø 30; precinto que se rompe al tirar",
                           f"(IRAM 3517-2 9.4.13). En el nuevo lleva la id. {fab}", "y el lote (IRAM 3523 3.3.2): su",
                           "integridad indica que el equipo no fue accionado."]):
        h.texto(t, (px + 2, py + 18 - 4 * i), 1.6)
    # R7 marcado estampado
    mx, my = X0 + 385, Y0 + 61
    h.texto("R7 MARCADO GRABADO DEL RECIPIENTE", (mx + 42, my + 58), 2.8, A.MIDDLE_CENTER)
    n_ext = m.spec["Norma IRAM extintor"]
    if rev:
        h.rect(mx + 3, my + 34, mx + 82, my + 46, "08-FINA")
        h.texto("FABRICANTE  N° SERIE  AÑO", (mx + 42.5, my + 40), 2.8, A.MIDDLE_CENTER)
        ref = ("IRAM 2533 (cilindro de CO₂ sin costura: estampado del fabricante del cilindro)" if m.familia == "co2"
               else f"IRAM {n_ext} (norma del producto, aplicado por el fabricante)")
        for i, t in enumerate(["Grabado por el fabricante del equipo según", ref[:62], ref[62:],
                               "FLAMA verifica que exista y coincida con la placa."]):
            h.texto(t, (mx + 3, my + 28 - 4.5 * i), 1.6)
        mx = None
    txt = ("FLAMA S.A.  N° 000001  " + ("PH " + m.spec["Presión de ensayo (MPa)"] + " MPa  " if n_ext == "3550" else "")
           + "26")
    for i, t in enumerate([] if mx is None else [("Fabricante, n° de " + ("serie, presión de ensayo" if n_ext == "3550" else "recipiente") +
                            " y año (2 dígitos)" + (" - IRAM 3550 5.1" if n_ext == "3550" else " - IRAM 3523 5.1")),
                           "Grabado legible e indeleble sobre el recipiente o accesorio fijo;",
                           "FLAMA: estampado en la cúpula junto al cuello, letra 5 mm (IRAM 4503).",
                           "Últimos 3 meses del año: puede marcarse con el año siguiente."]):
        h.texto(t, (mx + 3, my + 28 - 4.5 * i), 1.6)
    if mx is not None:
        h.rect(mx + 3, my + 34, mx + 82, my + 46, "01-VISIBLE")
        h.texto(txt, (mx + 42.5, my + 40), 2.8, A.MIDDLE_CENTER)
    # R8 tarjeta CABA
    tx, ty = X0 + 472, Y0 + 61
    h.texto("R8 TARJETA OFICIAL (CABA)", (tx + 42, ty + 58), 2.8, A.MIDDLE_CENTER)
    h.rect(tx + 6, ty + 18, tx + 80, ty + 50, "01-VISIBLE")
    for i, t in enumerate(["Clase:", "Capacidad:", "Fecha de carga:", "Vencimiento:", "Garantía empresa:"]):
        h.texto(t, (tx + 9, ty + 46 - 6 * i), 1.8)
    h.texto("Ordenanza 40.473 art. 6: adquirida en DG Rentas, se anexa", (tx + 2, ty + 12), 1.6)
    h.texto("a cada matafuego (colgada del cuello; no se dibuja).", (tx + 2, ty + 8.5), 1.6)
    # tabla de contenido
    filas = [("Zona", "Ítem", "Texto / dato de la placa", "Referencia")]
    for z, it, t, ref in contenido(m):
        filas.append((z, it, t[:150], ref))
    alto = min(4.6, 178 / (len(filas) + 1))
    _tabla(h, X0 + 6, Y0 + 186, filas, [10, 44, 238, 60], alto=alto, hs=(2.0, 2.0, 1.8, 1.8),
           encabezado="CONTENIDO OBLIGATORIO DE LA PLACA DE CARACTERÍSTICAS")
    h.texto(f"Letra de instrucciones {_n(hl, 1)} mm (IRAM 3534 2.2.4.3: masa total "
            f"{'< 9 kg: 3-8 mm' if float(m.spec['Peso cargado (kg)'].replace(',', '.')) < 9 else '≥ 9 kg: 6,5-10 mm'}); "
            "mayúsculas IRAM 4503, color en contraste. Placa autoadhesiva ensayada a adherencia ≥ 0,35 N/mm y abrasión "
            "100 pasadas (IRAM 3534 cap. 3).", (X0 + 6, Y0 + 4), 1.8)
    return h
