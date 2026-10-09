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
from flama import modelo3d as M, planos as P, materiales as MAT, bom as B  # noqa: E402
from flama.catalogo import MODELOS  # noqa: E402

FADESA_REC = {"1 kg": "1kg", "2,5 kg": "2.5kg", "5 kg": "5kg", "10 kg": "10kg", "25 kg": "25kg", "50 kg": "50kg"}
# modelos que usan el recipiente de un plano Fadesa (BC, HCFC = 5 kg; Clase D = 10 kg; AFFF 50 l = 50 kg)
REC_DE = {"FL_MAT_ABC_1kg": "1kg", "FL_MAT_ABC_2.5kg": "2.5kg", "FL_MAT_ABC_5kg": "5kg", "FL_MAT_ABC_10kg": "10kg",
          "FL_MAT_BC_5kg": "5kg", "FL_MAT_HCFC-HFC_5kg": "5kg", "FL_MAT_CLASED_9l": "10kg",
          "FL_MAT_ABC_25kg": "25kg", "FL_MAT_ABC_50kg": "50kg", "FL_MAT_AFFF_50l": "50kg"}
PROPIOS = B.PROPIOS

T_FAD, T_CAT, T_NOR, T_MP, T_REL, T_CAL, T_DIS, T_DER, T_FIC = (
    "Plano Fadesa", "Catálogo Fadesa", "Norma / resolución", "Planilla MP FLAMA", "Relevamiento de mercado",
    "Cálculo", "Diseño FLAMA (supuesto)", "Derivado (a validar)", "Ficha técnica de mercado")

