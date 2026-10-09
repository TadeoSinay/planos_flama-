"""Hoja 4 de cada plano FL_MAT: rotulado e identificación del extintor nuevo.

Fuentes (se citan apartados, no se transcriben las normas):
  IRAM 3534:1983 placas de características: contenido 2.2.1 (1° prominente: símbolos/pictogramas e
      instrucciones; 2° marca del fabricante; 3° datos a-i), símbolos fig. 1 (mín. 12 mm), colores 2.2.2.3,
      pictogramas 2.2.3 (mín. 18 mm), letras 2.2.4.3 (altura según masa total, proporciones fig. 2,
      longitud máxima de las instrucciones: arco de 108°), ensayos de adherencia y abrasión (cap. 3 y 5).
  IRAM 3523:1983 cap. 5 (polvo manual): marcado del recipiente 5.1, leyendas propias 5.2.4 (tipo, contenido
      bajo presión, mes/año, n° de recipiente, etiqueta del polvo n, nitrógeno seco o, Sello IRAM p), 7.13 e).
  IRAM 3550:1981 cap. 5 (polvo sobre ruedas): marcado 5.1 (incluye presión de ensayo), leyendas 5.2.4.
  IRAM 3504:2001 cap. 6 (gases limpios): leyendas de uso en espacios cerrados y gas según IRAM 3526.
  IRAM Anexo R (DC-PG-129 rev. 12, 2025): estampilla de conformidad de extintor nuevo, provista por IRAM.
  Res. OPDS 522/07 anexos 1, 2 y 6 (Provincia de Buenos Aires): oblea de fabricación Ø 46.
  Ordenanza 40.473 art. 6 (CABA): tarjeta oficial; formato actual relevado = etiqueta autoadhesiva AGC.
  IRAM 3517-2:2020 9.4.13: traba y precinto (identificación del fabricante y del lote).

Relevamiento de mercado (fotos de equipos instalados y de la línea de etiquetado, 2026: Georgia, Melisam,
Fadesa, Horizonte, De León, Maxiseguridad; recargadores Suyai y Firegram). Lo que la norma deja abierto se
resolvió como lo resuelve el mercado:
  * La etiqueta envuelve ≈ 200-230°: panel central con instrucciones (≤ 108°, IRAM 3534) y dos alas laterales
    con DATOS TÉCNICOS (izq.) y MANTENIMIENTO / ATENCIÓN (der.) en letra menor.
  * Encabezado marca + leyenda de tipo; instrucciones en 3 pasos numerados con ilustración ("ROMPA EL
    PRECINTO / QUITE EL SEGURO", "COLÓQUESE A 3 m" — 1,5 m en 1 kg —, "ACCIONE LA PALANCA Y DIRIJA EL
    CHORRO A LA BASE DEL FUEGO"); fila "PARA FUEGOS CLASE" con símbolo + pictograma por clase; logos de
    Sello IRAM, OPDS, GCBA y DPS; pie con registros (Ord. 40.473, OPDS, C.H.A.S.) e "INDUSTRIA ARGENTINA".
  * Debajo de la etiqueta: estampilla IRAM (rosa, guilloche, n° vertical "A 25 1111053", logo y QR) y oblea
    PBA; tarjeta AGC autoadhesiva con QR; etiqueta de serie GS1 (QR "(01)779…") en el costado; faja de
    garantía rayada roja/blanca "la rotura total de esta cinta interrumpe la garantía" y precinto plástico
    de color con el nombre del fabricante o recargador en la traba.
"""

import math
import textwrap

import shapely.geometry as sg

from . import modelo3d as M
from . import vistas as V
from . import agentes as AG
from .lamina import Hoja, A, partir
from .planos import _tabla, rotulo_base

PROPIOS_ROT = {"3523", "3550"}     # extintores que fabrica FLAMA: placa diseñada por FLAMA
MERCADO = "mercado (fotos Georgia/Melisam/Fadesa)"
CW = 0.95          # ancho de carácter / altura medido en el PDF (mayúsculas IRAM 4503) + margen


def _n(v, d=1):
    s = f"{v:.{d}f}".replace(".", ",")
    return s.rstrip("0").rstrip(",") if "," in s else s


def _propio(m):
    from .bom import PROPIOS
    return m.codigo in PROPIOS


def clases(m):
    if m.codigo.startswith("FL_MAT_ABC") or "HCFC" in m.codigo:
        return ["A", "B", "C"]
    if "_BC_" in m.codigo or "CO2" in m.codigo:
        return ["B", "C"]
    if "CLASED" in m.codigo:
        return ["D"]
    if "AFFF" in m.codigo:
        return ["A", "B"]
    if "SALESK" in m.codigo:
        return ["A", "K"]
    return ["A"]


def pictogramas(m):
    """IRAM 3534 2.2.3: (fuego A, fuego B, fuego C) -> True apto / False tachado; None si la norma no lo prevé."""
    c = clases(m)
    if "D" in c or "K" in c:
        return None
    return [x in c for x in ("A", "B", "C")]


def _mpa(v):
    return f"{_n(float(v.replace(',', '.')), 1)} MPa ({_n(float(v.replace(',', '.')) * 1000, 0)} kPa)"


def _masa(m):
    return float(m.spec["Peso cargado (kg)"].replace(",", "."))


# ------------------------------------------------------------------ textos de la etiqueta
def tipo(m):
    n_ext = m.spec["Norma IRAM extintor"]
    return {"3523": "MATAFUEGO A POLVO BAJO PRESIÓN", "3550": "MATAFUEGO DE POLVO BAJO PRESIÓN SOBRE RUEDAS",
            "3504": "MATAFUEGO A BASE DE AGENTE LIMPIO BAJO PRESIÓN", "3509": "MATAFUEGO DE DIÓXIDO DE CARBONO",
            "3525": "MATAFUEGO DE AGUA BAJO PRESIÓN", "3527": "MATAFUEGO DE ESPUMA AFFF BAJO PRESIÓN",
            "3541": "MATAFUEGO DE ESPUMA AFFF SOBRE RUEDAS", "3694": "MATAFUEGO CLASE K BAJO PRESIÓN"
            }.get(n_ext, f"MATAFUEGO DE {m.agente.upper()}")


def distancia(m):
    """Distancia de ataque de la instrucción 2 (IRAM 3534 2.2.1 1°: instrucciones con la distancia).
    Mercado: 3 m en manuales, 1,5 m en 1 kg; se usa la mitad inferior del alcance del catálogo."""
    alc = float(str(m.spec.get("Alcance (m)", "3")).split("/")[0].replace(",", "."))
    if m.familia == "rodante":
        return 5.0
    return 1.5 if alc <= 2 else 3.0


