"""Recorta cada captura a la zona de sus marcas rojas (planos y normas) para el Word compacto."""
import json

import numpy as np
from PIL import Image

SP = "/tmp/claude-0/-home-user-TP-optimizacion/15292aaf-e550-5dee-a83e-77fd9177a6ef/scratchpad"
C = json.load(open(f"{SP}/jw/compacto.json"))
for f in C["figs"]:
    im = Image.open(f["png"]).convert("RGB")
    if f["tipo"] in ("Plano Fadesa", "Norma / resolución"):
        a = np.asarray(im).astype(int)
        red = (a[:, :, 0] > 180) & (a[:, :, 1] < 70) & (a[:, :, 2] < 70)
        ys, xs = np.nonzero(red)
        if len(xs):
            m = 30
            box = (max(0, xs.min() - m), max(0, ys.min() - m), min(im.width, xs.max() + m), min(im.height, ys.max() + m))
            im = im.crop(box)
    if f["tipo"] in ("Catálogo Fadesa", "Relevamiento de mercado"):
        out = f["png"][:-4] + "_c.jpg"
        im.save(out, "JPEG", quality=80, optimize=True)
    else:
        out = f["png"][:-4] + "_c.png"
        im.quantize(colors=48, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).save(out, optimize=True)
    f["crop"], f["cw"], f["ch"] = out, im.width, im.height
json.dump(C, open(f"{SP}/jw/compacto.json", "w"), ensure_ascii=False, indent=0)
print("ok", len(C["figs"]))
