"""Análisis justificativo de las medidas de diseño FLAMA (las que no salen de un documento): para cada una, la
verificación técnica (presión, estática, resistencia de materiales), la norma que la encuadra (sólo se citan las
cláusulas) y la razón económica, con la conclusión y, si corresponde, la condición que pasa a la orden de compra.

Uso: python analisis.py  ->  analisis.json (lo lee node/word2.js, sección 8)
Las cuentas usan las medidas de los modelos y los datos de la hoja de especificaciones del catálogo del proyecto.
"""
import json
import math
import os
import sys

sys.path.insert(0, "/home/user/planos_flama-")
from flama.catalogo import MODELOS  # noqa: E402

SP = "/tmp/claude-0/-home-user-TP-optimizacion/15292aaf-e550-5dee-a83e-77fd9177a6ef/scratchpad"
M = {m.codigo: m for m in MODELOS}


def f(s):
    return float(str(s).replace(",", ".").split("/")[0])


def n(v, d=1):
    s = f"{v:.{d}f}".replace(".", ",")
    return s[:-2] if d and s.endswith(",0") else s


def ps(c):
    return f(M[c].spec["Presión de servicio (MPa)"])


def pe(c):
    return f(M[c].spec["Presión de ensayo (MPa)"])


# ------------------------------------------------------------------ datos de partida
SY_304, SU_304, SY_304_2B = 205.0, 515.0, 240.0      # ASTM A240 tipo 304: fluencia y rotura mínimas; 2B típica ≥ 240
SF_LAC = 265.0                                       # LAC IRAM-IAS U 500-04 exigida en la compra (validación)
SY_1010, SY_1045 = 180.0, 530.0                      # SAE 1010 laminado; SAE 1045 trefilado
RHO_INOX, RHO_AC = 7.9e-6, 7.85e-6                   # kg/mm³

# recipientes inoxidables (agua, AFFF 10 l, sales K)
inox = M["FL_MAT_AGUA_10l"].geo
D_i, t_i = 2 * inox["R"], inox["t"]
s_e_i = pe("FL_MAT_AGUA_10l") * D_i / (2 * t_i)
s_s_i = ps("FL_MAT_AGUA_10l") * D_i / (2 * t_i)
p_rot_i = 2 * t_i * SU_304 / D_i
t_min205 = pe("FL_MAT_AGUA_10l") * D_i / (2 * SY_304)
area_i = math.pi * D_i * inox["hc"] + 2 * 1.15 * math.pi * D_i ** 2 / 4
kg08, kg10 = area_i * 0.8 * RHO_INOX, area_i * 1.0 * RHO_INOX

# casquetes Ø390 (70 y 100 kg)
g100 = M["FL_MAT_ABC_100kg"].geo
R390, t390, h390 = g100["R"], g100["t"], g100["hd"]
K = (2 + (R390 / h390) ** 2) / 6
t_req = lambda P, S, k: P * 2 * R390 * k / (2 * S - 0.2 * P)            # noqa: E731 (cabezal elipsoidal)
t_e_656, t_e_21 = t_req(pe("FL_MAT_ABC_100kg"), 0.9 * SF_LAC, K), t_req(pe("FL_MAT_ABC_100kg"), 0.9 * SF_LAC, 1.0)
s_cil_e = pe("FL_MAT_ABC_100kg") * 2 * R390 / (2 * t390)

# cuello M30 de manuales y muesca de altura
dn, dmaj = 37.0, 30.0
pared = (dn - dmaj) / 2
s_muesca = pe("FL_MAT_ABC_5kg") * dmaj / (2 * (pared - 1.0))

# válvulas: empuje sobre el asiento a la presión de servicio
asiento = {"F510": 9.0, "F192": 14.0, "G763": 20.0}
F_as = {k: 1.4 * math.pi / 4 * d * d for k, d in asiento.items()}
perno = {"F510": 3.6, "F192": 4.0, "G763": 8.0}
tau_perno = {k: 3 * (F_as[k] * 1.3) / (2 * math.pi / 4 * perno[k] ** 2) for k in perno}   # ×1,3 resorte, ×3 palanca

# pasador de seguridad Ø3,2 inox: capacidad al corte doble
cap_pas = 2 * math.pi / 4 * 3.2 ** 2 * 0.6 * SU_304 / 1000

# palanca de carros (G763): fuerza de mano y flexión
F_vas = F_as["G763"] * 1.25
F_mano = F_vas * 25.0 / 146.2
s_pal = F_mano * 146.2 / (10 * 16 ** 2 / 6)

# carros: rueda, eje, buje, disco
carros = []
for c, dw, bw, de in (("FL_MAT_ABC_25kg", 300, 50, 19.05), ("FL_MAT_ABC_50kg", 350, 60, 25.4),
                      ("FL_MAT_ABC_70kg", 350, 60, 25.4), ("FL_MAT_ABC_100kg", 400, 60, 25.4)):
    W = f(M[c].spec["Peso cargado (kg)"]) * 9.81
    Fw = W / 2
    a = 4 + bw / 2
    s_eje = 32 * Fw * a / (math.pi * de ** 3)
    carros.append(dict(c=c, kg=f(M[c].spec["Peso cargado (kg)"]), dw=dw, bw=bw, de=de, Fw=Fw, a=a, s_eje=s_eje,
                       p_buje=Fw / (de * bw), tau_disco=Fw / (math.pi * (de + 34) * 2.5), macizo=0.14 * dw))
c100 = carros[-1]