def instrucciones(m):
    d = _n(distancia(m), 1)
    if m.familia == "rodante":
        return [f"1 LLEVE EL CARRO A {d}\u00a0m DEL FUEGO", "2 DESENROLLE TOTALMENTE LA MANGUERA",
                "3 ROMPA EL PRECINTO, QUITE EL SEGURO Y ABRA LA VÁLVULA",
                "4 EMPUÑE LA LANZA Y DIRIJA EL " + ("CHORRO A LA BASE DEL FUEGO" if "ABC" in m.codigo else
                                                   "CHORRO DE ESPUMA CONTRA UNA SUPERFICIE")]
    p1, p2 = "1 ROMPA EL PRECINTO Y QUITE EL SEGURO", f"2 COLÓQUESE A {d}\u00a0m DEL FUEGO"
    if "CO2" in m.codigo:
        return [p1, p2, "3 ACCIONE LA PALANCA Y DIRIJA EL DIFUSOR A LA BASE DEL FUEGO",
                "4 NO TOME EL DIFUSOR CON LA MANO: DESCARGA A -78 °C"]
    if "SALESK" in m.codigo:
        return [p1, p2, "3 ACCIONE LA PALANCA Y APLIQUE EN FORMA DE LLUVIA SOBRE LA SUPERFICIE DEL ACEITE",
                "4 CORTE EL GAS O LA ENERGÍA DEL ARTEFACTO"]
    if "CLASED" in m.codigo:
        return [p1, p2, "3 ACCIONE LA PALANCA Y APLIQUE SUAVEMENTE HASTA CUBRIR TOTALMENTE EL METAL"]
    if "AFFF" in m.codigo:
        return [p1, p2, "3 ACCIONE LA PALANCA Y DIRIJA LA ESPUMA CONTRA UNA SUPERFICIE PARA QUE ESCURRA"]
    return [p1, p2, "3 ACCIONE LA PALANCA Y DIRIJA EL CHORRO A LA BASE DEL FUEGO"]


def electrico(m):
    if "CLASED" in m.codigo:
        return "SÓLO PARA FUEGOS DE METALES COMBUSTIBLES"
    if "C" in clases(m):
        return "APTO PARA FUEGOS EN EQUIPOS ELÉCTRICOS ENERGIZADOS"
    return "NO APTO PARA USAR EN ELECTRICIDAD"


def etiqueta_agente(m):
    ag = AG.agente(m)
    if ag["grado"] in AG.GRADOS_ABC:
        return (f"ESTE MATAFUEGO ESTÁ CARGADO CON POLVO {ag['grado']} ({_n(AG.GRADOS_ABC[ag['grado']]['map'], 0)} % "
                "FOSFATO MONOAMÓNICO) - SELLO IRAM 3569. RECARGAR EXCLUSIVAMENTE CON POLVO ABC IRAM 3569. LA MEZCLA "
                "CON OTROS POLVOS PUEDE ORIGINAR GRAVES INCONVENIENTES")
    if "_BC_" in m.codigo:
        return ("ESTE MATAFUEGO ESTÁ CARGADO CON POLVO BC (BICARBONATO DE SODIO) - SELLO IRAM 3566. NO RECARGAR CON "
                "POLVO ABC: LA MEZCLA DE POLVOS PUEDE ORIGINAR GRAVES INCONVENIENTES")
    if "CLASED" in m.codigo:
        return "CARGADO CON POLVO CLASE D (CLORURO DE SODIO). NO MEZCLAR NI RECARGAR CON OTROS POLVOS"
    if "SALESK" in m.codigo:
        return "CARGADO CON SOLUCIÓN DE ACETATO DE POTASIO (IRAM 3697). RECARGAR SÓLO CON EL MISMO AGENTE"
    if "AFFF" in m.codigo:
        return "CARGADO CON PREMEZCLA AFFF 3 % (IRAM 3515). NO MEZCLAR CON OTROS ESPUMÍGENOS"
    if "HCFC" in m.codigo:
        return "CARGADO CON HCFC-123 MEZCLA B (IRAM 3526-1). RECARGAR SÓLO CON EL MISMO AGENTE (RECUPERAR, NO VENTEAR)"
    return ""


def gas(m):
    n_ext = m.spec["Norma IRAM extintor"]
    if n_ext in ("3523", "3550", "3694"):
        return "PRESURIZAR ÚNICAMENTE CON NITRÓGENO SECO"
    if n_ext == "3504":
        return "PRESURIZAR ÚNICAMENTE CON EL GAS INDICADO EN IRAM 3526 (ARGÓN)"
    if n_ext in ("3525", "3527", "3541"):
        return "PRESURIZAR CON AIRE COMPRIMIDO SECO O NITRÓGENO"
    return ""


def datos(m):
    """Ala izquierda DATOS TÉCNICOS: (ítem, texto, referencia)."""
    s, ag = m.spec, AG.agente(m)
    n_ext = s["Norma IRAM extintor"]
    rod = m.familia == "rodante"
    pot = ag["potencial"] if ag["potencial"] != "-" else "(SEGÚN ENSAYO DE TIPO IRAM 3542/3543)"
    agen = {True: f"POLVO {ag['grado']} - SELLO IRAM 3569 - MARCA DEMSA"}.get(ag["grado"] in AG.GRADOS_ABC,
                                                                              ag["grado"].upper())
    f = [("CAPACIDAD NOMINAL", m.capacidad.replace(" Ø3", "").replace(".", ","), "3534 3° b"),
         ("AGENTE EXTINTOR", agen, "3523 7.13 e · " + MERCADO),
         ("POTENCIAL EXTINTOR", f"{pot}. ADVERTENCIA: EL POTENCIAL SE GARANTIZA SÓLO EN LAS CONDICIONES ORIGINALES "
          "DE FABRICACIÓN", "3534 3° i")]
    if m.familia != "co2":
        f.append(("PRESIÓN DE SERVICIO", _mpa(s["Presión de servicio (MPa)"]) + " A 20 °C", "3534 3° c"))
    f.append(("PRESIÓN DE ENSAYO HIDROSTÁTICO", _mpa(s["Presión de ensayo (MPa)"]), "3534 3° d"))
    f.append(("TEMPERATURA DE USO", f"DE {s['Rango temperatura (°C)'].replace(' a ', ' °C A ')} °C", "3534 3° h"))
    f.append(("PESO TOTAL CARGADO", f"{s['Peso cargado (kg)']} kg", "catálogo · control de carga IRAM 3517-2"))
    if n_ext in ("3523", "3550"):
        f.append(("FABRICACIÓN", "MES / AÑO: __ / __", f"{n_ext} 5.2.4"))
        f.append(("N° DE " + ("SERIE" if rod else "RECIPIENTE"), "______ (IGUAL AL GRABADO)", f"{n_ext} 5.2.4 / 5.1"))
    f.append(("VIDA ÚTIL", f"{30 if m.familia == 'co2' else 20} AÑOS DESDE LA FABRICACIÓN (VENCE MM/AA)",
              "Res. 349/07 art. 26 (mod. 717/07) · Res. AGC 32/15"))
    f.append(("ORIGEN", "INDUSTRIA ARGENTINA", MERCADO))
    return f


