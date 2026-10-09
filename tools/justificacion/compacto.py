"""Datos comunes de la justificación compacta (Excel matriz por familia + Word con capturas de a dos).

Uso: python compacto.py <sha>  ->  compacto.json (lo leen xlsx_compacto.py y node/word2.js)
"""
import collections
import json
import re
import sys

SP = "/tmp/claude-0/-home-user-TP-optimizacion/15292aaf-e550-5dee-a83e-77fd9177a6ef/scratchpad"
REPO = "/home/user/planos_flama-"
SHA = sys.argv[1]
GH = f"https://github.com/TadeoSinay/planos_flama-/blob/{SHA}/flama/"

rows = json.load(open(f"{SP}/jw/crudo.json"))
figs = json.load(open(f"{SP}/jw/figs.json"))

FAM = collections.OrderedDict([
    ("Manuales ABC", ["FL_MAT_ABC_1kg", "FL_MAT_ABC_2.5kg", "FL_MAT_ABC_5kg", "FL_MAT_ABC_10kg"]),
    ("Rodantes ABC", ["FL_MAT_ABC_25kg", "FL_MAT_ABC_50kg", "FL_MAT_ABC_70kg", "FL_MAT_ABC_100kg"]),
])
FAM["Revendidos"] = [m for m in dict.fromkeys(r["modelo"] for r in rows) if not any(m in v for v in FAM.values())]


def corto(m):
    return (m.replace("FL_MAT_", "").replace("_", " ").replace("kg", " kg").replace("SALESK", "Sales K")
            .replace("CLASED", "Clase D").replace("AFFF 10l", "AFFF 10 l").replace("AFFF 50l", "AFFF 50 l")
            .replace("AGUA 10l", "Agua 10 l").replace("6l", "6 l").replace("9l", "9 l"))


# ------------------------------------------------------------- clave de fuente -> «F10·3»
k2m = collections.defaultdict(list)
for f in figs:
    for m in f["marcas"]:
        for k in m["claves"]:
            k2m[k].append(f"{f['id']}·{m['n']}")
TEXTO = {"N:3517": "IRAM 3517-2 9.4.13", "N:2533": "IRAM 2533", "N:3533": "IRAM 3533", "FR:1kg:cuello_h": "F01 nota",
         "CALC": "cálculo"}


# ------------------------------------------------------------- valores de diseño FLAMA -> D01…
def linea(archivo, patron):
    for i, s in enumerate(open(f"{REPO}/flama/{archivo}", encoding="utf-8"), 1):
        if patron in s:
            return i
    raise KeyError(f"{archivo}: {patron}")


def es_diseno(r):
    return r["estado"] == "E" or any(k.startswith("C:") for k in r["src"]) and r["tipo"] != "Cálculo"


dis = collections.OrderedDict()
for r in rows:
    if es_diseno(r):
        dis.setdefault(tuple(r["code"]), []).append(r)
D = []
dmap = {}
for i, (code, rs) in enumerate(dis.items(), 1):
    did = f"D{i:02d}"
    dmap[code] = did
    archivo, patron = code
    ln = linea(archivo, patron)
    piezas = list(dict.fromkeys(f"{r['pieza']}: {r['dim']}" for r in rs))
    modelos = sorted({r["modelo"] for r in rs})
    D.append(dict(id=did, archivo=archivo, linea=ln, link=f"{GH}{archivo}#L{ln}", que="; ".join(piezas[:4]) +
                  (f" (+{len(piezas) - 4})" if len(piezas) > 4 else ""), criterio=rs[0]["calc"],
                  modelos=("los 17" if len(modelos) == 17 else f"{len(modelos)} modelos" if len(modelos) > 3
                           else ", ".join(corto(m) for m in modelos)),
                  estado="A" if any(r["estado"] == "A" for r in rs) else "E"))