# tobera campana y lanza
semi = math.degrees(math.atan((34 - 16) / 200))

# CO2: espesor mínimo de cilindro sin costura (criterio ISO 9809-1, F = 0,77) con acero Re 350 MPa
def a_iso(D, Re, Ph=250.0, F=0.77):
    return D / 2 * (1 - math.sqrt((10 * F * Re - math.sqrt(3) * Ph) / (10 * F * Re)))


co2 = [(114.0, 5.4, a_iso(114.0, 350), a_iso(114.0, 450)), (140.0, 6.0, a_iso(140.0, 350), a_iso(140.0, 450))]
try:
    from CoolProp.CoolProp import PropsSI
    p_co2 = {T: PropsSI("P", "D", 680.0, "T", T + 273.15, "CO2") / 1e6 for T in (20, 50, 60, 65)}
    p_co2_75 = PropsSI("P", "D", 750.0, "T", 60 + 273.15, "CO2") / 1e6
except ImportError:                                   # valores de la ecuación de estado (Span-Wagner)
    p_co2 = {20: 5.73, 50: 14.26, 60: 17.66, 65: 19.38}
    p_co2_75 = 21.82


def it(id_, titulo, modelos, valor, tecnica, norma, economia, conclusion, condicion=None):
    return dict(id=id_, titulo=titulo, modelos=modelos, valor=valor, tecnica=tecnica, norma=norma,
                economia=economia, conclusion=conclusion, condicion=condicion)


