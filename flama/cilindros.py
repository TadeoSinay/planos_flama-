"""Cilindros (recipientes ABC vendidos sueltos como repuesto): plano completo FL_REC_<tamaño> de 3 hojas y
despiece FL_DES_REC_<tamaño>. Salida en salida/cilindros/ (separada de accesorios y complementarios).

  Hoja 1  Plano de fabricación (flama/recipientes.py): vista, corte A-A, vista D, detalles, tolerancias.
  Hoja 2  Especificaciones, verificación normativa y plan de inspección y ensayos.
  Hoja 3  Identificación, protección, protocolo y embalaje del cilindro suelto.
  Despiece  isometría explosionada con globos ligada al BOM (hoja FL_REC_* del Excel).

Fuentes (se citan apartados, no se transcriben):
  IRAM 3523:1983 (manuales): 3.2.1 a) material y espesor mínimo; 3.2.4 costuras y procesos; 4.1.1 fondo de apoyo;
      4.1.2 abertura; 4.1.3 estanquidad y expansión; 4.1.4 rotura; 4.14 corrosión (IRAM 121); 5.1 marcado;
      5.3 pintura; cap. 6 inspección y recepción (lote, visual, muestreo IRAM 18, rotura por lote).
  IRAM 3550:1981 (sobre ruedas): 3.2.1 material; 3.2.2 costuras y procesos; 3.11 pintura; 4.1.2 soldadura
      (tracción y plegado IRAM 609); 4.1.3 espesor (fórmula 4.1.3.1 y mínimos 4.1.3.2); 4.1.4 estanquidad;
      4.1.5 abertura; 4.1.6 expansión; 4.2 dispositivo de seguridad; 4.5 niebla salina; 5.1 marcado.
"""

import math
import os

import cadquery as cq
import shapely.geometry as sg

from . import modelo3d as M
from . import vistas as V
from . import recipientes as RC
from .lamina import Hoja, nuevo_doc, A, ESCALAS, FORMATOS, ROT_H
from .planos import FECHA, DIBUJO, _tabla, _n

SEPARACION = 60.0
SIGMA_F = 265.0      # MPa: fluencia que debe acreditar el certificado de la chapa LAC de rodantes (50 kg con 3,2 mm)
SIGMA_U = 340.0      # MPa: resistencia a la tracción que debe acreditar el certificado de la chapa LAF de manuales
# Ninguna cotización trae certificado (Pacheco: «Requiere certificado: NO»): son requisitos de compra, no datos.
ETIQ_REC = (100.0, 60.0)    # etiqueta de identificación del cilindro suelto (diseño FLAMA)


def _p(v):
    return float(str(v).replace(",", "."))


def _rosca_menor(rosca, bore):
    """Diámetro interior de la abertura roscada (mm): menor de la rosca o el agujero del modelo."""
    if rosca.startswith("M"):
        d, paso = rosca[1:].split("x")
        return round(float(d) - 1.0825 * float(paso.replace(",", ".")), 1)
    return round(bore, 1)


def e_3550(D, P, sf=SIGMA_F):
    """IRAM 3550 4.1.3.1: espesor de pared necesario (mm) para D ext., presión de ensayo P (MPa), σadm = 2/3 σf."""
    r = P / (2 / 3 * sf)
    return D / 2 * (1 - math.sqrt((1 - 1.3 * r) / (1 + 0.4 * r)))


