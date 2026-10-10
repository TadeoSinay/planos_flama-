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
import random
import textwrap

import numpy as np
import shapely.geometry as sg
from shapely import affinity
from shapely.ops import unary_union, polylabel, transform as shp_transform

from . import modelo3d as M
from . import vistas as V
from . import agentes as AG
from .lamina import Hoja, A, partir
from . import lamina as L
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


# ------------------------------------------------------------------ colores
ROJO_CUERPO = (178, 24, 32)    # esmalte del recipiente: IRAM 10005-1, el rojo identifica los elementos contra incendio
INOX = (196, 200, 206)         # acero inoxidable sin pintar (agua, AFFF y clase K manuales)
LATON = (203, 162, 62)         # válvula de latón forjado
CROMO = (214, 217, 222)        # latón cromado, acero cincado
GOMA = (32, 32, 32)            # manguera, tobera, suncho, cubiertas
ACERO = (120, 122, 128)
GRIS = (165, 168, 172)
CREMA = (238, 222, 170)
NARANJA = (245, 140, 30)
VIOLETA = (110, 70, 160)


def colores(m):
    """Colores del equipo y de la etiqueta. Recipiente rojo (IRAM 10005-1) salvo los de acero inoxidable, que van sin
    pintar. Encabezado de la etiqueta: rojo en polvo y agua (relevado Georgia, Melisam, De León), verde en HCFC
    (relevado Georgia HCFC 123, palancas también verdes), negro CO2, crema AFFF y amarillo clases K y D (código de
    color del agente de EN 3-7 / BS 7863 que repite el mercado)."""
    c = m.codigo
    inox = m.familia == "inox"
    enc, txt = L.ROJO, L.BLANCO
    if "HCFC" in c:
        enc = L.VERDE
    elif "CO2" in c:
        enc = L.NEGRO
    elif "AFFF" in c:
        enc, txt = CREMA, L.NEGRO
    elif "SALESK" in c or "CLASED" in c:
        enc, txt = L.AMARILLO, L.NEGRO
    ins, ins_txt = (L.NEGRO, L.AMARILLO) if enc == L.AMARILLO else (L.AMARILLO, L.NEGRO)   # franja de instrucciones
    return dict(cuerpo=INOX if inox else ROJO_CUERPO, enc=enc, enc_txt=txt, ins=ins, ins_txt=ins_txt,
                manguera=L.VERDE if "HCFC" in c else GOMA,          # HCFC: manguera verde (relevado Georgia)
                palanca=L.VERDE if "HCFC" in c else CROMO if inox else ROJO_CUERPO, valvula=CROMO if inox else LATON)


_INTERNAS = {"cano_pesca", "resorte", "vastago", "filtro_pesca", "junta_cuello", "disco_seguridad", "espiga"}


def color_pieza(k, col):
    """color de la pieza en la vista coloreada (None: pieza interior, no se ve)."""
    if k in _INTERNAS:
        return None
    if k.startswith("manguera"):
        return col["manguera"]
    if k.startswith(("rueda", "tobera", "suncho", "empunadura", "pie", "difusor", "lanza")):
        return GOMA
    if k.startswith("llanta"):
        return GRIS
    if k in ("eje_ruedas", "arandelas_tope"):
        return ACERO
    if k in ("cuerpo_valvula", "racor", "tuerca", "valvula_esferica"):
        return col["valvula"]
    if k in ("eje", "pasador", "brazo_difusor"):
        return CROMO
    if k.startswith("manija_") and k != "manija_carro":
        return col["palanca"]
    return {"manometro": L.BLANCO, "etiqueta": L.BLANCO, "etiqueta_serie": L.BLANCO, "tarjeta_caba": L.BLANCO,
            "oblea_pba": L.LILA, "sello_iram": L.ROSA, "faja_garantia": L.ROJO, "precinto": L.AMARILLO}.get(k, col["cuerpo"])


# ------------------------------------------------------------------ dibujo de símbolos
def _poly(h, pts, capa="01-VISIBLE"):
    h.msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": capa})


def _borde(h, g, rgb=None, capa="13-GRAFICA"):
    """contorno de una geometría shapely (en color si rgb)."""
    for q in getattr(g, "geoms", [g]):
        if q.is_empty or q.geom_type != "Polygon":
            continue
        for anillo in [q.exterior, *q.interiors]:
            ln = h.msp.add_lwpolyline(list(anillo.coords)[:-1], close=True, dxfattribs={"layer": capa})
            if rgb is not None:
                ln.rgb = rgb


def _tf(g, c, k):
    """lleva una figura dibujada en unidades (alto 1) al papel: centro c, escala k."""
    return affinity.affine_transform(g, [k, 0, 0, k, c[0], c[1]])


def _trazo(pts, ancho):
    return sg.LineString(pts).buffer(ancho / 2, cap_style=1, join_style=1)


def _forma_simbolo(letra, x, y, alto):
    """contorno exterior e interior (borde de espesor e) del símbolo de clase, IRAM 3550 5.2.5.2 fig. 1; K hexágono
    (IRAM 3517-2 7.2.2)."""
    if letra == "A":
        ln = alto / math.sin(math.radians(60))
        ext = [(x - ln / 2, y - alto / 2), (x + ln / 2, y - alto / 2), (x, y + alto / 2)]
        inte = [(x - ln / 2 * 0.8, y - alto / 2 * 0.85), (x + ln / 2 * 0.8, y - alto / 2 * 0.85), (x, y + alto / 2 * 0.65)]
        return sg.Polygon(ext), sg.Polygon(inte)
    if letra == "B":
        return sg.box(x - alto / 2, y - alto / 2, x + alto / 2, y + alto / 2), \
            sg.box(x - alto / 2 * 0.84, y - alto / 2 * 0.84, x + alto / 2 * 0.84, y + alto / 2 * 0.84)
    if letra == "C":
        return sg.Point(x, y).buffer(alto / 2, 48), sg.Point(x, y).buffer(alto / 2 * 0.86, 48)
    if letra == "K":
        hx = [(x + alto / 2 / math.cos(math.radians(30)) * math.cos(math.radians(60 * i)),
               y + alto / 2 / math.cos(math.radians(30)) * math.sin(math.radians(60 * i))) for i in range(6)]
        return sg.Polygon(hx), affinity.scale(sg.Polygon(hx), 0.84, 0.84, origin=(x, y))
    pts, pin = [], []
    for i in range(10):
        r = alto / 2 if i % 2 == 0 else alto / 2 * 0.5
        a = math.radians(90 + 36 * i)
        pts.append((x + r * math.cos(a), y + r * math.sin(a)))
        pin.append((x + 0.82 * r * math.cos(a), y + 0.82 * r * math.sin(a)))
    return sg.Polygon(pts), sg.Polygon(pin)


COLOR_CLASE = {"A": L.VERDE, "B": L.ROJO, "C": L.AZUL, "D": L.AMARILLO, "K": L.NEGRO}


