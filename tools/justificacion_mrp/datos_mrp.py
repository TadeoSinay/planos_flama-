"""Datos del Word «Justificación_MRP», leídos del propio FLAMA_MRP.xlsx recalculado (así el Word y el Excel salen
de las mismas fórmulas), más la comparación con los números de los documentos de proceso.

Uso: python datos_mrp.py <FLAMA_MRP.xlsx recalculado> <salida.json>
"""
import json
import os
import sys

from openpyxl import load_workbook

AQUI = os.path.dirname(os.path.abspath(__file__))
XLSX, OUT = sys.argv[1], sys.argv[2]
wb = load_workbook(XLSX, data_only=True)
AÑOS = list(range(2026, 2036))


def filas(hoja, fila_cab, desde=None):
    ws = wb[hoja]
    cab = [c.value for c in ws[fila_cab]]
    out = []
    for f in ws.iter_rows(min_row=desde or fila_cab + 1, values_only=True):
        out.append(dict(zip(cab, f)))
    return out


def r(x, n=2):
    return round(x, n) if isinstance(x, (int, float)) else x


# ------------------------------------------------------------------ parámetros
par, par_y = [], []
ws = wb["PARAMETROS"]
modo = 0
for f in ws.iter_rows(min_row=4, values_only=True):
    if f[0] == "PARÁMETROS POR AÑO":
        modo = 1
        continue
    if f[0] == "ID":
        continue
    if f[0] and modo == 0:
        par.append(dict(id=f[0], dato=f[1], valor=r(f[2], 4), unidad=f[3], fuente=f[4], nota=f[5] or ""))
    elif f[0] and modo == 1:
        par_y.append(dict(id=f[0], dato=f[1], valores=[r(x, 4) for x in f[2:12]], fuente=f[12]))
P = {x["id"]: x["valor"] for x in par}

# ------------------------------------------------------------------ demanda
dem = [x for x in filas("DEMANDA", 3) if x.get("Línea")]
tot = {}
for x in filas("DEMANDA", 3):
    if x.get("Producto") and str(x["Producto"]).startswith("Total "):
        tot[x["Producto"][6:]] = [r(x[a], 0) for a in AÑOS]
demanda = [dict(linea=x["Línea"], clave=x["Clave"], producto=x["Producto"], origen=x["Origen (fila de las Proyecciones)"],
                perfil=x["Perfil estacional"], d2026=r(x[2026], 0), d2030=r(x[2030], 0), d2035=r(x[2035], 0))
           for x in dem]

# ------------------------------------------------------------------ estacionalidad
ws = wb["ESTACIONALIDAD"]
perfiles, lineas = [], {}
for f in ws.iter_rows(min_row=4, max_row=40, max_col=14, values_only=True):
    if f[0] in ("MANUALES", "RODANTES", "RECARGAS", "REVENDIDOS"):
        lineas[f[0]] = dict(meses=[r(x, 4) for x in f[1:13]], factor=r(f[13], 3))
    elif f[0] and isinstance(f[1], (int, float)) and len(perfiles) < 6:
        perfiles.append(dict(nombre=f[0], meses=[r(x, 3) for x in f[1:13]]))

# ------------------------------------------------------------------ compras y política
compras = [x for x in filas("COMPRAS", 3) if x.get("Código")]
pol = [x for x in filas("POLITICA_STOCK", 3) if x.get("Código")]
POL = {x["Código"]: x for x in pol}
almacenes = []
ws = wb["POLITICA_STOCK"]
en = False
for f in ws.iter_rows(min_row=4, values_only=True):
    if f[1] == "Almacén":
        en = True
        continue
    if en and f[1]:
        almacenes.append(dict(almacen=f[1], pos=f[4], cap=f[5], res=f[6], m2=r(f[7], 1), segun=f[8] or ""))
cons = [x for x in filas("CONSOLIDADO_INSUMOS", 3) if x.get("Código")]
cons0 = [x for x in cons if x["Nivel"] == 0]


def dia(cod, lin):
    x = POL.get(cod)
    return None if not x else x[lin] / P["DH_AÑO"] * lineas[lin]["factor"]