def verificacion(m):
    """Filas (requisito, apartado, exigido, plano, estado) del recipiente contra su norma."""
    g, s = m.geo, m.spec
    rod = m.familia == "rodante"
    D = 2 * g["R"]
    t, td, tf = g["t"], g["td"], g["tf"]
    Ps, PE = _p(s["Presión de servicio (MPa)"]), _p(s["Presión de ensayo (MPa)"])
    _, dr = M.recipiente(dict(g), 0.0, costura=True)
    ab = _rosca_menor(g["cuello"][2], dr["bore"])
    ok, no, rev = "CUMPLE", "NO CUMPLE", "VERIFICAR"
    f = []
    if not rod:
        f.append(("Material", "3523 3.2.1 a", "acero al C, IRAM-IAS U 500-04/-05/-506 + recubrimiento exterior",
                  "LAF U 500-05 (1 kg: caño c-c) + pintura tercerizada", ok))
        f.append(("Espesor mínimo", "3523 3.2.1 a", "≥ 0,71 mm", f"{_n(t, 2)} / {_n(td, 2)} / {_n(tf, 2)} mm",
                  ok if min(t, td, tf) >= 0.71 else no))
        f.append(("Costuras", "3523 3.2.4.1", "≤ 1 longitudinal y ≤ 2 transversales", "1 long. + 2 transv.", ok))
        f.append(("Proceso de soldadura", "3523 3.2.4.2", "automático: arco sumergido, resistencia, atm. inerte o "
                  "brazing", "MAG (135) con Arcal 21 (Ar + 8 % CO₂, M20; Air Liquide): decisión FLAMA. La mezcla es activa: "
                  "acreditar con el certificador en el ensayo de tipo (probetas IRAM 609 y PH)", rev))
        f.append(("Abertura roscada", "3523 4.1.2", "Ø interior ≥ 19 mm", f"{_n(ab, 1)} mm ({g['cuello'][2]})",
                  ok if ab >= 19 else no))
        f.append(("Fondo de apoyo", "3523 4.1.1", "si el fondo cóncavo apoya: e ≥ 1,5 × e cuerpo",
                  "apoya la pollera del cuerpo; el fondo no es apoyo" if g["tipo_fondo"] == "concavo" else
                  "fondo convexo; apoya en base/soporte", ok))
        f.append(("Estanquidad y expansión", "3523 4.1.3", f"2,5 × Ps = {_n(2.5 * Ps, 2)} MPa (≥ 0,8); def. "
                  "permanente ≤ 10 % de la total", f"PE {_n(PE, 1)} MPa", ok if PE >= max(2.5 * Ps, 0.8) - 1e-6 else no))
        pb = 2 * t * SIGMA_U / D
        f.append(("Rotura", "3523 4.1.4", f"sin falla a 2 × PE = {_n(2 * PE, 1)} MPa; si rompe en soldadura ≥ 8 × Ps "
                  f"= {_n(8 * Ps, 1)}", f"Barlow 2·e·σu/D = {_n(pb, 1)} MPa (σu {SIGMA_U:.0f})",
                  ok if pb >= 2 * PE * 1.1 else rev if pb >= 2 * PE else no))
        f.append(("Corrosión", "3523 4.14", "niebla salina IRAM 121 sin corrosión del base",
                  "pintura tercerizada (Prymax): exigir informe IRAM 121", rev))
        f.append(("Pintura", "3523 5.3", "rojo 03-1-050 IRAM-DEF D 10-54", "rojo 03-1-050", ok))
        f.append(("Marcado", "3523 5.1", "fabricante, n° de recipiente, año (2 díg.)", M.marcado(m)[1], ok))
    else:
        emin = 2.9 if D <= 320 else 4.5
        ef = e_3550(D, PE)
        f.append(("Material", "3550 3.2.1", "IRAM-IAS U 500-04/-05/-506 + recubrimiento anticorrosivo",
                  f"LAC U 500-04 (cotizada); σf ≥ {SIGMA_F:.0f} MPa en certificado + pintura", ok))
        f.append(("Costuras", "3550 3.2.2.1", "≤ 1 longitudinal y ≤ 2 transversales", "1 long. + 2 transv.", ok))
        f.append(("Proceso de soldadura", "3550 3.2.2.2", "automático: arco sumergido, resistencia, atm. inerte o "
                  "brazing", "MAG (135) con Arcal 21 (Ar + 8 % CO₂, M20): decisión FLAMA. La mezcla es activa: acreditar con el "
                  "certificador en el ensayo de tipo (tracción y plegado 4.1.2)", rev))
        f.append(("Soldadura: tracción", "3550 4.1.2.1", "≥ resistencia de la chapa (IRAM 609)", "probeta por lote", ok))
        f.append(("Soldadura: plegado", "3550 4.1.2.2", "sin fisuras (IRAM 609)", "probeta por lote", ok))
        f.append(("Espesor por cálculo", "3550 4.1.3.1", f"e ≥ {_n(ef, 2)} mm (D {D:.0f}, PE {_n(PE, 1)}, "
                  f"σadm 2/3·{SIGMA_F:.0f})", f"{_n(t, 2)} mm", ok if t >= ef * 1.05 else rev if t >= ef else no))
        f.append(("Espesor mínimo", "3550 4.1.3.2", f"≥ {_n(emin, 1)} mm (Ø ext. {'≤' if D <= 320 else '>'} 320)",
                  f"{_n(t, 2)} mm", ok if t >= emin else no))
        f.append(("Estanquidad", "3550 4.1.4", f"2 × Ps = {_n(2 * Ps, 1)} → ≥ 4 MPa sin pérdidas",
                  f"PE {_n(PE, 1)} MPa", ok if PE >= max(2 * Ps, 4.0) - 1e-6 else no))
        amin = 25 if "25kg" in m.codigo else 70
        f.append(("Abertura", "3550 4.1.5", f"Ø interior ≥ {amin} mm", f"{_n(ab, 1)} mm ({g['cuello'][2]})",
                  ok if ab >= amin else no))
        f.append(("Expansión", "3550 4.1.6", "a 2 × Ps (≥ 4 MPa): def. permanente ≤ 10 % de la total",
                  f"PE {_n(PE, 1)} MPa", ok))
        f.append(("Dispositivo de seguridad", "3550 4.2", "opcional; actúa entre 70 y 90 % de PE",
                  f"no lleva (si se agrega: {_n(0.7 * PE, 1)}-{_n(0.9 * PE, 1)} MPa)", ok))
        f.append(("Niebla salina", "3550 4.5", "240 h IRAM 121 sin corrosión",
                  "pintura tercerizada de carros: exigir informe IRAM 121", rev))
        f.append(("Pintura", "3550 3.11", "rojo 03-1-050", "rojo 03-1-050", ok))
        f.append(("Marcado", "3550 5.1", "fabricante, n° de serie, presión de ensayo, año", M.marcado(m)[1], ok))
    return f


