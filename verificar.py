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
from flama.lamina import CAPAS

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
        for i in (1, 2, 3):
            f = os.path.join(BASE, m.codigo, f"{m.codigo}_H{i}.dxf")
            doc = ezdxf.readfile(f)
            aud = doc.audit()
            if aud.has_errors:
                errores.append(f"{f}: {len(aud.errors)} errores DXF")
            capas = {l.dxf.name for l in doc.layers}
            falt = set(CAPAS) - capas
            if falt:
                errores.append(f"{f}: faltan capas {falt}")
            textos = [t.dxf.text for t in doc.modelspace().query("TEXT")]
            if m.codigo not in textos or "FLAMA S.A." not in textos or f"{i} / 3" not in textos:
                errores.append(f"{f}: rótulo incompleto")
            esc = [t for t in textos if ":" in t and len(t) <= 5 and t.replace(":", "").isdigit()]
            for e in esc:
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
    print(f"OK: {len(MODELOS)} modelos, {3 * len(MODELOS)} láminas verificadas sin errores.")


if __name__ == "__main__":
    main()
