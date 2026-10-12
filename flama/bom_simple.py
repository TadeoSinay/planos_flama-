"""BOM de FLAMA para leer: la estructura de cada producto y sus números, con fórmulas (salida/bom/FLAMA_BOM.xlsx).

Hojas
  REFERENCIAS  cada dato que entra en una cuenta, con ID, valor, mínimo, máximo, unidad y fuente (cláusula de norma o
               ficha del fabricante): densidades, tolerancias de carga (IRAM 3517-2 tabla 3), gases, constantes,
               intervalos de prueba hidráulica (anexo E) y la tolerancia general ISO 2768-m de los planos
  MODELOS      por extintor: carga objetivo y su banda, volumen del agente y del recipiente, volumen libre, gas
               impulsor (gas ideal a la presión de servicio) con su mínimo y máximo, relación de llenado del CO₂ y
               reposición de agente en el mantenimiento. Todo con fórmulas que leen REFERENCIAS
  Fabricados   los 8 ABC propios; al final de cada uno, lo que se agrega si va como sustituto (IRAM 3517-2 9.4.5)
  Revendidos   los 9 equipos que se compran terminados, con el mismo agregado de sustituto
  Cilindros    los 8 recipientes ABC vendidos sueltos (planos FL_REC)
  Recargas     por extintor, los servicios de la IRAM 3517-2:2020: control periódico (8.2), mantenimiento (9.2.1),
               recarga (9.2.2) y prueba hidráulica (9.7, anexo E)

Columnas del BOM: Nivel, Código, Pieza, Ref. (ID de REFERENCIAS), Material / agente, Cant., UM, Densidad, Volumen
total, mínimo y máximo, Masa unitaria, Masa total, mínima y máxima. A la derecha, plegadas, las columnas de cálculo
de la tolerancia: densidad mínima y máxima, volumen de una unidad, superficie, espesor equivalente, tolerancia
ISO 2768-m y tolerancia de volumen.
  piezas    volumen y superficie del sólido del modelo 3D (con el factor de llenado de las piezas huecas). Tolerancia de
            volumen = tolerancia ISO 2768-m del espesor equivalente (2 × volumen / superficie) dividida por ese espesor:
            es lo que cambia el volumen si todas las caras se corren lo que permite la tolerancia general del plano.
            Masa mínima y máxima = volumen extremo × densidad mínima y máxima del material
  agentes   cantidad = carga objetivo de MODELOS; mínimo y máximo = banda de la tabla 3
  CO₂       densidad = relación de llenado (kg por litro de cilindro); volumen = capacidad del cilindro
  gases     masa de MODELOS; volumen en litros normales (0 °C, 101,325 kPa); densidad normal del gas
Las filas que agrupan (producto, subconjunto, válvula comprada armada, servicio) suman la masa de sus hijos directos.

No lleva insumos de proceso (soldadura, granalla, pintura), embalaje ni materia prima: siguen en bom.py, que es lo
que usa el MRP, y en el libro completo de respaldo (salida/bom/respaldo/FLAMA_BOM_respaldo.xlsx). La justificación de
cada valor está en el Word «Justificación del BOM».
"""
import os
import re
import shutil
import subprocess
import tempfile
import zipfile

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.workbook.defined_name import DefinedName

from . import bom as B
from . import materiales as MAT
from . import recipientes as RC
from . import sustituto as SU
from .catalogo import MODELOS

NEGRO, GRIS_O, GRIS_C, GRIS_T, BLANCO = "000000", "595959", "E7E6E6", "F2F2F2", "FFFFFF"
VOL_MOLAR_N = 22.414                     # L/mol en condiciones normales (0 °C, 101,325 kPa)
P_ATM = 0.101325                         # MPa
INTERVALO_PH = {"3523": 5, "3550": 5, "3509": 5, "3565": 5, "3504": 5,
                "3525": 2, "3527": 2, "3537": 2, "3541": 2, "3694": 2, "3693": 2}    # años, anexo E