def plan_ensayos(m):
    rod = m.familia == "rodante"
    n = "3550" if rod else "3523"
    f = [("Lote", f"{n} cap. 6", "recipientes de iguales características, antes de granallar y pintar", "por turno"),
         ("Inspección visual y dimensional", f"{n} cap. 6 · 7.1", "aspecto, cordones, rosca (calibre pasa/no pasa), "
          "espesor (±0,01)", "100 %"),
         ("Prueba hidráulica a PE", f"{n} 4.1.3/4.1.4 · IRAM 2587", "sin pérdidas ni deformación visible "
          "(FLAMA: 100 %)", "100 %"),
         ("Expansión volumétrica (camisa de agua)", f"{n} · IRAM 2587", "def. permanente ≤ 10 % de la total",
          "10 % del lote (IRAM 18)" if not rod else "muestra por lote"),
         ("Rotura", "3523 4.1.4 · 6.1.4" if not rod else "3550 (criterio FLAMA)", "a 2 × PE sin falla; luego "
          "hasta romper", "1 por lote")]
    if rod:
        f.append(("Tracción y plegado de soldadura", "3550 4.1.2 · IRAM 609", "probetas del cupón de la costura",
                  "1 juego por lote de chapa"))
    f += [("Niebla salina", f"{n} · IRAM 121", "probetas pintadas", "aprobación de prototipo / semestral"),
          ("Rechazo", f"{n} cap. 6", "si falla la muestra: ensayo del 100 % del lote o rechazo del lote", "-")]
    return f


NORMAS_REC = [("IRAM 3523 / IRAM 3550", "Matafuegos de polvo manuales / sobre ruedas (recipiente: cap. 3, 4, 5 y 6)"),
              ("IRAM-IAS U 500-04 / -05 / -506", "Chapas de acero laminadas en caliente / en frío / para cilindros"),
              ("IRAM 2587", "Ensayo hidrostático (estanquidad y expansión)"),
              ("IRAM 609", "Tracción y plegado de la soldadura (rodantes)"),
              ("IRAM 121", "Ensayo de niebla salina"),
              ("IRAM 15 / IRAM 18", "Inspección por atributos / extracción de muestras al azar"),
              ("IRAM 5058 / 5063", "Roscas métricas finas / Whitworth gas (cuello)"),
              ("IRAM-DEF D 10-54", "Colores (rojo 03-1-050)"),
              ("ISO 4063 / ISO 2768-m", "Procesos de soldadura / tolerancias generales"),
              ("IRAM 4503 / IRAM 4508", "Letras del marcado / rótulo del plano")]


def _rot(m, hoja, tipo, sub, esc="-", fmt="A3"):
    return dict(titulo=f"Cilindro {m.nombre.replace('Extintor ', '').replace(' sobre ruedas', ' rodante')}",
                subtitulo=sub, codigo=RC.codigo_rec(m), hoja=hoja, hojas=3, escala=esc,
                material="Chapa LAF IRAM-IAS U 500-05" if m.familia != "rodante" else "Chapa LAC IRAM-IAS U 500-04",
                edicion="0", fecha=FECHA, dibujo=DIBUJO, reviso="", aprobo="", tipo_doc=tipo, empresa="FLAMA S.A.")