rows = []


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
        add(m, pl, "0", "Conjunto", 1, "-", dim, r1(val), "mm", T_CAT, [f"CAT:{cod}:{campo}"],
            f"Envolvente del modelo ajustada al catálogo: válvula/palanca (manuales) o arco del bastidor y "
            f"posición de ruedas (rodantes) se corrigen hasta igualar {campo} del catálogo",
            ("modelo3d.py", "def construir"))
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
        add(m, pl, "R", "Recipiente", 1, "-", "Volumen interior", g["vol_dm3"], "dm³", T_DER,
            ["FR:50kg:vol", "C:g_rodante"],
            f"Proporcional al recipiente Fadesa de 50 kg (61,8 dm³ / 50 kg = 1,236 dm³/kg) × {tam} ≈ {g['vol_dm3']}",
            ("catalogo.py", f"G_{tam.split()[0]}KG = _g_rodante"))
    else:
        add(m, pl, "R", "Recipiente", 1, "-", "Volumen interior", g["vol_dm3"], "dm³", T_CAL,
            [f"CAT:{cod}:Altura", "C:g_inox" if fam == "inox" else "C:g_co2"],
            "Calculado con la geometría derivada de la altura del catálogo",
            ("catalogo.py", "def _g_inox" if fam == "inox" else "def _g_co2"))
    htot = dr["z_cuello"] - dr["z_fondo"] if g["tipo_fondo"] != "concavo" else dr["z_cuello"]
    tsrc = fsrc("total") if rec in ("1kg", "2.5kg", "5kg", "10kg") else []
    add(m, pl, "R", "Recipiente", 1, "-", "Altura total del recipiente (apoyo a boca del cuello)", r1(htot), "mm",
        T_FAD if tsrc else T_CAL, tsrc or ([f"FR:{rec}:hc", f"FR:{rec}:hd", f"FR:{rec}:cuello_h"] if rec else []),
        "Cota del plano Fadesa" if tsrc else "Suma: cabezal inferior + cuerpo + cúpula (truncada en la boca) + cuello",
        ("modelo3d.py", "def recipiente"))
    masa_rec = sum(MAT.peso(piezas[k], MAT.ACERO if fam != "inox" else MAT.INOX) for k in
                   ("cuerpo", "cupula", "fondo", "cuello", "varilla") if k in piezas)
    add(m, pl, "R", "Recipiente", 1, "-", "Masa del recipiente (calculada, sin cordones)", r1(masa_rec, 2), "kg",
        T_CAL, fsrc("masa"), "Σ volumen de cuerpo, cúpula, fondo, cuello y varilla × 7,85 kg/dm³"
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
            elif tam == "100 kg":
                A_("Ø exterior", r1(D), "mm", T_FAD, ["FE:100 kg:D"], "Cota Ø390 del plano Fadesa del extintor de 100 kg",
                   ("catalogo.py", "G_100KG = _g_rodante"))
            else:
                A_("Ø exterior", r1(D), "mm", T_DER, ["C:g_rodante"],
                   "Ø350 adoptado (sin plano de referencia); entre Ø320 (50 kg) y Ø390 (100 kg)",
                   ("catalogo.py", "G_70KG = _g_rodante"))
            e = {"cuerpo": g["t"], "cupula": g["td"], "fondo": g["tf"]}[k]
            if rec:
                par = {"cuerpo": "t", "cupula": "td", "fondo": "tf"}[k]
                A_("Espesor", e, "mm", T_FAD, fsrc(par), "Cota/nota de espesor del plano Fadesa",
                   ("catalogo.py", {"1kg": "G_1KG", "2.5kg": "G_2K5", "5kg": "G_5KG", "10kg": "G_10KG",
                                    "25kg": "G_25KG", "50kg": "G_50KG"}[rec] + " = dict"))
            else:
                A_("Espesor", e, "mm", T_NOR, ["N:3550", "MP:J32"],
                   "IRAM 3550 4.1.3.2: mínimo 4,5 mm para Ø > 320 → chapa comercial 4,75 (planilla MP)",
                   ("catalogo.py", "def _g_rodante"))
            if k == "cuerpo":
                if rod:
                    src = fsrc("hc") if rec else ["C:g_rodante", "C:recipiente"]
                    A_("Largo del cuerpo entre cabezales", r1(H), "mm", T_FAD if rec else T_DER, src,
                       "Cota del plano Fadesa" if rec else
                       "Largo de cilindro para el volumen de diseño con dos cabezales semielípticos",
                       ("modelo3d.py", "rodantes: hc = largo"))
                else:
                    ztop = dr["z_union"]
                    A_("Alto del cuerpo (piso o fondo a unión con la cúpula)", r1(H), "mm", T_CAL,
                       fsrc("total") + fsrc("hd") + fsrc("cuello_h"),
                       f"Altura total {g.get('total', '')} − cuello {g['cuello'][1]} − cúpula en la boca"
                       + (f" − fondo {g.get('hf', '')}" if g["tipo_fondo"] == "cupula" else ""),
                       ("modelo3d.py", 'if "total" in g'))
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
                        A_("Recorte de hoja (alto × desarrollo)", f"{alto:g} × {de:g}", "mm", T_CAL, ["CALC"],
                           "Del plano: largo del cuerpo × π·(Ø − e); 3 piezas por hoja 1500 × 3000",
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
                        A_("Altura del casquete", g["hd"], "mm", T_DER if tam == "70 kg" else T_CAL,
                           ["FR:50kg:hd", "FR:50kg:D", "C:g_rodante"],
                           f"0,656 × R (relación del cabezal Fadesa 50 kg: 105 / 160) = 0,656 × {R:g}",
                           ("catalogo.py", "hd = round(0.656"))
                if k == "fondo" and g["tipo_fondo"] == "concavo":
                    A_("Altura de la pollera (borde del fondo)", g["zf_borde"], "mm", T_FAD, fsrc("zf_borde"),
                       "Cota del plano Fadesa", ("catalogo.py", "zf_borde"))
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
            tipo = T_FAD if rec else (T_CAT if fam in ("inox", "co2") else T_DER)
            srcd = (lambda p: ftag(p)) if rec else (lambda p: ["FR:50kg:" + p] if rod else ["C:g_inox" if fam == "inox" else "C:g_co2"])
            if fam in ("inox", "co2"):
                tipo = T_DIS
            A_("Ø exterior", dn, "mm", tipo, srcd("cuello_d"), "Cota del plano Fadesa" if rec else
               ("Igual al cuello del recipiente Fadesa de 50 kg (RBSP 2½\")" if rod else "Supuesto de diseño"),
               ("catalogo.py", "cuello=("))
            A_("Altura sobre la cúpula", hn, "mm", tipo, srcd("cuello_h"), "Cota del plano Fadesa" if rec else
               "Ídem 50 kg" if rod else "Supuesto de diseño", ("catalogo.py", "cuello=("))
            A_("Rosca", rosca, "-", tipo, srcd("rosca"), "Rótulo del corte A-A del plano Fadesa" if rec else
               "Ídem 50 kg" if rod else ("ISO 11363-1 (CO₂)" if fam == "co2" else "Supuesto de diseño"),
               ("catalogo.py", "cuello=("))
            A_("Ø del asiento", dh, "mm", tipo, srcd("asiento"), "Cota del corte A-A del plano Fadesa" if rec else
               "Ídem 50 kg" if rod else "Supuesto de diseño", ("catalogo.py", "cuello=("))
            continue
        if k == "varilla":
            A_("Ø", g["varilla"], "mm", T_DIS, ["MP:VARILLA", "C:recipiente"],
               "Ø8 decidido por FLAMA (planilla MP-22); sin cálculo", ("modelo3d.py", "piezas[\"varilla\"]"))
            A_("Largo", r1(H), "mm", T_CAL, ["CALC"], "Largo del cuerpo − 2 × 15 mm", ("modelo3d.py", "piezas[\"varilla\"]"))
            continue

        # -------------------------------------------- válvula (kit comprado HZ; geometría representativa)
        vi = info["valvula"]
        sv = vi["s"]
        if k == "tuerca":
            A_("Ø exterior", r1(g["cuello"][0] + 6 * sv), "mm", T_DIS, ["C:valvula"], f"Ø cuello + 6 × {sv}",
               ("modelo3d.py", 'p["tuerca"]'))
            A_("Alto", r1(10 * sv), "mm", T_DIS, ["C:valvula"], f"10 × {sv}", ("modelo3d.py", "hcol = 10 * s"))
            continue
        if k == "espiga":
            A_("Ø exterior (núcleo de la rosca del cuello)", r1(dr["bore"], 2), "mm", T_CAL, fsrc("rosca") or ["C:recipiente"],
               "Ø menor de la rosca del cuello (M30×1,5 → 28,376; M22×1,5 → 20,376)", ("modelo3d.py", "bore = {"))
            A_("Largo roscado", r1(12 * sv), "mm", T_DIS, ["C:valvula"], f"12 × {sv}", ("modelo3d.py", 'p["espiga"]'))
            continue
        if k == "cuerpo_valvula":
            A_("Ancho × fondo", f"{r1(vi['bw'])} × {r1(vi['bd'])}", "mm", T_DIS, ["C:valvula"],
               f"30 × {sv} y 28 × {sv}", ("modelo3d.py", "bw, bd = 30 * s"))
            A_("Alto del cuerpo", r1(vi["bh"]), "mm", T_CAL if not rod else T_DIS,
               [f"CAT:{cod}:Altura", "C:construir"] if not rod else ["C:valvula"],
               "Se ajusta para que la palanca llegue a la altura del catálogo (22·s a 75·s)" if not rod else "40 × 1,35",
               ("modelo3d.py", "bh = h_total - hcol"))
            continue
        if k == "vastago":
            A_("Ø × alto", f"{r1(8 * sv)} × {r1(3 * sv + 1)}", "mm", T_DIS, ["C:valvula"], f"Ø 8·s; alto 3·s + 1 (s = {sv})",
               ("modelo3d.py", 'p["vastago"]'))
            continue
        if k == "eje":
            A_("Ø × largo", f"{r1(6 * sv)} × {r1(vi['bd'] + 8 * sv)}", "mm", T_DIS, ["C:valvula"],
               "Ø 6·s; largo = fondo del cuerpo + 8·s", ("modelo3d.py", 'p["eje"]'))
            continue
        if k in ("manija_superior", "manija_inferior"):
            A_("Largo", r1(L), "mm", T_CAL if not rod else T_DIS,
               [f"CAT:{cod}:Ancho", "C:construir"] if not rod else ["C:valvula"],
               "Llega hasta el ancho total del catálogo (ajuste de la envolvente)" if not rod else "x_tip = 0,75·R",
               ("modelo3d.py", 'p["manija_superior"]' if k == "manija_superior" else 'p["manija_inferior"]'))
            A_("Ancho × espesor", f"{r1(20 * sv)} × {r1(4 * sv)}", "mm", T_DIS, ["C:valvula"], f"20·s × 4·s (s = {sv})",
               ("modelo3d.py", "lev_t, lev_w = 4 * s"))
            continue
        if k == "pasador":
            A_("Ø alambre × largo", f"{r1(3.2 * sv)} × {r1(vi['bd'] + 16 * sv)}", "mm", T_DIS, ["C:valvula"],
               "Ø 3,2·s; largo = fondo del cuerpo + 16·s; anilla Ø 18·s", ("modelo3d.py", 'p["pasador"]'))
            continue
        if k == "manometro":
            A_("Ø de la esfera", vi["man_d"], "mm", T_DIS, ["C:manual" if not rod else "C:rodante"],
               "28 (1 kg), 38 (manuales), 50 (rodantes)", ("modelo3d.py", "man_d = 28.0" if not rod else "man_d=50.0"))
            ps = B._ps(m)
            A_("Rango y sector verde", f"0-{ps * 2.5 if ps < 5 else 25:g} / {ps:g}", "MPa", T_CAL,
               [f"CAT:{cod}:Ps", "N:3533"], "Rango = 2,5 × presión de servicio del catálogo; sello IRAM 3533",
               ("bom.py", 'if k == "manometro"'))
            continue
        if k == "disco_seguridad":
            A_("Tapón hexagonal (entre caras × alto)", f"{r1(14 * sv)} × {r1(9 * sv)}", "mm", T_DIS, ["C:valvula"],
               "Hexágono 14·s × 9·s; rotura 18-21 MPa (materiales.py)", ("modelo3d.py", 'p["disco_seguridad"]'))
            continue
        if k == "cano_pesca":
            de, di = (A, A - 2 * (2.5 if rod else (1.5 * sv if fam != "co2" else 1.5)))
            A_("Ø exterior", r1(de), "mm", T_DIS, ["C:manual" if not rod else "C:rodante"],
               "12·s (manuales), 10 (CO₂), 24 (rodantes)", ("modelo3d.py", 'out["cano_pesca"]'))
            A_("Largo", r1(H), "mm", T_CAL, ["C:manual" if not rod else "C:rodante"],
               f"Desde {18 if not rod else 25} mm sobre el fondo hasta la válvula", ("modelo3d.py", "zf = dr[\"z_fondo\"] + g[\"tf\"]"))
            continue
        if k == "racor":
            A_("Ø × largo", f"{r1(min(A, H))} × {r1(L)}", "mm", T_DIS, ["C:manual" if not rod else "C:rodante"],
               "Ø18 × 12 (manuales), Ø24 × 16 (rodantes)", ("modelo3d.py", 'out["racor"]'))
            continue
        if k in ("manguera", "manguera_enrollada"):
            r = 12.5 if (rod) else {"co2": 7.0}.get(fam, 8.0)
            if k == "manguera" and not rod:
                r = (A / 2) if A < 40 else r
            largo = s.Volume() / (math.pi * r * r)
            A_("Ø exterior", r1(2 * r), "mm", T_DIS, ["C:manual" if not rod else "C:rodante"],
               "16 (manuales), 14 (CO₂), 25 (rodantes)", ("modelo3d.py", "d_hose = 0 if chico" if not rod else "d_hose = 25.0"))
            A_("Largo desarrollado dibujado", r1(largo, 0), "mm", T_CAL, ["CALC"],
               "Volumen del sólido / (π r²); en rodantes la manga real es la del catálogo", ("bom.py", "largo = s.Volume()"))
            continue
        if k in ("tobera", "lanza", "difusor", "empunadura", "brazo_difusor", "tobera_campana", "suncho", "pie",
                 "valvula_esferica", "apoyo", "soportes_manguera", "sunchos_bastidor", "bastidor", "eje_ruedas",
                 "rueda_der", "llanta_der"):
            if k == "rueda_der":
                Dw = float(m.spec["Diámetro de rueda (mm)"])
                A_("Ø exterior", Dw, "mm", T_CAT, [f"CAT:{cod}:Rueda"], "Diámetro de rueda del catálogo",
                   ("modelo3d.py", "Dw = float"))
                A_("Ancho de banda", info["bw_w"], "mm", T_DIS, ["C:rodante"], "55 (Ø300), 70 (Ø350), 80 (Ø400)",
                   ("modelo3d.py", "bw_w = 55.0"))
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
                A_("Ø × largo", f"25 × {r1(L)}", "mm", T_DIS, ["C:rodante", f"CAT:{cod}:Ancho"],
                   "Ø25 SAE 1045; largo = trocha (ancho catálogo − banda) − banda + 20", ("modelo3d.py", 'out["eje_ruedas"]'))
                continue
            if k == "bastidor":
                largo = s.Volume() / (math.pi * 12.7 ** 2)
                A_("Caño", "Ø25,4 × 1,6", "mm", T_DIS, ["C:rodante"], "Caño SAE 1010 (MP-CANO-CARRO)", ("modelo3d.py", "rt = 12.7"))
                A_("Altura del arco (= altura total)", r1(m.H), "mm", T_CAT, [f"CAT:{cod}:Altura"],
                   "Cota superior del arco = altura del catálogo", ("modelo3d.py", "ztop_arc = H - rt"))
                A_("Separación de parantes (ejes)", r1(2 * info["xa"]), "mm", T_CAL, ["C:rodante", f"CAT:{cod}:Ancho"],
                   "2 × min(R + 45; trocha/2 − banda/2 − 20)", ("modelo3d.py", "xa = min(R + 45"))
                A_("Largo desarrollado", r1(largo, 0), "mm", T_CAL, ["CALC"], "Volumen del sólido / (π × 12,7²)",
                   ("bom.py", "largo = s.Volume()"))
                continue
            if k == "sunchos_bastidor":
                ws, ts = M.planchuela(R)
                A_("Planchuela", f"{ws:g} × {ts:g}", "mm", T_DIS, ["C:planchuela", "FE:25 kg:masa"],
                   "30 × 3 hasta Ø330; 40 × 4 por encima (ajustado a la masa de los planos Fadesa)", ("modelo3d.py", "def planchuela"))
                A_("Ø interior de la abrazadera", r1(D), "mm", T_CAL, ["CALC"], "= Ø del recipiente", ("modelo3d.py", "b = _tube(R + ts"))
                A_("Cantidad de abrazaderas y altura", "2 (a 25 % y 85 % del cuerpo)", "-", T_DIS, ["C:rodante"],
                   "zb + 0,25·hc y zb + 0,85·hc", ("modelo3d.py", "zs1 = dr[\"zb\"]"))
                continue
            if k == "soportes_manguera":
                A_("Planchuela", "30 × 3", "mm", T_DIS, ["C:rodante"], "3 soportes de planchuela 30 × 3",
                   ("modelo3d.py", "planchuela 30 × 3"))
                continue
            if k == "apoyo":
                A_("Largo × ancho × alto", "70 × 50 × 55", "mm", T_DIS, ["C:rodante"], "Chapa plegada e≈3,2 (factor 0,20)",
                   ("modelo3d.py", "_box(70, 50, 55"))
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
            if k == "tobera":
                if m.descarga == "tobera_1kg":
                    A_("Ø base / Ø punta × largo", f"{r1(12 * sv)} / {r1(8 * sv)} × 26", "mm", T_DIS, ["C:manual"],
                       "Cono 6·s → 4·s de radio", ("modelo3d.py", "noz = cq.Solid.makeCone"))
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
