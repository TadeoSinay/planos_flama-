"""MRP de insumos de FLAMA (salida/mrp/FLAMA_MRP.xlsx): requerimiento bruto anual 2026-2035 por línea, consolidado por
ítem y política de stock dimensionada para el año 10 (2035). Todo con fórmulas indexadas: los datos entran una sola vez
en las hojas fijas y las demás hojas los leen.

Hojas fijas (dimensionamiento)
  PARAMETROS      cada dato que entra en una cuenta, con ID, valor, unidad y fuente; abajo, los que cambian por año
                  (% de recargas de equipos usados, % del destino CABA)
  PROY_INDEXADO   copia (valores) de «Indexado Dim Técnico» de las Proyecciones
  PROY_RESERVAS   copia (valores) de «Reservas y Sustitutos» de las Proyecciones
  DEMANDA         unidades por año de cada producto, por línea (fórmulas sobre las dos copias)
  ESTACIONALIDAD  perfil mensual de cada producto (Dimensionamiento Técnico) y perfil de cada línea en el año de diseño
  BOM_COEF        lo que se compra por unidad de producto, fila por fila del BOM (FLAMA_BOM.xlsx); en recargas, por
                  servicio (control, mantenimiento, recarga, prueba hidráulica) y mezcla del año
  FAB_COMPRA      de qué materia prima sale cada pieza fabricada y cuánto rinde (procesos de manuales y carros)
  PROCESO         insumos de proceso y embalaje por unidad, puesto por puesto (procesos de manuales y carros)
  COMPRAS         catálogo de ítems: tipo, clase, almacén, proveedor, unidad de compra, lead time y su fuente
Por línea (MANUALES, RODANTES, RECARGAS con los sustitutos, REVENDIDOS)
  INSUMOS_DIRECTOS_<línea> e INSUMOS_INDIRECTOS_<línea>: por ítem, una fila de total y una por producto que lo usa
Consolidado y política
  CONSOLIDADO_INSUMOS  por ítem: tipo, clase, almacén, de qué línea y hoja sale, requerimiento por año y en unidades
                       de compra
  POLITICA_STOCK       por ítem, en el año de diseño: consumo diario promedio y del mes pico, lead time, stock de
                       seguridad, punto de pedido, lote en múltiplos de la unidad de compra, stock máximo y posiciones

Uso: python generar.py --mrp-insumos <Proyecciones.xlsx>   (necesita salida/bom/FLAMA_BOM.xlsx ya recalculado)
"""
import os

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter as L
from openpyxl.workbook.defined_name import DefinedName

from .bom_simple import BLANCO, GRIS_C, GRIS_O, NEGRO, recalcular

AÑOS = list(range(2026, 2036))
LINEAS = ("MANUALES", "RODANTES", "RECARGAS", "REVENDIDOS")
AR = "Arial"
FINO = Side(style="thin", color="BFBFBF")

# ------------------------------------------------------------------ modelos
# (código BOM del producto, prefijo de pieza en el BOM, nombre corto)
FAB = [("ABC_1kg", "ABC1", "ABC 1 kg"), ("ABC_2.5kg", "ABC2.5", "ABC 2,5 kg"), ("ABC_5kg", "ABC5", "ABC 5 kg"),
       ("ABC_10kg", "ABC10", "ABC 10 kg"), ("ABC_25kg", "ABC25", "ABC 25 kg"), ("ABC_50kg", "ABC50", "ABC 50 kg"),
       ("ABC_70kg", "ABC70", "ABC 70 kg"), ("ABC_100kg", "ABC100", "ABC 100 kg")]
MAN, ROD = FAB[:4], FAB[4:]
REV = [("AGUA_10l", "Agua 10 l"), ("AFFF_10l", "AFFF 10 l"), ("AFFF_50l", "AFFF 50 l rodante"), ("BC_5kg", "BC 5 kg"),
       ("SALESK_6l", "Clase K 6 l"), ("CO2_2kg", "CO₂ 2 kg"), ("CO2_5kg", "CO₂ 5 kg"),
       ("HCFC-HFC_5kg", "HCFC/HFC 5 kg"), ("CLASED_9l", "Clase D 9 l")]
NOMBRE = {c: n for c, _, n in FAB} | dict(REV)
PREF = {c: p for c, p, _ in FAB}
# etiquetas de las filas de las Proyecciones
ETIQ = {"ABC 1 kg": "ABC_1kg", "ABC 2,5 kg": "ABC_2.5kg", "ABC 5 kg": "ABC_5kg", "ABC 10 kg": "ABC_10kg",
        "ABC 25 kg s/ruedas": "ABC_25kg", "ABC 50 kg s/ruedas": "ABC_50kg", "ABC 70 kg s/ruedas": "ABC_70kg",
        "ABC 100 kg s/ruedas": "ABC_100kg", "Agua 10 l": "AGUA_10l", "AFFF 10 l": "AFFF_10l",
        "AFFF 50 l s/ruedas": "AFFF_50l", "BC 5 kg": "BC_5kg", "Sales K 6 l": "SALESK_6l", "CO₂ 2 kg": "CO2_2kg",
        "CO₂ 5 kg": "CO2_5kg", "HCFC/HFC 5 kg": "HCFC-HFC_5kg", "Clase D 9 l": "CLASED_9l"}
# pool de sustitutos (Reservas y Sustitutos): tipo del pool y equipo que lo cubre
POOL = [("ABC 5 kg (cubre ABC 1; 2,5 y 5 kg)", "ABC_5kg"), ("ABC 10 kg", "ABC_10kg"), ("Agua 10 l", "AGUA_10l"),
        ("AFFF 10 l", "AFFF_10l"), ("AFFF 50 l s/ruedas", "AFFF_50l"), ("BC 5 kg", "BC_5kg"),
        ("Sales K 6 l", "SALESK_6l"), ("CO₂ 5 kg (cubre CO₂ 2 y 5 kg)", "CO2_5kg"), ("HCFC/HFC 5 kg", "HCFC-HFC_5kg"),
        ("Clase D 9 l", "CLASED_9l"), ("ABC 50 kg s/ruedas (cubre 25 y 50 kg)", "ABC_50kg"),
        ("ABC 100 kg s/ruedas (cubre 70 y 100 kg)", "ABC_100kg")]

# ------------------------------------------------------------------ catálogo de ítems (COMPRAS)
Z_CHM, Z_CANT, Z_CHR = "Chapa y fleje (manuales)", "Cantilever de caños y barras", "Calle de chapa (carros)"
Z_CASQ, Z_INR, Z_INM = "Rack de casquetes y cuplas (carros)", "Rack de insumos de montaje (carros)", \
    "Insumos de montaje (manuales)"
Z_POL, Z_GAS, Z_SOL = "Depósito de polvo químico", "Jaula de gases", "Insumos de soldadura y superficie"
Z_ID, Z_EMB, Z_REC = "Identificación", "Embalaje", "Insumos de recargas"
Z_REV, Z_SERV = "Equipos revendidos (almacén de PT)", "Servicio (no se almacena)"
# capacidad de las zonas que el proceso ya dimensionó (posiciones): proceso de carros, puesto 1, tabla de espacios
CAPACIDAD = {Z_CHR: (3, "3 posiciones de 3,0 × 1,5 m con hasta 2 paquetes cada una (proceso de carros, puesto 1)"),
             Z_CASQ: (12, "3 módulos de 2,3 m × 2 niveles = 12 posiciones (proceso de carros, puesto 1)"),
             Z_INR: (8, "2 módulos × 2 niveles = 8 posiciones (proceso de carros, puesto 1)")}

CRIT, NAC, IMP, ORG = 5, 10, 20, 10       # días hábiles entre pedidos (T): MP crítica, nacional, importado, organismo
# fuentes de lead time
Q_PRAD = ("Cotización", "Pradecon, mail del 28/09/2026: «son 7/10 días el plazo de entrega» si hay bobina en piso; "
                        "se toma el máximo")
Q_PRAD_P = ("Cotización", "Pacheco (PR-42021) no informa plazo; se toma el de Pradecon, que cotizó lo mismo: «7/10 días»")
Q_AL = ("Cotización", "Air Liquide (cotizaciones de MP por WhatsApp): «El plazo de entrega es a día + 1»")
Q_ELI = ("Cotización", "Eli-Met (cotizaciones de MP por WhatsApp): «plazo de entrega 35 a 40 días» corridos = 28 días "
                       "hábiles")
Q_ELI_A = ("Cotización", "Eli-Met no cotizó el asiento; se toma el plazo de su cupla: «35 a 40 días» corridos = 28 "
                         "hábiles")
Q_MID = ("Cotización", "Comercial MID (27626): «entrega inmediata salvo ventas»; Metalprisa no informa plazo; se toman "
                       "5 días hábiles de la planilla de MP para armar el pedido y el flete")
P_CASQ = ("Proceso", "Proceso de carros, puesto 1, tabla 3: «60 días háb. (importado)». Investigación: tránsito marítimo "
                     "Shanghái - Buenos Aires de 38 a 40 días puerto a puerto (iContainers), más fabricación y despacho")
P_POLVO = ("Proceso", "Proceso de carros, puesto 1, tabla 3: «7 días háb. (Polvex)»")
P_VALV = ("Proceso", "Proceso de carros, puesto 1: «válvula de carro y manómetro, 20 días hábiles» (planilla de MP)")
P_MANG = ("Proceso", "Proceso de carros, puesto 1: «manguera con lanza, 15» días hábiles (planilla de MP)")
P_RUEDA = ("Proceso", "Proceso de carros, puesto 1: «ruedas, 15» días hábiles (planilla de MP)")
P_ALAM = ("Proceso", "Proceso de carros, puestos 5 a 8: «el alambre en rollos (5 días hábiles)»")
PL = ("Planilla de MP", "Planilla «MP Abastecimiento» (opción D), estimado del equipo; ningún presupuesto trae plazo")
S_SID = ("Supuesto", "El proceso de carros (8.1) dice «las demoras de los dos proveedores están a confirmar»; se toma "
                     "el mismo plazo que el caño cotizado (entrega inmediata del distribuidor siderúrgico)")
S_ORG = ("Supuesto", "Se compra al organismo (DPS, AGC, IRAM); trámite estimado en 2 semanas")
S_REV = ("Supuesto", "Equipo terminado de un fabricante nacional; mismo plazo que los componentes que se les compran "
                     "(manguera, 15 días hábiles)")
S_SERV = ("Supuesto", "Servicio de pintura tercerizado por tandas semanales (sin plazo en la cotización)")


def I(cod, nom, um, tipo, clase, zona, prov, alt, estado, uc, cont, lt, fuente, T, ucpos, m2, nota=""):
    return dict(cod=cod, nom=nom, um=um, tipo=tipo, clase=clase, zona=zona, prov=prov, alt=alt, estado=estado, uc=uc,
                cont=cont, lt=lt, lt_or=fuente[0], lt_fu=fuente[1], T=T, ucpos=ucpos, m2=m2, nota=nota)


D, IN = "Directo", "Indirecto"
MPC, CMP, IDN, EMB, CON, REVT, SERV = ("Materia prima", "Componente comprado", "Identificación", "Embalaje",
                                       "Consumible de proceso", "Reventa", "Servicio")
# equipos revendidos por posición de pallet (cajas del fabricante, supuesto)
POR_POS_REV = {"AGUA_10l": 24, "AFFF_10l": 24, "AFFF_50l": 2, "BC_5kg": 40, "SALESK_6l": 30, "CO2_2kg": 48,
               "CO2_5kg": 24, "HCFC-HFC_5kg": 40, "CLASED_9l": 24}
