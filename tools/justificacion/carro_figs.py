"""Capturas marcadas del carro para la justificación: F41 (plano Fadesa «Rodante 50kg 800mm R2», vista lateral:
manija doblada 30° y extremo de la pata aplastado y soldado), F42 (foto del carro relevado que mandó el usuario:
portaeje y chapa triangular) y las fotos que marcó el usuario: F43 (barra lateral soldada al cuerpo con el extremo
afinado), F44 (altura del doblez de 30°: base de la válvula) y F45 (lanza con válvula esférica de palanca); del
proceso de carros v2 del usuario: F46 (vista de costado: triángulo con V, lengüeta, flejes y pata), F47 (plantilla de
posiciones sobre el cuerpo desarrollado) y F48 (piezas del kit); del proceso final: F50 (manija), F51 (carro armado)
y F52 (foto del fleje), y la hoja de especificaciones «Polvos carros» del usuario (F49). Se agregan al manifiesto
figs.json (las fuentes originales no están en el repo)."""
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


def recorte(png, box, marcas):
    """Recorta una figura del proceso v2 y marca en coordenadas de la imagen original."""
    im_ = Image.open(png).convert("RGB").crop(box)
    return marcar(im_, [(n, (a - box[0], b - box[1], c - box[0], d - box[1])) for n, (a, b, c, d) in marcas])


PC2 = f"{SP}/rod2/x/word/media"          # imágenes de PROCESO_CARRO_EN_LIMPIO_2.docx
f46 = recorte(f"{PC2}/image1.png", (1010, 45, 1673, 1125),
              [(1, (1440, 895, 1535, 990)), (2, (1308, 552, 1370, 628)), (3, (1326, 85, 1430, 238)),
               (4, (1142, 466, 1212, 522)), (5, (1220, 1045, 1262, 1118))])
f47 = recorte(f"{PC2}/image3.png", (130, 40, 1600, 1180),
              [(1, (180, 765, 300, 958)), (2, (185, 170, 535, 465)), (3, (650, 172, 945, 278)),
               (4, (650, 872, 945, 975)), (5, (765, 1088, 1410, 1170))])
f48 = recorte(f"{PC2}/image1.png", (55, 1290, 1680, 2025),
              [(1, (72, 1428, 316, 1910)), (2, (403, 1596, 685, 1768)), (3, (760, 1601, 1015, 1898)),
               (4, (1107, 1525, 1326, 1898)), (5, (1420, 1612, 1662, 1898))])
for fid, im_ in (("F46", f46), ("F47", f47), ("F48", f48)):
    im_.save(f"{OUT}/{fid}.png")

# del proceso final de carros (PROCESO_CARRO_EN_LIMPIO.pdf, imágenes extraídas) y de la hoja de especificaciones
# «Polvos carros» que pasó el usuario: F49 (hoja), F50 (manija), F51 (carro armado), F52 (foto del fleje con la manga)
PFIN = f"{SP}/pfin"
f49 = marcar(Image.open(f"{IMG}/25.png").convert("RGB").resize((1354, 798)),
             [(1, (610, 90, 750, 770)), (2, (756, 90, 884, 770)), (3, (888, 90, 1020, 770)), (4, (1160, 90, 1304, 770))])
f50 = marcar(Image.open(f"{PFIN}/img_p4_18.png").convert("RGB").crop((60, 200, 1820, 1170)),
             [(1, (220, 40, 560, 110)), (2, (1240, 40, 1520, 260)), (3, (190, 245, 640, 260))])
f51 = marcar(Image.open(f"{PFIN}/img_p1_9.png").convert("RGB"),
             [(1, (270, 1240, 660, 1290)), (2, (580, 1200, 740, 1250)), (3, (160, 810, 640, 1050)),
              (4, (1130, 480, 1200, 1030))])
f52 = marcar(Image.open(f"{PFIN}/img_p7_26.png").convert("RGB").resize((1000, 393)),
             [(1, (200, 80, 820, 190)), (2, (130, 210, 230, 330)), (3, (820, 210, 940, 330)), (4, (60, 280, 960, 390))])