def hoja2(m, doc, ox):
    h = Hoja(doc, "A3", ox)
    h.formato()
    h.rotulo(_rot(m, 2, "Especificaciones y ensayos", "Verificación normativa y plan de inspección"))
    X0, Y0, X1, Y1 = h.fx0, h.fy0, h.fx1, h.fy1
    h.texto(f"CILINDRO {RC.codigo_rec(m)} - ESPECIFICACIÓN, VERIFICACIÓN NORMATIVA Y ENSAYOS", ((X0 + X1) / 2, Y1 - 6),
            4, A.MIDDLE_CENTER)
    filas = [("Requisito", "Apartado", "Exigido por la norma", "Plano FLAMA", "Estado")]
    filas += verificacion(m)
    y = _tabla(h, X0 + 4, Y1 - 12, filas, [38, 24, 120, 112, 22], alto=5.2, hs=(2.0, 2.0, 1.7, 1.7, 2.0),
               encabezado="VERIFICACIÓN DEL RECIPIENTE CONTRA IRAM " + m.spec["Norma IRAM extintor"])
    fe = [("Ensayo", "Apartado", "Criterio de aceptación", "Frecuencia")] + plan_ensayos(m)
    y = _tabla(h, X0 + 4, y - 4, fe, [56, 40, 160, 60], alto=4.8, hs=(2.0, 1.8, 1.7, 1.8),
               encabezado="PLAN DE INSPECCIÓN Y ENSAYOS DE FABRICACIÓN (por lote)")
    fn = [("Norma", "Tema")] + NORMAS_REC
    _tabla(h, X0 + 4, min(y - 4, Y0 + ROT_H + 2 + 4.2 * 12), fn, [52, 120], alto=4.2, hs=(1.9, 1.7),
           encabezado="NORMAS APLICABLES")
    for i, t in enumerate(["NOTAS: 1) Normas citadas por apartado; no se transcriben.",
                           f"2) σu {SIGMA_U:.0f} MPa (manuales) y σf {SIGMA_F:.0f} MPa (rodantes) se",
                           "exigen en el certificado de colada de cada lote de chapa.",
                           "3) VERIFICAR = margen < 10 %, o falta el documento",
                           "(certificado / informe) que lo acredite.",
                           "4) NO CUMPLE = lo documentado contradice la norma."]):
        h.texto(t, (X0 + 182, Y0 + ROT_H + 40 - 4 * i), 1.9)
    return h


def _vista_ubicacion(h, m, zona, piezas):
    comp = M.compuesto({k: v for k, v in piezas.items() if k != "soldaduras"})
    proy = V.proyectar(comp, "anterior", tol=0.4, ocultas=False)
    ex = V.extension(proy["vis"])
    x0, y0, x1, y1 = zona
    f = next(s for s in (1 / 2, 1 / 5, 1 / 10, 1 / 20) if (ex[2] - ex[0]) * s <= x1 - x0 - 20 and
             (ex[3] - ex[1]) * s <= y1 - y0 - 18)
    Tx = (x0 + x1) / 2 - (ex[0] + ex[2]) / 2 * f
    Ty = y0 + 8 - ex[1] * f
    h.prims(proy["vis"], "01-VISIBLE", (Tx, Ty, f))
    return Tx, Ty, f


def piezas_cilindro(m):
    """Recipiente + tapón protector + etiqueta de identificación (sólidos para el despiece y la hoja 3)."""
    g = dict(m.geo)
    p, dr = M.recipiente(g, 0.0, costura=True)
    p = {k: v for k, v in p.items() if k in RC.PIEZAS_REC}
    cb = p["cuello"].BoundingBox()
    rt = g["cuello"][0] / 2 + 1.5
    p["tapon"] = (cq.Workplane("XY").circle(rt).extrude(18.0).faces(">Z").workplane().circle(rt * 0.55)
                  .extrude(4.0).translate((0, 0, cb.zmax - 14.0)).val())
    R = dr["R"]
    zc = (dr["z_union"] + max(dr["zb"], dr["z_fondo"])) / 2
    p["etiqueta_rec"] = M._sector(R, R + 0.3, ETIQ_REC[1], zc - ETIQ_REC[1] / 2, ETIQ_REC[0], 0.0, 0.0)
    return p, dr


