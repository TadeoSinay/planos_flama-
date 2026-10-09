"""Perfiles laterales (mm, x = eje de válvula, z = 0 en la cara del cuello) de cuerpo y manijas F510 / F192
a partir de las regiones del plano Fadesa."""
import json, numpy as np
from scipy import ndimage as ndi
import shapely.geometry as sg
from shapely.ops import unary_union
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
SP = "perf"  # carpeta de trabajo con las salidas de regiones.py

def perfil(base, ids, esc, eje_px, z0_px, dil=5):
    lab = np.load(f"{SP}/{base}_lab.npy"); meta = json.load(open(f"{SP}/{base}.json"))
    k = meta["k"]
    m = np.isin(lab, ids)
    m = ndi.binary_dilation(m, iterations=dil)
    m = ndi.binary_fill_holes(m)
    cs = plt.contour(m.astype(float), [0.5]); plt.close()
    polys = [sg.Polygon(s) for s in cs.allsegs[0] if len(s) > 10]
    p = unary_union([q.buffer(0) for q in polys])
    if p.geom_type == "MultiPolygon":
        p = max(p.geoms, key=lambda g: g.area)
    s = 25.4 / 72 * esc / k                     # mm reales por píxel
    pts = [((x - eje_px) * s, (z0_px - y) * s) for x, y in p.exterior.coords]
    return sg.Polygon(pts).simplify(0.15)

def agujero(base, idh, esc, eje_px, z0_px):
    lab = np.load(f"{SP}/{base}_lab.npy"); meta = json.load(open(f"{SP}/{base}.json")); k = meta["k"]
    ys, xs = np.nonzero(lab == idh); s = 25.4 / 72 * esc / k
    r = (np.sqrt(len(xs) / np.pi) + 4) * s
    return ((xs.mean() - eje_px) * s, (z0_px - ys.mean()) * s, r)

def ref(base, ids_collar, ids_rosca):
    lab = np.load(f"{SP}/{base}_lab.npy")
    yc = max(np.nonzero(np.isin(lab, ids_collar))[0]); yr = min(np.nonzero(np.isin(lab, ids_rosca))[0])
    return (yc + yr) / 2

out = {}
# F510 (1 kg, esc. 1:2,5): eje en x = 237 px
z0 = ref("f510r", [19, 20], [21, 22, 23, 24, 25, 26])
out["F510"] = dict(sup=perfil("f510r", [5, 6, 7], 2.5, 237, z0), inf=perfil("f510r", [3, 13], 2.5, 237, z0),
                   cuerpo=perfil("f510r", [4, 8, 9, 10, 11, 12, 14, 15, 16, 17, 18, 19, 20], 2.5, 237, z0),
                   piv=agujero("f510r", 7, 2.5, 237, z0), pas=agujero("f510r", 13, 2.5, 237, z0),
                   man=agujero("f510r", 12, 2.5, 237, z0))
z0 = ref("f192r", [26, 27], [28, 29, 30])
out["F192"] = dict(sup=perfil("f192r", [3, 4, 7], 4.0, 288, z0), inf=perfil("f192r", [5], 4.0, 288, z0),
                   cuerpo=perfil("f192r", [9, 6, 10, 11, 12, 13, 14, 15, 16, 17, 18, 20, 21, 22, 23, 24, 25, 26, 27], 4.0, 288, z0),
                   piv=agujero("f192r", 7, 4.0, 288, z0), man=agujero("f192r", 13, 4.0, 288, z0))
fig, axs = plt.subplots(1, 2, figsize=(16, 5))
res = {}
for ax, (v, d) in zip(axs, out.items()):
    res[v] = {}
    for n, g in d.items():
        if isinstance(g, sg.Polygon):
            x, y = g.exterior.xy; ax.plot(x, y, "-", lw=1); ax.text(g.centroid.x, g.centroid.y, n, color="r")
            res[v][n] = [list(map(lambda t: round(t, 2), c)) for c in g.exterior.coords]
            print(v, n, "bbox", [round(b, 1) for b in g.bounds], "pts", len(g.exterior.coords))
        else:
            ax.add_patch(plt.Circle(g[:2], g[2], fill=False, color="k")); res[v][n] = [round(t, 2) for t in g]
            print(v, n, [round(t, 2) for t in g])
    ax.set_aspect("equal"); ax.grid(True); ax.set_title(v); ax.axvline(0, color="gray"); ax.axhline(0, color="gray")
plt.savefig(f"{SP}/perfiles.png", dpi=80, bbox_inches="tight")
json.dump(res, open(f"{SP}/perfiles.json", "w"))

# ---- refinamientos: puente de la palanca F510 (tapada por la manija inferior), caja del cuerpo y centro del manómetro
def bbox_mm(base, ids, esc, eje_px, z0_px):
    lab = np.load(f"{SP}/{base}_lab.npy"); k = json.load(open(f"{SP}/{base}.json"))["k"]
    ys, xs = np.nonzero(np.isin(lab, ids)); s = 25.4 / 72 * esc / k
    return [round((xs.min() - eje_px) * s, 2), round((z0_px - ys.max()) * s, 2), round((xs.max() - eje_px) * s, 2),
            round((z0_px - ys.min()) * s, 2)]
z0a = ref("f510r", [19, 20], [21, 22, 23, 24, 25, 26]); z0b = ref("f192r", [26, 27], [28, 29, 30])
r5 = perfil("f510r", [5, 7], 2.5, 237, z0a); r6 = out["F510"]["sup"]
x5 = r5.bounds[2]; x6 = r6.bounds[0]
zb = min(z for x, z in r6.exterior.coords if x < x6 + 3); zt = max(z for x, z in r6.exterior.coords if x < x6 + 3)
sup510 = unary_union([r5, r6, sg.box(x5 - 2, zb, x6 + 2, zt)]).simplify(0.15)
res["F510"]["sup"] = [list(map(lambda t: round(t, 2), c)) for c in sup510.exterior.coords]
res["F510"]["cuerpo_bbox"] = bbox_mm("f510r", [4, 8, 9, 10, 11, 12, 14, 15, 16, 17, 18], 2.5, 237, z0a)
res["F510"]["man_bbox"] = bbox_mm("f510r", [10, 11, 12, 14, 15, 16], 2.5, 237, z0a)
res["F192"]["cuerpo_bbox"] = bbox_mm("f192r", [9, 6, 10, 11, 12, 13, 14, 15, 16, 17, 18, 20, 21, 22, 23, 24, 25, 26, 27], 4.0, 288, z0b)
res["F192"]["man_bbox"] = bbox_mm("f192r", [12, 13, 14, 15, 16, 17, 18, 21, 22, 23, 24, 25], 4.0, 288, z0b)
res["F192"]["salida_bbox"] = bbox_mm("f192r", [9, 6], 4.0, 288, z0b)
res["F510"]["salida_bbox"] = bbox_mm("f510r", [8], 2.5, 237, z0a)
for v in res:
    for n in ("cuerpo_bbox", "man_bbox", "salida_bbox"):
        print(v, n, res[v][n])
print("F510 sup", [round(b, 1) for b in sup510.bounds])
json.dump(res, open(f"{SP}/perfiles.json", "w"))
fig, ax = plt.subplots(figsize=(8, 4)); x, y = sup510.exterior.xy; ax.plot(x, y)
x, y = out["F510"]["inf"].exterior.xy; ax.plot(x, y); ax.set_aspect("equal"); ax.grid(True)
plt.savefig(f"{SP}/f510sup.png", dpi=70, bbox_inches="tight")
