"""Ajuste de compaginación del Word: que no queden huecos al pie de las páginas de figuras.

Las figuras van de a dos en filas que no se parten. Cuando una fila no entra en lo que queda de la página salta
entera a la siguiente y deja un hueco. El script arma el Word, lo pasa a PDF, mide cada fila (alto del texto y de las
imágenes de cada celda) y, página por página:
  - si achicando un poco las imágenes de la página y de la fila que saltó (hasta F_MIN) la fila entra, la sube;
  - si no, agranda las imágenes de la página (cada una hasta el ancho de su celda o S_MAX) hasta llenar el hueco.
El texto no cambia de tamaño. La escala de cada figura queda en escala.json, que lee word2.js.
"""
import json
import os
import re
import shutil
import subprocess

import pymupdf

SP = "/tmp/claude-0/-home-user-TP-optimizacion/15292aaf-e550-5dee-a83e-77fd9177a6ef/scratchpad"
NODE = f"{SP}/jw/node"                      # word2.js con node_modules
TMP = f"{SP}/wpdf"
ESC_F = f"{SP}/jw/escala.json"
AQUI = os.path.dirname(os.path.abspath(__file__))

LIM = 842 - 42.5     # pie de la caja de texto (A4, margen inferior 850 DXA)
HUECO_MIN = 28       # pt: huecos menores se aceptan
HOLGURA = 12         # pt: margen para diferencias de render entre Word y LibreOffice
F_MIN = 0.60         # no achicar las imágenes por debajo del 60 % de su tamaño base (en total, no por paso)
S_MAX = 1.6          # ni agrandarlas más del 160 % de su tamaño base
ANCHO = 247.5        # pt: ancho máximo de imagen en la celda (330 px)
TIT = re.compile(r"^F\d{2} · ")
H1 = re.compile(r"^\d\. ")
PIE = "— FLAMA S.A. — pág."


def armar(salida=f"{TMP}/a.docx"):
    os.makedirs(TMP, exist_ok=True)
    subprocess.run(["node", "word2.js", salida], cwd=NODE, check=True, capture_output=True)
    subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", TMP, salida],
                   check=True, capture_output=True, timeout=300)
    return pymupdf.open(salida[:-5] + ".pdf")


def contenido(pg):
    """Bloques de texto e imágenes de la caja (sin el pie): (x0, y0, x1, y1, texto)."""
    out = [(b[0], b[1], b[2], b[3], b[4].strip()) for b in pg.get_text("blocks")
           if b[1] < LIM - 2 and not b[4].startswith("<image") and PIE not in b[4]]
    out += [(*i["bbox"], "<img>") for i in pg.get_image_info()]
    return out


def filas(pg):
    """Filas de figuras de la página, de arriba abajo: dict(clave, y0, y1, celdas=[(texto, img, ancho_img, id)])."""
    cs = contenido(pg)
    tits = sorted([c for c in cs if TIT.match(c[4])], key=lambda c: c[1])
    tops = []
    for t in tits:
        if not tops or t[1] > tops[-1][0] + 4:
            tops.append([t[1], []])
        tops[-1][1].append(t)
    h1 = [c[1] for c in cs if H1.match(c[4])]
    medio = pg.rect.width / 2
    out = []
    for k, (y, ts) in enumerate(tops):
        borde = min([tops[k + 1][0] if k + 1 < len(tops) else 1e9] + [v for v in h1 if v > y])
        celdas = []
        for lado in (False, True):
            cc = [c for c in cs if y - 1 <= c[1] < borde and ((c[0] + c[2]) / 2 > medio) == lado]
            if not cc:
                continue
            ims = [c for c in cc if c[4] == "<img>"]
            img = sum(c[3] - c[1] for c in ims)
            alto = max(c[3] for c in cc) - min(c[1] for c in cc)
            tt = [t for t in ts if ((t[0] + t[2]) / 2 > medio) == lado]
            celdas.append((alto - img, img, max([c[2] - c[0] for c in ims] or [0]),
                           tt[0][4].split(" ")[0] if tt else None))
        out.append(dict(clave=min(ts, key=lambda t: t[0])[4].split(" ")[0], y0=y,
                        y1=max(c[3] for c in cs if y - 1 <= c[1] < borde), celdas=celdas))
    return out


