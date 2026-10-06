"""Agente extintor de cada modelo: grado (concentración), potencial extintor, gas impulsor y fuentes.

Una sola fuente para los planos (hoja 3), el BOM y el despiece. Criterio de fuentes, de mayor a menor peso:
  1) norma IRAM;  2) licencia IRAM / BVQI del extintor y hoja técnica del fabricante argentino del agente;
  3) ficha del fabricante argentino del extintor;  4) catálogo de referencia.

Hallazgo clave (licencias IRAM 3523 de Drago y de Georgia/Fadesa): el MISMO recipiente con la MISMA carga en kg
se certifica con distinto potencial según el grado del polvo. Ejemplo: 5 kg con DEM-60 = 6A-40B, con DEM-90 =
10A-40B. La masa la fija la norma (capacidad = masa de polvo, IRAM 3523 2.2); el % de fosfato monoamónico fija el
potencial A. Por eso el grado es una DECISIÓN DE PRODUCTO, no un dato de cálculo.
"""

# Grados de polvo ABC (Industrias Químicas DEM S.A., Sello IRAM 3569 y BVQI): % de fosfato monoamónico (MAP)
# DECLARADO por el fabricante del polvo. IRAM 3569 (tabla de requisitos) NO fija el % de MAP: exige que cada
# componente esté dentro de ± 5 % relativo del valor declarado si supera el 50 % del polvo, o ± 10 % si no lo
# supera, y que lo declarado sea el polvo con que se calificó el potencial. Banda = esa tolerancia aplicada al MAP.
# El resto es sulfato de amonio (relleno) + mica/sílice + silicona hidrófuga (≈ 2-3 %), según HDS DEMSA ABC.
# Proveedor cotizado (lista de precios 2026): Sancibrao ABC 55 / 75 / 90 (no ofrece ABC 60).
GRADOS_ABC = {
    "ABC 40": dict(map=40.0, banda=(36.0, 44.0), color="amarillo", hoja="DEMSA ABC 40 (Rev 02, 2019)"),
    "ABC 55": dict(map=55.0, banda=(52.25, 57.75), color="verde", hoja="DEMSA ABC 55 (Rev 02, 2019)"),
    "ABC 60": dict(map=60.0, banda=(57.0, 63.0), color="verde", hoja="DEMSA catálogo (ABC 60)"),
    "ABC 75": dict(map=75.0, banda=(71.25, 78.75), color="amarillo", hoja="DEMSA catálogo (ABC 75)"),
    "ABC 90": dict(map=90.0, banda=(85.5, 94.5), color="amarillo", hoja="DEMSA ABC 90 (Rev 02, 2019)"),
}
RELLENO_ABC = "sulfato de amonio"
ADITIVOS_ABC = 3.0   # % mica + sílice + silicona (HDS DEMSA ABC: metilhidrógeno-siloxano y minerales)

# Potencial extintor certificado según grado y capacidad (licencias IRAM 3523: Drago anexo I 2008 con DEM-60 /
# DEM-90; Georgia/Fadesa fichas técnicas y catálogo). "-" = no publicado / consultar.
POTENCIAL_ABC = {
    ("ABC 60", "1 kg"): "1A-5B:C",   ("ABC 90", "1 kg"): "-",
    ("ABC 60", "2,5 kg"): "3A-20B:C", ("ABC 90", "2,5 kg"): "3A-20B:C",
    ("ABC 60", "5 kg"): "6A-40B:C",  ("ABC 90", "5 kg"): "10A-40B:C",
    ("ABC 60", "10 kg"): "6A-60B:C", ("ABC 90", "10 kg"): "10A-60B:C",
}

