"""Regiones cerradas (componentes del fondo) de una zona del PDF, numeradas, para elegir las de cada pieza."""
import sys, json, numpy as np, pymupdf
from scipy import ndimage as ndi
from PIL import Image, ImageDraw
pdf, x0, y0, x1, y1, dpi, out = sys.argv[1], *map(float, sys.argv[2:7]), sys.argv[7]
page = pymupdf.open(pdf)[0]
pix = page.get_pixmap(dpi=int(dpi), clip=pymupdf.Rect(x0, y0, x1, y1), colorspace=pymupdf.csGRAY)
a = np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width)
tinta = a < 160
tinta = ndi.binary_dilation(tinta, iterations=1)        # cierra huecos de 1 px entre trazos
lab, n = ndi.label(~tinta)
sizes = ndi.sum(np.ones_like(lab), lab, range(1, n + 1))
np.save(out[:-4] + "_lab.npy", lab)
k = dpi / 72
im = Image.new("RGB", (pix.width, pix.height), "white")
rgb = np.zeros((pix.height, pix.width, 3), np.uint8) + 255
rng = np.random.default_rng(3)
cols = rng.integers(120, 255, (n + 1, 3)); cols[0] = 255
fondo = lab[0, 0]
rgb = cols[lab].astype(np.uint8); rgb[lab == fondo] = 255; rgb[tinta] = 0
im = Image.fromarray(rgb); dr = ImageDraw.Draw(im)
info = {}
for i in range(1, n + 1):
    if sizes[i - 1] < 30 or i == fondo:
        continue
    ys, xs = np.nonzero(lab == i)
    cx, cy = int(xs.mean()), int(ys.mean())
    dr.text((cx - 5, cy - 5), str(i), fill="red")
    info[i] = (x0 + cx / k, y0 + cy / k, int(sizes[i - 1]))
im.save(out)
json.dump(dict(x0=x0, y0=y0, k=k, fondo=int(fondo), info=info), open(out[:-4] + ".json", "w"))
print(n, "regiones; fondo", fondo, pix.width, pix.height)