def mantenimiento(m):
    """Ala derecha MANTENIMIENTO / ATENCIÓN: (ítem, texto, referencia)."""
    n_ext = m.spec["Norma IRAM extintor"]
    co2 = m.familia == "co2"
    f = [("Mensual", "MENSUALMENTE: " + ("CONTROLE EL PESO (RECARGAR SI PIERDE MÁS DEL 10 %)" if co2 else
                                         "VERIFIQUE QUE LA AGUJA DEL MANÓMETRO ESTÉ EN LA ZONA VERDE") +
          ", EL PRECINTO Y EL SEGURO INTACTOS Y EL ACCESO LIBRE", "3534 3° e · IRAM 3517-2 · " + MERCADO),
         ("Anual", "ANUALMENTE: MANTENIMIENTO Y CONTROL DE CARGA POR RECARGADOR HABILITADO", "3534 3° e · IRAM 3517-2"),
         ("Quinquenal", "CADA 5 AÑOS: PRUEBA HIDRÁULICA DEL RECIPIENTE", "3534 3° e · IRAM 3517-2"),
         ("Instalación", "EL MATAFUEGO DEBE SER INSTALADO Y MANTENIDO SEGÚN LA NORMA IRAM 3517", "3534 3° f"),
         ("Recarga", "RECARGAR INMEDIATAMENTE DESPUÉS DE CUALQUIER USO, AUNQUE SEA PARCIAL", "3534 3° g")]
    if n_ext in ("3523", "3550", "3504", "3694", "3525", "3527", "3541") or co2:
        f.append(("Presión", "ATENCIÓN: EL CONTENIDO DE ESTE MATAFUEGO ESTÁ BAJO PRESIÓN", "3523 5.2.4 j"))
    if etiqueta_agente(m):
        f.append(("Agente", etiqueta_agente(m), "3523 5.2.4 n · 7.13 e"))
    if gas(m):
        f.append(("Gas", gas(m), "3523 5.2.4 o" if n_ext in PROPIOS_ROT else f"IRAM {n_ext}"))
    return f


def logos(m):
    lg = ["SELLO IRAM", "OPDS", "GCBA", "DPS", "QR"]
    return lg


def pie(m):
    fab = "FLAMA S.A. - DOMICILIO" if _propio(m) else "FABRICANTE CERTIFICADO - COMERCIALIZA FLAMA S.A."
    chas = " · C.H.A.S. N° ___" if m.codigo in ("FL_MAT_ABC_1kg", "FL_MAT_ABC_2.5kg", "FL_MAT_ABC_5kg") else ""
    return f"{fab} · INDUSTRIA ARGENTINA · HABILIT. ORD. 40.473 (CABA) N° ___ · O.P.D.S. REG. N° ___{chas}"


def contenido(m):
    """Filas (zona IRAM 3534, ubicación, ítem, texto, referencia) para la tabla de la hoja 4.
    Ubicación: C = panel central (≤ 108°), I = ala izquierda, D = ala derecha, P = pie."""
    n_ext = m.spec["Norma IRAM extintor"]
    cls = clases(m)
    pic = pictogramas(m)
    f = [("2", "C", "Encabezado", ("FLAMA" if _propio(m) else "MARCA DEL FABRICANTE") + " + " + tipo(m),
          "3534 2.2.1 2° y 3° a · " + MERCADO),
         ("1", "C", "Instrucciones", " · ".join(instrucciones(m)) + " (con ilustración por paso)",
          "3534 2.2.1 1° y 2.2.4 · " + MERCADO),
         ("1", "C", "Símbolos de clase", "PARA FUEGOS CLASE " + " · ".join(cls) +
          " (fig. 1, mín. 12 mm; A verde, B rojo, C azul, D amarillo)", "3534 2.2.2"),
         ("1", "C", "Pictogramas", ("A " + ("apto" if pic[0] else "tachado") + " · B " + ("apto" if pic[1] else "tachado")
                                    + " · C " + ("apto" if pic[2] else "tachado") + " (mín. 18 × 18 mm, junto al símbolo)")
          if pic else "Clase " + "/".join(c for c in cls if c in "DK") + ": símbolo + leyenda del riesgo",
          "3534 2.2.3"),
         ("1", "C", "Uso eléctrico", electrico(m), MERCADO)]
    if n_ext == "3504":
        f.append(("1", "C", "Leyendas 3504", "PRECAUCIÓN AL USAR EN ESPACIOS CERRADOS · NO USAR EN ESPACIOS "
                  "CONFINADOS · EL CONTENIDO ESTÁ BAJO PRESIÓN", "3504 6.2.2 a-c"))
    f.append(("3", "C", "Logos", "SELLO IRAM DE CONFORMIDAD (versión placa) · OPDS · GCBA · DPS · QR a ficha técnica",
              f"{n_ext} 5.2.4 p · Anexo R · " + MERCADO))
    for it, t, ref in datos(m):
        f.append(("3", "I", it.capitalize(), t, ref))
    for it, t, ref in mantenimiento(m):
        f.append(("3", "D", it, t, ref))
    f.append(("2", "P", "Pie", pie(m), "3534 2.2.1 2° · Ord. 40.473 · Res. 522/07 · " + MERCADO))
    if not _propio(m):
        f.append(("-", "-", "Nota", f"Producto revendido: etiqueta del fabricante certificado (IRAM {n_ext}); FLAMA "
                  "verifica estos campos en recepción", "IRAM 3534"))
    return f


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
        h.grafica("A", (x, y - alto * 0.12), alto * 0.42, A.MIDDLE_CENTER)
    elif letra == "B":
        for k in (1.0, 0.84):
            a = alto / 2 * k
            _poly(h, [(x - a, y - a), (x + a, y - a), (x + a, y + a), (x - a, y + a)])
        h.grafica("B", (x, y), alto * 0.5, A.MIDDLE_CENTER)
    elif letra == "C":
        for k in (1.0, 0.86):
            h.msp.add_circle((x, y), alto / 2 * k, dxfattribs={"layer": "01-VISIBLE"})
        h.grafica("C", (x, y), alto * 0.5, A.MIDDLE_CENTER)
    elif letra == "D":
        pts = []
        for i in range(10):
            r = alto / 2 if i % 2 == 0 else alto / 2 * 0.5
            a = math.radians(90 + 36 * i)
            pts.append((x + r * math.cos(a), y + r * math.sin(a)))
        _poly(h, pts)
        h.grafica("D", (x, y), alto * 0.38, A.MIDDLE_CENTER)
    elif letra == "K":
        a = alto / 2
        _poly(h, [(x - a, y - a), (x + a, y - a), (x + a, y + a), (x - a, y + a)])
        h.grafica("K", (x, y), alto * 0.5, A.MIDDLE_CENTER)


def pictograma(h, c, lado, fuego, apto):
    x, y = c
    a = lado / 2
    _poly(h, [(x - a, y - a), (x + a, y - a), (x + a, y + a), (x - a, y + a)])
    h.grafica({"A": "sólido", "B": "líquido", "C": "eléctrico"}[fuego], (x, y), max(1.0, lado * 0.16), A.MIDDLE_CENTER)
    if not apto:
        h.linea((x - a, y + a), (x + a, y - a), "01-VISIBLE")