# ------------------------------------------------------------------ REFERENCIAS
# (ID, dato, valor, mín, máx, unidad, fuente, nota). Un ID vacío es un título de sección.
_TOL3 = "IRAM 3517-2:2020 9.4.12 tabla 3"
REFERENCIAS = [
    ("", "Materiales de las piezas (densidad)"),
    ("MAT_ACERO", "Acero (chapa LAC/LAF, SAE 1010/1045)", MAT.ACERO, MAT.ACERO, MAT.ACERO, "kg/L",
     "Valor de tabla del acero", ""),
    ("MAT_INOX", "Acero inoxidable AISI 302 / 304", MAT.INOX, MAT.INOX, MAT.INOX, "kg/L", "ASTM A240 (AISI 304)", ""),
    ("MAT_LATON", "Latón de forja (CuZn39Pb2 / C37700)", MAT.LATON, 8.40, 8.50, "kg/L", "Valores de tabla de latones de forja", ""),
    ("MAT_ALU", "Aluminio", MAT.ALUMINIO, MAT.ALUMINIO, MAT.ALUMINIO, "kg/L", "Valor de tabla del aluminio", ""),
    ("MAT_CAUCHO", "Caucho sintético (NBR / SBR)", MAT.CAUCHO, 1.10, 1.30, "kg/L", "Valores de tabla de elastómeros", ""),
    ("MAT_PP", "Polipropileno", MAT.PP, 0.90, 0.91, "kg/L", "Valores de tabla del PP", ""),
    ("MAT_PE", "Polietileno de alta densidad", MAT.PE, 0.94, 0.97, "kg/L", "Valores de tabla del PEAD", ""),
    ("MAT_PVC", "PVC rígido, vinilo y papeles de identificación", MAT.PVC, 1.35, 1.45, "kg/L",
     "Valores de tabla del PVC", "Etiquetas, obleas y tarjetas asimiladas al vinilo"),
    ("", "Agentes extintores (densidad)"),
    ("AG_ABC", "Polvo ABC asentado en el recipiente", B.RHO_EMPACADA["ABC"], B.RHO_EMPACADA["ABC"],
     B.RHO_EMPACADA["ABC"], "kg/L", "NOM-104-STPS-2001: empacada ≥ 1,10 · IRAM 3569 no fija densidad",
     "La NOM-104 da sólo el mínimo; se exige en la orden de compra"),
    ("AG_ABC_AP", "Polvo ABC aparente (suelto)", B.RHO_AGENTE["ABC"], B.AGENTES["ABC"][5], B.AGENTES["ABC"][7],
     "kg/L", "Ficha DEMSA ABC: aparente > 0,85", "Control de llenado sin vibrar (MODELOS)"),
    ("AG_BC", "Polvo BC (bicarbonato de sodio)", B.RHO_AGENTE["BC"], B.AGENTES["BC"][5], B.AGENTES["BC"][7], "kg/L",
     "Ficha DEMSA BC / Púrpura K: aparente > 0,85", "Revendido: lo carga su fabricante"),
    ("AG_D", "Polvo clase D (cloruro de sodio)", B.RHO_AGENTE["D"], B.AGENTES["D"][5], B.AGENTES["D"][7], "kg/L",
     "Ficha DEMSA polvo D: aparente > 0,85", "Revendido: lo carga su fabricante"),
    ("AG_HCFC", "HCFC Mezcla B (agente limpio)", B.RHO_AGENTE["HCFC"], B.AGENTES["HCFC"][5], B.AGENTES["HCFC"][7],
     "kg/L", "Ficha Halotron I: 1,48 kg/L a 25 °C", ""),
    ("AG_AGUA", "Agua potable", 1.0, 1.0, 1.0, "kg/L", "Agua de red", ""),
    ("AFFF_PROP", "Proporción de concentrado AFFF en la premezcla", 0.03, 0.03, 0.03, "fracción",
     "IRAM 3515 · ficha DEMSA 203 MN (3 %)", ""),
    ("AG_AFFF_C", "Concentrado espumígeno AFFF 3 %", B.RHO_AFFF_CONC, B.RHO_AFFF_CONC, B.RHO_AFFF_CONC, "kg/L",
     "Ficha DEMSA 203 MN: 1,025 g/cm³ a 20 °C", ""),
    ("AG_AFFF", "Premezcla AFFF 3 %", "=AFFF*CONC+(1-AFFF)*AGUA", "=AFFF*CONC+(1-AFFF)*AGUA",
     "=AFFF*CONC+(1-AFFF)*AGUA", "kg/L", "Cálculo: 3 % de concentrado + 97 % de agua", ""),
    ("AG_K", "Acetato de potasio (sales K)", B.RHO_AGENTE["K"], B.RHO_AGENTE["K"], B.RHO_AGENTE["K"], "kg/L",
     "Ficha DEMSA Kitchen: 1,300 g/mL a 20 °C", ""),
    ("AG_CO2", "Dióxido de carbono (IRAM 41170)", None, None, None, "kg/L",
     "La densidad del BOM es la relación de llenado de cada cilindro (MODELOS)", ""),
    ("RLL_CO2", "Relación de llenado máxima del CO₂", 0.68, None, 0.68, "kg/L", "IRAM 2533:2004 7.9 tabla 1", ""),
    ("", "Gases impulsores y constantes"),
    ("GAS_N2", "Nitrógeno seco (densidad normal)", "=M_N2/VM", None, None, "kg/L", "Masa molar / volumen molar normal",
     "IRAM 3517-2 9.4.9 tabla 2: polvo, sales K"),
    ("GAS_AIRE", "Aire comprimido (densidad normal)", "=M_AIRE/VM", None, None, "kg/L",
     "Masa molar / volumen molar normal", "Tabla 2: agua y AFFF (N₂ o aire)"),
    ("GAS_AR", "Argón (densidad normal)", "=M_AR/VM", None, None, "kg/L", "Masa molar / volumen molar normal",
     "Tabla 2, nota: el HCFC Mezcla B sólo admite argón"),
    ("M_N2", "Masa molar del nitrógeno", B.MOLAR["N₂"], None, None, "kg/mol", "Masa molar (28,01 g/mol, redondeada)", ""),
    ("M_AIRE", "Masa molar del aire", B.MOLAR["Aire comprimido"], None, None, "kg/mol",
     "Masa molar (28,97 g/mol, redondeada)", ""),
    ("M_AR", "Masa molar del argón", B.MOLAR["Argón"], None, None, "kg/mol", "Masa molar (39,95 g/mol, redondeada)", ""),
    ("VM", "Volumen molar normal (0 °C, 101,325 kPa)", VOL_MOLAR_N, None, None, "L/mol", "Constante física", ""),
    ("R_GAS", "Constante de los gases", 8.314, None, None, "J/(mol·K)", "Constante física", ""),
    ("P_ATM", "Presión atmosférica", P_ATM, None, None, "MPa", "Constante física", "Ps es manométrica"),
    ("T_REF", "Temperatura de carga y verificación", 293.15, 291.15, 295.15, "K", "IRAM 3523 2.3: 20 ± 2 °C", ""),
    ("PS_TOL", "Tolerancia de la presión de carga (zona verde del manómetro)", 0, -0.10, 0.10, "fracción",
     "NOM-045-SCFI (México): ±10 % de la nominal", "IRAM 3533 no disponible: verificar"),
    ("PS_MAX", "Presión de servicio máxima, manuales de polvo", 1.7, None, 1.7, "MPa", "IRAM 3523 4.7", ""),
    ("", "Tolerancia de carga (tabla 3): mín. y máx. respecto de la nominal"),
    ("T3_3523_A", "Polvo bajo presión manual, 1 y 2,5 kg", None, 0, 0.1, "kg", _TOL3 + " · IRAM 3523 tabla II", ""),
    ("T3_3523_B", "Polvo bajo presión manual, 5 y 10 kg", None, 0, 0.3, "kg", _TOL3 + " · IRAM 3523 tabla II", ""),
    ("T3_3550", "Polvo bajo presión sobre ruedas", None, -0.03, 0.03, "fracción", _TOL3, ""),
    ("T3_3525", "Agua bajo presión manual", None, -0.03, 0.03, "fracción", _TOL3, ""),
    ("T3_3527", "Agua con AFFF manual", None, -0.03, 0.03, "fracción", _TOL3, ""),
    ("T3_3541", "Agua con AFFF sobre ruedas", None, -0.03, 0.03, "fracción", _TOL3, ""),
    ("T3_3694", "Sales de potasio", None, 0, 0.03, "fracción", _TOL3, "IRAM 3694 5.5 admite +0,3 L en 6 L"),
    ("T3_3509", "Dióxido de carbono manual", None, -0.05, 0, "fracción", _TOL3, ""),
    ("T3_3504_A", "Gases limpios, 1 y 2,5 kg", None, -0.02, 0, "fracción", _TOL3, ""),
    ("T3_3504_B", "Gases limpios, 5 y 10 kg", None, -0.03, 0, "fracción", _TOL3, ""),
    ("", "Prueba hidráulica (anexo E)"),
    ("PH_5", "Polvo, CO₂ y gases limpios (IRAM 3523, 3550, 3509, 3565, 3504)", 5, None, None, "años",
     "IRAM 3517-2:2020 anexo E · 9.7", "Como máximo"),
    ("PH_2", "Agua, AFFF y sales de potasio (IRAM 3525, 3537, 3527, 3541, 3694)", 2, None, None, "años",
     "IRAM 3517-2:2020 anexo E · 9.7", "Como máximo"),
]
# tolerancia general de los planos: ISO 2768-1 clase m (rótulo de cada plano). Más de «desde» hasta «hasta» mm: ± mm
ISO_2768_M = [(0.5, 3, 0.1), (3, 6, 0.1), (6, 30, 0.2), (30, 120, 0.3), (120, 400, 0.5), (400, 1000, 0.8),
              (1000, 2000, 1.2), (2000, 4000, 2.0)]