ITEMS = [
    # ---- acero
    I("MP-01", "Caño c/costura LF SAE 1010 Ø76,2 × 1,25 × 6 m (cuerpo 1 kg)", "barra", D, MPC, Z_CANT,
      "Metalpri / Prilux", "Comercial MID", "Cotizado", "Atado de 16 barras", 16, 5, Q_MID, CRIT, 2, 1.0,
      "Proceso de manuales: atados de 16 tubos de 14 kg"),
    I("MP-02", "Hoja LAF 1,25 × 1220 × 2440 mm (cuerpo 2,5 kg, 27 por hoja)", "hoja", D, MPC, Z_CHM, "Pradecon",
      "Hierros Parrotta", "Cotizado", "Paquete de 50 hojas", 50, 10, Q_PRAD, CRIT, 2, 2.98,
      "Proceso de manuales: paquetes de 50 hojas"),
    I("MP-03", "Hoja LAF 1,6 × 1000 × 2000 mm (cuerpo 5 kg, 12 por hoja)", "hoja", D, MPC, Z_CHM, "Pradecon",
      "Hierros Parrotta", "Cotizado", "Paquete de 80 hojas", 80, 10, Q_PRAD, CRIT, 2, 2.0,
      "Proceso de manuales: paquete de 80 hojas, unos 2 t"),
    I("MP-04", "Hoja LAF 2,0 × 1500 × 3000 mm (cuerpo 10 kg, 15 por hoja)", "hoja", D, MPC, Z_CHM, "Pradecon",
      "Hierros Parrotta", "Cotizado", "Paquete de 20 hojas", 20, 10, Q_PRAD, CRIT, 2, 4.5,
      "Proceso de manuales: paquetes de 20 hojas"),
    I("MP-05", "Fleje LAF 0,9 × 114 mm (cúpula 1 kg, disco Ø95)", "kg", D, MPC, Z_CHM, "Pradecon", "Pacheco Chapas",
      "Cotizado", "Rollo de fleje ≈1.900 kg", 1900, 10, Q_PRAD, CRIT, 1, 1.0,
      "Pradecon: «el peso promedio por bobina de fleje es entre 1.8 y 2 tn»"),
    I("MP-13", "Fleje LAF 1,25 × 135 mm (fondo 1 kg, disco Ø112)", "kg", D, MPC, Z_CHM, "Pradecon", "Pacheco Chapas",
      "Cotizado (a recotizar)", "Rollo de fleje ≈1.900 kg", 1900, 10, Q_PRAD, CRIT, 1, 1.0,
      "Corregido: la planilla decía 0,9 × 106; el plano y el proceso piden 1,25 mm y el disco Ø112 no entra en 106"),
    I("MP-06", "Fleje LAF 1,25 × 200 mm (cúpula Ø179 y fondo Ø148, 2,5 kg)", "kg", D, MPC, Z_CHM, "Pacheco Chapas",
      "Pradecon", "Cotizado", "Rollo de 492 kg", 492, 10, Q_PRAD_P, CRIT, 1, 1.0,
      "Pacheco PR-42021: 2.951 kg en 6 rollos"),
    I("MP-07", "Fleje LAF 1,6 × 250 mm (cúpula Ø221, 5 kg)", "kg", D, MPC, Z_CHM, "Pacheco Chapas", "Pradecon",
      "Cotizado", "Rollo de 615 kg", 615, 10, Q_PRAD_P, CRIT, 1, 1.0, "Pacheco PR-42021: 2.459 kg en 4 rollos"),
    I("MP-08", "Fleje LAF 1,6 × 200 mm (fondo Ø177, 5 kg)", "kg", D, MPC, Z_CHM, "Pacheco Chapas", "Pradecon",
      "Cotizado", "Rollo de 492 kg", 492, 10, Q_PRAD_P, CRIT, 1, 1.0, "Pacheco PR-42021: 2.951 kg en 6 rollos"),
    I("MP-09", "Fleje LAF 1,6 × 300 mm (cúpula Ø258, 10 kg)", "kg", D, MPC, Z_CHM, "Pacheco Chapas", "Pradecon",
      "Cotizado (a recotizar en 1,6)", "Rollo ≈590 kg", 590, 10, Q_PRAD_P, CRIT, 1, 1.0,
      "Corregido: se cotizó en 2,0 mm; el plano y el proceso piden 1,6 mm (mismo largo de rollo: 738 × 1,6 / 2,0)"),
    I("MP-10", "Fleje LAF 2,0 × 249 mm (fondo Ø205, 10 kg)", "kg", D, MPC, Z_CHM, "Pacheco Chapas", "Pradecon",
      "Cotizado", "Rollo de 498 kg", 498, 10, Q_PRAD_P, CRIT, 1, 1.0, "Pacheco: 619 fondos por bobina"),
    I("MP-11", "Hoja LAC 3,2 × 1500 × 3000 mm (cuerpo 25 kg: 9 por hoja; 50 kg: 6)", "hoja", D, MPC, Z_CHR,
      "Pradecon", "Pacheco Chapas", "Cotizado", "Paquete de 20 hojas", 20, 10, Q_PRAD, CRIT, 2, 4.5,
      "Proceso de carros: paquetes de 20 hojas de 113 kg"),
    I("MP-12", "Hoja LAC 4,75 × 1500 × 3000 mm (cuerpos 70 y 100 kg)", "hoja", D, MPC, Z_CHR, "Pradecon",
      "Pacheco Chapas", "Cotizado", "Paquete de 15 hojas", 15, 10, Q_PRAD, CRIT, 2, 4.5,
      "Proceso de carros: paquetes de 15 hojas de 168 kg"),
    I("MP-15", "Casquete embutido 10\" × 3,2 mm (cúpula y fondo, carro 25 kg)", "u", D, CMP, Z_CASQ,
      "Importado (EKC / chinafiresafety)", "Gockel Ingeniería (a cotizar)", "A cotizar", "Pallet de 400 u", 400, 60,
      P_CASQ, IMP, 1, 0.73, "Proceso de carros: 400 casquetes por pallet (200 cúpulas + 200 fondos)"),
    I("MP-16", "Casquete embutido 12\" × 3,2 mm (cúpula y fondo, carro 50 kg)", "u", D, CMP, Z_CASQ,
      "Importado (EKC / chinafiresafety)", "Gockel Ingeniería (a cotizar)", "A cotizar", "Pallet de 300 u", 300, 60,
      P_CASQ, IMP, 1, 0.73, "Proceso de carros: 300 por pallet"),
    I("MP-17", "Casquete embutido 15\" × 4,75 mm (cúpula y fondo, carros 70 y 100 kg)", "u", D, CMP, Z_CASQ,
      "Importado (EKC / chinafiresafety)", "Gockel Ingeniería (a cotizar)", "A cotizar", "Pallet de 150 u", 150, 60,
      P_CASQ, IMP, 1, 0.73, "Proceso de carros: 150 por pallet"),
    I("MP-18", "Asiento de válvula roscado M22 × 1,5 (cúpula 1 kg)", "u", D, CMP, Z_INM, "Eli-Met", "-",
      "A cotizar", "Caja de 1.000 u", 1000, 28, Q_ELI_A, NAC, 12, 0.73, "Planilla de MP: cajas de 1.000 u"),
    I("MP-19", "Asiento de válvula roscado M30 × 1,5 (cúpula 2,5 a 10 kg)", "u", D, CMP, Z_INM, "Eli-Met", "-",
      "A cotizar", "Caja de 1.000 u", 1000, 28, Q_ELI_A, NAC, 8, 0.73, "Planilla de MP: cajas de 1.000 u"),
    I("MP-20", "Cupla soldable M30 × 1,5 (carros 25 y 50 kg)", "u", D, CMP, Z_CASQ, "Eli-Met", "-", "Cotizado",
      "Caja de 100 u", 100, 28, Q_ELI, NAC, 12, 0.73, "Proceso de carros: cajas de 100 u de 25 kg"),
    I("MP-21", "Cupla soldable 2½\" BSP (carros 70 y 100 kg)", "u", D, CMP, Z_CASQ, "Eli-Met", "-", "Cotizado",
      "Caja de 40 u", 40, 28, Q_ELI, NAC, 8, 0.73, "Proceso de carros: cajas de 40 u de 24 kg"),
    I("MP-66", "Caño estructural SAE 1010 1\" × 2,0 × 6 m (manija; caño del eje 25 kg)", "barra", D, MPC, Z_CANT,
      "Centrosider", "Metalpri / Prilux", "A cotizar", "Barra de 6 m", 1, 5, S_SID, CRIT, 40, 1.0,
      "Proceso de carros 8.1: se vende por barra entera de 6 m"),
    I("MP-67", "Caño estructural SAE 1010 1¼\" × 2,0 × 6 m (caño del eje 50 a 100 kg)", "barra", D, MPC, Z_CANT,
      "Centrosider", "Metalpri / Prilux", "A cotizar", "Barra de 6 m", 1, 5, S_SID, CRIT, 40, 1.0),
    I("MP-68", "Barra trefilada SAE 1045 3/4\" × 4 m (eje 25 kg)", "barra", D, MPC, Z_CANT, "Vladimirsky",
      "Hierros Parrotta", "A cotizar", "Barra de 4 m", 1, 5, S_SID, CRIT, 40, 1.0,
      "Proceso de carros 8.1: barras de 4 m hasta Ø20"),
    I("MP-69", "Barra trefilada SAE 1045 1\" × 6 m (eje 50 a 100 kg)", "barra", D, MPC, Z_CANT, "Vladimirsky",
      "Hierros Parrotta", "A cotizar", "Barra de 6 m", 1, 5, S_SID, CRIT, 40, 1.0,
      "Proceso de carros 8.1: barras de 6 m de 21 a 30 mm"),
    I("MP-70", "Arandela de tope del eje del carro", "u", D, CMP, Z_INR, "Hierros Parrotta", "-", "A cotizar",
      "Bolsa de 100 u", 100, 5, S_SID, NAC, 20, 0.73),
    I("MP-71", "Pasador partido del eje del carro", "u", D, CMP, Z_INR, "Hierros Parrotta", "-", "A cotizar",
      "Bolsa de 100 u", 100, 5, S_SID, NAC, 20, 0.73),
    # ---- carga
    I("MP-33", "Polvo ABC 60 (IRAM 3569), manuales y sus recargas", "kg", D, MPC, Z_POL, "DEMSA", "Polvex",
      "Cotizado", "Big bag de 1.000 kg", 1000, 7, P_POLVO, CRIT, 2, 1.0,
      "Proceso: big bags de 1.000 kg apilados de a 2 en el depósito de polvo"),
    I("MP-33B", "Polvo ABC 90 (IRAM 3569), rodantes y sus recargas", "kg", D, MPC, Z_POL, "DEMSA", "Polvex",
      "Cotizado", "Big bag de 1.000 kg", 1000, 7, P_POLVO, CRIT, 2, 1.0,
      "El BOM define ABC 90 en rodantes (decisión FLAMA); el proceso de carros lo llama MP-33"),
    I("MP-34", "Nitrógeno seco ≥ 99,8 % (gas impulsor)", "m³", D, MPC, Z_GAS, "Air Liquide", "Gogniat", "Cotizado",
      "Pack de 12 cilindros (≈110 m³)", 110, 1, Q_AL, CRIT, 1, 1.5, "Proceso de manuales, tabla 27: pack de 12 cilindros"),
    I("MP-39", "Argón (gas impulsor del agente limpio)", "m³", D, MPC, Z_GAS, "Air Liquide", "Gogniat", "A cotizar",
      "Cilindro de 9,5 m³", 9.5, 1, Q_AL, CRIT, 1, 0.1),
    # ---- soldadura y superficie
    I("MP-23", "Alambre MAG ER70S-6 Ø0,9 mm (manuales)", "kg", D, MPC, Z_SOL, "Conarco (ESAB)", "Distribuidor zona sur",
      "A cotizar", "Carrete de 15 kg", 15, 5, P_ALAM, NAC, 60, 0.73, "Proceso de manuales: alambre de 0,9 mm"),
    I("MP-24", "Alambre MAG ER70S-6 Ø1,0 mm (carros)", "kg", D, MPC, Z_INR, "Conarco (ESAB)", "Distribuidor zona sur",
      "A cotizar", "Carrete de 15 kg", 15, 5, P_ALAM, NAC, 60, 0.73,
      "El proceso de carros usa 1,0 mm en todos los puestos (la planilla decía 1,2)"),
    I("MP-25", "Gas de protección MAG Ar + 8 % CO₂ (Arcal 21)", "m³", IN, CON, Z_GAS, "Air Liquide", "Gogniat",
      "Cotizado", "Batería de 11 cilindros (115,5 m³)", 115.5, 1, Q_AL, CRIT, 1, 1.5,
      "Air Liquide: baterías de 11 cilindros de 10,5 m³, recambio semanal"),
    I("MP-26", "Puntas de contacto y toberas MAG", "u", IN, CON, Z_SOL, "ESAB / Binzel (distribuidor)", "-",
      "A cotizar", "Caja de 25 u", 25, 5, PL, NAC, 40, 0.73),
    I("MP-27", "Disco de corte 115 × 1,0 mm", "u", IN, CON, Z_SOL, "Norton / Pferd (distribuidor)", "-", "A cotizar",
      "Caja de 25 u", 25, 5, PL, NAC, 40, 0.73),
    I("MP-93", "Disco flap 115 mm grano 60", "u", IN, CON, Z_SOL, "Norton / Pferd (distribuidor)", "-", "A cotizar",
      "Caja de 10 u", 10, 5, PL, NAC, 40, 0.73),
    I("MP-92", "Disco de sensitiva 355 mm", "u", IN, CON, Z_SOL, "Norton / Pferd (distribuidor)", "-", "A cotizar",
      "Caja de 10 u", 10, 5, PL, NAC, 20, 0.73),
    I("MP-94", "Mecha de acero rápido 4,5 mm", "u", IN, CON, Z_SOL, "Ferretería industrial", "-", "A cotizar",
      "Caja de 10 u", 10, 5, PL, NAC, 40, 0.73),
    I("MP-95", "Spray antiproyecciones MIG 400 ml (Würth)", "u", IN, CON, Z_SOL, "Würth Argentina", "-", "A cotizar",
      "Aerosol de 400 ml", 1, 5, PL, NAC, 50, 0.73),
    I("MP-28", "Granalla de acero S330 / S390 (reposición)", "kg", IN, CON, Z_SOL, "CyM Materiales", "Roca Ingeniería",
      "Cotizado", "Pallet de 40 bolsas de 25 kg", 1000, 7, PL, NAC, 1, 1.2, "Precio cotizado ($2.000/kg), sin plazo"),
    I("MP-31", "Pintura en polvo poliéster rojo 03-1-050 (IRAM-DEF D 10-54)", "kg", D, MPC, Z_POL,
      "Sinteplast Industria", "Tersuave", "A cotizar", "Caja de 20 kg", 20, 10, PL, NAC, 30, 0.73,
      "Proceso de manuales: sector seco con el polvo ABC"),
    I("MP-32", "Tapón-gancho de silicona M22 / M30 (enmascarado)", "u", IN, CON, Z_SOL, "Distribuidor de enmascarado",
      "-", "A cotizar", "Caja de 500 u", 500, 10, PL, NAC, 10, 0.73),
    # ---- válvula, descarga y soporte
    I("MP-42", "Válvula HZ M-22 con tubo de pesca (1 kg)", "u", D, CMP, Z_INM, "Polvex (HZ)", "Mozart", "Cotizado",
      "Caja de 100 u", 100, 20, P_VALV, NAC, 30, 0.73, "Lista de precios: $4.200 c/u"),
    I("MP-43", "Válvula HZ M-30 con resorte y tubo 7/8 (2,5 a 10 kg)", "u", D, CMP, Z_INM, "Polvex (HZ)", "Mozart",
      "Cotizado", "Caja de 50 u", 50, 20, P_VALV, NAC, 30, 0.73, "Lista de precios: $6.800 c/u"),
    I("MP-44/25", "Válvula HZ de carro 25 kg (traba, manija y resorte)", "u", D, CMP, Z_INR, "Polvex (HZ)", "Mozart",
      "Cotizado", "Caja de 10 u", 10, 20, P_VALV, NAC, 20, 0.73, "Lista de precios: $7.500 c/u"),
    I("MP-44/50", "Válvula HZ de carro 50-70-100 kg", "u", D, CMP, Z_INR, "Polvex (HZ)", "Mozart", "Cotizado",
      "Caja de 10 u", 10, 20, P_VALV, NAC, 20, 0.73, "Lista de precios: $7.500 c/u"),
    I("MP-45", "Manómetro IRAM 3533, 1,4 MPa", "u", D, CMP, Z_INM, "Yukon", "Matafuegos Iglesias", "A validar",
      "Caja de 100 u", 100, 20, P_VALV, NAC, 20, 0.73),
] + [I(f"MP-48/{p}", f"{'Tobera' if p == 'ABC1' else 'Manguera con racor y tobera'} {n} (armada)", "u", D, CMP, Z_INM,
       "Yukon", "Matafuegos Iglesias", "A cotizar", "Caja de 50 u", 50, 15, P_MANG, NAC, 20, 0.73)
     for _, p, n in MAN] + [
    I(f"MP-49/{p}", f"Manguera armada con válvula esférica y tobera campana, carro {n[4:]}", "u", D, CMP, Z_INR,
      "Yukon", "Matafuegos Iglesias", "A cotizar", "Caja de 10 u", 10, 15, P_MANG, NAC, 20, 0.73) for _, p, n in ROD] + [
    I("MP-50/M22", "Junta tórica NBR 70 del cuello M22", "u", D, CMP, Z_INM, "Argensold", "Matafuegos Iglesias",
      "A cotizar", "Bolsa de 1.000 u", 1000, 10, PL, NAC, 50, 0.73),
    I("MP-50/M30", "Junta tórica NBR 70 del cuello M30", "u", D, CMP, Z_INM, "Argensold", "Matafuegos Iglesias",
      "A cotizar", "Bolsa de 1.000 u", 1000, 10, PL, NAC, 50, 0.73),
    I("MP-50/2½", "Junta tórica NBR 70 del cuello 2½\" (carros 70 y 100 kg)", "u", D, CMP, Z_INR, "Argensold",
      "Matafuegos Iglesias", "A cotizar", "Bolsa de 100 u", 100, 10, PL, NAC, 50, 0.73),
    I("MP-50/OT", "Junta tórica del cuello de los equipos de otros fabricantes (recargas)", "u", D, CMP, Z_REC,
      "Matafuegos Iglesias", "Yukon", "A cotizar", "Bolsa de 100 u", 100, 10, PL, NAC, 50, 0.73,
      "Medida según el fabricante del equipo"),
] + [I(f"MP-52/{p}", f"Soporte de pared {n}", "u", D, CMP, Z_INM, "Maxiseguridad", "CM Representaciones",
       "A cotizar", "Caja de 50 u", 50, 15, PL, NAC, 10, 0.73) for _, p, n in MAN[1:]] + [
    I("MP-87", "Soporte vehicular con cierre rápido (1 kg)", "u", D, CMP, Z_INM, "Maxiseguridad", "-", "A cotizar",
      "Caja de 50 u", 50, 15, PL, NAC, 10, 0.73),
    I("MP-86", "Tornillo M8 y tarugo Ø10 de fijación", "u", D, CMP, Z_INM, "Würth Argentina", "-", "A cotizar",
      "Caja de 500 u", 500, 5, PL, NAC, 20, 0.73),
    I("MP-54/300", "Rueda de chapa y goma Ø300 × 50, buje 3/4\" (carro 25 kg)", "u", D, CMP, Z_INR, "Ruedar", "-",
      "A validar", "Atado de 10 u", 10, 15, P_RUEDA, NAC, 4, 0.73),
    I("MP-54/350", "Rueda de chapa y goma Ø350 × 60, buje 1\" (carro 50 kg)", "u", D, CMP, Z_INR, "Ruedar",
      "Escanort", "A cotizar", "Atado de 10 u", 10, 15, P_RUEDA, NAC, 3, 0.73),
    I("MP-54/400", "Rueda de chapa y goma Ø400 × 60, buje 1\" (carros 70 y 100 kg)", "u", D, CMP, Z_INR, "Escanort",
      "Ruedar", "A cotizar", "Atado de 10 u", 10, 15, P_RUEDA, NAC, 3, 0.73),
    # ---- identificación
] + [I(f"MP-56/{p}", f"Etiqueta / placa de características {n}", "u", D, IDN, Z_ID, "Astuprint", "Multilabel",
       "A cotizar", "Rollo de 1.000 u", 1000, 10, PL, NAC, 30, 0.73) for _, p, n in FAB] + [
    I("MP-78", "Oblea de fabricación PBA (Res. 522/07)", "u", D, IDN, Z_ID, "Ministerio de Ambiente PBA (DPS)", "-",
      "Arancel oficial", "Paquete de 1.000 u", 1000, 10, S_ORG, ORG, 50, 0.73, "Sólo destino PBA"),
    I("MP-79", "Estampilla IRAM de conformidad", "u", D, IDN, Z_ID, "IRAM", "-", "Arancel de licencia",
      "Paquete de 1.000 u", 1000, 10, S_ORG, ORG, 50, 0.73),
    I("MP-77", "Tarjeta de identificación AGC (CABA)", "u", D, IDN, Z_ID, "AGC (CABA)", "-", "Arancel oficial",
      "Paquete de 500 u", 500, 10, S_ORG, ORG, 50, 0.73, "Sólo destino CABA"),
    I("MP-76", "Tarjeta de identificación DPS (PBA), recargas", "u", D, IDN, Z_ID, "Ministerio de Ambiente PBA (DPS)",
      "-", "Arancel oficial", "Paquete de 500 u", 500, 10, S_ORG, ORG, 50, 0.73, "Sólo destino PBA"),
    I("MP-75", "Estampilla y oblea de recarga (PBA)", "u", D, IDN, Z_ID, "Ministerio de Ambiente PBA (DPS)", "-",
      "Arancel oficial", "Paquete de 1.000 u", 1000, 10, S_ORG, ORG, 50, 0.73, "Sólo destino PBA"),
    I("MP-80", "Etiqueta de n° de serie GS1 con QR", "u", D, IDN, Z_ID, "Astuprint", "GS1 Argentina (códigos)",
      "A cotizar", "Rollo de 1.000 u", 1000, 10, PL, NAC, 50, 0.73),
    I("MP-81", "Faja de garantía válvula-cuello", "u", D, IDN, Z_ID, "Astuprint", "Multilabel", "A cotizar",
      "Rollo de 1.000 u", 1000, 10, PL, NAC, 50, 0.73),
    I("MP-51", "Precinto de fábrica numerado «FLAMA»", "u", D, IDN, Z_ID, "SonFuertes", "Precinter", "A cotizar",
      "Bolsa de 1.000 u", 1000, 10, PL, NAC, 50, 0.73),
    I("MP-88", "Etiqueta de identificación del cilindro suelto", "u", D, IDN, Z_ID, "Astuprint", "Multilabel",
      "A cotizar", "Rollo de 1.000 u", 1000, 10, PL, NAC, 50, 0.73),
    I("MP-73", "Etiqueta de control periódico (celeste 35 × 50)", "u", D, IDN, Z_REC, "Astuprint", "Multilabel",
      "A cotizar", "Rollo de 1.000 u", 1000, 10, PL, NAC, 50, 0.73),
    I("MP-72", "Etiqueta de servicio del recargador", "u", D, IDN, Z_REC, "Astuprint", "Multilabel", "A cotizar",
      "Rollo de 1.000 u", 1000, 10, PL, NAC, 50, 0.73),
    I("MP-57", "Marbete indicador de mantenimiento (color del año)", "u", D, IDN, Z_REC, "Astuprint", "Multilabel",
      "A cotizar", "Paquete de 1.000 u", 1000, 10, PL, NAC, 50, 0.73),
    I("MP-74", "Oblea de vencimiento de la prueba hidráulica", "u", D, IDN, Z_REC, "Astuprint", "Multilabel",
      "A cotizar", "Rollo de 1.000 u", 1000, 10, PL, NAC, 50, 0.73),
    I("MP-97", "Precinto con identificación del recargador", "u", D, IDN, Z_REC, "SonFuertes", "Precinter",
      "A cotizar", "Bolsa de 1.000 u", 1000, 10, PL, NAC, 50, 0.73),
    I("MP-55", "Conjunto de seguridad (disco) de CO₂, IRAM 2736", "u", D, CMP, Z_REC, "Georgia", "HZ", "A cotizar",
      "Bolsa de 100 u", 100, 15, PL, NAC, 50, 0.73),
    I("MP-82", "Faja amarilla de sustituto (≤ 40 mm)", "u", D, IDN, Z_REC, "Astuprint", "Multilabel", "A cotizar",
      "Rollo de 500 u", 500, 10, PL, NAC, 50, 0.73),
    I("MP-83", "Tarjeta DPS «SUSTITUTO HABILITADO»", "u", D, IDN, Z_REC, "Ministerio de Ambiente PBA (DPS)", "-",
      "Arancel oficial", "Paquete de 100 u", 100, 10, S_ORG, ORG, 50, 0.73),
    I("MP-84", "Tarjeta AGC con «Es sustituto»", "u", D, IDN, Z_REC, "AGC (CABA)", "-", "Arancel oficial",
      "Paquete de 100 u", 100, 10, S_ORG, ORG, 50, 0.73),
    I("MP-85", "Impresos (protocolo de ensayo, remito de préstamo)", "u", D, IDN, Z_ID, "Astuprint", "-", "A cotizar",
      "Paquete de 500 u", 500, 5, PL, NAC, 50, 0.73),
    # ---- agentes de recarga
    I("MP-35", "Polvo BC (IRAM 3566), recargas", "kg", D, MPC, Z_POL, "Polvex", "DEMSA", "Cotizado", "Bolsa de 25 kg",
      25, 7, PL, NAC, 40, 1.2),
    I("MP-36", "Polvo para metales combustibles clase D, recargas", "kg", D, MPC, Z_POL, "DEMSA", "-", "A validar",
      "Bolsa de 25 kg", 25, 15, PL, NAC, 40, 1.2),
    I("MP-37", "CO₂ líquido grado industrial, recargas", "kg", D, MPC, Z_GAS, "Air Liquide", "Gogniat", "A cotizar",
      "Cilindro con sifón de 25 kg", 25, 1, Q_AL, CRIT, 1, 0.1),
    I("MP-38", "Agente limpio HCFC-123 / HFC-236fa, recargas", "kg", D, MPC, Z_REC, "A definir (importado)", "-",
      "A definir", "Cilindro de 50 kg", 50, 30, PL, IMP, 1, 0.2),
    I("MP-40", "Concentrado AFFF 3 % (IRAM 3515), recargas", "L", D, MPC, Z_REC, "DEMSA", "Polvex", "Cotizado",
      "Bidón de 20 L", 20, 7, PL, NAC, 32, 0.73, "Lista de precios: bidón de 20 L"),
    I("MP-41", "Solución de acetato de potasio (clase K), recargas", "L", D, MPC, Z_REC, "Polvex (Gastro K)", "DEMSA",
      "Cotizado", "Bidón de 20 L", 20, 7, PL, NAC, 32, 0.73, "Lista de precios: bidones de 10, 20 y 30 L"),
    I("MP-65", "Esmalte rojo de retoque, recargas", "L", D, MPC, Z_REC, "Sinteplast", "Tersuave", "A cotizar",
      "Lata de 4 L", 4, 5, PL, NAC, 40, 0.73),
    # ---- embalaje
] + [I(f"MP-59/{p}", f"Caja de cartón corrugado {'doble' if p == 'ABC10' else 'simple'} {n}", "u", D, EMB, Z_EMB,
       "Maxipack", "Cartocan", "A cotizar", "Pallet de 600 cajas plegadas", 600, 10, PL, NAC, 1, 1.2)
     for _, p, n in MAN] + [
    I("MP-89", "Etiqueta de caja (código, serie y lote)", "u", D, EMB, Z_EMB, "Astuprint", "Multilabel", "A cotizar",
      "Rollo de 1.000 u", 1000, 10, PL, NAC, 50, 0.73),
    I("MP-60", "Pallet de madera 1200 × 1000 (IRAM 10016)", "u", D, EMB, Z_EMB, "IndusPallets", "-", "A cotizar",
      "Pila de 15 u", 15, 5, PL, NAC, 1, 1.2),
    I("MP-63", "Film stretch 500 mm pre-estirable", "kg", D, EMB, Z_EMB, "MV Embalajes", "Embalpack", "A cotizar",
      "Bobina de 16 kg", 16, 5, PL, NAC, 30, 0.73),
    I("MP-90", "Etiqueta de pallet", "u", D, EMB, Z_EMB, "Astuprint", "Multilabel", "A cotizar", "Rollo de 500 u",
      500, 10, PL, NAC, 50, 0.73),
    I("MP-64", "Esquinero de cartón 50 × 50 × 1200", "u", D, EMB, Z_EMB, "Maxipack", "Cartocan", "A cotizar",
      "Paquete de 100 u", 100, 10, PL, NAC, 5, 0.73),
    I("MP-91", "Funda de polietileno para rodante", "u", D, EMB, Z_EMB, "MV Embalajes", "Embalpack", "A cotizar",
      "Rollo de 100 u", 100, 5, PL, NAC, 10, 0.73),
    I("MP-62/M22", "Tapón protector de rosca PE M22 (cilindro suelto)", "u", D, EMB, Z_EMB, "A definir (inyectora)",
      "-", "Sin proveedor", "Caja de 5.000 u", 5000, 10, PL, NAC, 4, 0.73),
    I("MP-62/M30", "Tapón protector de rosca PE M30 (cilindro suelto)", "u", D, EMB, Z_EMB, "A definir (inyectora)",
      "-", "Sin proveedor", "Caja de 5.000 u", 5000, 10, PL, NAC, 4, 0.73),
    I("MP-62/2½", "Tapón protector de rosca PE 2½\" (cilindro suelto)", "u", D, EMB, Z_EMB, "A definir (inyectora)",
      "-", "Sin proveedor", "Caja de 500 u", 500, 10, PL, NAC, 4, 0.73),
] + [I(f"MP-96/{p}", f"Servicio de pintura en polvo, carro {n[4:]} (tercerizado)", "u", D, SERV, Z_SERV,
       "Pintor de carros (cotización por mensaje)", "Prymax", "Cotizado", "Unidad", 1, 5, S_SERV, CRIT, 0, 0,
       "Cotización: USD 13,5 / 20,3 / 27,5 / 32 por carro") for _, p, n in ROD] + [
    I(f"RV-{c}", f"Matafuego {n} terminado (reventa)", "u", D, REVT, Z_REV,
      {"CO2_2kg": "Mozart", "CO2_5kg": "Mozart"}.get(c, "Georgia"),
      {"CO2_2kg": "Georgia", "CO2_5kg": "Georgia", "HCFC-HFC_5kg": "Melisam", "BC_5kg": "Melisam",
       "CLASED_9l": "Melisam"}.get(c, "Drago"), "A cotizar", "Unidad", 1, 15, S_REV, NAC, POR_POS_REV[c], 0.73,
      "Equipos por posición de pallet: supuesto con la caja del fabricante")
    for c, n in REV]