G = []
# ================================================================== A. recipiente a presión
G.append(("A. Recipiente a presión", [
    it("P1", "Altura de los casquetes Ø390 (cúpula y fondo)", "ABC 70 y 100 kg", f"{n(h390)} mm (0,656 R)",
       f"El casquete es una tapa elipsoidal: la relación D/2h = {n(R390 / h390, 2)} da un factor de forma "
       f"K = [2 + (D/2h)²] / 6 = {n(K, 2)}, menor que el del cabezal 2:1 (K = 1). Con la fórmula de cabezales "
       f"elipsoidales (t = P·D·K / (2S − 0,2P)), a la presión de ensayo de {n(pe('FL_MAT_ABC_100kg'))} MPa y una "
       f"tensión admisible de 0,9·σf = {n(0.9 * SF_LAC, 0)} MPa hace falta {n(t_e_656, 2)} mm; un 2:1 pediría "
       f"{n(t_e_21, 2)} mm. Con los {n(t390, 2)} mm adoptados el margen es {n(t390 / t_e_656, 1)}. La virola del mismo "
       f"espesor trabaja a {n(s_cil_e, 0)} MPa en el ensayo: el casquete más profundo baja la tensión en el radio de "
       "transición, que es donde fallan las tapas.",
       "IRAM 3550 4.1.3 (espesor del recipiente: el 4,75 supera el mínimo para Ø > 320) y 6.1.1 (prueba hidráulica "
       "después de soldar). La fórmula de cabezales elipsoidales es la de ASME VIII Div. 1 UG-32, usada como "
       "criterio de cálculo.",
       "Es la misma relación que el cabezal Ø320 del plano Fadesa de 50 kg (105 / 160) y sale de una sola matriz "
       "Ø390 en el embutidor (Gockel) para el 70 y el 100 kg: una herramienta para dos modelos, sin costo de "
       "matriz nueva. Un casquete más bajo no ahorra chapa (el disco cambia menos de 3 %) y sube la tensión.",
       "Justificado: 127,9 mm, con margen 2 sobre la tensión de ensayo.",
       "Casquete Ø390 × 4,75 de la matriz del embutidor; certificado de la chapa con σf ≥ 265 MPa."),
    it("D32", "Ø del disco de cúpula y fondo (referencia)", "ABC 25, 50, 70 y 100 kg",
       "358 / 411 / 507 mm (cúpula); 362 / 424 / 518 mm (fondo)",
       "En el embutido profundo la superficie se conserva (el espesor cambia poco): el disco tiene la misma área "
       "que la superficie media del casquete, Ø = 2·√(A/π), más 3 % de pestaña que se recorta después del embutido.",
       "Sin requisito propio: el casquete terminado cumple IRAM 3550 4.1.3 (espesor) y la prueba hidráulica de 6.1.1.",
       "El casquete se compra embutido: el disco es dato del embutidor y sirve para controlar su presupuesto "
       "(kg de chapa por pieza × USD 1,10/kg de la LAC cotizada) y el aprovechamiento de la hoja.",
       "Justificado como referencia de costo: no es medida de fabricación de FLAMA."),
    it("D10", "Espesor de chapa inoxidable", "AFFF 10 l, Agua 10 l, Sales K 6 l (revendidos)",
       f"{n(t_i)} mm, AISI 304",
       f"Virola Ø{n(D_i, 0)}: a la presión de servicio ({n(ps('FL_MAT_AGUA_10l'))} MPa) la tensión circunferencial "
       f"σ = p·D/2t es {n(s_s_i, 0)} MPa (margen {n(SY_304 / s_s_i, 1)} sobre la fluencia mínima). En la prueba "
       f"hidráulica ({n(pe('FL_MAT_AGUA_10l'))} MPa) llega a {n(s_e_i, 0)} MPa: por debajo de la fluencia típica de la "
       f"chapa 2B (≥ {n(SY_304_2B, 0)} MPa) pero por encima del mínimo garantizado por ASTM A240 ({n(SY_304, 0)} MPa), "
       f"que pediría {n(t_min205, 2)} mm. La rotura estimada (2t·σr/D) es {n(p_rot_i, 1)} MPa: {n(p_rot_i / ps('FL_MAT_AGUA_10l'), 1)} "
       "veces la de servicio.",
       "IRAM 3525 3.2.1 b) (inoxidable de espesor mínimo 0,63 mm: se cumple) y 3.2.2 (costuras); IRAM 3517-2 9.4.21.",
       f"Son equipos revendidos: el espesor es el del fabricante. Frente a 1,0 mm, el 0,8 usa {n(kg08, 2)} kg de inox "
       f"por recipiente en lugar de {n(kg10, 2)} kg (−20 %), que es lo que hace competitivo el precio de mercado.",
       "Justificado por norma y por servicio; en la prueba hidráulica depende de la calidad real de la chapa.",
       "Comprar con certificado de prueba hidráulica del fabricante y chapa 304 con σ0,2 ≥ 240 MPa."),
    it("D11", "Cuello de los recipientes inoxidables", "AFFF 10 l, Agua 10 l, Sales K 6 l",
       "M30 × 1,5; Ø37 × 14; asiento Ø35",
       f"Pared del cuello (37 − 30)/2 = {n(pared)} mm; a {n(pe('FL_MAT_AGUA_10l'))} MPa la tensión es menor a 10 MPa. "
       "El asiento Ø35 apoya la junta tórica de la válvula y el filete M30 × 1,5 con 14 mm de largo deja más de 8 "
       "hilos enganchados: la tracción de la presión sobre la válvula (≈ 1,4 kN en el ensayo) da una tensión de corte "
       "en la rosca menor a 5 MPa.",
       "IRAM 3525 (recipiente y válvula); rosca métrica fina de la serie de válvulas de la línea manual.",
       "Es la misma rosca de las válvulas de 2,5 a 10 kg: el mismo stock de válvulas, juntas y manómetros sirve para "
       "los revendidos en la recarga y el service.",
       "Justificado: dimensión de mercado compatible con la familia M30."),
    it("D01", "Muesca de altura en el cuello", "10 modelos manuales", "2 × 1 × 2 mm (ancho × prof. × alto)",
       f"La pared del cuello es de {n(pared)} mm; con 1 mm de muesca quedan {n(pared - 1)} mm. En el ensayo "
       f"({n(pe('FL_MAT_ABC_5kg'))} MPa) la tensión circunferencial allí es {n(s_muesca, 0)} MPa y, con un factor de "
       f"concentración de 3 por el fondo de la muesca, {n(3 * s_muesca, 0)} MPa, muy por debajo de la fluencia del "
       "SAE 1020 (≈ 350 MPa). 1 mm de profundidad sobrevive a la pintura en polvo (60-80 µm, menos del 10 % de la "
       "muesca): sigue viéndose y sintiéndose al tacto como referencia de altura al armar.",
       "IRAM 3523 4.1.2 (cuello) y 5.1 (marcado): la muesca no toca la rosca ni el asiento.",
       "Se marca en la misma prensa Pannier de la preparación del cuello, sin herramienta ni operación aparte.",
       "Justificado."),
    it("D29", "Espesor del cilindro sin costura de CO₂", "CO₂ 2 kg y 5 kg (revendidos)",
       "5,4 mm (Ø114) y 6,0 mm (Ø140)",
       f"Con el criterio de cilindros sin costura de ISO 9809-1 (presión de prueba 25 MPa, F = 0,77) el espesor "
       f"mínimo es {n(co2[0][2], 2)} / {n(co2[1][2], 2)} mm para un acero de Re = 350 MPa y {n(co2[0][3], 2)} / "
       f"{n(co2[1][3], 2)} mm para Re = 450 MPa. Los espesores dibujados cubren el acero más débil del mercado.",
       "IRAM 3509 (extintores de CO₂); prueba del cilindro a 25 MPa como en la hoja de especificaciones.",
       "Son revendidos: el cilindro es del fabricante y el espesor real puede ser menor con aceros templados; el "
       "plano usa el caso conservador para el peso del conjunto.",
       "Justificado como envolvente conservadora.",
       "Cilindro con estampa de prueba a 25 MPa y fecha vigente."),
    it("D30", "Disco de seguridad del CO₂", "CO₂ 2 kg y 5 kg", "Rotura 18 a 21 MPa; tapón 14 × 9",
       f"Con la relación de llenado máxima para elementos contra incendio (0,68 kg/L), la presión del CO₂ es "
       f"{n(p_co2[20])} MPa a 20 °C, {n(p_co2[50])} MPa a 50 °C (tope del rango de uso), {n(p_co2[60])} MPa a 60 °C y "
       f"{n(p_co2[65])} MPa a 65 °C (ecuación de estado de Span-Wagner). Los cilindros quedan en 0,676 kg/L (2 kg) y "
       "0,631 kg/L (5 kg). El disco no abre en todo el rango de uso y abre antes de que el cilindro llegue a la "
       f"presión de prueba de 25 MPa. A 0,75 kg/L (la relación de almacenamiento y transporte, hasta 45 °C) la "
       f"presión a 60 °C sería {n(p_co2_75)} MPa y el disco abriría: el disco también limita el sobrellenado.",
       "IRAM 2533 7.9 tabla 1 (relación de llenado 0,68 kg/L hasta 65 °C en elementos contra incendio); IRAM 3509 "
       "(dispositivo de seguridad del cilindro).",
       "Disco comercial de válvula de CO₂; se repone en la recarga.",
       "Justificado.",
       "En la recarga, relación de llenado ≤ 0,68 kg/L (IRAM 2533 7.9): 2 kg en ≥ 2,94 L y 5 kg en ≥ 7,35 L."),
    it("D31", "Pie de apoyo del CO₂", "CO₂ 2 kg y 5 kg", "Ø114 × 31,4 y Ø140 × 38,5 mm (alto 0,55 R)",
       "El fondo del cilindro sin costura es convexo: el pie da una base plana del mismo Ø del cilindro. Con el "
       "centro de gravedad cerca del 45 % de la altura (520 y 790 mm), el ángulo de vuelco es atan(R / zG) ≈ 14° "
       "en el 2 kg y 11° en el 5 kg: el mismo que tendría el cilindro parado sobre un fondo plano.",
       "IRAM 3509 (extintor de CO₂): el pie es un accesorio, no forma parte del cilindro a presión.",
       "Pie de plástico inyectado comercial, de bajo costo.",
       "Justificado."),
    it("CD", "Clase D 9 l: recipiente del 10 kg", "Clase D 9 l (revendido)", "Recipiente Ø181,5 × 562,5 mm, 12,5 l",
       "El catálogo de referencia sólo tiene clase D de 5 y 10 kg. El polvo D (base cloruro de sodio) tiene una "
       "densidad aparente cercana a 1,1 kg/l: 9 l son ≈ 10 kg, la carga del modelo de 10 kg, y por eso coincide el "
       "peso cargado de 16,5 kg. En el recipiente de 12,5 l la carga ocupa el 72 % y deja 3,5 l de gas impulsor, "
       "más cámara que la del ABC 10 kg, que llena ≈ 85 %: la descarga se completa con la misma presión de 1,4 MPa.",
       "IRAM 3523 (recipiente, presión de servicio 1,4 MPa y prueba 3,5 MPa, los mismos del 10 kg).",
       "Mismo recipiente, válvula y soporte que el ABC 10 kg: no suma códigos de compra ni de repuesto.",
       "Justificado."),
]))
# ================================================================== B. válvula
G.append(("B. Válvula (se compra armada)", [
    it("D02-D09-D22", "Cuerpo de válvula: fondo y salida; vástago, resorte y junta de la válvula de carro",
       "manuales y rodantes",
       "Fondo 24 / 28 / 40 mm; salida Ø10,8 × 7,3 y Ø26 × 20; vástago Ø10 × 36, asiento Ø20; resorte Ø27 × 35; "
       "junta 81 × 4,7",
       f"El vástago cierra contra la presión: el empuje sobre el asiento a 1,4 MPa es {n(F_as['F510'], 0)} N (Ø9), "
       f"{n(F_as['F192'], 0)} N (Ø14) y {n(F_as['G763'], 0)} N (Ø20). El resorte sólo asegura el cierre sin presión. "
       "La salida no estrangula el caudal: Ø26 en la válvula de carro iguala el paso de la manguera.",
       "IRAM 3523 3.3 y IRAM 3550 3.4 (válvula): la cumple el fabricante de la válvula.",
       "La válvula se compra armada (lista HZ: $4.200 la de 1 kg, $6.800 la M30, $7.500 la de carro). Mecanizar un "
       "cuerpo forjado propio exige matrices de forja y CNC que no se amortizan con el volumen de FLAMA.",
       "Justificado: las medidas reproducen la válvula comercial que se compra.",
       "Válvula HZ con certificado del fabricante."),
    it("D03", "Manómetro: rango y sector verde", "15 modelos", "0-2 MPa / verde 0,8 · 0-3,5 MPa / verde 1,4",
       "La escala llega a 2,5 veces la presión de servicio: en carga la aguja queda al 40 % del recorrido, dentro del "
       "tercio medio donde un manómetro Bourdon es más preciso y su tubo no se fatiga, y la escala cubre el aumento de "
       "presión por temperatura sin llegar al tope.",
       "IRAM 3523 4.5 (manómetro) e IRAM 3533 (sello del manómetro).",
       "Dos rangos cubren los 15 modelos: dos códigos de compra en lugar de uno por modelo.",
       "Justificado.",
       "Manómetro con sello IRAM 3533 y la rosca de la válvula."),
    it("D04-D24", "Eje de la palanca", "manuales y rodantes", "Ø3,6 × 29 · Ø4 × 33 · Ø8 × 47 mm",
       f"El eje trabaja al corte doble. Con el empuje del asiento más 30 % de resorte y la relación de palanca de 3, "
       f"la tensión es {n(tau_perno['F510'], 0)} MPa (Ø3,6), {n(tau_perno['F192'], 0)} MPa (Ø4) y "
       f"{n(tau_perno['G763'], 0)} MPa (Ø8), frente a ≈ 105 MPa de fluencia al corte de un acero SAE 1010: margen "
       "mayor a 3 en el caso más cargado.",
       "IRAM 3523 3.3 / IRAM 3550 3.4.",
       "Viene con la válvula armada; suelto es un perno o tornillo comercial.",
       "Justificado."),
    it("D05", "Pasador de seguridad", "los 17", "Alambre inox Ø3,2 × 40,5 / 44,5 / 53 mm",
       f"Al corte doble aguanta {n(cap_pas, 1)} kN: ninguna fuerza de mano sobre la palanca lo vence, así que el "
       "extintor no se dispara por accidente. Se saca tirando de la anilla y rompiendo el precinto, que cede con "
       "pocas decenas de newton. El inoxidable no se oxida dentro de la horquilla: no se traba con los años.",
       "IRAM 3550 3.4.2 (traba) e IRAM 3517-2 9.4.13 (precinto).",
       "Alambre comercial cortado a largo; el largo es el ancho de la horquilla más la anilla.",
       "Justificado."),
    it("D06", "Ancho de las manijas de accionamiento y de transporte", "13 modelos", "27 / 31 / 35 mm (U de chapa)",
       "Cada U va a horcajadas del cuerpo de la válvula (la de accionamiento) o de la palanca (la de transporte): "
       "el ancho es el del cuerpo más el juego y los dos espesores. La palma reparte la fuerza en todo el ancho.",
       "IRAM 3523 3.3.",
       "Parte de la válvula armada.",
       "Justificado: compatibilidad dimensional con la válvula comercial."),
    it("D23", "Palanca de accionamiento de carros", "4 rodantes", "146 × 16 × 10 mm (120 en el 25 kg), empuñadura Ø22 × 44",
       f"Para abrir hay que vencer el empuje del asiento más el resorte (≈ {n(F_vas, 0)} N) con un brazo de 25 mm: "
       f"en la empuñadura hacen falta ≈ {n(F_mano, 0)} N, una fuerza cómoda de mano. A flexión, la sección 16 × 10 "
       f"trabaja a {n(s_pal, 0)} MPa contra 180 MPa del SAE 1010: margen {n(SY_1010 / s_pal, 1)}.",
       "IRAM 3550 3.4.",
       "Planchuela comercial 10 × 16 cortada y pintada.",
       "Justificado."),
    it("D08", "Precinto de fábrica", "los 17", "Ø5 × 10 mm", "Cuerpo de polipropileno con la identificación del "
       "fabricante en relieve: el tamaño mínimo que hace legible la marca y se rompe sin herramientas.",
       "IRAM 3517-2 9.4.13 (precinto con identificación del fabricante).",
       "Insumo comercial de costo despreciable.",
       "Justificado."),
]))
# ================================================================== C. descarga
G.append(("C. Descarga", [
    it("D13", "Racor de manguera", "10 modelos", "Ø18 × 12 y Ø24 × 16 mm",
       f"El racor engarzado tiene que retener el empuje de la presión sobre la sección interior de la manguera: "
       f"a 3,5 MPa sobre Ø12 son {n(3.5 * math.pi / 4 * 144, 0)} N. 12-16 mm de casquillo engarzado es el largo "
       "comercial para esas mangueras.",
       "IRAM 3523 4.2 (manga con prueba hidráulica a 2 veces la de servicio).",
       "Racor comercial con la manguera armada (se compra con su ensayo).",
       "Justificado.",
       "Manguera armada con certificado de prueba hidráulica."),
    it("D14-D26", "Diámetro exterior de la manguera", "manuales y rodantes", "14 / 17,4 / 23,5 mm",
       "El diámetro interior iguala el paso de salida de la válvula para no estrangular la descarga. En los carros, la "
       "manga de 23,5 permite curvas de radio ≥ 100 mm (unas 4 veces el diámetro), que es lo que usa el lazo de los "
       "flejes sin aplastarla.",
       "IRAM 3523 4.2 (largo y prueba de la manga); IRAM 3550 (manga de los rodantes; largos de la hoja de especificaciones).",
       "Medidas comerciales de manguera de caucho trenzada.",
       "Justificado."),
    it("D25", "Caño de pesca", "7 modelos", "Ø10 y Ø24 mm",
       "Su sección iguala la entrada de la válvula; llega a 25 mm del fondo para vaciar el recipiente sin aspirar "
       "depósitos.",
       "IRAM 3523 3.3 (válvula y tubo de pesca).",
       "Tubo comercial que viene con la válvula (lista HZ: válvula con tubo).",
       "Justificado."),
    it("D12", "Filtro del tubo de pesca", "AFFF 10 l, Agua 10 l, Sales K 6 l", "24 × 24 × 25 mm",
       f"Con 40 % de área abierta la canasta Ø24 × 25 deja pasar {n(0.4 * math.pi * 24 * 25, 0)} mm², más de 10 "
       "veces la sección del tubo: retiene partículas sin pérdida de carga apreciable.",
       "IRAM 3525 (agua y espuma).",
       "Accesorio estándar del recipiente revendido.",
       "Justificado."),
    it("D07", "Tobera del 1 kg", "ABC 1 kg", "Boquilla Ø12 / Ø9 × 10 mm",
       "El orificio de Ø9 fija el caudal: descarga 1 kg en el tiempo de la hoja (8-9 s), con el alcance de 2-3 m.",
       "IRAM 3523 (tiempo de descarga y alcance).",
       "Tobera directa sobre la válvula, sin manguera: la opción más barata en el 1 kg.",
       "Justificado."),
    it("D15", "Toberas y lanzas de los revendidos", "6 modelos", "Ø y largo por tipo (chorro pleno, espuma, clase K)",
       "Cada agente tiene su dispositivo: chorro pleno para agua, lanza que aspira aire para la espuma, lanza "
       "aplicadora para clase K. El largo se limita a la altura del equipo para que quede dentro de su silueta.",
       "IRAM 3525, IRAM 3697 / 3694 (clase K), IRAM 3509 (CO₂).",
       "Accesorio del equipo revendido.",
       "Justificado."),
    it("D16", "Sunchos portatobera y soporte de difusor", "5 modelos", "Fleje 18 × 1,5 mm; Ø interior = cuerpo + 0,6",
       "El suncho abraza el cuerpo por encima de las etiquetas (0,3 mm de cada lado). Sostiene una tobera de "
       "menos de 0,3 kg: la tensión en el fleje es despreciable; el ancho de 18 da superficie de apoyo sin marcar la "
       "pintura.",
       "IRAM 3523 (soporte de la manga).",
       "Fleje comercial de bobina cortado y curvado.",
       "Justificado."),
    it("D27", "Válvula esférica de la lanza de carros", "5 rodantes", "Cuerpo Ø40 × 56, hexágonos 46, palanca 105",
       "Paso total: no frena la descarga. Cerrada, la palanca queda atravesada al caño, así que se ve el estado de "
       "un vistazo. Con la palanca de 105 mm alcanza una fuerza de mano baja.",
       "IRAM 3550 3.4 (cierre de la descarga).",
       "Válvula esférica de bronce comercial: se cambia sin desarmar la manga.",
       "Justificado."),
    it("D33", "Tobera campana de carros", "4 rodantes", "Ø32 entrada / Ø68 boca × 200 mm",
       f"La sección crece {n((68 / 32) ** 2, 1)} veces: el polvo sale más lento y en una nube ancha, que es lo que "
       f"sirve para fuegos A y B. El semiángulo del cono es {n(semi, 1)}° (cono de {n(2 * semi, 0)}° total): un cono de "
       "ángulo chico frena el chorro sin que se despegue de la pared, y el polvo sale parejo en toda la boca.",
       "IRAM 3550 (alcance y tiempo de descarga de la hoja).",
       "Tobera de polipropileno inyectado comercial.",
       "Justificado."),
    it("D28", "Lanza espumígena", "AFFF 50 l", "Ø40 × 380 mm, boca Ø56",
       "La lanza aspira aire por 4 tomas: el largo de 9,5 diámetros asegura el mezclado antes de la boca.",
       "IRAM 3525 / 3541 (espuma).",
       "Accesorio del equipo revendido.",
       "Justificado."),
]))
# ================================================================== D. tren de rodaje
filas_c = "; ".join(f"{c['c'][7:].replace('_', ' ')}: {n(c['Fw'], 0)} N" for c in carros)
G.append(("D. Tren de rodaje", [
    it("D17", "Neumático macizo y llanta", "4 rodantes y AFFF 50 l", "Ø interior del macizo = 0,72 × Ø rueda",
       f"El caucho queda con un alto de 0,14 D ({n(carros[0]['macizo'], 0)}-{n(c100['macizo'], 0)} mm), que amortigua "
       f"los golpes sin aumentar la resistencia a la rodadura. Con el carro inclinado sobre las ruedas, cada rueda "
       f"lleva la mitad del peso cargado de la hoja ({filas_c}). La rueda Ø350 × 60 cotizada carga 150 kg y una Ø400 "
       f"maciza de mercado 136 kg: en el 100 kg queda margen {n(136 * 9.81 / c100['Fw'], 1)} en estático.",
       "IRAM 3550 3.12 y tabla III (Ø ≥ 300, banda ≥ 50, trocha ≥ 400).",
       "Rueda de chapa y goma con buje liso: más barata que una con rodamiento y sin mantenimiento.",
       "Justificado.",
       "Capacidad de carga por rueda ≥ 90 kg en el 100 kg, con ficha del proveedor."),
    it("D18", "Espesor del aro y del disco de la llanta", "rodantes", "2 / 2,5 mm",
       f"El disco transmite la carga de la rueda al cubo por corte: en el 100 kg son {n(c100['tau_disco'], 1)} MPa "
       "alrededor del cubo, muy por debajo de la resistencia de la chapa. Los espesores reproducen la masa de las "
       "ruedas de los planos Fadesa.",
       "IRAM 3550 3.12.",
       "Chapa estampada estándar del fabricante de ruedas.",
       "Justificado."),
    it("D19", "Cubo y buje de la rueda", "rodantes", "Ø ext = eje + 34; buje = eje + 1 mm",
       f"El buje liso apoya sobre el eje: la presión es F / (d·b) = {n(c100['p_buje'], 2)} MPa en el 100 kg, que a "
       "velocidad de paso es muy baja para un buje acero-acero engrasado. El juego de 1 mm deja girar la rueda con "
       "pintura y polvo.",
       "IRAM 3550 3.12.",
       "Buje liso en vez de rodamiento: menor costo y sin piezas que se oxiden.",
       "Justificado."),
    it("D20", "Arandelas de tope", "rodantes", "40 × (eje + 1) × 4 mm (4 por carro)",
       "Toman el empuje lateral de la rueda al doblar (≈ 30 % de su carga). El anillo de apoyo tiene unos 700 mm²: la "
       "presión es menor a 0,5 MPa.",
       "IRAM 3550 3.12.",
       "Se puede comprar la arandela plana normalizada ISO 7089 equivalente: M20 (Ø21 × 37 × 3) para el eje de 3/4\" y "
       "M27 (Ø28 × 50 × 4) para el de 1\". Es stock de bulonería, más barata que una arandela a medida.",
       "Justificado.",
       "Comprar ISO 7089 M20 / M27."),
    it("D21", "Pasadores del eje", "rodantes", "Pasador partido Ø4 × 40 mm (2 por carro)",
       "Sólo retienen la arandela exterior: el empuje lateral (< 300 N) al corte doble del pasador da menos de "
       "15 MPa. El agujero de Ø4,2 en el eje está fuera de la zona de flexión, en la punta.",
       "IRAM 3550 3.12; pasador partido DIN 94 / ISO 1234.",
       "Pasador normalizado de bulonería.",
       "Justificado."),
    it("EJE", "Eje y caño del eje (control de resistencia)", "4 rodantes",
       "Barra trefilada SAE 1045 Ø19,05 / Ø25,4; voladizo = arandela + media banda",
       f"La rueda carga el eje en voladizo desde la punta del caño, con un brazo de {n(c100['a'], 0)} mm. En el 100 kg "
       f"la tensión de flexión es {n(c100['s_eje'], 1)} MPa en estático y {n(3 * c100['s_eje'], 0)} MPa con un "
       f"factor de impacto de 3 (cordón de vereda), frente a ≈ {n(SY_1045, 0)} MPa de fluencia del 1045 trefilado.",
       "IRAM 3550 3.12.",
       "La barra trefilada se compra a medida y el caño del eje la protege: no hace falta mecanizarla.",
       "Justificado."),
]))
# ------------------------------------------------------------------ marcado estampado en la cúpula (proceso «numerado
# de cúpula»): tensión de membrana de la cúpula en la franja (elipse de semiejes R y hd − c0) frente a la tensión
# circunferencial de la virola, a la presión de ensayo; la marca se toma como una ranura continua (cota superior)
from flama import modelo3d as M3  # noqa: E402

