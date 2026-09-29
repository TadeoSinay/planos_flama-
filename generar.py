"""Genera todos los planos FLAMA S.A.

Uso:  python generar.py [CODIGO ...]      (sin argumentos: todo)
      python generar.py --complementarios  (sólo recipientes, señalética, accesorios, esquemas y documentos)
Salida: salida/<CODIGO>/  (DXF con 3 láminas/presentaciones, PDF de 3 hojas, STEP, DXF 3D)
        salida/recipientes/, senaletica/, accesorios/, esquemas/, documentos/
"""

import os
import sys
import json
import time
import pymupdf

from flama.catalogo import MODELOS
from flama import planos as P, exportar as X, modelo3d as M
from flama import recipientes as RC, senaletica as SN, accesorios as AC, esquemas as ES, documentos as DO

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


def _lamina(doc, fmt, carpeta, cod, titulo, color=False):
    hojas = [("Lamina", fmt, 0.0)]
    X.preparar_layouts(doc, hojas)
    doc.saveas(os.path.join(carpeta, f"{cod}.dxf"))
    p = X.pdf_hojas(doc, hojas, color=color)
    p.set_metadata({"title": f"{cod} - {titulo}", "author": "FLAMA S.A."})
    p.save(os.path.join(carpeta, f"{cod}.pdf"))
    return p


def complementarios():
    """Recipientes ABC sueltos, señalética, accesorios, esquemas de ensayo y documentos."""
    salida = os.path.join(BASE, "salida")
    total = pymupdf.open()
    # recipientes ABC para venta suelta
    for m in RC.modelos_abc():
        cod = RC.codigo_rec(m)
        d = os.path.join(salida, "recipientes", cod)
        os.makedirs(d, exist_ok=True)
        doc, fmt, inf = RC.generar_recipiente(m)
        total.insert_pdf(_lamina(doc, fmt, d, cod, "Recipiente " + m.nombre.replace("Extintor ", "")))
        X.step(inf["piezas"], os.path.join(d, f"{cod}.step"))
        print(cod, flush=True)
    # señalética (en color), accesorios y esquemas
    for carpeta, mod, color in (("senaletica", SN, True), ("accesorios", AC, False), ("esquemas", ES, False)):
        d = os.path.join(salida, carpeta)
        os.makedirs(d, exist_ok=True)
        for cod, fn, fmt in mod.LAMINAS:
            r = fn()
            doc, sol = (r if isinstance(r, tuple) else (r, None))
            total.insert_pdf(_lamina(doc, fmt, d, cod, carpeta, color))
            if sol is not None:
                X.step({cod: sol}, os.path.join(d, f"{cod}.step"))
            print(cod, flush=True)
    # documentos A4
    d = os.path.join(salida, "documentos")
    os.makedirs(d, exist_ok=True)
    for nombre, fn in DO.DOCUMENTOS:
        ruta = os.path.join(d, f"{nombre}.pdf")
        DO.pdf(fn(), ruta, nombre.split("_")[0])
        total.insert_pdf(pymupdf.open(ruta))
        print(nombre, flush=True)
    total.save(os.path.join(salida, "FLAMA_complementarios.pdf"))


if __name__ == "__main__":
    args = sys.argv[1:]
    if args == ["--complementarios"]:
        complementarios()
    else:
        main(args)
        if not args:
            complementarios()