def simbolo(h, letra, c, alto):
    """Símbolo de clase IRAM 3550 5.2.5 / IRAM 3534 fig. 1 centrado en c, de `alto` mm de papel, con el fondo
    coloreado (5.2.5.3 e IRAM 3517-2 7.2.2: verde 01-1-150, rojo 03-1-050, azul 08-1-070, amarillo, negro K; mismos
    colores que la forma-letra de NFPA 10 anexo B), borde interior y letra en blanco (en negro sobre el amarillo)."""
    x, y = c
    ext, inte = _forma_simbolo(letra, x, y, alto)
    h.relleno(ext, COLOR_CLASE[letra])
    claro = L.NEGRO if letra == "D" else L.BLANCO
    _poly(h, list(ext.exterior.coords)[:-1])
    _borde(h, inte, claro)
    hl, dy = {"A": (0.42, -0.12), "B": (0.5, 0), "C": (0.5, 0), "D": (0.38, 0), "K": (0.5, 0)}[letra]
    h.grafica(letra, (x, y + dy * alto), alto * hl, A.MIDDLE_CENTER, rgb=claro)


def _llama(x, y, a):
    """llama (exterior, interior) con la base en (x, y) y alto a."""
    pts = [(-0.30, 0), (-0.38, 0.22), (-0.28, 0.42), (-0.21, 0.30), (-0.13, 0.62), (0.0, 0.44), (0.06, 1.0),
           (0.17, 0.55), (0.26, 0.70), (0.36, 0.30), (0.30, 0)]
    ext = sg.Polygon(pts).buffer(0.03, join_style=1)
    return _tf(ext, (x, y), a), _tf(affinity.scale(ext, 0.55, 0.6, origin=(0, 0)), (x, y), a)


def _figura_pictograma(fuego):
    """figura del pictograma de NFPA 10 anexo B en un cuadrado unitario centrado: A cesto y leña con fuego,
    B bidón y líquido derramado con fuego, C tomacorriente y ficha con fuego."""
    ll, _ = _llama(0.0, 0.0, 1.0)
    if fuego == "A":
        cesto = sg.Polygon([(-0.40, -0.36), (-0.12, -0.36), (-0.07, 0.02), (-0.45, 0.02)])
        lena = unary_union([affinity.rotate(sg.box(0.0, -0.37, 0.42, -0.29), a, origin=(0.21, -0.33)) for a in (18, -18)])
        return unary_union([cesto, _tf(ll, (-0.26, 0.04), 0.36), lena, _tf(ll, (0.21, -0.26), 0.58)])
    if fuego == "B":
        bidon = sg.Polygon([(-0.42, -0.36), (-0.08, -0.36), (-0.08, 0.08), (-0.24, 0.08), (-0.42, -0.08)])
        pico = affinity.rotate(sg.box(-0.42, -0.02, -0.34, 0.16), 35, origin=(-0.38, 0.0))
        charco = sg.Point(0.18, -0.37).buffer(1).simplify(0.01)
        charco = affinity.scale(charco, 0.26, 0.05, origin=(0.18, -0.37))
        return unary_union([bidon, pico, charco, _tf(ll, (0.18, -0.34), 0.66)])
    toma = sg.box(-0.44, -0.36, -0.06, 0.06).difference(unary_union([sg.box(-0.33, -0.2, -0.29, -0.06),
                                                                  sg.box(-0.21, -0.2, -0.17, -0.06)]))
    ficha = unary_union([sg.box(0.06, -0.36, 0.30, -0.18), sg.box(0.10, -0.18, 0.13, -0.08), sg.box(0.23, -0.18, 0.26, -0.08),
                         _trazo([(0.18, -0.36), (0.18, -0.44), (0.40, -0.44)], 0.04)])
    return unary_union([toma, ficha, _tf(ll, (0.2, -0.06), 0.5)])


def pictograma(h, c, lado, fuego, apto, rotulo=False):
    """Pictograma de NFPA 10 anexo B: figura blanca sobre fondo azul si es apto; sobre fondo negro con barra diagonal
    roja si no lo es. rotulo: nombre de la clase de fuego debajo del cuadro."""
    x, y = c
    a = lado / 2
    cuadro = sg.box(x - a, y - a, x + a, y + a)
    h.relleno(cuadro, L.AZUL if apto else L.NEGRO)
    h.relleno(_tf(_figura_pictograma(fuego), c, lado), L.BLANCO)
    _poly(h, [(x - a, y - a), (x + a, y - a), (x + a, y + a), (x - a, y + a)])
    if not apto:
        barra = sg.LineString([(x - a, y + a), (x + a, y - a)]).buffer(lado * 0.07, cap_style=2).intersection(cuadro)
        h.relleno(barra, L.ROJO)
    if rotulo:
        h.texto({"A": "sólido", "B": "líquido", "C": "eléctrico"}[fuego] + (" (apto)" if apto else " (no apto)"),
                (x, y - a - 1.5), 1.8, A.TOP_CENTER)


def qr(h, c, lado, semilla=7):
    """código QR de muestra (17 módulos, 3 patrones de posición) en negro sobre blanco."""
    x, y = c
    n = 17
    mdl = lado / n
    x0, y0 = x - lado / 2, y - lado / 2
    h.relleno(sg.box(x0, y0, x0 + lado, y0 + lado), L.BLANCO)
    rnd = random.Random(semilla)
    esq = ((0, 0), (n - 7, n - 7), (0, n - 7))
    for i0, j0 in esq:
        ext = sg.box(x0 + i0 * mdl, y0 + j0 * mdl, x0 + (i0 + 7) * mdl, y0 + (j0 + 7) * mdl)
        h.relleno(ext.difference(ext.buffer(-mdl, join_style=2)), L.NEGRO)
        h.relleno(ext.buffer(-2 * mdl, join_style=2), L.NEGRO)
    for i in range(n):
        for j in range(n):
            if any(i0 - 1 <= i <= i0 + 7 and j0 - 1 <= j <= j0 + 7 for i0, j0 in esq) or rnd.random() > 0.45:
                continue
            h.relleno(sg.box(x0 + i * mdl, y0 + j * mdl, x0 + (i + 1) * mdl, y0 + (j + 1) * mdl), L.NEGRO)
    _poly(h, [(x0, y0), (x0 + lado, y0), (x0 + lado, y0 + lado), (x0, y0 + lado)], "08-FINA")


def _logo(h, nombre, c, lado):
    """logos del pie de la etiqueta en sus colores (arte final del titular de cada marca: acá el lugar y el color)."""
    x, y = c
    a = lado / 2
    if nombre == "SELLO IRAM":
        h.relleno(sg.Point(x, y).buffer(a, 48), L.AZUL)
        _borde(h, sg.Point(x, y).buffer(a * 0.78, 48), L.BLANCO)
        h.msp.add_circle((x, y), a, dxfattribs={"layer": "08-FINA"})
        h.grafica("IRAM", (x, y), lado * 0.24, A.MIDDLE_CENTER, rgb=L.BLANCO)
    elif nombre == "QR":
        qr(h, c, lado)
    elif nombre == "OPDS":
        h.relleno(sg.Point(x, y).buffer(a, 48), L.VERDE)
        h.grafica("OPDS", (x, y), lado * 0.22, A.MIDDLE_CENTER, rgb=L.BLANCO)
    else:
        caja = sg.box(x - a, y - a * 0.6, x + a, y + a * 0.6)
        fondo, letra = (L.AMARILLO, L.NEGRO) if nombre == "GCBA" else ((0, 70, 140), L.BLANCO)
        h.relleno(caja, fondo)
        _poly(h, list(caja.exterior.coords)[:-1], "08-FINA")
        h.grafica(nombre, (x, y), lado * 0.22, A.MIDDLE_CENTER, rgb=letra)


