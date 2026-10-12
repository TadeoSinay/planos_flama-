"""BOM de FLAMA para leer: sólo la estructura de cada producto y sus números (salida/bom/FLAMA_BOM.xlsx).

Hojas
  Fabricados  los 8 ABC propios; al final de cada uno, lo que se agrega si va como sustituto (IRAM 3517-2 9.4.5)
  Revendidos  los 9 equipos que se compran terminados, con el mismo agregado de sustituto
  Cilindros   los 8 recipientes ABC vendidos sueltos (planos FL_REC)
  Recargas    por extintor, los servicios de la IRAM 3517-2:2020: control periódico (8.2, trimestral),
              mantenimiento (9.2.1, anual), recarga (9.2.2, después de cada uso) y ensayo hidrostático (9.7 y
              anexo E: cada 5 años en polvo, CO₂ y gases; cada 2 en agua, AFFF y sales de potasio)

Columnas: Nivel, Código, Pieza, Cant., UM, Densidad (kg/L), Volumen total (L), Masa unit. (kg), Masa total (kg).
El volumen es el de la cantidad del renglón (cantidad × volumen de una unidad), igual que la masa total.
  piezas    volumen del material = masa del modelo 3D / densidad del material
  polvos    densidad del polvo asentado en el recipiente; volumen = masa / densidad
  líquidos  la cantidad va en litros; masa = litros × densidad
  CO₂       densidad = relación de llenado (kg de CO₂ por litro de cilindro); volumen = capacidad del cilindro
  gases     masa en kg; volumen en litros normales (0 °C, 101,325 kPa); densidad normal del gas

No lleva insumos de proceso (soldadura, granalla, pintura), embalaje ni materia prima: siguen en bom.py, que es lo
que usa el MRP, y en el libro completo de respaldo (salida/bom/respaldo/FLAMA_BOM_respaldo.xlsx). La justificación de
cada valor está en el Word «Justificación del BOM».
"""
import re

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

from . import bom as B
from . import recipientes as RC
from . import sustituto as SU
from .catalogo import MODELOS

CAB = ["Nivel", "Código", "Pieza", "Cant.", "UM", "Densidad (kg/L)", "Volumen total (L)", "Masa unit. (kg)",
       "Masa total (kg)"]
ANCHO = [7, 19, 46, 9, 6, 11, 11, 11, 11]
FMT = [None, None, None, "0.####", None, "0.#####", "[<0.001]0.0000;0.000", "[<0.001]0.0000;0.000",
       "[<0.001]0.0000;0.000"]
NEGRO, GRIS_O, GRIS_C, BLANCO = "000000", "595959", "E7E6E6", "FFFFFF"
VOL_MOLAR_N = 22.414                     # L/mol en condiciones normales (0 °C, 101,325 kPa)

INTERVALO_PH = {"3523": 5, "3550": 5, "3509": 5, "3565": 5, "3504": 5,
                "3525": 2, "3527": 2, "3537": 2, "3541": 2, "3694": 2, "3693": 2}    # años, anexo E


def _corto(s):
    """Nombre corto: sin normas, fuentes ni aclaraciones entre paréntesis (salvo cuántas piezas son o el tramo)."""
    s = str(s).split(" — ")[0].split(", ")[0].split(" - ")[0].split(" c/")[0]
    s = re.sub(r" \((?!\d+\)|tramo enrollado\)).*", "", s)
    for a, b in (("Polvo químico seco", "Polvo"), ("Tarjeta de identificación DPS con sello", "Tarjeta DPS")):
        s = s.replace(a, b)
    return s.strip()[:48]


def _fila(niv, cod, pieza, cant, um, rho=None, vol=None, mu=None):
    """[nivel, código, pieza, cant, um, densidad, volumen total, masa unit., masa total]; vol es el de una unidad."""
    mt = None if mu is None or cant is None else cant * mu
    vt = None if vol is None or cant is None else cant * vol
    return [niv, cod, pieza, cant, um, rho, vt, mu, mt]