PROF_MARCA = {"1 kg": 0.10, "manual": 0.15, "rodante": 0.20}      # profundidad máxima de la marca (mm)


def membrana(a, b, t, p, r):
    """Tensiones de membrana (meridiana, circunferencial) de un casquete elipsoidal a la distancia r del eje."""
    u = r / a
    s_ = math.sqrt(1 - u * u)
    zp, zpp = (b / a ** 2) * r / s_, (b / a ** 2) / s_ ** 3
    r1, r2 = (1 + zp ** 2) ** 1.5 / zpp, r * math.sqrt(1 + zp ** 2) / zp
    return p * r2 / (2 * t), p * r2 / t * (1 - r2 / (2 * r1))


MK = {}
for c in ("FL_MAT_ABC_1kg", "FL_MAT_ABC_2.5kg", "FL_MAT_ABC_5kg", "FL_MAT_ABC_10kg", "FL_MAT_ABC_25kg",
          "FL_MAT_ABC_50kg", "FL_MAT_ABC_70kg", "FL_MAT_ABC_100kg"):
    m_, g_ = M[c], M[c].geo
    rod_ = m_.familia == "rodante"
    lab_, esc_ = M3.encastre(g_)
    b_ = g_["hd"] - (esc_ if rod_ else lab_)
    mk_ = M3.marca_cupula(m_)
    sm = max(abs(v) for v in membrana(g_["R"], b_, g_["td"], pe(c), mk_["rc"]))
    d_ = PROF_MARCA["1 kg" if m_.capacidad == "1 kg" else m_.familia]
    MK[c] = dict(franja=(2 * mk_["r_in"], 2 * mk_["r_out"]), arco=mk_["a_tot"], b=b_, s=sm,
                 s_marca=sm * g_["td"] / (g_["td"] - d_), s_cuerpo=pe(c) * g_["R"] / g_["t"], d=d_, td=g_["td"])


