"""BOM (lista de materiales multinivel) de cada matafuego y de cada cilindro, en Excel.

Sale del MISMO modelo 3D que los planos FL_MAT_* y FL_REC_*: posición, código de pieza, denominación y
material son los de la lista de piezas IRAM 4508 de cada plano (planos.lista), y la medida y el peso de
cada pieza se miden sobre el sólido (caja envolvente, volumen × densidad). A eso se suma lo que el plano
de conjunto no dibuja pero el producto lleva: consumibles de soldadura y pintura, agente extintor y gas
impulsor, juntas y resorte de la válvula, identificación, precinto, soporte y embalaje.

Niveles: 0 producto (plano) · 1 subconjunto · 2 pieza o insumo · 3 materia prima de la pieza fabricada.
Fuente de cada valor: P plano / modelo 3D · C cálculo declarado · N norma · L layout + cotización de chapa ·
Q cotización o ficha del proveedor · I investigación FLAMA · V sin documento.
Estado de cada fila (color): sin color = validado · amarillo = estimado con justificación (norma / fuente técnica) ·
naranja = a validar (falta dato, cotización o confirmación) · rojo = no cumple o decisión pendiente.
El BOM es completo; la columna «Entra MRP» marca lo que se compra (lo fabricado se explota en su materia prima y lo
que viene dentro de un conjunto comprado no se pide aparte). En los revendidos sólo entra el equipo terminado.

Uso: python generar.py --bom   ->   salida/bom/FLAMA_BOM.xlsx
"""

import math

from . import modelo3d as M
from . import materiales as MAT
from . import planos as P
from .catalogo import MODELOS
from . import accesorios as AC
from . import agentes as AG
from . import proveedores as PV

# ------------------------------------------------------------------ datos de planta (planos_industrial_flama)
# recorte del cuerpo en hoja estándar (FL_PI_04 hoja 2): formato, chapa, espesor, franja (alto), pieza (desarrollo),
# aprovechamiento de la hoja (%)
HOJA_CUERPO = {
    "2,5 kg": ("LAF 1220 × 2440", 1.25, 385.5, 269.5, 94.2),
    "5 kg": ("LAF 1000 × 2000", 1.6, 330.0, 474.5, 94.0),
    "10 kg": ("LAF 1500 × 3000", 2.0, 495.0, 563.0, 92.9),
    "25 kg": ("LAC 1500 × 3000", 3.2, 490.0, 858.0, 84.1),
    "50 kg": ("LAC 1500 × 3000", 3.2, 640.0, 994.0, 84.8),
    "70 kg": ("LAC 1500 × 3000", 4.75, 680.0, 1212.0, 73.3),
    "100 kg": ("LAC 1500 × 3000", 4.75, 900.0, 1212.0, 72.7),
}
# discos de cúpula y fondo en fleje a medida (CC Nesting): Ø disco, espesor, ancho de fleje; paso = Ø + 3
DISCO = {
    ("cupula", "1 kg"): (108, 0.9, 114), ("fondo", "1 kg"): (100, 1.25, 106),
    ("cupula", "2,5 kg"): (179, 1.25, 200), ("fondo", "2,5 kg"): (148, 1.25, 200),
    ("cupula", "5 kg"): (221, 1.6, 250), ("fondo", "5 kg"): (177, 1.6, 200),
    ("cupula", "10 kg"): (258, 1.6, 300), ("fondo", "10 kg"): (205, 2.0, 249),
}
CANO_1KG = dict(barra=6000, pieza=255, piezas=23, diam=76.2, esp=1.25)

# familias que la planta fabrica (líneas S1, S2, S3) y las que revende (S4 tercerizados con sello IRAM)
# Fabricación propia: SÓLO los ABC (decisión FLAMA). Todo el resto (BC, Clase D, agua, AFFF, Sales K, CO₂,
# HCFC) se compra terminado al fabricante certificado y se revende.
PROPIOS = {"FL_MAT_ABC_1kg", "FL_MAT_ABC_2.5kg", "FL_MAT_ABC_5kg", "FL_MAT_ABC_10kg", "FL_MAT_ABC_25kg",
           "FL_MAT_ABC_50kg", "FL_MAT_ABC_70kg", "FL_MAT_ABC_100kg"}
# Válvula HZ comprada armada (lista de precios Q-AGENTES): piezas del plano que vienen dentro del kit
KIT_VALVULA = {"tuerca", "espiga", "cuerpo_valvula", "vastago", "cano_pesca", "manija_superior", "manija_inferior", "eje",
               "pasador"}
# Carro de rodantes: se fabrica en planta (no hay proveedor nacional del carro armado); las ruedas se compran
CARRO_FAB = {"eje_ruedas", "bastidor", "sunchos_bastidor", "apoyo"}

# subconjuntos: clave de pieza del modelo -> subconjunto
SUB = {
    "cuerpo": 1, "cupula": 1, "fondo": 1, "cuello": 1, "pie": 1, "varilla": 1,
    "tuerca": 2, "espiga": 2, "cuerpo_valvula": 2, "vastago": 2, "eje": 2, "manija_superior": 2,
    "manija_inferior": 2, "pasador": 2, "manometro": 2, "disco_seguridad": 2, "cano_pesca": 2,
    "racor": 3, "manguera": 3, "tobera": 3, "lanza": 3, "empunadura": 3, "brazo_difusor": 3, "difusor": 3,
    "suncho": 3, "valvula_esferica": 3, "tobera_campana": 3, "manguera_enrollada": 3, "soportes_manguera": 3,
    "rueda_der": 4, "llanta_der": 4, "eje_ruedas": 4, "bastidor": 4, "sunchos_bastidor": 4, "apoyo": 4,
    "junta_cuello": 2, "etiqueta": 6, "oblea_pba": 6, "sello_iram": 6, "precinto": 6,
    "faja_garantia": 6, "tarjeta_caba": 6, "etiqueta_serie": 6,
}
NOMBRE_SUB = {1: "Recipiente (cilindro)", 2: "Conjunto de válvula", 3: "Dispositivo de descarga",
              4: "Carro (bastidor y ruedas)", 5: "Carga: agente extintor y gas impulsor",
              6: "Identificación y precinto", 7: "Embalaje", 8: "Soporte (accesorio de montaje)"}

# densidad aparente de los agentes (kg/dm³) y masa molar del gas impulsor (kg/mol): R = referencia
# Química de los agentes. Densidad aparente (polvos) o densidad (líquidos) en kg/dm³: mín / típica / máx. La
# típica entra al BOM; la mínima es el peor caso de volumen (el polvo más liviano ocupa más lugar).
# (clave, nombre, composición, mecanismo, saponifica, gas impulsor, ρmín, ρtip, ρmáx, fuente)
AGENTES = {
    "ABC": ("Polvo ABC (fosfato monoamónico) con Sello IRAM 3569 - DEMSA",
            "MAP 40-90 % según grado (nominal ± 5 %) + sulfato de amonio 5-55 % + mica, sílice y silicona",
            "Captura de radicales; en clase A el MAP funde (≈177-190 °C) y cubre las brasas con una capa vítrea: "
            "el potencial A depende del grado (licencias IRAM 3523: 5 kg DEM-60 = 6A, DEM-90 = 10A)",
            "No. Ácido (pH 6-7,5 al 1 % según DEMSA; 4-5 otras fichas): no saponifica, no apto clase K; con BC "
            "reacciona (CO₂ + apelmazamiento)",
            "N₂", 0.85, 0.90, 0.98,
            "DEMSA HDS ABC: densidad aparente > 0,85 (piso garantizado) · típica 0,90 (ficha IZ; Corponor 0,85-0,98) "
            "· IRAM 3569 no fija densidad: exigirla en la orden de compra"),
    "BC": ("Polvo BC sódico con Sello IRAM 3566 - DEMSA", "NaHCO₃ ≥ 85,5 % (85,5-94,5) + estearatos, sílice, "
           "silicona (Púrpura K: KHCO₃ 92 ± 5 %)", "Captura de radicales y descomposición endotérmica (CO₂ + H₂O)",
           "Leve: alcalino (pH 8-9), saponifica superficialmente aceites; no reemplaza clase K",
           "N₂", 0.85, 0.90, 1.00, "DEMSA HDS Púrpura K: > 0,85 · Buckeye estándar 0,90 · Purple K aireado 0,88"),
    "D": ("Polvo clase D (cloruro de sodio) - DEMSA", "NaCl > 90 % + aditivos siliconados",
          "Forma costra sobre el metal fundido y lo aísla del aire", "No (pH 6-7,5)", "N₂",
          0.85, 1.00, 1.20, "DEMSA HDS polvo D: > 0,85 · típica R (pedir valor garantizado)"),
    "HCFC": ("HCFC Mezcla B (HCFC-123 base)", "HCFC-123 > 93 % + mezcla de gases < 7 %",
             "Enfriamiento y captura de radicales; no deja residuo", "No", "Argón", 1.47, 1.48, 1.48,
             "Halotron I HDS: 1,48 kg/L a 25 °C; 655 kPa a 20 °C (IRAM 3526-1: pedir ficha local)"),
    "AGUA": ("Agua", "Agua potable", "Enfriamiento", "No", "Aire comprimido", 1.00, 1.00, 1.00,
             "Catálogo de referencia: aire comprimido"),
    "AFFF": ("Agua + espumígeno AFFF 3 % (DEMSA 203 MN, IRAM 3515)", "97 % agua + 3 % concentrado (1,025 g/cm³)",
             "Película acuosa que sella vapores + enfriamiento", "No", "Aire comprimido",
             1.00, 1.00, 1.00, "DEMSA 203 MN: concentrado 1,025 g/cm³ → premezcla ≈ 1,001"),
    "K": ("Acetato de potasio - DEMSA Kitchen (IRAM 3697)", "Sales orgánicas de potasio + aditivos en agua",
          "SAPONIFICACIÓN y enfriamiento: el agente alcalino reacciona con los ácidos grasos del aceite caliente y "
          "forma una espuma jabonosa que sella la superficie y evita la reignición",
          "Sí: mecanismo principal (pH 8,5)", "N₂", 1.30, 1.30, 1.30,
          "DEMSA Kitchen: 1,300 g/ml a 20 °C, pH 8,5; agente certificado en las licencias IRAM 3694 de Drago y "
          "Georgia/Fadesa"),
}
RHO_AGENTE = {k: v[6] for k, v in AGENTES.items()}
# Densidad empacada (asentada) mínima: es la que ocupa el polvo dentro del recipiente después del vibrado de la
# carga. IRAM 3569 no la fija; se adopta el mínimo de la NOM-104-STPS-2001 (polvo ABC de fosfato monoamónico):
# densidad aparente ≥ 0,82 y empacada ≥ 1,10 g/cm³. Criterio de aceptación: descarga continua ≥ 85 % de la masa en
# el ensayo de tipo (IRAM 3523 4.9.1). Los demás agentes los carga el fabricante del equipo revendido.
RHO_EMPACADA = {"ABC": 1.10}
FUENTE_EMPACADA = ("NOM-104-STPS-2001 (México): polvo ABC, densidad empacada ≥ 1,10 g/cm³ (aparente ≥ 0,82). IRAM 3569 "
                   "no fija densidad: exigir el valor en la OC y verificar con descarga ≥ 85 % (IRAM 3523 4.9.1)")
MOLAR = {"N₂": 0.028, "Argón": 0.040, "Aire comprimido": 0.029}


def _f(v, d=1):
    s = f"{v:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return s.rstrip("0").rstrip(",") if "," in s else s


def _tam(m):
    return m.capacidad.replace(".", ",")


def _agente(m):
    if "_ABC_" in m.codigo:
        return "ABC"
    if "_BC_" in m.codigo:
        return "BC"
    if "CLASED" in m.codigo:
        return "D"
    if "HCFC" in m.codigo:
        return "HCFC"
    if "ABC" in m.codigo:
        return "ABC"
    if "CO2" in m.codigo:
        return "CO2"
    if "AFFF" in m.codigo:
        return "AFFF"
    if "SALESK" in m.codigo:
        return "K"
    return "AGUA"


def _ps(m):
    return float(m.spec["Presión de servicio (MPa)"].replace(",", "."))


def _bbox(s):
    bb = s.BoundingBox()
    return sorted((bb.xlen, bb.ylen, bb.zlen), reverse=True)


# ------------------------------------------------------------------ medidas por pieza
def medida(m, k, s, info):
    """Medida característica de la pieza (mm) a partir del modelo y de la geometría del plano."""
    g = m.geo
    D = 2 * g["R"]
    L, A, H = _bbox(s)
    if k == "oblea_pba":
        return "Ø46 (Res. OPDS 522/07), numerada, autodestructible"
    if k in ("etiqueta", "sello_iram", "tarjeta_caba", "etiqueta_serie", "faja_garantia"):
        bb = s.BoundingBox()
        arco = s.Volume() / (0.2 if k == "faja_garantia" else 0.3) / bb.zlen
        if k == "etiqueta":
            return (f"{_f(arco, 0)} × {_f(bb.zlen, 0)} (desarrollo × alto: panel central 108° + 2 alas laterales), "
                    "e ≈ 0,3, laminado UV")
        return f"{_f(arco, 0)} × {_f(bb.zlen, 0)}"
    if k == "junta_cuello":
        return f"Ø{_f(L, 1)} ext. × cordón 3"
    if k == "precinto":
        return "Ø5 × 10, numerado, rotura 30-50 N"
    if k == "cuerpo":
        if m.familia == "co2":
            return f"Cilindro sin costura Ø{_f(D)} × e{_f(g['t'], 2)} × {_f(L)} de alto (cuello integral)"
        largo = s.BoundingBox().zlen
        return (f"Ø{_f(D)} × e{_f(g['t'], 2)} × {_f(largo)} de alto; desarrollo {_f(math.pi * (D - g['t']))} × "
                f"{_f(largo)}")
    if k in ("cupula", "fondo"):
        e = g["td"] if k == "cupula" else g["tf"]
        return f"Ø{_f(D)} × e{_f(e, 2)} × {_f(s.BoundingBox().zlen)} de alto; disco Ø{_f(disco(m, k, s))}"
    if k == "cuello":
        dn, hn, rosca, dh = g["cuello"]
        return f"Ø{_f(dn)} × {_f(hn)} de alto, rosca {rosca}, asiento Ø{_f(dh)}"
    if k in ("manguera", "manguera_enrollada", "bastidor", "brazo_difusor"):
        r = {"manguera": 8.0, "manguera_enrollada": 12.5, "bastidor": 12.7, "brazo_difusor": 6.0}[k]
        if k == "manguera":
            r = (A / 2) if A < 40 else r
        largo = s.Volume() / (math.pi * r * r)
        tubo = {"bastidor": "caño Ø25,4 × 1,6", "brazo_difusor": "tubo Ø12"}.get(k, f"Ø{_f(2 * r)}")
        return f"{tubo} × {_f(largo, 0)} de largo desarrollado"
    if k == "cano_pesca":
        return f"Ø{_f(A)} × {_f(L)} de largo"
    if k in ("rueda_der", "llanta_der"):
        Dw = float(m.spec["Diámetro de rueda (mm)"])
        return f"Ø{_f(Dw if k == 'rueda_der' else Dw * 0.72)} × {_f(A if A < L else H)} de ancho"
    if k == "eje_ruedas":
        return f"Ø25 × {_f(L)} de largo"
    if k == "manometro":
        return f"Ø{_f(L)} esfera, rango 0-{_f(_ps(m) * 2.5 if _ps(m) < 5 else 25, 1)} MPa, sector verde en {_f(_ps(m), 1)}"
    return f"{_f(L)} × {_f(A)} × {_f(H)}"


def disco(m, k, s):
    t = (m.geo["td"] if k == "cupula" else m.geo["tf"])
    d = DISCO.get((k, _tam(m)))
    if d and m.familia == "manual":
        return d[0]
    area = s.Volume() / t                       # superficie media de la chapa embutida
    return 2 * math.sqrt(area / math.pi) * 1.03  # + 3 % de recorte de pestaña


def operacion(m, k):
    rod = m.familia == "rodante"
    if m.codigo not in PROPIOS:
        return "S4 - se compra terminado (tercerizado con sello IRAM)"
    if k == "cuerpo":
        if m.capacidad == "1 kg":
            return "5 Corte láser de caño (M15/M16) -> 9 encastre"
        return ("1 Guillotina -> C1 cilindrado -> C2 punteo -> C3 sold. long." if rod else
                "1 Guillotina -> 2 numerado -> 3 cilindrado -> 4 soldadura longitudinal")
    if k in ("cupula", "fondo"):
        return "Compra (casquetes de carros, rack RK1)" if rod else "6 Desbobinado + embutido (M06-M08)"
    if k == "varilla":
        return "Corte de barra -> C2 punteo interior antes de C3 soldadura longitudinal"
    if k == "cuello":
        return "Compra -> C2 punteo" if rod else "Compra -> 8 soldadura de cuello"
    if SUB.get(k) == 2:
        return "C9 armado" if rod else "19 Ensamblaje de válvula (T03/T04)"
    if SUB.get(k) == 3:
        return "C9 armado de ruedas y manguera" if rod else "19 Ensamblaje (T03/T04)"
    if k in CARRO_FAB:
        return ("Corte en sierra -> curvado / plegado -> soldadura MAG del carro -> C9 armado (S-TC); "
                "puesto de soldadura de carros a incorporar al layout")
    if SUB.get(k) == 4:
        return "C9 armado de ruedas (S-TC)"
    return ""