def _es_insumo(r):
    return (r["nivel"] >= 3 or re.search(r"-(C\d+|S0)$", str(r["codigo"])) or r["sub"] == 7 or
            str(r["ori"]).startswith("Proceso") or not r["cant"])


def agente(m, cant=None):
    """(pieza, UM, densidad, volumen por UM, masa por UM) del agente del modelo; cant en su UM (por defecto la
    carga objetivo del BOM)."""
    ag = B._agente(m)
    nombre, q, um, *_ = B.carga(m)
    _, obj, _ = B.tolerancia(m)
    if ag == "CO2":
        V = float(m.geo["vol_dm3"])
        return "Dióxido de carbono", "kg", q / V, V / q, 1.0
    if um == "L":
        rho = B.RHO_AGENTE.get(ag, 1.0)
        return _corto(nombre), "L", rho, 1.0, rho
    rho = B.RHO_EMPACADA.get(ag, B.RHO_AGENTE[ag])
    return _corto(nombre), "kg", rho, 1.0 / rho, 1.0


def gas(m):
    """(pieza, densidad normal kg/L, kg por carga completa) del gas impulsor, o None si es autopresurizado."""
    _, _, _, _, g, m_gas, nm3, _ = B.carga(m)
    if str(g).startswith("-") or not m_gas:
        return None
    return f"Gas impulsor: {g}", B.MOLAR[g] / VOL_MOLAR_N, m_gas


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


def estructura(m, cilindro=False):
    """Filas de la estructura del producto con densidad, volumen y masa; sin insumos."""
    out = []
    for r in _anidar([r for r in B.bom_producto(m, cilindro=cilindro) if not _es_insumo(r)]):
        cod, cant, um, peso = r["codigo"], r["cant"], r["um"], r["peso"]
        pieza = _corto(r["desc"]) if r["nivel"] else r["desc"].split(" - ")[0]
        if re.search(r"-A1b?$", cod):                        # agente
            if B._agente(m) == "AFFF":
                rho = B.RHO_AFFF_CONC if cod.endswith("b") else 1.0
                out.append(_fila(2, cod, "Concentrado AFFF 3 %" if cod.endswith("b") else "Agua (premezcla)",
                                 cant, "L", rho, 1.0, rho))
            else:
                pz, um_, rho, vol, mu = agente(m)
                out.append(_fila(2, cod, pz, cant, um_, rho, vol, mu))
        elif cod.endswith("-A2"):                             # gas impulsor
            pz, rho, _ = gas(m)
            out.append(_fila(2, cod, pz + " (L normales)", cant, "kg", rho, 1.0 / rho, 1.0))
        elif r["nivel"] >= 2 and peso and r.get("rho"):       # pieza del modelo 3D
            out.append(_fila(r["nivel"], cod, pieza, cant, um, r["rho"], peso / r["rho"], peso))
        else:
            out.append(_fila(r["nivel"], cod, pieza, cant, um, None, None, peso if r["nivel"] >= 2 else None))
    return _sumar(out)


def _sumar(out):
    """Masa de los renglones que agrupan (producto, subconjunto, compra armada) = suma de la masa total de sus hijos
    directos."""
    for i in range(len(out) - 1, -1, -1):
        tiene_hijos = i + 1 < len(out) and out[i + 1][0] > out[i][0]
        if tiene_hijos and out[i][7] is None:
            tot, j = 0.0, i + 1
            while j < len(out) and out[j][0] > out[i][0]:
                if out[j][0] == out[i][0] + 1 and out[j][8]:
                    tot += out[j][8]
                j += 1
            out[i][8] = round(tot, 4) if tot else None
            if out[i][0] >= 2 and tot:                    # compra armada: masa unitaria = la de sus piezas
                out[i][7] = round(tot / out[i][3], 4)
    return out