def hoja3(m, doc, ox):
    rod = m.familia == "rodante"
    h = Hoja(doc, "A3", ox)
    h.formato()
    h.rotulo(_rot(m, 3, "Identificación y embalaje", "Marcado, etiqueta, tapón, protocolo y embalaje"))
    X0, Y0, X1, Y1 = h.fx0, h.fy0, h.fx1, h.fy1
    s = m.spec
    h.texto(f"CILINDRO {RC.codigo_rec(m)} - IDENTIFICACIÓN, PROTECCIÓN, PROTOCOLO Y EMBALAJE", ((X0 + X1) / 2, Y1 - 6),
            4, A.MIDDLE_CENTER)
    piezas, dr = piezas_cilindro(m)
    # R1 ubicación
    Tx, Ty, f = _vista_ubicacion(h, m, (X0 + 4, Y0 + 60, X0 + 120, Y1 - 12), piezas)
    eb = piezas["etiqueta_rec"].BoundingBox()
    cu = 2 * dr["R"] * math.sin(ETIQ_REC[0] / 2 / dr["R"])
    h.rayado(sg.box(Tx - cu / 2 * f, Ty + eb.zmin * f, Tx + cu / 2 * f, Ty + eb.zmax * f), 45, 1.5)
    tb = piezas["tapon"].BoundingBox()
    h.nota_referencia("Tapón protector", (Tx, Ty + (tb.zmin + tb.zmax) / 2 * f), (Tx + dr["R"] * f + 8,
                      Ty + tb.zmax * f + 6), 2.2)
    en_cupula = M.marcado(m)[0] == "cupula"
    # franja superior del cuerpo, cara opuesta a la etiqueta; 1 kg: sobre la cúpula
    zm = (dr["z_union"] + 0.45 * (dr["z_cupula"] - dr["z_union"])) if en_cupula else dr["z_union"] - 12.0
    h.rect(Tx - 10 * f, Ty + (zm - 3) * f, Tx + 10 * f, Ty + (zm + 3) * f, "02-OCULTA")
    h.nota_referencia("Marcado grabado en la cúpula" if en_cupula else "Marcado grabado en el cuerpo (cara posterior)",
                      (Tx + 10 * f, Ty + zm * f),
                      (Tx + dr["R"] * f + 8, Ty + dr["z_cuello"] * f + 4), 2.2)
    h.nota_referencia("Etiqueta (R2)", (Tx, Ty + (eb.zmin + eb.zmax) / 2 * f), (Tx - dr["R"] * f - 6,
                      Ty + eb.zmin * f - 8), 2.2)
    h.texto(f"R1 UBICACIÓN (vista anterior, esc. 1:{_n(1 / f, 0)})", (X0 + 62, Y1 - 13), 3, A.MIDDLE_CENTER)
    # R2 etiqueta del cilindro suelto (esc. 1:1)
    ex_, ey_ = X0 + 132, Y1 - 82
    w, hh = ETIQ_REC
    h.texto("R2 ETIQUETA DE IDENTIFICACIÓN DEL CILINDRO SUELTO (1:1)", (ex_ + w / 2, ey_ + hh + 6), 3, A.MIDDLE_CENTER)
    h.rect(ex_, ey_, ex_ + w, ey_ + hh, "01-VISIBLE")
    h.texto("FLAMA S.A.", (ex_ + 3, ey_ + hh - 3), 5, A.TOP_LEFT)
    lin = [f"RECIPIENTE PARA MATAFUEGO DE POLVO {m.capacidad.upper()}",
           "SIN VÁLVULA NI CARGA - NO PRESURIZAR SIN VÁLVULA",
           f"CÓDIGO {RC.codigo_rec(m)}   N° SERIE ______   LOTE CHAPA ____",
           f"PS {s['Presión de servicio (MPa)']} MPa   PE {s['Presión de ensayo (MPa)']} MPa   PH: MM/AA",
           f"IRAM {s['Norma IRAM extintor']} (recipiente) - PROTOCOLO N° ______",
           "USO EXCLUSIVO POLVO ABC IRAM 3569 / N2 SECO",
           "EL ARMADO COMO MATAFUEGO REQUIERE LICENCIA IRAM",
           "DEL ARMADOR. RETIRAR ESTA ETIQUETA AL ARMAR.",
           "INDUSTRIA ARGENTINA"]
    for i, t in enumerate(lin):
        h.texto(t, (ex_ + 3, ey_ + hh - 12 - 5.0 * i), 2.0 if i < 6 else 1.8)
    q = 20
    h.rect(ex_ + w - q - 3, ey_ + 3, ex_ + w - 3, ey_ + 3 + q, "08-FINA")
    h.texto("QR GS1", (ex_ + w - 3 - q / 2, ey_ + 3 + q / 2), 2.0, A.MIDDLE_CENTER)
    h.cota_lineal((ex_, ey_), (ex_ + w, ey_), (ex_, ey_ - 6), 0, 1)
    h.cota_lineal((ex_ + w, ey_), (ex_ + w, ey_ + hh), (ex_ + w + 6, ey_), 90, 1)
    h.texto("Poliéster autoadhesivo removible, impresión térmica. Diseño FLAMA (sin norma: el recipiente suelto no",
            (ex_, ey_ - 13), 1.8)
    h.texto("lleva placa IRAM 3534; ésta la pone quien arma el matafuego). Va sobre el eje de la futura placa.",
            (ex_, ey_ - 16.5), 1.8)
    # R3 marcado grabado
    mx, my = X0 + 132, Y0 + 116
    h.texto("R3 MARCADO GRABADO (IRAM " + s["Norma IRAM extintor"] + " 5.1)", (mx + 60, my + 30), 3, A.MIDDLE_CENTER)
    txt = "FLAMA S.A.  N° 000001  " + (f"PE {s['Presión de ensayo (MPa)']} MPa  " if rod else "") + "26"
    h.rect(mx, my + 14, mx + 120, my + 24, "01-VISIBLE")
    h.texto(txt, (mx + 60, my + 19), 3.5, A.MIDDLE_CENTER)
    h.texto(("Fabricante, n° de serie, presión de ensayo y año (2 díg.)" if rod else
             "Fabricante, n° de recipiente y año (2 díg.)"), (mx, my + 9), 1.9)
    l1, l2 = M.marcado(m)[2]
    h.texto(l1, (mx, my + 5.5), 1.9)
    h.texto(l2 + " letra 5 mm IRAM 4503; legible después de pintar.", (mx, my + 2), 1.9)
    h.rect(mx + 122, my + 15.5, mx + 137, my + 22.5, "01-VISIBLE")
    h.texto("DPS", (mx + 129.5, my + 19), 3.0, A.MIDDLE_CENTER)
    h.texto("cuño DPS 15 × 7 junto al n° (Res. 349/07 anexo IV)", (mx, my - 1.5), 1.9)
    # R4 tapón protector
    tx, ty = X0 + 262, Y1 - 50
    rt = m.geo["cuello"][0] / 2 + 1.5
    k = min(1.0, 30 / rt)
    h.texto("R4 TAPÓN PROTECTOR DE ROSCA", (tx + 35, ty + 34), 3, A.MIDDLE_CENTER)
    h.rect(tx + 35 - rt * k, ty, tx + 35 + rt * k, ty + 18 * k, "01-VISIBLE")
    h.rect(tx + 35 - rt * 0.55 * k, ty + 18 * k, tx + 35 + rt * 0.55 * k, ty + 22 * k, "01-VISIBLE")
    h.cota_lineal((tx + 35 - rt * k, ty), (tx + 35 + rt * k, ty), (tx, ty - 6), 0, 1 / k, prefijo="%%c")
    h.texto(f"PE baja densidad, a presión sobre {m.geo['cuello'][2]}; protege rosca e interior (polvo/humedad)",
            (tx - 4, ty - 12), 1.8)
    h.texto("hasta el armado. Se coloca después del secado interior posterior a la PH.", (tx - 4, ty - 15.5), 1.8)
    # R5 protocolo
    px, py = X0 + 248, Y0 + 150
    filas = [("Campo", "Dato"), ("Código / n° de serie", RC.codigo_rec(m) + " / ______"),
             ("Lote de chapa / colada", "______ (σu / σf del certificado)"),
             ("PE aplicada / tiempo", f"{s['Presión de ensayo (MPa)']} MPa / ≥ 30 s"),
             ("Expansión total / permanente", "____ / ____ cm³ (≤ 10 %)"),
             ("Visual / dimensional / rosca", "OK / OK / pasa-no pasa"), ("Resultado y firma", "APROBADO ____")]
    _tabla(h, px, py + 34, filas, [42, 88], alto=4.6, hs=(1.9, 1.8), encabezado="R5 PROTOCOLO DE ENSAYO (acompaña)")
    # R6 tratamiento y embalaje
    bx, by = X0 + 132, Y0 + ROT_H + 6
    lineas = ["R6 TRATAMIENTO SUPERFICIAL Y EMBALAJE",
              "Exterior: granallado Sa 2½ + pintura en polvo rojo 03-1-050 (DOC-01), espesor seco según DOC-01.",
              "Interior: limpio, seco (secado en horno tras la PH) y sin pintar; resistente al agente (3523 3.2.2).",
              "Embalaje: caja de cartón (manuales) o funda PE + esquineros (rodantes); etiqueta de caja con código,",
              "serie y lote; pallet 1200 × 1000 con film stretch. Ver BOM hoja " + RC.codigo_rec(m) + " (S7)."]
    for i, t in enumerate(lineas):
        h.texto(t, (bx, by + 30 - 5 * i), 3 if i == 0 else 1.9)
    return h


