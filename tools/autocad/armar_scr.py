"""Arma salida/dxf_a_dwg.scr: script de AutoCAD que abre cada DXF de salida/, lo audita, lo purga y lo guarda como
DWG 2018 al lado del DXF. Uso (desde la raíz del repo, en la PC con AutoCAD):

    python tools/autocad/armar_scr.py            # todos los planos 2D
    python tools/autocad/armar_scr.py --3d       # también los modelos *_3D.dxf

Después, en AutoCAD con un solo dibujo abierto (nuevo, sin cambios): comando SCRIPT -> salida/dxf_a_dwg.scr.
"""
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SALIDA = os.path.join(RAIZ, "salida")


def main(argv):
    con_3d = "--3d" in argv
    dxfs = []
    for d, _, fs in os.walk(SALIDA):
        for f in sorted(fs):
            if f.lower().endswith(".dxf") and (con_3d or not f.lower().endswith("_3d.dxf")):
                dxfs.append(os.path.join(d, f))
    lineas = ["_.SDI 1", "_.FILEDIA 0", "_.CMDDIA 0", "_.PROXYNOTICE 0"]
    for f in sorted(dxfs):
        dwg = f[:-4] + ".dwg"
        if os.path.exists(dwg):
            os.remove(dwg)                       # SAVEAS no pregunta si reemplazar
        lineas += [f'_.OPEN "{f}"', "_.AUDIT _Y", "_.-PURGE _A * _N", "_.-PURGE _A * _N",
                   "_.-LAYOUT _S Hoja1_Conjunto" if os.path.basename(f).startswith("FL_MAT_") else "",
                   f'_.SAVEAS 2018 "{dwg}"']
    lineas += ["_.FILEDIA 1", "_.CMDDIA 1", "_.SDI 0", ""]
    out = os.path.join(SALIDA, "dxf_a_dwg.scr")
    with open(out, "w", encoding="utf-8-sig", newline="\r\n") as fh:
        fh.write("\n".join(l for l in lineas if l is not None))
    print(len(dxfs), "DXF ->", out)


if __name__ == "__main__":
    main(sys.argv[1:])