def sustituto(m):
    filas = [r for r in SU.bom_sustituto(m) if r["nivel"] == 2]
    if not filas:
        return []
    out = [_fila(1, m.codigo.replace("FL_MAT_", "FL_SUS_"), "Si va como sustituto, se agrega", 1, "u")]
    for r in filas:
        kg = r["peso"] if isinstance(r.get("peso"), (int, float)) else None
        out.append(_fila(2, r["codigo"], _corto(r["desc"]), r["cant"], r["um"].split("/")[0], None, None, kg))
    return out


# ------------------------------------------------------------------ recargas por servicio (IRAM 3517-2:2020)
def servicios(m):
    """Bloques [(título, filas)] de los cuatro servicios del modelo."""
    n = m.spec["Norma IRAM extintor"]
    ag = B._agente(m)
    _, q, um, *_ = B.carga(m)
    _, obj, _ = B.tolerancia(m)                       # carga objetivo: centro de la banda de tolerancia
    base = m.codigo.replace("FL_MAT_", "RK_")
    pz, um_ag, rho, vol, mu = agente(m)
    g = gas(m)
    co2, liquido = ag == "CO2", um == "L"

    def carga_ag(cant, pref=""):
        if ag == "AFFF":
            return [_fila(2, f"{base}-{pref}A1b", "Concentrado AFFF 3 %", round(cant * 0.03, 3), "L", B.RHO_AFFF_CONC,
                          1.0, B.RHO_AFFF_CONC),
                    _fila(2, f"{base}-{pref}A1", "Agua (premezcla)", round(cant * 0.97, 3), "L", 1.0, 1.0, 1.0)]
        return [_fila(2, f"{base}-{pref}A1", pz + (" recuperado" if pref == "R" else ""), round(cant, 4), um_ag,
                      rho, vol, mu)]

    def gas_lleno():
        if not g:
            return []
        return [_fila(2, f"{base}-A2", g[0] + " (L normales)", round(g[2], 4), "kg", g[1], 1.0 / g[1], 1.0)]

    def ident(junta=True, marbete=True):
        f = [_fila(2, f"{base}-P1", "Precinto con identificación del recargador", 1, "u"),       # 9.4.13
             _fila(2, f"{base}-P2", "Etiqueta de servicio del recargador", 1, "u"),               # 9.4.14
             _fila(2, f"{base}-P3", "Estampilla y oblea de recarga (PBA)", 1, "u"),              # Res. 522/07 an. 5-6
             _fila(2, f"{base}-P4", "Tarjeta de identificación DPS (PBA)", 1, "u"),              # Res. 349/07 art. 21
             _fila(2, f"{base}-P5", "Tarjeta de identificación AGC (CABA)", 1, "u")]             # Ord. 40.473 art. 6
        if marbete:
            f.insert(1, _fila(2, f"{base}-P6", "Marbete indicador", 1, "u"))                      # 9.6, anexo E
        if junta:
            f.append(_fila(2, f"{base}-P7", "Junta tórica de asiento del cuello", 1, "u"))
        return f

    repo = B.reposicion(m)                             # objetivo − límite inferior de la tabla 3; None en líquidos
    años = INTERVALO_PH.get(n, 5)
    bloques = [("Control periódico (trimestral)", [_fila(2, f"{base}-C1", "Etiqueta de control (celeste 35 × 50)", 1,
                                                         "u")])]
    if liquido:
        mant = carga_ag(obj) + gas_lleno() + ident()
    elif co2:
        mant = carga_ag(repo) + ident(junta=False, marbete=False)
    else:
        mant = carga_ag(repo) + gas_lleno() + ident()
    bloques.append(("Mantenimiento (anual)", mant))
    rec = carga_ag(obj) + gas_lleno() + ident(junta=not co2, marbete=not co2)
    if co2:
        rec.append(_fila(2, f"{base}-S1", "Conjunto de seguridad (disco)", 1, "u"))
    bloques.append(("Recarga (después de cada uso)", rec))
    if co2:
        ph = (carga_ag(obj, "R") + [_fila(2, f"{base}-S1", "Conjunto de seguridad (disco)", 1, "u"),
                                 _fila(2, f"{base}-P6", "Marbete indicador", 1, "u"),
                                 _fila(2, f"{base}-P7", "Junta tórica de asiento del cuello", 1, "u")])
    elif liquido:
        ph = [_fila(2, f"{base}-H1", "Oblea de vencimiento de la prueba hidráulica", 1, "u")]
    else:
        ph = carga_ag(obj - repo, "R") + [_fila(2, f"{base}-H1", "Oblea de vencimiento de la prueba hidráulica", 1, "u")]
    bloques.append((f"Ensayo hidrostático (cada {años} años, se suma al mantenimiento)", ph))
    return bloques