def origen(m, k):
    if m.codigo not in PROPIOS:
        return "Compra (en el conjunto)"
    if k == "cuello":
        return "Compra (mecanizado, Eli-Met)"
    if k in ("cuerpo", "varilla") or (k in ("cupula", "fondo") and m.familia != "rodante"):
        return "Fabricación"
    if k in ("cupula", "fondo"):
        return "Compra (tapa embutida tercerizada)"
    if k in KIT_VALVULA:
        return "Incluido en válvula HZ"
    if m.familia == "rodante" and k in CARRO_FAB:
        return "Fabricación"
    if k == "llanta_der":
        return "Incluido en rueda"
    if k in ("soportes_manguera", "suncho"):
        return "Compra (estructura)"
    return "Compra"


# ------------------------------------------------------------------ carga y gas impulsor
def carga(m):
    """(agente, kg o L, UM, norma del agente, gas impulsor, kg de gas, Nm³) según tipo y volumen."""
    ag = _agente(m)
    V = m.geo["vol_dm3"]
    cap = m.capacidad
    n_ag = m.spec.get("Norma IRAM agente extintor", "-")
    if ag in ("ABC", "BC", "D", "HCFC"):
        kg = float(cap.split()[0].replace(",", ".")) if "kg" in cap else round(float(cap.split()[0]) * RHO_AGENTE["D"], 1)
        # D 9 l: 9 dm³ de polvo a densidad típica
        nombre = {"ABC": "Polvo químico seco ABC (fosfato monoamónico)", "BC": "Polvo químico seco BC (bicarbonato)",
                  "D": "Polvo para metales combustibles clase D", "HCFC": "HCFC 123 / HFC 236fa (agente limpio)"}[ag]
        v_ag = kg / RHO_EMPACADA.get(ag, RHO_AGENTE[ag])
        gas = AGENTES[ag][4]
        libre = max(0.0, V - v_ag)
        q, um = kg, "kg"
    elif ag == "CO2":
        kg = float(cap.split()[0])
        return ("Dióxido de carbono (IRAM 41170)", kg, "kg", n_ag, "- (autopresurizado)", 0.0, 0.0, 0.0)
    else:
        litros = float(cap.split()[0])
        nombre = AGENTES[ag][0]
        q, um = litros, "L"
        gas, libre = AGENTES[ag][4], V - litros
        kg = litros
    pa = (_ps(m) + 0.101) * 1e6
    n = pa * libre * 1e-3 / (8.314 * 293.15)
    m_gas = n * MOLAR[gas]
    nm3 = n * 0.022414
    return (nombre, q, um, n_ag, gas, m_gas, nm3, libre)


# tolerancia de carga: IRAM 3517-2:2020 tabla 3 (9.4.12) e IRAM 3523 tabla II (4.6). La carga objetivo se toma
# en el centro de la banda cuando la tolerancia es sólo positiva (0 / +X), para no quedar nunca por debajo.
def tolerancia(m):
    """(texto de tolerancia, carga objetivo, referencia)."""
    ag = _agente(m)
    _, q, um, *_ = carga(m)
    n = m.spec["Norma IRAM extintor"]
    ref = "IRAM 3517-2:2020 tabla 3"
    if n == "3523":
        x = 0.1 if q <= 2.5 else 0.3
        return f"0 / +{_f(x * 1000, 0)} g", q + x / 2, ref + " · IRAM 3523 tabla II"
    if n in ("3550", "3541", "3537", "3525", "3527"):
        return "± 3 %", q, ref
    if n == "3694":
        return "0 / +3 %", q * 1.015, ref
    if n in ("3509", "3565"):
        return "0 / -5 %", q, ref
    if n == "3504":
        return ("0 / -2 %" if q <= 2.5 else "0 / -3 %"), q, ref
    return "-", q, ""


