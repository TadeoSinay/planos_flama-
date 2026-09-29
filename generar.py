"""Genera todos los planos FLAMA S.A.

Uso:  python generar.py [CODIGO ...]      (sin argumentos: todos los modelos)
Salida: salida/<CODIGO>/  (DXF con 3 láminas/presentaciones, PDF de 3 hojas, STEP, DXF 3D)
"""

import os
import sys
import json
import time
import pymupdf

from flama.catalogo import MODELOS
from flama import planos as P, exportar as X, modelo3d as M

BASE = os.path.dirname(os.path.abspath(__file__))


def main(codigos):
    salida = os.path.join(BASE, "salida")
    os.makedirs(salida, exist_ok=True)
    resumen = []
    pdf_total = pymupdf.open()
    for m in MODELOS:
        if codigos and m.codigo not in codigos:
            continue
        t = time.time()
        d = os.path.join(salida, m.codigo)
        os.makedirs(d, exist_ok=True)
        piezas, info, doc, hojas, res = P.generar(m)
        X.preparar_layouts(doc, hojas)
        doc.saveas(os.path.join(d, f"{m.codigo}.dxf"))
        pdf_m = X.pdf_hojas(doc, hojas)
        pdf_m.set_metadata({"title": f"{m.codigo} - {m.nombre}", "author": "FLAMA S.A.",
                            "subject": "Plano de conjunto, corte y detalles, especificaciones"})
        pdf_m.save(os.path.join(d, f"{m.codigo}.pdf"))
        pdf_total.insert_pdf(pdf_m)
        X.step(piezas, os.path.join(d, f"{m.codigo}.step"))
        X.dxf_3d(piezas, os.path.join(d, f"{m.codigo}_3D.dxf"))
        bb = M.bbox(piezas)
        resumen.append(dict(codigo=m.codigo, nombre=m.nombre, formato_h1=res["fmt"],
                            escala_h1=f"{res['escala'][0]}:{res['escala'][1]}",
                            H_cat=m.H, H_mod=round(bb.zmax - bb.zmin, 1),
                            W_cat=m.W, W_mod=round(bb.xlen, 1),
                            D_cat=m.D, D_mod=round(bb.ylen, 1),
                            vol_dm3=m.geo["vol_dm3"]))
        print(f"{m.codigo}: {time.time() - t:.1f} s", flush=True)
    if not codigos:
        pdf_total.save(os.path.join(salida, "FLAMA_planos_completos.pdf"))
        with open(os.path.join(salida, "validacion.json"), "w", encoding="utf-8") as fh:
            json.dump(resumen, fh, ensure_ascii=False, indent=1)
    return resumen


if __name__ == "__main__":
    main(sys.argv[1:])