ID_RHO = {MAT.ACERO: "MAT_ACERO", MAT.INOX: "MAT_INOX", MAT.LATON: "MAT_LATON", MAT.ALUMINIO: "MAT_ALU",
          MAT.CAUCHO: "MAT_CAUCHO", MAT.PP: "MAT_PP", MAT.PE: "MAT_PE", MAT.PVC: "MAT_PVC"}
ID_AGENTE = {"ABC": "AG_ABC", "BC": "AG_BC", "D": "AG_D", "HCFC": "AG_HCFC", "AGUA": "AG_AGUA", "AFFF": "AG_AFFF",
             "K": "AG_K", "CO2": "AG_CO2"}
ID_GAS = {"N₂": "GAS_N2", "Aire comprimido": "GAS_AIRE", "Argón": "GAS_AR"}


def ref_tolerancia(m):
    n = m.spec["Norma IRAM extintor"]
    _, q, *_ = B.carga(m)
    if n in ("3523", "3504"):
        return f"T3_{n}_{'A' if q <= 2.5 else 'B'}"
    return f"T3_{n}"


def ref_ph(m):
    return "PH_2" if INTERVALO_PH.get(m.spec["Norma IRAM extintor"], 5) == 2 else "PH_5"


# ------------------------------------------------------------------ fórmulas
def _r(campo, ref):
    """INDEX/MATCH de un campo de REFERENCIAS por ID (ref: celda o texto entre comillas)."""
    return f"INDEX(REF_{campo},MATCH({ref},REF_ID,0))"


# MODELOS: columnas
MC = {k: get_column_letter(i + 1) for i, k in enumerate([
    "cod", "nom", "norma", "ref_ag", "ref_gas", "ref_tol", "ref_ph", "nom_q", "um", "tol_m", "tol_p", "obj", "qmin",
    "qmax", "V", "rho", "rho_min", "rho_max", "Vag", "Vag_max", "Vag_min", "ocup", "ocup_max", "ocup_ap", "Vl", "Vl_min",
    "Vl_max", "ps", "ps_min", "ps_max", "M", "gas", "gas_min", "gas_max", "nl", "rll", "rll_max", "rll_ok", "ps_ok",
    "repo", "ph"])}
MCAB = ["Código", "Extintor", "Norma IRAM", "Ref. agente", "Ref. gas", "Ref. tolerancia", "Ref. prueba hidráulica",
        "Carga nominal", "UM", "Tol. − (UM)", "Tol. + (UM)", "Carga objetivo", "Carga mín.", "Carga máx.",
        "V recipiente (L)", "ρ agente (kg/L)", "ρ mín.", "ρ máx.", "V agente (L)", "V agente máx. (L)",
        "V agente mín. (L)", "Ocupa (%)", "Ocupa máx. (%)", "Ocupa con ρ aparente mín. (%)", "V libre (L)",
        "V libre mín. (L)", "V libre máx. (L)", "Ps (MPa)", "Ps mín. (MPa)", "Ps máx. (MPa)", "M gas (kg/mol)",
        "Gas (kg)", "Gas mín. (kg)", "Gas máx. (kg)", "Gas (L normales)", "Relación de llenado CO₂ (kg/L)",
        "Máx. IRAM 2533 (kg/L)", "CO₂ cumple", "Ps < máx. IRAM 3523", "Reposición en mantenimiento (UM)",
        "Prueba hidráulica cada (años)"]
M0 = 3                                   # primera fila de datos de MODELOS
FILA_M = {m.codigo: M0 + i for i, m in enumerate(MODELOS)}


def _mref(m, campo):
    return f"MODELOS!${MC[campo]}${FILA_M[m.codigo]}"