ITEM = {it["cod"]: it for it in ITEMS}

# ------------------------------------------------------------------ fabricación: pieza → materia prima (FAB_COMPRA)
CUERPO = {"ABC1": ("MP-01", "tramos de 255 mm por caño de 6 m", 23, "Proceso de manuales, corte de tubo: «Cortar 23 "
                   "tramos» por caño"),
          "ABC2.5": ("MP-02", "cuerpos por hoja 1220 × 2440", 27, "Proceso de manuales, guillotina: 27 por hoja (94 %)"),
          "ABC5": ("MP-03", "cuerpos por hoja 1000 × 2000", 12, "Proceso de manuales, guillotina: 12 por hoja (94 %)"),
          "ABC10": ("MP-04", "cuerpos por hoja 1500 × 3000", 15, "Proceso de manuales, guillotina: 15 por hoja (93 %)"),
          "ABC25": ("MP-11", "cuerpos por hoja 1500 × 3000", 9, "Proceso de carros, puesto 2: 9 por hoja (84,1 %)"),
          "ABC50": ("MP-11", "cuerpos por hoja 1500 × 3000", 6, "Proceso de carros, puesto 2: 6 por hoja (84,8 %)"),
          "ABC70": ("MP-12", "cuerpos por hoja sola (la mixta se calcula en la hoja RODANTES)", 4,
                    "Proceso de carros, puesto 2: 4 por hoja sola (73,3 %); mixta 3 + 1 (79,2 %)"),
          "ABC100": ("MP-12", "cuerpos por hoja sola (la mixta se calcula en la hoja RODANTES)", 3,
                     "Proceso de carros, puesto 2: 3 por hoja sola (72,7 %); mixta 3 + 1 (79,2 %)")}
# disco de cúpula / fondo de manuales: (ítem, ancho del fleje, Ø del disco, espesor del plano)
DISCO = {("ABC1", "Cúpula"): ("MP-05", 114, 95, 0.9), ("ABC1", "Fondo"): ("MP-13", 135, 112, 1.25),
         ("ABC2.5", "Cúpula"): ("MP-06", 200, 179, 1.25), ("ABC2.5", "Fondo"): ("MP-06", 200, 148, 1.25),
         ("ABC5", "Cúpula"): ("MP-07", 250, 221, 1.6), ("ABC5", "Fondo"): ("MP-08", 200, 177, 1.6),
         ("ABC10", "Cúpula"): ("MP-09", 300, 258, 1.6), ("ABC10", "Fondo"): ("MP-10", 249, 205, 2.0)}
CASQ = {"ABC25": "MP-15", "ABC50": "MP-16", "ABC70": "MP-17", "ABC100": "MP-17"}
CUELLO = {"ABC1": "MP-18", "ABC2.5": "MP-19", "ABC5": "MP-19", "ABC10": "MP-19", "ABC25": "MP-20", "ABC50": "MP-20",
          "ABC70": "MP-21", "ABC100": "MP-21"}
MANIJA = {"ABC25": 1440, "ABC50": 1520, "ABC70": 1590, "ABC100": 1590}               # caño 1" (8.1)
CANO_EJE = {"ABC25": ("MP-66", 354), "ABC50": ("MP-67", 354), "ABC70": ("MP-67", 434), "ABC100": ("MP-67", 434)}
EJE = {"ABC25": ("MP-68", 490, 4000), "ABC50": ("MP-69", 510, 6000), "ABC70": ("MP-69", 590, 6000),
       "ABC100": ("MP-69", 590, 6000)}
RUEDA = {"ABC25": "MP-54/300", "ABC50": "MP-54/350", "ABC70": "MP-54/400", "ABC100": "MP-54/400"}
VALV = {"ABC1": "MP-42", "ABC2.5": "MP-43", "ABC5": "MP-43", "ABC10": "MP-43", "ABC25": "MP-44/25",
        "ABC50": "MP-44/50", "ABC70": "MP-44/50", "ABC100": "MP-44/50"}
JUNTA = {"ABC1": "MP-50/M22", "ABC70": "MP-50/2½", "ABC100": "MP-50/2½"}
TAPON = {"ABC1": "MP-62/M22", "ABC70": "MP-62/2½", "ABC100": "MP-62/2½"}

# ------------------------------------------------------------------ insumos de proceso y embalaje (PROCESO)
GAS_MAN = {"ABC1": 0.01671, "ABC2.5": 0.03388, "ABC5": 0.04096, "ABC10": 0.051}      # m³ por recipiente
PICO_DOC_MAN = {"ABC1": 1216, "ABC2.5": 99, "ABC5": 446, "ABC10": 27}   # recipientes por día en el pico (proceso)
ALAMBRE_MAN = {"ABC1": 0.01499, "ABC2.5": 0.0304, "ABC5": 0.03675, "ABC10": 0.04575}   # kg por recipiente
POR_PALLET_MAN = {"ABC1": 400, "ABC2.5": 167, "ABC5": 90, "ABC10": 40}
POR_PALLET_ROD = {"ABC25": 24, "ABC50": 9, "ABC70": 6, "ABC100": 6}
# proceso de carros: (puesto, gas en L por unidad, alambre en g por unidad) por modelo 25 / 50 / 70 / 100
CARRO = [("Puesto 4, punteo del cuerpo", (3.4, 4.1, 9.5, 10.2), (6.0, 7.2, 16.8, 18.0)),
         ("Puesto 5, soldadura longitudinal", (18, 22, 32, 42), (48, 63, 120, 158)),
         ("Puesto 6, soldadura de cupla", (10, 10, 17, 17), (10.5, 10.5, 29, 29)),
         ("Puesto 7, soldadura circunferencial", (66, 75, 122, 122), (190, 218, 463, 463)),
         ("Puesto 8, soldadura de accesorios", (96, 98, 109, 109), (141, 146, 199, 199))]

