"""Capturas marcadas de los procesos FLAMA (documentos del usuario) para la justificación: F38 carros, F39 manuales.

Se arma una página con los fragmentos textuales (citas cortas) de cada documento, se renderiza con Chromium y se
marcan en rojo, numerados, los datos tomados. Se agrega al manifiesto figs.json.
"""
import html
import json
import subprocess

SP = "/tmp/claude-0/-home-user-TP-optimizacion/15292aaf-e550-5dee-a83e-77fd9177a6ef/scratchpad"
OUT = f"{SP}/jw/figs"
NODE = f"{SP}/jw/node"

CSS = """body{font-family:Arial;font-size:15px;margin:0;padding:18px 26px;width:900px;background:#fff;color:#111}
h1{font-size:17px;margin:0 0 4px} .src{color:#555;font-size:12px;margin-bottom:12px}
h2{font-size:14px;margin:12px 0 4px;color:#1F3864} p{margin:3px 0 6px;line-height:1.35}
table{border-collapse:collapse;font-size:13px} td,th{border:1px solid #999;padding:2px 8px;text-align:center}
.m{outline:3px solid #dc0000;outline-offset:2px;position:relative}
.b{position:absolute;left:-30px;top:-6px;background:#dc0000;color:#fff;border-radius:50%;width:22px;height:22px;
font:bold 13px Arial;display:flex;align-items:center;justify-content:center}"""


def marca(n, contenido, bloque=False):
    tag = "div" if bloque else "span"
    return f'<{tag} class="m"><span class="b">{n}</span>{contenido}</{tag}>'


def e(t):
    return html.escape(t)


FIGS = [
    dict(id="F38", archivo="PROCESO_CARRO_EN_LIMPIO.docx", titulo="Proceso FLAMA de carros (documento del usuario)",
         ubic="Tabla 0; puestos 1, 2, 4, 6, 7 y 8", marcas=[
             (1, "Tabla 0: Ø, chapa y alto del cuerpo de 25 / 50 / 70 / 100 kg", ["PC:tabla0"]),
             (2, "Casquetes estampados con borde reducido y tope (15\" para 70 y 100 kg)", ["PC:casquete"]),
             (3, "Hoja mixta 70 + 100 kg: lado de 1212, columnas de 680 y 900", ["PC:corte"]),
             (4, "Placas de refuerzo 200 × 100 × 4,75, Ø380, a 100 mm del borde", ["PC:refuerzo"]),
             (5, "Cupla apoyada por fuera y soldada con filete", ["PC:cupla"]),
             (6, "Accesorios soldados: eje con soportes, manija, 2 ganchos, tercera pata", ["PC:accesorios"]),
         ],
         html=f"""<h1>Producción de carros — FLAMA S.A.</h1><div class="src">PROCESO_CARRO_EN_LIMPIO.docx (extractos)</div>
{marca(1, '''<table><tr><th>Modelo</th><th>Ø (mm)</th><th>Chapa (mm)</th><th>Altura cuerpo (mm)</th></tr>
<tr><td>25 kg</td><td>276,5</td><td>3,2</td><td>490</td></tr><tr><td>50 kg</td><td>320</td><td>3,2</td><td>640</td></tr>
<tr><td>70 kg</td><td>390</td><td>4,75</td><td>680</td></tr><tr><td>100 kg</td><td>390</td><td>4,75</td><td>900</td></tr>
</table><div style="font-size:12px">Tabla 0. Datos de cada modelo</div>''', True)}
<h2>Puesto 1 — Casquetes / Puesto 7 — Armado del casquete</h2>
<p>{marca(2, e("Los fondos y las cúpulas se compran estampados, con tope de encastre y la cúpula ya perforada. […] 150 de 15″ (MP-17, 75 y 75) para los de 70 y 100 kg. […] El fondo y la cúpula vienen del proveedor con el borde reducido y un tope, así que entran dentro del cuerpo hasta apoyar el borde del cuerpo contra ese tope."))}</p>
<h2>Puesto 2 — Corte de chapas</h2>
<p>{marca(3, e("Carros de 70 y 100 kg. Se cortan juntos de la hoja mixta, porque los dos tienen un lado de 1212 mm […] En la primera fase se separan tres columnas de 680 mm y una de 900 mm."))}</p>
<h2>Puesto 4 — Placas de refuerzo (70 y 100 kg)</h2>
<p>{marca(4, e("Los cuerpos de 70 y 100 kg llevan dos placas de refuerzo de 200 × 100 × 4,75 mm, curvadas a Ø 380 mm, por dentro y sobre la junta longitudinal, una en cada extremo a 100 mm del borde."))}</p>
<h2>Puesto 6 — Soldadura de cupla en la cúpula</h2>
<p>{marca(5, e("La cupla se apoya por fuera, centrada sobre la boca, y se suelda con un cordón de filete alrededor."))} {e("Cupla M30 × 1,5 (25 y 50 kg); cupla 2½″ BSP (70 y 100 kg).")}</p>
<h2>Puesto 8 — Soldadura de accesorios</h2>
<p>{marca(6, e("El eje con sus soportes va atrás, en la parte baja del cuerpo; la manija va atrás, en la parte alta, y sube por encima de la cúpula; los dos ganchos portamanguera van en el costado derecho, uno arriba y otro abajo, y la manga se enrolla entre los dos; y la tercera pata va adelante, en el fondo […] Solo se compran el caño de la manija, la barra del eje y las arandelas de tope. […] Kit de accesorios: 4,2 a 4,9 kg."))}</p>"""),
    dict(id="F39", archivo="PROCESO DE MANUALES EXPLICATIVO + VIDEOS.docx",
         titulo="Proceso FLAMA de manuales (documento del usuario)",
         ubic="Preparación de cuello, numerado, encastre de fondo y bordoneado", marcas=[
             (1, "Numerado: desarrollo de 2,5-10 kg; en el 1 kg el número va en la cúpula", ["PM:numerado"]),
             (2, "Muesca de altura en el cuello (prensa Pannier)", ["PM:muesca"]),
             (3, "Encastre: extremo del cuerpo reducido y fondo encastrado a presión", ["PM:encastre"]),
             (4, "Bordoneado: bordoneadora SWM-400; profundidad y posición del bordón", ["PM:bordoneado"]),
         ],
         html=f"""<h1>Proceso de manuales — FLAMA S.A.</h1><div class="src">PROCESO DE MANUALES EXPLICATIVO + VIDEOS.docx (extractos)</div>
<h2>Numerado de cuerpo</h2>
<p>{marca(1, e("Entra: Desarrollo de cuerpo (2,5–10 kg). En el 1 kg el número va en la cúpula."))} {e("En un solo golpe se graban el nombre, el número y el año.")}</p>
<h2>Preparación de cuello</h2>
<p>{marca(2, e("Cuño de muesca a medida (Pannier). […] El cuello tiene que quedar a la altura que marca la muesca y perpendicular a la cúpula."))}</p>
<h2>Encastre de fondo</h2>
<p>{marca(3, e("Sale: Cuerpo con el extremo reducido y el fondo encastrado. […] 2. Colocar el cuerpo y reducir el extremo. 3. Presentar el fondo y encastrarlo a presión."))}</p>
<h2>Bordoneado</h2>
<p>{marca(4, e("Máquina: Bordoneadora motorizada Pilman SWM-400. […] Calidad: Profundidad y posición del bordón con calibre."))}</p>"""),
]