def _logo(h, nombre, c, lado):
    x, y = c
    a = lado / 2
    if nombre == "SELLO IRAM":
        h.msp.add_circle((x, y), a, dxfattribs={"layer": "01-VISIBLE"})
        h.msp.add_circle((x, y), a * 0.62, dxfattribs={"layer": "08-FINA"})
        h.grafica("IRAM", (x, y), lado * 0.2, A.MIDDLE_CENTER)
    elif nombre == "QR":
        _poly(h, [(x - a, y - a), (x + a, y - a), (x + a, y + a), (x - a, y + a)], "08-FINA")
        for dx, dy in ((-1, 1), (1, 1), (-1, -1)):
            q = a * 0.3
            cx, cy = x + dx * (a - q - a * 0.08), y + dy * (a - q - a * 0.08)
            _poly(h, [(cx - q, cy - q), (cx + q, cy - q), (cx + q, cy + q), (cx - q, cy + q)], "08-FINA")
        h.grafica("QR", (x, y), lado * 0.2, A.MIDDLE_CENTER)
    else:
        _poly(h, [(x - a, y - a * 0.6), (x + a, y - a * 0.6), (x + a, y + a * 0.6), (x - a, y + a * 0.6)], "08-FINA")
        h.grafica(nombre, (x, y), lado * 0.22, A.MIDDLE_CENTER)


def _ilustracion(h, c, w, hh, n):
    """Recuadro de la ilustración del paso n (figura del operador; arte final del proveedor de etiquetas)."""
    x, y = c
    _poly(h, [(x - w / 2, y - hh / 2), (x + w / 2, y - hh / 2), (x + w / 2, y + hh / 2), (x - w / 2, y + hh / 2)], "08-FINA")
    h.linea((x - w / 2, y - hh / 2), (x + w / 2, y + hh / 2), "08-FINA")
    h.grafica(f"ilustr. {n}", (x, y - hh / 2 + max(0.8, hh * 0.08)), max(0.8, min(w, hh) * 0.12), A.BOTTOM_CENTER)


# ------------------------------------------------------------------ diagramación de la etiqueta
def _wrap(t, w, alto):
    return textwrap.wrap(t, max(6, int(w / (CW * alto))))


def _filas_ala(filas, w, ht):
    out = []
    for it, t, _ in filas:
        out += _wrap(t if it in ("Mensual", "Anual", "Quinquenal", "Instalación", "Recarga", "Presión", "Agente", "Gas")
                     else f"{it}: {t}", w, ht)
        out.append("")
    return out[:-1]


def disposicion(m, W, Wa=None):
    """Diagramación en mm reales de la etiqueta: panel central W (arco 108°, instrucciones, IRAM 3534 2.2.4.3)
    y alas Wa a cada lado (datos y mantenimiento). Letras de instrucciones según masa total (2.2.4.3),
    símbolos ≥ 12 mm, pictogramas ≥ 18 mm. Devuelve bloques y el alto H que pide el contenido."""
    Wa = W / 2 if Wa is None else Wa
    masa = _masa(m)
    lo, hi = (3.0, 8.0) if masa < 9 else (6.5, 10.0)
    ht = 1.8 if masa < 9 else 2.5                     # otras indicaciones: serie IRAM 4503
    u = W - 6
    # encabezado
    hm = min(12.0, max(lo + 2, u / (CW * 8)))        # marca
    hti = max(ht * 1.2, min(lo + 1, u / (CW * len(tipo(m)))))
    t_lin = _wrap(tipo(m), u, hti)
    z_enc = 3 + hm + 2 + len(t_lin) * hti * 1.4 + 2
    # instrucciones
    pasos = instrucciones(m)
    cols = W >= 150
    if cols:
        cw = u / len(pasos)
        hl = max(lo, min(hi, (cw - 2) / (CW * 13)))
        p_lin = [_wrap(p, cw - 2, hl) for p in pasos]
        ill = min(cw - 4, 26.0)
        z_ins = max(len(x) for x in p_lin) * hl * 1.4 + 2 + ill * 0.75 + 3
    else:
        ill = max(12.0, min(22.0, u * 0.24))
        tw = u - ill - 2
        hl = max(lo, min(hi, tw / (CW * 24)))
        p_lin = [_wrap(p, tw, hl) for p in pasos]
        z_ins = sum(max(ill * 0.75, len(x) * hl * 1.4) + 2 for x in p_lin)
    z_tit = ht * 1.3 * 1.8
    # clases
    sym = max(12.0, min(30.0, u / 9))
    pz = max(18.0, min(40.0, u / 6.5))
    pic = pictogramas(m)
    ncl = len(clases(m))
    if pic is None:
        z_cls = ht * 1.6 + 0.6 + sym + 3
        dos = False
    else:
        dos = 3 * (sym * 1.2 + pz + 5) > u
        z_cls = ht * 1.6 + 0.6 + (sym + 3 + pz if dos else max(sym, pz)) + 3
    he = max(ht * 1.3, lo * 0.8)
    e_lin = _wrap(electrico(m), u, he)
    z_ele = len(e_lin) * he * 1.4 + 2
    ley = []
    if m.spec["Norma IRAM extintor"] == "3504":
        ley = _wrap("PRECAUCIÓN AL USAR EN ESPACIOS CERRADOS · NO USAR EN ESPACIOS CONFINADOS · EL CONTENIDO ESTÁ BAJO "
                    "PRESIÓN", u, he)
    z_ley = len(ley) * he * 1.4 + (2 if ley else 0)
    lg = min(24.0, max(6.0, u / len(logos(m)) / 2.5))
    z_log = lg + 4
    centro = z_enc + z_tit + z_ins + z_cls + z_ele + z_ley + z_log
    # alas
    wa = Wa - 4
    i_lin = _filas_ala(datos(m), wa, ht)
    d_lin = _filas_ala(mantenimiento(m), wa, ht)
    ala = 3 + ht * 1.6 + max(len(i_lin), len(d_lin)) * ht * 1.4 + 2
    f_lin = _wrap(pie(m), W + 2 * Wa - 6, ht)
    z_pie = len(f_lin) * ht * 1.4 + 2.5
    H = max(centro, ala) + z_pie
    return dict(hl=hl, ht=ht, hm=hm, hti=hti, t_lin=t_lin, z_enc=z_enc, z_tit=z_tit, cols=cols, p_lin=p_lin, ill=ill,
                z_ins=z_ins, sym=sym, pz=pz, dos=dos, z_cls=z_cls, he=he, e_lin=e_lin, z_ele=z_ele, ley=ley,
                z_ley=z_ley, lg=lg, z_log=z_log, i_lin=i_lin, d_lin=d_lin, f_lin=f_lin, z_pie=z_pie, W=W, Wa=Wa,
                H=H, rango=(lo, hi), centro=centro)