def _modelo_fila(m, i):
    """Valores y fórmulas de la fila del modelo en MODELOS."""
    r = M0 + i
    c = {k: f"{v}{r}" for k, v in MC.items()}
    ag = B._agente(m)
    _, q, um, _, gas, *_ = B.carga(m)
    co2 = ag == "CO2"
    kg = f'{c["um"]}="kg"'
    tol = f"{c['ref_tol']}"
    f = {
        "cod": m.codigo, "nom": m.nombre, "norma": m.spec["Norma IRAM extintor"], "ref_ag": ID_AGENTE[ag],
        "ref_gas": "" if co2 else ID_GAS[gas], "ref_tol": ref_tolerancia(m), "ref_ph": ref_ph(m), "nom_q": q, "um": um,
        "tol_m": f'=IF({_r("UNI", tol)}="kg",{_r("MIN", tol)},{_r("MIN", tol)}*{c["nom_q"]})',
        "tol_p": f'=IF({_r("UNI", tol)}="kg",{_r("MAX", tol)},{_r("MAX", tol)}*{c["nom_q"]})',
        "obj": f'=IF(AND({c["tol_m"]}=0,{c["tol_p"]}>0),{c["nom_q"]}+{c["tol_p"]}/2,{c["nom_q"]})',
        "qmin": f'={c["nom_q"]}+{c["tol_m"]}', "qmax": f'={c["nom_q"]}+{c["tol_p"]}',
        "V": float(m.geo["vol_dm3"]),
        "ps": float(m.spec["Presión de servicio (MPa)"].replace(",", ".")),
        "ph": f'={_r("VAL", c["ref_ph"])}',
    }
    if co2:
        f.update({
            "rho": f'={c["obj"]}/{c["V"]}', "Vag": f'={c["V"]}', "rll": f'={c["obj"]}/{c["V"]}',
            "rll_max": '=' + _r("MAX", '"RLL_CO2"'), "rll_ok": f'=IF({c["rll"]}<={c["rll_max"]},"Sí","No")',
            "repo": f'={c["obj"]}-{c["qmin"]}'})
        return f
    f.update({
        "rho": f'={_r("VAL", c["ref_ag"])}', "rho_min": f'={_r("MIN", c["ref_ag"])}',
        "rho_max": f'={_r("MAX", c["ref_ag"])}',
        "Vag": f'=IF({kg},{c["obj"]}/{c["rho"]},{c["obj"]})',
        "Vag_max": f'=IF({kg},{c["qmax"]}/{c["rho_min"]},{c["qmax"]})',
        "Vag_min": f'=IF({kg},{c["qmin"]}/{c["rho_max"]},{c["qmin"]})',
        "ocup": f'={c["Vag"]}/{c["V"]}', "ocup_max": f'={c["Vag_max"]}/{c["V"]}',
        "Vl": f'={c["V"]}-{c["Vag"]}', "Vl_min": f'=MAX(0,{c["V"]}-{c["Vag_max"]})',
        "Vl_max": f'={c["V"]}-{c["Vag_min"]}',
        "ps_min": f'={c["ps"]}*(1+{_r("MIN", chr(34) + "PS_TOL" + chr(34))})',
        "ps_max": f'={c["ps"]}*(1+{_r("MAX", chr(34) + "PS_TOL" + chr(34))})',
        "M": f'={_r("VAL", c["ref_gas"])}*VM',
        "gas": f'=({c["ps"]}+P_ATM)*1000*{c["Vl"]}*{c["M"]}/(R_GAS*T_REF)',
        "gas_min": f'=({c["ps_min"]}+P_ATM)*1000*{c["Vl_min"]}*{c["M"]}/(R_GAS*{_r("MAX", chr(34) + "T_REF" + chr(34))})',
        "gas_max": f'=({c["ps_max"]}+P_ATM)*1000*{c["Vl_max"]}*{c["M"]}/(R_GAS*{_r("MIN", chr(34) + "T_REF" + chr(34))})',
        "nl": f'={c["gas"]}/{_r("VAL", c["ref_gas"])}',
    })
    if ag == "ABC":
        f["ocup_ap"] = f'={c["qmax"]}/{_r("MIN", chr(34) + "AG_ABC_AP" + chr(34))}/{c["V"]}'
    if m.spec["Norma IRAM extintor"] == "3523":
        f["ps_ok"] = f'=IF({c["ps_max"]}<PS_MAX,"Sí","No")'
    if um == "kg":
        f["repo"] = f'={c["obj"]}-{c["qmin"]}'
    return f


# ------------------------------------------------------------------ estructura de cada producto
def _corto(s):
    """Nombre corto: sin normas, fuentes ni aclaraciones entre paréntesis (salvo cuántas piezas son o el tramo)."""
    s = str(s).split(" — ")[0].split(", ")[0].split(" - ")[0].split(" c/")[0]
    s = re.sub(r" \((?!\d+\)|tramo enrollado\)).*", "", s)
    for a, b in (("Polvo químico seco", "Polvo"), ("Tarjeta de identificación DPS con sello", "Tarjeta DPS")):
        s = s.replace(a, b)
    return s.strip()[:48]


def _es_insumo(r):
    return (r["nivel"] >= 3 or re.search(r"-(C\d+|S0)$", str(r["codigo"])) or r["sub"] == 7 or
            str(r["ori"]).startswith("Proceso") or not r["cant"])


def _anidar(filas):
    """Las piezas que vienen dentro de la válvula HZ comprada armada (y sus internos) bajan un nivel y quedan debajo
    de ella; su masa es la de la válvula."""
    kit = next((r for r in filas if re.search(r"-K2$", str(r["codigo"]))), None)
    if kit is None:
        return filas
    dentro = [r for r in filas if r is not kit and (str(r["ori"]).startswith("Incluido en válvula") or
                                                    re.search(r"-V\d$", str(r["codigo"])))]
    ids = {id(r) for r in dentro}
    out = []
    for r in filas:
        if id(r) in ids:
            continue
        out.append(r)
        if r is kit:
            out += [dict(h, nivel=h["nivel"] + 1) for h in dentro]
    return out