validacion = [
    ("Caños Ø76,2 de 1 kg por día (pico)", dia("MP-01", "MANUALES"), 53, "Proceso de manuales, corte de tubo (P03)"),
    ("Hojas LAF 1,25 (2,5 kg) por día (pico)", dia("MP-02", "MANUALES"), 3.7, "Proceso de manuales, guillotina"),
    ("Hojas LAF 1,6 (5 kg) por día (pico)", dia("MP-03", "MANUALES"), 37.1, "Proceso de manuales, guillotina"),
    ("Hojas LAF 2,0 (10 kg) por día (pico)", dia("MP-04", "MANUALES"), 1.8, "Proceso de manuales, guillotina"),
    ("Granalla de manuales, kg por día (pico)", dia("MP-28", "MANUALES"), 133, "Proceso de manuales, granallado (P04)"),
    ("Nitrógeno de manuales, m³ por día (pico)", dia("MP-34", "MANUALES"), 7.1, "Proceso de manuales, presurización"),
    ("Gas MAG de manuales, m³ por día (pico)", dia("MP-25", "MANUALES"), 48, "Proceso de manuales, recepción (P01)"),
    ("Polvo ABC 60 de manuales, kg por día (pico)", dia("MP-33", "MANUALES"), 1700, "Proceso de manuales, recepción"),
    ("Polvo ABC 60 de manuales, kg por día (promedio)", POL["MP-33"]["MANUALES"] / P["DH_AÑO"], 900,
     "Proceso de manuales, recepción"),
    ("Hojas LAC 3,2 de carros por día (pico)", dia("MP-11", "RODANTES"), 2.39, "Proceso de carros, tabla 3 (P06)"),
    ("Hojas LAC 4,75 de carros por año", POL["MP-12"]["RODANTES"], 0.7 * 240, "Proceso de carros: 0,7 hojas por día "
     "en el promedio × 240"),
    ("Casquetes 12\" por día (pico)", dia("MP-16", "RODANTES"), 22, "Proceso de carros, tabla 3"),
    ("Cuplas M30 por día (pico)", dia("MP-20", "RODANTES"), 16, "Proceso de carros, tabla 3"),
    ("Polvo ABC 90 de carros, kg por día (pico)", dia("MP-33B", "RODANTES"), 995, "Proceso de carros, tabla 3"),
    ("Recipientes de carros por día (pico)", tot["RODANTES"][-1] / P["DH_AÑO"] * lineas["RODANTES"]["factor"], 20,
     "Proceso de carros (20 por día en el pico y 14 en el promedio)"),
    ("Recipientes de carros por día (promedio)", tot["RODANTES"][-1] / P["DH_AÑO"], 14, "Proceso de carros"),
    ("Factor de pico de manuales", lineas["MANUALES"]["factor"], 1665 / 1184, "Proceso de manuales: 1.665 / 1.184 "
     "cilindros por día"),
    ("Factor de pico de carros", lineas["RODANTES"]["factor"], 20 / 14, "Proceso de carros: 20 / 14"),
]
validacion = [dict(dato=a, mrp=r(b, 2), doc=r(c, 2), dif=r(100 * (b - c) / c, 1), fuente=d) for a, b, c, d in validacion]

# coeficientes destacados
ws = wb["FAB_COMPRA"]
fab = [dict(modelo=f[0], pieza=f[1], hace=f[2], item=f[3], um=f[4], ancho=f[6], d=f[7], e=f[8], rend=f[9],
            factor=r(f[10], 5)) for f in ws.iter_rows(min_row=4, values_only=True) if f[0]]
ws = wb["PROCESO"]
proc = [dict(linea=f[0], puesto=f[1], item=f[2], um=f[3], tipo=f[4], modelo=f[5], aplica=f[6], base=f[7],
             coef=r(f[8], 6), fuente=f[9]) for f in ws.iter_rows(min_row=4, values_only=True) if f[0]]
carro = {}
for x in proc:
    if x["linea"] == "RODANTES" and x["item"] in ("MP-25", "MP-24"):
        carro.setdefault(x["modelo"], {}).setdefault(x["item"], 0)
        carro[x["modelo"]][x["item"]] += x["coef"]
man = {x["modelo"]: {} for x in proc if x["linea"] == "MANUALES"}
for x in proc:
    if x["linea"] == "MANUALES" and x["item"] in ("MP-25", "MP-23", "MP-31", "MP-28"):
        man[x["modelo"]][x["item"]] = x["coef"]

bc = filas("BOM_COEF", 3)
trat = {}
for x in bc:
    if x.get("Producto"):
        trat[x["Tratamiento"] or "Sin compra"] = trat.get(x["Tratamiento"] or "Sin compra", 0) + 1
rec5 = [dict(item=x["Ítem de compra"], pieza=x["Pieza / insumo (BOM)"], um=x["UM"], ctrl=x["Control"],
             mant=r(x["Mantenimiento"], 4), rec=r(x["Recarga"], 4), ph=x["Prueba hidráulica"], anios=x["PH cada (años)"],
             rep=r(x["Reposición"], 3), coef=r(x["Coef. 2035"], 4)) for x in bc if x.get("Producto") == "RK_ABC_5kg"
        and x.get("Ítem de compra")]

origen_lt = {}
for x in compras:
    origen_lt[x["Origen del lead time"]] = origen_lt.get(x["Origen del lead time"], 0) + 1

D = dict(par=par, par_y=par_y, demanda=demanda, totales=tot, perfiles=perfiles, lineas=lineas,
         compras=[{k: (r(v, 3) if isinstance(v, float) else v) for k, v in x.items()} for x in compras],
         politica=[{k: (r(v, 3) if isinstance(v, float) else v) for k, v in x.items()} for x in pol],
         almacenes=almacenes, consolidado=[{k: (r(v, 2) if isinstance(v, float) else v) for k, v in x.items()}
                                           for x in cons0],
         validacion=validacion, fab=fab, carro={k: {i: r(v, 4) for i, v in d.items()} for k, d in carro.items()},
         man=man, tratamientos=trat, rec5=rec5, origen_lt=origen_lt,
         capturas=json.load(open(os.path.join(AQUI, "capturas.json"))))
json.dump(D, open(OUT, "w"), ensure_ascii=False, indent=1, default=str)
print("ok", OUT, len(compras), "ítems", len(pol), "en la política")