# Agente por modelo. grado = decisión FLAMA por defecto (a confirmar): ABC 60 en manuales (mínimo costo con
# potencial certificado), ABC 90 en rodantes (único grado que ofrecen los fabricantes locales en rodantes).
AGENTE = {
    "FL_MAT_ABC_1kg": dict(grado="ABC 60", norma="IRAM 3569", gas="N₂ seco"),
    "FL_MAT_ABC_2.5kg": dict(grado="ABC 60", norma="IRAM 3569", gas="N₂ seco"),
    "FL_MAT_ABC_5kg": dict(grado="ABC 60", norma="IRAM 3569", gas="N₂ seco", alternativa="ABC 90"),
    "FL_MAT_ABC_10kg": dict(grado="ABC 60", norma="IRAM 3569", gas="N₂ seco", alternativa="ABC 90"),
    "FL_MAT_ABC_25kg": dict(grado="ABC 90", norma="IRAM 3569", gas="N₂ seco", potencial="-"),
    "FL_MAT_ABC_50kg": dict(grado="ABC 90", norma="IRAM 3569", gas="N₂ seco", potencial="-"),
    "FL_MAT_ABC_70kg": dict(grado="ABC 90", norma="IRAM 3569", gas="N₂ seco", potencial="-"),
    "FL_MAT_ABC_100kg": dict(grado="ABC 90", norma="IRAM 3569", gas="N₂ seco", potencial="-"),
    "FL_MAT_BC_5kg": dict(grado="BC sódico (NaHCO₃ ≥ 85,5 %)", norma="IRAM 3566", gas="N₂ seco",
                          potencial="-", alternativa="BC Púrpura K (KHCO₃ 92 ± 5 %): 40B"),
    "FL_MAT_CLASED_9l": dict(grado="Clase D (NaCl > 90 %)", norma="sin norma IRAM de agente (DEMSA ISO 9001)",
                             gas="N₂ seco", potencial="-"),
    "FL_MAT_AGUA_10l": dict(grado="Agua potable", norma="-", gas="Aire comprimido", potencial="1A"),
    "FL_MAT_AFFF_10l": dict(grado="Premezcla AFFF 3 % (DEMSA 203 MN, IRAM 3515)", norma="IRAM 3515",
                            gas="Aire comprimido", potencial="3A-10B"),
    "FL_MAT_AFFF_50l": dict(grado="Premezcla AFFF 3 % (DEMSA 203 MN, IRAM 3515)", norma="IRAM 3515",
                            gas="Aire comprimido", potencial="-"),
    "FL_MAT_SALESK_6l": dict(grado="Acetato de potasio (DEMSA Kitchen, 1,300 g/ml, pH 8,5)", norma="IRAM 3697",
                             gas="N₂ seco", potencial="1A-K"),
    "FL_MAT_CO2_2kg": dict(grado="CO₂ ≥ 99,5 %", norma="IRAM 41170", gas="autopresurizado", potencial="-"),
    "FL_MAT_CO2_5kg": dict(grado="CO₂ ≥ 99,5 %", norma="IRAM 41170", gas="autopresurizado", potencial="-"),
    "FL_MAT_HCFC-HFC_5kg": dict(grado="HCFC-123 (Mezcla B) > 93 %", norma="IRAM 3526-1", gas="Argón",
                                potencial="-"),
}


def agente(m):
    """Dict del agente del modelo con potencial resuelto."""
    a = dict(AGENTE[m.codigo])
    if "potencial" not in a:
        a["potencial"] = POTENCIAL_ABC.get((a["grado"], m.capacidad.split(" Ø")[0].replace(".", ",")), "-")
    if a.get("alternativa", "").startswith("ABC"):
        alt = POTENCIAL_ABC.get((a["alternativa"], m.capacidad.replace(".", ",")), "-")
        a["alternativa"] = f"{a['alternativa']}: {alt}"
    return a


def composicion_abc(grado, kg):
    """kg de MAP, de relleno (sulfato de amonio) y de aditivos en `kg` de polvo del grado."""
    g = GRADOS_ABC[grado]
    k_map = kg * g["map"] / 100
    k_ad = kg * ADITIVOS_ABC / 100
    return k_map, kg - k_map - k_ad, k_ad
