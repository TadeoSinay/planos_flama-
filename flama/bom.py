"""BOM (lista de materiales multinivel) de cada matafuego y de cada cilindro, en Excel.

Sale del MISMO modelo 3D que los planos FL_MAT_* y FL_REC_*: posición, código de pieza, denominación y
material son los de la lista de piezas IRAM 4508 de cada plano (planos.lista), y la medida y el peso de
cada pieza se miden sobre el sólido (caja envolvente, volumen × densidad). A eso se suma lo que el plano
de conjunto no dibuja pero el producto lleva: consumibles de soldadura y pintura, agente extintor y gas
impulsor, juntas y resorte de la válvula, identificación, precinto, soporte y embalaje.

Niveles: 0 producto (plano) · 1 subconjunto · 2 pieza o insumo · 3 materia prima de la pieza fabricada.
Fuente de cada valor: P = plano / modelo 3D · C = catálogo · N = norma (IRAM 3517-2:2020, 3504) ·
L = layout de planta (FL_PI_04 aprovechamiento de chapa) · R = valor de referencia a confirmar.

Uso: python generar.py --bom   ->   salida/bom/FLAMA_BOM.xlsx
"""

import math

from . import modelo3d as M
from . import materiales as MAT
from . import planos as P
from .catalogo import MODELOS
from . import accesorios as AC

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
    ("cupula", "1 kg"): (108, 0.9, 114), ("fondo", "1 kg"): (100, 0.9, 106),
    ("cupula", "2,5 kg"): (179, 1.25, 200), ("fondo", "2,5 kg"): (148, 1.25, 200),
    ("cupula", "5 kg"): (221, 1.6, 250), ("fondo", "5 kg"): (177, 1.6, 200),
    ("cupula", "10 kg"): (258, 2.0, 300), ("fondo", "10 kg"): (205, 2.0, 249),
}
CANO_1KG = dict(barra=6000, pieza=255, piezas=23, diam=76.2, esp=1.25)

# familias que la planta fabrica (líneas S1, S2, S3) y las que revende (S4 tercerizados con sello IRAM)
PROPIOS = {"FL_MAT_ABC_1kg", "FL_MAT_ABC_2.5kg", "FL_MAT_ABC_5kg", "FL_MAT_ABC_10kg", "FL_MAT_ABC_25kg",
           "FL_MAT_ABC_50kg", "FL_MAT_ABC_70kg", "FL_MAT_ABC_100kg", "FL_MAT_BC_5kg", "FL_MAT_CLASED_9l"}

# subconjuntos: clave de pieza del modelo -> subconjunto
SUB = {
    "cuerpo": 1, "cupula": 1, "fondo": 1, "cuello": 1, "pie": 1,
    "tuerca": 2, "espiga": 2, "cuerpo_valvula": 2, "vastago": 2, "eje": 2, "manija_superior": 2,
    "manija_inferior": 2, "pasador": 2, "manometro": 2, "disco_seguridad": 2, "cano_pesca": 2,
    "racor": 3, "manguera": 3, "tobera": 3, "lanza": 3, "empunadura": 3, "brazo_difusor": 3, "difusor": 3,
    "suncho": 3, "valvula_esferica": 3, "tobera_campana": 3, "manguera_enrollada": 3, "soportes_manguera": 3,
    "rueda_der": 4, "llanta_der": 4, "eje_ruedas": 4, "bastidor": 4, "sunchos_bastidor": 4, "apoyo": 4,
}
NOMBRE_SUB = {1: "Recipiente (cilindro)", 2: "Conjunto de válvula", 3: "Dispositivo de descarga",
              4: "Carro (bastidor y ruedas)", 5: "Carga: agente extintor y gas impulsor",
              6: "Identificación y precinto", 7: "Embalaje", 8: "Soporte (accesorio de montaje)"}

# densidad aparente de los agentes (kg/dm³) y masa molar del gas impulsor (kg/mol): R = referencia
RHO_AGENTE = {"ABC": 0.95, "BC": 1.05, "D": 1.10, "HCFC": 1.46}
MOLAR = {"N₂": 0.028, "Argón": 0.040}


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
    if k == "cuello":
        return "C2 punteo" if rod else "7 Preparación de cuello -> 8 soldadura de cuello"
    if SUB.get(k) == 2:
        return "C9 armado" if rod else "19 Ensamblaje de válvula (T03/T04)"
    if SUB.get(k) == 3:
        return "C9 armado de ruedas y manguera" if rod else "19 Ensamblaje (T03/T04)"
    if SUB.get(k) == 4:
        return "C9 armado de ruedas y manguera (S-TC)"
    return ""


def origen(m, k):
    if m.codigo not in PROPIOS:
        return "Compra (en el conjunto)"
    if k in ("cuerpo", "cuello") or (k in ("cupula", "fondo") and m.familia != "rodante"):
        return "Fabricación"
    if k in ("bastidor", "sunchos_bastidor", "apoyo", "soportes_manguera", "suncho"):
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
        nombre = {"ABC": "Polvo químico seco ABC (fosfato monoamónico)", "BC": "Polvo químico seco BC (bicarbonato)",
                  "D": "Polvo para metales combustibles clase D", "HCFC": "HCFC 123 / HFC 236fa (agente limpio)"}[ag]
        v_ag = kg / RHO_AGENTE[ag]
        gas = "Argón" if ag == "HCFC" else "N₂"
        libre = V - v_ag
        q, um = kg, "kg"
    elif ag == "CO2":
        kg = float(cap.split()[0])
        return ("Dióxido de carbono (IRAM 41170)", kg, "kg", n_ag, "- (autopresurizado)", 0.0, 0.0, 0.0)
    else:
        litros = float(cap.split()[0])
        nombre = {"AGUA": "Agua", "AFFF": "Agua + concentrado AFFF 3 %", "K": "Solución de sales de potasio (clase K)"}[ag]
        q, um = litros, "L"
        gas, libre = "N₂", V - litros
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