def _fila(niv, cod, pieza, tipo, cant=None, um="u", ref="", **kw):
    """Renglón del BOM: tipo pieza / agente / co2 / gas / compra / grupo. kw: vol, sup (pieza); qmin, qmax (agente)."""
    return dict(niv=niv, cod=cod, pieza=pieza, tipo=tipo, cant=cant, um=um, ref=ref, **kw)


def _pieza(r):
    sup = r["sup"] * (2 if r["fac"] < 1 else 1)          # pieza hueca modelada maciza: caras interior y exterior
    return _fila(r["nivel"], r["codigo"], _corto(r["desc"]), "pieza", r["cant"], r["um"], ID_RHO[r["rho"]],
                 vol=r["vol"], sup=sup)


def agente_fila(m, niv, cod, cant, qmin, qmax, sufijo=""):
    """Renglón(es) de agente con cantidad y banda dadas como fórmulas sobre MODELOS."""
    ag = B._agente(m)
    nombre, _, um, *_ = B.carga(m)
    if ag == "AFFF":
        p = _r("VAL", '"AFFF_PROP"')
        return [_fila(niv, cod + "b", "Concentrado AFFF 3 %" + sufijo, "agente", f"={cant}*{p}", "L", "AG_AFFF_C",
                      qmin=f"{qmin}*{p}", qmax=f"{qmax}*{p}"),
                _fila(niv, cod, "Agua (premezcla)" + sufijo, "agente", f"={cant}*(1-{p})", "L", "AG_AGUA",
                      qmin=f"{qmin}*(1-{p})", qmax=f"{qmax}*(1-{p})")]
    if ag == "ABC":
        nombre = f"Polvo {B.AG.agente(m)['grado']}"
    pz = "Dióxido de carbono" if ag == "CO2" else _corto(nombre)
    return [_fila(niv, cod, pz + sufijo, "co2" if ag == "CO2" else "agente", f"={cant}", um, ID_AGENTE[ag],
                  qmin=qmin, qmax=qmax, m=m)]


def gas_fila(m, niv, cod):
    _, _, _, _, g, m_gas, *_ = B.carga(m)
    if str(g).startswith("-") or not m_gas:
        return []
    return [_fila(niv, cod, f"Gas impulsor: {g} (L normales)", "gas", "=" + _mref(m, "gas"), "kg", ID_GAS[g],
                  qmin=_mref(m, "gas_min"), qmax=_mref(m, "gas_max"))]


def estructura(m, cilindro=False):
    """Renglones de la estructura del producto; sin insumos."""
    out = []
    for r in _anidar([r for r in B.bom_producto(m, cilindro=cilindro) if not _es_insumo(r)]):
        cod = r["codigo"]
        if re.search(r"-A1b?$", cod):                        # agente (la premezcla AFFF sale de una sola fila)
            if cod.endswith("b"):
                out += agente_fila(m, 2, cod[:-1], _mref(m, "obj"), _mref(m, "qmin"), _mref(m, "qmax"))
            elif B._agente(m) != "AFFF":
                out += agente_fila(m, 2, cod, _mref(m, "obj"), _mref(m, "qmin"), _mref(m, "qmax"))
        elif cod.endswith("-A2"):
            out += gas_fila(m, 2, cod)
        elif r["nivel"] >= 2 and r.get("rho") and r.get("vol"):
            out.append(_pieza(r))
        else:
            niv = r["nivel"]
            pieza = _corto(r["desc"]) if niv else r["desc"].split(" - ")[0]
            out.append(_fila(niv, cod, pieza, "grupo" if niv < 2 else "compra", r["cant"], r["um"]))
    for a, b in zip(out, out[1:]):          # lo que tiene hijos (la válvula HZ armada) suma sus piezas
        if b["niv"] > a["niv"]:
            a["tipo"] = "grupo"
    return out


def sustituto(m):
    filas = [r for r in SU.bom_sustituto(m) if r["nivel"] == 2]
    if not filas:
        return []
    return ([_fila(1, m.codigo.replace("FL_MAT_", "FL_SUS_"), "Si va como sustituto, se agrega", "grupo", 1)] +
            [_fila(2, r["codigo"], _corto(r["desc"]), "compra", r["cant"], r["um"].split("/")[0]) for r in filas])


# ------------------------------------------------------------------ recargas por servicio (IRAM 3517-2:2020)
def servicios(m):
    """Bloques [(título, filas)] de los cuatro servicios del modelo."""
    ag = B._agente(m)
    _, _, um, *_ = B.carga(m)
    base = m.codigo.replace("FL_MAT_", "RK_")
    co2, liquido = ag == "CO2", um == "L"
    obj, qmin, qmax, repo = (_mref(m, k) for k in ("obj", "qmin", "qmax", "repo"))

    def u(cod, txt):
        return _fila(2, f"{base}-{cod}", txt, "compra", 1)

    def ident(junta=True, marbete=True):
        f = [u("P1", "Precinto con identificación del recargador"),           # 9.4.13
             u("P2", "Etiqueta de servicio del recargador"),                  # 9.4.14
             u("P3", "Estampilla y oblea de recarga (PBA)"),                  # Res. 522/07
             u("P4", "Tarjeta de identificación DPS (PBA)"),                  # Res. 349/07 art. 21
             u("P5", "Tarjeta de identificación AGC (CABA)")]                 # Ord. 40.473 art. 6
        if marbete:
            f.insert(1, u("P6", "Marbete indicador"))                         # 9.6, anexo E
        if junta:
            f.append(u("P7", "Junta tórica de asiento del cuello"))
        return f

    gas = gas_fila(m, 2, f"{base}-A2")
    entera = agente_fila(m, 2, f"{base}-A1", obj, qmin, qmax)
    bloques = [("Control periódico (trimestral)", [u("C1", "Etiqueta de control (celeste 35 × 50)")])]
    if liquido:
        mant = entera + gas + ident()
    else:                                    # reposición: de 0 a (objetivo − límite inferior de la tabla 3)
        rep = agente_fila(m, 2, f"{base}-A1", repo, "0", repo, " (reposición)")
        mant = rep + (ident(junta=False, marbete=False) if co2 else gas + ident())
    bloques.append(("Mantenimiento (anual)", mant))
    rec = entera + gas + ident(junta=not co2, marbete=not co2)
    if co2:
        rec.append(u("S1", "Conjunto de seguridad (disco)"))
    bloques.append(("Recarga (después de cada uso)", rec))
    if co2:
        ph = (agente_fila(m, 2, f"{base}-RA1", obj, qmin, qmax, " recuperado") +
              [u("S1", "Conjunto de seguridad (disco)"), u("P6", "Marbete indicador"),
               u("P7", "Junta tórica de asiento del cuello")])
    elif liquido:
        ph = [u("H1", "Oblea de vencimiento de la prueba hidráulica")]
    else:
        ph = (agente_fila(m, 2, f"{base}-RA1", f"({obj}-{repo})", f"({obj}-{repo})", obj, " recuperado") +
              [u("H1", "Oblea de vencimiento de la prueba hidráulica")])
    ph_tit = f'="Prueba hidráulica (cada "&{_mref(m, "ph")}&" años, se suma al mantenimiento)"'
    bloques.append((ph_tit, ph))
    return bloques


