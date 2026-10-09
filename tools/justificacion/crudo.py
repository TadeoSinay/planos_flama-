"""Valores crudos pieza a pieza de los planos FL_MAT / FL_REC, con la clave de su fuente.

Salida: crudo.json = lista de filas
  modelo, plano, pos, pieza, cant, material, dim, valor, unidad, tipo, src (claves de marca), calc, code, estado
"""
import json
import math
import os
import sys

sys.path.insert(0, "/home/user/planos_flama-")
os.chdir("/home/user/planos_flama-")
from flama import perfiles_valvula as PV  # noqa: E402
from flama import modelo3d as M, planos as P, materiales as MAT, bom as B  # noqa: E402
from flama.catalogo import MODELOS  # noqa: E402

FADESA_REC = {"1 kg": "1kg", "2,5 kg": "2.5kg", "5 kg": "5kg", "10 kg": "10kg", "25 kg": "25kg", "50 kg": "50kg"}
# modelos que usan el recipiente de un plano Fadesa (BC, HCFC = 5 kg; Clase D = 10 kg; AFFF 50 l = 50 kg)
REC_DE = {"FL_MAT_ABC_1kg": "1kg", "FL_MAT_ABC_2.5kg": "2.5kg", "FL_MAT_ABC_5kg": "5kg", "FL_MAT_ABC_10kg": "10kg",
          "FL_MAT_BC_5kg": "5kg", "FL_MAT_HCFC-HFC_5kg": "5kg", "FL_MAT_CLASED_9l": "10kg",
          "FL_MAT_ABC_25kg": "25kg", "FL_MAT_ABC_50kg": "50kg", "FL_MAT_AFFF_50l": "50kg"}
PROPIOS = B.PROPIOS

T_FAD, T_CAT, T_NOR, T_MP, T_REL, T_CAL, T_DIS, T_DER, T_FIC, T_PRO = (
    "Plano Fadesa", "Catálogo Fadesa", "Norma / resolución", "Planilla MP FLAMA", "Relevamiento de mercado",
    "Cálculo", "Diseño FLAMA (supuesto)", "Derivado (a validar)", "Ficha técnica de mercado", "Proceso FLAMA")
# tabla 0 del proceso de carros: Ø, chapa y alto del cuerpo
PC_T0 = {"25 kg": (276.5, 3.2, 490), "50 kg": (320, 3.2, 640), "70 kg": (390, 4.75, 680), "100 kg": (390, 4.75, 900)}
# detalle de las uniones medido en el plano Fadesa de recipiente (1:1)
FD_DET = {"1kg": "1kg", "2.5kg": "5kg", "5kg": "5kg", "10kg": "5kg", "25kg": "25kg", "50kg": "25kg"}

rows = []
FE_PROPIO = {"FL_MAT_ABC_1kg": "1 kg", "FL_MAT_ABC_2.5kg": "2,5 kg", "FL_MAT_ABC_5kg": "5 kg", "FL_MAT_ABC_10kg": "10 kg",
             "FL_MAT_ABC_25kg": "25 kg", "FL_MAT_ABC_50kg": "50 kg", "FL_MAT_ABC_70kg": "50 kg", "FL_MAT_ABC_100kg": "100 kg"}


def plan_fe(m):
    """Plano Fadesa de extintor completo del que se midieron válvula y accesorios."""
    if m.codigo in FE_PROPIO:
        return FE_PROPIO[m.codigo]
    return {"F510": "1 kg", "F192": "5 kg", "G763": "50 kg"}[M.tipo_valvula(m)]


def r1(v, d=1):
    return round(float(v), d)


def add(m, plano, pos, pieza, cant, mat, dim, valor, unidad, tipo, src, calc, code, estado=""):
    if estado == "":
        estado = {T_DIS: "E", T_DER: "A", T_REL: "A"}.get(tipo, "V")
    rows.append(dict(modelo=m.codigo, plano=plano, pos=pos, pieza=pieza, cant=cant, material=mat, dim=dim,
                     valor=valor, unidad=unidad, tipo=tipo, src=src, calc=calc, code=code, estado=estado))


def bb(s):
    b = s.BoundingBox()
    return b.xlen, b.ylen, b.zlen