for fid, im_ in (("F49", f49), ("F50", f50), ("F51", f51), ("F52", f52)):
    im_.save(f"{OUT}/{fid}.png")

NUEVAS = ("F41", "F42", "F43", "F44", "F45", "F46", "F47", "F48", "F49", "F50", "F51", "F52")
POLVO = ("FL_MAT_ABC_25kg", "FL_MAT_ABC_50kg", "FL_MAT_ABC_70kg", "FL_MAT_ABC_100kg")
CAMPOS = ("Peso", "Altura", "Ancho", "Profundidad", "Rueda", "Manga", "Ps", "Pe")
figs = [x for x in json.load(open(f"{SP}/jw/figs.json")) if x["id"] not in NUEVAS]
for x in figs:                       # los carros de polvo ya no salen del catálogo Fadesa sino de la hoja del usuario
    for mk in x["marcas"]:
        mk["claves"] = [k for k in mk["claves"] if not any(k.startswith(f"CAT:{c}:") for c in POLVO)]
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
          (2, "Tobera cónica de salida", ["FU:lanza:valvula"])]),
        ("F46", f46, "Proceso de carros v2: dónde va cada accesorio (vista de costado, 50 kg)", "Documento de proceso "
         "del usuario «PROCESO_CARRO_EN_LIMPIO_2.docx»", "Soldadura de accesorios, figura «Dónde va cada accesorio»",
         "Proceso FLAMA", "La V de 90° de cada triángulo mira hacia atrás y el caño del eje se apoya en ella: la chapa "
         "no lo envuelve; el caño no gira y el eje pasa por adentro al montaje final.",
         [(1, "Triángulo con V y caño del eje apoyado (20 del cuerpo)", ["PC2:tri"]),
          (2, "Lengüeta aplastada 40 × 60 soldada al costado", ["PC2:manija"]),
          (3, "Doblez de 30° hacia atrás y puño", ["PC2:manija"]),
          (4, "Fleje del soporte de manga (Ω)", ["PC2:fleje"]),
          (5, "Pata delantera de canto en el fondo", ["PC2:pata"])]),
        ("F47", f47, "Proceso de carros v2: posiciones sobre el cuerpo desarrollado (50 kg)", "Documento de proceso "
         "del usuario «PROCESO_CARRO_EN_LIMPIO_2.docx»", "Soldadura de accesorios, plantilla y tabla de posiciones",
         "Proceso FLAMA", "Medidas desde la costura longitudinal (atrás) con la cinta envuelta y alturas desde las "
         "costuras del fondo y de la cúpula; los otros modelos, en la tabla de posiciones del proceso.",
         [(1, "Triángulos a 82 de la costura, borde de abajo a 20 del fondo", ["PC2:tabla"]),
          (2, "Lengüetas a 251 (costados), borde de abajo 200 bajo la cúpula", ["PC2:tabla"]),
          (3, "Fleje superior: borde de arriba 40 bajo la cúpula", ["PC2:tabla"]),
          (4, "Fleje inferior: borde de abajo 40 sobre el fondo", ["PC2:tabla"]),
          (5, "Pata 48 hacia adentro; línea del piso a 135 bajo el fondo", ["PC2:piso"])]),
        ("F48", f48, "Proceso de carros v2: piezas del kit (25 / 50 / 70 y 100 kg)", "Documento de proceso del "
         "usuario «PROCESO_CARRO_EN_LIMPIO_2.docx»", "Soldadura de accesorios, piezas de un kit (puesto 8.1)",
         "Proceso FLAMA", "El eje no va en el kit: va al montaje final con las ruedas, las arandelas y los pasadores.",
         [(1, "Manija: caño 1\" × 2,0, corte 1440 / 1520 / 1590", ["PC2:manija"]),
          (2, "Caño del eje 1\" / 1¼\" × 2,0 × 354 / 354 / 434", ["PC2:cano"]),
          (3, "Triángulos con V: chapa 4,75, cateto 70 / 80 / 100", ["PC2:tri"]),
          (4, "Flejes: 3,2 × 40, corte 292 / 318 / 400", ["PC2:fleje"]),
          (5, "Pata: 3,2, 80 × 60 / 100 × 80", ["PC2:pata"])]),
        ("F49", f49, "Hoja de especificaciones «Polvos carros» (usuario)", "Tabla enviada por el usuario",
         "Columnas 25, 50, 70 (5 m) y 100 kg", "Hoja de especificaciones",
         "Alto, ancho, profundidad, Ø de rueda y largo de manga que el carro tiene que cumplir; el 70 kg va con 5 m de "
         "manga (la columna de 10 m no se fabrica).",
         [(i + 1, f"{c[7:].replace('_', ' ')}", [f"CAT:{c}:{k}" for k in CAMPOS]) for i, c in enumerate(POLVO)]),
        ("F50", f50, "Proceso final de carros: manija (vistas y desarrollo)", "Documento de proceso del usuario "
         "«PROCESO_CARRO_EN_LIMPIO.pdf»", "Puesto 8.1, figura de la manija", "Proceso FLAMA",
         "A entre ejes de las patas, tramo inclinado C = 180 (sube 156 y se corre 90) y curvas con la matriz de radio "
         "100; la altura de la curva (B) se ajusta para dar el alto de la hoja de especificaciones.",
         [(1, "A entre ejes de las patas", ["PCF:manija"]), (2, "Tramo inclinado C = 180 a 30°", ["PCF:manija"]),
          (3, "Curva de 30° sobre la costura de la cúpula (B)", ["PCF:manija"])]),
        ("F51", f51, "Proceso final de carros: carro armado (50 kg)", "Documento de proceso del usuario "
         "«PROCESO_CARRO_EN_LIMPIO.pdf»", "Figura «Carro de 50 kg armado»", "Proceso FLAMA",
         "Ruedas de chapa y goma con buje liso, eje de barra trefilada dentro del caño apoyado en los triángulos; la "
         "trocha sale del ancho de la hoja de especificaciones.",
         [(1, "Trocha entre centros de rueda", ["PCF:tabla"]), (2, "Rueda Ø × banda (montaje final)", ["PCF:tabla"]),
          (3, "Caño del eje con el eje adentro, sobre los triángulos", ["PCF:tabla"]),
          (4, "Flejes superior e inferior adelante", ["PCF:fleje"])]),
        ("F52", f52, "Proceso final de carros: fleje del soporte de manga (foto)", "Documento de proceso del usuario "
         "«PROCESO_CARRO_EN_LIMPIO.pdf»", "Figura de los flejes del soporte de manga", "Proceso FLAMA",
         "U abierta hacia afuera con la base recta soldada al cuerpo por el centro; la manga pasa por afuera de las "
         "patas y la oreja no la deja salirse (las medidas del esquema del documento eran orientativas: salen del "
         "largo de manga).",
         [(1, "Base recta soldada al centro", ["PCF:fleje"]), (2, "Pata y oreja (izquierda)", ["PCF:fleje"]),
          (3, "Pata y oreja (derecha)", ["PCF:fleje"]), (4, "Manga por afuera de las patas", ["PCF:fleje"])])):
    q = f"{OUT}/{fid}_q.png"
    im_.quantize(colors=64).save(q, optimize=True)
    figs.append(dict(id=fid, titulo=tit, fuente=fte, ubic=ubic, png=f"{OUT}/{fid}.png", w=im_.width, h=im_.height,
                     link="", tipo=tipo, nota=nota, img=q,
                     marcas=[dict(n=n, etiqueta=t, claves=c) for n, t, c in marcas]))
json.dump(figs, open(f"{SP}/jw/figs.json", "w"), ensure_ascii=False, indent=1)
print(len(figs), "figuras; ángulo medido", round(ang, 1))