# perfiles de estacionalidad (Dimensionamiento Técnico V2: Parametros y Parametros Recargas)
PERFILES = [
    ("Ventas automovilístico (1 kg)", [.12, .09, .08, .075, .07, .07, .075, .075, .075, .075, .075, .12]),
    ("Ventas manual comercial (2,5 / 5 / 10 kg)", [.10, .08, .085, .085, .08, .075, .08, .08, .08, .075, .07, .11]),
    ("Ventas industrial s/ruedas (25 - 100 kg)", [.085, .075, .09, .09, .09, .08, .09, .09, .085, .075, .07, .08]),
    ("Recargas automovilístico (1 kg)", [.10] + [.078] * 10 + [.12]),
    ("Recargas manual comercial", [.09, .08, .085, .08, .075, .07, .08, .085, .085, .08, .08, .11]),
    ("Recargas industrial s/ruedas", [.10, .08, .085, .085, .08, .075, .09, .08, .08, .08, .075, .09])]
MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
F_PERFILES = ("Dimensionamiento_TecnicoV2.xlsx, hoja Parametros (perfiles de estacionalidad ajustados en sept. 2026) "
              "y hoja Parametros Recargas (perfiles de estacionalidad de recargas)")


def perfil(c, recarga=False):
    if c == "ABC_1kg":
        return PERFILES[3][0] if recarga else PERFILES[0][0]
    if c in ("ABC_25kg", "ABC_50kg", "ABC_70kg", "ABC_100kg", "AFFF_50l"):
        return PERFILES[5][0] if recarga else PERFILES[2][0]
    return PERFILES[4][0] if recarga else PERFILES[1][0]


# ------------------------------------------------------------------ estilo
def _f(bold=False, color=NEGRO, size=10, italic=False):
    return Font(name=AR, size=size, bold=bold, color=color, italic=italic)


def _titulo(ws, texto, sub=None):
    ws["A1"] = texto
    ws["A1"].font = _f(True, size=12)
    if sub:
        ws["A2"] = sub
        ws["A2"].font = _f(italic=True, size=9)


def _cab(ws, r, textos, anchos=None, c0=1):
    for j, t in enumerate(textos, c0):
        c = ws.cell(r, j, t)
        c.font = _f(True, BLANCO)
        c.fill = PatternFill("solid", fgColor=NEGRO)
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.row_dimensions[r].height = 32
    if anchos:
        for j, w in enumerate(anchos, c0):
            ws.column_dimensions[L(j)].width = w


def _fila(ws, r, n, niv=None, c0=1):
    for j in range(c0, c0 + n):
        c = ws.cell(r, j)
        c.border = Border(bottom=FINO)
        if niv == 0:
            c.font = _f(True)
            c.fill = PatternFill("solid", fgColor=GRIS_C)
        elif niv == "sec":
            c.font = _f(True, BLANCO)
            c.fill = PatternFill("solid", fgColor=GRIS_O)
        elif not (c.font and c.font.bold):
            c.font = _f()


def _imprimir(ws, titulos, ultima_col):
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth, ws.page_setup.fitToHeight = 1, 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.print_title_rows = titulos
    ws.sheet_properties.outlinePr.summaryBelow = False
    ws.sheet_properties.outlinePr.summaryRight = False


def q(hoja):
    return f"'{hoja}'"


# ------------------------------------------------------------------ lectura de las fuentes
def leer_bom(ruta):
    """Filas del FLAMA_BOM.xlsx recalculado, agrupadas por producto (nivel 0) y por hoja."""
    wb = load_workbook(ruta, data_only=True)
    prods, refs, modelos = {}, {}, {}
    for hoja in ("Fabricados", "Revendidos", "Cilindros", "Recargas"):
        ws = wb[hoja]
        cab = [c.value for c in ws[1]]
        prod = None
        for r, fila in enumerate(ws.iter_rows(min_row=2, values_only=True), 2):
            if not fila[1]:
                continue
            d = dict(zip(cab, fila))
            d["fila"], d["hoja"] = r, hoja
            if d["Nivel"] == 0:
                prod = d["Código"]
                prods[(hoja, prod)] = []
            prods[(hoja, prod)].append(d)
    for fila in wb["REFERENCIAS"].iter_rows(min_row=3, values_only=True):
        if fila[0] and isinstance(fila[2], (int, float)):
            refs[fila[0]] = fila[2]
    ws = wb["MODELOS"]
    cab = [c.value for c in ws[2]]
    for fila in ws.iter_rows(min_row=3, values_only=True):
        if fila[0]:
            modelos[fila[0]] = dict(zip(cab, fila))
    return prods, refs, modelos


def arbol(filas):
    """Agrega a cada fila su padre y si es grupo (la sigue una fila más profunda)."""
    pila = []
    for i, f in enumerate(filas):
        while pila and pila[-1]["Nivel"] >= f["Nivel"]:
            pila.pop()
        f["padre"] = pila[-1] if pila else None
        f["grupo"] = i + 1 < len(filas) and filas[i + 1]["Nivel"] > f["Nivel"]
        pila.append(f)
    return filas


def usados(src):
    """% de recargas de equipos usados (accionados) = Mat Usados / RECARGAS TOT de las hojas de proyección que lo
    traen (columnas O y P), por año."""
    out = []
    for y in AÑOS:
        u = t = 0.0
        for hoja in ("SALUD", "EDUCACION", "INDUSTRIASALM", "HOTELES"):
            for row in src["PROYECCION " + hoja].iter_rows(min_row=2, values_only=True):
                if str(row[0]) == str(y):
                    u += row[14] if isinstance(row[14], (int, float)) else 0
                    t += row[15] if isinstance(row[15], (int, float)) else 0
        out.append(round(u / t, 6) if t else 0)
    return out


def ubicar(ws):
    """Filas de las Proyecciones por sección y etiqueta."""
    sec, pos = None, {}
    for r, fila in enumerate(ws.iter_rows(min_row=1, max_row=ws.max_row, max_col=1, values_only=True), 1):
        v = fila[0]
        if not isinstance(v, str):
            continue
        t = v.strip()
        if t.startswith(("PRODUCCION", "RECARGAS", "MATAFUEGOS", "DISTRIBUCI", "STOCK DE", "ALTA ANUAL", "A. ",
                         "B. ", "C. ")) and t != "RECARGAS TOT":
            sec = t
            continue
        pos[(sec, t)] = r
    return pos