def recargas_modelo(m):
    out = [_fila(0, m.codigo.replace("FL_MAT_", "RK_"), m.nombre, "titulo", 1)]
    for i, (tit, filas) in enumerate(servicios(m), 1):
        out.append(_fila(1, f"{out[0]['cod']}-{i}", tit, "grupo", 1, "servicio"))
        out += filas
    return out


# ------------------------------------------------------------------ Excel
# Vista normal: volumen total y masa total. Con el «+» de arriba de cada una se abre el detalle (unitario, mínimo y
# máximo); dentro de la masa, un segundo «+» abre el cálculo de la tolerancia.
CAB = ["Nivel", "Código", "Pieza", "Ref.", "Material / agente", "Cant.", "UM", "Densidad (kg/L)",
       "Volumen total (L)", "Vol. unit. (L)", "Vol. mín. (L)", "Vol. máx. (L)", "Masa total (kg)", "Masa unit. (kg)",
       "Masa mín. (kg)", "Masa máx. (kg)", "ρ mín. (kg/L)", "ρ máx. (kg/L)", "Superficie (dm²)", "Espesor eq. (mm)",
       "Tol. ISO 2768-m (± mm)", "Tol. volumen (± %)"]
ANCHO = [6, 19, 40, 11, 34, 9, 6, 9, 10, 10, 10, 10, 10, 10, 10, 10, 9, 9, 10, 9, 10, 10]
COL = {k: get_column_letter(i + 1) for i, k in enumerate(
    ["niv", "cod", "pieza", "ref", "mat", "cant", "um", "rho", "vol", "vu", "vmin", "vmax", "mt", "mu", "mmin", "mmax",
     "rmin", "rmax", "sup", "e", "tiso", "tvol"])}
GRUPOS = [("vu", "vmax", 1), ("mu", "tvol", 1), ("rmin", "tvol", 2)]     # columnas que se abren con «+»
NUM = "[<0.001]0.0000;0.000"
FMT = {"cant": "0.####", "rho": "0.#####", "vol": NUM, "vmin": NUM, "vmax": NUM, "mu": NUM, "mt": NUM, "mmin": NUM,
       "mmax": NUM, "rmin": "0.#####", "rmax": "0.#####", "vu": NUM, "sup": "0.000", "e": "0.00", "tiso": "0.0",
       "tvol": "0.0%"}


def _formulas(f, r, fin):
    """Celdas del renglón f escrito en la fila r; fin = última fila de su bloque (para los que agrupan)."""
    c = {k: f"{v}{r}" for k, v in COL.items()}
    out = {"niv": f["niv"], "cod": f["cod"], "pieza": f["pieza"], "ref": f["ref"] or None, "um": f["um"],
           "cant": f["cant"]}
    if f["ref"]:
        out["mat"] = f'={_r("DATO", c["ref"])}'
    t = f["tipo"]
    if t == "grupo" and fin > r:
        for k in ("mt", "mmin", "mmax"):
            rng = f"{COL[k]}{r + 1}:{COL[k]}{fin}"
            suma = f'SUMIF({COL["niv"]}{r + 1}:{COL["niv"]}{fin},{f["niv"] + 1},{rng})'
            out[k] = f'=IF({suma}=0,"",{suma})'
        if f["niv"] >= 2:
            out["mu"] = f'=IF({c["mt"]}="","",{c["mt"]}/{c["cant"]})'
    elif t == "pieza":
        out.update(rho=f'={_r("VAL", c["ref"])}', rmin=f'={_r("MIN", c["ref"])}', rmax=f'={_r("MAX", c["ref"])}',
                   vu=f["vol"], sup=f["sup"], e=f'=200*{c["vu"]}/{c["sup"]}',
                   tiso=f'=IFERROR(INDEX(ISO_TOL,MATCH({c["e"]},ISO_DESDE,1)),0)',
                   tvol=f'=IF({c["e"]}>0,{c["tiso"]}/{c["e"]},0)',
                   vol=f'={c["cant"]}*{c["vu"]}', vmin=f'={c["vol"]}*(1-{c["tvol"]})',
                   vmax=f'={c["vol"]}*(1+{c["tvol"]})', mu=f'={c["vu"]}*{c["rho"]}', mt=f'={c["cant"]}*{c["mu"]}',
                   mmin=f'={c["vmin"]}*{c["rmin"]}', mmax=f'={c["vmax"]}*{c["rmax"]}')
    elif t in ("agente", "co2", "gas"):
        qmin, qmax = f["qmin"], f["qmax"]
        if t == "co2":
            rho = "=" + _mref(f["m"], "rll")
            rmin = rmax = c["rho"]
        else:
            rho, rmin, rmax = (f'={_r(k, c["ref"])}' for k in ("VAL", "MIN", "MAX"))
            if t == "gas":
                rmin = rmax = c["rho"]
        out.update(rho=rho)
        if t == "agente" and f["um"] == "L":      # líquidos: la cantidad es el volumen
            out.update(rmin=rmin, rmax=rmax, vu=1, vol=f'={c["cant"]}', vmin=f"={qmin}", vmax=f"={qmax}",
                       mu=f'={c["rho"]}', mt=f'={c["cant"]}*{c["mu"]}', mmin=f'={qmin}*{c["rmin"]}',
                       mmax=f'={qmax}*{c["rmax"]}')
        else:                                     # en kg: el volumen es masa / densidad
            if t == "agente":
                out.update(rmin=rmin, rmax=rmax)
                lo, hi = c["rmax"], c["rmin"]
            else:
                lo = hi = c["rho"]
            out.update(vu=f'=1/{c["rho"]}', vol=f'={c["cant"]}*{c["vu"]}', vmin=f"={qmin}/{lo}",
                       vmax=f"={qmax}/{hi}", mu=1, mt=f'={c["cant"]}', mmin=f"={qmin}", mmax=f"={qmax}")
    return out


