"""Datos del Word «Justificación del BOM»: cada valor del BOM simple (salida/bom/FLAMA_BOM.xlsx) con su fuente, su
cálculo y su control contra la norma o la ficha del fabricante.

Uso: python datos_bom.py <salida.json> [cache.pkl]
  cache.pkl (opcional): bom_producto / bom_sustituto ya calculados {"prod": {...}, "cil": {...}, "sus": {...}}, para no
  volver a armar los modelos 3D (tardan unos 8 minutos).
"""
import json
import math
import os
import pickle
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from flama import bom as B                       # noqa: E402
from flama import bom_simple as S                # noqa: E402
from flama import materiales as MAT              # noqa: E402
from flama import recipientes as RC             # noqa: E402
from flama import sustituto as SU                # noqa: E402
from flama.catalogo import MODELOS               # noqa: E402
import textos                                    # noqa: E402

try:
    from CoolProp.CoolProp import PropsSI
except ImportError:                              # sin CoolProp: sólo gas ideal
    PropsSI = None

OUT = sys.argv[1]
if len(sys.argv) > 2:
    C = pickle.load(open(sys.argv[2], "rb"))
    B.bom_producto = lambda m, cilindro=False: C["cil" if cilindro else "prod"][m.codigo]
    SU.bom_sustituto = lambda m: C["sus"][m.codigo]

R_GAS, T_REF = 8.314, 293.15
RLL_IRAM2533 = 0.68          # kg/L, IRAM 2533:2004 7.9 tabla 1 (CO₂, 65 °C)
FLUIDO = {"N₂": "Nitrogen", "Aire comprimido": "Air", "Argón": "Argon"}
M_REAL = {"N₂": 28.014, "Aire comprimido": 28.965, "Argón": 39.948}     # g/mol
NOMBRE = {m.codigo: m.nombre for m in MODELOS}


def r(x, n=3):
    return None if x is None else round(x, n)


def pct(a, b):
    return None if not b else round(100 * (a - b) / b, 1)


# ------------------------------------------------------------------ densidades
materiales = [
    dict(mat="Acero al carbono (SAE 1010 / 1045, chapa LAC)", rho=MAT.ACERO, rango="7,85 (valor de tabla del acero)",
         uso="Cuerpo, cúpula, fondo, cuello, manijas, suncho, soporte, carro"),
    dict(mat="Acero inoxidable AISI 302 / 304", rho=MAT.INOX, rango="7,93 (ASTM A240, AISI 304)",
         uso="Resorte, eje de palanca, pasador de seguridad"),
    dict(mat="Latón forjado (CuZn39Pb2 / C37700)", rho=MAT.LATON, rango="8,4-8,5 (latones de forja)",
         uso="Cuerpo de válvula, collarín, vástago, espiga, racor"),
    dict(mat="Aluminio", rho=MAT.ALUMINIO, rango="2,70", uso="Piezas de aluminio de válvulas compradas"),
    dict(mat="Caucho sintético (NBR / SBR)", rho=MAT.CAUCHO, rango="1,1-1,3", uso="Manguera, juntas, neumático"),
    dict(mat="Polipropileno", rho=MAT.PP, rango="0,90-0,91", uso="Tobera, lanza, empuñadura, filtro, precinto"),
    dict(mat="Polietileno de alta densidad", rho=MAT.PE, rango="0,94-0,97", uso="Difusor, pie de apoyo"),
    dict(mat="PVC rígido / vinilo de etiquetas", rho=MAT.PVC, rango="1,35-1,45", uso="Caño de pesca, etiquetas, obleas"),
]
llenado = [dict(pieza=v[0], material=v[1], factor=v[3], obs=v[4] or "")
           for k, v in MAT.PIEZAS.items() if v and v[3] < 1.0]

FUENTE = {"AGUA": "Agua potable de red: 1,000 kg/L"}
agentes = []
for k, v in B.AGENTES.items():
    agentes.append(dict(clave=k, nombre=v[0], rho_min=v[5], rho_tip=v[6], rho_max=v[7], fuente=FUENTE.get(k, v[8]),
                        gas=v[4], empacada=B.RHO_EMPACADA.get(k)))
gases = []
for g, M in B.MOLAR.items():
    rho_n = M / S.VOL_MOLAR_N
    real = M_REAL[g] / 1000 / S.VOL_MOLAR_N
    gases.append(dict(gas=g, M=M * 1000, rho_n=r(rho_n, 6), rho_real=r(real, 6), dif=pct(rho_n, real)))

# ------------------------------------------------------------------ carga por modelo
cargas = []
for m in MODELOS:
    ag = B._agente(m)
    nombre, q, um, n_ag, gas, m_gas, nm3, libre = B.carga(m)
    tol, obj, ref_tol = B.tolerancia(m)
    n = m.spec["Norma IRAM extintor"]
    V = float(m.geo["vol_dm3"])
    ps = B._ps(m)
    d = dict(codigo=m.codigo, nombre=m.nombre, norma=n, agente=ag, q=q, um=um, tol=tol, obj=r(obj, 3), V=V, ps=ps,
             pe=float(m.spec["Presión de ensayo (MPa)"].replace(",", ".")), gas=gas, propio=m.codigo in B.PROPIOS)
    if ag == "CO2":
        d.update(rho=r(q / V, 3), v_ag=V, ocup=None, rll=r(q / V, 3), rll_max=RLL_IRAM2533,
                 rll_ok=q / V <= RLL_IRAM2533, libre=0.0, m_gas=0.0)
    else:
        if um == "L":
            rho = B.RHO_AFFF_CONC * 0.03 + 0.97 if ag == "AFFF" else B.RHO_AGENTE.get(ag, 1.0)
            v_ag = obj
        else:
            rho = B.RHO_EMPACADA.get(ag, B.RHO_AGENTE[ag])
            v_ag = obj / rho
        v_peor = obj / B.AGENTES[ag][5] if um == "kg" else v_ag            # densidad mínima de la ficha
        pa = (ps + 0.101325) * 1e6
        n_mol = pa * libre * 1e-3 / (R_GAS * T_REF)
        m_real = None
        if PropsSI is not None and libre > 0:
            m_real = PropsSI("D", "T", T_REF, "P", pa, FLUIDO[gas]) * libre * 1e-3
        d.update(rho=r(rho, 4), v_ag=r(v_ag, 3), ocup=r(100 * v_ag / V, 1), v_peor=r(v_peor, 3),
                 ocup_peor=r(100 * v_peor / V, 1), libre=r(libre, 3), m_gas=r(m_gas, 4), nl=r(nm3 * 1000, 1),
                 m_gas_real=r(m_real, 4), dif_real=pct(m_gas, m_real) if m_real else None,
                 masa_ag=r(obj * rho if um == "L" else obj, 3))
    cargas.append(d)