def _tipo_paso(t):
    if "NO TOME" in t:
        return "frio"
    if "CORTE EL GAS" in t:
        return "gas"
    if "DESENROLLE" in t:
        return "manguera"
    if "PRECINTO" in t:
        return "seguro"
    if "COLÓQUESE" in t or "LLEVE" in t:
        return "distancia"
    return "descarga"


def _figura_extintor(c, k, col):
    """extintor de la ilustración: (geometría, color) en papel; c = base, k = alto."""
    cuerpo = unary_union([sg.box(-0.17, 0, 0.17, 0.62), affinity.scale(sg.Point(0, 0.62).buffer(0.17), 1, 0.7,
                                                                      origin=(0, 0.62))])
    valv = sg.box(-0.06, 0.72, 0.06, 0.86)
    pal = _trazo([(-0.02, 0.88), (0.30, 0.95)], 0.05)
    mang = _trazo([(0.06, 0.80), (0.24, 0.74), (0.26, 0.30)], 0.05)
    return [(_tf(cuerpo, c, k), col["cuerpo"]), (_tf(valv, c, k), LATON), (_tf(pal, c, k), L.NEGRO),
            (_tf(mang, c, k), L.NEGRO if col["manguera"] == GOMA else col["manguera"])]   # tinta negra salvo manga de color


def _persona(c, k):
    """operador de pie mirando a la derecha; c = pies, k = alto."""
    g = unary_union([sg.Point(0.03, 0.91).buffer(0.08), _trazo([(0.0, 0.80), (-0.02, 0.46)], 0.11),
                     _trazo([(-0.12, 0.0), (-0.02, 0.46), (0.11, 0.0)], 0.08),
                     _trazo([(0.0, 0.74), (0.13, 0.56), (0.27, 0.58)], 0.06)])
    return _tf(g, c, k)


def _ilustracion(h, c, w, hh, paso, m):
    """ilustración del paso (figuras simplificadas del operador, del equipo y del fuego, como las de las etiquetas
    relevadas); el arte final lo entrega el proveedor de etiquetas."""
    x, y = c
    col = colores(m)
    caja = sg.box(x - w / 2, y - hh / 2, x + w / 2, y + hh / 2)
    h.relleno(caja, L.BLANCO)
    _poly(h, list(caja.exterior.coords)[:-1], "08-FINA")
    k = hh
    piso = y - hh * 0.40
    tipo = _tipo_paso(paso)
    capas = []
    rojo_ll, amar_ll = (230, 60, 20), (255, 190, 0)
    if tipo == "seguro":
        capas += _figura_extintor((x - w * 0.12, piso), k * 0.78, col)
        anillo = sg.Point(x + w * 0.16, piso + k * 0.66).buffer(k * 0.08).difference(
            sg.Point(x + w * 0.16, piso + k * 0.66).buffer(k * 0.05))
        flecha = unary_union([_trazo([(x + w * 0.24, piso + k * 0.66), (x + w * 0.40, piso + k * 0.66)], k * 0.035),
                              sg.Polygon([(x + w * 0.44, piso + k * 0.66), (x + w * 0.38, piso + k * 0.71),
                                          (x + w * 0.38, piso + k * 0.61)])])
        capas += [(anillo, L.NEGRO), (sg.box(x + w * 0.06, piso + k * 0.64, x + w * 0.12, piso + k * 0.68), L.AMARILLO),
                  (flecha, L.ROJO)]
    elif tipo in ("distancia", "descarga"):
        px = x - w * 0.36
        capas.append((_persona((px, piso), k * 0.78), L.NEGRO))
        if m.familia == "rodante":
            carro = sg.box(px + k * 0.22, piso + k * 0.08, px + k * 0.40, piso + k * 0.62)
            capas += [(carro, col["cuerpo"]), (sg.Point(px + k * 0.24, piso + k * 0.08).buffer(k * 0.08), L.NEGRO)]
        else:
            capas += _figura_extintor((px + k * 0.30, piso + k * 0.20), k * 0.36, col)
        lo, li = _llama(x + w * 0.34, piso, k * 0.42)
        capas += [(lo, rojo_ll), (li, amar_ll)]
        if tipo == "distancia":
            yd = piso + k * 0.62
            x1, x2 = px + k * 0.30, x + w * 0.34
            cota = unary_union([_trazo([(x1, yd), (x2, yd)], k * 0.02),
                                sg.Polygon([(x1, yd), (x1 + k * 0.06, yd + k * 0.03), (x1 + k * 0.06, yd - k * 0.03)]),
                                sg.Polygon([(x2, yd), (x2 - k * 0.06, yd + k * 0.03), (x2 - k * 0.06, yd - k * 0.03)])])
            capas.append((cota, L.NEGRO))
        else:
            boca = (px + k * 0.40, piso + k * 0.45)
            chorro = sg.Polygon([boca, (x + w * 0.42, piso + k * 0.02), (x + w * 0.20, piso - k * 0.02)])
            capas.insert(0, (chorro, L.CELESTE if "AGUA" in m.codigo or "AFFF" in m.codigo else (205, 205, 210)))
    elif tipo == "manguera":
        T = 6 * math.pi
        esp = [(x - w * 0.14 + k * (0.04 + 0.30 * t / T) * math.cos(t), y + k * (0.04 + 0.30 * t / T) * math.sin(t))
               for t in [i * T / 120 for i in range(121)]]
        flecha = sg.Polygon([(x + w * 0.44, y - k * 0.30), (x + w * 0.34, y - k * 0.24), (x + w * 0.36, y - k * 0.36)])
        capas += [(_trazo(esp + [(x + w * 0.36, y - k * 0.30)], k * 0.045), L.NEGRO), (flecha, L.ROJO)]
    elif tipo == "frio":
        mano = unary_union([sg.box(x - k * 0.18, y - k * 0.20, x + k * 0.10, y + k * 0.08),
                            *[sg.box(x - k * 0.18 + i * k * 0.07, y + k * 0.08, x - k * 0.13 + i * k * 0.07, y + k * 0.24)
                              for i in range(4)]]).buffer(k * 0.02)
        anillo = sg.Point(x, y).buffer(k * 0.38).difference(sg.Point(x, y).buffer(k * 0.31))
        barra = _trazo([(x - k * 0.25, y + k * 0.25), (x + k * 0.25, y - k * 0.25)], k * 0.07)
        capas += [(mano, L.NEGRO), (anillo, L.ROJO), (barra, L.ROJO)]
    elif tipo == "gas":
        capas += [(sg.box(x - w * 0.42, y - k * 0.06, x + w * 0.42, y + k * 0.06), L.AMARILLO),
                  (sg.Point(x, y).buffer(k * 0.12), GRIS), (_trazo([(x, y), (x + k * 0.05, y + k * 0.34)], k * 0.06), L.NEGRO),
                  (_trazo([(x + k * 0.30, y + k * 0.30), (x + k * 0.36, y + k * 0.12), (x + k * 0.30, y - k * 0.04)],
                          k * 0.04), L.ROJO)]
    for g, rgb in capas:
        h.relleno(g.intersection(caja), rgb)
    if tipo == "distancia":
        h.grafica(f"{_n(distancia(m), 1)} m", ((x - w * 0.36 + k * 0.30 + x + w * 0.34) / 2, piso + k * 0.66),
                  max(0.6, k * 0.14), A.BOTTOM_CENTER)


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
    htit = max(ht * 1.3, hl * 0.7)                   # título INSTRUCCIONES en franja amarilla (mercado)
    z_tit = htit * 1.6 + 1
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
    return dict(htit=htit, hl=hl, ht=ht, hm=hm, hti=hti, t_lin=t_lin, z_enc=z_enc, z_tit=z_tit, cols=cols, p_lin=p_lin, ill=ill,
                z_ins=z_ins, sym=sym, pz=pz, dos=dos, z_cls=z_cls, he=he, e_lin=e_lin, z_ele=z_ele, ley=ley,
                z_ley=z_ley, lg=lg, z_log=z_log, i_lin=i_lin, d_lin=d_lin, f_lin=f_lin, z_pie=z_pie, W=W, Wa=Wa,
                H=H, rango=(lo, hi), centro=centro)


