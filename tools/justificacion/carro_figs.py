"""Capturas marcadas del carro para la justificación: F41 (plano Fadesa «Rodante 50kg 800mm R2», vista lateral:
manija doblada 30° y oreja) y F42 (foto del carro relevado que mandó el usuario: portaeje y chapa triangular).
Se agregan al manifiesto figs.json (las fuentes originales no están en el repo)."""
import json
import math

import pymupdf
from PIL import Image, ImageDraw, ImageFont

SP = "/tmp/claude-0/-home-user-TP-optimizacion/15292aaf-e550-5dee-a83e-77fd9177a6ef/scratchpad"
OUT = f"{SP}/jw/figs"
PDF = f"{SP}/fadesa/PLANOS FADESA/Rodante 50kg 800mm R2.pdf"
FOTO = "/tmp/claude-0/-home-user-TP-optimizacion/15292aaf-e550-5dee-a83e-77fd9177a6ef/images/7.png"
ROJO = (220, 0, 0)


def marcar(im, marcas):
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


# F41: vista lateral del plano Fadesa (a 200 dpi)
pg = pymupdf.open(PDF)[0]
pix = pg.get_pixmap(dpi=200, clip=pymupdf.Rect(330, 100, 520, 300))
im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
k = 200 / 150
f40 = marcar(im, [(1, (125 * k, 15 * k, 285 * k, 245 * k)), (2, (228 * k, 255 * k, 298 * k, 296 * k))])
# ángulo medido sobre el dibujo: eje del caño inclinado de (140, 25) a (250, 215) a 150 dpi
ang = math.degrees(math.atan2(250 - 140, 215 - 25))
f40.save(f"{OUT}/F41.png")
# F42: foto del carro (ampliada ×4)
im = Image.open(FOTO).convert("RGB")
im = im.resize((im.width * 4, im.height * 4), Image.LANCZOS)
f41 = marcar(im, [(1, (190, 505, 495, 655)), (2, (238, 492, 312, 568))])
f41.save(f"{OUT}/F42.png")

figs = [x for x in json.load(open(f"{SP}/jw/figs.json")) if x["id"] not in ("F41", "F42")]
for fid, im_, tit, fte, ubic, tipo, nota, marcas in (
        ("F41", f40, "Plano Fadesa «Rodante 50kg 800mm R2» (código G692): vista lateral", "Plano de conjunto Fadesa, "
         "archivo «Rodante 50kg 800mm R2.pdf»", "Página 1 (única): vista lateral, manija", "Plano Fadesa",
         f"Ángulo del tramo superior de la manija medido sobre el dibujo vectorial: {ang:.1f}° respecto de la vertical. "
         "El caño sube recto pegado al cuerpo, sujeto por la oreja a la altura de la unión cuerpo-cúpula, y se dobla "
         "por encima de la cúpula.",
         [(1, "Manija: tramo superior doblado 30° hacia atrás por encima de la cúpula", ["FR:800:manija"]),
          (2, "Oreja que sujeta la pata de la manija al cuerpo", ["FR:800:oreja"])]),
        ("F42", f41, "Carro relevado (foto enviada por el usuario)", "Foto de un extintor rodante enviada por el "
         "usuario", "Vista trasera-lateral del tren rodante", "Relevamiento de mercado",
         "El eje pasa por un portaeje (caño) cruzado detrás del cuerpo, sostenido por chapas triangulares soldadas a "
         "la pared del recipiente.",
         [(1, "Portaeje: caño cruzado atrás, con el eje de las ruedas adentro", ["REL:carro:portaeje"]),
          (2, "Chapa triangular soldada al cuerpo y al portaeje", ["REL:carro:chapa"])])):
    q = f"{OUT}/{fid}_q.png"
    im_.quantize(colors=64).save(q, optimize=True)
    figs.append(dict(id=fid, titulo=tit, fuente=fte, ubic=ubic, png=f"{OUT}/{fid}.png", w=im_.width, h=im_.height,
                     link="", tipo=tipo, nota=nota, img=q,
                     marcas=[dict(n=n, etiqueta=t, claves=c) for n, t, c in marcas]))
json.dump(figs, open(f"{SP}/jw/figs.json", "w"), ensure_ascii=False, indent=1)
print(len(figs), "figuras; ángulo medido", round(ang, 1))