def recargas_modelo(m):
    out = [_fila(0, m.codigo.replace("FL_MAT_", "RK_"), m.nombre, 1, "u")]
    for i, (tit, filas) in enumerate(servicios(m), 1):
        out.append(_fila(1, f"{out[0][1]}-{i}", tit, 1, "servicio"))
        out += filas
    for f in out:
        if f[0] == 2 and f[8] is None and f[7] is not None:
            f[8] = f[3] * f[7]
    _sumar(out)
    out[0][8] = None                  # los servicios no se suman entre sí
    return out


# ------------------------------------------------------------------ Excel
def _hoja(wb, titulo, bloques):
    ws = wb.create_sheet(titulo)
    ws.append(CAB)
    for i, (w, c) in enumerate(zip(ANCHO, CAB), 1):
        col = ws.cell(1, i).column_letter
        ws.column_dimensions[col].width = w
        cel = ws.cell(1, i)
        cel.font = Font(name="Arial", size=10, bold=True, color=BLANCO)
        cel.fill = PatternFill("solid", fgColor=NEGRO)
        cel.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.row_dimensions[1].height = 30
    fino = Side(style="thin", color="BFBFBF")
    for filas in bloques:
        for f in filas:
            ws.append(f)
            r = ws.max_row
            niv = f[0]
            ws.row_dimensions[r].outline_level = min(niv, 7)
            for i in range(1, len(CAB) + 1):
                c = ws.cell(r, i)
                c.border = Border(bottom=fino)
                if FMT[i - 1]:
                    c.number_format = FMT[i - 1]
                c.font = Font(name="Arial", size=10)
                if niv == 0:
                    c.font = Font(name="Arial", size=10, bold=True, color=BLANCO)
                    c.fill = PatternFill("solid", fgColor=GRIS_O)
                elif niv == 1:
                    c.font = Font(name="Arial", size=10, bold=True)
                    c.fill = PatternFill("solid", fgColor=GRIS_C)
            ws.cell(r, 1).alignment = ws.cell(r, 5).alignment = Alignment(horizontal="center")
            ws.cell(r, 3).alignment = Alignment(indent=2 * niv)
        ws.append([])
    ws.sheet_properties.outlinePr.summaryBelow = False
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:{ws.cell(1, len(CAB)).column_letter}{ws.max_row}"
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth, ws.page_setup.fitToHeight = 1, 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.print_title_rows = "1:1"
    return ws


def excel(ruta):
    wb = Workbook()
    wb.remove(wb.active)
    fab = [m for m in MODELOS if m.codigo in B.PROPIOS]
    rev = [m for m in MODELOS if m.codigo not in B.PROPIOS]
    _hoja(wb, "Fabricados", [estructura(m) + _sumar(sustituto(m)) for m in fab])
    _hoja(wb, "Revendidos", [estructura(m) + _sumar(sustituto(m)) for m in rev])
    _hoja(wb, "Cilindros", [estructura(m, cilindro=True) for m in RC.modelos_abc()])
    _hoja(wb, "Recargas", [recargas_modelo(m) for m in fab + rev])
    wb.save(ruta)
    return [(ws.title, ws.max_row) for ws in wb.worksheets]
