"""Capturas marcadas de normas y fichas para el Word «Justificación del BOM».

Recorta sólo la cláusula o la tabla citada (las normas no se transcriben ni se suben al repo; los recortes dejan
afuera los márgenes con los datos de la licencia), marca en rojo el dato que se toma y escribe figs/N??.png y
capturas.json (lo lee word_bom.js).

Uso: python capturas.py <carpeta de normas> <carpeta de fichas DEMSA>
"""
import json
import os
import sys

import pymupdf
from PIL import Image, ImageDraw, ImageFont

AQUI = os.path.dirname(os.path.abspath(__file__))
NOR, FIC = sys.argv[1], sys.argv[2]
OUT = os.path.join(AQUI, "figs")
Z = 2.0                                  # 144 dpi
ROJO = (220, 0, 0)
N3517 = os.path.join(NOR, "NORMAS PARA RECARGAS", "IRAM-3517-2.2020pdf.pdf")
N3523 = os.path.join(NOR, "NORMAS PARA PRODUCCION", "IRAM-3523.pdf")
N2533 = os.path.join(NOR, "IRAM COMPLETO", "796656234-IRAM-2533-Cilindros-de-Dioxido-de-Carbono.pdf")
N3694 = os.path.join(NOR, "NUEVAS", "IRAM-3694-5-7.pdf")
X0, X1 = 40, 562                         # caja de texto de la IRAM 3517-2 (páginas pares e impares)


def _y(pdf, pag, texto, n=0, fin=False):
    r = pymupdf.open(pdf)[pag - 1].search_for(texto)[n]
    return r.y1 if fin else r.y0


def parte(pdf, pag, rect, marcas=(), rot0=False):
    """rect en puntos; marcas: lista de (n, texto a buscar o rect, índice de la ocurrencia dentro del recorte)."""
    return dict(pdf=pdf, pag=pag, rect=rect, marcas=marcas, rot0=rot0)


def render(partes):
    imgs, cajas, dy = [], [], 0
    for p in partes:
        pg = pymupdf.open(p["pdf"])[p["pag"] - 1]
        if p["rot0"]:
            pg.set_rotation(0)
        clip = pymupdf.Rect(*p["rect"])
        pix = pg.get_pixmap(matrix=pymupdf.Matrix(Z, Z), clip=clip)
        imgs.append(Image.frombytes("RGB", (pix.width, pix.height), pix.samples))
        for n, q, k in p["marcas"]:
            if isinstance(q, str):
                rs = [r for r in pg.search_for(q) if clip.contains(r) or clip.intersects(r)]
                assert len(rs) > k, f"no está en el recorte: {q}"
                r = rs[k]
            else:
                r = pymupdf.Rect(*q)
            cajas.append((n, ((r.x0 - clip.x0) * Z - 5, (r.y0 - clip.y0) * Z + dy - 4, (r.x1 - clip.x0) * Z + 5,
                              (r.y1 - clip.y0) * Z + dy + 4)))
        dy += pix.height + 12
    im = Image.new("RGB", (max(i.width for i in imgs), dy - 12), (255, 255, 255))
    y = 0
    for i in imgs:
        im.paste(i, (0, y))
        y += i.height + 12
    d = ImageDraw.Draw(im)
    try:
        fnt = ImageFont.truetype("DejaVuSans-Bold.ttf", 22)
    except OSError:
        fnt = ImageFont.load_default()
    for n, (x0, y0, x1, y1) in cajas:
        d.rectangle((x0, y0, x1, y1), outline=ROJO, width=4)
        cx, cy = max(x0 - 2, 17), max(y0 - 2, 17)
        d.ellipse((cx - 16, cy - 16, cx + 16, cy + 16), fill=ROJO)
        d.text((cx, cy), str(n), fill=(255, 255, 255), font=fnt, anchor="mm")
    return im


def _fin_texto(pdf, pag, y0):
    """Pie del último bloque de texto de la página debajo de y0 (sin el pie con los datos de la licencia)."""
    return max(b[3] for b in pymupdf.open(pdf)[pag - 1].get_text("blocks") if y0 < b[3] < 785) + 4


def r3517(pag, y0, y1, marcas=()):
    return parte(N3517, pag, (X0, y0, X1, _fin_texto(N3517, pag, y0) if y1 is None else y1), marcas)


