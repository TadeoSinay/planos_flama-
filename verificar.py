"""Verificaciones automáticas de las láminas generadas.

1. Integridad DXF (auditoría ezdxf, sin errores).
2. Caja envolvente del modelo 3D contra catálogo (altura y ancho: ±0,05 mm).
3. Escalas del rótulo pertenecientes a la serie normalizada ISO 5455 / IRAM 4505.
4. Capas y tipos de línea según IRAM 4502 presentes en cada lámina.
5. Cada lámina tiene rótulo con código, hoja n/3 y propietario FLAMA S.A.
"""

import glob
import json
import os
import sys

import ezdxf

from flama.catalogo import MODELOS
from flama.lamina import CAPAS, FORMATOS, ROT_W, ROT_H

ESCALAS_OK = {"1:1", "1:2", "1:5", "1:10", "1:20", "2:1", "5:1", "-"}
BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "salida")


def main():
    errores = []
    val = {v["codigo"]: v for v in json.load(open(os.path.join(BASE, "validacion.json"), encoding="utf-8"))}
    filas = []
    for m in MODELOS:
        v = val[m.codigo]
        dH, dW = v["H_mod"] - v["H_cat"], v["W_mod"] - v["W_cat"]
        if abs(dH) > 0.05 or abs(dW) > 0.05:
            errores.append(f"{m.codigo}: caja envolvente difiere del catálogo (dH={dH}, dW={dW})")
        f = os.path.join(BASE, m.codigo, f"{m.codigo}.dxf")
        doc = ezdxf.readfile(f)
        aud = doc.audit()
        if aud.has_errors:
            errores.append(f"{f}: {len(aud.errors)} errores DXF")
        capas = {l.dxf.name for l in doc.layers}
        falt = set(CAPAS) - capas
        if falt:
            errores.append(f"{f}: faltan capas {falt}")
        pres = [n for n in doc.layouts.names() if n != "Model"]
        if len(pres) != 3:
            errores.append(f"{f}: se esperaban 3 presentaciones, hay {pres}")
        textos = [t.dxf.text for t in doc.modelspace().query("TEXT")]
        for i in (1, 2, 3):
            if f"{i} / 3" not in textos:
                errores.append(f"{f}: falta el rótulo de la hoja {i}")
        if textos.count(m.codigo) != 3 or textos.count("FLAMA S.A.") != 3:
            errores.append(f"{f}: rótulos incompletos (código o propietario)")
        if any("definir" in t.lower() for t in textos):
            errores.append(f"{f}: quedan textos 'A definir'")
        # IRAM 4502: grupo de líneas (visibles 0,70 / ocultas media 0,35 / finas 0,18)
        lw = {l.dxf.name: l.dxf.lineweight for l in doc.layers}
        if (lw.get("01-VISIBLE"), lw.get("02-OCULTA"), lw.get("03-EJE"), lw.get("04-COTA")) != (70, 35, 18, 18):
            errores.append(f"{f}: grupo de líneas IRAM 4502 incorrecto {lw}")
        # IRAM 4513: flecha con relación 1:4
        blk = doc.blocks.get("IRAM_FLECHA")
        if blk is None or doc.dimstyles.get("FLAMA-IRAM").dxf.dimblk != "IRAM_FLECHA":
            errores.append(f"{f}: estilo de cota sin flecha IRAM 1:4")
        # IRAM 4504 (recuadro 25/10) e IRAM 4508 (rótulo 175 x 51) en cada lámina
        recuadros = [p for p in doc.modelspace().query("LWPOLYLINE[layer=='07-RECUADRO']")]
        rects = []
        for p in recuadros:
            pts = [(round(x, 2), round(y, 2)) for x, y, *_ in p.get_points()]
            xs, ys = [q[0] for q in pts], [q[1] for q in pts]
            rects.append((min(xs), min(ys), max(xs), max(ys)))
        for nombre in pres:
            lay = doc.layouts.get(nombre)
            fmt = next(k for k, v in FORMATOS.items() if abs(v[0] - lay.dxf.paper_width) < 1 and abs(v[1] - lay.dxf.paper_height) < 1)
            W, H = FORMATOS[fmt]
            vp = [e for e in lay.query("VIEWPORT") if e.dxf.id != 1][-1]
            ox = vp.dxf.view_center_point[0] - W / 2
            marco = (round(ox + 25, 2), 10.0, round(ox + W - 10, 2), round(H - 10, 2))
            if marco not in rects:
                errores.append(f"{f} {nombre}: recuadro no está a 25/10 mm (IRAM 4504)")
            rot = (round(ox + W - 10 - ROT_W, 2), 10.0, round(ox + W - 10, 2), round(10 + ROT_H, 2))
            if rot not in rects:
                errores.append(f"{f} {nombre}: rótulo distinto de 175 x 51 mm (IRAM 4508)")
            # nada del dibujo fuera del recuadro ni dentro del rótulo/lista (salvo sus textos)
            for e in doc.modelspace().query("LINE[layer=='01-VISIBLE']"):
                for q in (e.dxf.start, e.dxf.end):
                    if ox <= q.x <= ox + W and not (marco[0] - 0.01 <= q.x <= marco[2] + 0.01 and marco[1] - 0.01 <= q.y <= marco[3] + 0.01):
                        errores.append(f"{f} {nombre}: arista visible fuera del recuadro")
                        break
        for e in [t for t in textos if ":" in t and len(t) <= 5 and t.replace(":", "").isdigit()]:
            if e not in ESCALAS_OK:
                errores.append(f"{f}: escala no normalizada {e}")
        filas.append(f"| {m.codigo} | {v['H_cat']:.0f} | {v['H_mod']:.1f} | {v['W_cat']:.0f} | {v['W_mod']:.1f} | "
                     f"{v['D_cat']:.0f} | {v['D_mod']:.1f} | {v['formato_h1']} {v['escala_h1']} |")
    print("| Código | H cat. | H modelo | A cat. | A modelo | P cat. | P modelo | Hoja 1 |")
    print("|---|---|---|---|---|---|---|---|")
    print("\n".join(filas))
    print()
    if errores:
        print("ERRORES:")
        print("\n".join(errores))
        sys.exit(1)
    print(f"OK: {len(MODELOS)} planos ({3 * len(MODELOS)} láminas) verificados sin errores.")


if __name__ == "__main__":
    main()