def tabla_carga():
    """Relación agente / gas impulsor por modelo (hoja Carga_N2)."""
    out = []
    for m in MODELOS:
        ag = _agente(m)
        nombre, q, um, n_ag, gas, m_gas, nm3, libre = carga(m)
        tol, obj, ref = tolerancia(m)
        V = m.geo["vol_dm3"]
        rho = RHO_AGENTE.get(ag)
        v_ag = q / rho if rho else (q if um == "L" else None)
        if ag == "CO2":
            llen = q / V
            obs = (f"Autopresurizado. Grado de llenado {_f(llen, 3)} kg/dm³ (máx. 0,75 kg/dm³, R: IRAM 2533 / ADR P200)"
                   + ("" if llen <= 0.75 else " - EXCEDE"))
        else:
            obs = ("" if libre >= 0.10 * V else "OJO: volumen libre < 10 % del recipiente; revisar densidad aparente "
                   "del polvo o volumen del plano")
        out.append([m.codigo, nombre, m.spec["Norma IRAM extintor"], q, um, tol, round(obj, 3), ref, V,
                    rho, None if v_ag is None else round(v_ag, 3), None if ag == "CO2" else round(libre, 3),
                    None if ag == "CO2" else round(libre / V, 4), _ps(m), gas, round(m_gas * 1000, 1),
                    round(nm3 * 1000, 1), round(m_gas * 1000 / obj, 2) if m_gas else None, obs])
    return out