def placa(h, m, zona, W, Wa, H):
    """Dibuja la etiqueta desarrollada ((W + 2 Wa) × H mm reales) dentro de zona a la mayor escala normal."""
    d = disposicion(m, W, Wa)
    Wt = W + 2 * Wa
    x0, y0, x1, y1 = zona
    esc = next(s for s in (1.0, 0.5, 0.4, 0.2, 0.1) if Wt * s <= x1 - x0 - 18 and H * s <= y1 - y0 - 20)
    w, hh = Wt * esc, H * esc
    ox, oy = (x0 + x1) / 2 - w / 2, (y0 + y1 - 10) / 2 - hh / 2 + 3
    e = esc
    top = oy + hh
    h.rect(ox, oy, ox + w, top, "01-VISIBLE")
    xa, xb = ox + Wa * e, ox + (Wa + W) * e                 # límites del panel central (arco 108°)
    yp = oy + d["z_pie"] * e
    h.linea((xa, yp), (xa, top), "08-FINA")
    h.linea((xb, yp), (xb, top), "08-FINA")
    h.linea((ox, yp), (ox + w, yp), "08-FINA")
    h.texto(f"R1 ETIQUETA DESARROLLADA {_n(Wt, 0)} × {_n(H, 0)} mm (panel central {_n(W, 0)} = arco 108° + alas "
            f"{_n(Wa, 0)}) - ESC. {'1:1' if esc == 1 else '1:' + _n(1 / esc, 1)}", ((x0 + x1) / 2, y1 - 3), 2.5,
            A.MIDDLE_CENTER)
    cx = (xa + xb) / 2
    xl = xa + 3 * e
    u = (W - 6) * e
    y = top - 3 * e
    # encabezado: marca + tipo (zona 2 + 3° a)
    h.grafica("FLAMA" if _propio(m) else "MARCA DEL FABRICANTE", (cx, y), d["hm"] * e * (1 if _propio(m) else 0.45),
            A.TOP_CENTER)
    y -= (d["hm"] + 2) * e
    for ln in d["t_lin"]:
        h.grafica(ln, (cx, y), d["hti"] * e, A.TOP_CENTER)
        y -= d["hti"] * 1.4 * e
    y = top - d["z_enc"] * e
    h.linea((xa, y), (xb, y), "08-FINA")
    h.grafica("INSTRUCCIONES", (cx, y - 1 * e), d["ht"] * 1.3 * e, A.TOP_CENTER)
    y -= d["z_tit"] * e
    # pasos
    hl, ill = d["hl"] * e, d["ill"] * e
    if d["cols"]:
        cw = u / len(d["p_lin"])
        for i, lns in enumerate(d["p_lin"]):
            xc_ = xl + cw * i
            yy = y
            for ln in lns:
                h.grafica(ln, (xc_ + 1 * e, yy), hl, A.TOP_LEFT)
                yy -= hl * 1.4
            yt = y - max(len(x) for x in d["p_lin"]) * hl * 1.4 - 2 * e
            _ilustracion(h, (xc_ + cw / 2, yt - ill * 0.375), ill, ill * 0.75, i + 1)
            if i:
                h.linea((xc_, y + 1 * e), (xc_, y - d["z_ins"] * e + 2 * e), "08-FINA")
    else:
        yy = y
        for i, lns in enumerate(d["p_lin"]):
            alto = max(ill * 0.75, len(lns) * hl * 1.4)
            for k, ln in enumerate(lns):
                h.grafica(ln, (xl, yy - k * hl * 1.4), hl, A.TOP_LEFT)
            _ilustracion(h, (xl + u - ill / 2, yy - ill * 0.375), ill, ill * 0.75, i + 1)
            yy -= alto + 2 * e
    y -= d["z_ins"] * e
    h.linea((xa, y), (xb, y), "08-FINA")
    # clases
    h.grafica("PARA FUEGOS CLASE", (xl, y - 0.6 * e), d["ht"] * e, A.TOP_LEFT)
    y -= d["ht"] * 1.6 * e + 0.6 * e
    sym, pz = d["sym"] * e, d["pz"] * e
    pic = pictogramas(m)
    cls = clases(m)
    if pic is None:
        xx = xl + sym / 2
        for c in cls:
            simbolo(h, c, (xx, y - sym / 2), sym)
            xx += sym * 1.3
        h.grafica({"D": "METALES COMBUSTIBLES", "K": "ACEITES Y GRASAS DE COCINA"}["D" if "D" in cls else "K"],
                (xx - sym * 0.3, y - sym / 2), d["ht"] * e, A.MIDDLE_LEFT)
    elif d["dos"]:
        xx = xl + sym / 2
        for c in cls:
            simbolo(h, c, (xx, y - sym / 2), sym)
            xx += sym * 1.25
        xp = xl + pz / 2
        for fz, ok in zip("ABC", pic):
            pictograma(h, (xp, y - sym - 3 * e - pz / 2), pz, fz, ok)
            xp += pz * 1.1
    else:
        xx = xl
        for fz, ok in zip("ABC", pic):
            if fz in cls:
                simbolo(h, fz, (xx + sym / 2, y - max(sym, pz) / 2), sym)
            xx += sym * 1.2 + 1 * e
            pictograma(h, (xx + pz / 2, y - max(sym, pz) / 2), pz, fz, ok)
            xx += pz + 4 * e
    y = top - (d["z_enc"] + d["z_tit"] + d["z_ins"] + d["z_cls"]) * e
    for ln in d["e_lin"] + d["ley"]:
        h.grafica(ln, (cx, y), d["he"] * e, A.TOP_CENTER)
        y -= d["he"] * 1.4 * e
    y -= 2 * e
    lg = d["lg"] * e
    nl = logos(m)
    paso = u / len(nl)
    for i, nom in enumerate(nl):
        _logo(h, nom, (xl + paso * (i + 0.5), y - 2 * e - lg / 2), lg)
    # alas
    ht = d["ht"] * e
    for titulo, lns, x_ in (("DATOS TÉCNICOS", d["i_lin"], ox + 2 * e), ("MANTENIMIENTO / ATENCIÓN", d["d_lin"], xb + 2 * e)):
        yy = top - 3 * e
        h.grafica(titulo, (x_, yy), min(ht * 1.15, (Wa - 4) * e / (CW * len(titulo))), A.TOP_LEFT)
        yy -= ht * 1.6
        for ln in lns:
            if ln:
                h.grafica(ln, (x_, yy), ht, A.TOP_LEFT)
            yy -= ht * 1.4
    yy = yp - 1.2 * e
    for ln in d["f_lin"]:
        h.grafica(ln, (ox + w / 2, yy), ht, A.TOP_CENTER)
        yy -= ht * 1.4
    h.cota_lineal((ox, oy), (ox + w, oy), (ox, oy - 7), 0, 1 / esc)
    h.cota_lineal((xa, top), (xb, top), (xa, top + 4), 0, 1 / esc)
    h.cota_lineal((ox + w, oy), (ox + w, top), (ox + w + 7, oy), 90, 1 / esc)
    ga = _n(math.degrees(Wa / (W / math.radians(M.ARCO_PLACA))), 0)
    h.texto(f"ala izq. ({ga}°)", ((ox + xa) / 2, oy - 2), 1.6, A.TOP_CENTER, "08-FINA")
    h.texto(f"ala der. ({ga}°)", ((xb + ox + w) / 2, oy - 2), 1.6, A.TOP_CENTER, "08-FINA")
    return esc, d["hl"]