P = N3517
CAPTURAS = [
    dict(id="N01", titulo="IRAM 3517-2:2020, 9.4.12 y tabla 3: condiciones de funcionamiento", tipo="Norma",
         partes=[parte(P, 37, (50, _y(P, 37, "9.4.12 Funcionamiento") - 4, 562, 772),
                       [(1, "+100 g", 0), (2, "+300 g", 0), (3, "- 5%", 0), (4, (236, 588, 362, 648), 0)]),
                 parte(P, 38, (40, _y(P, 38, "Tabla 3 (fin)") - 4, 548, _y(P, 38, "9.4.13 Precintos") - 6),
                       [(5, (224, 125, 354, 156), 0), (6, (224, 283, 354, 335), 0), (7, (224, 399, 354, 457), 0)])],
         marcas=["Polvo manual 1 y 2,5 kg: 0 / +100 g", "Polvo manual 5 y 10 kg: 0 / +300 g", "CO₂: 0 / −5 %",
                 "Gases limpios: 0 / −2 % (1 y 2,5 kg) y 0 / −3 % (5 y 10 kg)",
                 "Agua (y AFFF en las filas siguientes): ±3 %", "Polvo sobre ruedas: ±3 %", "Sales de potasio: 0 / +3 %"]),
    dict(id="N02", titulo="IRAM 3517-2:2020, 9.4.9 y tabla 2: gas impulsor según el tipo de extintor", tipo="Norma",
         partes=[r3517(36, _y(P, 36, "9.4.9 Gas Impulsor") - 4, 640),
                 r3517(37, _y(P, 37, "Tabla 2 - Gas impulsor") - 6, _y(P, 37, "9.4.10 Ensayo de pérdidas") - 6,
                       [(1, "Nitrógeno seco", 0), (2, "Nitrógeno seco o aire comprimido", 0),
                        (3, "HCFC Mezcla B: sólo admite argón", 0)])],
         marcas=["Polvo: nitrógeno seco", "Agua, AFFF y sales de potasio: nitrógeno o aire comprimido",
                 "HCFC Mezcla B: sólo argón"]),
    dict(id="N03", titulo="IRAM 3517-2:2020, anexo E: guía de control y mantenimiento (CO₂, polvo, agua, AFFF)",
         tipo="Norma",
         partes=[parte(P, 81, (58, 50, 790, 500), [(1, "Como máximo", 0), (2, "Cambiar el conjunto", 0),
                                                   (3, "Cambiar cada vez", 0), (4, "Verificar cada", 0),
                                                   (5, "Como máximo", 2), (6, "Cambiar cada", 1)], rot0=True)],
         marcas=["Prueba hidráulica cada 5 años como máximo (CO₂, polvo)", "CO₂: disco de seguridad nuevo cada vez que "
                 "se descarga", "CO₂: marbete cada vez que se interviene", "Polvo: control del agente cada año (9.9.3)",
                 "Agua y AFFF: prueba hidráulica cada 2 años", "Agua y AFFF: carga nueva cada año, previo lavado"]),
    dict(id="N04", titulo="IRAM 3517-2:2020, anexo E (fin): rodantes, gases limpios y acetato de potasio",
         tipo="Norma",
         partes=[parte(P, 82, (58, 60, 790, 480), [(1, "Como máximo", 2), (2, "Anualmente se", 6),
                                                   (3, "Cambiar cada", 3), (4, "Como máximo", 5)], rot0=True)],
         marcas=["Polvo sobre ruedas: 5 años", "Gases limpios: control anual (9.9.2)",
                 "Acetato de potasio: carga nueva cada año (9.9.1.9)", "Acetato de potasio: prueba hidráulica cada 2 años"]),
    dict(id="N05", titulo="IRAM 3517-2:2020, 8.2 y 8.3.3.1: control trimestral y etiqueta de control", tipo="Norma",
         partes=[r3517(29, _y(P, 29, "8.2  Frecuencia") - 4, _y(P, 29, "8.2  Frecuencia") + 52,
                       [(1, "cuatro", 0)]),
                 r3517(31, _y(P, 31, "8.3.3.1") - 4, _y(P, 31, "Figura 7 - Etiqueta de control", fin=True) + 4,
                       [(2, "color celeste, de 35 mm de alto por 50 mm", 0)])],
         marcas=["Control como mínimo cuatro veces por año", "Etiqueta celeste de 35 × 50 mm (figura 7)"]),
    dict(id="N06", titulo="IRAM 3517-2:2020, 9.2.1 y 9.2.2: mantenimiento anual y recarga", tipo="Norma",
         partes=[r3517(33, _y(P, 33, "9.2.1 Mantenimiento") - 4, _y(P, 33, "9.3  Procedimientos") - 6,
                       [(1, "frecuencia anual", 0), (2, "después de su utilización", 0)])],
         marcas=["Mantenimiento como mínimo anual", "Recarga después de cada uso"]),
    dict(id="N07", titulo="IRAM 3517-2:2020, 9.4.5: extintores sustitutos", tipo="Norma",
         partes=[r3517(35, _y(P, 35, "9.4.5 Extintores sustitutos") - 4, _y(P, 35, "9.4.6 Conversión") - 6,
                       [(1, "igual clasificación y por lo menos igual capacidad", 0),
                        (2, "40 mm de altura", 0)])],
         marcas=["Igual clasificación y por lo menos igual capacidad", "Faja amarilla de 40 mm como máximo"]),
    dict(id="N08", titulo="IRAM 3517-2:2020, 9.4.13 y 9.4.14: precintos y etiqueta de servicio", tipo="Norma",
         partes=[r3517(38, _y(P, 38, "9.4.13 Precintos") - 4, _y(P, 38, "9.4.13 Precintos") + 38,
                       [(1, "reponer los precintos", 0)]),
                 r3517(39, _y(P, 39, "9.4.14 Etiqueta") - 4, _y(P, 39, "9.4.15 Placa") - 6,
                       [(2, "etiqueta u oblea", 0)])],
         marcas=["Precinto nuevo después del mantenimiento o la recarga", "Etiqueta de servicio en cada extintor"]),
    dict(id="N09", titulo="IRAM 3517-2:2020, 9.6.1: marbete indicador", tipo="Norma",
         partes=[r3517(40, _y(P, 40, "9.6 Marbete indicador") - 4, None, [(1, "retiro de la válvula o desarmado", 0)]),
                 r3517(41, _y(P, 41, "Las características del mencionado") - 4, _y(P, 41, "9.6.2") - 6)],
         marcas=["Marbete sólo cuando se retira la válvula o se desarma el extintor"]),
    dict(id="N10", titulo="IRAM 3517-2:2020, 9.9.1.4: el polvo de un extintor accionado no se reutiliza",
         tipo="Norma",
         partes=[r3517(47, _y(P, 47, "9.9.1.4") - 4, _y(P, 47, "9.9.1.5") - 6, [(1, "no debe ser reutilizado", 0)])],
         marcas=["Recarga después de uso: polvo nuevo"]),
    dict(id="N11", titulo="IRAM 3517-2:2020, 4.4.1 y) z): recuperación cerrada de polvo y gases limpios",
         tipo="Norma",
         partes=[r3517(15, _y(P, 15, "sistema cerrado de recuperación de polvo") - 4,
                       _y(P, 15, "hasta que se vuelva a usar", fin=True) + 4,
                       [(1, "sistema cerrado de recuperación de polvo", 0),
                        (2, "sistema cerrado de recuperación de gases limpios", 0)])],
         marcas=["Polvo recuperado en sistema cerrado con inspección", "Gases limpios recuperados sin ventear"]),
    dict(id="N12", titulo="IRAM 3517-2:2020, 9.9.3.2 y tabla 7: ensayo de extinción del polvo (muestras de gramos)",
         tipo="Norma",
         partes=[r3517(49, _y(P, 49, "9.9.3.2") - 4, _y(P, 49, "9.9.3.3") - 6, [(1, "1,7 g", 0)])],
         marcas=["Masas de ensayo de 1,1 a 1,8 g por disparo"]),
    dict(id="N13", titulo="IRAM 3517-2:2020, anexo F: masa inadecuada → recargar hasta la masa correcta",
         tipo="Norma",
         partes=[r3517(85, _y(P, 85, "Masa del extintor inadecuada") - 40, _y(P, 85, "Recargar hasta la masa correcta",
                                                                              fin=True) + 40,
                       [(1, "Masa del extintor inadecuada", 0), (2, "Recargar hasta la masa correcta", 0)])],
         marcas=["Masa fuera de la tabla 3", "Acción: recargar hasta la masa correcta"]),
    dict(id="N14", titulo="IRAM 3523:1983, 2.2 y 2.3: capacidad y presión de servicio a 20 ± 2 °C", tipo="Norma",
         partes=[parte(N3523, 6, (45, 298, 562, 420), [(1, (54, 361, 476, 380), 0), (2, (54, 387, 557, 416), 0)])],
         marcas=["La capacidad es la masa de polvo", "Presión de servicio a 20 °C ± 2 °C"]),
    dict(id="N15", titulo="IRAM 3523:1983, 4.5 a 4.7: manómetro, tabla II de capacidad y presión de servicio",
         tipo="Norma",
         partes=[parte(N3523, 9, (55, 408, 562, 676), [(1, (73, 413, 557, 450), 0), (2, (99, 510, 519, 643), 0),
                                                       (3, (73, 651, 507, 672), 0)])],
         marcas=["Manómetro según la norma IRAM (IRAM 3533)", "Tabla II: +100 g (1 y 2,5 kg), +300 g (5 y 10 kg)",
                 "Presión de servicio menor de 1,7 MPa"]),
    dict(id="N16", titulo="IRAM 2533:2004, 7.9 y tabla 1: relación de llenado del CO₂", tipo="Norma",
         partes=[parte(N2533, 10, (290, 318, 550, 558), [(1, (293, 322, 472, 376), 0), (2, (295, 507, 472, 553), 0)])],
         marcas=["Relación de llenado según la temperatura máxima", "Elementos contra incendio: 65 °C, 0,68 kg/L"]),
    dict(id="N17", titulo="IRAM 3694:2014, 5.4 a 5.6: manómetro, capacidad y presión de servicio (sales de potasio)",
         tipo="Norma",
         partes=[parte(N3694, 1, (290, 262, 556, 466), [(1, (293, 289, 552, 344), 0), (2, (293, 366, 552, 401), 0),
                                                        (3, (293, 428, 552, 461), 0)])],
         marcas=["Manómetro según IRAM 3533", "Capacidad 6 L +0,3 / −0", "Presión de servicio menor de 1,7 MPa"]),
]
FICHAS = [
    ("F_ABC", "Ficha DEMSA polvo ABC (hoja de seguridad): densidad aparente", "abc-polvo-quimico-seco-deguridad.pdf",
     [(2, (310, 420, 545, 470), [(1, "Densidad aparente", 0)])], ["Densidad aparente > 0,85"]),
    ("F_BC", "Ficha DEMSA polvo BC Púrpura K (hoja de seguridad): densidad aparente",
     "Polvo-BC_Purpura-K_H_seguridad.pdf", [(6, (50, 228, 270, 272), [(1, "Densidad aparente", 0)])],
     ["Densidad aparente > 0,85"]),
    ("F_D", "Ficha DEMSA polvo clase D (hoja de seguridad): densidad aparente", "Polvo_D_H_seguridad.pdf",
     [(3, (48, 428, 300, 468), [(1, "Densidad aparente", 0)])], ["Densidad aparente > 0,85 g/cm³"]),
    ("F_K", "Ficha técnica DEMSA Kitchen (acetato de potasio): densidad", "kitchen-tecnica.pdf",
     [(1, (300, 158, 512, 268), [(1, "Densidad (g/ml a 20", 0)])], ["Densidad 1,300 g/mL a 20 °C"]),
    ("F_AFFF", "Ficha técnica DEMSA 203 MN (AFFF 3 %): concentración y peso específico", "espuma-sintetica-203.pdf",
     [(2, (40, 306, 290, 360), [(1, "Concentración nominal", 0), (2, "Peso espacífico", 0)])],
     ["Concentración 3 %", "Peso específico 1,025 g/cm³ a 20 °C"]),
]
for fid, tit, f, partes, marcas in FICHAS:
    CAPTURAS.append(dict(id=fid, titulo=tit, tipo="Ficha", marcas=marcas,
                         partes=[parte(os.path.join(FIC, f), pg, rect, mk) for pg, rect, mk in partes]))

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    man = []
    for c in CAPTURAS:
        im = render(c["partes"])
        png = os.path.join(OUT, f"{c['id']}.png")
        im.quantize(colors=64).save(png, optimize=True)
        man.append(dict(id=c["id"], titulo=c["titulo"], tipo=c["tipo"], png=os.path.relpath(png, AQUI), w=im.width,
                        h=im.height, marcas=[dict(n=i + 1, etiqueta=e) for i, e in enumerate(c["marcas"])]))
        print(c["id"], im.size)
    json.dump(man, open(os.path.join(AQUI, "capturas.json"), "w"), ensure_ascii=False, indent=1)