def alto(fila, f):
    """Alto de la fila si sus imágenes se escalan por f (número, o función de la celda); el texto no cambia."""
    return max(txt + (f(c) if callable(f) else f) * img for c in fila["celdas"] for txt, img in [c[:2]])


def biseccion(g, a, b, n=40):
    """Mayor x en [a, b] con g(x) ≤ 0, para g creciente (None si g(a) > 0)."""
    if g(a) > 0:
        return None
    for _ in range(n):
        m = (a + b) / 2
        a, b = (m, b) if g(m) <= 0 else (a, m)
    return a


def main():
    esc = {}
    tocadas = {}
    for it in range(40):
        json.dump(esc, open(ESC_F, "w"), indent=1)
        d = armar()
        accion = None
        for i in range(d.page_count - 1):
            cs = contenido(d[i])
            abajo = max(c[3] for c in cs)
            hueco = LIM - abajo
            if hueco < HUECO_MIN or tocadas.get(i, 0) >= 3:
                continue
            aqui = filas(d[i])
            sig = filas(d[i + 1])
            cs2 = contenido(d[i + 1])
            previo = None
            if sig:
                arriba = min(c[1] for c in cs2)
                encima = [c for c in cs2 if c[1] < sig[0]["y0"] - 2]
                previo = sig[0]["y0"] - arriba if all(c[4] != "<img>" for c in encima) else None
            # 1) subir la fila siguiente achicando la página y esa fila
            if previo is not None:
                nxt = sig[0]
                gaps = [b["y0"] - a["y1"] for a, b in zip(aqui, aqui[1:])]
                sep = (min(gaps) if gaps else 8.0) + (10 if previo > 1 else 0)

                def exceso(f):
                    baja = sum(alto(r, 1) - alto(r, f) for r in aqui)
                    return abajo - baja + sep + previo + alto(nxt, f) - (LIM - HOLGURA)
                ids = [c[3] for r in aqui + [nxt] for c in r["celdas"] if c[3]]
                piso = max([F_MIN / esc.get(i_, 1.0) for i_ in ids] + [F_MIN])
                f = biseccion(exceso, piso, 1.0) if piso < 1.0 else None
                if f is not None and f < 0.999:
                    for r in aqui + [nxt]:
                        for c in r["celdas"]:
                            if c[3]:
                                esc[c[3]] = round(esc.get(c[3], 1.0) * f, 3)
                    accion = f"pág. {i + 1}: hueco {hueco:.0f} pt → sube {nxt['clave']} (imágenes al {100 * f:.0f} %)"
            # 2) si no, agrandar las imágenes de la página hasta llenar el hueco
            if accion is None and aqui:
                def tope(c):
                    return min(S_MAX / esc.get(c[3], 1.0), ANCHO / c[2] if c[2] > 0 else 1.0)

                def crece(f):
                    return sum(alto(r, lambda c: max(1.0, min(f, tope(c)))) - alto(r, 1) for r in aqui) - (hueco - HOLGURA)
                fmax = max([1.0] + [tope(c) for r in aqui for c in r["celdas"] if c[3]])
                f = biseccion(crece, 1.0, fmax)
                if f is not None and f > 1.005:
                    for r in aqui:
                        for c in r["celdas"]:
                            if c[3] and min(f, tope(c)) > 1.0:
                                esc[c[3]] = round(esc.get(c[3], 1.0) * min(f, tope(c)), 3)
                    accion = f"pág. {i + 1}: hueco {hueco:.0f} pt → agranda {', '.join(r['clave'] for r in aqui)}"
            if accion:
                tocadas[i] = tocadas.get(i, 0) + 1
                break
            tocadas[i] = 99      # sin arreglo posible: no volver a intentar
        if not accion:
            break
        print(accion, flush=True)
    json.dump(esc, open(ESC_F, "w"), indent=1)
    shutil.copy(ESC_F, os.path.join(AQUI, "escala.json"))
    d = pymupdf.open(f"{TMP}/a.pdf")
    print("huecos al pie (pt):", [round(LIM - max(c[3] for c in contenido(pg))) for pg in d])


if __name__ == "__main__":
    main()
