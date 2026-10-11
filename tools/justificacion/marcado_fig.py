"""F53: proceso FLAMA de manuales (versión con «Numerado de cúpula»): el número va estampado en la cúpula, en arco
alrededor del cuello. Recorta las dos páginas del apartado del documento del usuario (pasado a PDF con LibreOffice),
marca lo que se toma y lo agrega al manifiesto figs.json; corrige además la marca 1 de F39 (versión anterior del
documento, que numeraba el desarrollo del cuerpo).

Uso: python marcado_fig.py "<documento de proceso>.pdf"
"""
import json
import sys

import pymupdf
from PIL import Image, ImageDraw, ImageFont

SP = "/tmp/claude-0/-home-user-TP-optimizacion/15292aaf-e550-5dee-a83e-77fd9177a6ef/scratchpad"
OUT = f"{SP}/jw/figs"
Z = 2.0                                  # 144 dpi
ROJO = (220, 0, 0)


def marcar(im, marcas):
    """Rectángulos rojos numerados (mismo estilo que carro_figs.py)."""
    d = ImageDraw.Draw(im)
    try:
        fnt = ImageFont.truetype("DejaVuSans-Bold.ttf", 22)
    except OSError:
        fnt = ImageFont.load_default()
    for n, (x0, y0, x1, y1) in marcas:
        d.rectangle((x0, y0, x1, y1), outline=ROJO, width=4)
        cx, cy = x0 - 2, y0 - 2
        d.ellipse((cx - 16, cy - 16, cx + 16, cy + 16), fill=ROJO)
        d.text((cx, cy), str(n), fill=(255, 255, 255), font=fnt, anchor="mm")
    return im

doc = pymupdf.open(sys.argv[1])
pag = next(i for i, p in enumerate(doc) if p.search_for("Numerado de cúpula"))
p1, p2 = doc[pag], doc[pag + 1]
y0 = p1.search_for("Numerado de cúpula")[0].y0 - 6
y1 = p2.search_for("sin deformar la cúpula")[0].y1 + 22
fin1 = max(b[3] for b in p1.get_text("blocks") if b[1] > y0 and b[3] < p1.rect.height - 45) + 6
partes, marcas, dy = [], [], 0.0
for p, a, b, buscar in ((p1, y0, fin1, ("estampados en frío en la cúpula", "junto al cuello, con letra de 5 mm",
                                                          "marcando en arco alrededor del cuello")),
                        (p2, 50, y1, ("la aguja marca en arco", "junto al cuello y sin deformar la cúpula"))):
    clip = pymupdf.Rect(60, a, p.rect.width - 60, b)
    pix = p.get_pixmap(matrix=pymupdf.Matrix(Z, Z), clip=clip)
    partes.append(Image.frombytes("RGB", (pix.width, pix.height), pix.samples))
    for s in buscar:
        rs = p.search_for(s)
        assert rs, f"no está en el documento: {s}"
        if rs:
            r = rs[0]
            for q in rs[1:]:
                if abs(q.y0 - r.y1) < 16:
                    r |= q
            marcas.append(((r.x0 - clip.x0) * Z - 4, (r.y0 - a) * Z + dy - 3, (r.x1 - clip.x0) * Z + 4,
                           (r.y1 - a) * Z + dy + 3))
    dy += pix.height
im = Image.new("RGB", (max(x.width for x in partes), int(dy)), (255, 255, 255))
y = 0
for x in partes:
    im.paste(x, (0, y))
    y += x.height
im = marcar(im, [(i + 1, m) for i, m in enumerate(marcas)])
im.save(f"{OUT}/F53.png")
q = f"{OUT}/F53_q.png"
im.quantize(colors=64).save(q, optimize=True)

figs = [x for x in json.load(open(f"{SP}/jw/figs.json")) if x["id"] != "F53"]
for x in figs:
    if x["id"] == "F39":
        x["marcas"][0]["etiqueta"] = ("Numerado: esta versión del documento lo hacía en el desarrollo del cuerpo (el 1 kg en "
                                      "la cúpula); la versión vigente lo estampa en la cúpula en todos los modelos (F53)")
figs.append(dict(
    id="F53", titulo="Proceso FLAMA de manuales: numerado de cúpula (documento del usuario)",
    fuente="Documento de proceso FLAMA «PROCESO DE MANUALES EXPLICATIVO + VIDEOS.docx» (versión vigente)",
    ubic="Apartado «Numerado de cúpula»: proceso, paso a paso y controles", png=f"{OUT}/F53.png", w=im.width,
    h=im.height, link="", tipo="Proceso FLAMA", img=q,
    nota=("El número va estampado en la cúpula, en arco alrededor del cuello (micropercusión, un apoyo por modelo), "
          "antes de soldar el cuello y antes de la PH; el mismo criterio se aplica a los carros (puesto 11)."),
    marcas=[dict(n=1, etiqueta="Fabricante, n° de recipiente y año estampados en frío en la cúpula", claves=["PM2:numerado"]),
            dict(n=2, etiqueta="Junto al cuello, letra de 5 mm (IRAM 4503) y cuño DPS al lado", claves=["PM2:numerado"]),
            dict(n=3, etiqueta="En arco alrededor del cuello: la aguja trabaja a la misma distancia", claves=["PM2:numerado"]),
            dict(n=4, etiqueta="Ciclo: fabricante, número, año y DPS en arco", claves=["PM2:numerado"]),
            dict(n=5, etiqueta="Control: junto al cuello y sin deformar la cúpula (IRAM 3523 5.1)", claves=["PM2:numerado"])]))
json.dump(figs, open(f"{SP}/jw/figs.json", "w"), ensure_ascii=False, indent=1)
print("F53", im.size, len(marcas), "marcas")