def _cmp(cs):
    return "; ".join(f"{M[c].capacidad}: {n(MK[c]['s'], 0)} ({n(MK[c]['s_marca'], 0)}) contra {n(MK[c]['s_cuerpo'], 0)}"
                     for c in cs)


MAN = ("FL_MAT_ABC_2.5kg", "FL_MAT_ABC_5kg", "FL_MAT_ABC_10kg")
ROD = ("FL_MAT_ABC_25kg", "FL_MAT_ABC_50kg", "FL_MAT_ABC_70kg")
m1 = MK["FL_MAT_ABC_1kg"]
# ================================================================== E. identificación
G.append(("E. Identificación", [
    it("M1", "Marcado estampado en la cúpula, en arco junto al cuello", "8 ABC propios",
       f"Franja Ø{n(m1['franja'][0], 0)}-{n(m1['franja'][1], 0)} (1 kg), "
       f"Ø{n(MK['FL_MAT_ABC_10kg']['franja'][0], 0)}-{n(MK['FL_MAT_ABC_10kg']['franja'][1], 0)} (2,5-10 kg), "
       f"Ø{n(MK['FL_MAT_ABC_25kg']['franja'][0], 0)}-{n(MK['FL_MAT_ABC_25kg']['franja'][1], 0)} (25 kg), "
       f"Ø{n(MK['FL_MAT_ABC_100kg']['franja'][0], 0)}-{n(MK['FL_MAT_ABC_100kg']['franja'][1], 0)} (50-100 kg); "
       "letra 5 mm; cuño DPS 15 × 7; arco de 169 a 270°",
       "Va en la cúpula y no en el cuerpo: la etiqueta, la oblea y el soporte no la tapan y el recargador la lee junto "
       "al cuello. Se marca en arco alrededor del eje porque en una pieza de revolución ese círculo está a una sola "
       "altura: la aguja de micropercusión trabaja a distancia constante y la letra sale pareja. La franja empieza "
       "4 mm afuera del cuello, fuera del pie del cordón cuello-cúpula. Tensión de membrana de la cúpula en la franja "
       "a la presión de ensayo, en MPa (entre paréntesis, tomando la marca como una ranura continua, que es la cota "
       f"superior) contra la tensión circunferencial de la virola: {_cmp(MAN)}; carros {_cmp(ROD)}. La franja queda "
       "dentro de ± 10 % de la virola, que es la que manda en la prueba hidráulica; las marcas de micropercusión son "
       "puntos redondeados, sin el filo de un cuño. En los manuales se marca antes de la PH, así que la prueba "
       "verifica cada cúpula ya marcada. En los carros se marca después de la PH (puesto 11), pero la franja queda "
       f"por debajo de la virola aun con la cota superior. La cúpula del 1 kg es casi plana ({n(m1['b'], 1)} mm de "
       "curva sobre Ø76, 0,9 mm de espesor): trabaja como una placa anular entre el cuello y la pollera, la teoría de "
       "membrana no aplica y lo que la verifica es la PH posterior al marcado.",
       "IRAM 3523 5.1 e IRAM 3550 5.1 (fabricante, número y año sobre el recipiente; en los carros también la "
       "presión de ensayo); IRAM 3523 5.2.4 3° l) (el número de la placa es el mismo del grabado); IRAM 4503 "
       "(letra); Res. 349/07 anexo IV (cuño DPS).",
       "Una marcadora de micropercusión (Pannier MarkFirst ADP120160D) con un apoyo por modelo hace los 4 manuales "
       "cambiando el programa, sin cuños ni yunques por formato: 37,5 s por cúpula. La marcadora va al lado de la "
       "prensa de muesca y de la soldadora de cuello: el mismo operario numera, marca el cuello y suelda, sin "
       "transporte entre los tres puestos.",
       "Justificado: marcado en la cúpula, en arco junto al cuello.",
       f"Profundidad de marca: hasta {n(PROF_MARCA['1 kg'], 2)} mm en el 1 kg, {n(PROF_MARCA['manual'], 2)} mm en "
       f"los demás manuales y {n(PROF_MARCA['rodante'], 1)} mm en los carros; controlarla en la primera pieza de "
       "cada tanda."),
    it("I1", "Etiqueta: alas laterales", "los 17", "Panel frontal de 108° + 2 alas de 54° (72° si Ø < 100)",
       "El frente visible del cilindro son 180°. El panel de 108° lleva las instrucciones de uso dentro de ± 54°, "
       "donde el ancho aparente del texto es al menos 0,59 del real (cos 54°); las alas llevan los datos del fabricante y de la carga. "
       "La costura y los accesorios de atrás quedan libres para soldar e inspeccionar. En cuerpos de Ø < 100 el "
       "contenido no entra en 108° de alto y se usan alas de 72°.",
       "IRAM 3534 (placa de características) e IRAM 3523 5.1 / IRAM 3550 5.2.5 (marcado).",
       "Una etiqueta de vinilo por modelo con el área justa del contenido: menos material y un solo pegado.",
       "Justificado."),
    it("I2", "Estampilla IRAM de conformidad", "los 17", "60 × 40 mm",
       "La provee el organismo certificador: el plano sólo reserva su lugar en la proporción 3:2 del Anexo R.",
       "Anexo R (estampilla IRAM de conformidad).",
       "Sin costo de fabricación: la entrega el certificador con la marca.",
       "Justificado.",
       "Confirmar la medida con el certificador al solicitar la marca."),
    it("I3", "Etiqueta de n° de serie GS1", "los 17", "45 × 25 mm",
       "Lleva un código QR de unos 20 mm: con un módulo cercano a 0,8 mm se lee con el celular a unos 20 cm (regla "
       "práctica: distancia de lectura ≈ 10 veces el lado del código), además del número en texto.",
       "Res. 349/07 PBA (trazabilidad del equipo); código GS1.",
       "Formato estándar de rollo para impresora térmica: el más barato del mercado.",
       "Justificado."),
    it("I4", "Faja de garantía válvula-cuello", "los 17", "30 × 40 mm (dibujada a la medida del cuello)",
       "Cubre la unión entre la válvula y el cuello: si se desenrosca la válvula, la faja se rompe y la manipulación "
       "queda a la vista. Va del lado donde no la tapan el manómetro ni las palancas; el ancho se limita al cuello.",
       "IRAM 3517-2 (identificación de equipos; la faja de sustitutos es ≤ 40 mm según 9.4.5).",
       "Vinilo destructible comercial en rollo.",
       "Justificado."),
    it("I5", "Tarjeta de identificación AGC (CABA)", "16 modelos (todos menos el 1 kg)", "140 × 55 mm",
       "Son dos módulos de 70 × 55: uno con el código QR y los datos del equipo y otro para la etiqueta de la AGC. En "
       "el 1 kg el cuerpo no tiene 140 mm de superficie libre.",
       "Res. AGC 32/15 (CABA), anexos I y II.",
       "Papel autoadhesivo impreso en el servicio de recarga; costo despreciable.",
       "Justificado.",
       "Confirmar el formato vigente con la AGC."),
]))

condiciones = [dict(item=i["titulo"], condicion=i["condicion"]) for _, its in G for i in its if i["condicion"]]
out = dict(grupos=[dict(titulo=t_, items=its) for t_, its in G], condiciones=condiciones)
json.dump(out, open(os.path.join(SP, "jw", "analisis.json"), "w"), ensure_ascii=False, indent=1)
print(sum(len(its) for _, its in G), "ítems;", len(condiciones), "condiciones de compra")