def fuente(r):
    refs = []
    for k in r["src"]:
        if k in k2m:
            refs += k2m[k][:1]
        elif k in TEXTO:
            refs.append(TEXTO[k])
        elif k.startswith("C:"):
            refs.append(dmap.get(tuple(r["code"]), "cálculo"))
    if es_diseno(r) and tuple(r["code"]) in dmap:
        refs.append(dmap[tuple(r["code"])])
    refs = list(dict.fromkeys(x for x in refs if x != "cálculo" or len(refs) == 1))
    destino = next((x.split("·")[0] for x in refs if re.match(r"F\d\d", x)), None) or \
        next((x for x in refs if re.match(r"D\d\d", x)), None)
    return " + ".join(refs), destino


def num(v):
    if isinstance(v, str):
        return re.sub(r"(\d)\.(\d)", r"\1,\2", v)
    return v


# ------------------------------------------------------------- matriz por familia
hojas = []
for fam, ms in FAM.items():
    orden = []  # [(pieza, dim, unidad)]
    celdas = {}
    for m in ms:
        prev = None
        for r in (x for x in rows if x["modelo"] == m):
            key = (r["pieza"], r["dim"])
            if key not in [o[:2] for o in orden]:
                idx = None
                same = [j for j, o in enumerate(orden) if o[0] == r["pieza"]]
                if same:
                    idx = same[-1] + 1
                elif prev is not None:
                    idx = [o[:2] for o in orden].index(prev) + 1
                    while idx < len(orden) and orden[idx][0] == orden[idx - 1][0]:
                        idx += 1
                orden.insert(len(orden) if idx is None else idx, (r["pieza"], r["dim"], r["unidad"]))
            prev = key
            fu, dest = fuente(r)
            celdas[(key, m)] = dict(v=num(r["valor"]), f=fu, dest=dest, e=r["estado"], calc=r["calc"], tipo=r["tipo"])
    filas = []
    h_mod = [corto(m) for m in ms]
    for pieza, dim, un in orden:
        cs = [celdas.get(((pieza, dim), m)) for m in ms]
        calcs = {c["calc"] for c in cs if c}
        # criterio común: el texto del primer modelo sin los números propios del modelo
        base = next(c["calc"] for c in cs if c)
        comun = base if len(calcs) == 1 else re.sub(r"\s*\(?[-+]?\d+(?:[.,]\d+)?\)?\s*(?:mm|kg|%|°)?", " ", base)
        comun = re.sub(r"\s{2,}", " ", re.sub(r"\(\s*[;,]?\s*\)", "", comun)).strip(" ;:,")
        if len(calcs) > 1:
            grupos = collections.OrderedDict()
            for mod, c in zip(h_mod, cs):
                if c:
                    grupos.setdefault(c["calc"], []).append(mod)
            esq = {re.sub(r"\d+(?:[.,]\d+)?", "#", k) for k in grupos}
            if len(esq) == 1:
                crit = f"{next(iter(grupos.values()))[0]}: {base} (cada modelo con sus valores: ver el comentario)"
            else:
                crit = " · ".join(f"{', '.join(v)}: {k}" for k, v in grupos.items())
        else:
            crit = comun
        filas.append(dict(pieza=pieza, dim=dim, unidad=un, criterio=crit, varia=len(calcs) > 1, celdas=cs))
    hojas.append(dict(nombre=fam, modelos=[corto(m) for m in ms], codigos=ms, filas=filas))

# ------------------------------------------------------------- pendientes (naranja)
pend = collections.OrderedDict()
for r in rows:
    if r["estado"] == "A":
        pend.setdefault((r["pieza"], r["dim"], r["calc"]), set()).add(r["modelo"])
PEND = []
for (p, d, c), ms in pend.items():
    PEND.append(dict(que=f"{p}: {d}", modelos="los 17" if len(ms) == 17 else
                     ("16 (todos menos ABC 1 kg)" if len(ms) == 16 else ", ".join(corto(m) for m in sorted(ms))), criterio=c))

est = collections.Counter(r["estado"] for r in rows)
json.dump(dict(sha=SHA, hojas=hojas, disenos=D, pendientes=PEND, figs=figs, n=len(rows), estados=dict(est),
               tipos=collections.Counter(r["tipo"] for r in rows).most_common()),
          open(f"{SP}/jw/compacto.json", "w"), ensure_ascii=False, indent=0)
print("ok", len(rows), dict(est), [(h["nombre"], len(h["filas"])) for h in hojas], len(D), "diseños", len(PEND), "pendientes")