def generar_cilindro(m):
    doc, fmt, inf = RC.generar_recipiente(m, hojas=3)
    ox2 = FORMATOS[fmt][0] + SEPARACION
    ox3 = ox2 + FORMATOS["A3"][0] + SEPARACION
    hoja2(m, doc, ox2)
    hoja3(m, doc, ox3)
    hojas = [("Hoja1_Fabricacion", fmt, 0.0), ("Hoja2_Especificaciones", "A3", ox2),
             ("Hoja3_Identificacion", "A3", ox3)]
    return doc, hojas, inf


# ------------------------------------------------------------------ despiece del cilindro
def despiece(m):
    from . import bom as B
    from .despiece import _anclaje, _repartir
    piezas, dr = piezas_cilindro(m)
    filas = B.bom_producto(m, cilindro=True)
    R = dr["R"]
    gap = max(30.0, 0.35 * R)
    d = {k: (0.0, 0.0, 0.0) for k in piezas}
    cbz = piezas["cuerpo"].BoundingBox()
    d["cupula"] = (0, 0, gap)
    d["cuello"] = (0, 0, 2 * gap)
    d["tapon"] = (0, 0, 3 * gap)
    d["fondo"] = (0, 0, -gap)
    d["etiqueta_rec"] = (0, -1.2 * R, 0)
    if "placas_refuerzo" in piezas:
        d["placas_refuerzo"] = (-2.2 * R, 0, 0)
    mov = {k: s.translate(cq.Vector(*d[k])) for k, s in piezas.items() if k != "soldaduras"}
    proy = V.proyectar(cq.Compound.makeCompound(list(mov.values())), "iso", tol=0.4, ocultas=False)
    ex = V.extension(proy["vis"])
    doc = nuevo_doc()
    h = Hoja(doc, "A3")
    h.formato()
    tabla_w = 175.0
    zona = (h.fx0 + 30, h.fy0 + 8, h.fx1 - tabla_w - 34, h.fy1 - 18)
    esc = next(e for e in ESCALAS + [(1, 50)] if (ex[2] - ex[0]) * e[0] / e[1] <= zona[2] - zona[0] and
               (ex[3] - ex[1]) * e[0] / e[1] <= zona[3] - zona[1])
    f = esc[0] / esc[1]
    ox = (zona[0] + zona[2]) / 2 - (ex[0] + ex[2]) / 2 * f
    oy = (zona[1] + zona[3]) / 2 - (ex[1] + ex[3]) / 2 * f
    h.prims(proy["vis"], "01-VISIBLE", (ox, oy, f))
    # globos = sufijo del código BOM
    sufijo = {}
    for r in filas:
        if r["nivel"] == 2:
            sufijo.setdefault(r["desc"].strip().lower(), r["codigo"].split("-")[-1])
    nombre_bom = {"cuerpo": "cuerpo", "cupula": "cúpula", "fondo": "fondo", "cuello": "cuello", "tapon": "tapón",
                  "etiqueta_rec": "etiqueta de identificación", "placas_refuerzo": "placas de refuerzo"}
    glob = {}
    for k in mov:
        for desc, suf in sufijo.items():
            if nombre_bom[k] in desc:
                glob[k] = suf
                break
    xc = (zona[0] + zona[2]) / 2
    items = []
    for k, s in mov.items():
        if k not in glob:
            continue
        bb = s.BoundingBox()
        c = V.proyectar_punto(((bb.xmin + bb.xmax) / 2, (bb.ymin + bb.ymax) / 2, (bb.zmin + bb.zmax) / 2), "iso")
        lado = -1 if ox + c[0] * f < xc else 1
        a = _anclaje(s, lado)
        items.append((lado, (ox + a[0] * f, oy + a[1] * f), glob[k]))
    for lado in (-1, 1):
        col = sorted([it for it in items if it[0] == lado], key=lambda it: it[1][1])
        xg = (h.fx0 + 14) if lado < 0 else (zona[2] + 16)
        ys = _repartir([it[1][1] for it in col], h.fy0 + 12, h.fy1 - 24, 10)
        for it, y in zip(col, ys):
            h.globo(it[2], it[1], (xg, y), r=4.5)
    h.texto(f"DESPIECE - CILINDRO {m.capacidad.upper()}", (xc, h.fy1 - 7), 5, A.MIDDLE_CENTER)
    h.texto(f"Isometría explosionada, esc. {esc[0]}:{esc[1]}. Globo = sufijo del código BOM (hoja "
            f"{RC.codigo_rec(m)})", (xc, h.fy1 - 13), 2.5, A.MIDDLE_CENTER)
    xt = h.fx1 - tabla_w - 2
    ft = [("Glo.", "Código BOM", "Denominación", "Cant.", "Material")]
    for r in filas:
        if r["nivel"] == 1:
            ft.append(("", r["codigo"], r["desc"].upper()[:40], "", ""))
        elif r["nivel"] == 2:
            suf = r["codigo"].split("-")[-1]
            cant = r["cant"]
            ct = (f"{cant:g}".replace(".", ",") if isinstance(cant, (int, float)) else str(cant)) + \
                 ("" if r["um"] == "u" else " " + r["um"])
            ft.append((suf, r["codigo"], r["desc"].strip()[:42], ct, (r["mat"] or "")[:26]))
    alto = min(4.6, (h.fy1 - 6 - (h.fy0 + ROT_H + 26)) / (len(ft) + 1))
    y = _tabla(h, xt, h.fy1 - 4, ft, [10, 24, 76, 17, 48], alto=alto, hs=(2.2, 2.0, 1.8, 2.0, 1.6),
               encabezado=f"LISTA DE DESPIECE - BOM {RC.codigo_rec(m)}")
    for i, t in enumerate(["NOTAS: 1) Medidas, pesos y normas: salida/bom/FLAMA_BOM.xlsx, hoja " + RC.codigo_rec(m) + ".",
                           "2) Sin globo: consumibles, marcado, protocolo y embalaje (no dibujados).",
                           "3) Cordones de soldadura no se dibujan en el despiece."]):
        h.texto(t, (xt, y - 5 - 4 * i), 2.0)
    cod = "FL_DES_" + RC.codigo_rec(m)[3:]
    h.rotulo(dict(titulo=f"Despiece cilindro {m.capacidad}", subtitulo="Vista explosionada y lista (BOM)", codigo=cod,
                  hoja=1, hojas=1, escala=f"{esc[0]}:{esc[1]}", material="Ver lista", edicion="0", fecha=FECHA,
                  dibujo=DIBUJO, reviso="", aprobo="", tipo_doc="Plano de despiece", empresa="FLAMA S.A."))
    return cod, doc, piezas