def _hoja(wb, titulo, bloques):
    ws = wb.create_sheet(titulo)
    ws.append(CAB)
    for i, (w, h) in enumerate(zip(ANCHO, CAB), 1):
        ws.column_dimensions[get_column_letter(i)].width = w
        cel = ws.cell(1, i)
        cel.font = Font(name="Arial", size=10, bold=True, color=BLANCO)
        cel.fill = PatternFill("solid", fgColor=NEGRO if CAB[i - 1] in ("Volumen total (L)", "Masa total (kg)") or
                               i <= 8 else GRIS_O)
        cel.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.row_dimensions[1].height = 42
    fino = Side(style="thin", color="BFBFBF")
    claves = list(COL)
    for filas in bloques:
        r0 = ws.max_row + 1
        for j, f in enumerate(filas):
            fin = j
            while fin + 1 < len(filas) and filas[fin + 1]["niv"] > f["niv"]:
                fin += 1
            vals = _formulas(f, r0 + j, r0 + fin)
            r = r0 + j
            niv = f["niv"]
            ws.row_dimensions[r].outline_level = min(niv, 7)
            for i, k in enumerate(claves, 1):
                cel = ws.cell(r, i, vals.get(k))
                cel.border = Border(bottom=fino)
                if k in FMT:
                    cel.number_format = FMT[k]
                cel.font = Font(name="Arial", size=10, bold=niv < 2, color=BLANCO if niv == 0 else NEGRO)
                if niv == 0:
                    cel.fill = PatternFill("solid", fgColor=GRIS_O)
                elif niv == 1:
                    cel.fill = PatternFill("solid", fgColor=GRIS_C)
            ws.cell(r, 1).alignment = ws.cell(r, 7).alignment = Alignment(horizontal="center")
            ws.cell(r, 3).alignment = Alignment(indent=2 * niv)
        ws.append([])
    ws.sheet_properties.outlinePr.summaryBelow = False
    ws.sheet_properties.outlinePr.summaryRight = False
    for a, z, nivel in GRUPOS:
        for col in range(ws[COL[a] + "1"].column, ws[COL[z] + "1"].column + 1):
            d = ws.column_dimensions[get_column_letter(col)]
            d.outline_level = max(d.outline_level or 0, nivel)
            d.hidden = True
    ws.freeze_panes = "D2"
    ws.auto_filter.ref = f"A1:V{ws.max_row}"
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth, ws.page_setup.fitToHeight = 1, 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.print_title_rows = "1:1"
    return ws