shot = f"""const {{ chromium }} = require('/opt/node22/lib/node_modules/playwright');
(async () => {{
  const b = await chromium.launch();
  const p = await b.newPage({{ viewport: {{ width: 960, height: 600 }} }});
  for (const [src, out] of {json.dumps([[f"{OUT}/{f['id']}.html", f"{OUT}/{f['id']}.png"] for f in FIGS])}) {{
    await p.goto('file://' + src);
    await p.screenshot({{ path: out, fullPage: true }});
  }}
  await b.close();
}})();"""
for f in FIGS:
    open(f"{OUT}/{f['id']}.html", "w").write(f"<html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{f['html']}</body></html>")
open(f"{NODE}/shot_proc.js", "w").write(shot)
subprocess.run(["node", f"{NODE}/shot_proc.js"], check=True)

from PIL import Image  # noqa: E402

figs = [x for x in json.load(open(f"{SP}/jw/figs.json")) if x["id"] not in {f["id"] for f in FIGS}]
for f in FIGS:
    im = Image.open(f"{OUT}/{f['id']}.png").convert("RGB")
    q = f"{OUT}/{f['id']}_q.png"
    im.quantize(colors=48).save(q, optimize=True)
    figs.append(dict(id=f["id"], titulo=f["titulo"], fuente=f"Documento de proceso FLAMA «{f['archivo']}»",
                     ubic=f["ubic"], png=f"{OUT}/{f['id']}.png", w=im.width, h=im.height, link="", tipo="Proceso FLAMA",
                     nota="Documento del usuario (no es la fuente de verdad: se usa para el paso a paso y las medidas que fija).",
                     marcas=[dict(n=n, etiqueta=t, claves=k) for n, t, k in f["marcas"]], img=q))
json.dump(figs, open(f"{SP}/jw/figs.json", "w"), ensure_ascii=False, indent=1)
print(len(figs), "figuras")
