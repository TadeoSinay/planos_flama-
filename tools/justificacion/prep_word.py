import json, collections
SP = "/tmp/claude-0/-home-user-TP-optimizacion/15292aaf-e550-5dee-a83e-77fd9177a6ef/scratchpad"
rows = json.load(open(f"{SP}/jw/crudo.json"))
figs = json.load(open(f"{SP}/jw/figs.json"))
for r in rows:
    r["src"] = [k for k in r["src"] if k not in ("N:2533", "N:3517", "N:3533")]
    if r["dim"] == "Rango y sector verde":
        r["tipo"], r["estado"] = "Diseño FLAMA (supuesto)", "E"


def corto(m):
    return m.replace("FL_MAT_", "").replace("_", " ").replace("kg", " kg").replace("l", " l").replace("  ", " ") \
        .replace("SALESK", "Sales K").replace("CLASED", "Clase D").replace("HCFC-HF", "HCFC-HF")


def fmt(v):
    if isinstance(v, float):
        s = f"{v:.2f}".rstrip("0").rstrip(".")
        return s.replace(".", ",")
    return str(v)


SECC = [
    ("Planos Fadesa de recipiente", "Cotas de los planos de recipiente de referencia. Son la base de la geometría de los "
     "recipientes de 1 a 50 kg (y del cuello y la proporción de cabezal de 70 / 100 kg).", ["F01", "F02", "F03", "F04", "F05", "F06"]),
    ("Planos Fadesa de extintor completo", "Masa total de cada extintor (referencia de la verificación de masa), tipo de "
     "válvula y cotas generales.", ["F07", "F08", "F09", "F10", "F11", "F12", "F13"]),
    ("Catálogo Fadesa 3", "Peso cargado, altura, ancho, profundidad, rueda, manga y presiones de cada modelo. La envolvente "
     "de cada plano se ajusta a estos valores.", ["F14", "F15", "F16", "F17", "F18", "F19", "F20", "F21", "F22", "F23"]),
    ("Fichas técnicas de mercado", "Masa de referencia de los modelos sin plano Fadesa.", ["F24", "F25"]),
    ("Normas IRAM y resoluciones", "Sólo la cláusula usada (se cita, no se transcribe la norma).", ["F26", "F27", "F28", "F29", "F30"]),
    ("Relevamiento de mercado", "Fotos de equipos instalados y de la línea de etiquetado. Las medidas se estimaron por "
     "proporción: quedan a validar (naranja).", ["F31", "F32", "F33", "F34", "F35"]),
    ("Planilla MP FLAMA", "Celdas de la planilla de abastecimiento usadas para recortes, discos y caño.", ["F36", "F37"]),
    ("Valores de diseño FLAMA (código del generador)", "Lo que no sale de un documento externo es una decisión de diseño "
     "FLAMA escrita en el generador de planos. Se muestra la línea exacta (resaltada) y el link a GitHub. Estos valores "
     "están en amarillo en el Excel: hay que confirmarlos con el proveedor o con el prototipo.",
     ["F38", "F39", "F40", "F41", "F42", "F43", "F44", "F45", "F46", "F47"]),
]
byid = {f["id"]: f for f in figs}
out = []
for tit, intro, ids in SECC:
    fs = []
    for fid in ids:
        f = dict(byid[fid])
        code = f["tipo"].startswith("Diseño")
        for m in f["marcas"]:
            us = [r for r in rows if set(r["src"]) & set(m["claves"])]
            if code:
                m["usos"], m["mas"] = [], 0
                continue
            vistos = []
            for r in us:
                t = f"{corto(r['modelo'])} — {r['pieza']}: {r['dim']} = {fmt(r['valor'])} {r['unidad'] if r['unidad'] != '-' else ''}".strip()
                if t not in vistos:
                    vistos.append(t)
            m["usos"], m["mas"] = vistos[:6], max(0, len(vistos) - 6)
        if code:
            claves = {k for m in f["marcas"] for k in m["claves"]}
            us = [r for r in rows if set(r["src"]) & claves]
            g = collections.OrderedDict()
            for r in us:
                g.setdefault(r["pieza"], set()).add(r["modelo"])
            f["usos_global"] = [f"{p} ({len(ms)} modelo{'s' if len(ms) > 1 else ''})" for p, ms in g.items()]
            f["n_usos"] = len(us)
        fs.append(f)
    out.append(dict(titulo=tit, intro=intro, figs=fs))
cnt = collections.Counter(r["tipo"] for r in rows)
est = collections.Counter(r["estado"] for r in rows)
pend = collections.OrderedDict()
for r in rows:
    if r["estado"] == "A":
        pend.setdefault(f"{r['pieza']}: {r['dim']}", set()).add(corto(r["modelo"]))
json.dump(dict(secciones=out, tipos=sorted(cnt.items(), key=lambda x: -x[1]), estados=dict(est), n=len(rows),
               pendientes=[f"{k} — " + ("los 17 modelos" if len(v) == 17 else ("16 modelos (todos menos ABC 1 kg)" if len(v) == 16 else ", ".join(sorted(v)))) for k, v in pend.items()]),
          open(f"{SP}/jw/word.json", "w"), ensure_ascii=False, indent=1)
print("ok", len(rows), dict(est), len(pend))