def _referencias(wb):
    ws = wb.create_sheet("REFERENCIAS", 0)
    ws.append(["Datos de entrada de todas las cuentas del BOM. Cada fila tiene un ID; las fórmulas de las demás "
               "hojas lo buscan acá (columna Ref.). Las normas se citan por cláusula."])
    ws.append(["ID", "Dato", "Valor", "Mín.", "Máx.", "Unidad", "Fuente (norma o ficha, cláusula)", "Nota"])
    nombres = {"AFFF": "AFFF_PROP", "CONC": "AG_AFFF_C", "AGUA": "AG_AGUA", "M_N2": "M_N2", "M_AIRE": "M_AIRE",
               "M_AR": "M_AR", "VM": "VM"}
    pos = {}
    for fila in REFERENCIAS:
        if not fila[0]:
            ws.append(["", fila[1]])
            r = ws.max_row
            for i in range(1, 9):
                ws.cell(r, i).fill = PatternFill("solid", fgColor=GRIS_C)
                ws.cell(r, i).font = Font(name="Arial", size=10, bold=True)
            continue
        ws.append(list(fila))
        pos[fila[0]] = ws.max_row
    for row in ws.iter_rows(min_row=3, max_row=ws.max_row):
        for cel in row[2:5]:
            if isinstance(cel.value, str) and cel.value.startswith("="):
                v = cel.value
                for k in sorted(nombres, key=len, reverse=True):
                    v = re.sub(rf"\b{k}\b", f"$C${pos[nombres[k]]}", v)
                cel.value = v
    fin = ws.max_row
    ws.append([])
    ws.append(["", "Tolerancia general de los planos: ISO 2768-1 clase m (rótulo de cada plano FL_MAT, FL_REC y FL_DES)"])
    r_t = ws.max_row
    ws.append(["", "Más de (mm)", "Hasta (mm)", "± (mm)", "", "", "ISO 2768-1 tabla 1, clase m (media)",
               "Para menos de 0,5 mm la norma no da tolerancia general"])
    i0 = ws.max_row + 1
    for a, b, t in ISO_2768_M:
        ws.append(["", a, b, t])
    i1 = ws.max_row
    for r in (r_t, r_t + 1):
        for i in range(1, 9):
            ws.cell(r, i).font = Font(name="Arial", size=10, bold=True)
            ws.cell(r, i).fill = PatternFill("solid", fgColor=GRIS_C)
    for col, nom in (("A", "ID"), ("B", "DATO"), ("C", "VAL"), ("D", "MIN"), ("E", "MAX"), ("F", "UNI")):
        wb.defined_names[f"REF_{nom}"] = DefinedName(f"REF_{nom}", attr_text=f"REFERENCIAS!${col}$3:${col}${fin}")
    wb.defined_names["ISO_DESDE"] = DefinedName("ISO_DESDE", attr_text=f"REFERENCIAS!$B${i0}:$B${i1}")
    wb.defined_names["ISO_TOL"] = DefinedName("ISO_TOL", attr_text=f"REFERENCIAS!$D${i0}:$D${i1}")
    for k in ("P_ATM", "R_GAS", "T_REF", "VM", "PS_MAX"):
        wb.defined_names[k] = DefinedName(k, attr_text=f"REFERENCIAS!$C${pos[k]}")
    for i, w in enumerate([12, 52, 10, 10, 10, 10, 52, 44], 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    for row in ws.iter_rows(min_row=1, max_row=ws.max_row):
        for cel in row:
            if not cel.font.bold:
                cel.font = Font(name="Arial", size=10)
            cel.alignment = Alignment(wrap_text=cel.column in (2, 7, 8), vertical="top")
    ws["A1"].font = Font(name="Arial", size=11, bold=True)
    ws["A1"].alignment = Alignment(wrap_text=False)
    for i in range(1, 9):
        c = ws.cell(2, i)
        c.font = Font(name="Arial", size=10, bold=True, color=BLANCO)
        c.fill = PatternFill("solid", fgColor=NEGRO)
    ws.freeze_panes = "B3"
    _imprimir(ws, "2:2")
    return ws


def _imprimir(ws, titulos):
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth, ws.page_setup.fitToHeight = 1, 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.print_title_rows = titulos


def _modelos(wb):
    ws = wb.create_sheet("MODELOS", 1)
    ws.append(["Carga y gas impulsor de cada extintor. Fórmulas sobre REFERENCIAS; la carga objetivo va al centro de "
               "la banda cuando la tolerancia es sólo positiva. Gas: (Ps + Patm) · V libre · M / (R · T)."])
    ws.append(MCAB)
    for i, m in enumerate(MODELOS):
        f = _modelo_fila(m, i)
        for j, k in enumerate(MC, 1):
            ws.cell(M0 + i, j, f.get(k))
    fmt = {"ocup": "0%", "ocup_max": "0%", "ocup_ap": "0%", "rho": "0.0000", "rll": "0.000", "M": "0.000",
           "gas": "0.0000", "gas_min": "0.0000", "gas_max": "0.0000", "nl": "0.0"}
    for i, k in enumerate(MC, 1):
        col = get_column_letter(i)
        ws.column_dimensions[col].width = 26 if k == "nom" else (20 if k == "cod" else 11)
        for r in range(1, ws.max_row + 1):
            cel = ws.cell(r, i)
            cel.font = Font(name="Arial", size=10, bold=r <= 2, color=BLANCO if r == 2 else NEGRO)
            if r == 2:
                cel.fill = PatternFill("solid", fgColor=NEGRO)
                cel.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            elif r > 2:
                cel.number_format = fmt.get(k, "0.###")
    ws.row_dimensions[2].height = 56
    ws.freeze_panes = "C3"
    _imprimir(ws, "2:2")
    return ws


def excel(ruta):
    wb = Workbook()
    wb.remove(wb.active)
    _referencias(wb)
    _modelos(wb)
    fab = [m for m in MODELOS if m.codigo in B.PROPIOS]
    rev = [m for m in MODELOS if m.codigo not in B.PROPIOS]
    _hoja(wb, "Fabricados", [estructura(m) + sustituto(m) for m in fab])
    _hoja(wb, "Revendidos", [estructura(m) + sustituto(m) for m in rev])
    _hoja(wb, "Cilindros", [estructura(m, cilindro=True) for m in RC.modelos_abc()])
    _hoja(wb, "Recargas", [recargas_modelo(m) for m in fab + rev])
    wb.calculation.fullCalcOnLoad = True
    wb.save(ruta)
    recalcular(ruta)
    return [(ws.title, ws.max_row) for ws in wb.worksheets]


def recalcular(ruta):
    """Guarda en el libro los valores de las fórmulas (LibreOffice), para que se vean aun en un visor que no calcula.
    LibreOffice pasa los botones +/− abajo y a la derecha del grupo; se vuelven arriba y a la izquierda. Sin
    LibreOffice el libro queda sólo con las fórmulas (Excel y Google Sheets las calculan al abrirlo)."""
    if not shutil.which("soffice"):
        return False
    with tempfile.TemporaryDirectory() as d:
        try:
            subprocess.run(["soffice", "--headless", "--convert-to", "xlsx:Calc MS Excel 2007 XML", "--outdir", d, ruta],
                           check=True, capture_output=True, timeout=900)
        except (subprocess.SubprocessError, OSError):
            return False
        tmp = os.path.join(d, os.path.basename(ruta))
        with zipfile.ZipFile(tmp) as zin, zipfile.ZipFile(ruta, "w", zipfile.ZIP_DEFLATED) as zout:
            for it in zin.infolist():
                data = zin.read(it.filename)
                if it.filename.startswith("xl/worksheets/sheet"):
                    x = data.decode("utf-8")
                    op = '<outlinePr summaryBelow="0" summaryRight="0"/>'
                    if "<outlinePr" in x:
                        x = re.sub(r"<outlinePr[^>]*/>", op, x)
                    elif re.search(r"<sheetPr[^>]*/>", x):
                        x = re.sub(r"<sheetPr([^>]*)/>", rf"<sheetPr\1>{op}</sheetPr>", x, count=1)
                    else:
                        x = re.sub(r"(<sheetPr[^>]*>(?:<tabColor[^>]*/>)?)", rf"\1{op}", x, count=1)
                    data = x.encode("utf-8")
                zout.writestr(it, data)
    return True