# ------------------------------------------------------------------ hoja 4
def _bloque(h, txts, x, y, alto=1.8, paso=3.6, ancho=None):
    """nota de varias líneas; con `ancho` el texto se vuelve a partir para no salir de su recuadro."""
    if ancho:
        txts = partir(" ".join(txts), ancho, 1.8, 40)
        paso = max(1.8 * 1.45, min(paso, 2.9))
    for i, t in enumerate(txts):
        h.texto(t, (x, y - paso * i), alto)


def hoja4(m, piezas, info, proy, doc, ox):
    rev = not _propio(m)
    h = Hoja(doc, "A2", ox)
    h.formato()
    r = rotulo_base(m, "A2", None, 4, "Rotulado e identificación", "Etiqueta, sellos, oblea, tarjeta, precinto y marcado")
    h.rotulo(r)
    X0, Y0, X1, Y1 = h.fx0, h.fy0, h.fx1, h.fy1
    h.texto(f"ROTULADO E IDENTIFICACIÓN - {m.nombre.upper()}", ((X0 + X1) / 2, Y1 - 7), 5, A.MIDDLE_CENTER)
    if rev:
        h.texto("PRODUCTO REVENDIDO: etiqueta, estampado y precinto los aplica el fabricante certificado; esta hoja es la "
                "especificación de RECEPCIÓN de FLAMA (lo que el equipo debe traer).", ((X0 + X1) / 2, Y1 - 11.8), 2.5,
                A.MIDDLE_CENTER)
    W, H, z0, R, xc, yc = M.placa_dim(m, piezas)
    Wa = M.ala_dim(R)
    # R1 etiqueta
    esc, hl = placa(h, m, (X0 + 8, Y0 + 195, X0 + 290, Y1 - 14), W, Wa, H)
    # R2 ubicación (vista anterior)
    ex = V.extension(proy["anterior"]["vis"])
    zx0, zy0, zx1, zy1 = X0 + 300, Y0 + 195, X0 + 430, Y1 - 14
    f = min((zx1 - zx0 - 30) / (ex[2] - ex[0]), (zy1 - zy0 - 22) / (ex[3] - ex[1]))
    f = next(s for s in (1 / 2, 1 / 5, 1 / 10, 1 / 20) if s <= f)
    Tx = (zx0 + zx1) / 2 - (ex[0] + ex[2]) / 2 * f
    Ty = zy0 + 24 - ex[1] * f
    h.prims(proy["anterior"]["vis"], "01-VISIBLE", (Tx, Ty, f))
    cuerda = 2 * R * math.sin(math.radians(M.ARCO_PLACA / 2))
    ancho_p = R * min(1.0, math.sin(math.radians(M.ARCO_PLACA / 2 + M.arco_ala(R))))
    h.rayado(sg.box(Tx + (xc - ancho_p) * f, Ty + z0 * f, Tx + (xc + ancho_p) * f, Ty + (z0 + H) * f), 45, 2.5)
    h.rayado(sg.box(Tx + (xc - cuerda / 2) * f, Ty + z0 * f, Tx + (xc + cuerda / 2) * f, Ty + (z0 + H) * f), 45, 1.2)
    zo = z0 - 3 - M.OBLEA_PBA
    h.cota_lineal((Tx + (xc + cuerda / 2) * f, Ty), (Tx + (xc + cuerda / 2) * f, Ty + z0 * f),
                  (Tx + (xc + R) * f + 10, Ty), 90, 1 / f)
    h.cota_lineal((Tx + (xc + cuerda / 2) * f, Ty + z0 * f), (Tx + (xc + cuerda / 2) * f, Ty + (z0 + H) * f),
                  (Tx + (xc + R) * f + 10, Ty), 90, 1 / f)
    h.cota_lineal((Tx + (xc - cuerda / 2) * f, Ty + z0 * f), (Tx + (xc + cuerda / 2) * f, Ty + z0 * f),
                  (Tx, Ty - 8), 0, 1 / f)
    h.texto(f"cuerda {_n(cuerda, 0)} = panel central (arco 108° = {_n(W, 0)} mm desarrollados); rayado ancho = alas",
            ((zx0 + zx1) / 2, Ty - 14), 1.8, A.MIDDLE_CENTER)
    h.nota_referencia("Oblea PBA Ø46", (Tx + xc * f, Ty + (zo + M.OBLEA_PBA / 2) * f),
                      (Tx + (xc - R) * f - 14, Ty + (zo - 10) * f), 2.2)
    tb = piezas.get("tarjeta_caba")
    if tb is not None:
        bt = tb.BoundingBox()
        h.nota_referencia("Tarjeta AGC (CABA)", (Tx + xc * f, Ty + (bt.zmin + bt.zmax) / 2 * f),
                          (Tx + (xc - R) * f - 14, Ty + bt.zmin * f - 16), 2.2)
    fj = piezas.get("faja_garantia")
    if fj is not None:
        bf = fj.BoundingBox()
        h.nota_referencia("Faja de garantía", (Tx + (bf.xmin + bf.xmax) / 2 * f, Ty + (bf.zmin + bf.zmax) / 2 * f),
                          (Tx + (xc + R) * f + 6, Ty + (bf.zmax + 25) * f), 2.2)
    h.eje((Tx + xc * f, Ty - 3), (Tx + xc * f, Ty + (z0 + H) * f + 3))
    h.texto("R2 UBICACIÓN (vista anterior, esc. 1:" + _n(1 / f, 0) + ")", ((zx0 + zx1) / 2, zy1 - 3), 2.5,
            A.MIDDLE_CENTER)
    nota_r2 = partir("Etiqueta de frente sobre el eje del manómetro; oblea inmediatamente debajo, sin otra "
                     "identificación entre ambas (Res. 522/07 an. 6); estampilla IRAM al costado; etiqueta GS1 a 180° "
                     "(posterior).", zx1 - zx0, 1.8, 3)
    for i, ln in enumerate(nota_r2):
        h.texto(ln, ((zx0 + zx1) / 2, zy0 + 2.5 + 2.6 * (len(nota_r2) - 1 - i)), 1.8, A.MIDDLE_CENTER)
    # R3 símbolos acotados
    sx0, sy0, sx1, sy1 = X0 + 436, Y0 + 290, X1 - 4, Y1 - 14
    h.texto("R3 SÍMBOLOS Y PICTOGRAMAS (IRAM 3534)", ((sx0 + sx1) / 2, sy1 - 3), 2.5, A.MIDDLE_CENTER)
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
            pictograma(h, (xs, sy0 + 26), 18, fz, ok)
            xs += 24
        h.texto("Pictogramas mín. 18 × 18 mm, fondo negro y figura blanca", (sx0 + 2, sy0 + 12), 1.8)
        h.texto("(mercado); tachado rojo = no apto.", (sx0 + 2, sy0 + 8.5), 1.8)
    else:
        h.texto("Clases D/K: símbolo del producto (IRAM 3534 no prevé pictograma)", (sx0 + 2, sy0 + 20), 1.8)
    # R4 oblea PBA
    ox_, oy_ = X0 + 436, Y0 + 195
    h.texto("R4 OBLEA FABRICACIÓN PBA (Res. 522/07)", ((ox_ + X1 - 4) / 2, oy_ + 90), 2.5, A.MIDDLE_CENTER)
    c4 = (ox_ + 30, oy_ + 45)
    for rr in (23, 16):
        h.msp.add_circle(c4, rr, dxfattribs={"layer": "01-VISIBLE"})
    h.grafica("ÚNICO SELLO OFICIAL", (c4[0], c4[1] + 19.5), 1.15, A.MIDDLE_CENTER)
    h.grafica("LEY 19.587", (c4[0], c4[1] - 19.5), 1.15, A.MIDDLE_CENTER)
    h.grafica("DPS", (c4[0] - 19.5, c4[1]), 1.4, A.MIDDLE_CENTER, rot=90)
    h.grafica("DPS", (c4[0] + 19.5, c4[1]), 1.4, A.MIDDLE_CENTER, rot=-90)
    h.grafica("PROVINCIA DE BUENOS AIRES", (c4[0], c4[1] + 11), 1.3, A.MIDDLE_CENTER)
    h.rect(c4[0] - 12, c4[1] + 1, c4[0] + 12, c4[1] + 8, "08-FINA")
    h.grafica("PRÓXIMA REVISIÓN DE CARGA", (c4[0], c4[1] + 6.5), 1.1, A.MIDDLE_CENTER)
    h.grafica("MM / AAAA", (c4[0], c4[1] + 3), 1.6, A.MIDDLE_CENTER)
    h.grafica("1H0 0000000", (c4[0], c4[1] - 5), 2.0, A.MIDDLE_CENTER)
    h.grafica("LEY 11.459 - DTO. 4992/90", (c4[0], c4[1] - 10), 1.1, A.MIDDLE_CENTER)
    h.cota_lineal((c4[0] - 23, c4[1] - 25), (c4[0] + 23, c4[1] - 25), (c4[0] - 23, c4[1] - 30), 0, 1, prefijo="%%c")
    _bloque(h, ["Autoadhesiva, autodestructible, fondo", "guilloche lila, imagen latente «válido»,",
                "numerada (relevado: «1H01036888»).", "Anillo: único sello oficial obligatorio;",
                "Sello DPS; Ley 19.587; Ley 11.459.", "Campo «próxima revisión de carga»", "completado (mes/año).",
                "Ubicación: frente, eje del manómetro,", "inmediatamente debajo de la etiqueta.",
                "Venta en Prov. de Bs. As.; la provee", "el organismo al fabricante inscripto."], ox_ + 57, oy_ + 80,
            ancho=X1 - 4 - (ox_ + 57))
    # R5 estampilla IRAM
    ex_, ey_ = X0 + 385, Y0 + 125
    ew, eh = M.ESTAMPILLA_IRAM
    h.texto("R5 ESTAMPILLA IRAM EXTINTOR NUEVO", (ex_ + 42, ey_ + 66), 2.5, A.MIDDLE_CENTER)
    sx, sy = ex_ + 12, ey_ + 17
    h.rect(sx, sy, sx + ew, sy + eh, "01-VISIBLE")
    h.grafica("A 26 000000", (sx + 4, sy + eh / 2), 2.4, A.MIDDLE_CENTER, rot=90)
    for i, t in enumerate(["leyenda de conformidad con", "norma IRAM (lote aprobado,", "fabricación bajo control)"]):
        h.grafica(t, (sx + 9, sy + eh - 4 - 3 * i), 1.5)
    h.grafica("INSTITUTO ARGENTINO DE", (sx + 9, sy + eh - 15), 1.6)
    h.grafica("NORMALIZACIÓN Y CERTIF.", (sx + 9, sy + eh - 18), 1.6)
    for i, t in enumerate(["advertencia: la numeración", "identifica matafuego y", "fabricante; adulteración", "= acciones legales"]):
        h.grafica(t, (sx + 9, sy + 13 - 3 * i), 1.4)
    h.msp.add_circle((sx + ew - 11, sy + eh - 11), 8, dxfattribs={"layer": "08-FINA"})
    h.grafica("SELLO", (sx + ew - 11, sy + eh - 10), 1.4, A.MIDDLE_CENTER)
    h.grafica("IRAM", (sx + ew - 11, sy + eh - 12.5), 1.6, A.MIDDLE_CENTER)
    _logo(h, "QR", (sx + ew - 11, sy + 9), 12)
    _bloque(h, [f"≈ {_n(ew, 0)} × {_n(eh, 0)}, fondo guilloche rosa, sello azul; n° vertical",
                "letra + año + n° (relevado «A 25 1111053»). La provee IRAM",
                "numerada sólo al licenciatario; se aplica con etiquetadora.",
                "Alternativa (certifica Bureau Veritas): etiqueta naranja",
                "«MODELO APROBADO» con n° y QR."], ex_ + 2, ey_ + 13, 1.8, 2.9, ancho=84)
    # R6 precinto y faja de garantía
    px, py = X0 + 472, Y0 + 125
    h.texto("R6 PRECINTO Y FAJA DE GARANTÍA", (px + 42, py + 66), 2.5, A.MIDDLE_CENTER)
    fab = "del fabricante" if rev else "FLAMA"
    h.msp.add_circle((px + 14, py + 46), 9, dxfattribs={"layer": "01-VISIBLE"})
    h.linea((px + 23, py + 46), (px + 46, py + 46), "01-VISIBLE")
    h.rect(px + 32, py + 42, px + 42, py + 50, "01-VISIBLE")
    h.grafica("FAB." if rev else "FLAMA", (px + 37, py + 47.2), 1.2, A.MIDDLE_CENTER)
    h.grafica("L 0000", (px + 37, py + 44.5), 1.2, A.MIDDLE_CENTER)
    fx, fy = px + 52, py + 34
    fw, fh = M.FAJA_GARANTIA
    fw, fh = fw * 0.5, fh * 0.5                     # esc. 1:2 (IRAM 4505)
    h.rect(fx, fy, fx + fw, fy + fh, "01-VISIBLE")
    h.rayado(sg.box(fx, fy + fh * 0.5, fx + fw, fy + fh), -45, 2.2)
    h.grafica("LA ROTURA TOTAL DE ESTA", (fx + 1, fy + fh * 0.42), 1.0)
    h.grafica("CINTA INTERRUMPE LA GARANTÍA", (fx + 1, fy + fh * 0.30), 1.0)
    h.grafica("ATENCIÓN", (fx + fw / 2, fy + 1.5), 1.8, A.BOTTOM_CENTER)
    _bloque(h, ["Precinto: pasador alambre Ø 2,5-3,5 con ojal que deja pasar un",
                "cilindro Ø 30 y precinto plástico de color que se rompe al tirar",
                f"(IRAM 3517-2 9.4.13), con la id. {fab} y el lote (IRAM 3523 3.3.2).",
                f"Faja de garantía {_n(M.FAJA_GARANTIA[0], 0)} × {_n(M.FAJA_GARANTIA[1], 0)} (esc. 1:2): vinilo destructible",
                "rayado rojo/blanco, abraza la unión válvula-cuello; indica equipo",
                "nuevo no abierto. Sin norma: práctica de mercado (Georgia)."], px + 2, py + 26, 1.8, 3.4,
            ancho=X1 - 3 - (px + 2))
    # R7 marcado estampado y etiqueta de serie
    mx, my = X0 + 385, Y0 + 61
    h.texto("R7 MARCADO GRABADO Y ETIQUETA DE SERIE", (mx + 42, my + 58), 2.5, A.MIDDLE_CENTER)
    n_ext = m.spec["Norma IRAM extintor"]
    if rev:
        txt = "FABRICANTE  N° SERIE  AÑO"
        ref = ("IRAM 2533 (cilindro CO₂ sin costura: estampado del fabricante)" if m.familia == "co2"
               else f"IRAM {n_ext} (norma del producto, aplicado por el fabricante)")
        lin = ["Grabado por el fabricante del equipo según", ref, "FLAMA verifica que exista y coincida con la etiqueta."]
    else:
        txt = ("FLAMA S.A.  N° 000001  " + ("PH " + m.spec["Presión de ensayo (MPa)"] + " MPa  " if n_ext == "3550" else "")
               + "26")
        lin = [("Fabricante, n° de " + ("serie, presión de ensayo" if n_ext == "3550" else "recipiente") +
                " y año (2 díg.) - IRAM " + n_ext + " 5.1"),
               *M.marcado(m)[2],
               "letra 5 mm (IRAM 4503); cuño DPS 15 × 7 junto al n°",
               "(Res. 349/07 anexo IV, art. 24 mod. 717/07)."]
    h.rect(mx + 3, my + 42, mx + 82, my + 52, "01-VISIBLE" if not rev else "08-FINA")
    h.grafica(txt, (mx + 38, my + 47), 2.4, A.MIDDLE_CENTER)
    if not rev:
        h.rect(mx + 66, my + 43.5, mx + 81, my + 50.5, "01-VISIBLE")
        h.grafica("DPS", (mx + 73.5, my + 47), 3.0, A.MIDDLE_CENTER)
    _bloque(h, lin, mx + 3, my + 38, 1.8, 3.2, ancho=83)
    gw, gh = M.ETIQUETA_SERIE
    gx, gy = mx + 6, my + 6
    h.rect(gx, gy, gx + gw * 0.5, gy + gh * 0.5, "01-VISIBLE")
    _logo(h, "QR", (gx + gw * 0.25, gy + gh * 0.3), gh * 0.35)
    h.grafica("(01)779xxxxxxxxxx(21)000001", (gx + gw * 0.25, gy + 0.6), 0.8, A.BOTTOM_CENTER)
    _bloque(h, [f"Etiqueta de serie GS1 {_n(gw, 0)} × {_n(gh, 0)} (esc. 1:2): QR con", "GTIN (prefijo 779 Argentina) + n° de serie,",
                "a 180° de la etiqueta (relevado Melisam).", "Traza lote de polvo, PH y estampilla."], gx + gw * 0.5 + 3,
            gy + gh * 0.5 + 6, 1.8, 3.0, ancho=mx + 86 - (gx + gw * 0.5 + 3))
    # R8 tarjeta CABA
    tx, ty = X0 + 472, Y0 + 61
    h.texto("R8 TARJETA DE IDENTIFICACIÓN AGC (CABA)", (tx + 42, ty + 58), 2.5, A.MIDDLE_CENTER)
    tw_, th_ = M.TARJETA_CABA
    s8 = 0.5                                         # esc. 1:2 (IRAM 4505)
    bx0, by0 = tx + 3, ty + 20
    h.rect(bx0, by0, bx0 + tw_ * s8, by0 + th_ * s8, "01-VISIBLE")
    h.grafica("Tarjeta de Identificación de Extintor", (bx0 + 1.5, by0 + th_ * s8 - 1.5), 1.3, A.TOP_LEFT)
    h.grafica("AGC · BA Ciudad", (bx0 + tw_ * s8 - 1.5, by0 + th_ * s8 - 1.5), 1.2, A.TOP_RIGHT)
    for i, t in enumerate(["Domicilio instalación", "Empresa fabricante", "Empresa recargadora", "Venc. mantenim.",
                           "Fecha fab. / N° tarjeta", "Venc. VU / Agente", "Capacidad / Extintor N°"]):
        h.grafica(t + ":", (bx0 + 1.5, by0 + th_ * s8 - 5 - 3.05 * i), 1.1)
    _logo(h, "QR", (bx0 + tw_ * s8 - 9, by0 + 10), 14)
    ult = ("Ubicación: al costado de la oblea, opuesta a la estampilla." if "tarjeta_caba" in piezas and
           M.tarjeta_al_costado(M.placa_dim(m, piezas)[3]) else "Ubicación: debajo de la oblea." if "tarjeta_caba" in
           piezas else "NO ENTRA en el cuerpo: 1 kg vehicular sin tarjeta (confirmar con la AGC).")
    _bloque(h, [f"≈ {_n(tw_, 0)} × {_n(th_, 0)}, esc. 1:2 (proporción del modelo, Res. AGC 32/15 anexo I; medida a "
                "confirmar).",
                "Dos módulos: papel con QR impreso por el inscripto en el sistema AGC + etiqueta",
                "autoadhesiva provista por la AGC que lo fija (anexo II art. 3). Cada fabricación",
                "se registra (art. 2). Sólo destino CABA. Venc. VU = fab. + 20 años (349/07 art. 26).", ult],
            tx + 1, ty + 15, 1.8, 3.0, ancho=X1 - 3 - (tx + 1))
    # tabla de contenido
    filas = [("Zona", "Ubic.", "Ítem", "Texto / dato de la etiqueta", "Referencia")]
    for z, ub, it, t, ref in contenido(m):
        filas.append((z, ub, it, t if len(t) <= 215 else t[:212] + "...", ref[:52]))
    alto = min(4.6, 176 / (len(filas) + 1))
    _tabla(h, X0 + 6, Y0 + 186, filas, [9, 9, 33, 236, 75], alto=alto, hs=(1.8, 1.8, 1.8, 1.8, 1.8),
           encabezado="CONTENIDO DE LA ETIQUETA (IRAM 3534 + norma del producto + relevamiento de mercado)")
    h.texto(f"Letra de instrucciones {_n(hl, 1)} mm (IRAM 3534 2.2.4.3: masa total "
            f"{'< 9 kg: 3-8 mm' if _masa(m) < 9 else '≥ 9 kg: 6,5-10 mm'}); mayúsculas IRAM 4503, color en contraste. "
            "Ubic.: C panel central ≤ 108°, I/D alas, P pie. Vinilo laminado ensayado a adherencia ≥ 0,35 N/mm y "
            "abrasión 100 pasadas (IRAM 3534 cap. 3).", (X0 + 6, Y0 + 4), 1.7)
    return h