# ------------------------------------------------------------------ libro
class Libro:
    def __init__(self, proyecciones, bom):
        self.src = load_workbook(proyecciones, data_only=True)
        self.prods, self.refs, self.modelos = leer_bom(bom)
        for k in self.prods:
            arbol(self.prods[k])
        self.wb = Workbook()
        self.wb.remove(self.wb.active)
        self.pid = {}          # ID de PARAMETROS → fila
        self.dem = {}          # clave de demanda → fila de DEMANDA
        self.coef = {}         # (hoja, clave) → lista de filas de coeficientes
        self.tot = {}          # (hoja de insumos, código) → fila de total

    # -------- parámetros
    def P(self, pid):
        return f'INDEX(P_VAL,MATCH("{pid}",P_ID,0))'

    def PY(self, pid, j):
        return f'INDEX(PY_VAL,MATCH("{pid}",PY_ID,0),{j + 1})'

    def parametros(self):
        ws = self.wb.create_sheet("PARAMETROS")
        _titulo(ws, "PARÁMETROS DEL MRP: cada dato que entra en una cuenta, con ID, valor y fuente",
                "Las fórmulas de las demás hojas los buscan por ID (INDEX / MATCH). Las normas se citan por cláusula.")
        _cab(ws, 3, ["ID", "Dato", "Valor", "Unidad", "Fuente", "Nota"], [14, 58, 11, 11, 70, 50])
        rn2, rar = self.refs.get("GAS_N2"), self.refs.get("GAS_AR")
        filas = [
            ("AÑO_DIS", "Año de diseño de la política de stock (año 10)", 2035, "año", "Decisión FLAMA", ""),
            ("DH_MES", "Días hábiles por mes", 20, "día", "Dimensionamiento Técnico V2, hoja Parametros: «Días "
             "hábiles/mes: 20»", "Coincide con el proceso de manuales: 72.089 terminados / 300 por día = 240 días"),
            ("DH_AÑO", "Días hábiles por año", f'=12*{self.P("DH_MES")}', "día", "12 × DH_MES", ""),
            ("MERMA_POLVO", "Merma de polvo en la carga de fábrica", 0.01, "fracción",
             "Proceso de carros, puesto 1, tabla 3: «carga de cada carro + 1 % de merma»", "Se aplica también a "
             "manuales (misma máquina de carga por vacío)"),
            ("RHO_N2", "Densidad normal del nitrógeno", round(rn2 * 1000, 4) if rn2 else 1.2492, "kg/m³",
             "FLAMA_BOM.xlsx, REFERENCIAS, GAS_N2 (masa molar / volumen molar normal)",
             "Pasa el gas del BOM (kg) a m³ normales, que es como lo vende Air Liquide"),
            ("RHO_AR", "Densidad normal del argón", round(rar * 1000, 4) if rar else 1.7846, "kg/m³",
             "FLAMA_BOM.xlsx, REFERENCIAS, GAS_AR", ""),
            ("N2_PERD", "Pérdidas de N₂ en la presurización (pinza, mangueras y purgas)", 0.30, "fracción",
             "Planilla de MP (opción D), Coef Fabricación: factor 1,3 (estimado)", "El proceso de manuales las "
             "menciona («más las pérdidas de la pinza y las purgas») sin cuantificarlas"),
            ("CTRL_AÑO", "Controles periódicos por equipo atendido y por año", 4, "control",
             "IRAM 3517-2:2020, 8.2: control periódico trimestral", "Supone que FLAMA, como prestador, hace los "
             "controles de los equipos que mantiene; si los hace el usuario, poner 0"),
            ("P_RETOQUE", "Equipos de recarga que llegan con la pintura deteriorada", 0.15, "fracción",
             "Dimensionamiento Técnico V2, Parametros Recargas (IRAM 3517-2:2020 9.10)", ""),
            ("RETOQUE_L", "Esmalte por retoque", 0.05, "L/equipo", "Planilla de MP, Coef Recargas (estimado)", ""),
            ("REPO_VALV", "Válvulas que se reemplazan en el mantenimiento (ABC)", 0.03, "fracción",
             "Planilla de MP, Coef Recargas (estimado)", "La IRAM 3517-2 manda reemplazar lo que no pasa la "
             "inspección, sin fijar una tasa"),
            ("REPO_MANO", "Manómetros que se reemplazan en el mantenimiento (ABC)", 0.08, "fracción",
             "Planilla de MP, Coef Recargas (estimado)", "Ídem"),
            ("REPO_MANG", "Mangueras que se reemplazan en el mantenimiento (ABC)", 0.05, "fracción",
             "Planilla de MP, Coef Recargas (estimado)", "Ídem"),
            ("PINT_RHO", "Densidad de la pintura en polvo poliéster", 1.63, "g/cm³",
             "Ficha técnica WEG Politherm 20 R (densidad 1,63; rendimiento 8,76 m²/kg a 70 µm)", "Rango usual "
             "1,5 a 1,8 g/cm³"),
            ("PINT_ESP", "Espesor seco de película", 70, "µm", "Ficha técnica WEG Politherm: «espesura media 70 µm»",
             "El proceso controla el espesor seco por muestreo; el plano no fija un valor"),
            ("PINT_APROV", "Aprovechamiento del polvo con recuperación", 0.95, "fracción",
             "Powder Coating Institute (citado por Products Finishing): 95 a 98 % con recuperación", "El proceso de "
             "manuales usa cabina «con recuperación de polvo»; se toma el mínimo del rango"),
            ("GRANALLA", "Granalla de reposición por cilindro", 0.08, "kg", "Proceso de manuales, granallado: «unos "
             "0,08 kg por cilindro según la BOM: unos 133 kg por día en el pico»", ""),
            ("TAPON_CICLOS", "Ciclos de vida de un tapón de silicona", 50, "ciclo",
             "Planilla de MP, Coef Fabricación (estimado)", "Los tapones circulan (1.665 en el pico); se repone "
             "uno cada 50 usos"),
            ("DISCO_MAN", "Recipientes por disco de amolado (manuales)", 150, "u",
             "Planilla de MP, Coef Fabricación (estimado)", "Corrección de defectos con disco flap"),
            ("GAS_MAN_AJ", "Ajuste del gas MAG de manuales al consumo del proceso",
             "=48/(" + "+".join(f"{PICO_DOC_MAN[k]}*{GAS_MAN[k]}" for k in GAS_MAN) + ")", "factor",
             "Proceso de manuales, recepción: «unos 48 m³ por día en el pico»; con la producción del pico de ese "
             "proceso (1.216 tramos de 1 kg; 99, 446 y 27 desarrollos de 2,5, 5 y 10 kg) los coeficientes de la "
             "planilla dan 43,3 m³", "Es el gas de arranque y cierre de cada costura, que la geometría no cuenta (el "
             "proceso de carros lo suma: 0,1 a 0,2 min por costura)"),
            ("ALAMBRE_PUNTA", "Alambre por punta de contacto", 4, "kg", "Planilla de MP, Coef Fabricación "
             "(estimado)", ""),
            ("APROV_CANO", "Aprovechamiento de las barras de caño (carros)", 0.95, "fracción",
             "Proceso de carros, 8.1: «Se tomó un 95 % de aprovechamiento de las barras de caño»", ""),
            ("FILM_PALLET", "Film stretch por pallet", 0.35, "kg", "Planilla de MP, Coef Fabricación (estimado con "
             "el pre-estirado de la envolvedora EDOS PS5)", ""),
            ("ESQ_PALLET", "Esquineros por pallet de cilindros de carro", 4, "u", "Planilla de MP (estimado)", ""),
        ]
        r = 4
        for fila in filas:
            for j, v in enumerate(fila, 1):
                ws.cell(r, j, v)
            _fila(ws, r, 6)
            self.pid[fila[0]] = r
            r += 1
        fin = r - 1
        self.wb.defined_names["P_ID"] = DefinedName("P_ID", attr_text=f"PARAMETROS!$A$4:$A${fin}")
        self.wb.defined_names["P_VAL"] = DefinedName("P_VAL", attr_text=f"PARAMETROS!$C$4:$C${fin}")
        # parámetros por año
        r += 1
        ws.cell(r, 1, "PARÁMETROS POR AÑO").font = _f(True)
        r += 1
        _cab(ws, r, ["ID", "Dato"] + AÑOS + ["Fuente"])
        ws.column_dimensions[L(13)].width = 70
        r0 = r + 1
        ix = ubicar(self.src["Indexado Dim Técnico"])
        caba_rec = [ix[(s, z)] for (s, z) in ix if s and s.startswith("DISTRIBUCIÓN DE RECARGAS") and
                    z.startswith("CABA")]
        sub_rec = next(ix[(s, z)] for (s, z) in ix if s and s.startswith("DISTRIBUCIÓN DE RECARGAS") and
                       z.startswith("SUBTOTAL"))
        caba_nue = [ix[(s, z)] for (s, z) in ix if s and s.startswith("DISTRIBUCIÓN DE UNIDADES NUEVAS") and
                    z.startswith("CABA")]
        sub_nue = next(ix[(s, z)] for (s, z) in ix if s and s.startswith("DISTRIBUCIÓN DE UNIDADES NUEVAS") and
                       z.startswith("SUBTOTAL"))
        u = usados(self.src)
        filas_y = [("P_USADOS", "Recargas de equipos usados (accionados) / recargas totales", u,
                    "Proyecciones, hojas PROYECCION SALUD / EDUCACION / INDUSTRIASALM / HOTELES: columnas «Mat "
                    "Usados» / «RECARGAS TOT» (O / P) del año"),
                   ("P_CABA_REC", "Recargas con destino CABA", [
                       "=(" + "+".join(f"{q('PROY_INDEXADO')}!{L(2 + j)}{x}" for x in caba_rec) +
                       f")/{q('PROY_INDEXADO')}!{L(2 + j)}{sub_rec}" for j in range(10)],
                    f"PROY_INDEXADO: CABA Norte/Este/Sur/Oeste (filas {caba_rec[0]}-{caba_rec[-1]}) / subtotal "
                    f"(fila {sub_rec})"),
                   ("P_CABA_NUE", "Unidades nuevas con destino CABA", [
                       "=(" + "+".join(f"{q('PROY_INDEXADO')}!{L(2 + j)}{x}" for x in caba_nue) +
                       f")/{q('PROY_INDEXADO')}!{L(2 + j)}{sub_nue}" for j in range(10)],
                    f"PROY_INDEXADO: distribución de unidades nuevas (filas {caba_nue[0]}-{caba_nue[-1]} / "
                    f"{sub_nue}); es la única distribución de unidades nuevas de las Proyecciones")]
        for pid, dato, vals, fu in filas_y:
            r += 1
            ws.cell(r, 1, pid)
            ws.cell(r, 2, dato)
            for j, v in enumerate(vals):
                ws.cell(r, 3 + j, v).number_format = "0.0%"
            ws.cell(r, 13, fu)
            _fila(ws, r, 13)
        self.wb.defined_names["PY_ID"] = DefinedName("PY_ID", attr_text=f"PARAMETROS!$A${r0}:$A${r}")
        self.wb.defined_names["PY_VAL"] = DefinedName("PY_VAL", attr_text=f"PARAMETROS!$C${r0}:$L${r}")
        for row in ws.iter_rows(min_row=4, max_row=r):
            for c in row:
                c.alignment = Alignment(wrap_text=c.column in (2, 5, 6, 13), vertical="top")
        ws.freeze_panes = "B4"
        _imprimir(ws, "3:3", 13)

    # -------- copia de las proyecciones
    def copia(self, origen, nombre):
        src = self.src[origen]
        ws = self.wb.create_sheet(nombre)
        for row in src.iter_rows():
            for c in row:
                if c.value is None:
                    continue
                d = ws.cell(c.row, c.column, c.value)
                d.number_format = c.number_format
                d.font = _f(bool(c.font and c.font.b))
        for k, dim in src.column_dimensions.items():
            if dim.width:
                ws.column_dimensions[k].width = dim.width
        ws.sheet_view.zoomScale = 85
        return ubicar(src)

    # -------- demanda
    def demanda(self):
        ws = self.wb.create_sheet("DEMANDA")
        _titulo(ws, "DEMANDA POR PRODUCTO Y LÍNEA (unidades por año)",
                "Fórmulas sobre PROY_INDEXADO y PROY_RESERVAS (copias de las Proyecciones). Si se pegan valores "
                "nuevos en esas dos hojas, todo el MRP se recalcula.")
        _cab(ws, 3, ["Línea", "Clave", "Producto", "Origen (fila de las Proyecciones)", "Perfil estacional"] + AÑOS,
             [12, 24, 44, 44, 34] + [10] * 10)
        ix, rs = self.ix, self.rs
        sec_fab = next(s for (s, _) in ix if s and s.startswith("PRODUCCION DE MATAFUEGOS"))
        sec_cil = next(s for (s, _) in ix if s and s.startswith("PRODUCCION DE CILINDROS"))
        sec_rec = next(s for (s, _) in ix if s == "RECARGAS")
        sec_rev = next(s for (s, _) in ix if s and s.startswith("MATAFUEGOS TERCIARIZADOS"))
        inv = {v: k for k, v in ETIQ.items()}

        def fx(hoja, filas):
            return ["=" + "+".join(f"{q(hoja)}!{L(2 + j)}{x}" for x in filas) for j in range(10)]

        def fx2(partes):
            return ["=" + "+".join(f"{q(h)}!{L(2 + j)}{x}" for h, x in partes) for j in range(10)]

        filas = []
        venta_res = rs[next(k for k in rs if k[1].startswith("VENTA de reserva"))]
        for c, p, n in MAN + ROD:
            lin = "MANUALES" if (c, p, n) in MAN else "RODANTES"
            fi = ix[(sec_fab, inv[c])]
            if c == "ABC_5kg":
                filas.append((lin, f"FL_MAT_{c}", f"Matafuego {n} nuevo (incluye la venta de reserva)",
                              f"Indexado fila {fi} + Reservas fila {venta_res} (venta de reserva, IRAM 3517-2 5.3)",
                              perfil(c), fx2([("PROY_INDEXADO", fi), ("PROY_RESERVAS", venta_res)])))
            else:
                filas.append((lin, f"FL_MAT_{c}", f"Matafuego {n} nuevo", f"Indexado fila {fi}", perfil(c),
                              fx("PROY_INDEXADO", [fi])))
        for c, p, n in MAN + ROD:
            lin = "MANUALES" if (c, p, n) in MAN else "RODANTES"
            fi = ix[(sec_cil, "Cilindros " + inv[c].replace(" s/ruedas", ""))]
            filas.append((lin, f"FL_REC_{c}", f"Cilindro vacío {n} (venta suelto)", f"Indexado fila {fi}", perfil(c),
                          fx("PROY_INDEXADO", [fi])))
        for etq, c in ETIQ.items():
            fi = ix[(sec_rec, etq)]
            filas.append(("RECARGAS", f"RK_{c}", f"Recarga {NOMBRE[c]} (equipos de clientes)", f"Indexado fila {fi}",
                          perfil(c, True), fx("PROY_INDEXADO", [fi])))
        st = next(s for (s, _) in rs if s and s.startswith("STOCK DE SUSTITUTOS"))
        al = next(s for (s, _) in rs if s and s.startswith("ALTA ANUAL"))
        for etq, c in POOL:
            fi = rs[(st, etq)]
            filas.append(("RECARGAS", f"RKP_{c}", f"Recarga {NOMBRE[c]} del pool de sustitutos (9.4.5)",
                          f"Reservas fila {fi} (stock de sustitutos: se mantiene cada año)", perfil(c, True),
                          fx("PROY_RESERVAS", [fi])))
        for etq, c in POOL:
            fi = rs[(al, etq)]
            filas.append(("RECARGAS", f"FL_SUS_{c}", f"Alta de sustitutos {NOMBRE[c]} (equipo + kit 9.4.5)",
                          f"Reservas fila {fi} (alta anual de sustitutos)", perfil(c, True),
                          fx("PROY_RESERVAS", [fi])))
        for c, n in REV:
            fi = ix[(sec_rev, inv[c])]
            filas.append(("REVENDIDOS", f"FL_MAT_{c}", f"Matafuego {n} revendido", f"Indexado fila {fi}", perfil(c),
                          fx("PROY_INDEXADO", [fi])))
        r = 4
        for lin, clave, nom, ori, per, fs in filas:
            for j, v in enumerate([lin, clave, nom, ori, per] + fs, 1):
                c = ws.cell(r, j, v)
                if j > 5:
                    c.number_format = "#,##0"
            _fila(ws, r, 15)
            self.dem[clave] = r
            r += 1
        self.dem_fin = r - 1
        for lin in LINEAS:
            r += 1
            ws.cell(r, 3, f"Total {lin}").font = _f(True)
            for j in range(10):
                c = ws.cell(r, 6 + j, f'=SUMIF($A$4:$A${self.dem_fin},"{lin}",{L(6 + j)}$4:{L(6 + j)}${self.dem_fin})')
                c.number_format = "#,##0"
                c.font = _f(True)
        ws.freeze_panes = "F4"
        ws.auto_filter.ref = f"A3:O{self.dem_fin}"
        _imprimir(ws, "3:3", 15)

    def D(self, clave, j):
        return f"DEMANDA!{L(6 + j)}{self.dem[clave]}"

    # -------- estacionalidad
    def estacionalidad(self):
        ws = self.wb.create_sheet("ESTACIONALIDAD")
        _titulo(ws, "ESTACIONALIDAD: perfil mensual de cada producto y de cada línea en el año de diseño",
                "Fuente: " + F_PERFILES + ". El perfil de la línea pondera el de cada producto por su demanda del "
                "año de diseño; el mes pico de cada ítem sale de la hoja POLITICA_STOCK.")
        _cab(ws, 3, ["Perfil"] + MESES + ["Total"], [44] + [8] * 13)
        r = 4
        p0 = r
        for nom, v in PERFILES:
            ws.cell(r, 1, nom)
            for j, x in enumerate(v):
                ws.cell(r, 2 + j, x).number_format = "0.0%"
            ws.cell(r, 14, f"=SUM(B{r}:M{r})").number_format = "0%"
            _fila(ws, r, 14)
            r += 1
        p1 = r - 1
        r += 1
        _cab(ws, r, ["Clave (DEMANDA)", "Línea", "Perfil"] + MESES + ["Demanda año de diseño"], c0=16)
        for j, w in enumerate([24, 12, 40] + [7] * 12 + [12], 16):
            ws.column_dimensions[L(j)].width = w
        r_cab = r
        r = 4
        filas_p = []
        for clave, rd in sorted(self.dem.items(), key=lambda x: x[1]):
            ws.cell(r, 16, f"=DEMANDA!B{rd}")
            ws.cell(r, 17, f"=DEMANDA!A{rd}")
            ws.cell(r, 18, f"=DEMANDA!E{rd}")
            for j in range(12):
                ws.cell(r, 19 + j, f"=INDEX($B${p0}:$M${p1},MATCH($R{r},$A${p0}:$A${p1},0),{j + 1})"
                        ).number_format = "0.0%"
            ws.cell(r, 31, f'=INDEX(DEMANDA!$F{rd}:$O{rd},{self.P("AÑO_DIS")}-2025)').number_format = "#,##0"
            _fila(ws, r, 16, c0=16)
            filas_p.append(r)
            r += 1
        a, b = filas_p[0], filas_p[-1]
        ws.cell(r_cab, 16).value = "Clave (DEMANDA)"
        # perfil por línea
        r = p1 + 3
        ws.cell(r, 1, "PERFIL DE CADA LÍNEA EN EL AÑO DE DISEÑO (demanda ponderada)").font = _f(True)
        r += 1
        _cab(ws, r, ["Línea"] + MESES + ["Factor de pico"])
        self.est = {}
        for lin in LINEAS:
            r += 1
            ws.cell(r, 1, lin)
            for j in range(12):
                col = L(19 + j)
                ws.cell(r, 2 + j, f'=SUMPRODUCT(($Q${a}:$Q${b}="{lin}")*$AE${a}:$AE${b}*{col}${a}:{col}${b})/'
                                  f'SUMIF($Q${a}:$Q${b},"{lin}",$AE${a}:$AE${b})').number_format = "0.0%"
            ws.cell(r, 14, f"=MAX(B{r}:M{r})*12").number_format = "0.000"
            _fila(ws, r, 14)
            self.est[lin] = r
        ws.cell(r + 1, 1, "Factor de pico = mes de mayor demanda / mes promedio (1/12).").font = _f(italic=True,
                                                                                                    size=9)
        ws.freeze_panes = "B4"
        _imprimir(ws, "3:3", 31)

    # -------- BOM_COEF
    def item_bom(self, pref, f):
        """(tratamiento, [(ítem, factor como fórmula o número, fuente)], destino) de una fila del BOM."""
        pz, cod = f["Pieza"], f["Código"]
        pa = f["padre"]
        # descendientes de un grupo que se compra armado
        anc = pa
        while anc:
            if anc["Código"].endswith("-K2") or anc["Código"].endswith("-S3"):
                return "Incluido en " + ("la válvula armada" if anc["Código"].endswith("-K2") else
                                         "la manguera armada"), [], ""
            anc = anc["padre"]
        if f["grupo"]:
            if cod.endswith("-K2"):
                return "Se compra armada", [(VALV[pref], 1, "")], ""
            if cod.endswith("-S3"):
                it = f"MP-48/{pref}" if pref in PREF.values() and pref in [p for _, p, _ in MAN] else f"MP-49/{pref}"
                return "Se compra armada", [(it, 1, "")], ""
            return None, [], ""
        if pz in ("Cuerpo", "Cúpula", "Fondo", "Cuello roscado"):
            return "Fabricada (FAB_COMPRA)", [("FAB", pz, "")], ""
        if pz.startswith("Polvo ABC 60"):
            return "Compra", [("MP-33", f'=1+{self.P("MERMA_POLVO")}', "")], ""
        if pz.startswith("Polvo ABC 90"):
            return "Compra", [("MP-33B", f'=1+{self.P("MERMA_POLVO")}', "")], ""
        if pz.startswith("Gas impulsor: N₂"):
            return "Compra (kg → m³)", [("MP-34", f'=(1+{self.P("N2_PERD")})/{self.P("RHO_N2")}', "")], ""
        mapa = {"Manómetro": ("MP-45", ""), "Junta tórica de asiento": (JUNTA.get(pref, "MP-50/M30"), ""),
                "Etiqueta / placa de características": (f"MP-56/{pref}", ""), "Oblea de fabricación": ("MP-78", "PBA"),
                "Estampilla IRAM de conformidad": ("MP-79", ""), "Tarjeta de identificación AGC": ("MP-77", "CABA"),
                "Etiqueta de n° de serie GS1": ("MP-80", ""), "Faja de garantía válvula-cuello": ("MP-81", ""),
                "Precinto de fábrica": ("MP-51", ""), "Soporte de pared": (f"MP-52/{pref}", ""),
                "Soporte vehicular con cierre rápido": ("MP-87", ""), "Tornillo y tarugo de fijación": ("MP-86", ""),
                "Tapón protector de rosca del cuello": (TAPON.get(pref, "MP-62/M30"), ""),
                "Etiqueta de identificación del cilindro suelto": ("MP-88", "")}
        if pz in mapa:
            it, dest = mapa[pz]
            return "Compra", [(it, 1, "")], dest
        if pz.startswith(("Pata delantera", "Triángulos", "Flejes del soporte", "Placas de refuerzo")):
            return "Sale de las orillas del corte (sin compra)", [], ""
        if pz == "Manija del carro":
            mm = MANIJA[pref]
            return "Fabricada (caño)", [("MP-66", f'={mm}/6000/{self.P("APROV_CANO")}',
                                         f"Corte {mm} mm de caño 1\" (proceso de carros, 8.1)")], ""
        if pz == "Caño del eje":
            it, mm = CANO_EJE[pref]
            return "Fabricada (caño)", [(it, f'={mm}/6000/{self.P("APROV_CANO")}',
                                         f"Corte {mm} mm (proceso de carros, 8.1)")], ""
        if pz == "Eje de ruedas":
            it, mm, lb = EJE[pref]
            return "Fabricada (barra)", [(it, f"=1/INT({lb}/{mm})", f"{lb // mm} ejes de {mm} mm por barra de "
                                                                     f"{lb / 1000:g} m (proceso de carros, 8.1)")], ""
        if pz == "Neumático macizo":
            return "Compra (rueda completa)", [(RUEDA[pref], 1, "")], ""
        if pz == "Llanta con cubo":
            return "Incluida en la rueda completa", [], ""
        if pz.startswith("Arandelas de tope"):
            return "Compra", [("MP-70", 4, "4 por carro")], ""
        if pz.startswith("Pasadores del eje"):
            return "Compra", [("MP-71", 2, "2 por carro")], ""
        return "Sin ítem de compra", [], ""

    def bom_coef(self):
        ws = self.wb.create_sheet("BOM_COEF")
        self.ws_bc = ws
        _titulo(ws, "BOM_COEF: lo que se compra por unidad de producto, fila por fila del BOM (FLAMA_BOM.xlsx)",
                "Cant. ítem = Cant. BOM × factor. Las piezas fabricadas toman el factor de FAB_COMPRA. En recargas, "
                "el coeficiente del año = controles × control + (1 − % usados) × mantenimiento + % usados × recarga + "
                "prueba hidráulica / años + reposición.")
        cab = ["Producto", "Código BOM", "Fila BOM", "Pieza / insumo (BOM)", "Cant. BOM", "UM", "Tratamiento",
               "Ítem de compra", "Factor", "Cant. ítem por unidad", "Destino", "Control", "Mantenimiento", "Recarga",
               "Prueba hidráulica", "PH cada (años)", "Reposición"] + [f"Coef. {a}" for a in AÑOS] + ["Fuente"]
        _cab(ws, 3, cab, [20, 16, 16, 44, 9, 6, 30, 12, 10, 11, 8, 8, 10, 8, 9, 8, 9] + [9] * 10 + [50])
        self.r_bc = 4
        self.fab_rows = {}     # (pref, pieza) → [(ítem, celda de factor)]
        return ws

    def _bc(self, prod, f, trat, it, factor, dest, fuente, serv=None, ph=None):
        ws, r = self.ws_bc, self.r_bc
        vals = [prod, f["Código"] if f else "", f"{f['hoja']} {f['fila']}" if f else "",
                f["Pieza"] if f else fuente, f["Cant."] if f else 1, f["UM"] if f else "u", trat, it, factor,
                f"=E{r}*I{r}", dest]
        for j, v in enumerate(vals, 1):
            ws.cell(r, j, v)
        if serv:
            for k, col in zip(("ctrl", "mant", "rec", "ph", "rep"), (12, 13, 14, 15, 17)):
                ws.cell(r, col, serv.get(k, 0))
            ws.cell(r, 16, ph)
            for j in range(10):
                ws.cell(r, 18 + j, f'=J{r}*({self.P("CTRL_AÑO")}*L{r}+(1-{self.PY("P_USADOS", j)})*M{r}+'
                                   f'{self.PY("P_USADOS", j)}*N{r}+IF(P{r}>0,O{r}/P{r},0)+Q{r})')
        else:
            for j in range(10):
                ws.cell(r, 18 + j, f"=$J{r}")
        ws.cell(r, 28, fuente if f else "")
        for j in (5, 9, 10, 12, 13, 14, 15, 17):
            ws.cell(r, j).number_format = "0.######"
        for j in range(18, 28):
            ws.cell(r, j).number_format = "0.######"
        _fila(ws, r, 28)
        self.r_bc += 1
        return r

    def coef_producto(self, clave, hoja_bom, prod_bom, pref, sustituto=False, kit=True):
        """Filas de BOM_COEF de un producto fabricado; devuelve [(ítem, fila, destino)]."""
        out = []
        filas = self.prods[(hoja_bom, prod_bom)]
        en_sus = False
        for f in filas:
            if f["Nivel"] == 0:
                continue
            if f["Código"].startswith("FL_SUS_"):
                en_sus = True
                continue
            if en_sus and f["Nivel"] == 1:
                en_sus = False
            if en_sus:
                if sustituto and kit:
                    it = {"Faja amarilla": "MP-82", "Tarjeta DPS": "MP-83", "Tarjeta AGC": "MP-84",
                          "Remito de préstamo": "MP-85"}[next(k for k in ("Faja amarilla", "Tarjeta DPS",
                                                                           "Tarjeta AGC", "Remito de préstamo")
                                                              if f["Pieza"].startswith(k))]
                    out.append((it, self._bc(clave, f, "Kit de sustituto", it, 1, "", "IRAM 3517-2:2020 9.4.5"), ""))
                continue
            if sustituto:
                continue
            trat, its, dest = self.item_bom(pref, f)
            if trat is None:
                continue
            if not its:
                self._bc(clave, f, trat, "", "", "", "")
                continue
            for it, fac, fu in its:
                if it == "FAB":
                    for it2, celda in self.fab_rows[(pref, fac)]:
                        out.append((it2, self._bc(clave, f, trat, it2, f"=FAB_COMPRA!{celda}", dest,
                                                  "FAB_COMPRA"), dest))
                else:
                    out.append((it, self._bc(clave, f, trat, it, fac, dest, fu), dest))
        return out

    # -------- FAB_COMPRA
    def fab_compra(self):
        ws = self.wb.create_sheet("FAB_COMPRA")
        _titulo(ws, "FAB_COMPRA: de qué materia prima sale cada pieza que se fabrica y cuánto rinde",
                "Cuerpos: piezas por hoja o por caño del plan de corte. Discos de cúpula y fondo: kg de fleje = ancho "
                "× paso × espesor × 7,85 kg/dm³, con paso = Ø del disco + puente (puente = espesor). Casquetes y "
                "cuellos de carros: se compran.")
        _cab(ws, 3, ["Modelo", "Pieza", "Se hace en", "Ítem de compra", "UM ítem", "Base de cálculo", "Ancho (mm)",
                     "Ø disco (mm)", "Espesor (mm)", "Rendimiento", "Factor (ítem por pieza)", "Fuente"],
             [9, 16, 28, 12, 8, 40, 9, 9, 9, 11, 12, 70])
        r = 4
        for _, pref, n in FAB:
            # cuerpo
            it, base, rend, fu = CUERPO[pref]
            for j, v in enumerate([pref, "Cuerpo", "Corte de tubo" if pref == "ABC1" else "Guillotina", it,
                                   ITEM[it]["um"], base, "", "", "", rend, f"=1/J{r}", fu], 1):
                ws.cell(r, j, v)
            self.fab_rows[(pref, "Cuerpo")] = [(it, f"K{r}")]
            _fila(ws, r, 12)
            r += 1
            for pz in ("Cúpula", "Fondo"):
                if (pref, pz) in DISCO:
                    it, an, d, e = DISCO[(pref, pz)]
                    for j, v in enumerate([pref, pz, "Corte de disco y embutido (fleje)", it, "kg",
                                           "kg de fleje por disco = ancho × (Ø + e) × e × 7,85e-6", an, d, e, "",
                                           f"=G{r}*(H{r}+I{r})*I{r}*7.85/1000000",
                                           "Ø disco: planilla de MP (Lineamientos, con sobremedida de recorte); "
                                           "ancho: cotización Pacheco PR-42021 / planilla; espesor: plano y proceso "
                                           "de manuales"], 1):
                        ws.cell(r, j, v)
                else:
                    it = CASQ[pref]
                    for j, v in enumerate([pref, pz, "Se compra embutido (casquete)", it, "u",
                                           "1 casquete por pieza (cúpula y fondo son iguales)", "", "", "", 1,
                                           f"=1/J{r}", "Proceso de carros, puesto 1: casquetes MP-15 a 17"], 1):
                        ws.cell(r, j, v)
                self.fab_rows[(pref, pz)] = [(it, f"K{r}")]
                _fila(ws, r, 12)
                r += 1
            it = CUELLO[pref]
            for j, v in enumerate([pref, "Cuello roscado", "Se compra mecanizado", it, "u", "1 por recipiente", "", "",
                                   "", 1, f"=1/J{r}", "Proceso de manuales (cuellos comprados) / carros (cuplas)"], 1):
                ws.cell(r, j, v)
            self.fab_rows[(pref, "Cuello roscado")] = [(it, f"K{r}")]
            _fila(ws, r, 12)
            r += 1
        for row in ws.iter_rows(min_row=4, max_row=r):
            for c in row:
                if c.column in (7, 8, 9, 10):
                    c.number_format = "0.##"
                if c.column == 11:
                    c.number_format = "0.000000"
                c.alignment = Alignment(wrap_text=c.column in (6, 12), vertical="top")
        ws.freeze_panes = "C4"
        _imprimir(ws, "3:3", 12)

    # -------- PROCESO
    def proceso(self):
        ws = self.wb.create_sheet("PROCESO")
        self.ws_pr = ws
        _titulo(ws, "PROCESO: insumos de proceso y embalaje por unidad, puesto por puesto",
                "Coeficiente por unidad de producto. Tipo: Directo si queda en el producto o sale con él (alambre, "
                "pintura, embalaje); Indirecto si se gasta en el puesto (gas de protección, discos, granalla, "
                "tapones).")
        _cab(ws, 3, ["Línea", "Puesto", "Ítem", "UM", "Tipo", "Modelo", "Aplica a", "Base de cálculo",
                     "Coef. por unidad", "Fuente"], [10, 34, 12, 6, 9, 8, 22, 46, 12, 70])
        self.r_pr = 4
        self.pr = {}       # (línea, modelo) → [(ítem, fila, tipo, aplica)]

        def fila(lin, puesto, it, tipo, pref, aplica, base, coef, fuente):
            r = self.r_pr
            for j, v in enumerate([lin, puesto, it, ITEM[it]["um"], tipo, pref, aplica, base, coef, fuente], 1):
                ws.cell(r, j, v)
            ws.cell(r, 9).number_format = "0.000000"
            for c in ws[r]:
                c.alignment = Alignment(wrap_text=c.column in (2, 8, 10), vertical="top")
            _fila(ws, r, 10)
            self.pr.setdefault((lin, pref), []).append((it, r, tipo, aplica))
            self.r_pr += 1

        P = self.P
        sup = {}
        for _, pref, _ in MAN:
            filas = self.prods[("Fabricados", f"FL_MAT_{[c for c, p, _ in FAB if p == pref][0]}")]
            sup[pref] = {f["Pieza"]: f["Superficie (dm²)"] for f in filas if f["Nivel"] == 2 and
                         f["Pieza"] in ("Cuerpo", "Cúpula", "Fondo")}
        for _, pref, n in MAN:
            s = sup[pref]
            area = (s["Cuerpo"] + s["Cúpula"] + s["Fondo"]) / 2 / 100
            fila("MANUALES", "Soldadura longitudinal, de cuello y circunferencial (MAG 135)", "MP-25", IN, pref,
                 "Recipiente (terminado y cilindro)", "m³ de Ar + 8 % CO₂ por recipiente (largo de costura × caudal) × GAS_MAN_AJ",
                 f'={GAS_MAN[pref]}*{P("GAS_MAN_AJ")}', "Planilla de MP (opción D), Coef Fabricación MP-25 "
                 "(geometría de costuras) × ajuste al consumo del proceso de manuales (GAS_MAN_AJ)")
            fila("MANUALES", "Soldadura (MAG 135)", "MP-23", D, pref, "Recipiente (terminado y cilindro)",
                 "kg de alambre Ø0,9 por recipiente", ALAMBRE_MAN[pref],
                 "Planilla de MP, Coef Fabricación MP-23 (geometría); proceso de manuales: alambre de 0,9 mm")
            fila("MANUALES", "Soldadura (MAG 135)", "MP-26", IN, pref, "Recipiente (terminado y cilindro)",
                 "1 punta cada ALAMBRE_PUNTA kg de alambre", f'={ALAMBRE_MAN[pref]}/{P("ALAMBRE_PUNTA")}',
                 "Planilla de MP (estimado)")
            fila("MANUALES", "Inspección y corrección de defectos (amoladora con disco flap)", "MP-93", IN, pref,
                 "Recipiente (terminado y cilindro)", "1 disco cada DISCO_MAN recipientes", f'=1/{P("DISCO_MAN")}',
                 "Planilla de MP (estimado); proceso de manuales: amoladora 115 mm con disco flap")
            fila("MANUALES", "Granallado (AirBlast G-100)", "MP-28", IN, pref, "Recipiente (terminado y cilindro)",
                 "kg de granalla por cilindro", f'={P("GRANALLA")}', "Proceso de manuales, granallado")
            fila("MANUALES", "Granallado y pintura (enmascarado de la rosca)", "MP-32", IN, pref,
                 "Recipiente (terminado y cilindro)", "1 tapón cada TAPON_CICLOS cilindros", f'=1/{P("TAPON_CICLOS")}',
                 "Proceso de manuales (tapones-gancho que circulan); planilla de MP (vida útil estimada)")
            fila("MANUALES", "Pintura en polvo y horno (Firesafer)", "MP-31", D, pref,
                 "Recipiente (terminado y cilindro)",
                 f"kg = área exterior {area:.4f} m² × ρ × espesor / 1000 / aprovechamiento",
                 f'={area:.5f}*{P("PINT_RHO")}*{P("PINT_ESP")}/1000/{P("PINT_APROV")}',
                 f"Área exterior = (S cuerpo {s['Cuerpo']:.2f} + S cúpula {s['Cúpula']:.2f} + S fondo "
                 f"{s['Fondo']:.2f}) / 2 dm² (FLAMA_BOM, superficie de las dos caras); rendimiento m²/kg = 1000 / "
                 "(ρ × espesor) (Tiger Drylac)")
            pp = POR_PALLET_MAN[pref]
            for it, base, coef, fu in [
                    (f"MP-59/{pref}", "1 caja por recipiente", 1, "Proceso de manuales, embalaje: «una caja de "
                     f"cartón corrugado por recipiente (simple hasta el 5 kg, doble en el 10 kg)»"),
                    ("MP-89", "1 etiqueta de caja por recipiente", 1, "Proceso de manuales, embalaje"),
                    ("MP-60", f"1 pallet cada {pp} recipientes", f"=1/{pp}",
                     "Proceso de manuales, embalaje: tabla de unidades por pallet (BOM)"),
                    ("MP-63", "FILM_PALLET kg por pallet", f'={P("FILM_PALLET")}/{pp}', "Planilla de MP (estimado)"),
                    ("MP-90", "1 etiqueta por pallet", f"=1/{pp}", "Proceso de manuales, embalaje")]:
                fila("MANUALES", "Embalaje y palletizado", it, D, pref, "Recipiente (terminado y cilindro)", base,
                     coef, fu)
            fila("MANUALES", "Embalaje (cilindro vacío)", "MP-85", D, pref, "Sólo cilindro vacío",
                 "1 protocolo de ensayo por cilindro", 1, "Proceso de manuales, embalaje: «El protocolo de ensayo "
                 "hidrostático (R5 del plano) acompaña a cada cilindro vacío»")
        for k, (_, pref, n) in enumerate(ROD):
            for puesto, gas, alam in CARRO:
                fila("RODANTES", puesto, "MP-25", IN, pref, "Recipiente (terminado y cilindro)" if "accesorios" not in
                     puesto else "Sólo carro terminado", f"{gas[k]} L de Ar + 8 % CO₂ por unidad",
                     f"={gas[k]}/1000", f"Proceso de carros, {puesto.split(',')[0].lower()}: tabla de consumo de gas "
                     "y alambre")
                fila("RODANTES", puesto, "MP-24", D, pref, "Recipiente (terminado y cilindro)" if "accesorios" not in
                     puesto else "Sólo carro terminado", f"{alam[k]} g de alambre Ø1,0 por unidad",
                     f"={alam[k]}/1000", f"Proceso de carros, {puesto.split(',')[0].lower()}: tabla de consumo")
            fila("RODANTES", "Soldadura (todos los puestos)", "MP-26", IN, pref, "Recipiente (terminado y cilindro)",
                 "1 punta cada ALAMBRE_PUNTA kg de alambre",
                 f'=({"+".join(str(a[k]) for _, _, a in CARRO)})/1000/{P("ALAMBRE_PUNTA")}',
                 "Planilla de MP (estimado), sobre el alambre de los cinco puestos")
            fila("RODANTES", "Puesto 6, soldadura de cupla", "MP-95", IN, pref, "Recipiente (terminado y cilindro)",
                 "1 ml por cúpula; aerosol de 400 ml", "=1/400", "Proceso de carros, puesto 6: «un disparo corto, "
                 "de alrededor de 1 segundo (unos 1 ml)»")
            if pref in ("ABC70", "ABC100"):
                fila("RODANTES", "Puesto 4, placas de refuerzo", "MP-27", IN, pref, "Recipiente (terminado y cilindro)",
                     "7 discos por mes pico / 80 cuerpos de 70 y 100 kg por mes", "=7/80", "Proceso de carros, "
                     "puesto 4: «un disco de corte por tanda (7 por mes en el pico)»; 4 cuerpos por día × 20 días")
                fila("RODANTES", "Puesto 4, placas de refuerzo", "MP-93", IN, pref, "Recipiente (terminado y cilindro)",
                     "1 disco flap cada 4 tandas", "=7/4/80", "Proceso de carros, puesto 4: «un disco flap cada 4 "
                     "tandas»")
            for it, base, coef, fu in [
                    ("MP-92", "3 cortes por juego / 200 cortes por disco", "=3/200", "Proceso de carros, 8.1: tabla de "
                     "consumos («unos 200 cortes por disco de sensitiva»)"),
                    ("MP-27", "1 disco cada 40 juegos de triángulos", "=1/40", "Proceso de carros, 8.1: «40 juegos de "
                     "triángulos por disco de corte de 115 mm»"),
                    ("MP-93", "2 discos flap por mes pico / 400 juegos", "=2/400", "Proceso de carros, 8.1: tabla de "
                     "consumos"),
                    ("MP-94", "2 agujeros por juego / 200 agujeros por mecha", "=2/200", "Proceso de carros, 8.1: "
                     "«200 agujeros por mecha»")]:
                fila("RODANTES", "Puesto 8.1, fabricación de accesorios", it, IN, pref, "Sólo carro terminado", base,
                     coef, fu)
            fila("RODANTES", "Puesto 12, pintura (tercerizada)", f"MP-96/{pref}", D, pref,
                 "Recipiente (terminado y cilindro)", "1 servicio por unidad", 1,
                 "Proceso de carros, 8.1: «luego del pintado que es tercerizado»; cotización por carro")
            fila("RODANTES", "Embalaje (carro terminado)", "MP-91", D, pref, "Sólo carro terminado",
                 "1 funda por carro", 1, "Investigación de proveedores (funda de PE de rodantes); el proceso de carros "
                 "no tiene escrito el embalaje (estimado)")
            pp = POR_PALLET_ROD[pref]
            for it, base, coef, fu in [
                    ("MP-60", f"1 pallet cada {pp} cilindros", f"=1/{pp}", "Planilla de MP, hoja Pallets PT "
                     "(estimado)"),
                    ("MP-63", "FILM_PALLET kg por pallet", f'={P("FILM_PALLET")}/{pp}', "Planilla de MP (estimado)"),
                    ("MP-64", "ESQ_PALLET esquineros por pallet", f'={P("ESQ_PALLET")}/{pp}', "Planilla de MP "
                     "(estimado)"),
                    ("MP-90", "1 etiqueta por pallet", f"=1/{pp}", "Ídem manuales"),
                    ("MP-85", "1 protocolo de ensayo por cilindro", 1, "Ídem manuales")]:
                fila("RODANTES", "Embalaje (cilindro vacío)", it, D, pref, "Sólo cilindro vacío", base, coef, fu)
        # recargas
        for c in [x for x, _, _ in FAB] + [x for x, _ in REV]:
            fila("RECARGAS", "Retoque de pintura", "MP-65", D, c, "Recarga", "P_RETOQUE × RETOQUE_L litros por "
                 "equipo", f'={P("P_RETOQUE")}*{P("RETOQUE_L")}', "Dimensionamiento Técnico V2, Parametros Recargas "
                 "(15 %); planilla de MP (0,05 L)")
        ws.freeze_panes = "D4"
        ws.auto_filter.ref = f"A3:J{self.r_pr - 1}"
        _imprimir(ws, "3:3", 10)

    # -------- recargas (BOM_COEF por servicio)
    AG = [("Polvo ABC 60", "MP-33"), ("Polvo ABC 90", "MP-33B"), ("Polvo BC", "MP-35"), ("Polvo químico BC", "MP-35"),
          ("Polvo para metales", "MP-36"), ("Dióxido de carbono", "MP-37"), ("HCFC", "MP-38"),
          ("Concentrado AFFF", "MP-40"), ("Acetato de potasio", "MP-41")]
    ID_REC = {"Etiqueta de control": ("MP-73", ""), "Precinto con identificación": ("MP-97", ""),
              "Marbete indicador": ("MP-57", ""), "Etiqueta de servicio": ("MP-72", ""),
              "Estampilla y oblea de recarga": ("MP-75", "PBA"), "Tarjeta de identificación DPS": ("MP-76", "PBA"),
              "Tarjeta de identificación AGC": ("MP-77", "CABA"), "Conjunto de seguridad": ("MP-55", ""),
              "Oblea de vencimiento": ("MP-74", "")}

    def coef_recarga(self, c):
        """Filas de BOM_COEF de la recarga del tipo c: una por ítem, con la cantidad de cada servicio."""
        filas = self.prods[("Recargas", f"RK_{c}")]
        pref = PREF.get(c)
        serv_de = {"1": "ctrl", "2": "mant", "3": "rec", "4": "ph"}
        acum = {}
        excl = []
        serv = None
        for f in filas:
            if f["Nivel"] == 1:
                serv = serv_de[f["Código"].rsplit("-", 1)[1]]
                continue
            if f["Nivel"] != 2:
                continue
            pz = f["Pieza"]
            it, fac, dest = None, 1, ""
            if "recuperado" in pz or pz.startswith("Agua") or "Aire comprimido" in pz:
                excl.append(f)
                continue
            if pz.startswith("Gas impulsor: N₂"):
                it, fac = "MP-34", f'=(1+{self.P("N2_PERD")})/{self.P("RHO_N2")}'
            elif pz.startswith("Gas impulsor: Argón"):
                it, fac = "MP-39", f'=(1+{self.P("N2_PERD")})/{self.P("RHO_AR")}'
            elif pz.startswith("Junta tórica"):
                it = JUNTA.get(pref, "MP-50/M30") if pref else "MP-50/OT"
            else:
                for k, v in self.AG:
                    if pz.startswith(k):
                        it = v
                for k, (v, d) in self.ID_REC.items():
                    if pz.startswith(k):
                        it, dest = v, d
            if not it:
                excl.append(f)
                continue
            a = acum.setdefault(it, dict(fac=fac, dest=dest, um=f["UM"], piezas=[], codigos=[], filas=[],
                                         s={"ctrl": 0, "mant": 0, "rec": 0, "ph": 0}))
            a["s"][serv] += f["Cant."] or 0
            if pz not in a["piezas"]:
                a["piezas"].append(pz)
            a["codigos"].append(f["Código"])
            a["filas"].append(str(f["fila"]))
        ph = self.modelos[f"FL_MAT_{c}"]["Prueba hidráulica cada (años)"]
        out = []
        for it, a in acum.items():
            cods = ", ".join(sorted(set(x.rsplit("-", 1)[1] for x in a["codigos"])))
            filas_bom = "Recargas " + ", ".join(a["filas"])
            out.append((it, self._bc_rec(f"RK_{c}", cods, filas_bom, " / ".join(a["piezas"]), a["um"], it, a["fac"],
                                         a["dest"], a["s"], ph, 0, "FLAMA_BOM, hoja Recargas (IRAM 3517-2:2020)"),
                        a["dest"]))
        for f in excl:
            self._bc_rec(f"RK_{c}", f["Código"].rsplit("-", 1)[1], f"Recargas {f['fila']}", f["Pieza"], f["UM"], "",
                         "", "", {}, 0, 0, "No se compra: " + ("se recupera" if "recuperado" in f["Pieza"] else
                                                               "agua de red o aire del compresor de planta"))
        if pref:
            m = [x for x in MAN if x[1] == pref]
            rep = [(VALV[pref], "REPO_VALV", "Válvula de reemplazo"), ("MP-45", "REPO_MANO", "Manómetro de reemplazo")]
            if pref != "ABC1":
                rep.append((f"MP-48/{pref}" if m else f"MP-49/{pref}", "REPO_MANG", "Manguera de reemplazo"))
            for it, pid, txt in rep:
                out.append((it, self._bc_rec(f"RK_{c}", "", "", txt, "u", it, 1, "", {}, 0,
                                             f'={self.P(pid)}', "Reposición en el mantenimiento: planilla de MP "
                                             "(estimado)"), ""))
        return out

    def _bc_rec(self, prod, cod, fila, pieza, um, it, fac, dest, s, ph, rep, fuente):
        ws, r = self.ws_bc, self.r_bc
        trat = "Compra por servicio" if it and s else ("Reposición" if it else "Sin compra")
        vals = [prod, cod, fila, pieza, 1, um, trat, it, fac, f"=E{r}*I{r}" if it else "", dest,
                s.get("ctrl", 0), s.get("mant", 0), s.get("rec", 0), s.get("ph", 0), ph, rep]
        for j, v in enumerate(vals, 1):
            ws.cell(r, j, v)
        if it:
            for j in range(10):
                ws.cell(r, 18 + j, f'=J{r}*({self.P("CTRL_AÑO")}*L{r}+(1-{self.PY("P_USADOS", j)})*M{r}+'
                                   f'{self.PY("P_USADOS", j)}*N{r}+IF(P{r}>0,O{r}/P{r},0)+Q{r})')
        ws.cell(r, 28, fuente)
        for j in list(range(5, 18)) + list(range(18, 28)):
            ws.cell(r, j).number_format = "0.######"
        _fila(ws, r, 28)
        self.r_bc += 1
        return r

    def coef_simple(self, prod, pieza, it, dest, fuente):
        ws, r = self.ws_bc, self.r_bc
        for j, v in enumerate([prod, "", "", pieza, 1, ITEM[it]["um"], "Compra", it, 1, f"=E{r}*I{r}", dest], 1):
            ws.cell(r, j, v)
        for j in range(10):
            ws.cell(r, 18 + j, f"=$J{r}")
        ws.cell(r, 28, fuente)
        _fila(ws, r, 28)
        self.r_bc += 1
        return r

    def coeficientes(self):
        """Arma BOM_COEF y deja en self.hijos, por línea y tipo, las filas hijas de las hojas de insumos."""
        self.hijos = {}      # (línea, tipo) → {ítem: [(clave, texto, fuente_coef, destino, base de destino)]}
        bc = lambda r: [f"BOM_COEF!{L(18 + j)}{r}" for j in range(10)]
        pr = lambda r: [f"PROCESO!$I${r}"] * 10

        def add(lin, it, clave, txt, refs, dest, base):
            tipo = ITEM[it]["tipo"]
            self.hijos.setdefault((lin, tipo), {}).setdefault(it, []).append((clave, txt, refs, dest, base))

        def piezas(r):
            return self.ws_bc.cell(r, 4).value

        self.base_fab = {}
        for c, pref, n in FAB:
            lin = "MANUALES" if pref in [p for _, p, _ in MAN] else "RODANTES"
            for clave, hoja, prod, aplica in ((f"FL_MAT_{c}", "Fabricados", f"FL_MAT_{c}", "terminado"),
                                              (f"FL_REC_{c}", "Cilindros", f"FL_REC_{c}", "cilindro")):
                rows = self.coef_producto(clave, hoja, prod, pref)
                if aplica == "terminado":
                    self.base_fab[c] = rows
                for it, r, dest in rows:
                    add(lin, it, clave, f"{n} {aplica} · {piezas(r)}", bc(r), dest, "NUE")
                for it, r, tipo, ap in self.pr.get((lin, pref), []):
                    if ap.startswith("Recipiente") or (aplica == "terminado" and ap.startswith("Sólo carro")) or \
                            (aplica == "cilindro" and ap.startswith("Sólo cilindro")):
                        add(lin, it, clave, f"{n} {aplica} · {self.ws_pr.cell(r, 2).value}", pr(r), "", "")
        # revendidos
        for c, n in REV:
            r = self.coef_simple(f"FL_MAT_{c}", "Equipo terminado comprado al fabricante", f"RV-{c}", "",
                                 "Se compra terminado e identificado por su fabricante")
            add("REVENDIDOS", f"RV-{c}", f"FL_MAT_{c}", f"{n} · equipo terminado", bc(r), "", "")
            r = self.coef_simple(f"FL_MAT_{c}", "Tarjeta AGC (sólo destino CABA)", "MP-77", "CABA",
                                 "Ord. 40.473 / Res. AGC 32/15: la tarjeta la agrega quien vende en CABA")
            add("REVENDIDOS", "MP-77", f"FL_MAT_{c}", f"{n} · tarjeta AGC", bc(r), "CABA", "NUE")
        # recargas de clientes y del pool
        self.rec_rows = {}
        for c in [x for x, _, _ in FAB] + [x for x, _ in REV]:
            self.rec_rows[c] = self.coef_recarga(c)
        prr = {self.ws_pr.cell(r, 6).value: r for r in range(4, self.r_pr) if self.ws_pr.cell(r, 1).value ==
               "RECARGAS"}
        for c in [x for x, _, _ in FAB] + [x for x, _ in REV]:
            for clave, txt in ((f"RK_{c}", "recarga de clientes"), (f"RKP_{c}", "recarga del pool de sustitutos")):
                if clave not in self.dem:
                    continue
                for it, r, dest in self.rec_rows[c]:
                    add("RECARGAS", it, clave, f"{NOMBRE[c]} {txt} · {piezas(r)}", bc(r), dest, "REC")
                add("RECARGAS", "MP-65", clave, f"{NOMBRE[c]} {txt} · retoque de pintura", pr(prr[c]), "", "")
        # alta de sustitutos: equipo base + kit
        for _, c in POOL:
            clave = f"FL_SUS_{c}"
            if c in PREF:
                pref = PREF[c]
                lin = "MANUALES" if pref in [p for _, p, _ in MAN] else "RODANTES"
                for it, r, dest in self.base_fab[c]:
                    add("RECARGAS", it, clave, f"Sustituto {NOMBRE[c]} · {piezas(r)}", bc(r), dest, "NUE")
                for it, r, tipo, ap in self.pr.get((lin, pref), []):
                    if (ap.startswith("Recipiente") or ap.startswith("Sólo carro")) and \
                            "Embalaje" not in self.ws_pr.cell(r, 2).value:
                        add("RECARGAS", it, clave, f"Sustituto {NOMBRE[c]} · {self.ws_pr.cell(r, 2).value}", pr(r),
                            "", "")
                kit = self.coef_producto(clave, "Fabricados", f"FL_MAT_{c}", pref, sustituto=True)
            else:
                r = self.coef_simple(clave, "Equipo base del sustituto (terminado)", f"RV-{c}", "",
                                     "IRAM 3517-2:2020 9.4.5: igual clasificación y capacidad")
                add("RECARGAS", f"RV-{c}", clave, f"Sustituto {NOMBRE[c]} · equipo terminado", bc(r), "", "")
                kit = self.coef_producto(clave, "Revendidos", f"FL_MAT_{c}", None, sustituto=True)
            for it, r, dest in kit:
                add("RECARGAS", it, clave, f"Sustituto {NOMBRE[c]} · {piezas(r)}", bc(r), dest, "")
        ws = self.ws_bc
        ws.freeze_panes = "E4"
        ws.auto_filter.ref = f"A3:AB{self.r_bc - 1}"
        for row in ws.iter_rows(min_row=4, max_row=self.r_bc):
            for c in row:
                c.alignment = Alignment(wrap_text=c.column in (4, 7, 28), vertical="top")
        _imprimir(ws, "3:3", 28)

    # -------- COMPRAS
    def compras(self):
        ws = self.wb.create_sheet("COMPRAS")
        _titulo(ws, "COMPRAS: catálogo de ítems con tipo, clase, almacén, proveedor, unidad de compra y lead time",
                "Lead time en días hábiles. Origen: Cotización (presupuesto o mensaje del proveedor), Proceso "
                "(documento de proceso de FLAMA), Planilla de MP (estimado del equipo), Supuesto (a confirmar). "
                "T = días hábiles entre pedidos: 5 MP crítica y gases, 10 nacionales y organismos, 20 importados.")
        cab = ["Código", "Ítem", "UM", "Tipo", "Clase", "Almacén", "Proveedor principal", "Alternativa", "Estado",
               "Unidad de compra (UC)", "Contenido por UC (UM)", "Lead time (días háb.)", "Origen del lead time",
               "Fuente del lead time", "T (días háb.)", "UC por posición", "m² por posición", "Nota"]
        _cab(ws, 3, cab, [11, 50, 6, 9, 20, 30, 28, 24, 16, 26, 11, 10, 14, 60, 8, 9, 9, 50])
        r = 4
        self.c_fila = {}
        for it in ITEMS:
            vals = [it["cod"], it["nom"], it["um"], it["tipo"], it["clase"], it["zona"], it["prov"], it["alt"],
                    it["estado"], it["uc"], it["cont"], it["lt"], it["lt_or"], it["lt_fu"], it["T"], it["ucpos"],
                    it["m2"], it["nota"]]
            for j, v in enumerate(vals, 1):
                c = ws.cell(r, j, v)
                c.alignment = Alignment(wrap_text=j in (2, 6, 7, 10, 14, 18), vertical="top")
            _fila(ws, r, 18)
            self.c_fila[it["cod"]] = r
            r += 1
        self.wb.defined_names["C_COD"] = DefinedName("C_COD", attr_text=f"COMPRAS!$A$4:$A${r - 1}")
        self.wb.defined_names["C_TAB"] = DefinedName("C_TAB", attr_text=f"COMPRAS!$A$4:$R${r - 1}")
        ws.freeze_panes = "C4"
        ws.auto_filter.ref = f"A3:R{r - 1}"
        _imprimir(ws, "3:3", 18)

    def C(self, celda, k):
        return f"INDEX(C_TAB,MATCH({celda},C_COD,0),{k})"

    # -------- hojas de insumos por línea
    def insumos(self, lin, tipo):
        nombre = f"INSUMOS_{'DIRECTOS' if tipo == D else 'INDIRECTOS'}_{lin}"
        ws = self.wb.create_sheet(nombre)
        _titulo(ws, f"{nombre.replace('_', ' ')}: requerimiento bruto por año",
                "Fila gris = total del ítem (suma de las filas de abajo). Cada fila de abajo = coeficiente por unidad "
                "× demanda del producto × % del destino si el ítem es sólo de CABA o de PBA. El coeficiente sale de "
                "la celda indicada en la última columna.")
        _cab(ws, 3, ["Nivel", "Código", "Ítem / origen", "UM", "Producto (DEMANDA)", "Coef. año de diseño",
                     "Destino"] + AÑOS + ["Coeficiente en"], [6, 12, 60, 6, 20, 11, 8] + [11] * 10 + [22])
        hijos = self.hijos.get((lin, tipo), {})
        r = 4
        orden = [it["cod"] for it in ITEMS if it["cod"] in hijos]
        if not orden:
            ws.cell(r, 3, "Sin insumos de este tipo: los equipos revendidos llegan terminados del fabricante; el "
                          "manipuleo es del almacén").font = _f(italic=True)
        for cod in orden:
            hs = hijos[cod]
            r0 = r
            ws.cell(r, 1, 0)
            ws.cell(r, 2, cod)
            ws.cell(r, 3, ITEM[cod]["nom"])
            ws.cell(r, 4, ITEM[cod]["um"])
            r1 = r0 + (3 if cod == "MP-12" and lin == "RODANTES" else len(hs))
            for j in range(10):
                ws.cell(r, 8 + j, f"=SUM({L(8 + j)}{r0 + 1}:{L(8 + j)}{r1})").number_format = "#,##0.00"
            _fila(ws, r, 18, 0)
            self.tot[(nombre, cod)] = r
            if cod == "MP-12" and lin == "RODANTES":
                r = self._hoja_mixta(ws, r0)
                continue
            for clave, txt, refs, dest, base in hs:
                r += 1
                ws.row_dimensions[r].outline_level = 1
                ws.cell(r, 1, 1)
                ws.cell(r, 2, cod)
                ws.cell(r, 3, txt)
                ws.cell(r, 4, ITEM[cod]["um"])
                ws.cell(r, 5, clave)
                ws.cell(r, 6, f'=INDEX(({",".join(refs)}),1,1,{self.P("AÑO_DIS")}-2025)' if len(set(refs)) > 1
                        else f"={refs[0]}").number_format = "0.######"
                ws.cell(r, 7, dest or "Todos")
                for j in range(10):
                    pc = "P_CABA_REC" if base == "REC" else "P_CABA_NUE"
                    fd = ("" if not dest else f"*{self.PY(pc, j)}" if dest == "CABA" else
                          f"*(1-{self.PY(pc, j)})")
                    ws.cell(r, 8 + j, f"={refs[j]}*{self.D(clave, j)}{fd}").number_format = "#,##0.00"
                ws.cell(r, 18, refs[0].split("!")[0] + "!" + refs[0].split("!")[1].replace("$", "") +
                        (" (por año)" if len(set(refs)) > 1 else ""))
                _fila(ws, r, 18)
                ws.cell(r, 3).alignment = Alignment(indent=2)
            r += 1
        ws.freeze_panes = "H4"
        ws.auto_filter.ref = f"A3:R{max(r - 1, 4)}"
        _imprimir(ws, "3:3", 18)
        return nombre

    def _hoja_mixta(self, ws, r0):
        """MP-12 en RODANTES: plan de corte mixto (3 cuerpos de 70 kg + 1 de 100 kg por hoja) y el resto en hojas de
        un solo modelo."""
        n70 = lambda j: f"({self.D('FL_MAT_ABC_70kg', j)}+{self.D('FL_REC_ABC_70kg', j)})"
        n100 = lambda j: f"({self.D('FL_MAT_ABC_100kg', j)}+{self.D('FL_REC_ABC_100kg', j)})"
        filas = [("Hojas mixtas: 3 cuerpos de 70 kg + 1 de 100 kg (79,2 %)",
                  lambda j: f"=MIN({n70(j)}/3,{n100(j)})"),
                 ("Hojas de 70 kg solas: 4 cuerpos (73,3 %)", lambda j: f"=({n70(j)}-3*{L(8 + j)}{r0 + 1})/4"),
                 ("Hojas de 100 kg solas: 3 cuerpos (72,7 %)", lambda j: f"=({n100(j)}-{L(8 + j)}{r0 + 1})/3")]
        r = r0
        for txt, fx in filas:
            r += 1
            ws.row_dimensions[r].outline_level = 1
            ws.cell(r, 1, 1)
            ws.cell(r, 2, "MP-12")
            ws.cell(r, 3, txt).alignment = Alignment(indent=2)
            ws.cell(r, 4, "hoja")
            ws.cell(r, 5, "FL_MAT + FL_REC 70 y 100 kg")
            ws.cell(r, 7, "Todos")
            for j in range(10):
                ws.cell(r, 8 + j, fx(j)).number_format = "#,##0.00"
            ws.cell(r, 18, "Proceso de carros, puesto 2 (planes de corte)")
            _fila(ws, r, 18)
        return r + 1

    # -------- consolidado
    def consolidado(self, hojas):
        ws = self.wb.create_sheet("CONSOLIDADO_INSUMOS")
        _titulo(ws, "CONSOLIDADO DE INSUMOS: requerimiento bruto por ítem, de qué línea y hoja sale",
                "Fila gris = total del ítem; abajo, una fila por hoja de origen (referencia a la fila de total del ítem "
                "en esa hoja). Tipo, clase, almacén, unidad de compra, proveedor y lead time se buscan en COMPRAS.")
        cab = ["Nivel", "Código", "Ítem / origen", "UM", "Tipo", "Clase", "Almacén", "Línea", "Hoja de origen"] + \
            AÑOS + ["Año de diseño", "Unidad de compra", "Contenido por UC", "UC en el año de diseño",
                    "Proveedor principal", "Lead time (días háb.)"]
        _cab(ws, 3, cab, [6, 12, 52, 6, 9, 18, 26, 12, 30] + [11] * 10 + [12, 24, 10, 11, 24, 9])
        r = 4
        self.cons = {}
        for it in ITEMS:
            orig = [(h, lin) for h, lin in hojas if (h, it["cod"]) in self.tot]
            if not orig:
                continue
            r0 = r
            ws.cell(r, 1, 0)
            ws.cell(r, 2, it["cod"])
            ws.cell(r, 3, f"={self.C(f'$B{r}', 2)}")
            ws.cell(r, 4, f"={self.C(f'$B{r}', 3)}")
            ws.cell(r, 5, f"={self.C(f'$B{r}', 4)}")
            ws.cell(r, 6, f"={self.C(f'$B{r}', 5)}")
            ws.cell(r, 7, f"={self.C(f'$B{r}', 6)}")
            for j in range(10):
                ws.cell(r, 10 + j, f"=SUM({L(10 + j)}{r0 + 1}:{L(10 + j)}{r0 + len(orig)})").number_format = "#,##0.00"
            ws.cell(r, 20, f'=INDEX(J{r}:S{r},{self.P("AÑO_DIS")}-2025)').number_format = "#,##0.00"
            ws.cell(r, 21, f"={self.C(f'$B{r}', 10)}")
            ws.cell(r, 22, f"={self.C(f'$B{r}', 11)}")
            ws.cell(r, 23, f"=ROUNDUP(T{r}/V{r},0)").number_format = "#,##0"
            ws.cell(r, 24, f"={self.C(f'$B{r}', 7)}")
            ws.cell(r, 25, f"={self.C(f'$B{r}', 12)}")
            _fila(ws, r, 25, 0)
            self.cons[it["cod"]] = r
            for h, lin in orig:
                r += 1
                ws.row_dimensions[r].outline_level = 1
                ws.cell(r, 1, 1)
                ws.cell(r, 2, it["cod"])
                ws.cell(r, 3, f"Sale de {h}").alignment = Alignment(indent=2)
                ws.cell(r, 8, lin)
                ws.cell(r, 9, h)
                for j in range(10):
                    ws.cell(r, 10 + j, f"={q(h)}!{L(8 + j)}{self.tot[(h, it['cod'])]}").number_format = "#,##0.00"
                ws.cell(r, 20, f'=INDEX(J{r}:S{r},{self.P("AÑO_DIS")}-2025)').number_format = "#,##0.00"
                _fila(ws, r, 25)
            r += 1
        self.cons_fin = r - 1
        ws.freeze_panes = "D4"
        ws.auto_filter.ref = f"A3:Y{r - 1}"
        _imprimir(ws, "3:3", 25)

    # -------- política de stock
    def politica(self):
        ws = self.wb.create_sheet("POLITICA_STOCK")
        _titulo(ws, "POLÍTICA DE STOCK EN EL AÑO DE DISEÑO (año 10): por ítem y almacén",
                "d prom = consumo del año / días hábiles; d pico = consumo del mes pico / días hábiles del mes. "
                "SS = (d pico − d prom) × LT. Punto de pedido = d prom × LT + SS. Lote = consumo de T días en el pico, "
                "redondeado hacia arriba a la unidad de compra. Stock máximo = SS + lote. Las posiciones se suman por "
                "almacén y se redondean al final (los ítems chicos comparten posición). Los servicios no se almacenan.")
        cab = ["Código", "Ítem", "UM", "Almacén", "Consumo del año de diseño", "MANUALES", "RODANTES", "RECARGAS",
               "REVENDIDOS"] + MESES + ["Mes pico (UM)", "d prom (UM/día)", "d pico (UM/día)", "Lead time (días háb.)",
                                       "Stock de seguridad (UM)", "Punto de pedido (UM)", "T (días háb.)",
                                       "Contenido por UC", "Lote (UM)", "Lote (UC)", "Stock máximo (UM)",
                                       "Stock máximo (UC)", "Cobertura del stock máx. (días)", "Entregas por año",
                                       "UC por posición", "Posiciones (fracción)", "m² por posición", "m²"]
        _cab(ws, 3, cab, [11, 46, 6, 26, 12, 11, 11, 11, 11] + [9] * 12 + [11] * 18)
        cn = q("CONSOLIDADO_INSUMOS")
        fin = self.cons_fin
        r = 4
        for it in ITEMS:
            if it["cod"] not in self.cons or it["clase"] == SERV:
                continue
            ws.cell(r, 1, it["cod"])
            ws.cell(r, 2, f"={self.C(f'$A{r}', 2)}")
            ws.cell(r, 3, f"={self.C(f'$A{r}', 3)}")
            ws.cell(r, 4, f"={self.C(f'$A{r}', 6)}")
            ws.cell(r, 5, f"={cn}!T{self.cons[it['cod']]}")
            for k, lin in enumerate(LINEAS):
                ws.cell(r, 6 + k, f'=SUMIFS({cn}!$T$4:$T${fin},{cn}!$B$4:$B${fin},$A{r},{cn}!$H$4:$H${fin},"{lin}")')
            for m in range(12):
                ws.cell(r, 10 + m, "=" + "+".join(f"{L(6 + k)}{r}*ESTACIONALIDAD!${L(2 + m)}${self.est[lin]}"
                                                  for k, lin in enumerate(LINEAS)))
            ws.cell(r, 22, f"=MAX(J{r}:U{r})")
            ws.cell(r, 23, f'=E{r}/{self.P("DH_AÑO")}')
            ws.cell(r, 24, f'=V{r}/{self.P("DH_MES")}')
            ws.cell(r, 25, f"={self.C(f'$A{r}', 12)}")
            ws.cell(r, 26, f"=(X{r}-W{r})*Y{r}")
            ws.cell(r, 27, f"=W{r}*Y{r}+Z{r}")
            ws.cell(r, 28, f"={self.C(f'$A{r}', 15)}")
            ws.cell(r, 29, f"={self.C(f'$A{r}', 11)}")
            ws.cell(r, 30, f"=MAX(AC{r},CEILING(X{r}*AB{r},AC{r}))")
            ws.cell(r, 31, f"=AD{r}/AC{r}")
            ws.cell(r, 32, f"=Z{r}+AD{r}")
            ws.cell(r, 33, f"=ROUNDUP(AF{r}/AC{r},0)")
            ws.cell(r, 34, f"=IF(W{r}>0,AF{r}/W{r},0)")
            ws.cell(r, 35, f"=IF(AD{r}>0,E{r}/AD{r},0)")
            ws.cell(r, 36, f"={self.C(f'$A{r}', 16)}")
            ws.cell(r, 37, f"=IF(AJ{r}>0,AG{r}/AJ{r},0)")
            ws.cell(r, 38, f"={self.C(f'$A{r}', 17)}")
            ws.cell(r, 39, f"=AK{r}*AL{r}")
            for j in range(5, 40):
                ws.cell(r, j).number_format = "#,##0.0" if j not in (25, 28, 31, 33, 35, 36) else "#,##0"
            ws.cell(r, 37).number_format = "0.00"
            for j in (23, 24, 26):
                ws.cell(r, j).number_format = "#,##0.000"
            _fila(ws, r, 39)
            r += 1
        fin_p = r - 1
        r += 1
        ws.cell(r, 2, "VERIFICACIÓN DE LOS ALMACENES (año de diseño)").font = _f(True)
        r += 1
        _cab(ws, r, ["", "Almacén", "", "", "Posiciones requeridas", "Capacidad (posiciones)", "Resultado",
                     "m² requeridos", "Capacidad según"], c0=1)
        zonas = []
        for it in ITEMS:
            if it["zona"] not in zonas and it["zona"] != Z_SERV:
                zonas.append(it["zona"])
        for z in zonas:
            r += 1
            ws.cell(r, 2, z)
            ws.cell(r, 5, f'=ROUNDUP(SUMIF($D$4:$D${fin_p},B{r},$AK$4:$AK${fin_p}),0)').number_format = "#,##0"
            ws.cell(r, 8, f'=SUMIF($D$4:$D${fin_p},B{r},$AM$4:$AM${fin_p})').number_format = "#,##0.0"
            if z in CAPACIDAD:
                ws.cell(r, 6, CAPACIDAD[z][0])
                ws.cell(r, 7, f'=IF(E{r}<=F{r},"Alcanza","No alcanza: ampliar")')
                ws.cell(r, 9, CAPACIDAD[z][1])
            else:
                ws.cell(r, 7, "Sin capacidad fijada en el proceso: el layout debe prever los m²")
            _fila(ws, r, 9)
        ws.freeze_panes = "C4"
        ws.auto_filter.ref = f"A3:AM{fin_p}"
        _imprimir(ws, "3:3", 39)

    # -------- armado
    def armar(self, ruta):
        self.parametros()
        self.ix = self.copia("Indexado Dim Técnico", "PROY_INDEXADO")
        self.rs = self.copia("Reservas y Sustitutos", "PROY_RESERVAS")
        self.demanda()
        self.estacionalidad()
        self.bom_coef()
        self.fab_compra()
        self.proceso()
        self.compras()
        self.coeficientes()
        hojas = []
        for lin in LINEAS:
            for tipo in (D, IN):
                hojas.append((self.insumos(lin, tipo), lin))
        self.consolidado(hojas)
        self.politica()
        for ws in self.wb.worksheets:
            ws.sheet_view.zoomScale = 90
        self.wb.calculation.fullCalcOnLoad = True
        self.wb.save(ruta)


def excel(proyecciones, ruta, bom=None):
    bom = bom or os.path.join(os.path.dirname(os.path.dirname(ruta)), "bom", "FLAMA_BOM.xlsx")
    Libro(proyecciones, bom).armar(ruta)
    recalcular(ruta)
    return ruta