for m in MODELOS:
    g = dict(m.geo)
    piezas, info = M.construir(m)
    filas, orden, total = P.lista(m, piezas)
    dr = info["recipiente"]
    R = g["R"]
    D = 2 * R
    fam = m.familia
    rod = fam == "rodante"
    rec = REC_DE.get(m.codigo)
    tam = m.capacidad
    pl = m.codigo
    cod = m.codigo

    # ------------------------------------------------ conjunto
    bx = M.bbox(piezas)
    for dim, val, campo in (("Altura total", bx.zmax - bx.zmin, "Altura"), ("Ancho total", bx.xlen, "Ancho"),
                            ("Profundidad total", bx.ylen, "Profundidad")):
        cat_v = {"Altura": m.H, "Ancho": m.W, "Profundidad": m.D}[campo]
        if rod and campo == "Altura":
            add(m, pl, "0", "Conjunto", 1, "-", dim, r1(val), "mm", T_CAT, [f"CAT:{cod}:{campo}"],
                "Agarre de la manija del carro a la altura del catálogo", ("modelo3d.py", "zg = H - rt"))
        elif rod:
            dif = 100 * (val - cat_v) / cat_v
            add(m, pl, "0", "Conjunto", 1, "-", dim, r1(val), "mm", T_CAL, ["N:3550T3", f"CAT:{cod}:{campo}"],
                (f"Resulta del tren de rodaje IRAM 3550 (trocha {info['track']:g}, banda {info['bw_w']:g})" if campo == "Ancho"
                 else "Resulta de la tercera pata adelante y de la rueda con el eje detrás del cuerpo") +
                f" (catálogo: {cat_v:g}; diferencia {dif:+.0f} %)", ("modelo3d.py", "def construir"))
        else:
            add(m, pl, "0", "Conjunto", 1, "-", dim, r1(val), "mm", T_CAL,
                [f"FE:{plan_fe(m)}:valvula", f"CAT:{cod}:{campo}"],
                f"Resulta de las piezas medidas en el plano Fadesa (catálogo: {cat_v:g}; diferencia "
                f"{100 * (val - cat_v) / cat_v:+.0f} %)", ("modelo3d.py", "def construir"))
    add(m, pl, "0", "Conjunto", 1, "-", "Peso cargado según catálogo", float(m.spec["Peso cargado (kg)"]
        .replace(".", "").replace(",", ".")), "kg", T_CAT, [f"CAT:{cod}:Peso"], "Transcripto del catálogo",
        ("catalogo.py", f'Modelo("{cod}"'))
    add(m, pl, "0", "Conjunto", 1, "-", "Equipo vacío (suma de la lista de materiales)", r1(total, 2), "kg", T_CAL,
        ["C:materiales"], "Σ (volumen del sólido × densidad × factor de llenado) de cada pieza de la lista",
        ("materiales.py", "def peso"))
    if cod in B.REF_PESO:
        v, f = B.REF_PESO[cod]
        key = {"FL_MAT_ABC_70kg": "GE:70kg:masa", "FL_MAT_SALESK_6l": "ME:6l:masa"}.get(cod, f"FE:{tam}:masa")
        tipo = T_FIC if cod in ("FL_MAT_ABC_70kg", "FL_MAT_SALESK_6l") else T_FAD
        add(m, pl, "0", "Conjunto", 1, "-", "Masa total de referencia (verificación)", v, "kg", tipo, [key],
            f"Referencia de verificación de masa del BOM: {f}", ("bom.py", "REF_PESO = {"))
    if rod:
        add(m, pl, "0", "Conjunto", 1, "-", "Diámetro de rueda", float(m.spec["Diámetro de rueda (mm)"]), "mm",
            T_CAT, [f"CAT:{cod}:Rueda"], "Transcripto del catálogo", ("catalogo.py", f'Modelo("{cod}"'))
        add(m, pl, "0", "Conjunto", 1, "-", "Longitud de manga", float(m.spec["Longitud de manga (m)"]), "m",
            T_CAT, [f"CAT:{cod}:Manga"], "Transcripto del catálogo (el plano dibuja el tramo enrollado)",
            ("catalogo.py", f'Modelo("{cod}"'))
    for dim, campo in (("Presión de servicio", "Presión de servicio (MPa)"), ("Presión de ensayo", "Presión de ensayo (MPa)")):
        add(m, pl, "0", "Conjunto", 1, "-", dim, float(m.spec[campo].replace(",", ".")), "MPa", T_CAT,
            [f"CAT:{cod}:{'Ps' if 'servicio' in dim else 'Pe'}"], "Transcripto del catálogo",
            ("catalogo.py", f'Modelo("{cod}"'))

    # ------------------------------------------------ recipiente (datos de conjunto)
    def fsrc(par):
        return [f"FR:{rec}:{par}"] if rec else []

    vol_src = fsrc("vol")
    if vol_src:
        add(m, pl, "R", "Recipiente", 1, "-", "Volumen interior", g["vol_dm3"], "dm³", T_FAD, vol_src,
            "Cota del plano Fadesa de recipiente", ("catalogo.py", {"1kg": "G_1KG", "2.5kg": "G_2K5", "5kg": "G_5KG",
                                                                     "10kg": "G_10KG", "25kg": "G_25KG",
                                                                     "50kg": "G_50KG"}[rec] + " = dict"))
    elif rod:
        add(m, pl, "R", "Recipiente", 1, "-", "Volumen interior", g["vol_dm3"], "dm³", T_CAL,
            ["PC:tabla0", "C:g_rodante"],
            "Calculado con Ø390 × cuerpo del proceso de carros y dos casquetes 0,656·R",
            ("catalogo.py", "def _g_rodante"))
    else:
        add(m, pl, "R", "Recipiente", 1, "-", "Volumen interior", g["vol_dm3"], "dm³", T_CAL,
            [f"CAT:{cod}:Altura", "C:g_inox" if fam == "inox" else "C:g_co2"],
            "Calculado con la geometría derivada de la altura del catálogo",
            ("catalogo.py", "def _g_inox" if fam == "inox" else "def _g_co2"))
    htot = dr["z_cuello"] - dr["z_fondo"] if g["tipo_fondo"] != "concavo" else dr["z_cuello"]
    tsrc = fsrc("total") if rec in ("1kg", "2.5kg", "5kg", "10kg") else []
    add(m, pl, "R", "Recipiente", 1, "-", "Altura total del recipiente (apoyo a boca del cuello)", r1(htot), "mm",
        T_FAD if tsrc else T_CAL, tsrc or ([f"FR:{rec}:hc", f"FR:{rec}:hd", f"FR:{rec}:cuello_h"] if rec else
                                          (["PC:tabla0", "C:recipiente"] if tam in PC_T0 else [])),
        "Cota del plano Fadesa" if tsrc else "Suma: cabezal inferior + cuerpo + cúpula (truncada en la boca) + cuello",
        ("modelo3d.py", "def recipiente"))
    masa_rec = sum(MAT.peso(piezas[k], MAT.ACERO if fam != "inox" else MAT.INOX) for k in
                   ("cuerpo", "cupula", "fondo", "cuello", "placas_refuerzo") if k in piezas)
    add(m, pl, "R", "Recipiente", 1, "-", "Masa del recipiente (calculada, sin cordones)", r1(masa_rec, 2), "kg",
        T_CAL, fsrc("masa"), "Σ volumen de cuerpo, cúpula, fondo, cuello y placas × 7,85 kg/dm³"
        + ("; comparar con la masa del plano Fadesa" if rec else ""), ("materiales.py", "ACERO, INOX"))

    for pos, k in enumerate(orden, 1):
        nom, mat, rho, fac, obs = MAT.especificacion(m, k)
        s = piezas[k]
        cant = 2 if k in ("rueda_der", "llanta_der") else 1
        L, A, H = bb(s)

        def A_(dim, val, uni, tipo, src, calc, code, estado=""):
            add(m, pl, pos, nom, cant, mat, dim, val, uni, tipo, src, calc, code, estado)

        # -------------------------------------------- recipiente
        if k in ("cuerpo", "cupula", "fondo"):
            if fam in ("inox", "co2"):
                cs = "C:g_inox" if fam == "inox" else "C:g_co2"
                A_("Ø exterior", r1(D), "mm", T_CAT, [f"CAT:{cod}:Profundidad"],
                   "Ø exterior = profundidad del catálogo", ("catalogo.py", "def _g_inox" if fam == "inox" else "def _g_co2"))
                e = g["t"]
                A_("Espesor", e, "mm", T_DIS, [cs, "N:3525" if fam == "inox" else "N:2533"],
                   "Inox 0,8 (≥ 0,63 mín. IRAM 3525 3.2.1 b)" if fam == "inox" else
                   "Pared para presión de ensayo 25 MPa (supuesto)", ("catalogo.py", "t = 0.8" if fam == "inox" else "t = 5.4"))
                A_("Altura de la pieza", r1(H), "mm", T_CAL, [f"CAT:{cod}:Altura", cs],
                   "Derivada de la altura total del catálogo menos válvula (100), cuello y cúpula/hombro",
                   ("catalogo.py", "def _g_inox" if fam == "inox" else "def _g_co2"))
                continue
            if rec:
                A_("Ø exterior", r1(D), "mm", T_FAD, fsrc("D"), "Cota del plano Fadesa",
                   ("catalogo.py", {"1kg": "G_1KG", "2.5kg": "G_2K5", "5kg": "G_5KG", "10kg": "G_10KG",
                                    "25kg": "G_25KG", "50kg": "G_50KG"}[rec] + " = dict"))
            else:
                A_("Ø exterior", r1(D), "mm", T_PRO, ["PC:tabla0"] + (["FE:100 kg:D"] if tam == "100 kg" else []),
                   "Tabla 0 del proceso de carros (Ø390, casquete 15\" compartido)" +
                   ("; coincide con el plano Fadesa del 100 kg" if tam == "100 kg" else ""),
                   ("catalogo.py", "G_70KG = _g_rodante"))
            e = {"cuerpo": g["t"], "cupula": g["td"], "fondo": g["tf"]}[k]
            if rec:
                par = {"cuerpo": "t", "cupula": "td", "fondo": "tf"}[k]
                A_("Espesor", e, "mm", T_FAD, fsrc(par), "Cota/nota de espesor del plano Fadesa",
                   ("catalogo.py", {"1kg": "G_1KG", "2.5kg": "G_2K5", "5kg": "G_5KG", "10kg": "G_10KG",
                                    "25kg": "G_25KG", "50kg": "G_50KG"}[rec] + " = dict"))
            else:
                A_("Espesor", e, "mm", T_NOR, ["N:3550", "PC:tabla0"],
                   "IRAM 3550 4.1.3.2: mínimo 4,5 mm para Ø > 320 → chapa 4,75 (tabla 0 del proceso de carros)",
                   ("catalogo.py", "def _g_rodante"))
            if k == "cuerpo":
                if rod:
                    src = (fsrc("hc") if rec else []) + (["PC:tabla0"] if tam in PC_T0 else [])
                    lc = r1(dr["z_union"] - dr["zb"])
                    A_("Largo del cuerpo entre cabezales", lc, "mm", T_FAD if rec else T_PRO, src,
                       ("Cota del plano Fadesa" + (f"; el proceso de carros dice {PC_T0[tam][2]:g}" if tam in PC_T0 else "")) if rec else
                       "Tabla 0 del proceso de carros (alto del cuerpo)", ("catalogo.py", "G_70KG = _g_rodante"))
                    A_("Encastre de los casquetes: labio × escalón", f"{r1(dr['encastre'][0])} × {r1(dr['encastre'][1])}",
                       "mm", T_FAD, ["FR:25kg:det2"] + (["PC:casquete"] if cod in PROPIOS else []),
                       "Casquete con borde reducido y tope que entra en el cuerpo (detalles 2 y 3 del plano Fadesa 25 kg; "
                       "proceso de carros); labio 2,5·e, escalón 2·e", ("modelo3d.py", "def encastre"))
                else:
                    ztop = dr["z_union"]
                    A_("Alto del cuerpo (piso o fondo a unión con la cúpula)", r1(H), "mm", T_CAL,
                       fsrc("total") + fsrc("hd") + fsrc("cuello_h"),
                       f"Altura total {g.get('total', '')} − cuello {g['cuello'][1]} − cúpula en la boca"
                       + (f" − fondo {g.get('hf', '')}" if g["tipo_fondo"] == "cupula" else ""),
                       ("modelo3d.py", 'if "total" in g'))
                    if g["tipo_fondo"] in ("concavo", "cupula"):
                        A_("Bordón (escalón × labio; escalón de 1 e)",
                           f"{r1(dr['encastre'][1])} × {r1(dr['encastre'][0])}" +
                           (" (los dos extremos)" if g["tipo_fondo"] == "cupula" else ""), "mm", T_FAD,
                           [f"FR:{FD_DET[rec]}:det2", "PM:bordoneado"],
                           "Medido a escala 1:1 en el detalle 2 del plano Fadesa (labio 5,5-5,8; escalón 4,5-5,2); "
                           "lo forma la bordoneadora (proceso de manuales)", ("modelo3d.py", "def encastre"))
                    if tam == "1 kg" and cod in PROPIOS:
                        A_("Largo de corte del caño", 255, "mm", T_MP, ["MP:C35"], "Planilla MP (caño cortado a 255 mm)",
                           ("bom.py", "CANO_1KG = dict"))
                des = math.pi * (D - e)
                A_("Desarrollo de la chapa π·(Ø − e)", r1(des), "mm", T_CAL, ["CALC"],
                   f"π × ({r1(D)} − {e})", ("bom.py", "desarrollo {_f(math.pi"))
                hc = B.HOJA_CUERPO.get(tam.replace(".", ",")) if cod in PROPIOS else None
                if hc:
                    fmt, ee, alto, de, ap = hc
                    if tam in ("70 kg", "100 kg"):
                        A_("Recorte de hoja (alto × desarrollo)", f"{alto:g} × {de:g}", "mm", T_PRO, ["PC:corte"],
                           "Proceso de carros: hoja mixta 3 × 680 + 1 × 900 con el lado de 1212 = π·(390 − 4,75) + luz",
                           ("bom.py", '"70 kg": ("LAC'))
                    else:
                        col = {"2,5 kg": "D", "5 kg": "E", "10 kg": "F", "25 kg": "G", "50 kg": "H"}[tam.replace(".", ",")]
                        A_("Recorte de hoja (alto × desarrollo)", f"{alto:g} × {de:g}", "mm", T_MP,
                           [f"MP:{col}34", f"MP:{col}35"], "Planilla MP fila 34 (desarrollo) y 35 (alto)",
                           ("bom.py", "HOJA_CUERPO = {"))
            else:
                if k == "cupula" or rod:
                    par = "hd"
                    if rec:
                        A_("Altura del casquete", g["hd"], "mm", T_FAD, fsrc(par), "Cota del plano Fadesa",
                           ("catalogo.py", "G_" + {"1kg": "1KG", "2.5kg": "2K5", "5kg": "5KG", "10kg": "10KG",
                                                    "25kg": "25KG", "50kg": "50KG"}[rec] + " = dict"))
                    else:
                        A_("Altura del casquete", g["hd"], "mm", T_DER,
                           ["FR:50kg:hd", "FR:50kg:D", "PC:casquete"],
                           f"0,656 × R (relación del cabezal Fadesa 50 kg: 105 / 160) = 0,656 × {R:g}",
                           ("catalogo.py", "hd = round(0.656"))
                if k == "fondo" and g["tipo_fondo"] == "concavo":
                    A_("Altura de la pollera (borde del fondo)", g["zf_borde"], "mm", T_FAD, fsrc("zf_borde"),
                       "Cota del plano Fadesa", ("catalogo.py", "zf_borde"))
                    A_("Pestaña del fondo encastrado (contra la pared)", 10.0, "mm", T_FAD,
                       [f"FR:{FD_DET[rec]}:det3", "PM:encastre"],
                       "Detalle 3 del plano Fadesa (pestaña ≥ 10 a escala 1:1); fondo encastrado a presión (proceso de "
                       "manuales); filete por debajo", ("modelo3d.py", "hp = 10.0"))
                    A_("Flecha del fondo cóncavo (centro sobre el piso)", g["zf_centro"], "mm", T_FAD,
                       fsrc("zf_centro"), "Cota del plano Fadesa", ("catalogo.py", "zf_centro"))
                if k == "fondo" and g["tipo_fondo"] == "cupula":
                    A_("Altura del fondo", g["hf"], "mm", T_FAD, fsrc("hf"), "Cota del plano Fadesa",
                       ("catalogo.py", "G_1KG = dict"))
                dsk = B.disco(m, k, s)
                if cod not in PROPIOS:
                    pass
                elif fam == "manual":
                    col = {"1kg": "C", "2.5kg": "D", "5kg": "E", "10kg": "F"}[rec]
                    if k == "cupula":
                        A_("Ø del disco a embutir", r1(dsk), "mm", T_MP, [f"MP:{col}38"],
                           "Planilla MP fila 38 (Ø del disco de cúpula)", ("bom.py", "DISCO = {"))
                    else:
                        A_("Ø del disco a embutir", r1(dsk), "mm", T_MP, [f"MP:{col}44"],
                           "Planilla MP fila 44 (Ø del disco de fondo)", ("bom.py", "DISCO = {"))
                else:
                    A_("Ø del disco (referencia; el casquete se compra embutido)", r1(dsk), "mm", T_CAL, ["CALC"],
                       "Ø = 2·√(superficie media / π) × 1,03 (recorte de pestaña); la define Gockel",
                       ("bom.py", "def disco"), "E")
            A_("Masa de la pieza", r1(MAT.peso(s, rho, fac), 3), "kg", T_CAL, ["C:materiales"],
               "Volumen del sólido × 7,85 kg/dm³", ("materiales.py", "def peso"))
            continue
        if k == "cuello":
            dn, hn, rosca, dh = g["cuello"]
            ftag = fsrc
            tipo = T_FAD if rec else (T_CAT if fam in ("inox", "co2") else T_PRO)
            srcd = (lambda p: ftag(p)) if rec else (lambda p: ["FR:50kg:" + p, "PC:cupla"] if rod else ["C:g_inox" if fam == "inox" else "C:g_co2"])
            if fam in ("inox", "co2"):
                tipo = T_DIS
            A_("Ø exterior", dn, "mm", tipo, srcd("cuello_d"), "Cota del plano Fadesa" if rec else
               ("Cupla 2½\" BSP del proceso de carros, igual a la del recipiente Fadesa de 50 kg" if rod else "Supuesto de diseño"),
               ("catalogo.py", "cuello=("))
            A_("Altura sobre la cúpula", hn, "mm", tipo, srcd("cuello_h"), "Cota del plano Fadesa" if rec else
               "Ídem 50 kg" if rod else "Supuesto de diseño", ("catalogo.py", "cuello=("))
            A_("Rosca", rosca, "-", tipo, srcd("rosca"), "Rótulo del corte A-A del plano Fadesa" if rec else
               "Ídem 50 kg" if rod else ("ISO 11363-1 (CO₂)" if fam == "co2" else "Supuesto de diseño"),
               ("catalogo.py", "cuello=("))
            A_("Ø del asiento", dh, "mm", tipo, srcd("asiento"), "Cota del corte A-A del plano Fadesa" if rec else
               "Ídem 50 kg" if rod else "Supuesto de diseño", ("catalogo.py", "cuello=("))
            if g["tipo_fondo"] in ("concavo", "cupula"):
                A_("Muesca de altura (ancho × prof. × alto)", "2 × 1 × 2", "mm", T_DIS, ["PM:muesca", "C:recipiente"],
                   "El proceso pide la muesca (prensa Pannier) sin medidas: valor de diseño", ("modelo3d.py", "# muesca"))
            continue
        if k == "placas_refuerzo":
            A_("Placas (cant. × largo × arco × e)", "2 × 200 × 100 × 4,75", "mm", T_PRO, ["PC:refuerzo"],
               "Proceso de carros: 200 a lo largo del cuerpo, 100 de arco", ("catalogo.py", "refuerzo=(200.0"))
            A_("Curvado / posición", "Ø380 / a 100 mm de cada boca, sobre la costura", "mm", T_PRO, ["PC:refuerzo"],
               "Curvadas al Ø interior, por dentro y punteadas en las 4 esquinas", ("modelo3d.py", "placas_refuerzo"))
            continue

        # -------------------------------------------- válvula y descarga: medidas a escala en planos Fadesa
        vi = info["valvula"]
        tv = vi["tipo"]
        V = M.VALVULAS[tv]
        pf = plan_fe(m)
        # pieza medida en otro plano Fadesa cuando el del tamaño no la muestra
        ALT = {("2,5 kg", "suncho"): "10 kg", ("5 kg", "suncho"): "10 kg", ("25 kg", "racor"): "10 kg",
               ("100 kg", "manometro"): "50 kg"}
        FE = lambda comp: [f"FE:{ALT.get((pf, comp), pf)}:{comp}"]
        g763 = tv == "G763"  # válvula de rodantes: el plano Fadesa sólo la muestra por fuera
        ref_v = ("modelo3d.py", f'"{tv}": dict(')
        if k == "tuerca":
            A_("Cuello de la válvula Ø × alto", f"{V['cuello_d']:g} × {V['cuello_h']:g}", "mm", T_FAD, FE("valvula"),
               f"Medido a escala en el plano Fadesa (válvula {tv})", ref_v)
            continue
        if k == "espiga":
            A_("Espiga roscada Ø × largo", f"{V['esp_d']:g} × {V['esp_h']:g}", "mm", T_FAD, FE("valvula"),
               f"Medido a escala en el plano Fadesa (válvula {tv})", ref_v)
            continue
        if k == "cuerpo_valvula":
            A_("Cuerpo ancho × alto", f"{V['bw']:g} × {V['bh']:g}", "mm", T_FAD, FE("valvula"),
               f"Medido a escala en el plano Fadesa (válvula {tv})", ref_v)
            A_("Fondo del cuerpo", V["bd"], "mm", T_DIS, ["C:valvula"], "No visible en la vista lateral Fadesa", ref_v)
            if tv != "G763":
                pv = PV.PERFILES[tv][2]
                A_("Oreja del pivote: ancho / eje a (x, z)", f"{V['oreja']:g} / ({pv[0]:g}; {pv[1]:g})", "mm", T_FAD,
                   FE("valvula"), "Centro del agujero del pivote medido en el plano Fadesa; ancho de diseño",
                   ("perfiles_valvula.py", f"{tv}_PIVOTE = "))
            else:
                A_("Torre / horquilla: base × alto, ranura", "49 × 30 → 37 × 30; horquilla 17, ranura 11", "mm", T_FAD,
                   FE("valvula"), "Medido a escala en el despiece de la válvula (plano Fadesa 50 / 100 kg)", ref_v)
            A_("Salida a la manguera Ø × largo", f"{V['sal_d']:g} × {V['sal_l']:g}", "mm", T_FAD if tv == "F192" else T_DIS,
               FE("racor") if tv == "F192" else ["C:valvula"], "Rosca del racor medida en Fadesa" if tv == "F192" else
               ("Boquilla del 1 kg: sin cota en Fadesa" if tv == "F510" else "Sin cota en Fadesa"), ref_v)
            continue
        if k == "vastago":
            vd, vl, ad, ah = V["vas"]
            A_("Vástago Ø × largo / asiento Ø", f"{vd:g} × {vl:g} / {ad:g}", "mm", T_DIS if g763 else T_FAD, ["C:valvula"] if g763 else FE("vastago"),
               "Interno: no se ve en el plano Fadesa (G763)" if g763 else "Medido a escala en el plano Fadesa", ref_v)
            continue
        if k == "resorte":
            A_("Resorte Ø × largo libre", f"{V['res'][0]:g} × {V['res'][1]:g}", "mm", T_DIS if g763 else T_FAD, ["C:valvula"] if g763 else FE("resorte"),
               "Interno: no se ve en el plano Fadesa (G763)" if g763 else "Medido a escala en el plano Fadesa", ref_v)
            continue
        if k == "eje":
            if tv == "G763":
                A_("Ø × largo", f"8 × {V['torre'][2] + 10:g}", "mm", T_DIS, ["C:valvula", "FE:50 kg:valvula"],
                   "Tornillo F840 + buje + arandela del plano Fadesa, sin cota", ("modelo3d.py", 'e_d = V["eje_d"]'))
                continue
            A_("Ø × largo", f"{3.6 if tv == 'F510' else 4.0:g} × {V['bd'] + 5:g}", "mm", T_DIS, ["C:valvula"],
               "Pasa por la oreja y la palanca en el agujero del plano Fadesa; Ø sin cota", ("modelo3d.py", 'p["eje"] = _cyl(r_e'))
            continue
        if k in ("manija_superior", "manija_inferior"):
            if tv == "G763":
                if k == "manija_inferior":
                    continue
                A_("Palanca largo × alto × espesor / empuñadura", f"{r1(info['valvula']['y_tip'] - 11)} × 16 × 10 / Ø22 × 44",
                   "mm", T_DIS, ["C:valvula", "FE:50 kg:valvula"],
                   "Gira en la ranura de la horquilla (eje según X, plano Fadesa); hacia atrás, 0,75·R con 15 de luz a "
                   "la manija del carro; sin cota en Fadesa", ("modelo3d.py", "L_ = x_tip or 110.0"))
                continue
            pts = PV.PERFILES[tv][0 if k == "manija_superior" else 1]
            xs_, zs_ = [q[0] for q in pts], [q[1] for q in pts]
            A_("Perfil lateral: largo × alto (x / z extremos)", f"{r1(max(xs_) - min(xs_))} × {r1(max(zs_) - min(zs_))} "
               f"({r1(min(xs_))} a {r1(max(xs_))} / {r1(min(zs_))} a {r1(max(zs_))})", "mm", T_FAD, FE("valvula"),
               f"Contorno completo extraído del plano vectorial Fadesa ({len(pts)} puntos), no una caja",
               ("perfiles_valvula.py", f"{tv}_{'SUP' if k == 'manija_superior' else 'INF'} = ("))
            A_("Ancho (chapa estampada en U)", f"{V['bd'] + (3 if k == 'manija_superior' else 7):g}", "mm", T_DIS,
               ["C:valvula"], "No visible en la vista lateral: a horcajadas del cuerpo (palanca) y de la palanca (manija)",
               ("modelo3d.py", "wu, wl = bd + 3.0, bd + 7.0"))
            continue
        if k == "pasador":
            A_("Ø alambre × largo", f"3,2 × {(V['torre'][2] + 16) if tv == 'G763' else (V['bd'] + 16.5):g}", "mm", T_DIS,
               ["C:valvula", "N:3550"], "Traba con anilla Ø18 y precinto (IRAM 3550 3.4.2)" +
               ("; cruza horquilla y nariz de la palanca" if tv == "G763" else ""),
               ("modelo3d.py", 'p["pasador"] = _cyl(1.6'))
            continue
        if k == "manometro":
            A_("Ø de la esfera", vi["man_d"], "mm", T_FAD, FE("manometro"),
               "Medido a escala (manómetro F645 en manuales; con cubremanómetro G711 en rodantes)", ref_v)
            ps = B._ps(m)
            A_("Rango y sector verde", f"0-{ps * 2.5 if ps < 5 else 25:g} / {ps:g}", "MPa", T_DIS,
               [f"CAT:{cod}:Ps"], "Rango ≈ 2,5 × presión de servicio (criterio); sello IRAM 3533 exigido en la compra",
               ("bom.py", 'if k == "manometro"'))
            continue
        if k == "disco_seguridad":
            A_("Tapón hexagonal (entre caras × alto)", "14 × 9", "mm", T_DIS, ["C:valvula"],
               "CO₂: disco de seguridad, rotura 18-21 MPa", ("modelo3d.py", 'p["disco_seguridad"]'))
            continue
        if k == "cano_pesca":
            if rod or fam == "co2":
                A_("Ø exterior", r1(A), "mm", T_DIS, ["C:rodante" if rod else "C:manual"], "Sin cota en Fadesa",
                   ("modelo3d.py", 'out["cano_pesca"]'))
            else:
                A_("Ø exterior", r1(A), "mm", T_FAD, FE("cano"), "Medido a escala (cabeza del caño de pesca)",
                   ("modelo3d.py", "dp = 14.4 if tv"))
            A_("Largo", r1(H), "mm", T_CAL, ["C:manual" if not rod else "C:rodante"],
               f"Desde la espiga hasta {18 if not rod else 25} mm sobre el fondo", ("modelo3d.py", 'zf = dr["z_fondo"] + g["tf"]'))
            continue
        if k == "junta_cuello":
            A_("O-ring Ø ext × cordón", f"{V['oring'][0]:g} × {V['oring'][1]:g}", "mm", T_DIS if g763 else T_FAD, ["C:valvula"] if g763 else FE("oring"),
               "Interno: no se ve en el plano Fadesa (G763)" if g763 else "Medido a escala en el plano Fadesa", ref_v)
            continue
        if k == "racor":
            if m.descarga == "tobera_polvo":
                A_("Tuerca Ø × largo / casquillo Ø × largo", "18,8 × 5,9 / 16,9 × 13,5", "mm", T_FAD, FE("racor"),
                   "Medido a escala en el plano Fadesa", ("modelo3d.py", "rc = _cyl(9.4, 5.9"))
            else:
                A_("Ø × largo", f"{r1(min(A, H))} × {r1(L)}", "mm", T_DIS, ["C:manual" if not rod else "C:rodante"],
                   "Sin cota en Fadesa", ("modelo3d.py", 'out["racor"]'))
            continue
        if k in ("manguera", "manguera_enrollada"):
            r = 12.5 if rod else {"co2": 7.0}.get(fam, 8.7)
            largo = s.Volume() / (math.pi * r * r)
            if m.descarga == "tobera_polvo" and k == "manguera":
                A_("Ø exterior", 17.4, "mm", T_FAD, FE("manguera"), "Medido a escala en el plano Fadesa",
                   ("modelo3d.py", "d_hose = 0 if chico"))
            else:
                A_("Ø exterior", r1(2 * r), "mm", T_DIS, ["C:manual" if not rod else "C:rodante"], "Sin cota en Fadesa",
                   ("modelo3d.py", "d_hose = 0 if chico" if not rod else "d_hose = 25.0"))
            A_("Largo desarrollado dibujado", r1(largo, 0), "mm", T_CAL, ["CALC"],
               "Volumen del sólido / (π r²); en rodantes la manga real es la del catálogo", ("bom.py", "largo = s.Volume()"))
            continue
        if k in ("tobera", "lanza", "difusor", "empunadura", "brazo_difusor", "tobera_campana", "suncho", "pie",
                 "valvula_esferica", "soportes_eje", "manija_carro", "ganchos_manguera", "tercera_pata", "arandelas_tope", "eje_ruedas",
                 "rueda_der", "llanta_der"):
            if k == "rueda_der":
                Dw = float(m.spec["Diámetro de rueda (mm)"])
                A_("Ø exterior", Dw, "mm", T_CAT, [f"CAT:{cod}:Rueda"], "Diámetro de rueda del catálogo",
                   ("modelo3d.py", "Dw = float"))
                A_("Ancho de banda", info["bw_w"], "mm", T_NOR, ["N:3550T3", f"FE:{'100 kg' if Dw > 350 else '50 kg'}:rueda"],
                   "IRAM 3550 tabla III: ≥ 50 (Fadesa usa 49: no cumple); Ruedar Ø300 / Ø350 × 60 y Escanort Ø400 × 100",
                   ("modelo3d.py", "banda={300: 60.0"))
                A_("Trocha entre centros de rueda", info["track"], "mm", T_NOR, ["N:3550T3"],
                   "IRAM 3550 tabla III: ≥ 400; además Ø del cuerpo + banda + 2 × 20 de luz con el cuerpo",
                   ("modelo3d.py", "trocha_min=400.0"))
                A_("Ø interior del macizo", r1(0.72 * Dw), "mm", T_DIS, ["C:rodante"], "0,72 × Ø rueda", ("modelo3d.py", "Rw * 0.72"))
                continue
            if k == "llanta_der":
                A_("Ø de la llanta", r1(0.72 * float(m.spec['Diámetro de rueda (mm)'])), "mm", T_DIS, ["C:rodante"],
                   "0,72 × Ø rueda", ("modelo3d.py", "llanta = _tube"))
                A_("Espesor aro / disco", "2 / 2,5", "mm", T_DIS, ["C:rodante", "FE:25 kg:masa"],
                   "Chapa estampada; ajustado a la masa de los planos Fadesa", ("modelo3d.py", "aro e = 2"))
                A_("Cubo Ø ext / Ø int", "60 / 26", "mm", T_DIS, ["C:rodante"], "Cubo para eje Ø25", ("modelo3d.py", "_tube(30, 13"))
                continue
            if k == "eje_ruedas":
                A_("Ø × largo / posición", f"25 × {r1(L)} / {r1(info['yw'])} detrás del eje del cuerpo", "mm", T_DIS,
                   ["PC:accesorios", "N:3550T3"], "Barra SAE 1045 Ø25 comprada; recta, detrás de la pared trasera "
                   "(luz 15) a la altura del centro de rueda; largo = trocha + banda + arandelas",
                   ("modelo3d.py", "yw = R + CARRO"))
                continue
            if k == "arandelas_tope":
                A_("Ø ext × Ø int × e (4 u)", "40 × 26 × 4", "mm", T_DIS, ["PC:accesorios"],
                   "El proceso las compra; medidas de diseño", ("modelo3d.py", "arandela=(40.0"))
                continue
            if k == "soportes_eje":
                A_("Alto × largo × e (2 u)", f"80 × {r1(A)} × {g['t']:g}", "mm", T_DIS, ["PC:accesorios"],
                   "Chapa de orilla soldada atrás y abajo; desde la pared hasta 25 mm detrás del eje",
                   ("modelo3d.py", "soporte=(80.0"))
                A_("Separación de los soportes", r1(2 * info["xs"]), "mm", T_DIS, ["PC:accesorios"], "± 0,55·R",
                   ("modelo3d.py", "x_soporte=0.55"))
                continue
            if k == "manija_carro":
                largo = s.Volume() / (math.pi * 12.7 ** 2)
                A_("Caño", "Ø25,4 × 1,6", "mm", T_DIS, ["PC:accesorios"], "El proceso compra el caño de la manija",
                   ("modelo3d.py", "manija=(25.4"))
                A_("Altura del agarre (= altura total)", r1(m.H), "mm", T_CAT, [f"CAT:{cod}:Altura", "PC:accesorios"],
                   "Sube por encima de la cúpula hasta la altura del catálogo", ("modelo3d.py", "zg = H - rt"))
                A_("Separación de las patas (ejes) / largo desarrollado", f"{r1(2 * info['xm'])} / {r1(largo, 0)}", "mm",
                   T_DIS, ["PC:accesorios"], "Patas a ± 0,55·R, tangentes al cuerpo; radio de curvado 40",
                   ("modelo3d.py", "manija=(25.4"))
                continue
            if k == "ganchos_manguera":
                A_("Ancho × vuelo × labio × e (2 u)", f"40 × {r1(2 * 25 + 10)} × 30 × {g['t']:g}", "mm", T_DIS,
                   ["PC:accesorios"], "Costado de la salida, arriba (12 %) y abajo (90 %) del cuerpo; vuelo = 2 Ø de "
                   "manga + 10", ("modelo3d.py", "gancho=(40.0"))
                continue
            if k == "tercera_pata":
                A_("Ancho × pie × e", f"80 × 50 × {g['t']:g}", "mm", T_DIS, ["PC:accesorios"],
                   "Chapa plegada en L, adelante a 0,75·R del eje, soldada al casquete inferior",
                   ("modelo3d.py", "pata=(80.0"))
                continue
            if k == "valvula_esferica":
                A_("Cuerpo × palanca", "40 × 40 × 60; palanca 90", "mm", T_DIS, ["C:rodante"], "Representativa (comercial)",
                   ("modelo3d.py", "ve = _box(40, 40, 60"))
                continue
            if k == "tobera_campana":
                A_("Ø entrada / Ø boca × largo", "32 / 68 × 200", "mm", T_DIS, ["C:rodante"], "Cono 16→34 de radio, 200 de largo",
                   ("modelo3d.py", "tb = cq.Solid.makeCone(16, 34"))
                continue
            if k == "lanza" and rod:
                A_("Ø × largo", "40 × 380 (boca Ø56)", "mm", T_DIS, ["C:rodante"], "Lanza espumígena de rodante",
                   ("modelo3d.py", "hn = 380.0"))
                continue
            # dispositivos de descarga manuales y suncho
            d_dev = {"tobera_polvo": 24.0, "tobera_chorro": 22.0, "lanza_espuma": 32.0, "lanza_k": 20.0,
                     "lanza_d": 40.0, "difusor_brazo": 70.0, "difusor_manga": 90.0, "tobera_1kg": 0.0}.get(m.descarga, 0)
            if k == "tobera" and m.descarga == "tobera_polvo":
                A_("Portatobera Ø × largo / tobera Ø × largo", "18,8 × 13,4 / 19,9 × 60,1", "mm", T_FAD, FE("tobera"),
                   "Medido a escala en el plano Fadesa", ("modelo3d.py", "body = _cyl(9.4, 13.4"))
                continue
            if k == "suncho" and m.descarga == "tobera_polvo":
                A_("Banda (alto) / Ø interior", f"14,4 / {r1(D - 0.4)}", "mm", T_FAD, FE("suncho"),
                   "Suncho portamanguera F674 medido a escala", ("modelo3d.py", "hb = 14.4 if tipo"))
                continue
            if k == "tobera":
                if m.descarga == "tobera_1kg":
                    A_("Boquilla Ø base / Ø punta × largo", "12 / 9 × 10", "mm", T_DIS, ["C:manual"],
                       "F510: el plano Fadesa no muestra tobera aparte", ("modelo3d.py", "noz = cq.Solid.makeCone"))
                else:
                    A_("Ø mayor × largo", f"{d_dev:g} × {r1(H)}", "mm", T_DIS, ["C:manual"],
                       "Ø de tobera por tipo; largo limitado por la altura disponible", ("modelo3d.py", "d_dev = {"))
                continue
            if k == "suncho":
                A_("Fleje (alto × espesor) / Ø interior", f"18 × 1,7 / {r1(D - 0.4)}", "mm", T_DIS, ["C:manual"],
                   "Banda de 18 mm abrazando el cuerpo", ("modelo3d.py", "band = _tube(R + 1.5"))
                continue
            if k == "pie":
                A_("Ø × alto", f"{r1(D)} × {r1(0.55 * R)}", "mm", T_DIS, ["C:manual"], "Ø del cilindro × 0,55·R",
                   ("modelo3d.py", 'out["pie"]'))
                continue
            A_("Envolvente L × A × H", f"{r1(L)} × {r1(A)} × {r1(H)}", "mm", T_DIS, ["C:manual"],
               "Dimensiones del sólido dibujado (constantes del tipo de descarga)", ("modelo3d.py", "d_dev = {"))
            continue

        # -------------------------------------------- identificación
        R_ = R
        if k == "etiqueta":
            ancho = math.radians(M.ARCO_PLACA) * R_
            A_("Panel central (arco 108°)", r1(ancho), "mm", T_NOR, ["N:3534"], f"108° × π/180 × R({R_:g})",
               ("modelo3d.py", "ARCO_PLACA = 108.0"))
            A_("Alas laterales (arco c/u)", f"{M.arco_ala(R_):g}° = {r1(M.ala_dim(R_))}", "mm", T_REL, ["RV:etiqueta"],
               "Relevamiento: la etiqueta envuelve ≈ 216° (72° si Ø < 100)", ("modelo3d.py", "ARCO_ALA = 54.0"))
            A_("Alto", r1(H), "mm", T_CAL, ["N:3534", "C:identificacion"], "Alto que pide el contenido (rotulado.disposicion)",
               ("rotulado.py", "def disposicion"))
            continue
        if k == "oblea_pba":
            A_("Ø", M.OBLEA_PBA, "mm", T_NOR, ["N:522"], "Res. OPDS 522/07 anexos 1 y 2", ("modelo3d.py", "OBLEA_PBA = 46.0"))
            continue
        if k == "sello_iram":
            A_("Ancho × alto", "60 × 40", "mm", T_REL, ["N:AnexoR", "RV:estampilla"], "Anexo R IRAM + relevada (a confirmar)",
               ("modelo3d.py", "ESTAMPILLA_IRAM = (60.0"))
            continue
        if k == "tarjeta_caba":
            A_("Ancho × alto", "140 × 55", "mm", T_REL, ["RV:tarjeta"], "Relevada en un 10 kg (a confirmar con la AGC)",
               ("modelo3d.py", "TARJETA_CABA = (140.0"))
            continue
        if k == "etiqueta_serie":
            A_("Ancho × alto", "45 × 25", "mm", T_REL, ["RV:serie"], "Relevada en Melisam", ("modelo3d.py", "ETIQUETA_SERIE = (45.0"))
            continue
        if k == "faja_garantia":
            A_("Ancho × alto", "30 × 40", "mm", T_REL, ["RV:faja"], "Relevada en la línea Georgia", ("modelo3d.py", "FAJA_GARANTIA = (30.0"))
            continue
        if k == "junta_cuello":
            A_("Ø exterior × cordón", f"{r1(L)} × 3", "mm", T_CAL, ["C:identificacion"], "Ø espiga + 3; cordón 3",
               ("modelo3d.py", 'p["junta_cuello"]'))
            continue
        if k == "precinto":
            A_("Ø × largo", "5 × 10", "mm", T_DIS, ["C:identificacion", "N:3517"], "IRAM 3517-2 9.4.13 (precinto con id. del fabricante)",
               ("modelo3d.py", 'p["precinto"]'))
            continue
        A_("Envolvente L × A × H", f"{r1(L)} × {r1(A)} × {r1(H)}", "mm", T_DIS, ["C:manual"], "Sólido dibujado",
           ("modelo3d.py", "def extintor_manual"))
    print(m.codigo, len(rows), flush=True)

json.dump(rows, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "crudo.json"), "w"), ensure_ascii=False, indent=0)
print("FIN", len(rows))