def _banda_electrico(m):
    t = electrico(m)
    if t.startswith("SÓLO"):
        return L.AMARILLO, L.NEGRO
    return (L.ROJO, L.BLANCO) if "NO APTO" in t else (L.AZUL, L.BLANCO)


def _titulo_ala(d, titulo):
    return min(d["ht"] * 1.15, (d["Wa"] - 4) / (CW * len(titulo)))


ALAS = ("DATOS TÉCNICOS", "MANTENIMIENTO / ATENCIÓN")


def elementos(m, d):
    """Elementos de color de la etiqueta en mm reales, origen en el ángulo inferior izquierdo de la etiqueta
    desarrollada (misma diagramación que placa): bandas, símbolos, pictogramas, logos e ilustraciones."""
    col = colores(m)
    W, Wa, H = d["W"], d["Wa"], d["H"]
    Wt = W + 2 * Wa
    xa, xb = Wa, Wa + W
    xl, u = xa + 3, W - 6
    ht, hl, ill = d["ht"], d["hl"], d["ill"]
    ok = {"bandas": [], "simbolos": [], "pictos": [], "logos": [], "ilus": [], "texto_dk": None}
    y_enc = H - d["z_enc"]
    ok["bandas"] += [(sg.box(xa, y_enc, xb, H), col["enc"]), (sg.box(xa, y_enc - d["z_tit"] + 1, xb, y_enc), col["ins"])]
    for titulo, x_ in zip(ALAS, (0, xb)):
        ok["bandas"].append((sg.box(x_, H - 2 - _titulo_ala(d, titulo) - 0.8, x_ + Wa, H), col["enc"]))
    ok["bandas"].append((sg.box(0, 0, Wt, d["z_pie"]), col["enc"]))
    pasos = instrucciones(m)
    y = y_enc - d["z_tit"]
    if d["cols"]:
        cw = u / len(d["p_lin"])
        yt = y - max(len(x) for x in d["p_lin"]) * hl * 1.4 - 2
        for i in range(len(d["p_lin"])):
            ok["ilus"].append(((xl + cw * i + cw / 2, yt - ill * 0.375), ill, ill * 0.75, pasos[i]))
    else:
        yy = y
        for i, lns in enumerate(d["p_lin"]):
            ok["ilus"].append(((xl + u - ill / 2, yy - ill * 0.375), ill, ill * 0.75, pasos[i]))
            yy -= max(ill * 0.75, len(lns) * hl * 1.4) + 2
    y -= d["z_ins"]
    y -= ht * 1.6 + 0.6
    sym, pz = d["sym"], d["pz"]
    pic, cls = pictogramas(m), clases(m)
    if pic is None:
        xx = xl + sym / 2
        for c in cls:
            ok["simbolos"].append((c, (xx, y - sym / 2), sym))
            xx += sym * 1.3
        ok["texto_dk"] = (xx - sym * 0.3, y - sym / 2)
    elif d["dos"]:
        xx = xl + sym / 2
        for c in cls:
            ok["simbolos"].append((c, (xx, y - sym / 2), sym))
            xx += sym * 1.25
        xp = xl + pz / 2
        for fz, apto in zip("ABC", pic):
            ok["pictos"].append((fz, apto, (xp, y - sym - 3 - pz / 2), pz))
            xp += pz * 1.1
    else:
        xx = xl
        for fz, apto in zip("ABC", pic):
            if fz in cls:
                ok["simbolos"].append((fz, (xx + sym / 2, y - max(sym, pz) / 2), sym))
            xx += sym * 1.2 + 1
            ok["pictos"].append((fz, apto, (xx + pz / 2, y - max(sym, pz) / 2), pz))
            xx += pz + 4
    y_e = H - (d["z_enc"] + d["z_tit"] + d["z_ins"] + d["z_cls"])
    ne = len(d["e_lin"])
    ok["bandas"].append((sg.box(xa, y_e - (ne - 1) * d["he"] * 1.4 - d["he"] * 1.2, xb, y_e + d["he"] * 0.3),
                         _banda_electrico(m)[0]))
    y = y_e - (ne + len(d["ley"])) * d["he"] * 1.4 - 2
    nl = logos(m)
    paso = u / len(nl)
    for i, nom in enumerate(nl):
        ok["logos"].append((nom, (xl + paso * (i + 0.5), y - 2 - d["lg"] / 2), d["lg"]))
    return ok


