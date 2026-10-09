"""Verificación del plano contra la norma IRAM de producto (hoja 3).

Cada fila: (cláusula, requisito resumido, valor del plano, estado). Los requisitos se citan por cláusula y se
resumen con palabras propias (no se transcribe la norma). Normas de producto consultadas: IRAM 3525 (agua),
IRAM 3509 (CO2), IRAM 3550 (polvo sobre ruedas). IRAM 3523 (polvo manual), 3527 (AFFF), 3504 (HCFC) y 3694 (clase K)
no están en la carpeta de normas: para esos equipos se verifican por analogía los requisitos constructivos
equivalentes de IRAM 3525 y se indica «(analogía)».
"""

import math

OK, VER, NA = "cumple", "verificar", "no aplica"


def _n(v, d=1):
    s = f"{v:.{d}f}"
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s.replace(".", ",")


def largo_manga(piezas):
    """largo desarrollado de la manga (eje del tubo) + terminales, en mm."""
    if "manguera" not in piezas:
        return None
    bb = piezas["manguera"].BoundingBox()
    r = min(bb.xlen, bb.ylen, 16.0) / 2
    largo = piezas["manguera"].Volume() / (math.pi * r * r) if r > 0 else 0
    for k in ("tobera", "lanza", "difusor"):
        if k in piezas:
            largo += piezas[k].BoundingBox().zlen
    return largo


def norma_base(m):
    """(norma usada, directa?) para la verificación del modelo."""
    n = m.spec.get("Norma IRAM extintor", "")
    if m.familia == "co2":
        return "3509", True
    if m.familia == "rodante":
        return "3550", n == "3550"
    if n == "3525":
        return "3525", True
    return "3525", False


def filas(m, info, piezas):
    g = m.geo
    norma, directa = norma_base(m)
    an = "" if directa else " (analogía)"
    rec = info["recipiente"]
    t = g["t"]
    out = []
    if m.familia == "co2":
        out += [
            ("3509 3.2.1", "válvula manual con disco de seguridad, tubo de pesca y precinto", "disco de rotura, sifón, "
             "pasador con precinto", OK),
            ("3509 3.2.3", "tubo de pesca metálico, resistente a la corrosión", "tubo de aluminio", OK),
            ("3509 3.3", "más de 3,5 kg: manga flexible con uniones no ferrosas o inox.",
             "manga alta presión, racores de latón" if "manguera" in piezas else "≤ 3,5 kg: brazo giratorio",
             OK),
            ("3509 3.4", "más de 3,5 kg: manguito aislante del frío en la manga",
             "empuñadura de PP" if "empunadura" in piezas else "no lleva (≤ 3,5 kg)", OK),
            ("3509 3.5", "tobera de material dieléctrico, resistente a la humedad", "bocina de polietileno AD", OK),
            ("3509 3.7", "más de 1 kg: manija de transporte", "manija fija de la válvula", OK),
            ("3509 3.8", "más de 3,5 kg: medio de apoyo en el piso", "pie de polietileno AD" if "pie" in piezas
             else "sin pie", OK if ("pie" in piezas or float(m.capacidad.split()[0]) <= 3.5) else VER),
            ("3509 4.1", "cilindro según IRAM 2533", "cilindro sin costura comprado con sello", VER),
        ]
        return f"IRAM 3509 (CO₂ manual)", out
    if m.familia == "rodante":
        D = 2 * g["R"]
        e_min = 2.9 if D <= 320 else 4.5
        out += [
            ("3550 4.1.3.2", f"espesor de chapa ≥ {_n(e_min)} mm (Ø {'≤' if D <= 320 else '>'} 320)",
             f"{_n(t, 2)} mm, Ø{_n(D, 0)}", OK if t >= e_min else VER),
            ("3550 4.8.2", "tabla III: rueda Ø ≥ 300, banda ≥ 50, trocha ≥ 400",
             f"Ø{m.spec.get('Diámetro de rueda (mm)')}, banda {_n(info['bw_w'], 0)}, trocha {_n(info['track'], 0)}",
             OK if info["bw_w"] >= 50 and info["track"] >= 400 else VER),
            ("3550 3.12.1", "ruedas metálicas, con caucho o cubierta neumática", "llanta de chapa + caucho / neumático",
             OK),
            ("3550 3.4.2", "traba con precinto", "pasador Ø3,2 con anilla y precinto", OK),
            ("3550 3.8.1", "manga de una sola pieza", f"{m.spec.get('Longitud de manga (m)', '-')} m, una pieza", OK),
            ("3550 3.8.2", "soporte firme para la manga", "2 ganchos soldados al cuerpo", OK),
            ("3550 3.12.3", "estable y manejable por un operador", "3 apoyos: 2 ruedas + pata; manija", OK),
            ("3550 6.1.1", "tren rodante soldado antes de formar el lote", "soldado antes de la PH (puesto C)", OK),
        ]
        return f"IRAM 3550 (sobre ruedas){an}", out
    # manuales
    inox = m.familia == "inox"
    e_min = 0.63 if inox else 0.71
    out += [
        (f"3525 3.2.1{' b' if inox else ' a'}", f"chapa {'inox.' if inox else 'de acero'} ≥ {_n(e_min, 2)} mm",
         f"{_n(t, 2)} mm", OK if t >= e_min else VER),
        ("3525 3.2.2.1", "como máximo 1 costura longitudinal y 2 transversales",
         ("1 longitudinal (caño con costura)" if m.capacidad == "1 kg" else "1 longitudinal") + " + 2 transversales", OK),
        ("3525 3.3.2", "traba con precinto identificado", "pasador con anilla y precinto FLAMA", OK),
        ("3525 4.1.3", "boca roscada con Ø interior ≥ 19 mm", f"{g['cuello'][2]} (Ø int. {_n(rec['bore'], 1)})",
         OK if rec["bore"] >= 19 else VER),
        ("3525 3.9", "manija para el transporte manual", "manija fija de la válvula", OK),
    ]
    lm = largo_manga(piezas)
    if lm is None:
        out.append(("3525 4.2.1", "manga ≥ 350 mm con el terminal", "sin manga: tobera directa (1 kg)", NA))
    else:
        out.append(("3525 4.2.1", "manga ≥ 350 mm con el terminal", f"≈ {_n(lm, 0)} mm", OK if lm >= 350 else VER))
        out.append(("3525 3.10", "soporte firme para la manga", "suncho portatobera", OK))
    if inox:
        out.append(("3525 3.6.1", "filtro en la entrada del tubo interior", "filtro PP perforado", OK))
        out.append(("3525 3.3.5", "partes en contacto con el agua no ferrosas o inox.", "latón, inox. AISI 302/304",
                    OK))
    return f"IRAM {'3525 (agua manual)' if directa else '3525 por analogía'}", out