# ------------------------------------------------------------------ embalaje
def embalaje(m, bb):
    W, Dd, H = bb.xlen, bb.ylen, bb.zlen
    if m.familia == "rodante":
        n = max(1, int(1200 // W) * int(1000 // Dd)) if W < 1200 and Dd < 1000 else 1
        return dict(caja=None, por_pallet=n, film=0.35 / n)
    cw, cd, ch = W + 30, Dd + 30, H + 20
    capas = max(1, int(1450 // ch))
    por_capa = max(int(1200 // cw) * int(1000 // cd), int(1200 // cd) * int(1000 // cw), 1)
    n = capas * por_capa
    pared = "simple" if m.familia == "manual" and float(m.geo["vol_dm3"]) < 7 else "doble"
    return dict(caja=(cw, cd, ch, pared), por_pallet=n, film=0.35 / n)


# ------------------------------------------------------------------ BOM de un producto
def bom_producto(m, cilindro=False):
    """Filas del BOM. Si `cilindro`, sólo el recipiente vendido suelto (plano FL_REC)."""
    piezas, info = M.construir(m)
    filas_plano, orden, _ = P.lista(m, piezas)
    cod_plano = m.codigo.replace("FL_MAT_", "FL_REC_") if cilindro else m.codigo
    base = P.codigo_pieza(m, 0)[:-3]
    rows = []

    def add(nivel, cod, desc, cant, um, mat="", med="", peso=None, ori="", op="", norma="", fte="", plano="",
            obs="", sub=0):
        peso = None if peso is None else round(peso, 4)   # kg por unidad de medida
        rows.append(dict(nivel=nivel, codigo=cod, desc=desc, cant=cant, um=um, mat=mat, med=med, peso=peso,
                         ori=ori, op=op, norma=norma, fte=fte, plano=plano, obs=obs, sub=sub))

    nombre = (f"Cilindro (recipiente) {m.nombre.replace('Extintor ', '').replace(' sobre ruedas', ' rodante')} "
              "- repuesto vacío sin válvula") if cilindro else m.nombre
    n_ext = m.spec["Norma IRAM extintor"]
    add(0, cod_plano, nombre, 1, "u", norma=f"IRAM {n_ext}", fte="P",
        plano=cod_plano, obs=("Fabricación propia" if m.codigo in PROPIOS else "Tercerizado revendido (S4)"))
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
        add(1, cod_sub, NOMBRE_SUB[s_], 1, "u", ori=("Fabricación" if s_ == 1 and m.codigo in PROPIOS
                                                         and m.familia != "co2" else "Compra / armado"),
            plano=plano_sub, sub=s_,
            norma={1: "IRAM 3523 / 3550 (recipiente)", 2: "Manómetro IRAM 3533"}.get(s_, ""), fte="P")
        for fila, k in por_sub[s_]:
            pos, cant, nom, cod, mat, _kg, obs = fila
            if cod == "Comercial":
                cod, obs = P.codigo_pieza(m, pos), ("Pieza comercial; " + obs).strip("; ")
            kg = MAT.peso(piezas[k], MAT.especificacion(m, k)[2], MAT.especificacion(m, k)[3])
            fte = "P"
            if kg is None:
                kg = {28.0: 0.04, 38.0: 0.06, 50.0: 0.12}.get(round(info["valvula"]["man_d"]), 0.06)
                fte = "R"
            add(2, cod, nom, cant, "u", mat, medida(m, k, piezas[k], info), kg, origen(m, k), operacion(m, k),
                norma=("IRAM 3533" if k == "manometro" else ""), fte=fte, plano=f"FL_DES_{m.codigo[7:]}", obs=obs,
                sub=s_)
            # materia prima de las piezas fabricadas
            if m.codigo in PROPIOS and origen(m, k) == "Fabricación":
                for r in materia_prima(m, k, piezas[k], kg):
                    add(3, *r, sub=s_)
        if s_ == 1:
            for r in consumibles_recipiente(m, piezas):
                add(2, f"{base}-{r[0]}", *r[1:], sub=1)
        if s_ == 2:
            for r in internos_valvula(m):
                add(2, f"{base}-{r[0]}", *r[1:], sub=2)
    if cilindro:
        add(2, f"{base}-T1", "Tapón protector de rosca del cuello", 1, "u", "Polietileno",
            f"para rosca {m.geo['cuello'][2]}", 0.005, "Compra", "Embalaje", fte="R", sub=1)
        add(2, f"{base}-T2", "Marcado del recipiente (estampado)", 1, "u", "-",
            "N° de serie, año, presión de prueba, norma", None, "Proceso", "Marcado", norma="IRAM 3523 (marcado)",
            fte="R", sub=1)
        emb = embalaje(m, M.bbox({k: v for k, v in piezas.items() if SUB.get(k) == 1}))
        _emb(add, base, emb, m, sub=7, cilindro=True)
        return rows
    # ---- carga
    ag, q, um, n_ag, gas, m_gas, nm3, libre = carga(m)
    add(1, f"{base}-S5", NOMBRE_SUB[5], 1, "u", ori="Carga en planta" if m.codigo in PROPIOS else "Compra",
        op=("18 Carga de polvo (T01) / C8 (T02)" if m.codigo in PROPIOS else ""), sub=5)
    tol, obj, ref_tol = tolerancia(m)
    if _agente(m) == "AFFF":
        add(2, f"{base}-A1", "Agua potable (premezcla)", round(q * 0.97, 3), "L", "Agua", f"97 % de {_f(q)} L; "
            f"tolerancia {tol}", 1.0, "Red", "SP-1 premezcla", norma=ref_tol, fte="N", sub=5)
        ag, q, um = "Concentrado espumígeno AFFF 3 % (IRAM 3515)", round(q * 0.03, 3), "L"
    add(2, f"{base}-A1" + ("b" if _agente(m) == "AFFF" else ""), ag, q if _agente(m) == "AFFF" else round(obj, 3), um, ag,
        f"nominal {_f(q, 3)} {um}; tolerancia {tol} ({ref_tol})", {"AGUA": 1.0, "AFFF": 1.0, "K": 1.35}.get(_agente(m), 1.0),
        "Compra", "SP-1 almacén previo a la carga", norma=f"IRAM {n_ag}" if n_ag != "-" else "", fte="C",
        obs="Lote único por extintor; prohibido mezclar ABC con BC (3517-2 9.9.1.6)" if _agente(m) in ("ABC", "BC")
        else "", sub=5)
    if m_gas:
        add(2, f"{base}-A2", f"Gas impulsor: {gas}", round(m_gas, 4), "kg", gas,
            f"{_f(nm3 * 1000, 1)} L normales para {_f(_ps(m), 1)} MPa a 20 °C en {_f(libre, 2)} dm³ libres",
            1.0, "Compra", "20 Presurización (T05) / C10", norma="IRAM 3517-2 9.4.9 (tabla 2) · IRAM 3523 2.3 y 3.10", fte="C",
            obs="Batería en SP-1; punto de rocío ≤ -56,7 °C para gases limpios", sub=5)
    # ---- identificación, precinto y accesorios
    add(1, f"{base}-S6", NOMBRE_SUB[6], 1, "u", ori="Compra", op="22 Etiquetado (T07)", sub=6)
    D = 2 * m.geo["R"]
    alto_cuerpo = piezas["cuerpo"].BoundingBox().zlen
    ew, eh = min(round(0.42 * math.pi * D), 240), min(round(0.45 * alto_cuerpo), 220)
    add(2, f"{base}-I1", "Etiqueta frontal: instrucciones de uso, clases de fuego y datos del fabricante", 1, "u",
        "Vinilo autoadhesivo laminado", f"{ew} × {eh}", 0.01, "Compra", "22 Etiquetado (T07)",
        norma=f"IRAM {n_ext} (rotulado) · IRAM 3517-2 7.2.2", fte="R", sub=6)
    add(2, f"{base}-I2", "Sello de conformidad IRAM (marca de certificación)", 1, "u", "Oblea de seguridad",
        "según IRAM", 0.001, "Compra", "22 Etiquetado", norma="Marca IRAM", fte="R", sub=6)
    add(2, f"{base}-I3", "Tarjeta de control (registro de servicio)", 1, "u", "Cartulina plastificada",
        "35 × 50 (celeste)", 0.002, "Compra", "22 Etiquetado", norma="IRAM 3517-2 8.3.3", fte="N", sub=6)
    add(2, f"{base}-I4", "Precinto numerado (traba del pasador)", 1, "u", "Polipropileno",
        "rompe entre 30 y 50 N; identifica fabricante y lote", 0.001, "Compra", "20 Presurización",
        norma="IRAM 3517-2 9.4.13", fte="N", sub=6)
    sop = m.spec.get("Soporte pared"), m.spec.get("Soporte vehicular")
    if "Si" in sop or "Opcional" in sop:
        add(1, f"{base}-S8", NOMBRE_SUB[8], 1, "u", ori="Compra", op="23 Embalaje (va dentro de la caja)",
            norma="IRAM 3517-2 7.4", sub=8)
    if sop[0] == "Si":
        kg_s = AC.soporte_pared(g=m.geo, e=2.0)[0].Volume() * 1e-6 * MAT.ACERO
        add(2, f"{base}-I5", "Soporte de pared (FL_ACC_01)", 1, "u", "Chapa acero SAE 1010 e=2 pintada",
            "placa 60 × 180, ala con ranura Ø cuello + 3", round(kg_s, 3), "Compra", "23 Embalaje",
            norma="IRAM 3517-2 7.4", fte="P", plano="FL_ACC_01", sub=8)
        add(2, f"{base}-I6", "Tornillo y tarugo de fijación", 2, "u", "Acero cincado / nylon", "M6 × 50 + tarugo 8",
            0.01, "Compra", "23 Embalaje", fte="R", sub=8)
    if sop[1] == "Si":
        kg_s = AC.soporte_vehicular(g=m.geo, e=2.5)[0].Volume() * 1e-6 * MAT.ACERO
        add(2, f"{base}-I7", "Soporte vehicular con cierre rápido (FL_ACC_02)", 1, "u",
            "Chapa acero SAE 1010 e=2,5 pintada", "base 80 de ancho, 2 aros con hebilla", round(kg_s, 3), "Compra",
            "23 Embalaje", norma="IRAM 3517-2 7.4", fte="P", plano="FL_ACC_02", sub=8)
    if "Opcional" in sop:
        add(2, f"{base}-I8", "Soporte opcional (pared o vehicular, según pedido)", 0, "u", "-", "-", None,
            "Compra", "", fte="C", obs="Sólo si el pedido lo incluye", sub=8)
    # ---- embalaje
    emb = embalaje(m, M.bbox(piezas))
    _emb(add, base, emb, m, sub=7)
    return rows


def _emb(add, base, emb, m, sub, cilindro=False):
    add(1, f"{base}-S7", NOMBRE_SUB[7], 1, "u", ori="Compra", op="23 Embalaje -> 24 envolvedora (T11)", sub=sub)
    n = emb["por_pallet"]
    if emb["caja"]:
        cw, cd, ch, pared = emb["caja"]
        add(2, f"{base}-E1", f"Caja de cartón corrugado {pared}", 1, "u", "Cartón corrugado",
            f"{_f(cw, 0)} × {_f(cd, 0)} × {_f(ch, 0)} interior", 0.25 if pared == "simple" else 0.5, "Compra",
            "23 Embalaje", fte="R", sub=sub)
        if not cilindro:
            add(2, f"{base}-E2", "Instructivo de uso y mantenimiento", 1, "u", "Papel", "A5", 0.01, "Compra",
                "23 Embalaje", norma="IRAM 3517-2 (información al usuario)", fte="R", sub=sub)
    else:
        add(2, f"{base}-E1", "Esquineros y funda de polietileno", 1, "jgo", "PE / cartón", "a medida", 0.3,
            "Compra", "23 Embalaje", fte="R", sub=sub)
    add(2, f"{base}-E3", "Pallet 1200 × 1000 (fracción)", round(1 / n, 4), "u", "Madera", f"{n} u por pallet",
        round(22.0 / n, 3), "Compra", "23 Embalaje", fte="R", sub=sub)
    add(2, f"{base}-E4", "Film stretch (fracción del pallet)", round(emb["film"], 4), "kg", "PE lineal 23 µm",
        "envolvedora EDOS PS5", 1.0, "Compra", "24 Envolvedora (T11)", fte="R", sub=sub)
    add(2, f"{base}-E5", "Etiqueta de pallet (lote y destino, fracción)", round(1 / n, 4), "u", "Papel térmico",
        "100 × 150", 0.0, "Compra", "24 Envolvedora", fte="R", sub=sub)


def materia_prima(m, k, s, kg):
    """Nivel 3: materia prima de las piezas fabricadas (código, descripción, cant, UM, material, medida, peso,
    origen, operación, norma, fuente, plano, obs)."""
    g = m.geo
    tam = _tam(m)
    out = []
    if k == "cuerpo":
        if m.capacidad == "1 kg":
            c = CANO_1KG
            out.append(("MP-CANO", f"Caño Ø{_f(c['diam'])} × {_f(c['esp'], 2)} (tramo de barra de 6 m)",
                        round(1 / c["piezas"], 4), "barra", "Caño acero SAE 1010 con costura",
                        f"{c['pieza']} mm por cuerpo; {c['piezas']} cuerpos por barra (kg por barra)", round(kg * c['barra'] / c['pieza'], 3),
                        "Compra (Metalprisa)", "AL-1T cantiléver", "", "L", "FL_PI_04 h2", ""))
        elif tam in HOJA_CUERPO:
            fmt, e, alto, des, ap = HOJA_CUERPO[tam]
            bruto = alto * des * e * 7.85e-6 / (ap / 100)
            obs = "" if abs(e - g["t"]) < 0.01 else f"OJO: la hoja de corte usa e={_f(e, 2)} y el plano e={_f(g['t'], 2)}"
            out.append(("MP-HOJA", f"Recorte de hoja {fmt} e={_f(e, 2)}", 1, "u", "Chapa SAE 1010 "
                        + fmt.split()[0], f"{_f(alto)} × {_f(des)} (aprovech. {_f(ap)} %)", round(bruto, 3),
                        "Compra (Pradecon)", "AL-1H paquetes de hojas", "", "L", "FL_PI_04 h2", obs))
    if k in ("cupula", "fondo"):
        d = DISCO.get((k, tam))
        e = g["td"] if k == "cupula" else g["tf"]
        if d:
            Ø, e_l, anc = d
            paso = Ø + 3
            kg_m = anc * 1000 * e_l * 7.85e-6         # kg por metro de fleje
            obs = "" if abs(e_l - e) < 0.01 else f"OJO: el fleje es e={_f(e_l, 2)} y el plano e={_f(e, 2)}"
            out.append(("MP-FLEJE", f"Fleje e={_f(e_l, 2)} × {anc} (paso {_f(paso)})", round(paso / 1000, 4), "m",
                        "Fleje SAE 1010", f"disco Ø{Ø} (kg por m de fleje)", round(kg_m, 3), "Compra (Pacheco / Pradecon)",
                        "AL-1F porta-flejes", "", "L", "FL_PI_04 h2", obs))
    if k == "cuello":
        out.append(("MP-CUELLO", "Cuello roscado mecanizado (pieza comprada lista para soldar)", 1, "u",
                    "Acero SAE 1010 / 1020", f"rosca {g['cuello'][2]}", round(kg, 3), "Compra (Eli-Met)",
                    "AL-1C cuellos y roscas", "", "L", "", ""))
    return out


def consumibles_recipiente(m, piezas):
    """Soldadura (alambre y gas), granalla y pintura del recipiente, a partir del modelo."""
    out = []
    if m.familia == "co2":
        out.append(("C3", "Pintura en polvo poliéster rojo (recipiente)", round(_area(m, piezas) * 0.185, 3), "kg",
                    "Poliéster RAL 3000 / rojo 03-1-050", f"{_f(_area(m, piezas), 3)} m² × 80 µm, rendimiento 65 %",
                    0.65, "Compra", "17 Pintura (S-P)", "DOC-01", "R", "", ""))
        return out
    v = piezas["soldaduras"].Volume() * 1e-6 * MAT.ACERO
    if m.familia == "inox":
        aporte, gas, rate, q_gas = "Varilla TIG ER308L Ø1,6", "Argón", 0.8, 10
        dep = 0.95
    else:
        aporte, gas, rate, q_gas = "Alambre MAG ER70S-6 Ø0,9/1,2", "Arcal 21 (Ar + 18 % CO₂)", 2.0, 15
        dep = 0.92
    kg_al = v / dep
    min_arco = kg_al / rate * 60
    out.append(("C1", f"Aporte de soldadura: {aporte}", round(kg_al, 4), "kg", aporte.split(":")[0],
                f"cordones del plano: {_f(v * 1000, 0)} g depositados (rend. {int(dep * 100)} %)", dep,
                "Compra", "4 sold. long. / 8 cuello / 11 circunferencial", "ISO 4063 131 / 141", "P", "", ""))
    out.append(("C2", f"Gas de protección: {gas}", round(min_arco * q_gas, 1), "L", gas,
                f"{_f(min_arco, 1)} min de arco × {q_gas} L/min", None, "Compra",
                "Colector SC" if m.familia != "inox" else "Botellón", "", "R", "", ""))
    if m.familia != "inox":
        a = _area(m, piezas)
        out.append(("C3", "Granalla de acero (consumo)", round(a * 0.08, 3), "kg", "Granalla S-230",
                    f"{_f(a, 3)} m² a Sa 2½", None, "Compra", "14 Granallado (B08)", "ISO 8501-1", "R", "", ""))
        out.append(("C4", "Pintura en polvo poliéster rojo", round(a * 0.185, 3), "kg", "Poliéster rojo 03-1-050",
                    f"{_f(a, 3)} m² × 80 µm (60-100 µm), rendimiento 65 %", 0.65, "Compra",
                    "17 Pintura (S-P) / tercerizada en carros", "DOC-01 · IRAM 3517-2 9.10", "R", "", ""))
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
    out = [("V1", "Junta tórica de asiento del cuello", 1, "u", "NBR 70 Shore A",
            f"para cuello Ø{_f(dn)} ({m.geo['cuello'][2]})", 0.002, "Compra", "19 Ensamblaje",
            "", "R", "", "Se cambia en cada recarga")]
    if m.familia != "co2":
        out.append(("V2", "Resorte de retorno del vástago", 1, "u", "Alambre acero inox. AISI 302", "según válvula",
                    0.003, "Compra", "19 Ensamblaje", "", "R", "", ""))
    out.append(("V3", "Junta tórica del vástago", 1, "u", "NBR 70 Shore A", "según válvula", 0.001, "Compra",
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
        rep = [("Precinto numerado nuevo", 1, "u", "Nuevo", "9.4.13"),
               ("Marbete (anillo, color del año)", 1, "u", "Nuevo", "9.4.14 · fig. 9 · tabla 4"),
               ("Tarjeta / etiqueta de control", 1, "u", "Nuevo", "8.3.3"),
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
        ("Peso total (kg)", 11), ("Material", 30), ("Medida (mm)", 52), ("Origen", 20),
        ("Operación / puesto (layout FLAMA)", 40), ("Norma / referencia", 32), ("Fte.", 5), ("Plano", 20),
        ("Observaciones", 48)]
CLAVES = ["nivel", "codigo", "desc", "cant", "um", "peso", None, "mat", "med", "ori", "op", "norma", "fte", "plano",
          "obs"]
FUENTES = {"P": "Plano / modelo 3D (misma geometría que el plano FL_MAT / FL_REC)",
           "C": "Catálogo técnico (flama/catalogo.py)",
           "N": "Norma IRAM (se cita el apartado; texto no transcripto por licencia)",
           "L": "Layout de planta FLAMA (FL_PI_04: aprovechamiento de chapa, proveedores, ubicaciones)",
           "R": "Valor de referencia a confirmar con proveedor o en planta"}


def _estilos():
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    fino = Side(style="thin", color="B0B0B0")
    return dict(
        Font=Font, Fill=PatternFill, Al=Alignment,
        borde=Border(left=fino, right=fino, top=fino, bottom=fino),
        cab=PatternFill("solid", fgColor="7F1D1D"),
        niv={0: PatternFill("solid", fgColor="E5B8B7"), 1: PatternFill("solid", fgColor="F2DCDB"),
             2: None, 3: PatternFill("solid", fgColor="F2F2F2")},
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
    for f in filas:
        r += 1
        if prod_col:
            ws.cell(r, 1, f["_prod"])
        for j, k in enumerate(CLAVES, 1 + off):
            if k is None:
                continue
            v = f[k]
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
        for j in range(1, len(cols) + 1):
            c = ws.cell(r, j)
            c.border = E["borde"]
            c.alignment = E["Al"](wrap_text=j in (3 + off, 9 + off, 11 + off, 12 + off, 15 + off), vertical="top")
            if fill:
                c.fill = fill
            if n <= 1:
                c.font = E["Font"](bold=True)
            elif n == 3:
                c.font = E["Font"](italic=True, color="555555")
        ws.cell(r, 4 + off).number_format = "0.####"
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


def _hoja_producto(wb, m, filas, E, cilindro=False):
    cod = filas[0]["codigo"]
    ws = wb.create_sheet(cod[:31])
    ws.sheet_properties.outlinePr.summaryBelow = False
    ws.sheet_properties.tabColor = "1F4E79" if cilindro else "7F1D1D"
    ws["A1"] = f"FLAMA S.A. - Lista de materiales (BOM) multinivel - {cod}"
    ws["A1"].font = E["Font"](bold=True, size=14)
    ws["A2"] = filas[0]["desc"]
    ws["A2"].font = E["Font"](bold=True, size=11)
    datos = [("Plano de origen", cod + ("  (recipiente para venta suelta)" if cilindro else "  (3 láminas)")),
             ("Plano de despiece", "FL_DES_" + m.codigo[7:] + " (salida/despiece/)"),
             ("Norma del producto", filas[0]["norma"]),
             ("Fabricación", filas[0]["obs"]),
             ("Peso catálogo cargado (kg)", None if cilindro else float(m.spec["Peso cargado (kg)"].replace(",", ".")))]
    for i, (k, v) in enumerate(datos, 3):
        ws.cell(i, 1, k).font = E["Font"](bold=True)
        ws.cell(i, 3, v)
    r0 = 10
    last, subs, raiz = _tabla(ws, _grupos(filas), r0, E)
    from openpyxl.utils import get_column_letter as L
    # pesos resumen (fórmulas sobre los subtotales)
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
        ws["E6"] = "Desvío cargado vs catálogo"
        ws["G6"] = "=G4/C7-1"
        ws["G6"].number_format = "0.0%"
    for c in ("E3", "E4", "E5", "E6"):
        ws[c].font = E["Font"](bold=True)
    for c in ("G3", "G4", "G5"):
        ws[c].number_format = "0.000"
    ws["A8"] = ("Niveles: 0 producto · 1 subconjunto · 2 pieza / insumo · 3 materia prima (gris, no suma). "
                "Use los botones 1-2-3 de la izquierda para plegar. Fte.: P plano · C catálogo · N norma · "
                "L layout · R referencia a confirmar.")
    ws["A8"].font = E["Font"](italic=True, size=9)
    ws.freeze_panes = ws.cell(r0 + 1, 4)
    ws.auto_filter.ref = f"A{r0}:{L(len(COLS))}{last}"
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth = 1
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.page_setup.fitToHeight = 0
    return ws


def _plana(wb, nombre, productos, E):
    ws = wb.create_sheet(nombre)
    ws.sheet_properties.outlinePr.summaryBelow = False
    todas = []
    for cod, filas in productos:
        todas += _grupos([dict(f) for f in filas], cod)
    last, _, _ = _tabla(ws, todas, 1, E, prod_col=True, outline=False)
    ws.freeze_panes = "D2"
    ws.auto_filter.ref = f"A1:P{last}"
    return ws


def _mp_clave(f):
    """Clave de agregación de materia prima para la explosión."""
    d, um = f["desc"], f["um"]
    if f["nivel"] == 3:
        if f["codigo"] == "MP-HOJA":
            return (f"Chapa {d.split('Recorte de hoja ')[1]}", "kg", f["peso"] * f["cant"])
        if f["codigo"] == "MP-FLEJE":
            return (d.split(" (paso")[0], "m", f["cant"])
        if f["codigo"] == "MP-CANO":
            return (d.split(" (")[0], "barra 6 m", f["cant"])
        if f["codigo"] == "MP-CUELLO":
            return (f"Cuello roscado {f['med']}", "u", f["cant"])
    if f["nivel"] != 2:
        return None
    suf = f["codigo"].split("-")[-1]
    if suf in ("C1", "C2", "C3", "C4", "A1", "A1b", "A2", "E1", "E3", "E4", "I1", "I3", "I4", "V1"):
        nom = d if suf != "E1" else f"{d} {f['med']}"
        return (nom, um, f["cant"])
    if f["ori"].startswith("Compra") and f["sub"] in (2, 3, 4) and f["cant"]:
        return (f"{d} ({f['plano'][7:] if f['plano'] else ''})", um, f["cant"])
    return None


def _explosion(wb, productos, E):
    ws = wb.create_sheet("Explosion_MP")
    claves, tabla = [], {}
    for cod, filas in productos:
        for f in filas:
            k = _mp_clave(f)
            if not k or k[2] in (None, 0):
                continue
            kk = (k[0], k[1])
            if kk not in tabla:
                claves.append(kk)
                tabla[kk] = {}
            tabla[kk][cod] = tabla[kk].get(cod, 0) + k[2]
    cods = [c for c, _ in productos]
    ws.cell(1, 1, "Explosión de materia prima e insumos por unidad de producto terminado "
                  "(suma de niveles 2 y 3 de cada BOM; piezas compradas de válvula/descarga/carro al final)")
    ws.cell(1, 1).font = E["Font"](bold=True, size=12)
    cab = ["Material / insumo", "UM"] + [c.replace("FL_MAT_", "") for c in cods]
    for j, t in enumerate(cab, 1):
        c = ws.cell(3, j, t)
        c.font = E["Font"](bold=True, color="FFFFFF")
        c.fill = E["cab"]
        c.alignment = E["Al"](wrap_text=True, vertical="center")
        ws.column_dimensions[c.column_letter].width = 58 if j == 1 else (8 if j == 2 else 11)
    orden = sorted(claves, key=lambda k: (0 if k[0].startswith(("Chapa", "Fleje", "Caño", "Cuello")) else
                                          1 if not k[0].endswith(")") or "Ar +" in k[0] else 2, k[0]))
    for i, kk in enumerate(orden, 4):
        ws.cell(i, 1, kk[0])
        ws.cell(i, 2, kk[1])
        for j, c in enumerate(cods, 3):
            v = tabla[kk].get(c)
            if v:
                ws.cell(i, j, round(v, 4)).number_format = "0.###"
    ws.freeze_panes = "C4"
    ws.auto_filter.ref = f"A3:{ws.cell(3, len(cab)).column_letter}{3 + len(orden)}"
    return ws


def _resumen(wb, productos, E):
    ws = wb.create_sheet("Resumen", 1)
    cab = ["Plano", "Producto", "Familia", "Fabricación", "Norma IRAM", "Agente", "Carga", "UM", "Gas impulsor",
           "Gas (kg)", "Peso vacío S1-S4 (kg)", "Peso cargado (kg)", "Peso catálogo (kg)", "Desvío", "Piezas del plano",
           "Ítems BOM", "Recipiente suelto", "Hoja", "Tara catálogo (kg) = catálogo - carga - gas",
           "Desvío de tara (modelo vs catálogo)"]
    for j, t in enumerate(cab, 1):
        c = ws.cell(1, j, t)
        c.font = E["Font"](bold=True, color="FFFFFF")
        c.fill = E["cab"]
        c.alignment = E["Al"](wrap_text=True, vertical="center")
        ws.column_dimensions[c.column_letter].width = [18, 40, 9, 16, 11, 40, 7, 5, 13, 8, 10, 10, 10, 8, 8, 8, 18, 8,
                                                       14, 12][j - 1]
    ws.row_dimensions[1].height = 32
    for i, (m, filas) in enumerate(productos, 2):
        ag, q, um, n_ag, gas, m_gas, nm3, libre = carga(m)
        n_p = sum(1 for f in filas if f["nivel"] == 2 and f["codigo"][-2:].isdigit())
        sh = m.codigo[:31]
        vals = [m.codigo, m.nombre, m.familia, "Propia" if m.codigo in PROPIOS else "Tercerizado S4",
                m.spec["Norma IRAM extintor"], ag, q, um, gas, round(m_gas, 4) or None,
                f"='{sh}'!G3", f"='{sh}'!G4", float(m.spec["Peso cargado (kg)"].replace(",", ".")),
                f"=L{i}/M{i}-1", n_p, len(filas),
                m.codigo.replace("FL_MAT_", "FL_REC_") if m.codigo.startswith("FL_MAT_ABC") else "-", None]
        for j, v in enumerate(vals, 1):
            c = ws.cell(i, j, v)
            c.border = E["borde"]
        _, obj, _ = tolerancia(m)
        kg_carga = obj if um == "kg" else q * {"AGUA": 1.0, "AFFF": 1.0, "K": 1.35}.get(_agente(m), 1.0)
        ws.cell(i, 7, round(obj, 3))
        ws.cell(i, 19, f"=M{i}-{round(kg_carga, 3)}-J{i}" if m_gas else f"=M{i}-{round(kg_carga, 3)}")
        ws.cell(i, 20, f"=(L{i}-{round(kg_carga, 3)}-J{i})/S{i}-1" if m_gas else f"=(L{i}-{round(kg_carga, 3)})/S{i}-1")
        ws.cell(i, 19).number_format = "0.00"
        ws.cell(i, 20).number_format = "0.0%"
        ws.cell(i, 18).hyperlink = f"#'{sh}'!A1"
        ws.cell(i, 18, "ir »").font = E["Font"](color="0563C1", underline="single")
        for j in (11, 12):
            ws.cell(i, j).number_format = "0.00"
        ws.cell(i, 14).number_format = "0.0%"
    ws.freeze_panes = "C2"
    ws.auto_filter.ref = f"A1:T{1 + len(productos)}"
    return ws


def _carga_n2(wb, E):
    ws = wb.create_sheet("Carga_N2", 2)
    ws["A1"] = ("Carga de agente y gas impulsor por extintor - la capacidad es la MASA de agente (IRAM 3523 2.2); "
                "el N₂ no es una concentración: es la masa que da la presión de servicio a 20 °C en el volumen libre")
    ws["A1"].font = E["Font"](bold=True, size=12)
    notas = ["Carga: nominal del catálogo con la tolerancia de IRAM 3517-2:2020 tabla 3 / IRAM 3523 tabla II. Si la "
             "tolerancia es sólo positiva se carga al centro de la banda (p. ej. 10 kg → 10,15 kg).",
             "N₂ (o argón en HCFC, tabla 2 de 3517-2): m = (Ps + 0,101 MPa) × V libre / (R × 293,15 K) × M. "
             "V libre = V recipiente - carga / densidad aparente (R). Ps a 20 °C ± 2 °C (IRAM 3523 2.3), < 1,7 MPa (4.7).",
             "CO₂: no lleva gas impulsor; se controla el grado de llenado (kg de CO₂ por dm³ de recipiente)."]
    for i, n in enumerate(notas, 2):
        ws.cell(i, 1, "• " + n)
    cab = ["Plano", "Agente", "Norma ext.", "Carga nominal", "UM", "Tolerancia", "Carga objetivo", "Referencia",
           "V recipiente (dm³)", "Densidad aparente (kg/dm³)", "V agente (dm³)", "V libre (dm³)", "V libre (%)",
           "Ps (MPa a 20 °C)", "Gas", "Gas (g)", "Gas (L normales)", "g de gas por kg / L de agente", "Observaciones"]
    w = [20, 40, 9, 9, 5, 11, 10, 30, 10, 10, 9, 9, 8, 9, 9, 8, 9, 10, 60]
    for j, (t, ww) in enumerate(zip(cab, w), 1):
        c = ws.cell(6, j, t)
        c.font = E["Font"](bold=True, color="FFFFFF")
        c.fill = E["cab"]
        c.alignment = E["Al"](wrap_text=True, vertical="center")
        ws.column_dimensions[c.column_letter].width = ww
    ws.row_dimensions[6].height = 45
    for i, fila in enumerate(tabla_carga(), 7):
        for j, v in enumerate(fila, 1):
            c = ws.cell(i, j, v)
            c.border = E["borde"]
        ws.cell(i, 13).number_format = "0.0%"
        if fila[-1].startswith("OJO"):
            ws.cell(i, 19).font = E["Font"](bold=True, color="C00000")
    ws.freeze_panes = "B7"
    return ws


def _recargas(wb, E):
    ws = wb.create_sheet("Recargas")
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
        "Porcentajes de merma (3 % polvo, 2 % HCFC) = valores R a medir en planta con la balanza de RC-CQ.",
    ]
    for i, n in enumerate(notas, 2):
        ws.cell(i, 1, "• " + n).alignment = E["Al"](wrap_text=True, vertical="top")
        ws.merge_cells(start_row=i, start_column=1, end_row=i, end_column=9)
        ws.row_dimensions[i].height = 44
    r0 = 2 + len(notas) + 1
    cab = ["Código kit", "Plano", "Extintor", "Caso", "Ítem", "Cant.", "UM", "Estado / origen", "Referencia"]
    anchos = [16, 20, 36, 44, 48, 9, 6, 48, 52]
    for j, (t, w) in enumerate(zip(cab, anchos), 1):
        c = ws.cell(r0, j, t)
        c.font = E["Font"](bold=True, color="FFFFFF")
        c.fill = E["cab"]
        ws.column_dimensions[c.column_letter].width = w
    r = r0
    for f in recargas():
        r += 1
        m = next(x for x in MODELOS if x.codigo == f[0])
        letra = f[2][0] if f[2][1:3] == " -" else "I"
        vals = [f"RK-{P.codigo_pieza(m, 0)[:-3]}-{letra}"] + f
        for j, v in enumerate(vals, 1):
            c = ws.cell(r, j, v)
            c.border = E["borde"]
            c.alignment = E["Al"](wrap_text=j in (4, 5, 8, 9), vertical="top")
    ws.freeze_panes = ws.cell(r0 + 1, 4)
    ws.auto_filter.ref = f"A{r0}:I{r}"
    return ws


def _leeme(wb, E, n_term, n_cil):
    ws = wb.active
    ws.title = "LEEME"
    ws.column_dimensions["A"].width = 26
    ws.column_dimensions["B"].width = 120
    t = [("FLAMA S.A. - BOM de matafuegos y cilindros", None),
         ("Origen", "Generado por código (python generar.py --bom) a partir del MISMO modelo 3D que los planos "
                    "FL_MAT_* y FL_REC_*: código de pieza, posición, denominación y material son los de la lista de "
                    "piezas de cada plano; medida y peso se miden sobre el sólido."),
         ("Hojas", f"Resumen · BOM_Terminados ({n_term} productos, tabla plana filtrable) · BOM_Cilindros ({n_cil} "
                   "recipientes FL_REC) · una hoja por plano (BOM multinivel plegable) · Recargas · Explosion_MP · "
                   "Despiece (planos FL_DES)"),
         ("Niveles", "0 producto (= plano) · 1 subconjunto · 2 pieza o insumo · 3 materia prima de la pieza "
                     "fabricada (gris; NO suma al peso porque ya está en la pieza)"),
         ("Subconjuntos", " · ".join(f"S{k} {v}" for k, v in NOMBRE_SUB.items()) +
          ". En los ABC el S1 es el plano FL_REC_* (el mismo recipiente que se vende suelto)."),
         ("Peso unitario", "kg por unidad de medida. Peso total = Cant. × Peso unit. (fórmula). Subconjunto = "
                           "suma de sus piezas. Consumibles: aporte = fracción depositada, pintura = 65 % depositado, "
                           "granalla y gas de protección no quedan en el producto."),
         ("Códigos", "ABC10-01… = pieza del plano (posición 01). ABC10-S1…S7 subconjuntos. Sufijos: C consumible "
                     "de recipiente, V interno de válvula (no dibujado), A carga, I identificación, E embalaje, "
                     "T cilindro suelto. MP-* materia prima. RK-*-A/B/C kits de recarga.")]
    t += [(f"Fuente {k}", v) for k, v in FUENTES.items()]
    t += [("Para definir", None),
          ("1. Espesores", "Hoja de corte (layout) vs plano: cuerpo 70 y 100 kg LAC e=4,75 en la hoja de corte y "
                           "e=3,2 en el plano; cúpula 10 kg fleje e=2,0 y plano e=1,6. Marcado «OJO» en el nivel 3."),
          ("2. Válvula", "Hoy la válvula es un subconjunto (S2) con sus piezas. Si se compra armada (lo habitual) "
                         "conviene pasarla a un único código comprado con su propio plano de proveedor."),
          ("3. Tercerizados", "Agua, AFFF, Sales K, CO₂ y HCFC se compran terminados (S4): su BOM es de referencia "
                              "para repuestos y recarga, no de fabricación."),
          ("4. Recargas", "Mermas de polvo y HCFC (R) a medir. Ver hoja Recargas."),
          ("Normas", "IRAM 3517-2:2020, IRAM 3504:2001 y las IRAM de producto citadas. Los PDF de las normas tienen "
                     "licencia monousuario: se citan apartados, no se transcribe texto.")]
    for i, (a, b) in enumerate(t, 1):
        ws.cell(i, 1, a).font = E["Font"](bold=True, size=14 if i == 1 else 11)
        if b:
            c = ws.cell(i, 2, b)
            c.alignment = E["Al"](wrap_text=True, vertical="top")
            ws.row_dimensions[i].height = max(18, 15 * (len(b) // 110 + 1))


def _despiece_hoja(wb, productos, E):
    ws = wb.create_sheet("Despiece")
    cab = ["Plano de despiece", "Producto", "Subconjuntos", "Globos (códigos BOM)", "Archivo"]
    for j, (t, w) in enumerate(zip(cab, [24, 40, 50, 60, 40]), 1):
        c = ws.cell(1, j, t)
        c.font = E["Font"](bold=True, color="FFFFFF")
        c.fill = E["cab"]
        ws.column_dimensions[c.column_letter].width = w
    for i, (m, filas) in enumerate(productos, 2):
        cod = "FL_DES_" + m.codigo[7:]
        subs = ", ".join(f["codigo"].split("-")[-1] + " " + f["desc"] for f in filas if f["nivel"] == 1
                         and f["sub"] <= 4)
        glob = ", ".join(f["codigo"].split("-")[-1] for f in filas if f["nivel"] == 2 and f["sub"] <= 4)
        for j, v in enumerate([cod, m.nombre, subs, glob, f"salida/despiece/{cod}.pdf"], 1):
            ws.cell(i, j, v).alignment = E["Al"](wrap_text=True, vertical="top")


def excel(ruta):
    from openpyxl import Workbook
    from . import recipientes as RC
    E = _estilos()
    wb = Workbook()
    term = [(m, bom_producto(m)) for m in MODELOS]
    cil = [(m, bom_producto(m, cilindro=True)) for m in RC.modelos_abc()]
    _leeme(wb, E, len(term), len(cil))
    _resumen(wb, term, E)
    _carga_n2(wb, E)
    _plana(wb, "BOM_Terminados", [(m.codigo, f) for m, f in term], E)
    _plana(wb, "BOM_Cilindros", [(RC.codigo_rec(m), f) for m, f in cil], E)
    for m, f in term:
        _hoja_producto(wb, m, f, E)
    for m, f in cil:
        _hoja_producto(wb, m, f, E, cilindro=True)
    _recargas(wb, E)
    _explosion(wb, [(m.codigo, f) for m, f in term], E)
    _despiece_hoja(wb, term, E)
    wb.save(ruta)
    return term, cil
