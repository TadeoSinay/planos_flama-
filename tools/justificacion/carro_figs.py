"""Capturas marcadas del carro para la justificación: F41 (plano Fadesa «Rodante 50kg 800mm R2», vista lateral:
manija doblada 30° y extremo de la pata aplastado y soldado), F42 (foto del carro relevado que mandó el usuario:
portaeje y chapa triangular) y las fotos que marcó el usuario: F43 (barra lateral soldada al cuerpo con el extremo
afinado), F44 (altura del doblez de 30°: base de la válvula) y F45 (lanza con válvula esférica de palanca).
Se agregan al manifiesto figs.json (las fuentes originales no están en el repo)."""
import json
import math

import pymupdf
from PIL import Image, ImageDraw, ImageFont

SP = "/tmp/claude-0/-home-user-TP-optimizacion/15292aaf-e550-5dee-a83e-77fd9177a6ef/scratchpad"
OUT = f"{SP}/jw/figs"
PDF = f"{SP}/fadesa/PLANOS FADESA/Rodante 50kg 800mm R2.pdf"
IMG = "/tmp/claude-0/-home-user-TP-optimizacion/15292aaf-e550-5dee-a83e-77fd9177a6ef/images"
FOTO = f"{IMG}/7.png"
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
pix = pg.get_pixmap(dpi=200, clip=pymupdf.Rect(330, 100, 520, 320))
im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
k = 200 / 150
f40 = marcar(im, [(1, (125 * k, 15 * k, 285 * k, 245 * k)), (2, (322, 489, 389, 586))])
# ángulo medido sobre el dibujo: eje del caño inclinado de (140, 25) a (250, 215) a 150 dpi
ang = math.degrees(math.atan2(250 - 140, 215 - 25))
f40.save(f"{OUT}/F41.png")
# F42: foto del carro (ampliada ×4)
im = Image.open(FOTO).convert("RGB")
im = im.resize((im.width * 4, im.height * 4), Image.LANCZOS)
f41 = marcar(im, [(1, (190, 505, 495, 655)), (2, (238, 492, 312, 568))])
f41.save(f"{OUT}/F42.png")


def foto(n, esc, marcas):
    im_ = Image.open(f"{IMG}/{n}.png").convert("RGB")
    im_ = im_.resize((im_.width * esc, im_.height * esc), Image.LANCZOS)
    return marcar(im_, marcas)


f43 = foto(14, 3, [(1, (292, 282, 368, 448))])
f44 = foto(15, 3, [(1, (470, 395, 565, 505)), (2, (650, 395, 765, 480))])
f45 = foto(16, 3, [(1, (205, 180, 305, 345)), (2, (232, 262, 338, 398))])
for fid, im_ in (("F43", f43), ("F44", f44), ("F45", f45)):
    im_.save(f"{OUT}/{fid}.png")

figs = [x for x in json.load(open(f"{SP}/jw/figs.json")) if x["id"] not in ("F41", "F42", "F43", "F44", "F45")]
for fid, im_, tit, fte, ubic, tipo, nota, marcas in (
        ("F41", f40, "Plano Fadesa «Rodante 50kg 800mm R2» (código G692): vista lateral", "Plano de conjunto Fadesa, "
         "archivo «Rodante 50kg 800mm R2.pdf»", "Página 1 (única): vista lateral, manija", "Plano Fadesa",
         f"Ángulo del tramo superior de la manija medido sobre el dibujo vectorial: {ang:.1f}° respecto de la vertical. "
         "El caño baja recto casi pegado al cuerpo y termina afinado (aplastado) contra la pared, donde se suelda; "
         "se dobla a la altura de la cupla. Fadesa además usa una oreja, que FLAMA no lleva (debilita la unión).",
         [(1, "Manija: tramo superior doblado 30° hacia atrás desde la altura de la cupla", ["FR:800:manija"]),
          (2, "Extremo de la pata afinado (aplastado) y soldado al cuerpo", ["FR:800:aplastado"])]),
        ("F42", f41, "Carro relevado (foto enviada por el usuario)", "Foto de un extintor rodante enviada por el "
         "usuario", "Vista trasera-lateral del tren rodante", "Relevamiento de mercado",
         "El eje pasa por un portaeje (caño) cruzado detrás del cuerpo, sostenido por chapas triangulares soldadas a "
         "la pared del recipiente.",
         [(1, "Portaeje: caño cruzado atrás, con el eje de las ruedas adentro", ["REL:carro:portaeje"]),
          (2, "Chapa triangular soldada al cuerpo y al portaeje", ["REL:carro:chapa"])]),
        ("F43", f43, "Carro Elisam marcado por el usuario: soldadura de la barra lateral", "Foto enviada y marcada por "
         "el usuario", "Costado del recipiente, debajo del hombro", "Relevamiento de mercado",
         "La barra lateral de la manija baja separada del cuerpo y su extremo se curva hacia la pared, se afina y se "
         "suelda directo al cuerpo (sin oreja).",
         [(1, "Extremo de la barra afinado y soldado al cuerpo", ["FU:elisam:soldadura"])]),
        ("F44", f44, "Carro AFFF marcado por el usuario: altura del doblez de 30°", "Foto enviada y marcada por el "
         "usuario", "Parte superior del carro", "Relevamiento de mercado",
         "Las patas de la manija suben verticales y se doblan hacia atrás a la altura de la base de la válvula (línea "
         "azul del usuario).",
         [(1, "Doblez de la pata de la manija", ["FU:afff:doblez"]),
          (2, "Base de la válvula (cupla): misma altura", [])]),
        ("F45", f45, "Lanza de carro con válvula esférica (foto del usuario)", "Foto enviada por el usuario",
         "Punta de la manga", "Relevamiento de mercado",
         "Entre la manga y la tobera cónica va una válvula esférica con palanca de accionamiento.",
         [(1, "Válvula esférica con palanca (empuñadura azul)", ["FU:lanza:valvula"]),
          (2, "Tobera cónica de salida", ["FU:lanza:valvula"])])):
    q = f"{OUT}/{fid}_q.png"
    im_.quantize(colors=64).save(q, optimize=True)
    figs.append(dict(id=fid, titulo=tit, fuente=fte, ubic=ubic, png=f"{OUT}/{fid}.png", w=im_.width, h=im_.height,
                     link="", tipo=tipo, nota=nota, img=q,
                     marcas=[dict(n=n, etiqueta=t, claves=c) for n, t, c in marcas]))
json.dump(figs, open(f"{SP}/jw/figs.json", "w"), ensure_ascii=False, indent=1)
print(len(figs), "figuras; ángulo medido", round(ang, 1))