def placa(h, m, zona, W, Wa, H):
    """Dibuja la etiqueta desarrollada ((W + 2 Wa) × H mm reales) dentro de zona a la mayor escala normal, en color:
    encabezado de marca en el color del agente, franja INSTRUCCIONES amarilla con los números de paso en rojo,
    ilustraciones, símbolos de clase (IRAM 3550 5.2.5.3), pictogramas (NFPA 10 anexo B), franja de aptitud
    eléctrica, logos y pie (relevamiento Georgia / Melisam / De León)."""
    d = disposicion(m, W, Wa)
    col = colores(m)
    Wt = W + 2 * Wa
    x0, y0, x1, y1 = zona
    esc = next(s for s in (1.0, 0.5, 0.4, 0.2, 0.1) if Wt * s <= x1 - x0 - 18 and H * s <= y1 - y0 - 20)
    w, hh = Wt * esc, H * esc
    ox, oy = (x0 + x1) / 2 - w / 2, (y0 + y1 - 10) / 2 - hh / 2 + 3
    e = esc
    top = oy + hh
    xa, xb = ox + Wa * e, ox + (Wa + W) * e                 # límites del panel central (arco 108°)
    el = elementos(m, d)
    P = lambda p: (ox + p[0] * e, oy + p[1] * e)            # noqa: E731 (mm reales de la etiqueta -> papel)
    for g, rgb in el["bandas"]:
        h.relleno(_tf(g, (ox, oy), e), rgb)
    h.rect(ox, oy, ox + w, top, "01-VISIBLE")
    yp = oy + d["z_pie"] * e
    h.linea((xa, yp), (xa, top), "08-FINA")
    h.linea((xb, yp), (xb, top), "08-FINA")
    h.texto(f"R1 ETIQUETA DESARROLLADA {_n(Wt, 0)} × {_n(H, 0)} mm (panel central {_n(W, 0)} = arco 108° + alas "
            f"{_n(Wa, 0)}) - ESC. {'1:1' if esc == 1 else '1:' + _n(1 / esc, 1)}", ((x0 + x1) / 2, y1 - 3), 2.5,
            A.MIDDLE_CENTER)
    cx = (xa + xb) / 2
    xl = xa + 3 * e
    u = (W - 6) * e
    y = top - 3 * e
    # encabezado: marca + tipo (zona 2 + 3° a)
    h.grafica("FLAMA" if _propio(m) else "MARCA DEL FABRICANTE", (cx, y), d["hm"] * e * (1 if _propio(m) else 0.45),
              A.TOP_CENTER, rgb=col["enc_txt"])
    y -= (d["hm"] + 2) * e
    for ln in d["t_lin"]:
        h.grafica(ln, (cx, y), d["hti"] * e, A.TOP_CENTER, rgb=col["enc_txt"])
        y -= d["hti"] * 1.4 * e
    y = top - d["z_enc"] * e
    h.grafica("INSTRUCCIONES", (cx, y - (d["z_tit"] - 1) / 2 * e), d["htit"] * e, A.MIDDLE_CENTER, rgb=col["ins_txt"])
    y -= d["z_tit"] * e
    # pasos: número en rojo, texto en negro
    hl = d["hl"] * e

    def renglon(ln, x_, y_, primero):
        if primero and ln.strip().isdigit():
            h.grafica(ln, (x_, y_), hl, A.TOP_LEFT, rgb=L.ROJO)
        elif primero and " " in ln and ln.split(" ", 1)[0].isdigit():
            num, resto = ln.split(" ", 1)
            h.grafica(num, (x_, y_), hl, A.TOP_LEFT, rgb=L.ROJO)
            h.grafica(resto, (x_ + L.ancho_texto(num + " ", hl), y_), hl, A.TOP_LEFT, rgb=L.NEGRO)
        else:
            h.grafica(ln, (x_, y_), hl, A.TOP_LEFT, rgb=L.NEGRO)

    if d["cols"]:
        cw = u / len(d["p_lin"])
        for i, lns in enumerate(d["p_lin"]):
            xc_ = xl + cw * i
            for k, ln in enumerate(lns):
                renglon(ln, xc_ + 1 * e, y - k * hl * 1.4, k == 0)
            if i:
                h.linea((xc_, y + 1 * e), (xc_, y - d["z_ins"] * e + 2 * e), "08-FINA")
    else:
        yy = y
        for i, lns in enumerate(d["p_lin"]):
            for k, ln in enumerate(lns):
                renglon(ln, xl, yy - k * hl * 1.4, k == 0)
            yy -= (max(d["ill"] * 0.75, len(lns) * d["hl"] * 1.4) + 2) * e
    for c_, iw, ih, paso in el["ilus"]:
        _ilustracion(h, P(c_), iw * e, ih * e, paso, m)
    y -= d["z_ins"] * e
    h.linea((xa, y), (xb, y), "08-FINA")
    # clases
    h.grafica("PARA FUEGOS CLASE", (xl, y - 0.6 * e), d["ht"] * e, A.TOP_LEFT, rgb=L.NEGRO)
    for c_, p_, s_ in el["simbolos"]:
        simbolo(h, c_, P(p_), s_ * e)
    for fz, apto, p_, s_ in el["pictos"]:
        pictograma(h, P(p_), s_ * e, fz, apto)
    if el["texto_dk"]:
        h.grafica({"D": "METALES COMBUSTIBLES", "K": "ACEITES Y GRASAS DE COCINA"}["D" if "D" in clases(m) else "K"],
                  P(el["texto_dk"]), d["ht"] * e, A.MIDDLE_LEFT, rgb=L.NEGRO)
    y = top - (d["z_enc"] + d["z_tit"] + d["z_ins"] + d["z_cls"]) * e
    t_ele = _banda_electrico(m)[1]
    for ln in d["e_lin"]:
        h.grafica(ln, (cx, y), d["he"] * e, A.TOP_CENTER, rgb=t_ele)
        y -= d["he"] * 1.4 * e
    for ln in d["ley"]:
        h.grafica(ln, (cx, y), d["he"] * e, A.TOP_CENTER, rgb=L.ROJO)
        y -= d["he"] * 1.4 * e
    for nom, p_, s_ in el["logos"]:
        _logo(h, nom, P(p_), s_ * e)
    # alas
    ht = d["ht"] * e
    for titulo, lns, x_ in zip(ALAS, (d["i_lin"], d["d_lin"]), (ox + 2 * e, xb + 2 * e)):
        yy = top - 2 * e
        h.grafica(titulo, (x_, yy), _titulo_ala(d, titulo) * e, A.TOP_LEFT, rgb=col["enc_txt"])
        yy = top - 3 * e - ht * 1.6
        for ln in lns:
            if ln:
                h.grafica(ln, (x_, yy), ht, A.TOP_LEFT, rgb=L.NEGRO)
            yy -= ht * 1.4
    yy = yp - 1.2 * e
    for ln in d["f_lin"]:
        h.grafica(ln, (ox + w / 2, yy), ht, A.TOP_CENTER, rgb=col["enc_txt"])
        yy -= ht * 1.4
    h.cota_lineal((ox, oy), (ox + w, oy), (ox, oy - 7), 0, 1 / esc)
    h.cota_lineal((xa, top), (xb, top), (xa, top + 4), 0, 1 / esc)
    h.cota_lineal((ox + w, oy), (ox + w, top), (ox + w + 7, oy), 90, 1 / esc)
    ga = _n(math.degrees(Wa / (W / math.radians(M.ARCO_PLACA))), 0)
    h.texto(f"ala izq. ({ga}°)", ((ox + xa) / 2, oy - 2), 1.6, A.TOP_CENTER, "08-FINA")
    h.texto(f"ala der. ({ga}°)", ((xb + ox + w) / 2, oy - 2), 1.6, A.TOP_CENTER, "08-FINA")
    return esc, d["hl"]


PEGADO = {"etiqueta": 2.0, "oblea_pba": 2.0, "sello_iram": 2.0, "tarjeta_caba": 2.0, "etiqueta_serie": 2.0,
          "etiqueta_rec": 2.0, "faja_garantia": 1.0, "suncho": 1.0}