def generar(base):
    """Escribe salida/cilindros/: FL_REC_* (3 hojas, DXF/PDF/STEP), despiece/FL_DES_REC_* y FLAMA_cilindros.pdf."""
    import pymupdf
    from . import exportar as X
    carpeta = os.path.join(base, "cilindros")
    total = pymupdf.open()
    for m in RC.modelos_abc():
        cod = RC.codigo_rec(m)
        d = os.path.join(carpeta, cod)
        os.makedirs(d, exist_ok=True)
        doc, hojas, inf = generar_cilindro(m)
        X.preparar_layouts(doc, hojas)
        doc.saveas(os.path.join(d, f"{cod}.dxf"))
        p = X.pdf_hojas(doc, hojas)
        p.set_metadata({"title": f"{cod} - Cilindro {m.capacidad}", "author": "FLAMA S.A."})
        p.save(os.path.join(d, f"{cod}.pdf"))
        total.insert_pdf(p)
        piezas, _ = piezas_cilindro(m)
        X.step({k: v for k, v in piezas.items() if k != "soldaduras"}, os.path.join(d, f"{cod}.step"))
        cod_d, doc_d, _ = despiece(m)
        dd = os.path.join(carpeta, "despiece")
        os.makedirs(dd, exist_ok=True)
        hd = [("Lamina", "A3", 0.0)]
        X.preparar_layouts(doc_d, hd)
        doc_d.saveas(os.path.join(dd, f"{cod_d}.dxf"))
        pd = X.pdf_hojas(doc_d, hd)
        pd.save(os.path.join(dd, f"{cod_d}.pdf"))
        total.insert_pdf(pd)
        print(cod, cod_d, flush=True)
    total.save(os.path.join(carpeta, "FLAMA_cilindros.pdf"))