# ------------------------------------------------------------------ embalaje
def embalaje(m, bb):
    W, Dd, H = bb.xlen, bb.ylen, bb.zlen
    if m.familia == "rodante":
        n = max(1, int(1200 // W) * int(1000 // Dd)) if W < 1200 and Dd < 1000 else 1
        return dict(caja=None, por_pallet=n, film=0.35 / n, capas=1)
    cw, cd, ch = W + 30, Dd + 30, H + 20
    capas = max(1, int(1450 // ch))
    por_capa = max(int(1200 // cw) * int(1000 // cd), int(1200 // cd) * int(1000 // cw), 1)
    n = capas * por_capa
    pared = "simple" if m.familia == "manual" and float(m.geo["vol_dm3"]) < 7 else "doble"
    return dict(caja=(cw, cd, ch, pared), por_pallet=n, film=0.35 / n, capas=capas)


# ------------------------------------------------------------------ BOM de un producto
NIV_EST = {"V": 0, "E": 1, "A": 2, "X": 3}
EST_PROV = {"COTIZADO": "V", "A COTIZAR": "V", "ESTIMADO": "E", "A VALIDAR": "A", "NO CUMPLE / A DEFINIR": "X"}
ID_PIEZA = {"etiqueta": "ETIQUETA", "oblea_pba": "OBLEA-PBA", "sello_iram": "ESTAMPILLA", "tarjeta_caba": "TARJETA-AGC",
            "etiqueta_serie": "ETIQ-SERIE", "faja_garantia": "FAJA", "precinto": "PRECINTO", "manometro": "MANOMETRO",
            "junta_cuello": "ORING"}


def _item(m, k):
    """Ítem de compra (proveedores.ITEMS) de una pieza del plano."""
    rod = m.familia == "rodante"
    if k in ID_PIEZA:
        return ID_PIEZA[k]
    if k in ("cupula", "fondo") and rod:
        return "TAPA-ROD-G" if m.capacidad in ("70 kg", "100 kg") else "TAPA-ROD-C"
    if k == "cuello":
        return "MP-CUPLA" if rod else "MP-CUELLO"
    if k == "rueda_der":
        return f"RUEDA-{int(float(m.spec['Diámetro de rueda (mm)']))}"
    if SUB.get(k) == 2 and k not in KIT_VALVULA:
        return "REP-VALV"
    if SUB.get(k) == 3:
        return "DESC-ROD" if rod else "DESC-MAN"
    return ""


def _clasificar(rows, m, cilindro):
    """Completa Entra MRP, proveedores y estado (color) de cada fila."""
    propio = m.codigo in PROPIOS
    for r in rows:
        n = r["nivel"]
        if not r["mrp"]:
            if n <= 1:
                r["mrp"] = ""
            elif not propio and not cilindro:
                r["mrp"] = "No"
            elif n == 3:
                r["mrp"] = "Sí"
            else:
                r["mrp"] = "Sí" if r["ori"].startswith("Compra") else "No"
        prov, alt, est_p = ("", "", "")
        if r["mrp"] == "Sí" and r["item"]:
            prov, alt, est_p = PV.asignar(r["item"])
        r["prov"], r["alt"] = prov, alt
        est = r["est"] or ("A" if r["fte"] == "V" else "V")
        if not propio and not cilindro and r["mrp"] == "No":
            est = "V"     # referencia: viene dentro del equipo terminado comprado
        elif est_p and NIV_EST[EST_PROV[est_p]] > NIV_EST[est]:
            est = EST_PROV[est_p]
        r["est"] = est
    return rows


def _cordon(m, piezas):
    """Longitud de cordón de soldadura del recipiente (mm) a partir del plano."""
    g = m.geo
    D = 2 * g["R"]
    lon = 0.0 if m.capacidad == "1 kg" else piezas["cuerpo"].BoundingBox().zlen
    return lon, 2 * math.pi * D, math.pi * g["cuello"][0]


def bom_producto(m, cilindro=False):
    """Filas del BOM. Si `cilindro`, sólo el recipiente vendido suelto (plano FL_REC)."""
    piezas, info = M.construir(m)
    filas_plano, orden, _ = P.lista(m, piezas)
    cod_plano = m.codigo.replace("FL_MAT_", "FL_REC_") if cilindro else m.codigo
    base = P.codigo_pieza(m, 0)[:-3]
    propio = m.codigo in PROPIOS
    rows = []

    def add(nivel, cod, desc, cant, um, mat="", med="", peso=None, ori="", op="", norma="", fte="", plano="",
            obs="", sub=0, item="", est="", mrp=""):
        peso = None if peso is None else round(peso, 4)   # kg por unidad de medida
        rows.append(dict(nivel=nivel, codigo=cod, desc=desc, cant=cant, um=um, mat=mat, med=med, peso=peso,
                         ori=ori, op=op, norma=norma, fte=fte, plano=plano, obs=obs, sub=sub, item=item, est=est,
                         mrp=mrp))

    nombre = (f"Cilindro (recipiente) {m.nombre.replace('Extintor ', '').replace(' sobre ruedas', ' rodante')} "
              "- repuesto vacío sin válvula") if cilindro else m.nombre
    n_ext = m.spec["Norma IRAM extintor"]
    add(0, cod_plano, nombre, 1, "u", norma=f"IRAM {n_ext}", fte="P",
        plano=cod_plano, obs=("Fabricación propia" if propio else "Revendido: se compra terminado al fabricante "
                              "con Sello IRAM; las piezas internas quedan como referencia (no entran en MRP)"))
    if not propio and not cilindro:
        add(1, f"{base}-S0", "Equipo terminado comprado (fabricante con Sello IRAM)", 1, "u",
            ori="Compra", op="Recepción y control de ingreso (SP-1)", norma=f"IRAM {n_ext}", fte="I",
            plano=cod_plano, obs="Única fila de compra del revendido (más la tarjeta AGC si el destino es CABA)",
            item=PV.equipo(m), mrp="Sí")
    # ---- piezas del plano agrupadas por subconjunto
    por_sub = {}
    for fila, k in zip(filas_plano, orden):
        por_sub.setdefault(SUB.get(k, 2), []).append((fila, k))
    subs = [1] if cilindro else [s for s in (1, 2, 3, 4) if s in por_sub]
    for s_ in subs:
        cod_sub = f"{base}-S{s_}"
        if s_ == 1 and not cilindro and m.codigo.startswith("FL_MAT_ABC"):
            cod_sub = m.codigo.replace("FL_MAT_", "FL_REC_")
        plano_sub = cod_sub if cod_sub.startswith("FL_REC") else f"FL_DES_{m.codigo[7:]}"
        add(1, cod_sub, NOMBRE_SUB[s_], 1, "u", ori=("Fabricación" if s_ in (1, 4) and propio
                                                     and m.familia != "co2" else "Compra / armado"),
            plano=plano_sub, sub=s_,
            norma={1: "IRAM 3523 / 3550 (recipiente)", 2: "Manómetro IRAM 3533",
                   4: "IRAM 3550 3.12 y 4.8 (ruedas ≥ Ø300 × 50)"}.get(s_, ""), fte="P")
        for fila, k in por_sub[s_]:
            pos, cant, nom, cod, mat, _kg, obs = fila
            if cod == "Comercial":
                cod, obs = P.codigo_pieza(m, pos), ("Pieza comercial; " + obs).strip("; ")
            kg = MAT.peso(piezas[k], MAT.especificacion(m, k)[2], MAT.especificacion(m, k)[3])
            fte, est = "P", ""
            if kg is None:
                obs = (obs + "; peso: completar con la ficha del proveedor (no afecta el MRP)").strip("; ")
            if k == "varilla":
                est = "E"
                obs = ("Interior, detrás de la costura longitudinal; se puntea antes de la soldadura longitudinal "
                       "para mantener la simetría del cilindrado (decisión FLAMA). Ø8 = propuesta de diseño, sin "
                       "cálculo")
            if k == "rueda_der":
                obs = (obs + "; IRAM 3550 4.8: Ø ≥ 300 y ancho ≥ 50").strip("; ")
            add(2, cod, nom, cant, "u", mat, medida(m, k, piezas[k], info), kg, origen(m, k), operacion(m, k),
                norma=("IRAM 3533" if k == "manometro" else ""), fte=fte, plano=f"FL_DES_{m.codigo[7:]}", obs=obs,
                sub=s_, item=_item(m, k) if propio else "", est=est)
            # materia prima de las piezas fabricadas
            if propio and origen(m, k) == "Fabricación":
                for r in materia_prima(m, k, piezas[k], kg):
                    add(3, *r[:13], sub=s_, item=r[13], est=r[14])
        if s_ == 1:
            for r in consumibles_recipiente(m, piezas):
                add(2, f"{base}-{r[0]}", *r[1:13], sub=1, item=r[13], est=r[14])
        if s_ == 2:
            if propio and not cilindro:
                hz = {"1 kg": "M-22 1 kg c/tubo de pesca plástico", "25 kg": "de carro 25 kg c/traba, manija y resorte"}
                vi = "VALV-1" if m.capacidad == "1 kg" else ("VALV-CARRO" if m.familia == "rodante" else "VALV-M30")
                add(2, f"{base}-K2", "Válvula HZ armada " + hz.get(m.capacidad, "M-30 c/resorte y tubo 7/8" if
                    m.familia != "rodante" else "de carro 50-70-100 kg"), 1, "u", "Latón forjado (HZ)",
                    f"rosca {m.geo['cuello'][2]}", None, "Compra", "19 Ensamblaje de válvula", norma="IRAM 3523 3.3",
                    fte="Q", plano=f"FL_DES_{m.codigo[7:]}", obs="Lista de precios HZ (Q-AGENTES); plano Fadesa usa "
                    "válvula HZ (R-FADESA). Trae las piezas marcadas «Incluido en válvula HZ»",
                    sub=2, item=vi)
            for r in internos_valvula(m):
                add(2, f"{base}-{r[0]}", *r[1:], sub=2)
    if cilindro:
        add(2, f"{base}-T1", "Tapón protector de rosca del cuello", 1, "u", "Polietileno",
            f"para rosca {m.geo['cuello'][2]} (plano {cod_plano} hoja 3, R4)", None, "Compra", "Embalaje", fte="P",
            sub=1, item="TAPON")
        add(2, f"{base}-T2", "Marcado del recipiente (estampado)", 1, "u", "-",
            "Fabricante, n° de serie, año" + (", presión de ensayo" if m.familia == "rodante" else "") +
            "; cuño DPS 15 × 7 junto al n°", None, "Proceso", "Marcado",
            norma=f"IRAM {n_ext} 5.1 · Res. 349/07 anexo IV", fte="N", sub=1)
        add(2, f"{base}-T3", "Etiqueta de identificación del cilindro suelto", 1, "u", "Poliéster autoadhesivo "
            "removible", "100 × 60, impresión térmica, QR GS1", None, "Compra", "Etiquetado", fte="P",
            plano=f"{cod_plano} hoja 3", sub=1, item="ETIQ-SERIE")
        add(2, f"{base}-T4", "Protocolo de ensayo hidrostático (certificado que acompaña)", 1, "u", "Papel", "A5",
            0.005, "Proceso", "Control de calidad", norma=f"IRAM {n_ext} 4.1 y cap. 6 · IRAM 2587", fte="N",
            plano=f"{cod_plano} hoja 3", sub=1)
        emb = embalaje(m, M.bbox({k: v for k, v in piezas.items() if SUB.get(k) == 1}))
        _emb(add, base, emb, m, sub=7, cilindro=True)
        return _clasificar(rows, m, cilindro)
    # ---- carga
    ag, q, um, n_ag, gas, m_gas, nm3, libre = carga(m)
    add(1, f"{base}-S5", NOMBRE_SUB[5], 1, "u", ori="Carga en planta" if propio else "Compra",
        op=("18 Carga de polvo (T01) / C8 (T02)" if propio else ""), sub=5)
    tol, obj, ref_tol = tolerancia(m)
    ag_m = AG.agente(m)
    comp = ""
    if ag_m["grado"] in AG.GRADOS_ABC:
        g_ = AG.GRADOS_ABC[ag_m["grado"]]
        k_map, k_rel, k_ad = AG.composicion_abc(ag_m["grado"], obj)
        ag = f"Polvo químico seco {ag_m['grado']} (Sello IRAM 3569)"
        comp = (f"Composición declarada del polvo {ag_m['grado']}: MAP {_f(g_['map'], 0)} % (IRAM 3569: "
                f"{_f(g_['banda'][0], 2)}-{_f(g_['banda'][1], 2)} %) = {_f(k_map, 3)} kg MAP + {_f(k_rel, 3)} kg "
                f"{AG.RELLENO_ABC} + {_f(k_ad, 3)} kg aditivos · potencial de referencia {ag_m['potencial']} (licencia "
                "Drago con DEM-60/90, L-DRAGO) · Decisión: DEMSA principal (sello IRAM 3569 y potencial de "
                "referencia); Polvex/Sancibrao alternativa sujeta a sello IRAM 3569 y ensayo de tipo de FLAMA "
                "(IRAM 3542/3543)")
        if ag_m.get("alternativa"):
            comp += f" · alternativa {ag_m['alternativa']}"
    elif _agente(m) in ("BC", "D", "K", "HCFC"):
        ag = f"{ag[:ag.find('(')].strip() if '(' in ag else ag} - {ag_m['grado']}"
        comp = f"potencial {ag_m['potencial']}" + (f" · alternativa {ag_m['alternativa']}" if ag_m.get("alternativa") else "")
    if _agente(m) == "AFFF":
        add(2, f"{base}-A1", "Agua potable (premezcla)", round(q * 0.97, 3), "L", "Agua", f"97 % de {_f(q)} L; "
            f"tolerancia {tol}", 1.0, "Red", "SP-1 premezcla", norma=ref_tol, fte="N", sub=5)
        ag, q, um = "Concentrado espumígeno AFFF 3 % (IRAM 3515)", round(q * 0.03, 3), "L"
    add(2, f"{base}-A1" + ("b" if _agente(m) == "AFFF" else ""), ag, q if _agente(m) == "AFFF" else round(obj, 3), um, ag,
        f"nominal {_f(q, 3)} {um}; tolerancia {tol} ({ref_tol})", (RHO_AGENTE.get(_agente(m), 1.0) if um == "L" else 1.0),
        "Compra", "SP-1 almacén previo a la carga", norma=ag_m["norma"], fte="N",
        obs=(comp + (" · " if comp else "") + ("Lote único por extintor; prohibido mezclar ABC con BC (3517-2 "
             "9.9.1.6)" if _agente(m) in ("ABC", "BC") else "")).strip(" ·"), sub=5,
        item="POLVO-ABC" if _agente(m) == "ABC" else "")
    if not gas.startswith("-"):
        rho_e = RHO_EMPACADA.get(_agente(m))
        if libre <= 0:
            aviso, est_g = (f"EL AGENTE NO ENTRA con ρ empacada {_f(rho_e or 0, 2)}: ver 09_Carga_N2", "X")
        else:
            aviso = ("N₂ ≥ 99,8 %, H₂O ≤ 40 ppm (Q-N2, Air Liquide)" if "N" in gas else
                     "Batería en SP-1; punto de rocío ≤ -56,7 °C para gases limpios")
            est_g = "E" if rho_e else ""
            if rho_e:
                aviso += (f" · volumen libre con ρ empacada mínima {_f(rho_e, 2)} kg/dm³ (NOM-104-STPS-2001); "
                          "confirmar con descarga ≥ 85 % (IRAM 3523 4.9.1)")
        add(2, f"{base}-A2", f"Gas impulsor: {gas}", round(m_gas, 4), "kg", gas,
            f"{_f(nm3 * 1000, 1)} L normales para {_f(_ps(m), 1)} MPa a 20 °C en {_f(libre, 2)} dm³ libres",
            1.0, "Compra", "20 Presurización (T05) / C10", norma="IRAM 3517-2 9.4.9 (tabla 2) · IRAM 3523 2.3 y 3.10",
            fte="C", obs=aviso, sub=5, item="N2" if "N" in gas else "", est=est_g)
    # ---- identificación, precinto y accesorios
    add(1, f"{base}-S6", NOMBRE_SUB[6], 1, "u", ori="Compra", op="22 Etiquetado (T07)", sub=6)
    norma_id = {"etiqueta": f"IRAM 3534 · IRAM {n_ext} cap. 5 · relevamiento de mercado",
                "sello_iram": "IRAM Anexo R (DC-PG-129)", "oblea_pba": "Res. OPDS 522/07 anexos 1, 2 y 6",
                "precinto": "IRAM 3523 3.3.2 · IRAM 3517-2:2020 9.4.13",
                "faja_garantia": "Sin norma: práctica de mercado (garantía de fábrica)",
                "tarjeta_caba": "Ordenanza 40.473 art. 6 · Res. AGC 32/15",
                "etiqueta_serie": "GS1 Argentina (GTIN 779) · trazabilidad IRAM 3523 5.1"}
    op_id = {k: "22 Etiquetado (T07)" for k in norma_id}
    op_id["precinto"] = "20 Presurización (T05)"
    for fila, k in por_sub.get(6, []):
        pos, cant, nom, cod, mat, _kg, obs = fila
        kg = MAT.peso(piezas[k], MAT.especificacion(m, k)[2], MAT.especificacion(m, k)[3])
        rev_agc = not propio and k == "tarjeta_caba"
        add(2, cod, nom, cant, "u", mat, medida(m, k, piezas[k], info), kg, "Compra", op_id[k], norma=norma_id[k],
            fte="P", plano=f"FL_DES_{m.codigo[7:]}", obs=(obs + "; sólo destino CABA").strip("; ") if rev_agc else obs,
            sub=6, item=_item(m, k) if (propio or rev_agc) else "", mrp="Sí" if rev_agc else "")
    sop = m.spec.get("Soporte pared"), m.spec.get("Soporte vehicular")
    if "Si" in sop or "Opcional" in sop:
        add(1, f"{base}-S8", NOMBRE_SUB[8], 1, "u", ori="Compra", op="23 Embalaje (va dentro de la caja)",
            norma="IRAM 3517-2 7.4", sub=8)
    if sop[0] == "Si":
        kg_s = AC.soporte_pared(g=m.geo, e=2.0)[0].Volume() * 1e-6 * MAT.ACERO
        add(2, f"{base}-I5", "Soporte de pared (FL_ACC_01)", 1, "u", "Chapa acero SAE 1010 e=2 pintada",
            "placa 60 × 180, ala con ranura Ø cuello + 3", round(kg_s, 3), "Compra", "23 Embalaje",
            norma="IRAM 3517-2 7.4", fte="P", plano="FL_ACC_01", sub=8, item="SOPORTE")
        add(2, f"{base}-I6", "Tornillo y tarugo de fijación", 2, "u", "Acero cincado / nylon",
            "2 agujeros Ø8,5 del plano FL_ACC_01 → tornillo M8 + tarugo", None, "Compra", "23 Embalaje", fte="P",
            plano="FL_ACC_01", sub=8, item="TORNILLERIA")
    if sop[1] == "Si":
        kg_s = AC.soporte_vehicular(g=m.geo, e=2.5)[0].Volume() * 1e-6 * MAT.ACERO
        add(2, f"{base}-I7", "Soporte vehicular con cierre rápido (FL_ACC_02)", 1, "u",
            "Chapa acero SAE 1010 e=2,5 pintada", "base 80 de ancho, 2 aros con hebilla", round(kg_s, 3), "Compra",
            "23 Embalaje", norma="IRAM 3517-2 7.4", fte="P", plano="FL_ACC_02", sub=8, item="SOPORTE")
    if "Opcional" in sop:
        add(2, f"{base}-I8", "Soporte opcional (pared o vehicular, según pedido)", 0, "u", "-", "-", None,
            "Compra", "", fte="N", norma="IRAM 3517-2 7.4", obs="Sólo si el pedido lo incluye", sub=8, item="SOPORTE")
    # ---- embalaje
    emb = embalaje(m, M.bbox(piezas))
    _emb(add, base, emb, m, sub=7)
    return _clasificar(rows, m, cilindro)


FILM_PALLET = 0.12   # kg de film por pallet (cálculo en la observación de E4)


def _emb(add, base, emb, m, sub, cilindro=False):
    add(1, f"{base}-S7", NOMBRE_SUB[7], 1, "u", ori="Compra", op="23 Embalaje -> 24 envolvedora (T11)", sub=sub)
    n = emb["por_pallet"]
    if emb["caja"]:
        cw, cd, ch, pared = emb["caja"]
        add(2, f"{base}-E1", f"Caja de cartón corrugado {pared}", 1, "u", "Cartón corrugado",
            f"{_f(cw, 0)} × {_f(cd, 0)} × {_f(ch, 0)} interior (envolvente del plano + 15 por lado)", None, "Compra",
            "23 Embalaje", fte="P", obs="Medida del plano", sub=sub, item="CAJA")
        if not cilindro:
            add(2, f"{base}-E2", "Instructivo de uso y mantenimiento", 1, "u", "Papel", "A5", None, "Compra",
                "23 Embalaje", fte="I", obs="Decisión comercial de FLAMA (las instrucciones de uso obligatorias van en la "
                "etiqueta, IRAM 3534)", sub=sub, item="IMPRESOS")
    else:
        add(2, f"{base}-E1", "Esquineros y funda de polietileno", 1, "jgo", "PE / cartón",
            "a medida de la envolvente del plano", None, "Compra", "23 Embalaje", fte="P",
            obs="Medida del plano", sub=sub, item="FUNDA")
    add(2, f"{base}-E3", "Pallet 1200 × 1000 (fracción)", round(1 / n, 4), "u", "Madera", f"{n} u por pallet",
        None, "Compra", "23 Embalaje", fte="C", obs="u por pallet = acomodo de la caja (plano) en 1200 × 1000 × "
        "1450 de alto", sub=sub, item="PALLET")
    add(2, f"{base}-E4", "Film stretch (fracción del pallet)", round(FILM_PALLET / n, 4), "kg", "PE lineal 23 µm",
        f"{_f(FILM_PALLET, 2)} kg por pallet / {n} u", 1.0, "Compra", "24 Envolvedora (T11)", fte="C",
        obs="Perímetro del pallet 4,4 m × 9 vueltas = 40 m aplicados; con pre-estirado 250 % (1 m de bobina = 3,5 m "
            "aplicados) = 11,4 m de bobina × 0,5 m × 23 µm × 0,92 g/cm³ = 0,12 kg. Fuentes: fichas de film 23 µm × "
            "500 mm (MV Embalajes / Embalpack) y pre-estirado de la envolvedora. Medir en la puesta en marcha",
        sub=sub, item="FILM", est="E")
    add(2, f"{base}-E5", "Etiqueta de pallet (lote y destino, fracción)", round(1 / n, 4), "u", "Papel térmico",
        "100 × 150", None, "Compra", "24 Envolvedora", fte="C", sub=sub, item="ETIQ-PALLET")
    if emb["caja"]:
        cw, cd, ch, _ = emb["caja"]
        largo = 2 * (cw + 2 * 70)
        add(2, f"{base}-E6", "Cinta de embalaje PP 48 mm (cierre de la caja)", round(largo / 1000, 3), "m",
            "Polipropileno con adhesivo acrílico", f"cierre en I arriba y abajo: 2 × ({_f(cw, 0)} + 2 × 70 de "
            "solapa)", None, "Compra", "23 Embalaje", fte="C", sub=sub, item="CINTA", est="E",
            obs="Solapa de 70 mm por lado: práctica de cierre de cajas (medir en la línea)")
        add(2, f"{base}-E7", "Esquineros de cartón 50 × 50 × 1200 (fracción del pallet)", round(4 / n, 4), "u",
            "Cartón", f"4 por pallet / {n} u", None, "Compra", "24 Envolvedora (T11)", fte="C", sub=sub,
            item="ESQUINERO", obs="Planilla MP-64")
    if cilindro:
        capas = emb.get("capas", 1)
        add(2, f"{base}-E8", "Separador de capa de cartón 1200 × 1000 (fracción del pallet)",
            round(max(capas - 1, 0) / n, 4), "u", "Cartón", f"{capas} capas → {max(capas - 1, 0)} separadores por "
            f"pallet / {n} u", None, "Compra", "23 Embalaje", fte="C", sub=sub, item="SEPARADOR",
            obs="Planilla MP-61")


def materia_prima(m, k, s, kg):
    """Nivel 3: materia prima de las piezas fabricadas (código, descripción, cant, UM, material, medida, peso,
    origen, operación, norma, fuente, plano, obs, ítem de compra, estado)."""
    g = m.geo
    tam = _tam(m)
    rod = m.familia == "rodante"
    out = []

    def barra(cod, desc, mat, L, kg_m, item, est="", obs=""):
        out.append((cod, f"{desc} (tramo de barra de 6 m)", round(L / 6000, 4), "barra", mat,
                    f"{_f(L, 0)} mm por pieza (kg por barra de 6 m)", round(kg_m * 6, 3), "Compra",
                    "Corte en sierra", "", "C", "", obs, item, est))

    if k == "cuerpo":
        if m.capacidad == "1 kg":
            c = CANO_1KG
            out.append(("MP-CANO", f"Caño Ø{_f(c['diam'])} × {_f(c['esp'], 2)} (tramo de barra de 6 m)",
                        round(1 / c["piezas"], 4), "barra", "Caño acero SAE 1010 con costura",
                        f"{c['pieza']} mm por cuerpo; {c['piezas']} cuerpos por barra (kg por barra)",
                        round(kg * c['barra'] / c['pieza'], 3), "Compra", "AL-1T cantiléver", "", "L", "FL_PI_04 h2",
                        "", "MP-CANO", ""))
        elif tam in HOJA_CUERPO:
            fmt, e, alto, des, ap = HOJA_CUERPO[tam]
            bruto = alto * des * e * 7.85e-6 / (ap / 100)
            obs = "" if abs(e - g["t"]) < 0.01 else f"OJO: la hoja de corte usa e={_f(e, 2)} y el plano e={_f(g['t'], 2)}"
            out.append(("MP-HOJA", f"Recorte de hoja {fmt} e={_f(e, 2)}", 1, "u",
                        ("Chapa LAC IRAM-IAS U 500-04 " if rod else "Chapa LAF IRAM-IAS U 500-05 ") + fmt.split()[0],
                        f"{_f(alto)} × {_f(des)} (aprovech. {_f(ap)} %)", round(bruto, 3), "Compra",
                        "AL-1H paquetes de hojas", "", "L", "FL_PI_04 h2", obs,
                        "MP-HOJA-LAC" if rod else "MP-HOJA-LAF", "X" if obs else ""))
    if k == "varilla":
        barra("MP-VARILLA", "Redondo liso SAE 1010 Ø8", "Redondo liso SAE 1010 Ø8", s.BoundingBox().zlen, 0.395,
              "MP-VARILLA", "E", "Ø8 = propuesta de diseño (sin cálculo)")
    if k == "eje_ruedas":
        barra("MP-EJE", "Redondo SAE 1045 Ø25", "Redondo SAE 1045 Ø25", s.BoundingBox().xlen,
              math.pi / 4 * 25 ** 2 * 7.85e-3, "MP-EJE")
    if k == "bastidor":
        barra("MP-CANO-CARRO", "Caño SAE 1010 Ø25,4 × 1,6", "Caño acero SAE 1010 Ø25,4 × 1,6",
              s.Volume() / (math.pi * 12.7 ** 2), math.pi / 4 * (25.4 ** 2 - 22.2 ** 2) * 7.85e-3, "MP-CANO-CARRO",
              obs="Largo desarrollado del plano + curvado")
    if k == "sunchos_bastidor":
        ws, ts = M.planchuela(g["R"])
        sec = f"{_f(ws, 0)} × {_f(ts, 0)}"
        barra("MP-PLANCHUELA", f"Planchuela SAE 1010 {sec}", f"Planchuela SAE 1010 {sec}", s.Volume() / (ws * ts),
              ws * ts * 7.85e-3, "MP-PLANCHUELA", est="E",
              obs=f"Largo = volumen del plano / sección {sec}. Sección dimensionada para la masa de los planos Fadesa")
    if k == "apoyo":
        out.append(("MP-CHAPA-APOYO", "Recorte de chapa LAC e=3,2 para el apoyo plegado", 1, "u", "Chapa LAC SAE 1010",
                    "desarrollo del apoyo + 15 % de recorte", round(kg * 1.15, 3), "Compra", "Corte y plegado", "",
                    "C", "", "15 % de recorte: valor de taller sin medir", "MP-CHAPA-APOYO", "E"))
    if k in ("cupula", "fondo"):
        d = DISCO.get((k, tam))
        e = g["td"] if k == "cupula" else g["tf"]
        if d:
            Ø, e_l, anc = d
            paso = Ø + 3
            kg_m = anc * 1000 * e_l * 7.85e-6         # kg por metro de fleje
            obs = "" if abs(e_l - e) < 0.01 else f"OJO: el fleje es e={_f(e_l, 2)} y el plano e={_f(e, 2)}"
            out.append(("MP-FLEJE", f"Fleje e={_f(e_l, 2)} × {anc} (paso {_f(paso)})", round(paso / 1000, 4), "m",
                        "Fleje SAE 1010", f"disco Ø{Ø} (kg por m de fleje)", round(kg_m, 3), "Compra",
                        "AL-1F porta-flejes", "", "L", "FL_PI_04 h2", obs, "MP-FLEJE", "X" if obs else ""))
    return out


# consumos de soldadura y granallado: fuentes técnicas citadas en la columna Observaciones
REND_ALAMBRE = 0.95      # ESAB: rendimiento de deposición del alambre macizo MAG 90-97 %
CAUDAL_GAS = 14.0        # L/min para alambre Ø0,9-1,2 (Air Liquide: 12-16 L/min)
VEL_SOLD = 600.0         # mm/min de avance (Getweld: 0-1500 mm/min; 340 u por turno de 8 h)
GRANALLA_H = 3.4         # kg/h: regla «lb/h ≈ HP / 2» por turbina (The Fabricator), Airblast G-100 2 × 7,5 HP
RITMO_LINEA = 42.5       # u/h: 340 u por turno de 8 h (Getweld)


def consumibles_recipiente(m, piezas):
    """Consumibles del recipiente de fabricación propia (sólo ABC), con el cálculo y la fuente en Observaciones.
    Tupla: (suf, desc, cant, UM, material, medida, peso, origen, operación, norma, fuente, plano, obs, ítem, estado)."""
    if m.codigo not in PROPIOS:
        return []
    rod = m.familia == "rodante"
    v = piezas["soldaduras"].Volume() * 1e-6 * MAT.ACERO
    a = _area(m, piezas)
    lon, circ, cue = _cordon(m, piezas)
    largo = lon + circ + cue
    t_arco = largo / VEL_SOLD
    out = [("C1", "Alambre MAG ER70S-6 " + ("Ø1,2" if rod else "Ø0,9") + " (AWS A5.18)", round(v / REND_ALAMBRE, 4),
            "kg", "ER70S-6", f"metal depositado de los cordones del plano {_f(v * 1000, 0)} g / rendimiento "
            f"{_f(REND_ALAMBRE, 2)}", REND_ALAMBRE, "Compra", "4 sold. long. / 8 cuello / 11 circunferencial",
            "IRAM 3523 3.2.4.2 · IRAM 3550 4.1.2", "C", "",
            "Peso unit. = fracción que queda en la pieza (el resto es salpicadura). Depositado = volumen de los cordones del modelo × 7,85. Rendimiento de deposición del alambre macizo "
            "MAG 90-97 % (ESAB): se adopta 0,95. Medir en la prueba de soldadura del equipo (Getweld)", "C1", "E"),
           ("C2", "Gas de protección MAG Arcal 21 / ARCAL Speed (Ar + 8 % CO₂, M20)", round(CAUDAL_GAS * t_arco, 1),
            "L", "EN ISO 14175 M20-ArC-8", f"{_f(CAUDAL_GAS, 0)} L/min × {_f(t_arco, 2)} min de arco "
            f"(cordones {_f(largo, 0)} mm: long. {_f(lon, 0)} + circ. {_f(circ, 0)} + cuello {_f(cue, 0)}, a "
            f"{_f(VEL_SOLD, 0)} mm/min)", None, "Compra", "Colector SC",
            "IRAM 3523 3.2.4.2 · IRAM 3550 3.2.2.2", "C", "",
            "Caudal 12-16 L/min para alambre 0,9-1,2 (Air Liquide; Ingemecánica): se adopta 14. Velocidad: Getweld "
            "0-1500 mm/min; se adopta 600. Decisión FLAMA: MAG 135 con Arcal 21; la norma nombra «atmósfera "
            "inerte»: acreditar con el certificador en el ensayo de tipo. No incluye la soldadura del carro", "C2", "E")]
    if not rod:
        D = 2 * m.geo["R"]
        entra = 80 <= D <= 200
        out.append(("C3", "Granalla de acero S330 / S390 (ISO 11124-3, SAE J444)", round(GRANALLA_H / RITMO_LINEA, 3),
                    "kg", "Granalla esférica alto C", f"{_f(a, 3)} m² a Sa 2½ (ISO 8501-1); {_f(GRANALLA_H, 1)} kg/h "
                    f"÷ {_f(RITMO_LINEA, 1)} u/h", None, "Compra", "14 Granallado (B08)", "DOC-01", "C", "",
                    "Consumo (desgaste) por turbina ≈ HP / 2 lb/h (The Fabricator, «aspectos básicos del granallado "
                    "por turbina»): G-100 con 2 × 7,5 HP = 7,5 lb/h = 3,4 kg/h; ritmo 340 u por turno (Getweld) = "
                    "42,5 u/h." + ("" if entra else f" OJO: Ø{_f(D)} fuera del rango de la Airblast G-100 (Ø80-200): "
                                   "definir soporte o equipo"), "C3", "E" if entra else "X"))
    out.append(("C4", "Servicio de pintura en polvo al horno, rojo 03-1-050" + (" (con preparación por quemado)" if rod
                else ""), 1, "u", "Servicio tercerizado", f"superficie exterior {_f(a, 3)} m²", None,
                "Compra (servicio)", "17 Pintura tercerizada", "IRAM 3523 5.3 / IRAM 3550 3.11 · IRAM 121", "Q", "",
                ("Q-CARROS (precio por carro)" if rod else "Q-PRYMAX (precio por cilindro)") +
                "; exigir informe de niebla salina del sistema de pintura; tercerización aceptada por el Ministerio "
                "(Res. 349/07 art. 18)", "C4R" if rod else "C4M", ""))
    return out


def _area(m, piezas):
    a = 0.0
    for k, t in (("cuerpo", m.geo["t"]), ("cupula", m.geo["td"]), ("fondo", m.geo["tf"])):
        if k in piezas:
            a += piezas[k].Volume() / t
    return a / 1e6


def internos_valvula(m):
    """Piezas internas de la válvula que el plano de conjunto no dibuja por separado."""
    dn = m.geo["cuello"][0]
    out = []   # la junta tórica de asiento del cuello ahora es pieza del plano (junta_cuello)
    if m.familia != "co2":
        out.append(("V2", "Resorte de retorno del vástago", 1, "u", "Acero para resortes", "incluido en la válvula",
                    None, "Incluido en válvula HZ" if m.codigo in PROPIOS else "Compra (en el conjunto)",
                    "19 Ensamblaje", "", "Q", "", "Lista de precios HZ: válvula «c/resorte» (Q-AGENTES)"))
    out.append(("V3", "Junta tórica del vástago", 1, "u", "NBR 70 Shore A", "incluida en la válvula", None,
                "Incluido en válvula HZ" if m.codigo in PROPIOS else "Compra (en el conjunto)",
                "19 Ensamblaje", "", "P", "", "Figura en el plano como «vástago con junta tórica»"))
    return out


# ------------------------------------------------------------------ recargas
def recargas():
    """Filas de servicio por modelo y caso (repuestos y agente), con el criterio de la IRAM 3517-2:2020."""
    filas = []
    for m in MODELOS:
        ag = _agente(m)
        nombre, q, um, n_ag, gas, m_gas, nm3, libre = carga(m)
        base = P.codigo_pieza(m, 0)[:-3]
        rep = [("Precinto plástico numerado, color, con nombre del recargador", 1, "u", "Nuevo", "9.4.13"),
               ("Marbete (anillo, color del año)", 1, "u", "Nuevo", "9.4.14 · fig. 9 · tabla 4"),
               ("Etiqueta de servicio del recargador (extintor n°, serie, próxima recarga y PH)", 1, "u", "Nuevo",
                "8.3.3 · relevado Suyai/Firegram"),
               ("Oblea PBA de recarga Ø46 + estampilla precinto 1\" × 200 mm válvula-cuerpo", 1, "u",
                "Nuevo (venta en PBA)", "Res. OPDS 522/07"),
               ("Tarjeta de identificación AGC (módulo papel con QR + etiqueta AGC)", 1, "u", "Nuevo (destino CABA)",
                "Ord. 40.473 art. 6 · Res. AGC 32/15"),
               ("Tarjeta de identificación DPS de revisión / recarga", 1, "u", "Nuevo (PBA)", "Res. 349/07 art. 21"),
               ("Grabado de la fecha del servicio en el tubo de pesca (lápiz vibratorio; en polvo, marcador "
                "indeleble)", 1, "u", "Proceso", "Res. 349/07 art. 28"),
               ("Si hubo PH: oblea de vencimiento de PH + «PH» y fecha grabados en el tubo de pesca (CO₂: fecha y logo "
                "estampados en la ojiva)", 1, "u", "Proceso", "Res. 349/07 art. 29 · IRAM 3517-2"),
               ("Junta tórica de asiento del cuello", 1, "u", "Nuevo (R: cambio sistemático)", "-")]
        if m_gas:
            rep.append((f"Gas impulsor {gas}", round(m_gas, 4), "kg", "Nuevo", "9.4.9 tabla 2"))
        if ag in ("ABC", "BC", "D"):
            casos = [
                ("A - Extintor descargado (uso o descarga parcial)",
                 [(nombre, q, um, "Nuevo 100 %", "9.9.1.4: el polvo de un extintor accionado no se reutiliza")]),
                ("B - Mantenimiento con apertura sin descarga (control interior, PH)",
                 [(nombre + " recuperado", round(q * 0.97, 3), um, "Recuperado en sistema cerrado",
                   "4.4.1 y) sistema cerrado de recuperación con inspección; 9.9.3 control (puffer IRAM 3672, "
                   "fusión IRAM 3569 en ABC)"),
                  (nombre + " de reposición de mermas", round(q * 0.03, 3), um, "Nuevo (R: 3 % de merma)",
                   "Mismo tipo y marca (prohibido mezclar ABC con BC, 9.9.1.6)")]),
                ("C - Cambio obligatorio de polvo (versión anterior de la IRAM 3569)",
                 [(nombre, q, um, "Nuevo 100 %; el viejo va a residuos (RC-IR)", "9.9.4")]),
            ]
        elif ag == "HCFC":
            casos = [
                ("A - Extintor descargado", [(nombre, q, um, "Nuevo o reciclado certificado", "9.9 tabla 6 · IRAM 3526")]),
                ("B - Mantenimiento con vaciado (control interior, PH)",
                 [(nombre + " recuperado", round(q * 0.98, 3), um, "Recuperado en circuito cerrado (no se ventea)",
                   "4.4.1 z) recuperación de gases limpios en sistema cerrado"),
                  (nombre + " de reposición de pérdidas", round(q * 0.02, 3), um, "Nuevo o reciclado (R: 2 %)",
                   "El agente fuera de especificación va a regeneración o destrucción por gestor habilitado")]),
            ]
        elif ag == "CO2":
            casos = [
                ("A - Extintor descargado", [(nombre, q, um, "Nuevo (trasvase de batería o tanque criogénico)",
                                             "4.4.1 l) trasvasador; 9.9.1.11 calidad del CO₂")]),
                ("B - Mantenimiento con vaciado (PH cada 5 años)",
                 [(nombre + " recuperado", q, um, "Recuperación en circuito cerrado recomendada", "9.4.18"),
                  ("Disco de seguridad", 1, "u", "Nuevo", "9.4.17 dispositivos")]),
            ]
        else:
            casos = [
                ("A - Extintor descargado", [(nombre, q, um, "Nuevo", "9.9 tabla 6")]),
                ("B - Mantenimiento (PH cada 2 años en inoxidables y AFFF)",
                 [(nombre, q, um, "Nuevo (R: la carga líquida no se recupera; confirmar vida útil del "
                   "concentrado con el fabricante)", "9.9")]),
            ]
        for caso, items in casos:
            for it in items + [(r[0], r[1], r[2], r[3], r[4]) for r in rep]:
                ref = it[4] if it[4].startswith(("Mismo", "El agente")) else "IRAM 3517-2:2020 " + it[4]
                filas.append([m.codigo, m.nombre, caso, it[0], it[1], it[2], it[3], "" if it[4] == "-" else ref])
        filas.append([m.codigo, m.nombre, "Según inspección (consumo estadístico a definir)",
                      "Manómetro / manguera / tobera / kit de válvula", "-", "u", "Recambio sólo si falla",
                      "IRAM 3517-2:2020 9.4.11 (cada manguera vuelve a su extintor)"])
    return filas


# ------------------------------------------------------------------ Excel
COLS = [("Nivel", 6), ("Código", 17), ("Descripción", 52), ("Cant.", 9), ("UM", 6), ("Peso unit. (kg/UM)", 11),
        ("Peso total (kg)", 11), ("Material", 30), ("Medida (mm)", 52), ("Origen", 20), ("Entra MRP", 8),
        ("Proveedor principal", 26), ("Alternativa", 24), ("Operación / puesto (layout FLAMA)", 40),
        ("Norma / referencia", 32), ("Fte.", 5), ("Plano", 20), ("Observaciones", 60)]
CLAVES = ["nivel", "codigo", "desc", "cant", "um", "peso", None, "mat", "med", "ori", "mrp", "prov", "alt", "op",
          "norma", "fte", "plano", "obs"]
ANCHAS = {"desc", "med", "prov", "alt", "op", "norma", "obs"}
FUENTES = {"P": "Plano / modelo 3D (misma geometría que el plano FL_MAT / FL_REC)",
           "C": "Cálculo declarado con datos del plano, de la norma o de una fuente técnica (fórmula en Medida u "
                "Observaciones)",
           "N": "Norma IRAM o resolución (se cita el apartado; texto no transcripto por licencia)",
           "L": "Layout de planta FLAMA (FL_PI_04) cruzado con la cotización de chapa (Pacheco / Pradecon)",
           "Q": "Cotización o ficha técnica recibida del proveedor (ver 11_Validacion_MP)",
           "I": "Investigación de mercado FLAMA (planillas entregadas; ver 11_Validacion_MP)",
           "V": "Sin documento de respaldo (la fila queda en naranja con lo que falta en Observaciones)"}
# estado de la fila -> (color, significado)
COLOR_EST = {"V": (None, "Validado: especificación respaldada por plano, norma, cotización o proveedor nacional con el "
                         "producto exacto (la falta de precio no cambia el color: ver 10_Proveedores)"),
             "E": ("FFF2CC", "Estimado: valor justificado con norma o fuente técnica citada, sin medición ni cotización "
                             "propia (corregir con dato real)"),
             "A": ("F8CBAD", "A validar: falta el dato, la cotización o la confirmación del proveedor"),
             "X": ("FF8B8B", "No cumple o decisión pendiente: contradicción con la norma, con el plano o sin proveedor "
                             "nacional")}
HOJAS = dict(indice="01_Indice", dec="02_Decisiones", res="03_Resumen_Productos", mat="04_BOM_Matafuegos",
             cil="05_BOM_Cilindros", sus="06_BOM_Sustitutos", rec="07_BOM_Recargas", qui="08_Quimica_Agentes",
             n2="09_Carga_N2", prov="10_Proveedores", val="11_Validacion_MP", exp="12_Maestro_Consolidado_MP",
             fue="13_Fuentes", mer="14_Comparacion_Mercado", pla="15_Indice_Planos")


def hoja(cod):
    """Nombre de la hoja del BOM multinivel de un producto."""
    return ("BOM_" + cod)[:31]


def _ref(nombre):
    return f"'{nombre}'"


def _estilos():
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    fino = Side(style="thin", color="B0B0B0")
    return dict(
        Font=Font, Fill=PatternFill, Al=Alignment,
        borde=Border(left=fino, right=fino, top=fino, bottom=fino),
        cab=PatternFill("solid", fgColor="7F1D1D"),
        niv={0: PatternFill("solid", fgColor="E5B8B7"), 1: PatternFill("solid", fgColor="F2DCDB"),
             2: None, 3: PatternFill("solid", fgColor="F2F2F2")},
        est={k: (PatternFill("solid", fgColor=c) if c else None) for k, (c, _) in COLOR_EST.items()},
    )


def _tabla(ws, filas, r0, E, prod_col=False, outline=True):
    """Escribe la tabla multinivel desde la fila r0 y devuelve (última fila, {sub: fila del subconjunto})."""
    cols = ([("Producto", 22)] if prod_col else []) + COLS
    off = 1 if prod_col else 0
    for j, (t, w) in enumerate(cols, 1):
        c = ws.cell(r0, j, t)
        c.font = E["Font"](bold=True, color="FFFFFF")
        c.fill = E["cab"]
        c.alignment = E["Al"](wrap_text=True, vertical="center")
        c.border = E["borde"]
        ws.column_dimensions[c.column_letter].width = w
    ws.row_dimensions[r0].height = 30
    r = r0
    filas_sub, hijos, raiz = {}, {}, None
    from openpyxl.utils import get_column_letter as L
    cC, cP, cT = L(4 + off), L(6 + off), L(7 + off)
    anchas = {j + off for j, k in enumerate(CLAVES, 1) if k in ANCHAS}
    for f in filas:
        r += 1
        if prod_col:
            ws.cell(r, 1, f["_prod"])
        for j, k in enumerate(CLAVES, 1 + off):
            if k is None:
                continue
            v = f.get(k)
            if k == "desc":
                v = "    " * f["nivel"] + v
            ws.cell(r, j, v if v not in (None, "") else None)
        n = f["nivel"]
        if n == 2 and f["peso"] is not None:
            ws.cell(r, 7 + off, f"={cC}{r}*{cP}{r}")
            hijos.setdefault(f["_g"], []).append(r)
        elif n == 3 and f["peso"] is not None:
            ws.cell(r, 7 + off, f"={cC}{r}*{cP}{r}")
        elif n == 1:
            filas_sub[f["_g"]] = r
        elif n == 0:
            raiz = r
        fill = E["niv"].get(n)
        if n >= 2 and E["est"].get(f.get("est") or "V"):
            fill = E["est"][f["est"]]
        for j in range(1, len(cols) + 1):
            c = ws.cell(r, j)
            c.border = E["borde"]
            c.alignment = E["Al"](wrap_text=j in anchas, vertical="top")
            if fill:
                c.fill = fill
            if n <= 1:
                c.font = E["Font"](bold=True)
            elif n == 3:
                c.font = E["Font"](italic=True, color="555555")
        ws.cell(r, 4 + off).number_format = "General"
        ws.cell(r, 6 + off).number_format = "0.000"
        ws.cell(r, 7 + off).number_format = "0.000"
        if outline and n >= 2:
            ws.row_dimensions[r].outline_level = n - 1
    # subtotales de subconjunto y total del producto
    for g, rs in filas_sub.items():
        if g in hijos:
            ws.cell(rs, 7 + off, "=" + "+".join(f"{cT}{x}" for x in hijos[g]))
    return r, filas_sub, raiz


def _grupos(filas, prod=""):
    g = 0
    for f in filas:
        if f["nivel"] <= 1:
            g += 1
        f["_g"] = (prod, g)
        f["_prod"] = prod
    return filas


def _leyenda(ws, fila, col, E):
    """Leyenda de colores de estado en una fila."""
    ws.cell(fila, col, "Colores:").font = E["Font"](bold=True, size=9)
    for i, (k, (c, t)) in enumerate(COLOR_EST.items()):
        x = ws.cell(fila, col + 1 + 2 * i, t.split(":")[0])
        x.font = E["Font"](size=9)
        if c:
            x.fill = E["Fill"]("solid", fgColor=c)
        x.border = E["borde"]


# Peso cargado de referencia: masa total de los planos Fadesa (mismo diseño del que salen las medidas) cuando existe;
# si no, la ficha técnica de un fabricante con Sello IRAM; si no, el catálogo Fadesa 3 (repite pesos entre tablas).
REF_PESO = {
    "FL_MAT_ABC_1kg": (1.84, "Plano Fadesa «Extintor 1 kg Ø76 (válvula HZ) R1»"),
    "FL_MAT_ABC_2.5kg": (4.62, "Plano Fadesa «Extintor 2,5 kg válvula HZ R1»"),
    "FL_MAT_ABC_5kg": (8.40, "Plano Fadesa «Extintor 5 kg válvula HZ R1»"),
    "FL_MAT_ABC_10kg": (16.40, "Plano Fadesa «Extintor 10 kg HZ R1»"),
    "FL_MAT_ABC_25kg": (53.2, "Plano Fadesa «Extintor rodante 25 kg R1»"),
    "FL_MAT_ABC_50kg": (94.0, "Plano Fadesa «Extintor rodante 50 kg R1»"),
    "FL_MAT_ABC_70kg": (140.0, "Ficha técnica Georgia ABC 90 70 kg"),
    "FL_MAT_ABC_100kg": (187.6, "Plano Fadesa «Extintor rodante 100 kg R1»"),
    "FL_MAT_SALESK_6l": (9.5, "Ficha técnica Melisam acetato 6 L"),
}


def peso_ref(m):
    if m.codigo in REF_PESO:
        return REF_PESO[m.codigo]
    return (float(m.spec["Peso cargado (kg)"].replace(",", ".")),
            "Catálogo Fadesa 3 (repite pesos entre tablas: sólo orientativo)")


def _hoja_producto(wb, m, filas, E, cilindro=False):
    cod = filas[0]["codigo"]
    ws = wb.create_sheet(hoja(cod))
    ws.sheet_properties.outlinePr.summaryBelow = False
    ws.sheet_properties.tabColor = "1F4E79" if cilindro else ("7F1D1D" if m.codigo in PROPIOS else "BF8F00")
    ws["A1"] = f"FLAMA S.A. - Lista de materiales (BOM) multinivel - {cod}"
    ws["A1"].font = E["Font"](bold=True, size=14)
    ws["A2"] = filas[0]["desc"]
    ws["A2"].font = E["Font"](bold=True, size=11)
    datos = [("Plano de origen", cod + ("  (recipiente para venta suelta)" if cilindro else "  (4 láminas)")),
             ("Plano de despiece", ("FL_REC_" if cilindro else "FL_DES_") + m.codigo[7:] +
              (" hoja 3" if cilindro else " (salida/despiece/)")),
             ("Norma del producto", filas[0]["norma"]),
             ("Fabricación", filas[0]["obs"]),
             ("Peso cargado de referencia (kg)", None if cilindro else peso_ref(m)[0])]
    for i, (k, v) in enumerate(datos, 3):
        ws.cell(i, 1, k).font = E["Font"](bold=True)
        ws.cell(i, 3, v)
    r0 = 10
    last, subs, raiz = _tabla(ws, _grupos(filas), r0, E)
    from openpyxl.utils import get_column_letter as L
    fila_sub = {}
    for f in filas:
        if f["nivel"] == 1:
            fila_sub[f["sub"]] = subs[f["_g"]]
    vac = [fila_sub[s] for s in (1, 2, 3, 4) if s in fila_sub]
    car = vac + [fila_sub[s] for s in (5, 6) if s in fila_sub]
    tot = car + [fila_sub[s] for s in (7, 8) if s in fila_sub]
    ws["E3"], ws["E4"], ws["E5"] = ("Peso vacío S1-S4 (kg)", "Peso cargado S1-S6 (kg)", "Peso con soporte y embalaje (kg)")
    ws["G3"] = "=" + "+".join(f"G{x}" for x in vac) if vac else 0
    ws["G4"] = "=" + "+".join(f"G{x}" for x in car)
    ws["G5"] = "=" + "+".join(f"G{x}" for x in tot)
    ws[f"G{raiz}"] = "=G5"
    if not cilindro:
        ws["E6"] = "Desvío cargado vs referencia"
        ws["E7"] = "Referencia: " + peso_ref(m)[1]
        ws["E7"].font = E["Font"](italic=True, size=9)
        ws["G6"] = "=G4/C7-1"
        ws["G6"].number_format = "0.0%"
    for c in ("E3", "E4", "E5", "E6"):
        ws[c].font = E["Font"](bold=True)
    for c in ("G3", "G4", "G5"):
        ws[c].number_format = "0.000"
    ws["A8"] = ("Niveles: 0 producto · 1 subconjunto · 2 pieza / insumo · 3 materia prima (cursiva, no suma). Botones "
                "1-2-3 de la izquierda para plegar. Entra MRP = Sí: se compra; No: se fabrica (se explota en su "
                "materia prima) o viene dentro de un conjunto comprado. Fte.: ver 01_Indice.")
    ws["A8"].font = E["Font"](italic=True, size=9)
    _leyenda(ws, 9, 1, E)
    ws.freeze_panes = ws.cell(r0 + 1, 4)
    ws.auto_filter.ref = f"A{r0}:{L(len(COLS))}{last}"
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth = 1
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.page_setup.fitToHeight = 0
    return ws


def _plana(wb, nombre, titulo, productos, E):
    ws = wb.create_sheet(nombre)
    ws.sheet_properties.outlinePr.summaryBelow = False
    ws["A1"] = titulo
    ws["A1"].font = E["Font"](bold=True, size=12)
    _leyenda(ws, 2, 1, E)
    todas = []
    for cod, filas in productos:
        todas += _grupos([dict(f) for f in filas], cod)
    last, _, _ = _tabla(ws, todas, 4, E, prod_col=True, outline=False)
    from openpyxl.utils import get_column_letter as L
    ws.freeze_panes = "D5"
    ws.auto_filter.ref = f"A4:{L(len(COLS) + 1)}{last}"
    return ws


RUBROS = ["Materia prima", "Semielaborado comprado", "Componente comprado", "Consumible de proceso", "Servicio",
          "Carga (agente y gas)", "Identificación", "Soporte", "Embalaje", "Equipo terminado comprado",
          "Recarga y mantenimiento", "Pieza fabricada (se explota en su MP)", "Incluido en un conjunto comprado",
          "Referencia del revendido (no se compra)", "Proceso (sin compra)"]


def _rubro(f, revendido):
    n, cod, ori = f["nivel"], f["codigo"], f.get("ori") or ""
    suf = cod.split("-")[-1]
    if n == 1:
        return "Equipo terminado comprado"
    if n == 3:
        return "Materia prima"
    if revendido and f.get("mrp") == "No":
        return "Referencia del revendido (no se compra)"
    if ori.startswith("Fabricación"):
        return "Pieza fabricada (se explota en su MP)"
    if ori.startswith("Incluido"):
        return "Incluido en un conjunto comprado"
    if ori.startswith(("Proceso", "Red")):
        return "Proceso (sin compra)"
    if suf in ("C1", "C2", "C3"):
        return "Consumible de proceso"
    if suf.startswith("C4"):
        return "Servicio"
    if suf.startswith("A"):
        return "Carga (agente y gas)"
    if f.get("sub") == 6 or suf.startswith("T3"):
        return "Identificación"
    if f.get("sub") == 8:
        return "Soporte"
    if f.get("sub") == 7 or suf.startswith(("E", "T1")):
        return "Embalaje"
    if f.get("item", "").startswith(("TAPA", "MP-CU")):
        return "Semielaborado comprado"
    return "Componente comprado"


def _clave_item(f):
    """(nombre del ítem, UM, cantidad por unidad de producto) de una fila de BOM."""
    d, um = f["desc"].strip(), f["um"]
    if f["nivel"] == 3:
        if f["codigo"] == "MP-HOJA":
            return f"Chapa {d.split('Recorte de hoja ')[1]}", "kg", f["peso"] * f["cant"]
        if f["codigo"] == "MP-FLEJE":
            return d.split(" (paso")[0], "m", f["cant"]
        if f["codigo"] == "MP-CHAPA-APOYO":
            return d, "kg", f["peso"] * f["cant"]
        return d.split(" (tramo")[0], ("barra 6 m" if um == "barra" else um), f["cant"]
    if f["nivel"] == 1:
        return f"{d}: {f['_prod']}", um, f["cant"]
    if (f["codigo"].split("-")[-1].isdigit() or f["codigo"].endswith("-E1")) and f.get("med"):
        return f"{d} — {f['med']}", um, f["cant"]
    return d, um, f["cant"]


PROCESOS = [
    # (proceso, insumo, planilla / norma, inductor, entra MRP, ítem o proveedor, cálculo por unidad, estado)
    ("Soldadura MAG", "Puntas de contacto CuCrZr Ø0,9 / Ø1,2 y toberas", "Planilla MP-26",
     "minutos de arco por unidad (columna por producto, de C2)", "Sí", "ESAB / Binzel vía distribuidor", "arco", "V"),
    ("Soldadura MAG", "Alambre ER70S-6 y gas Arcal 21", "Planilla MP-23/24/25", "por unidad (filas C1 y C2 de la "
     "matriz)", "Sí", "Conarco / Air Liquide", "", "E"),
    ("Corte y amolado", "Discos de amolado y corte Ø115", "Planilla MP-27", "horas de amolado y despunte", "Sí",
     "Norton / Pferd / 3M vía distribuidor", "", "V"),
    ("Granallado", "Granalla S330 / S390", "Planilla MP-28", "por unidad (fila C3 de la matriz)", "Sí", "CyM Materiales",
     "", "E"),
    ("Granallado", "Tapones cónicos de silicona para enmascarar roscas (reutilizables)", "Planilla MP-32",
     "cuellos granallados / ciclos de vida del tapón", "Sí", "Distribuidor de enmascarado", "", "V"),
    ("Pintura (tercerizada)", "Desengrasante alcalino y fosfatizante", "Planilla MP-29/30",
     "los aporta el pintor mientras la pintura sea tercerizada", "No", "Henkel / Chemetall", "", "V"),
    ("Prueba hidráulica", "Agua de red (circuito recirculado)", "Esquema banco PH", "volumen del recipiente por "
     "ensayo (dm³ = L, columna por producto)", "No", "Red", "ph", "V"),
    ("Carga y presurización", "Nitrógeno seco y polvo ABC", "Planilla MP-34 · Sello IRAM 3569",
     "por unidad (filas A1 y A2 de la matriz)", "Sí", "Air Liquide / DEMSA", "", "V"),
    ("Carga, presurización y recarga", "Solución detectora de fugas", "IRAM 3517-2:2020 9.4.10 (ensayo de pérdidas)",
     "unidades presurizadas y recargadas", "Sí", "A relevar", "", "A"),
    ("Recarga", "Esmalte rojo de retoque", "Planilla MP-65", "equipos recargados con daño de pintura", "Sí",
     "Sinteplast / Tersuave", "", "V"),
    ("Recarga", "Lubricante para ejes y cojinetes de ruedas de carros", "IRAM 3517-2:2020 anexo (lista de revisión)",
     "rodantes en mantenimiento", "Sí", "A relevar", "", "A"),
    ("Embalaje", "Caja, cinta, film, pallet, esquineros, separadores y etiquetas", "Planilla MP-59 a 64",
     "por unidad (filas E de la matriz)", "Sí", "Maxipack / MV Embalajes / IndusPallets", "", "V"),
]


def _maestro(wb, term, cil, E):
    """12_Maestro_Consolidado_MP: todo lo que lleva cada producto, en una sola matriz, más los insumos de proceso."""
    from . import sustituto as SU
    from . import recipientes as RC
    from openpyxl.utils import get_column_letter as L
    ws = wb.create_sheet(HOJAS["exp"])
    columnas, datos = [], {}       # columnas: (código, grupo); datos[clave][código] = cantidad
    meta = {}                      # clave -> dict(rubro, mrp, prov, proceso, est)

    def cargar(cod, grupo, filas, revendido=False):
        columnas.append((cod, grupo))
        for f in filas:
            if f["nivel"] == 0 or (f["nivel"] == 1 and not (f["codigo"].endswith("-S0") or f.get("_sus"))):
                continue
            f = dict(f, _prod=cod)
            if f["cant"] in (None, 0, "-"):
                continue
            nom, um, q = _clave_item(f)
            mrp = f.get("mrp") or "No"
            k = (nom, um, mrp)
            d = meta.setdefault(k, dict(rubro=_rubro(f, revendido), prov=f.get("prov") or "", proc=f.get("op") or "",
                                        est=f.get("est") or "V"))
            if NIV_EST.get(f.get("est") or "V", 0) > NIV_EST[d["est"]]:
                d["est"] = f["est"]
            datos.setdefault(k, {})
            datos[k][cod] = datos[k].get(cod, 0) + q

    for m, f in term:
        cargar(m.codigo, "Matafuego FL_MAT", f, revendido=m.codigo not in PROPIOS)
    for m, f in cil:
        cargar(RC.codigo_rec(m), "Cilindro FL_REC", f)
    for m in MODELOS:
        filas = _sustitutos(m)
        for x in filas:
            if x["nivel"] == 1 and x["codigo"] == m.codigo:
                x["_sus"] = True
                x["desc"] = "Extintor base del stock"
                x["um"] = "u"
        cargar(SU.codigo(m), "Sustituto FL_SUS", filas)
    # recargas: un kit por modelo y caso
    kits = {}
    for f in recargas():
        m = next(x for x in MODELOS if x.codigo == f[0])
        letra = f[2][0] if f[2][1:3] == " -" else "I"
        kits.setdefault((m.codigo, letra), []).append(f)
    for (mc, letra), filas in kits.items():
        m = next(x for x in MODELOS if x.codigo == mc)
        cod = f"RK-{P.codigo_pieza(m, 0)[:-3]}-{letra}"
        rows = []
        for f in filas:
            if not isinstance(f[4], (int, float)):
                continue
            mrp, item = _item_recarga(m, str(f[3]))
            prov = PV.asignar(item)[0] if item and mrp == "Sí" else ""
            est = "E" if "R:" in str(f[6]) else "V"
            rows.append(dict(nivel=2, codigo=cod + "-R", desc=str(f[3]), um=f[5], cant=f[4], mrp=mrp, prov=prov,
                             op="Recarga", est=est, ori="Proceso" if mrp == "No" else "Compra", sub=0))
        columnas.append((cod, "Kit de recarga RK"))
        for r_ in rows:
            nom, um = r_["desc"], r_["um"]
            k = (nom, um, r_["mrp"])
            meta.setdefault(k, dict(rubro="Recarga y mantenimiento" if r_["mrp"] == "Sí" else "Proceso (sin compra)",
                                    prov=r_["prov"], proc="Recarga", est=r_["est"]))
            datos.setdefault(k, {})
            datos[k][cod] = datos[k].get(cod, 0) + r_["cant"]
    # ---- escritura
    ws["A1"] = ("Maestro consolidado de materias primas e insumos: todo lo que lleva cada producto (matafuegos, "
                "cilindros, sustitutos y kits de recarga), por unidad")
    ws["A1"].font = E["Font"](bold=True, size=12)
    ws["A2"] = ("Entra MRP = Sí: se compra. No: se fabrica (su materia prima está en las filas de Materia prima), viene "
                "dentro de un conjunto comprado, es referencia del revendido o es un proceso. Filtrar por Rubro o por "
                "Entra MRP. Al final: insumos de cada proceso que no van por unidad.")
    _leyenda(ws, 3, 1, E)
    fijas = ["Rubro", "Ítem", "UM", "Entra MRP", "Proveedor principal", "Proceso / operación"]
    anchos = [24, 60, 9, 8, 28, 30]
    r0 = 6
    for j, (cod, grupo) in enumerate(columnas, len(fijas) + 1):
        c = ws.cell(r0 - 1, j, grupo)
        c.font = E["Font"](bold=True, size=8)
        c.alignment = E["Al"](text_rotation=90, vertical="bottom")
    ws.row_dimensions[r0 - 1].height = 95
    cab = fijas + [c.replace("FL_MAT_", "MAT ").replace("FL_REC_", "REC ").replace("FL_SUS_", "SUS ")
                   for c, _ in columnas]
    for j, t in enumerate(cab, 1):
        c = ws.cell(r0, j, t)
        c.font = E["Font"](bold=True, color="FFFFFF")
        c.fill = E["cab"]
        c.alignment = E["Al"](wrap_text=True, vertical="center", text_rotation=0 if j <= len(fijas) else 90)
        ws.column_dimensions[L(j)].width = anchos[j - 1] if j <= len(fijas) else 7
    ws.row_dimensions[r0].height = 110
    orden = sorted(datos, key=lambda k: (RUBROS.index(meta[k]["rubro"]), k[0]))
    r = r0
    for k in orden:
        r += 1
        d = meta[k]
        for j, v in enumerate([d["rubro"], k[0], k[1], k[2], d["prov"] or None, d["proc"] or None], 1):
            ws.cell(r, j, v)
        for j, (cod, _) in enumerate(columnas, len(fijas) + 1):
            v = datos[k].get(cod)
            if v:
                ws.cell(r, j, round(v, 4)).number_format = "General"
        fill = E["est"].get(d["est"])
        if fill:
            for j in range(1, len(fijas) + 1):
                ws.cell(r, j).fill = fill
        if k[2] == "No":
            for j in range(1, len(cab) + 1):
                ws.cell(r, j).font = E["Font"](color="808080")
    ws.freeze_panes = ws.cell(r0 + 1, len(fijas) + 1)
    ws.auto_filter.ref = f"A{r0}:{L(len(cab))}{r}"
    # ---- insumos de proceso
    r += 3
    ws.cell(r, 1, "Insumos de cada proceso (se planifican por su inductor; los que tienen dato por unidad lo muestran "
                  "en la columna del producto)").font = E["Font"](bold=True, size=12)
    r += 1
    for j, t in enumerate(["Proceso", "Insumo", "Planilla / norma", "Entra MRP", "Proveedor", "Inductor de consumo"],
                          1):
        c = ws.cell(r, j, t)
        c.font = E["Font"](bold=True, color="FFFFFF")
        c.fill = E["cab"]
    arco = {m.codigo: next((round(x["cant"] / CAUDAL_GAS, 2) for x in f if x["codigo"].endswith("-C2") and x["cant"]),
                           None) for m, f in term}
    arco.update({RC.codigo_rec(m): next((round(x["cant"] / CAUDAL_GAS, 2) for x in f if x["codigo"].endswith("-C2")
                                         and x["cant"]), None) for m, f in cil})
    vol = {m.codigo: m.geo["vol_dm3"] for m, _ in term if m.codigo in PROPIOS}
    vol.update({RC.codigo_rec(m): m.geo["vol_dm3"] for m, _ in cil})
    for proc, ins, ref, ind, mrp, prov, calc, est in PROCESOS:
        r += 1
        for j, v in enumerate([proc, ins, ref, mrp, prov, ind], 1):
            c = ws.cell(r, j, v)
            c.alignment = E["Al"](wrap_text=True, vertical="top")
            if E["est"].get(est):
                c.fill = E["est"][est]
        dato = arco if calc == "arco" else vol if calc == "ph" else {}
        for j, (cod, _) in enumerate(columnas, len(fijas) + 1):
            if dato.get(cod):
                ws.cell(r, j, dato[cod])
    return ws


def _resumen(wb, productos, E):
    ws = wb.create_sheet(HOJAS["res"])
    cab = ["Plano", "Producto", "Familia", "Fabricación", "Norma IRAM", "Agente", "Carga", "UM", "Gas impulsor",
           "Gas (kg)", "Peso vacío S1-S4 (kg)", "Peso cargado (kg)", "Peso de referencia (kg)", "Desvío", "Piezas del plano",
           "Ítems BOM", "Ítems que entran en MRP", "Recipiente suelto", "Hoja BOM",
           "Tara de referencia (kg) = referencia - carga - gas", "Desvío de tara (modelo vs referencia)",
           "Fuente del peso de referencia"]
    _cab(ws, 1, cab, [18, 40, 9, 16, 11, 40, 7, 5, 13, 8, 10, 10, 10, 8, 8, 8, 9, 18, 8, 14, 12, 46], E, 32)
    for i, (m, filas) in enumerate(productos, 2):
        ag, q, um, n_ag, gas, m_gas, nm3, libre = carga(m)
        n_p = sum(1 for f in filas if f["nivel"] == 2 and f["codigo"][-2:].isdigit())
        sh = _ref(hoja(m.codigo))
        vals = [m.codigo, m.nombre, m.familia, "Propia" if m.codigo in PROPIOS else "Revendido",
                m.spec["Norma IRAM extintor"], ag, q, um, gas, round(m_gas, 4) or None,
                f"={sh}!G3", f"={sh}!G4", peso_ref(m)[0],
                f"=L{i}/M{i}-1", n_p, len(filas), sum(1 for f in filas if f.get("mrp") == "Sí"),
                m.codigo.replace("FL_MAT_", "FL_REC_") if m.codigo in PROPIOS else "-", None]
        for j, v in enumerate(vals, 1):
            ws.cell(i, j, v).border = E["borde"]
        _, obj, _ = tolerancia(m)
        kg_carga = obj if um == "kg" else q * (RHO_AGENTE.get(_agente(m), 1.0) if um == "L" else 1.0)
        ws.cell(i, 7, round(obj, 3))
        ws.cell(i, 20, f"=M{i}-{round(kg_carga, 3)}-J{i}" if m_gas else f"=M{i}-{round(kg_carga, 3)}")
        ws.cell(i, 21, f"=(L{i}-{round(kg_carga, 3)}-J{i})/T{i}-1" if m_gas else f"=(L{i}-{round(kg_carga, 3)})/T{i}-1")
        ws.cell(i, 20).number_format = "0.00"
        ws.cell(i, 21).number_format = "0.0%"
        ws.cell(i, 22, peso_ref(m)[1])
        ws.cell(i, 19).hyperlink = f"#{sh}!A1"
        ws.cell(i, 19, "ir »").font = E["Font"](color="0563C1", underline="single")
        for j in (11, 12):
            ws.cell(i, j).number_format = "0.00"
        ws.cell(i, 14).number_format = "0.0%"
    ws.freeze_panes = "C2"
    ws.auto_filter.ref = f"A1:V{1 + len(productos)}"
    return ws


def _cab(ws, fila, cab, anchos, E, alto=45):
    for j, (t, w) in enumerate(zip(cab, anchos), 1):
        c = ws.cell(fila, j, t)
        c.font = E["Font"](bold=True, color="FFFFFF")
        c.fill = E["cab"]
        c.alignment = E["Al"](wrap_text=True, vertical="center")
        ws.column_dimensions[c.column_letter].width = w
    ws.row_dimensions[fila].height = alto


def _quimica(wb, E):
    """Hoja de entrada: química y densidad de cada agente. Las celdas de entrada alimentan 09_Carga_N2."""
    ws = wb.create_sheet(HOJAS["qui"])
    ws["A1"] = "Química de los agentes extintores - datos de entrada (celdas celestes)"
    ws["A1"].font = E["Font"](bold=True, size=12)
    ws["A2"] = ("Si cambia la formulación (% de MAP, tipo de bicarbonato, concentración del acetato o del AFFF) cambia la "
                "densidad, y con ella el volumen que ocupa la carga, el volumen libre, el N₂ y si el recipiente alcanza. "
                "Cambie la densidad acá y mire 09_Carga_N2.")
    cab = ["Clave", "Agente", "Composición", "Mecanismo de extinción", "¿Saponifica?", "Gas impulsor",
           "ρ aparente mín (kg/dm³)", "ρ aparente típica (kg/dm³)", "ρ aparente máx (kg/dm³)",
           "Masa molar gas (kg/mol)", "Fuente ρ aparente", "ρ empacada mín (kg/dm³)", "Fuente ρ empacada"]
    _cab(ws, 4, cab, [7, 34, 40, 50, 34, 14, 9, 9, 9, 10, 50, 10, 50], E)
    entrada = E["Fill"]("solid", fgColor="DDEBF7")
    filas = {}
    for i, (k, v) in enumerate(AGENTES.items(), 5):
        nom, comp, mec, sap, gas, r0, r1, r2, fte = v
        emp = RHO_EMPACADA.get(k, r1)
        f_emp = FUENTE_EMPACADA if k in RHO_EMPACADA else ("Líquido: densidad del agente" if k in ("HCFC", "AGUA", "AFFF",
                                                            "K") else "Revendido: lo carga el fabricante (se usa la típica)")
        for j, x in enumerate([k, nom, comp, mec, sap, gas, r0, r1, r2, MOLAR[gas], fte, emp, f_emp], 1):
            c = ws.cell(i, j, x)
            c.border = E["borde"]
            c.alignment = E["Al"](wrap_text=True, vertical="top")
            if j in (7, 8, 9, 10, 12):
                c.fill = entrada
        if k in RHO_EMPACADA:
            ws.cell(i, 12).fill = E["est"]["E"]
        ws.row_dimensions[i].height = 60
        filas[k] = i
    r = 5 + len(AGENTES) + 1
    ws.cell(r, 1, "Criterio de aceptación del volumen libre: descarga continua ≥ 85 % de la masa de agente en el "
                  "ensayo de tipo (IRAM 3523 4.9.1). Reemplaza al antiguo «volumen libre mínimo» supuesto.").font = \
        E["Font"](bold=True)
    # grado del polvo ABC: composición y potencial certificado (licencias IRAM 3523 + DEMSA)
    r += 2
    ws.cell(r, 1, "Grado del polvo ABC: la masa la fija la norma; el % de MAP fija el potencial A (licencias IRAM "
                  "3523 Drago y Georgia/Fadesa)").font = E["Font"](bold=True)
    r += 1
    _cab(ws, r, ["Grado", "MAP nominal %", "Banda IRAM %", "Relleno", "1 kg", "2,5 kg", "5 kg", "10 kg", "Hoja técnica"],
         [7, 34, 40, 50, 34, 14, 9, 9, 9], E, 20)
    for g, d in AG.GRADOS_ABC.items():
        r += 1
        pot = [AG.POTENCIAL_ABC.get((g, c), "sin licencia relevada") for c in ("1 kg", "2,5 kg", "5 kg", "10 kg")]
        for j, x in enumerate([g, d["map"], f"{_f(d['banda'][0], 2)} - {_f(d['banda'][1], 2)}",
                               f"{AG.RELLENO_ABC} + {_f(AG.ADITIVOS_ABC, 0)} % aditivos"] + pot + [d["hoja"]], 1):
            ws.cell(r, j, x).border = E["borde"]
    r += 2
    ws.cell(r, 1, "Agente y grado adoptado por modelo (DEMSA principal; Polvex / Sancibrao alternativa)").font = \
        E["Font"](bold=True)
    r += 1
    _cab(ws, r, ["Plano", "Agente / grado", "Norma agente", "Gas", "Potencial", "Alternativa", "", "", ""],
         [7, 34, 40, 50, 34, 14, 9, 9, 9], E, 20)
    for m in MODELOS:
        a_ = AG.agente(m)
        r += 1
        for j, x in enumerate([m.codigo, a_["grado"], a_["norma"], a_["gas"], a_["potencial"],
                               a_.get("alternativa", "")], 1):
            ws.cell(r, j, x).border = E["borde"]
    return filas


def _carga_n2(wb, E, fq):
    ws = wb.create_sheet(HOJAS["n2"])
    ws["A1"] = ("Carga de agente y gas impulsor por extintor (fórmulas ligadas a 08_Quimica_Agentes) - la capacidad es la "
                "MASA de agente (IRAM 3523 2.2); el gas es la masa que da Ps a 20 °C en el volumen libre")
    ws["A1"].font = E["Font"](bold=True, size=12)
    notas = ["Carga: nominal con la tolerancia de IRAM 3517-2:2020 tabla 3 / IRAM 3523 tabla II; si la tolerancia es "
             "sólo positiva se carga al centro de la banda.",
             "Volumen que ocupa el polvo en servicio = masa / densidad EMPACADA (asentada después del vibrado de la "
             "carga). ABC: ≥ 1,10 kg/dm³ (NOM-104-STPS-2001; IRAM 3569 no la fija) - valor ESTIMADO (amarillo): exigirlo "
             "en la OC y confirmar con descarga ≥ 85 % (IRAM 3523 4.9.1).",
             "Llenado: con la densidad aparente mínima (polvo suelto) se controla si el polvo entra sin vibrar; si no, "
             "la carga T01 debe vibrar el recipiente.",
             "Gas: m = (Ps + 0,101 MPa) × V libre / (8,314 × 293,15 K) × M. N₂ seco en polvos, argón en HCFC, aire "
             "comprimido en agua, AFFF y acetato (IRAM 3517-2 tabla 2)."]
    for i, n in enumerate(notas, 2):
        ws.cell(i, 1, "• " + n)
    cab = ["Plano", "Clave agente", "Carga objetivo", "UM", "Tolerancia", "V recipiente (dm³)", "Ps (MPa)", "Gas",
           "ρ aparente mín (suelta)", "ρ empacada mín (asentada)", "V agente asentado (dm³)", "V libre (dm³)",
           "V libre (%)", "Gas impulsor (g)", "V agente suelto con ρ aparente mín (dm³)", "Control", "Observaciones"]
    _cab(ws, 7, cab, [20, 7, 9, 5, 11, 9, 7, 13, 9, 9, 10, 9, 8, 9, 12, 18, 60], E)
    qn = _ref(HOJAS["qui"])
    n0 = 8
    for i, m in enumerate(MODELOS, n0):
        ag = _agente(m)
        _, q, um, _, gas, *_ = carga(m)
        tol, obj, _ = tolerancia(m)
        V = m.geo["vol_dm3"]
        for j, x in enumerate([m.codigo, ag, round(obj, 3), um, tol, V, _ps(m), gas], 1):
            ws.cell(i, j, x)
        if ag == "CO2":
            ws.cell(i, 8, "- (autopresurizado)")
            ws.cell(i, 16, "OK")
            ws.cell(i, 17, f"Grado de llenado {_f(q / V, 3)} kg/dm³ (máx. 0,75 kg/dm³, IRAM 2533 / ADR P200)")
        else:
            f = fq[ag]
            ws.cell(i, 9, f"={qn}!$G${f}")
            ws.cell(i, 10, f"={qn}!$L${f}")
            Mm = f"{qn}!$J${f}"
            if um == "kg":
                ws.cell(i, 11, f"=C{i}/J{i}")
                ws.cell(i, 15, f"=C{i}/I{i}")
            else:
                ws.cell(i, 11, f"=C{i}")
                ws.cell(i, 15, f"=C{i}")
            ws.cell(i, 12, f"=F{i}-K{i}")
            ws.cell(i, 13, f"=L{i}/F{i}")
            ws.cell(i, 14, f"=(G{i}+0.101)*1000000*MAX(0,L{i})/1000/(8.314*293.15)*{Mm}*1000")
            ws.cell(i, 16, f'=IF(L{i}<0,"NO ENTRA",IF(O{i}>F{i},"VIBRAR EN EL LLENADO","OK"))')
            obs = []
            if ag in RHO_EMPACADA:
                obs.append("ρ empacada estimada (NOM-104): confirmar con descarga ≥ 85 % en el ensayo de tipo")
                for j in (10, 11, 12, 13, 14):
                    ws.cell(i, j).fill = E["est"]["E"]
            elif m.codigo not in PROPIOS:
                obs.append("Revendido: carga y gas del fabricante (referencia)")
            if m.codigo == "FL_MAT_CLASED_9l":
                obs.append("Capacidad en dm³ en el catálogo; IRAM 3523 la define en kg: definir 9 o 10 kg")
            ws.cell(i, 17, " · ".join(obs) or None)
        for j in range(1, 18):
            ws.cell(i, j).border = E["borde"]
        for j in (9, 10, 11, 12, 14, 15):
            ws.cell(i, j).number_format = "0.00"
        ws.cell(i, 13).number_format = "0.0%"
    from openpyxl.formatting.rule import CellIsRule
    rng = f"P{n0}:P{n0 - 1 + len(MODELOS)}"
    ws.conditional_formatting.add(rng, CellIsRule(operator="equal", formula=['"NO ENTRA"'],
                                                  fill=E["Fill"]("solid", fgColor=COLOR_EST["X"][0])))
    ws.conditional_formatting.add(rng, CellIsRule(operator="equal", formula=['"VIBRAR EN EL LLENADO"'],
                                                  fill=E["Fill"]("solid", fgColor=COLOR_EST["A"][0])))
    ws.freeze_panes = f"C{n0}"
    return ws


MERCADO = [
    # planos Fadesa (masa total indicada en el rótulo): mismo diseño del que salen las medidas de FLAMA
    ("FL_MAT_ABC_1kg", "Plano Fadesa extintor 1 kg Ø76 válvula HZ R1", 1.84, "Plano Fadesa (masa total)"),
    ("FL_MAT_ABC_2.5kg", "Plano Fadesa extintor 2,5 kg válvula HZ R1", 4.62, "Plano Fadesa (masa total)"),
    ("FL_MAT_ABC_5kg", "Plano Fadesa extintor 5 kg válvula HZ R1", 8.40, "Plano Fadesa (masa total)"),
    ("FL_MAT_ABC_10kg", "Plano Fadesa extintor 10 kg HZ R1", 16.40, "Plano Fadesa (masa total)"),
    ("FL_MAT_ABC_25kg", "Plano Fadesa extintor rodante 25 kg R1", 53.2, "Plano Fadesa (masa total)"),
    ("FL_MAT_ABC_50kg", "Plano Fadesa extintor rodante 50 kg R1", 94.0, "Plano Fadesa (masa total)"),
    ("FL_MAT_ABC_100kg", "Plano Fadesa extintor rodante 100 kg R1", 187.6, "Plano Fadesa (masa total)"),
    # (plano, referencia, peso cargado kg, fuente) - fabricantes argentinos con Sello IRAM
    ("FL_MAT_ABC_1kg", "Georgia ABC 60 1 kg Ø3\" (330 × 76)", 1.82, "Ficha técnica Georgia"),
    ("FL_MAT_ABC_1kg", "Fadesa 1 kg Ø3 (340 × 92)", 1.90, "Catálogo Fadesa pág. 4"),
    ("FL_MAT_ABC_2.5kg", "Georgia ABC 60 2,5 kg (380 × 230 × 135)", 5.20, "Ficha técnica Georgia"),
    ("FL_MAT_ABC_2.5kg", "Melisam ABC 2,5 kg (435 × 217 × 125)", 5.10, "Ficha técnica Melisam"),
    ("FL_MAT_ABC_5kg", "Georgia ABC 90 5 kg (480 × 240 × 175)", 8.90, "Ficha técnica Georgia"),
    ("FL_MAT_ABC_5kg", "Melisam ABC 5 kg (466 × 245 × 159)", 8.45, "Ficha técnica Melisam"),
    ("FL_MAT_ABC_10kg", "Georgia ABC 90 10 kg (690 × 250 × 175)", 16.30, "Ficha técnica Georgia"),
    ("FL_MAT_ABC_10kg", "Melisam ABC 10 kg (630 × 255 × 179)", 15.50, "Ficha técnica Melisam"),
    ("FL_MAT_ABC_25kg", "Georgia ABC 90 25 kg", 55.0, "Ficha técnica Georgia"),
    ("FL_MAT_ABC_50kg", "Georgia ABC 90 50 kg", 100.0, "Ficha técnica Georgia"),
    ("FL_MAT_ABC_70kg", "Georgia ABC 90 70 kg", 140.0, "Ficha técnica Georgia"),
    ("FL_MAT_ABC_100kg", "Georgia ABC 90 100 kg", 185.0, "Ficha técnica Georgia"),
    ("FL_MAT_SALESK_6l", "Melisam acetato 6 L inox (450 × 235 × 179)", 9.50, "Ficha técnica Melisam"),
    ("FL_MAT_SALESK_6l", "Georgia/Fadesa acetato 6 L (dato inconsistente con 1,30 g/ml)", 8.25,
     "Ficha Georgia / catálogo Fadesa"),
]
DUPLICADOS = ("En el catálogo de referencia el peso cargado de HCFC, HFC 236fa, BC y clase D es idéntico al de ABC "
              "(1,90 / 4,60 / 8,50 / 16,50 kg) y el de agua pulverizada 10 dm³ es igual al de acetato 10 dm³ (13,00 kg): "
              "son valores repetidos entre tablas, no pesadas. Un HCFC 5 kg (densidad 1,48) no puede pesar lo mismo que un "
              "ABC 5 kg en el mismo recipiente salvo por casualidad. Por eso el desvío contra catálogo no puede "
              "exigirse en 0: sirve como orden de magnitud y se valida con el rango de mercado.")


FUENTES_DOC = [
    # (id, documento, tipo, confianza, datos que aporta)
    ("N1", "IRAM 3517-2:2020", "Norma IRAM (licencia)", "1 - manda",
     "Tabla 2 gas impulsor; tabla 3 tolerancia de carga; 9.4.13 precinto; 9.9.1 agentes; 4.4.1 recuperación"),
    ("N2", "IRAM 3523 (polvo bajo presión manuales)", "Norma IRAM", "1 - manda",
     "2.2 capacidad = masa de polvo; 2.3 Ps a 20 °C; 3.10 N₂ seco; 4.6 tabla II tolerancia; 4.7 Ps < 1,7 MPa"),
    ("N3", "IRAM 3569:1996 (polvos ABC)", "Norma IRAM", "1 - manda",
     "No fija el % de MAP: composición declarada por el fabricante del polvo (± 5 % / ± 10 % relativo) ligada al "
     "polvo con que se calificó el potencial; color grisáceo; humedad ≤ 0,25; higroscopicidad ≤ 3"),
    ("N4", "IRAM 3550:1981 (polvo sobre ruedas)", "Norma IRAM", "1 - manda",
     "3.2 recipiente; 4.1.3 espesor (fórmula y mínimos 2,9 / 4,5 mm); 4.1.4-4.1.6 estanquidad y expansión; 4.5 "
     "niebla salina 240 h"),
    ("N5", "IRAM 3566 / 3697 / 3515 / 3526-1 (normas de agente de los revendidos)", "Norma IRAM", "1 - no "
     "necesarias", "Los revendidos llegan con el agente cargado por el fabricante certificado"),
    ("L1", "Licencia IRAM 3523 Drago/Norbco (Luis Pasquinelli e Hijos SA), anexo I 2008", "Certificado IRAM",
     "2", "Potencial por grado: 1 kg DEM-60 1A-5B; 5 kg DEM-60 6A-40B / DEM-90 10A-40B; 10 kg DEM-60 6A-60B / "
     "DEM-90 10A-60B"),
    ("M0", "Relevamiento fotográfico de equipos instalados y línea de etiquetado (2026): Georgia, Melisam, Fadesa, "
     "Horizonte, De León, Maxiseguridad; recargadores Suyai y Firegram", "Mercado (observación directa)", "3",
     "Diagramación de etiqueta (panel 108° + alas de datos y mantenimiento), textos de instrucciones, estampilla IRAM "
     "(n° vertical, guilloche rosa, QR), oblea PBA (anillo, n°, próxima revisión), tarjeta AGC autoadhesiva con QR, "
     "etiqueta GS1 de serie, faja de garantía, precinto de color, alternativa BV «Modelo aprobado»"),
    ("L2", "Licencia IRAM 3694 Drago y Georgia/Fadesa", "Certificado IRAM", "2",
     "Agente clase K certificado: DEMSA KITCHEN (DEM S.A.) o Cookingwater (Quimex); 6 y 10 L; 1A-K"),
    ("L3", "Licencia IRAM 3527 Drago 10 L", "Certificado IRAM", "2", "AFFF marca DEM S.A.; recipiente aluminio; 3A-10B"),
    ("A1", "DEMSA ABC 40 / 55 / 55 Premium / 90 - hojas técnicas", "Fabricante argentino del agente (Sello IRAM "
     "3569, BVQI)", "2", "MAP 40 / 55 (55,9-64,3 Premium) / 90 %; granulometría, repelencia ≥ 90-97, humedad ≤ 0,25"),
    ("A2", "DEMSA hoja de seguridad ABC", "Fabricante argentino", "2",
     "MAP 40-90 %, sulfato de amonio 5-55 %; densidad aparente > 0,85; pH 6-7,5"),
    ("A3", "DEMSA catálogo", "Fabricante argentino", "2",
     "Especificación IRAM por grado: ABC 55 52,25-57,75 %; ABC 90 85,5-94,5 %; BC 85,5-94,5 %; AFFF 3 % 1,025"),
    ("A4", "DEMSA BC STD / Púrpura K (IRAM 3566), clase D, Kitchen (IRAM 3697), AFFF 203 MN (IRAM 3515)",
     "Fabricante argentino", "2", "NaHCO₃ ≥ 85,5 %; KHCO₃ 92 ± 5 %; NaCl > 90 %; Kitchen 1,300 g/ml pH 8,5"),
    ("F1", "Georgia fichas técnicas ABC 60 (1; 2,5 kg), ABC 90 (5 a 100 kg), clase D, acetato", "Fabricante "
     "argentino del extintor", "3", "Pesos, medidas, potencial, gas (N₂ seco)"),
    ("F2", "Melisam fichas ABC, HFC 236fa, acetato", "Fabricante argentino del extintor", "3",
     "Pesos y medidas; acetato 6 L 9,5 kg (coherente con 1,30 g/ml)"),
    ("C1", "Catálogo Fadesa 3", "Catálogo comercial", "4 - pesos repetidos entre tablas", "Dimensiones y Ps"),
    ("X1", "HDS internacionales (Buckeye, Amerex, Badger, Brooks, Halotron, Met-L-X)", "HDS", "5 - respaldo",
     "Química y mecanismo; sus valores no son especificación"),
]


def _fuentes(wb, E):
    ws = wb.create_sheet(HOJAS["fue"])
    ws["A1"] = ("Fuentes y jerarquía: 1 norma IRAM > 2 certificado IRAM y ficha del fabricante certificado local > "
                "3 catálogo > 4 HDS internacional (las HDS aclaran que sus valores NO son especificación del producto)")
    ws["A1"].font = E["Font"](bold=True, size=12)
    _cab(ws, 3, ["Id", "Documento", "Tipo", "Confianza", "Datos que aporta"], [6, 52, 26, 22, 90], E, 20)
    extra = [("T1", "Air Liquide (ES) / Ingemecánica - parámetros MAG", "Fuente técnica", "4",
              "Caudal de gas 12-16 L/min para alambre 0,9-1,2 mm"),
             ("T2", "ESAB - rendimiento de deposición", "Fuente técnica", "4",
              "Alambre macizo MAG: 90-97 % del alambre queda depositado"),
             ("T3", "The Fabricator - «Los aspectos básicos del granallado por turbina»", "Fuente técnica", "4",
              "Consumo de granalla por turbina ≈ HP / 2 lb/h"),
             ("T4", "NOM-104-STPS-2001 (México) - polvo químico seco ABC", "Norma extranjera de referencia", "4",
              "Densidad aparente ≥ 0,82 y empacada ≥ 1,10 g/cm³ (IRAM 3569 no fija densidad)"),
             ("T5", "IRAM 3525:1983 3.2.1 y 3.2.2 (agua bajo presión)", "Norma IRAM", "1 - manda",
              "Recipiente inoxidable IRAM 30 304 e ≥ 0,63; ≤ 1 costura longitudinal y ≤ 2 transversales por proceso "
              "automático (arco sumergido, resistencia, atmósfera inerte o brazing): TIG con Ar puro = atmósfera inerte"),
             ("T6", "Webs y registros de los proveedores (Ruedar, Escanort, Gockel, Yukon, Iglesias, Astuprint, etc.)", "Mercado", "3",
              "Producto exacto y domicilio; ver 10_Proveedores")]
    for i, f in enumerate(FUENTES_DOC + extra, 4):
        for j, x in enumerate(f, 1):
            c = ws.cell(i, j, x)
            c.border = E["borde"]
            c.alignment = E["Al"](wrap_text=True, vertical="top")
    return ws


COLOR_VAL = {"VALIDADA": "C6EFCE", "VALIDADA CON CONDICIÓN": "E2EFDA", "ESTIMADA": COLOR_EST["E"][0],
             "A VALIDAR": COLOR_EST["A"][0], "NO CUMPLE / A DEFINIR": COLOR_EST["X"][0]}


def _validacion(wb, E):
    """Cada materia prima / componente comprado con su respaldo documental y estado."""
    from . import validacion as VA
    ws = wb.create_sheet(HOJAS["val"])
    ws["A1"] = "Validación documental de materias primas, consumibles y componentes"
    ws["A1"].font = E["Font"](bold=True, size=12)
    _cab(ws, 3, ["Rubro", "Ítem", "Especificación adoptada en el BOM", "Requisito normativo", "Respaldo (ver tabla "
                 "de documentos)", "Estado", "Acción para cerrar"], [13, 26, 46, 40, 30, 20, 70], E, 32)
    r = 4
    for f in VA.VALIDACION:
        for j, x in enumerate(f, 1):
            c = ws.cell(r, j, x)
            c.border = E["borde"]
            c.alignment = E["Al"](wrap_text=True, vertical="top")
            if j == 6:
                c.fill = E["Fill"]("solid", fgColor=COLOR_VAL[x])
        r += 1
    r += 1
    ws.cell(r, 1, "Documentos citados").font = E["Font"](bold=True)
    r += 1
    _cab(ws, r, ["Id", "Documento", "Qué respalda"], [13, 26, 46], E, 20)
    for k, (doc, dato) in VA.DOCS.items():
        r += 1
        for j, x in enumerate((k, doc, dato), 1):
            c = ws.cell(r, j, x)
            c.border = E["borde"]
            c.alignment = E["Al"](wrap_text=True, vertical="top")
    return ws


def _mercado(wb, E, term):
    ws = wb.create_sheet(HOJAS["mer"])
    ws["A1"] = "Comparación con el mercado: peso cargado real de otros fabricantes"
    ws["A1"].font = E["Font"](bold=True, size=12)
    ws["A2"] = DUPLICADOS
    ws["A2"].alignment = E["Al"](wrap_text=True, vertical="top")
    ws.merge_cells("A2:F2")
    ws.row_dimensions[2].height = 60
    _cab(ws, 4, ["Plano", "Referencia", "Peso cargado (kg)", "Fuente", "FLAMA modelo (kg)", "Diferencia"],
         [22, 34, 12, 44, 14, 11], E, 30)
    for i, (cod, ref, kg, fte) in enumerate(MERCADO, 5):
        sh = _ref(hoja(cod))
        for j, x in enumerate([cod, ref, kg, fte, f"={sh}!G4", f"=E{i}/C{i}-1"], 1):
            ws.cell(i, j, x).border = E["borde"]
        ws.cell(i, 5).number_format = "0.00"
        ws.cell(i, 6).number_format = "0.0%"
    return ws


ITEM_AGENTE_REC = {"ABC": "POLVO-ABC", "BC": "REC-BC", "D": "REC-D", "HCFC": "REC-HCFC", "CO2": "REC-CO2",
                   "AFFF": "REC-AFFF", "K": "REC-K"}


def _item_recarga(m, texto):
    """(Entra MRP, ítem de compra) de una fila de recarga."""
    t = texto
    if "recuperado" in t or t.startswith(("Grabado", "Si hubo PH")):
        return "No", ""
    pre = [("Precinto", "PRECINTO"), ("Marbete", "MARBETE"), ("Etiqueta de servicio", "ETIQUETA"),
           ("Oblea PBA", "OBLEA-PBA"), ("Tarjeta de identificación AGC", "TARJETA-AGC"),
           ("Tarjeta de identificación DPS", "TARJETA-DPS"), ("Junta tórica", "ORING"),
           ("Disco de seguridad", "REP-VALV"), ("Manómetro /", "REP-VALV")]
    for p, it in pre:
        if t.startswith(p):
            return "Sí", it
    if t.startswith("Gas impulsor"):
        if "N₂" in t:
            return "Sí", "N2"
        if "Argón" in t:
            return "Sí", "ARGON"
        return "No", ""          # aire comprimido de planta
    ag = _agente(m)
    if ag == "AGUA":
        return "No", ""
    return "Sí", ITEM_AGENTE_REC.get(ag, "")


def _recargas(wb, E):
    ws = wb.create_sheet(HOJAS["rec"])
    ws["A1"] = "BOM de servicio de recarga y mantenimiento por extintor y por caso (IRAM 3517-2:2020)"
    ws["A1"].font = E["Font"](bold=True, size=12)
    notas = [
        "Polvo: un extintor ACCIONADO (aunque sea parcialmente) se recarga con polvo NUEVO; el polvo de ese "
        "extintor no se reutiliza (9.9.1.4). El polvo de un extintor que se abre SIN haber sido accionado "
        "(control interior, prueba hidráulica) puede volver al mismo equipo si se trata en el sistema cerrado "
        "de recuperación del recinto y pasa el control de 9.9.3 (4.4.1 y). Nunca se mezcla ABC con BC (9.9.1.6).",
        "Polvo de la versión anterior de la IRAM 3569 → reemplazo total obligatorio (9.9.4); el retirado es residuo.",
        "HCFC / gases limpios: el agente se trasvasa y RECUPERA en circuito cerrado, nunca se ventea (4.4.1 z). "
        "Se repone sólo la pérdida. El recuperado fuera de especificación va a regeneración por gestor habilitado.",
        "CO₂: carga por trasvase (4.4.1 l); recuperación recomendada en vaciados (9.4.18).",
        "Mermas de 3 % (polvo) y 2 % (HCFC): valores estimados (amarillo) a medir en planta con la balanza de RC-CQ.",
        "Entra MRP: todo lo que se repone; lo recuperado, los grabados y el aire comprimido de planta no se compran.",
    ]
    for i, n in enumerate(notas, 2):
        ws.cell(i, 1, "• " + n).alignment = E["Al"](wrap_text=True, vertical="top")
        ws.merge_cells(start_row=i, start_column=1, end_row=i, end_column=9)
        ws.row_dimensions[i].height = 44
    r0 = 2 + len(notas) + 1
    _leyenda(ws, r0 - 1, 1, E)
    cab = ["Código kit", "Plano", "Extintor", "Caso", "Ítem", "Cant.", "UM", "Estado / origen", "Referencia",
           "Entra MRP", "Proveedor principal", "Alternativa"]
    _cab(ws, r0, cab, [16, 20, 36, 44, 48, 9, 6, 48, 52, 8, 26, 24], E, 30)
    r = r0
    for f in recargas():
        r += 1
        m = next(x for x in MODELOS if x.codigo == f[0])
        letra = f[2][0] if f[2][1:3] == " -" else "I"
        mrp, item = _item_recarga(m, str(f[3]))
        prov, alt, est_p = PV.asignar(item) if mrp == "Sí" else ("", "", "")
        est = "E" if "R:" in str(f[6]) else "V"
        if est_p and NIV_EST[EST_PROV[est_p]] > NIV_EST[est]:
            est = EST_PROV[est_p]
        vals = [f"RK-{P.codigo_pieza(m, 0)[:-3]}-{letra}"] + f + [mrp, prov or None, alt or None]
        fill = E["est"].get(est)
        for j, v in enumerate(vals, 1):
            c = ws.cell(r, j, v)
            c.border = E["borde"]
            c.alignment = E["Al"](wrap_text=j in (4, 5, 8, 9, 11, 12), vertical="top")
            if fill:
                c.fill = fill
    ws.freeze_panes = ws.cell(r0 + 1, 4)
    ws.auto_filter.ref = f"A{r0}:L{r}"
    return ws


def _proveedores(wb, E):
    ws = wb.create_sheet(HOJAS["prov"])
    ws["A1"] = ("Proveedores nacionales por ítem de compra (principal y alternativa) - criterio: argentinos, cercanos o "
                "razonables para Avellaneda, que vendan exactamente lo que pide el plano y cumplan la norma")
    ws["A1"].font = E["Font"](bold=True, size=12)
    ws["A2"] = ("Distancias por ruta desde Avellaneda, aproximadas. Precios: los de la planilla de materias primas de "
                "FLAMA (MP-xx) y las cotizaciones recibidas (ver 11_Validacion_MP).")
    _leyenda(ws, 3, 1, E)
    cab = ["Ítem", "Descripción", "Producto exacto que se pide", "Proveedor principal", "Domicilio",
           "Distancia", "Contacto", "Alternativa", "Domicilio alternativa", "Distancia alt.",
           "Precio / cotización de referencia", "Certificación / norma del principal", "Respaldo", "Estado",
           "Observaciones"]
    _cab(ws, 5, cab, [14, 30, 46, 28, 36, 13, 22, 28, 30, 13, 40, 40, 34, 14, 50], E, 32)
    r = 5
    for it, (desc, prod, pr, al, est, precio, obs) in PV.ITEMS.items():
        r += 1
        P_ = PV.PROV.get(pr) if pr else None
        A_ = PV.PROV.get(al) if al else None
        vals = [it, desc, prod, P_[0] if P_ else "Sin proveedor nacional identificado", P_[2] if P_ else None,
                PV.km(pr) if pr else None, P_[4] if P_ and P_[4] != "-" else None, A_[0] if A_ else None,
                A_[2] if A_ else None, PV.km(al) if al else None, precio, P_[5] if P_ else None,
                P_[6] if P_ else None, est.capitalize(), obs if obs != "-" else None]
        fill = E["est"].get(EST_PROV[est])
        for j, v in enumerate(vals, 1):
            c = ws.cell(r, j, v)
            c.border = E["borde"]
            c.alignment = E["Al"](wrap_text=True, vertical="top")
            if fill:
                c.fill = fill
    ws.freeze_panes = "C6"
    ws.auto_filter.ref = f"A5:O{r}"
    r += 3
    ws.cell(r, 1, "Directorio de proveedores").font = E["Font"](bold=True, size=12)
    r += 1
    _cab(ws, r, ["Id", "Razón social", "Rubro", "Domicilio", "Distancia", "Contacto", "Certificación / producto",
                 "Respaldo"], [14, 30, 46, 28, 36, 13, 40, 40], E, 20)
    for pid, (nom, rub, dom, k, con, cer, resp) in PV.PROV.items():
        r += 1
        for j, v in enumerate([pid, nom, rub, dom, PV.km(pid), con if con != "-" else None, cer, resp], 1):
            c = ws.cell(r, j, v)
            c.border = E["borde"]
            c.alignment = E["Al"](wrap_text=True, vertical="top")
    return ws


DECISIONES = [
    # (tema, decisión, fundamento, impacto en el BOM, estado: V / E / A / X)
    ("Fabricación propia", "Se fabrican sólo los ABC (1 a 100 kg). BC, clase D, agua, AFFF, sales K, CO₂ y HCFC se "
     "compran terminados y se revenden.", "Decisión FLAMA", "Revendidos: BOM completo de referencia; en MRP sólo la "
     "fila S0 «Equipo terminado comprado» (más la tarjeta AGC si el destino es CABA).", "V"),
    ("Alcance del MRP", "El BOM se arma completo; la columna «Entra MRP» marca lo que se compra. Lo fabricado se "
     "explota en su materia prima; lo que viene dentro de un conjunto comprado (válvula HZ, rueda) no se pide aparte.",
     "Decisión FLAMA", "12_Maestro_Consolidado_MP trae todo por producto con la marca Entra MRP. El MRP por año (MRP_MATERIA_PRIMA) va en otro "
     "archivo.", "V"),
    ("Polvo ABC", "DEMSA principal (DEM-60 / DEM-90 según modelo). Polvex / Sancibrao alternativa.",
     "IRAM 3569 (composición declarada por el fabricante del polvo); licencia IRAM 3523 Drago: potencial de "
     "referencia con DEM-60/90; Polvex: sello IRAM 3569 no confirmado", "Con la alternativa el potencial sale del "
     "ensayo de tipo de FLAMA (IRAM 3542 / 3543).", "V"),
    ("Densidad del polvo", "Volumen libre con densidad empacada mínima 1,10 kg/dm³; llenado controlado con aparente "
     "mínima.", "NOM-104-STPS-2001 (IRAM 3569 no fija densidad); criterio de aceptación: descarga ≥ 85 % (IRAM 3523 "
     "4.9.1)", "09_Carga_N2 y fila A2 (N₂) en amarillo hasta el ensayo de descarga.", "E"),
    ("Soldadura", "MAG 135 con Arcal 21 / ARCAL Speed (Ar + 8 % CO₂, M20) y alambre ER70S-6.",
     "Decisión FLAMA. IRAM 3523 3.2.4.2 y 3550 3.2.2.2 nombran «atmósfera inerte»: acreditar con el certificador en "
     "el ensayo de tipo (probetas IRAM 609 y PH)", "Consumos C1 y C2 calculados por longitud de cordón; planos con "
     "símbolo 135.", "E"),
    ("Varilla de refuerzo", "70 y 100 kg: varilla interior longitudinal detrás de la costura, punteada antes de la "
     "soldadura longitudinal para mantener la simetría del cilindrado.", "Decisión de proceso FLAMA", "Pieza en S1 "
     "(planos FL_MAT, FL_REC y FL_DES 70/100). Ø8 SAE 1010 = propuesta de diseño sin cálculo.", "E"),
    ("Carro de rodantes", "Se fabrica en planta (bastidor de caño, eje SAE 1045, sunchos de planchuela, apoyo); se "
     "compran las ruedas.", "Sin proveedor nacional del carro armado; IRAM 3550 3.12 y 4.8 (ruedas ≥ Ø300 × 50)",
     "Materia prima del carro en nivel 3; puesto de soldadura de carros a incorporar al layout.", "A"),
    ("Tapas de rodantes", "Casquetes de 25, 50, 70 y 100 kg embutidos por Gockel Ingeniería (Wilde, Avellaneda).",
     "IRAM 3550 3.2.1 / 4.1.3; proveedor de FLAMA", "Ítem comprado (semielaborado); cotizar con certificado de "
     "material.", "V"),
    ("Pintura", "Tercerizada (Prymax manuales, pintor de carros rodantes).", "Res. 349/07 art. 18: la cabina de "
     "pintura figura en el equipamiento del fabricante; la tercerización queda sujeta a la aceptación del Ministerio",
     "C4 servicio por unidad.", "V"),
    ("Granallado", "Manuales en Airblast G-100 (Ø80-200).", "Ficha del equipo", "1 kg (Ø76,2) fuera de rango: fila "
     "C3 en rojo hasta definir soporte o equipo.", "X"),
    ("Proveedores", "Sólo nacionales y cercanos o razonables para Avellaneda; principal + alternativa.",
     "Decisión FLAMA", "Columnas Proveedor principal / Alternativa y hoja 10_Proveedores.", "V"),
    ("Inoxidables revendidos", "Agua, AFFF 10 L y sales K: recipiente inoxidable soldado (no sin costura), TIG con Ar "
     "puro.", "IRAM 3525 3.2.1 b) y 3.2.2 (≤ 1 longitudinal + 2 transversales, proceso automático, atmósfera inerte); "
     "IRAM 3517-2 9.4.21 (sales K en inoxidable); mercado: «recipiente inoxidable soldado, PH 100 %»",
     "Referencia (revendidos). Proceso exacto (TIG / plasma / láser) no publicado por los fabricantes.", "E"),
    ("Identificación", "Estampilla IRAM, tarjeta AGC (2 módulos), faja de garantía y cuño DPS 15 × 7 según hoja 4.",
     "Anexo R; Res. AGC 32/15; Res. 349/07 anexo IV; Res. 522/07", "Grupo S6.", "V"),
    ("Sustitutos", "Extintor del stock + faja amarilla ≤ 40 mm + tarjeta DPS «sustituto habilitado» + tarjeta AGC "
     "«Es sustituto».", "IRAM 3517-2:2020 9.4.5; Res. 349/07 art. 32; Res. AGC 32/15", "06_BOM_Sustitutos (unitario; "
     "el tamaño del parque se dimensiona aparte).", "V"),
]


def _decisiones(wb, E):
    ws = wb.create_sheet(HOJAS["dec"])
    ws["A1"] = "Decisiones de diseño y abastecimiento que estructuran el BOM"
    ws["A1"].font = E["Font"](bold=True, size=12)
    _leyenda(ws, 2, 1, E)
    _cab(ws, 4, ["N°", "Tema", "Decisión adoptada", "Fundamento (norma / fuente)", "Impacto en el BOM"],
         [5, 22, 60, 60, 60], E, 20)
    for i, (t, d, f, im, est) in enumerate(DECISIONES, 5):
        fill = E["est"].get(est)
        for j, v in enumerate([i - 4, t, d, f, im], 1):
            c = ws.cell(i, j, v)
            c.border = E["borde"]
            c.alignment = E["Al"](wrap_text=True, vertical="top")
            if fill:
                c.fill = fill
    return ws


def _indice(wb, E, n_term, n_cil, n_prop):
    ws = wb.active
    ws.title = HOJAS["indice"]
    ws.column_dimensions["A"].width = 28
    ws.column_dimensions["B"].width = 120
    ws["A1"] = "FLAMA S.A. - Lista de materiales (BOM) de matafuegos, cilindros, sustitutos y recargas"
    ws["A1"].font = E["Font"](bold=True, size=14)
    t = [("Origen", "Generado por código (python generar.py --bom) a partir del mismo modelo 3D que los planos FL_MAT, "
                    "FL_REC, FL_DES y FL_SUS: código, posición, denominación y material de cada pieza son los del "
                    "plano; medida y peso se miden sobre el sólido."),
         ("Alcance", f"{n_term} matafuegos FL_MAT ({n_prop} de fabricación propia ABC y {n_term - n_prop} revendidos), "
                     f"{n_cil} cilindros sueltos FL_REC, {n_term} extintores sustitutos FL_SUS y los kits de "
                     "recarga RK por extintor y caso."),
         ("Niveles", "0 producto (= plano) · 1 subconjunto · 2 pieza o insumo · 3 materia prima de la pieza "
                     "fabricada (cursiva; no suma al peso porque ya está en la pieza)."),
         ("Subconjuntos", " · ".join(f"S{k} {v}" for k, v in NOMBRE_SUB.items()) +
          " · S0 Equipo terminado comprado (revendidos). En los ABC el S1 es el plano FL_REC (el mismo recipiente que "
          "se vende suelto)."),
         ("Entra MRP", "Sí = se compra (materia prima, componente, consumible, servicio, agente, gas, identificación, "
                       "embalaje). No = se fabrica (se explota en su materia prima), viene dentro de un conjunto "
                       "comprado o es un proceso. Revendidos: sólo S0 (y la tarjeta AGC si va a CABA). Cilindros: "
                       "materia prima del recipiente, tapón, etiqueta y embalaje. Sustitutos: sólo el kit de "
                       "identificación. Recargas: todo lo que se repone."),
         ("Códigos", "ABC10-01… pieza del plano (posición 01) · ABC10-S1…S8 subconjuntos · K2 válvula HZ armada · "
                     "C consumible del recipiente · V interno de válvula · A carga · I soporte · E embalaje · "
                     "T cilindro suelto · MP-* materia prima · SUS-* sustituto · RK-*-A/B/C kits de recarga."),
         ("Peso", "kg por unidad de medida. Peso total = Cant. × Peso unit. (fórmula). Subconjunto = suma de sus "
                  "piezas. Componentes comprados sin ficha quedan sin peso (fila naranja).")]
    t += [(f"Fuente {k}", v) for k, v in FUENTES.items()]
    t += [("Normas", "IRAM 3517-2:2020 y las IRAM de producto citadas; resoluciones PBA y CABA. Los PDF de las normas "
                     "tienen licencia monousuario: se citan apartados, no se transcribe texto.")]
    r = 3
    for a, b in t:
        ws.cell(r, 1, a).font = E["Font"](bold=True)
        c = ws.cell(r, 2, b)
        c.alignment = E["Al"](wrap_text=True, vertical="top")
        ws.row_dimensions[r].height = max(18, 15 * (len(b) // 115 + 1))
        r += 1
    r += 1
    ws.cell(r, 1, "Colores de estado").font = E["Font"](bold=True, size=12)
    for k, (c, txt) in COLOR_EST.items():
        r += 1
        a = ws.cell(r, 1, {"V": "Sin color", "E": "Amarillo", "A": "Naranja", "X": "Rojo"}[k])
        a.border = E["borde"]
        if c:
            a.fill = E["Fill"]("solid", fgColor=c)
        ws.cell(r, 2, txt).alignment = E["Al"](wrap_text=True)
    r += 2
    ws.cell(r, 1, "Hojas").font = E["Font"](bold=True, size=12)
    desc = {"dec": "Decisiones de diseño y abastecimiento con su fundamento",
            "res": "Una fila por matafuego: agente, carga, gas, pesos, desvío contra catálogo, ítems en MRP",
            "mat": "BOM de los 17 matafuegos en tabla plana filtrable",
            "cil": "BOM de los 8 cilindros sueltos FL_REC",
            "sus": "BOM unitario de los extintores sustitutos FL_SUS",
            "rec": "Kits de recarga por extintor y por caso (IRAM 3517-2:2020)",
            "qui": "Química y densidades de los agentes (entrada de 09_Carga_N2)",
            "n2": "Volumen libre, gas impulsor y control de llenado por modelo",
            "prov": "Proveedores nacionales por ítem (principal y alternativa) y directorio",
            "val": "Respaldo documental y estado de cada materia prima y componente",
            "exp": "Maestro consolidado: todo lo que lleva cada matafuego, cilindro, sustituto y kit de recarga, por "
                   "unidad, más los insumos de cada proceso (base del archivo MRP_MATERIA_PRIMA)",
            "fue": "Documentos y fuentes técnicas citadas",
            "mer": "Peso cargado de fabricantes con sello IRAM contra el modelo",
            "pla": "Planos de conjunto, despiece, recipiente y sustituto de cada producto"}
    for k, d in desc.items():
        r += 1
        c = ws.cell(r, 1, HOJAS[k])
        c.hyperlink = f"#{_ref(HOJAS[k])}!A1"
        c.font = E["Font"](color="0563C1", underline="single")
        ws.cell(r, 2, d)
    r += 1
    ws.cell(r, 1, "BOM_FL_MAT_* / BOM_FL_REC_*")
    ws.cell(r, 2, "Una hoja por plano con el BOM multinivel plegable (links en 03_Resumen_Productos y 15_Indice_Planos)")
    return ws


def _indice_planos(wb, productos, E):
    from . import sustituto as SU
    ws = wb.create_sheet(HOJAS["pla"])
    ws["A1"] = "Índice de planos por producto"
    ws["A1"].font = E["Font"](bold=True, size=12)
    _cab(ws, 3, ["Producto", "Fabricación", "Plano de conjunto (4 láminas)", "Despiece", "Recipiente suelto",
                 "Sustituto", "Subconjuntos", "BOM"], [40, 12, 30, 26, 30, 30, 60, 24], E, 30)
    for i, (m, filas) in enumerate(productos, 4):
        des = "FL_DES_" + m.codigo[7:]
        rec = m.codigo.replace("FL_MAT_", "FL_REC_") if m.codigo in PROPIOS else "-"
        subs = ", ".join(f["codigo"].split("-")[-1] + " " + f["desc"] for f in filas if f["nivel"] == 1)
        vals = [m.nombre, "Propia" if m.codigo in PROPIOS else "Revendido", f"salida/{m.codigo}/{m.codigo}.pdf",
                f"salida/despiece/{des}.pdf", f"salida/cilindros/{rec}/{rec}.pdf" if rec != "-" else "-",
                f"salida/sustituto (lámina {SU.codigo(m)})", subs, hoja(m.codigo)]
        for j, v in enumerate(vals, 1):
            c = ws.cell(i, j, v)
            c.border = E["borde"]
            c.alignment = E["Al"](wrap_text=True, vertical="top")
        ws.cell(i, 8).hyperlink = f"#{_ref(hoja(m.codigo))}!A1"
        ws.cell(i, 8).font = E["Font"](color="0563C1", underline="single")
    return ws


def _sustitutos(m):
    """BOM unitario del sustituto con MRP, proveedores y estado."""
    from . import sustituto as SU
    rows = SU.bom_sustituto(m)
    it = {"-01": "FAJA-SUS", "-02": "TARJETA-DPS", "-03": "TARJETA-AGC", "-04": "IMPRESOS"}
    for r in rows:
        r["item"], r["mrp"], r["est"] = "", "", ""
        if r["nivel"] == 1 and r["codigo"] == m.codigo:
            r["mrp"] = "No"
            r["obs"] += " · No entra en MRP del kit: es demanda del producto FL_MAT (stock)"
        elif r["nivel"] == 2:
            r["item"] = it.get(r["codigo"][-3:], "")
            r["mrp"] = "Sí"
        r["prov"], r["alt"], est_p = PV.asignar(r["item"]) if r["item"] else ("", "", "")
        if est_p:
            r["est"] = EST_PROV[est_p]
    return rows


def excel(ruta):
    from openpyxl import Workbook
    from . import recipientes as RC
    from . import sustituto as SU
    E = _estilos()
    wb = Workbook()
    term = [(m, bom_producto(m)) for m in MODELOS]
    cil = [(m, bom_producto(m, cilindro=True)) for m in RC.modelos_abc()]
    _indice(wb, E, len(term), len(cil), sum(1 for m, _ in term if m.codigo in PROPIOS))
    _decisiones(wb, E)
    _resumen(wb, term, E)
    _plana(wb, HOJAS["mat"], "BOM de matafuegos terminados FL_MAT (tabla plana filtrable)",
           [(m.codigo, f) for m, f in term], E)
    _plana(wb, HOJAS["cil"], "BOM de cilindros sueltos FL_REC", [(RC.codigo_rec(m), f) for m, f in cil], E)
    _plana(wb, HOJAS["sus"], "BOM unitario de extintores sustitutos FL_SUS (IRAM 3517-2:2020 9.4.5)",
           [(SU.codigo(m), _sustitutos(m)) for m in MODELOS], E)
    _recargas(wb, E)
    fq = _quimica(wb, E)
    _carga_n2(wb, E, fq)
    _proveedores(wb, E)
    _validacion(wb, E)
    _maestro(wb, term, cil, E)
    _fuentes(wb, E)
    _mercado(wb, E, term)
    _indice_planos(wb, term, E)
    for m, f in term:
        _hoja_producto(wb, m, f, E)
    for m, f in cil:
        _hoja_producto(wb, m, f, E, cilindro=True)
    wb.save(ruta)
    return term, cil