def colorear(h, piezas, T, res, color_de, pegado=PEGADO, vista="anterior"):
    """Rellena la parte visible de cada pieza en la vista (z-buffer) con color_de(clave); None = no se pinta
    (pieza interior). Devuelve las regiones en papel."""
    Tx, Ty, f = T
    claves = [k for k in piezas if color_de(k) is not None]
    reg = V.regiones_visibles(piezas, claves, vista, res, sesgo=pegado)
    papel = {k: affinity.affine_transform(g, [f, 0, 0, f, Tx, Ty]) for k, g in reg.items()}
    for k, g in papel.items():
        h.relleno(g, color_de(k))
    return papel


def vista_color(h, m, piezas, T, res):
    """Colorea la vista anterior pieza por pieza (sólo la parte visible de cada una, z-buffer) y dibuja sobre la
    etiqueta del cuerpo sus bandas, símbolos, pictogramas y logos; sobre el manómetro, el cuadrante con las zonas
    de recarga / operable / sobrecarga; sobre la oblea, el anillo."""
    Tx, Ty, f = T
    col = colores(m)
    papel = colorear(h, piezas, T, res, lambda k: color_pieza(k, col))
    W, H, z0, R, xc, yc = M.placa_dim(m, piezas)
    Wa = M.ala_dim(R)
    Wt = W + 2 * Wa
    if "etiqueta" in papel:
        d = disposicion(m, W, Wa)
        el = elementos(m, d)
        lim = math.pi / 2 * 0.999

        def cil(x, y, z=None):
            th = np.clip((np.asarray(x, float) - Wt / 2) / R, -lim, lim)
            return Tx + (xc + R * np.sin(th)) * f, Ty + (z0 + np.asarray(y, float)) * f

        geo = lambda g: shp_transform(cil, g.segmentize(4.0))     # noqa: E731
        zona = papel["etiqueta"]
        for g, rgb in el["bandas"]:
            h.relleno(geo(g).intersection(zona), rgb)
        for c_, p_, s_ in el["simbolos"]:
            h.relleno(geo(_forma_simbolo(c_, p_[0], p_[1], s_)[0]).intersection(zona), COLOR_CLASE[c_])
        for fz, apto, p_, s_ in el["pictos"]:
            h.relleno(geo(sg.box(p_[0] - s_ / 2, p_[1] - s_ / 2, p_[0] + s_ / 2, p_[1] + s_ / 2)).intersection(zona),
                      L.AZUL if apto else L.NEGRO)
        for nom, p_, s_ in el["logos"]:
            fondo = {"SELLO IRAM": L.AZUL, "OPDS": L.VERDE, "GCBA": L.AMARILLO, "QR": L.NEGRO}.get(nom, (0, 70, 140))
            h.relleno(geo(sg.Point(p_).buffer(s_ / 2, 24)).intersection(zona), fondo)
        for c_, iw, ih, _ in el["ilus"]:
            h.relleno(geo(sg.box(c_[0] - iw / 2, c_[1] - ih / 2, c_[0] + iw / 2, c_[1] + ih / 2)).intersection(zona),
                      (235, 235, 235))
        xm, ym = cil(Wt / 2, H - 3)
        h.grafica("FLAMA" if _propio(m) else "MARCA", (xm, ym), max(1.0, d["hm"] * f * (1 if _propio(m) else 0.6)),
                  A.TOP_CENTER, rgb=col["enc_txt"])
    if "manometro" in papel:
        g = papel["manometro"]
        g = max(getattr(g, "geoms", [g]), key=lambda q: q.area)
        cen = polylabel(g, 0.05)
        r = g.exterior.distance(cen) * 0.92
        for a0, a1, rgb in ((-135, -25, L.ROJO), (-25, 25, L.VERDE), (25, 135, L.ROJO)):
            arco = [(cen.x + r * 0.78 * math.sin(math.radians(a)), cen.y + r * 0.78 * math.cos(math.radians(a)))
                    for a in range(a0, a1 + 1, 5)]
            h.relleno(sg.LineString(arco).buffer(r * 0.14, cap_style=2), rgb)
        h.relleno(_trazo([(cen.x, cen.y), (cen.x + r * 0.6 * math.sin(0.15), cen.y + r * 0.6 * math.cos(0.15))],
                         r * 0.08), L.NEGRO)
    if "oblea_pba" in papel:
        g = papel["oblea_pba"]
        h.relleno(g.difference(g.buffer(-max(0.3, 0.18 * math.sqrt(g.area / math.pi)))), VIOLETA)
    if "sello_iram" in papel:
        x0_, y0_, x1_, y1_ = papel["sello_iram"].bounds
        rr = min(x1_ - x0_, y1_ - y0_) * 0.22
        h.relleno(sg.Point(x1_ - rr * 1.3, y1_ - rr * 1.3).buffer(rr, 24).intersection(papel["sello_iram"]), L.AZUL)
    if "tarjeta_caba" in papel:
        x0_, y0_, x1_, y1_ = papel["tarjeta_caba"].bounds
        h.relleno(sg.box(x0_, y1_ - (y1_ - y0_) * 0.2, x1_, y1_).intersection(papel["tarjeta_caba"]), (225, 225, 225))
    return papel


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
    f = min((zx1 - zx0 - 30) / (ex[2] - ex[0]), (zy1 - zy0 - 30) / (ex[3] - ex[1]))   # deja libre el título
    f = next(s for s in (1 / 2, 1 / 5, 1 / 10, 1 / 20) if s <= f)
    Tx = (zx0 + zx1) / 2 - (ex[0] + ex[2]) / 2 * f
    Ty = zy0 + 24 - ex[1] * f
    cuerda = 2 * R * math.sin(math.radians(M.ARCO_PLACA / 2))
    # vista en color: parte visible de cada pieza con su color real y la etiqueta impresa sobre el cuerpo
    vista_color(h, m, piezas, (Tx, Ty, f), 0.1 / f)
    h.prims(proy["anterior"]["vis"], "01-VISIBLE", (Tx, Ty, f))
    zo = z0 - 3 - M.OBLEA_PBA
    h.cota_lineal((Tx + (xc + cuerda / 2) * f, Ty), (Tx + (xc + cuerda / 2) * f, Ty + z0 * f),
                  (Tx + (xc + R) * f + 10, Ty), 90, 1 / f)
    h.cota_lineal((Tx + (xc + cuerda / 2) * f, Ty + z0 * f), (Tx + (xc + cuerda / 2) * f, Ty + (z0 + H) * f),
                  (Tx + (xc + R) * f + 10, Ty), 90, 1 / f)
    h.cota_lineal((Tx + (xc - cuerda / 2) * f, Ty + z0 * f), (Tx + (xc + cuerda / 2) * f, Ty + z0 * f),
                  (Tx, Ty - 8), 0, 1 / f)
    h.texto(f"cuerda {_n(cuerda, 0)} = panel central (arco 108° = {_n(W, 0)} mm desarrollados); colores reales",
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
    nota_r2 = partir(("Carro: etiqueta del lado de la manija, hacia el operador; manga, ganchos y pata adelante. "
                      if m.familia == "rodante" else "") +
                     "Etiqueta de frente sobre el eje del manómetro; oblea inmediatamente debajo, sin otra "
                     "identificación entre ambas (Res. 522/07 an. 6); estampilla IRAM al costado; etiqueta GS1 a 180° "
                     "(posterior).", zx1 - zx0, 1.8, 4)
    for i, ln in enumerate(nota_r2):
        h.texto(ln, ((zx0 + zx1) / 2, zy0 + 2.5 + 2.6 * (len(nota_r2) - 1 - i)), 1.8, A.MIDDLE_CENTER)
    # R3 símbolos acotados
    sx0, sy0, sx1, sy1 = X0 + 436, Y0 + 290, X1 - 4, Y1 - 14
    h.texto("R3 SÍMBOLOS (IRAM 3550 5.2.5) Y PICTOGRAMAS (NFPA 10)", ((sx0 + sx1) / 2, sy1 - 3), 2.5, A.MIDDLE_CENTER)
    cls = clases(m)
    xs = sx0 + 14
    for c in cls:
        simbolo(h, c, (xs, sy1 - 26), 14)
        h.texto({"A": "verde 01-1-150", "B": "rojo 03-1-050", "C": "azul 08-1-070", "D": "amarillo 05-1-040",
                 "K": "negro (hexágono)"}[c], (xs, sy1 - 38), 1.8, A.MIDDLE_CENTER)
        xs += 26
    h.texto("Alto mín. 12 mm; trazo e = alto/13 (A), alto/12 (B, D), alto/14 (C)", (sx0 + 2, sy1 - 46), 1.8)
    pic = pictogramas(m)
    if pic:
        xs = sx0 + 14
        for fz, ok in zip("ABC", pic):
            pictograma(h, (xs, sy0 + 28), 18, fz, ok)
            h.texto({"A": "sólido", "B": "líquido", "C": "eléctrico"}[fz], (xs, sy0 + 17.5), 1.8, A.TOP_CENTER)
            xs += 26
        h.texto("Pictogramas NFPA 10 anexo B, mín. 18 × 18 mm: figura blanca", (sx0 + 2, sy0 + 9), 1.8)
        h.texto("sobre azul = apto; sobre negro con barra roja = no apto.", (sx0 + 2, sy0 + 5.5), 1.8)
    else:
        h.texto("Clases D/K: símbolo del producto (IRAM 3534 no prevé pictograma)", (sx0 + 2, sy0 + 20), 1.8)
    # R4 oblea PBA
    ox_, oy_ = X0 + 436, Y0 + 195
    h.texto("R4 OBLEA FABRICACIÓN PBA (Res. 522/07)", ((ox_ + X1 - 4) / 2, oy_ + 90), 2.5, A.MIDDLE_CENTER)
    c4 = (ox_ + 30, oy_ + 45)
    h.relleno(sg.Point(c4).buffer(23, 64).difference(sg.Point(c4).buffer(16, 64)), VIOLETA)
    h.relleno(sg.Point(c4).buffer(16, 64), L.LILA)
    for k in range(10):                                           # guilloche
        onda = [(c4[0] + (6 + 9 * (k % 2) + 1.2 * math.sin(math.radians(6 * a))) * math.cos(math.radians(a + 18 * k)),
                 c4[1] + (6 + 9 * (k % 2) + 1.2 * math.sin(math.radians(6 * a))) * math.sin(math.radians(a + 18 * k)))
                for a in range(0, 361, 6)]
        ln = h.msp.add_lwpolyline(onda, dxfattribs={"layer": "13-GRAFICA"})
        ln.rgb = (190, 160, 220)
    h.relleno(sg.box(c4[0] - 12, c4[1] + 1, c4[0] + 12, c4[1] + 8), NARANJA)
    for rr in (23, 16):
        h.msp.add_circle(c4, rr, dxfattribs={"layer": "01-VISIBLE"})
    h.grafica("ÚNICO SELLO OFICIAL", (c4[0], c4[1] + 19.5), 1.15, A.MIDDLE_CENTER, rgb=L.BLANCO)
    h.grafica("LEY 19.587", (c4[0], c4[1] - 19.5), 1.15, A.MIDDLE_CENTER, rgb=L.BLANCO)
    h.grafica("DPS", (c4[0] - 19.5, c4[1]), 1.4, A.MIDDLE_CENTER, rot=90, rgb=L.BLANCO)
    h.grafica("DPS", (c4[0] + 19.5, c4[1]), 1.4, A.MIDDLE_CENTER, rot=-90, rgb=L.BLANCO)
    h.grafica("PROVINCIA DE BUENOS AIRES", (c4[0], c4[1] + 11), 1.3, A.MIDDLE_CENTER)
    h.rect(c4[0] - 12, c4[1] + 1, c4[0] + 12, c4[1] + 8, "08-FINA")
    h.grafica("PRÓXIMA REVISIÓN DE CARGA", (c4[0], c4[1] + 6.5), 1.1, A.MIDDLE_CENTER)
    h.grafica("MM / AAAA", (c4[0], c4[1] + 3), 1.6, A.MIDDLE_CENTER)
    h.grafica("1H0 0000000", (c4[0], c4[1] - 5), 2.0, A.MIDDLE_CENTER, rgb=L.ROJO)
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
    h.relleno(sg.box(sx, sy, sx + ew, sy + eh), L.ROSA)
    for k in range(9):                                            # guilloche
        onda = [(sx + 0.5 + t * (ew - 1) / 60, sy + 2 + k * (eh - 4) / 8 + 1.1 * math.sin(t / 60 * 4 * math.pi + k))
                for t in range(61)]
        ln = h.msp.add_lwpolyline(onda, dxfattribs={"layer": "13-GRAFICA"})
        ln.rgb = (225, 150, 180)
    h.relleno(sg.Point(sx + ew - 11, sy + eh - 11).buffer(8, 48), L.AZUL)
    h.rect(sx, sy, sx + ew, sy + eh, "01-VISIBLE")
    h.grafica("A 26 000000", (sx + 4, sy + eh / 2), 2.4, A.MIDDLE_CENTER, rot=90, rgb=L.ROJO)
    for i, t in enumerate(["leyenda de conformidad con", "norma IRAM (lote aprobado,", "fabricación bajo control)"]):
        h.grafica(t, (sx + 9, sy + eh - 4 - 3 * i), 1.5)
    h.grafica("INSTITUTO ARGENTINO DE", (sx + 9, sy + eh - 15), 1.6, rgb=L.AZUL)
    h.grafica("NORMALIZACIÓN Y CERTIF.", (sx + 9, sy + eh - 18), 1.6, rgb=L.AZUL)
    for i, t in enumerate(["advertencia: la numeración", "identifica matafuego y", "fabricante; adulteración", "= acciones legales"]):
        h.grafica(t, (sx + 9, sy + 13 - 3 * i), 1.4)
    h.msp.add_circle((sx + ew - 11, sy + eh - 11), 8, dxfattribs={"layer": "08-FINA"})
    h.grafica("SELLO", (sx + ew - 11, sy + eh - 10), 1.4, A.MIDDLE_CENTER, rgb=L.BLANCO)
    h.grafica("IRAM", (sx + ew - 11, sy + eh - 12.5), 1.6, A.MIDDLE_CENTER, rgb=L.BLANCO)
    qr(h, (sx + ew - 11, sy + 9), 12, 11)
    _bloque(h, [f"≈ {_n(ew, 0)} × {_n(eh, 0)}, fondo guilloche rosa, sello azul; n° vertical",
                "letra + año + n° (relevado «A 25 1111053»). La provee IRAM",
                "numerada sólo al licenciatario; se aplica con etiquetadora.",
                "Alternativa (certifica Bureau Veritas): etiqueta naranja",
                "«MODELO APROBADO» con n° y QR."], ex_ + 2, ey_ + 13, 1.8, 2.9, ancho=84)
    # R6 precinto y faja de garantía
    px, py = X0 + 472, Y0 + 125
    h.texto("R6 PRECINTO Y FAJA DE GARANTÍA", (px + 42, py + 66), 2.5, A.MIDDLE_CENTER)
    fab = "del fabricante" if rev else "FLAMA"
    h.relleno(sg.Point(px + 14, py + 46).buffer(9.9, 48).difference(sg.Point(px + 14, py + 46).buffer(8.1, 48)), CROMO)
    h.relleno(sg.box(px + 22, py + 45.1, px + 46, py + 46.9), CROMO)
    h.msp.add_circle((px + 14, py + 46), 9, dxfattribs={"layer": "01-VISIBLE"})
    h.linea((px + 23, py + 46), (px + 46, py + 46), "01-VISIBLE")
    h.relleno(sg.box(px + 32, py + 42, px + 42, py + 50), L.AMARILLO)      # precinto plástico de color
    h.rect(px + 32, py + 42, px + 42, py + 50, "01-VISIBLE")
    h.grafica("FAB." if rev else "FLAMA", (px + 37, py + 47.2), 1.2, A.MIDDLE_CENTER)
    h.grafica("L 0000", (px + 37, py + 44.5), 1.2, A.MIDDLE_CENTER)
    fx, fy = px + 52, py + 34
    fw, fh = M.FAJA_GARANTIA
    fw, fh = fw * 0.5, fh * 0.5                     # esc. 1:2 (IRAM 4505)
    zona_r = sg.box(fx, fy + fh * 0.5, fx + fw, fy + fh)
    for k in range(-6, 12):                                       # franjas a 45° rojo / blanco
        x_ = fx + k * 2.4
        banda = sg.Polygon([(x_, fy + fh * 0.5), (x_ + 1.2, fy + fh * 0.5), (x_ + 1.2 + fh, fy + fh * 1.5),
                            (x_ + fh, fy + fh * 1.5)]).intersection(zona_r)
        if not banda.is_empty:
            h.relleno(banda, L.ROJO)
    h.rect(fx, fy, fx + fw, fy + fh, "01-VISIBLE")
    for k, t in enumerate(("LA ROTURA TOTAL", "DE ESTA CINTA", "INTERRUMPE LA GARANTÍA")):
        h.grafica(t, (fx + fw / 2, fy + fh * (0.45 - 0.1 * k)), 0.9, A.MIDDLE_CENTER, rgb=L.NEGRO)
    h.grafica("ATENCIÓN", (fx + fw / 2, fy + 1.5), 1.8, A.BOTTOM_CENTER, rgb=L.ROJO)
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
    col = colores(m)
    h.relleno(sg.box(mx + 3, my + 42, mx + 82, my + 52), col["cuerpo"])      # grabado bajo la pintura del cuerpo
    h.rect(mx + 3, my + 42, mx + 82, my + 52, "01-VISIBLE" if not rev else "08-FINA")
    oscuro = (90, 10, 15) if col["cuerpo"] == ROJO_CUERPO else (60, 62, 66)
    h.grafica(txt, (mx + 38, my + 47), 2.4, A.MIDDLE_CENTER, rgb=oscuro)
    if not rev:
        h.rect(mx + 66, my + 43.5, mx + 81, my + 50.5, "01-VISIBLE")
        h.grafica("DPS", (mx + 73.5, my + 47), 3.0, A.MIDDLE_CENTER, rgb=oscuro)
    _bloque(h, lin, mx + 3, my + 38, 1.8, 3.2, ancho=83)
    gw, gh = M.ETIQUETA_SERIE
    gx, gy = mx + 6, my + 6
    h.relleno(sg.box(gx, gy, gx + gw * 0.5, gy + gh * 0.5), L.BLANCO)
    h.rect(gx, gy, gx + gw * 0.5, gy + gh * 0.5, "01-VISIBLE")
    qr(h, (gx + gw * 0.25, gy + gh * 0.3), gh * 0.35, 23)
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
    h.relleno(sg.box(bx0, by0, bx0 + tw_ * s8, by0 + th_ * s8), L.BLANCO)
    h.relleno(sg.box(bx0, by0 + th_ * s8 - 3.4, bx0 + tw_ * s8, by0 + th_ * s8), (225, 225, 225))
    h.relleno(sg.box(bx0 + tw_ * s8 - 15, by0 + th_ * s8 - 3.1, bx0 + tw_ * s8 - 1, by0 + th_ * s8 - 0.3), L.AMARILLO)
    h.rect(bx0, by0, bx0 + tw_ * s8, by0 + th_ * s8, "01-VISIBLE")
    h.grafica("Tarjeta de Identificación de Extintor", (bx0 + 1.5, by0 + th_ * s8 - 1.5), 1.3, A.TOP_LEFT)
    h.grafica("AGC · BA Ciudad", (bx0 + tw_ * s8 - 1.5, by0 + th_ * s8 - 1.5), 1.2, A.TOP_RIGHT, rgb=L.NEGRO)
    for i, t in enumerate(["Domicilio instalación", "Empresa fabricante", "Empresa recargadora", "Venc. mantenim.",
                           "Fecha fab. / N° tarjeta", "Venc. VU / Agente", "Capacidad / Extintor N°"]):
        h.grafica(t + ":", (bx0 + 1.5, by0 + th_ * s8 - 5 - 3.05 * i), 1.1)
    qr(h, (bx0 + tw_ * s8 - 9, by0 + 10), 14, 31)
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
           encabezado="CONTENIDO DE LA ETIQUETA (IRAM 3534 + norma del producto + relevamiento de mercado)",
           fondo=colores(m)["enc"], fondo_txt=colores(m)["enc_txt"])
    h.texto(f"Letra de instrucciones {_n(hl, 1)} mm (IRAM 3534 2.2.4.3: masa total "
            f"{'< 9 kg: 3-8 mm' if _masa(m) < 9 else '≥ 9 kg: 6,5-10 mm'}); mayúsculas IRAM 4503, color en contraste. "
            "Ubic.: C panel central ≤ 108°, I/D alas, P pie. Vinilo laminado ensayado a adherencia ≥ 0,35 N/mm y "
            "abrasión 100 pasadas (IRAM 3534 cap. 3).", (X0 + 6, Y0 + 4), 1.7)
    return h