# ------------------------------------------------------------------ masas: BOM contra referencia
masas, subconj = [], []
fab = [m for m in MODELOS if m.codigo in B.PROPIOS]
rev = [m for m in MODELOS if m.codigo not in B.PROPIOS]
for m in fab + rev:
    filas = S.estructura(m)
    total = filas[0][8]
    soporte = sum(f[8] or 0 for f in filas if f[0] == 1 and f[1].endswith("-S8"))   # el peso cargado no lo incluye
    cargado = total - soporte
    ref, fuente = B.peso_ref(m)
    fuente = "Catálogo Fadesa 3 (orientativo)" if fuente.startswith("Catálogo") else fuente
    cat = float(m.spec["Peso cargado (kg)"].replace(",", "."))
    sin_masa = sorted({f[2] for f in filas if f[0] >= 2 and f[7] is None and f[4] == "u"})
    masas.append(dict(codigo=m.codigo, nombre=m.nombre, propio=m.codigo in B.PROPIOS, total=r(total, 2),
                      soporte=r(soporte, 3), bom=r(cargado, 2), ref=ref, fuente=fuente, dif=pct(cargado, ref),
                      catalogo=cat, dif_cat=pct(cargado, cat), sin_masa=sin_masa))
    subconj.append(dict(codigo=m.codigo, partes=[(f[2], r(f[8], 3)) for f in filas if f[0] == 1]))

cilindros = []
for m in RC.modelos_abc():
    filas = S.estructura(m, cilindro=True)
    cilindros.append(dict(codigo=m.codigo, nombre=filas[0][2], masa=r(filas[0][8], 3),
                          partes=[(f[2], r(f[8], 3)) for f in filas if f[0] == 2 and f[8]]))

# ------------------------------------------------------------------ piezas principales de los fabricados
piezas = []
CLAVE = ("Cuerpo", "Cúpula", "Fondo", "Cuello", "Válvula HZ", "Manguera", "Soporte de pared")
for m in fab:
    filas = S.estructura(m)
    fila = {"codigo": m.codigo}
    for f in filas:
        for c in CLAVE:
            if f[2].startswith(c) and c not in fila:
                fila[c] = dict(vol=r(f[6], 4), rho=f[5], masa=r(f[7], 3), cant=f[3])
    piezas.append(fila)

# ------------------------------------------------------------------ sustituto
sustitutos = []
for m in MODELOS:
    rows = SU.bom_sustituto(m)
    faja = next((x for x in rows if x["codigo"].endswith("-01")), None)
    eq = SU.equivalencia(m)[3].replace("igual clasificación e igual capacidad (mismo modelo)", "").strip("; ")
    alto = float(faja["med"].split(" × ")[0]) if faja else 0
    sustitutos.append(dict(codigo=m.codigo, nombre=m.nombre, faja=faja["med"].split(" (")[0] if faja else "",
                           nota="; ".join(x for x in [eq, "alto < 40: lo limita la oblea PBA" if alto < 40 else ""] if x)))

# ------------------------------------------------------------------ recargas
recargas = []
for m in MODELOS:
    _, q, um, *_ = B.carga(m)
    tol, obj, _ = B.tolerancia(m)
    n = m.spec["Norma IRAM extintor"]
    rep = B.reposicion(m)
    g = S.gas(m)
    recargas.append(dict(codigo=m.codigo, nombre=m.nombre, norma=n, q=q, um=um, tol=tol, obj=r(obj, 3),
                         agente_polvo=B._agente(m) in ("ABC", "BC", "D"),
                         lim_inf=r(obj - rep, 3) if rep is not None else None, rep=r(rep, 3),
                         rep_pct=r(100 * rep / q, 1) if rep is not None else None,
                         ph=S.INTERVALO_PH.get(n, 5), gas=g[0].split(": ")[1] if g else "-",
                         m_gas=r(g[2], 4) if g else 0.0,
                         servicios=[(t, len(f)) for t, f in S.servicios(m)]))

D = dict(materiales=materiales, llenado=llenado, agentes=agentes, gases=gases, cargas=cargas, masas=masas,
         subconj=subconj, cilindros=cilindros, piezas=piezas, sustitutos=sustitutos, recargas=recargas,
         rll_iram2533=RLL_IRAM2533, afff_conc=B.RHO_AFFF_CONC, fuente_empacada=B.FUENTE_EMPACADA)
D["notas"] = textos.notas(D)
json.dump(D, open(OUT, "w"), ensure_ascii=False, indent=1)
print("ok", OUT, len(cargas), "modelos")
