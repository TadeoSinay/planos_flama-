"""Documentos técnicos FLAMA (PDF A4) generados con pymupdf.Story.

  DOC-01  Tratamiento superficial y pintura (granallado, fosfatizado,
          pintura en polvo, controles, saponificación).
  DOC-02  Ensayos obligatorios de fabricación de matafuegos ABC (manuales y rodantes).
  DOC-03  Ensayos e intervalos de mantenimiento y recarga por tipo de matafuego.
  DOC-04  NFPA 10 frente a IRAM: señalización, colores, instalación e intervalos.

Cada valor indica su origen en la columna "Fuente":
  C = catálogo FLAMA (dato propio), N = norma citada,
  R = valor de referencia habitual que FLAMA debe confirmar con la edición
      vigente de la norma IRAM (texto protegido, no disponible aquí).
"""

import html

import pymupdf

from .catalogo import MODELOS
from .planos import FECHA

CSS = """
* { font-family: sans-serif; }
body { font-size: 9pt; line-height: 1.3; }
h1 { font-size: 15pt; margin: 0 0 4pt 0; }
h2 { font-size: 11pt; margin: 10pt 0 3pt 0; border-bottom: 1px solid #000; }
h3 { font-size: 9.5pt; margin: 6pt 0 2pt 0; }
p { margin: 2pt 0 4pt 0; text-align: justify; }
table { border-collapse: collapse; width: 100%; margin: 3pt 0 6pt 0; }
td, th { border: 1px solid #000; padding: 2pt 3pt; font-size: 8pt; vertical-align: top; }
th { background-color: #e6e6e6; text-align: left; }
.cab td { font-size: 9pt; }
.nota { font-size: 7.5pt; color: #333; }
.rojo { color: #af2b1e; font-weight: bold; }
ul { margin: 2pt 0 4pt 14pt; } li { margin: 1pt 0; }
"""

FUENTES = ("<p class='nota'><b>Fuente:</b> C = catálogo FLAMA · N = norma citada · "
           "R = valor de referencia habitual, <b>a confirmar por FLAMA con la edición vigente de la norma IRAM</b> "
           "(el texto de las normas IRAM es material protegido y no se transcribe).</p>")


def _e(s):
    return html.escape(str(s))


def tabla(filas, encabezado=None, anchos=None):
    out = ["<table>"]
    if anchos:
        out.append("<tr>" + "".join(f"<th style='width:{w}%'>{_e(c)}</th>" for c, w in zip(encabezado, anchos)) + "</tr>")
    elif encabezado:
        out.append("<tr>" + "".join(f"<th>{_e(c)}</th>" for c in encabezado) + "</tr>")
    for f in filas:
        out.append("<tr>" + "".join(f"<td>{c}</td>" for c in f) + "</tr>")
    out.append("</table>")
    return "".join(out)


def cabecera(codigo, titulo, alcance):
    return (f"<table class='cab'><tr><td style='width:22%'><b>FLAMA S.A.</b></td>"
            f"<td style='width:56%'><b>{_e(titulo)}</b></td><td style='width:22%'>{_e(codigo)}</td></tr>"
            f"<tr><td>Edición 0</td><td>{_e(alcance)}</td><td>{FECHA}</td></tr></table>")


# ------------------------------------------------------------------ DOC-01
def doc01():
    h = [cabecera("DOC-01", "Tratamiento superficial y pintura", "Recipientes, soportes y gabinetes FLAMA"),
         "<h1>Tratamiento superficial, pintura y saponificación</h1>",
         "<h2>1. Alcance</h2>",
         "<p>Preparación de superficie y pintura exterior de recipientes de acero al carbono (ABC, BC, HCFC/HFC, "
         "clase D, rodantes), cilindros de CO<sub>2</sub>, soportes y gabinetes; terminación de recipientes de acero "
         "inoxidable (agua, AFFF, sales K). El interior de los recipientes no se pinta salvo indicación del plano.</p>",
         "<h2>2. Secuencia de proceso (acero al carbono)</h2>",
         tabla([
             ["1", "Desengrase", "Alcalino por aspersión o inmersión; enjuague. Superficie libre de aceite (ensayo de "
              "gota de agua).", "R"],
             ["2", "Granallado", "Granalla de acero angular (ISO 11124-3), grado <b>Sa 2½</b> (ISO 8501-1). "
              "Perfil de rugosidad <b>fino a medio</b> (comparador ISO 8503-1/-2), Rz ≈ 30 a 60 µm, adecuado a "
              "60-100 µm de polvo.", "N / R"],
             ["3", "Limpieza de polvo", "Aire seco sin aceite; polvo residual ≤ clase 2 (ISO 8502-3).", "N"],
             ["4", "Conversión (opcional)", "Fosfatizado de hierro o zinc, o nanocerámico; mejora la adherencia y la "
              "resistencia a la corrosión bajo película. Enjuague con agua desmineralizada y secado.", "R"],
             ["5", "Tiempo de espera", "Pintar dentro de las 4 h del granallado, con humedad relativa ≤ 85 % y "
              "temperatura de chapa ≥ 3 °C sobre el punto de rocío (ISO 8502-4).", "N / R"],
             ["6", "Pintura en polvo", "<b>Poliéster</b> (TGIC-free, apto exterior) rojo RAL 3000 (rojo de seguridad "
              "IRAM 10005). Aplicación electrostática. Espesor seco <b>60 a 100 µm</b>.", "R"],
             ["7", "Curado", "Según ficha técnica del polvo (típico 10 min a 180-200 °C de temperatura de pieza). "
              "Controlar con registrador de temperatura en pieza.", "R"],
         ], ["Paso", "Operación", "Especificación", "Fuente"], [6, 18, 68, 8]),
         "<h2>3. Acero inoxidable (agua, AFFF, sales K)</h2>",
         "<p>Recipiente AISI 304 soldado TIG (141). Después de soldar: decapado de las zonas térmicamente afectadas "
         "con pasta o gel de decapado y <b>pasivado</b> (ácido nítrico o cítrico, ASTM A967 / A380). Terminación "
         "exterior: pintura en polvo poliéster roja sobre imprimación compatible con inoxidable, o sin pintar con "
         "etiqueta roja según el diseño aprobado. Nunca granallar inoxidable con granalla de acero al carbono "
         "(contaminación con hierro); usar microesfera de vidrio u óxido de aluminio.</p>",
         "<h2>4. Controles de calidad de la pintura</h2>",
         tabla([
             ["Espesor de película seca", "ISO 2808 / ISO 19840", "60 a 100 µm; ningún punto &lt; 80 % del nominal",
              "cada lote", "R"],
             ["Adherencia (cuadriculado)", "ISO 2409", "clase 0 ó 1", "cada lote", "N / R"],
             ["Impacto", "ISO 6272-1", "sin fisuras ni desprendimiento con la energía de la ficha del polvo",
              "por partida de polvo", "R"],
             ["Grado de curado", "frote con MEK (ASTM D5402)", "sin ablandamiento ni pérdida de brillo", "cada turno", "R"],
             ["Brillo y color", "ISO 2813 / ISO 7724", "RAL 3000, ΔE ≤ 1,5 contra patrón", "cada lote", "R"],
             ["Niebla salina neutra", "ISO 9227 (NSS)", "<b>500 h</b>: ampollamiento 0(S0) ISO 4628-2; "
              "avance en la incisión ≤ 2 mm (ISO 4628-8)", "semestral / cambio de proceso", "R"],
             ["Resistencia a agentes extintores", "ISO 2812-4 (gota)", "24 h de contacto con cada agente del tipo: sin "
              "ablandamiento, ampollas ni cambio de color", "calificación de polvo", "R"],
         ], ["Ensayo", "Método", "Criterio de aceptación", "Frecuencia", "Fuente"], [20, 17, 40, 15, 8]),
         "<h2>5. Saponificación y compatibilidad química</h2>",
         "<p><b>Qué es.</b> La saponificación es la hidrólisis alcalina de los enlaces éster de un ligante: el álcali "
         "rompe la resina y forma jabones solubles. Afecta a las pinturas con ligantes de aceite o <b>alquídicos</b> "
         "(esmaltes sintéticos) y, en menor medida, a otros poliésteres no reticulados. El síntoma es ablandamiento, "
         "pegajosidad, ampollas, pérdida de brillo y desprendimiento por debajo de la película.</p>",
         "<p><b>Dónde aparece en un matafuego.</b></p>",
         tabla([
             ["Sales K (clase K)", "soluciones de sales de potasio (acetato, citrato, carbonato), <b>alcalinas</b>",
              "Alto: saponifica alquídicos; ataca aluminio y zinc", "Recipiente inoxidable sin pintura interior; "
              "exterior poliéster en polvo; válvula y lanza en latón/inox"],
             ["BC (bicarbonato de sodio)", "polvo alcalino; con humedad forma solución alcalina",
              "Medio en derrames húmedos", "Exterior poliéster en polvo; limpiar derrames en la recarga"],
             ["ABC (fosfato monoamónico)", "polvo <b>ácido</b> e higroscópico",
              "No saponifica; corroe acero si se humedece", "Interior seco (secado después de PH); polvo sellado"],
             ["AFFF / agua", "solución acuosa casi neutra, con tensioactivos",
              "Bajo; corrosión si el acero no está protegido", "Recipiente inoxidable (AISI 304)"],
             ["Galvanizados", "el zinc reacciona con alquídicos y forma jabones de zinc",
              "Desprendimiento de esmaltes sintéticos sobre zinc", "No usar alquídicos sobre soportes zincados; "
              "polvo poliéster sobre zincado con conversión"],
         ], ["Agente / sustrato", "Química", "Riesgo", "Medida adoptada por FLAMA"], [18, 30, 22, 30]),
         "<p><b>Criterio FLAMA:</b> no se usan esmaltes alquídicos (sintéticos) en ningún componente. Se usa "
         "pintura en polvo <b>poliéster reticulado</b>, resistente a álcalis diluidos y a la radiación UV. Todo "
         "polvo nuevo se califica con el ensayo de gota del punto 4 con solución de sales K, solución de bicarbonato "
         "y solución de fosfato monoamónico. Los retoques en recarga se hacen con pintura compatible (poliuretano "
         "bicomponente o poliéster), nunca con esmalte sintético.</p>",
         FUENTES]
    return "".join(h)


# ------------------------------------------------------------------ DOC-02
def _abc():
    return [m for m in MODELOS if m.codigo.startswith("FL_MAT_ABC")]


def doc02():
    filas_mod = []
    for m in _abc():
        s = m.spec
        filas_mod.append([m.codigo, _e(s["Capacidad nominal"]), _e(s["Presión de servicio (MPa)"]),
                          _e(s["Presión de ensayo (MPa)"]), _e(s["Tiempo de descarga (s)"]), _e(s["Alcance (m)"]),
                          _e(s["Rango temperatura (°C)"]), "IRAM " + _e(m.spec.get("Norma IRAM extintor", "3523"))])
    h = [cabecera("DOC-02", "Ensayos de fabricación - matafuegos ABC", "FL_MAT_ABC_1kg a FL_MAT_ABC_100kg y FL_REC_ABC_*"),
         "<h1>Ensayos obligatorios de fabricación - matafuegos ABC</h1>",
         "<h2>1. Normas de referencia</h2>",
         "<ul><li>IRAM 3523 - Matafuegos manuales de polvo bajo presión (ABC 1 a 10 kg).</li>"
         "<li>IRAM 3550 - Matafuegos rodantes de polvo (ABC 25 a 100 kg).</li>"
         "<li>IRAM 3569 - Polvo químico seco ABC. IRAM 3533 - Manómetros para matafuegos.</li>"
         "<li>ISO 15614-1 / ISO 9606-1 - calificación de procedimientos y soldadores; ISO 5817 - niveles de calidad.</li>"
         "<li>Referencia complementaria: EN 3-7 y EN 1866-1 (matafuegos portátiles y rodantes, Unión Europea).</li></ul>",
         "<h2>2. Datos de catálogo por modelo</h2>",
         tabla(filas_mod, ["Modelo", "Carga", "Ps (MPa)", "Pe (MPa)", "Descarga (s)", "Alcance (m)", "T (°C)",
                           "Norma"]),
         "<h2>3. Plan de ensayos</h2>",
         "<h3>3.1 Ensayos de rutina (100 % de las unidades)</h3>",
         tabla([
             ["R1", "Control de chapa", "certificado de colada; espesor ≥ nominal del plano FL_REC (micrómetro)",
              "por bobina", "N / C"],
             ["R2", "Inspección visual de soldaduras", "ISO 5817 nivel C: sin fisuras, poros abiertos ni falta de "
              "penetración visible en costura longitudinal, circunferencial y cuello", "100 %", "N"],
             ["R3", "<b>Prueba hidráulica</b> del recipiente (FL_ESQ_01)", "presión de ensayo Pe del catálogo "
              "(3,5 MPa manuales; 4,0 MPa rodantes) mantenida ≥ 30 s: sin pérdidas, exudación ni deformación visible",
              "100 %", "C / R"],
             ["R4", "Secado interior", "después de la PH, hasta ausencia de humedad (el polvo ABC es higroscópico)",
              "100 %", "R"],
             ["R5", "Pintura", "espesor y adherencia según DOC-01", "por lote", "R"],
             ["R6", "Carga de agente", "pesada de polvo IRAM 3569 con balanza calibrada; tolerancia ± 2 % de la carga "
              "nominal", "100 %", "R"],
             ["R7", "Presurización", "N<sub>2</sub> seco a la presión de servicio (1,4 MPa a 20 °C); verificación con "
              "manómetro patrón; aguja del manómetro IRAM 3533 en zona verde", "100 %", "C / N"],
             ["R8", "<b>Estanqueidad</b>", "inmersión o detector de fugas: sin burbujas; control de presión a las 24 h "
              "sin caída detectable", "100 %", "R"],
             ["R9", "Pesada final y marcado", "masa total dentro de la tolerancia; etiqueta, n° de serie, sello IRAM, "
              "fecha; precinto y seguro colocados", "100 %", "N / C"],
         ], ["N°", "Ensayo", "Método y criterio", "Frecuencia", "Fuente"], [5, 20, 55, 10, 10]),
         "<h3>3.2 Ensayos por lote (muestreo)</h3>",
         tabla([
             ["L1", "Rotura (destructivo)", "presurizar con agua hasta la rotura: presión ≥ la exigida por IRAM 3523/3550 "
              "(referencia: ≥ 2 × Pe); rotura dúctil, sin fragmentación, fuera de la costura del cuello",
              "1 por lote o por turno de soldadura", "R"],
             ["L2", "Expansión volumétrica", "método de camisa de agua a Pe: expansión permanente ≤ 10 % de la total",
              "1 por lote", "R"],
             ["L3", "Descarga", "tiempo de descarga y alcance dentro del catálogo; masa residual ≤ 15 % de la carga",
              "1 por lote", "C / R"],
             ["L4", "Polvo", "certificado del lote IRAM 3569; humedad y fluidez según certificado", "por lote de polvo", "N"],
             ["L5", "Manómetros y válvulas", "certificado IRAM 3533; prueba de la válvula a Pe", "por partida", "N / R"],
         ], ["N°", "Ensayo", "Método y criterio", "Frecuencia", "Fuente"], [5, 20, 55, 10, 10]),
         "<h3>3.3 Ensayos de tipo (certificación, laboratorio acreditado)</h3>",
         "<ul><li>Potencial extintor en fuegos normalizados clase A y B y ensayo de conductividad para clase C.</li>"
         "<li>Funcionamiento en los extremos del rango de temperatura del catálogo (−20 °C y +50 °C).</li>"
         "<li>Resistencia a la corrosión (niebla salina, DOC-01), caída y vibración (manuales), y rodadura y "
         "estabilidad (rodantes, IRAM 3550).</li>"
         "<li>Se repiten al cambiar el diseño, el proveedor del polvo, la válvula o el procedimiento de soldadura.</li></ul>",
         "<h2>4. Recipientes ABC sueltos (FL_REC_ABC_*)</h2>",
         "<p>Se entregan con R1 a R5, L1 y L2 aprobados, con el n° de serie y la fecha de PH estampados, el "
         "interior seco y el cuello protegido con tapón. El armado final (R6 a R9) queda a cargo del comprador, que "
         "asume los ensayos de conjunto.</p>",
         "<h2>5. Registros</h2>",
         "<p>Por n° de serie: colada de chapa, soldador, fecha y resultado de PH, lote de polvo, peso, presión y "
         "estanqueidad. Conservar según el sistema de calidad (mínimo la vida útil del matafuego).</p>",
         FUENTES]
    return "".join(h)


# ------------------------------------------------------------------ DOC-03
def doc03():
    grupos = [
        ("ABC / BC / clase D (polvo, presión permanente)", "FL_MAT_ABC_1kg a 10kg, BC_5kg, CLASED_9l",
         "3,5", "5 años", "12 años",
         "vaciar, secar, polvo nuevo o recuperado y tamizado del mismo tipo; N<sub>2</sub> a Ps; estanqueidad; "
         "NFPA: examen interno cada 6 años"),
        ("ABC rodantes", "FL_MAT_ABC_25kg a 100kg", "4,0", "5 años", "12 años",
         "igual que polvo; además PH de la manguera y control de ruedas, eje y válvula esférica"),
        ("CO<sub>2</sub>", "FL_MAT_CO2_2kg, 5kg", "25", "5 años", "5 años",
         "<b>control por pesada</b>: recargar si la pérdida supera el 10 % de la carga; PH con camisa de agua y "
         "expansión permanente; manga de alta presión con PH propia"),
        ("Agua", "FL_MAT_AGUA_10l", "2,0", "5 años", "5 años",
         "agua nueva; N<sub>2</sub> o aire seco a 0,8 MPa; revisar corrosión interna del inoxidable"),
        ("AFFF", "FL_MAT_AFFF_10l, 50l", "2,0 / 4,0", "5 años", "5 años",
         "solución nueva a la concentración del fabricante; NFPA: reemplazo de la solución premezclada cada 3 años"),
        ("Sales K", "FL_MAT_SALESK_6l", "2,0", "5 años", "5 años",
         "solución nueva del fabricante; lanza y boquilla limpias; recipiente inoxidable"),
        ("HCFC / HFC (halogenados)", "FL_MAT_HCFC-HFC_5kg", "2,0", "5 años", "12 años",
         "<b>recuperación en circuito cerrado</b> (prohibido ventear); reciclado o agente nuevo; control por "
         "presión y pesada"),
    ]
    filas = [[f"<b>{g[0]}</b><br/>{g[1]}", g[2], g[3], g[4], g[5]] for g in grupos]
    h = [cabecera("DOC-03", "Mantenimiento, recarga y prueba hidráulica", "Todos los modelos FLAMA"),
         "<h1>Ensayos de mantenimiento y recarga por tipo</h1>",
         "<h2>1. Normas</h2>",
         "<ul><li><b>IRAM 3517-2</b> - Matafuegos manuales y sobre ruedas. Dotación, control, mantenimiento y "
         "recarga (norma argentina de servicio).</li>"
         "<li><b>NFPA 10</b> - Standard for Portable Fire Extinguishers (inspección, mantenimiento y prueba "
         "hidrostática; referencia internacional).</li>"
         "<li>Reglamentación local: Dec. 351/79 (Ley 19.587) y ordenanzas municipales (habilitación de recargadoras).</li></ul>",
         "<h2>2. Intervalos</h2>",
         tabla([
             ["Control del usuario", "trimestral (R)", "mensual (inspección, N)"],
             ["Mantenimiento por empresa habilitada", "anual: control de carga y presión, tarjeta (R)", "anual (N)"],
             ["Recarga", "después de cada uso, por pérdida de carga/presión o al vencer la carga (R)",
              "después de cada uso o si la inspección lo indica (N)"],
             ["Prueba hidráulica", "cada 5 años como máximo, todos los tipos (R)", "según tabla 3 (N)"],
         ], ["Actividad", "IRAM 3517-2", "NFPA 10"], [30, 40, 30]),
         "<h2>3. Ensayos por tipo en la recarga</h2>",
         tabla(filas, ["Tipo / modelos", "PH (MPa, C)", "PH IRAM 3517-2", "PH NFPA 10", "Particularidades de la recarga"],
               [26, 10, 12, 10, 42]),
         "<h2>4. Ensayos comunes a toda recarga</h2>",
         tabla([
             ["1", "Inspección externa", "corrosión, abolladuras, soldaduras, rosca del cuello, legibilidad del marcado; "
              "rechazo: corrosión con pérdida de material, golpes con arista, fisuras, fuego"],
             ["2", "Inspección interna", "linterna o endoscopio: corrosión, restos de agente apelmazado; recubrimiento"],
             ["3", "Válvula", "O-ring nuevo, vástago y resorte, sifón destapado, manguera sin fisuras, tobera"],
             ["4", "Manómetro", "sello IRAM 3533, aguja libre, cero correcto; reemplazar si no verifica"],
             ["5", "Prueba hidráulica", "si vence o si el recipiente es dudoso (FL_ESQ_01); rechazo = inutilizar"],
             ["6", "Carga y presurización", "según FL_ESQ_02 / FL_ESQ_03 con la presión del catálogo"],
             ["7", "Estanqueidad", "inmersión o detector; control de presión a las 24 h"],
             ["8", "Registro", "tarjeta FL_SEN_04, precinto nuevo, oblea de la jurisdicción"],
         ], ["N°", "Ensayo", "Criterio"], [5, 20, 75]),
         "<p class='nota'>Presiones de ensayo (columna PH): catálogo FLAMA (Hoja 3 de cada plano). Los intervalos de "
         "NFPA 10 son los de la edición 2022 (hidrostática: 5 años para CO<sub>2</sub>, agua, espuma y químico "
         "húmedo; 12 años para polvo y halogenados; examen interno de polvo presurizado a los 6 años).</p>",
         FUENTES]
    return "".join(h)


# ------------------------------------------------------------------ DOC-04
def doc04():
    h = [cabecera("DOC-04", "NFPA 10 frente a IRAM", "Señalización, colores, instalación e intervalos"),
         "<h1>NFPA 10 frente a IRAM: marcado, colores e instalación</h1>",
         "<h2>1. Identificación de clases de fuego</h2>",
         "<p>NFPA 10 admite dos sistemas de marcado de la etiqueta: el sistema <b>letra-forma de color</b> y el "
         "sistema de <b>pictogramas</b> (Anexo B). En Argentina, IRAM 10005 usa las mismas formas geométricas para "
         "las clases. Láminas: FL_SEN_03 (letra-forma) y FL_SEN_05 (pictogramas).</p>",
         tabla([
             ["A", "combustibles sólidos comunes", "triángulo <b>verde</b>", "cesto con residuos y fuego"],
             ["B", "líquidos y gases inflamables", "cuadrado <b>rojo</b>", "bidón y fuego"],
             ["C", "equipos eléctricos energizados", "círculo <b>azul</b>", "enchufe y fuego"],
             ["D", "metales combustibles", "estrella de 5 puntas <b>amarilla</b>", "sin pictograma"],
             ["K", "aceites y grasas de cocina", "hexágono <b>negro</b>", "sartén y fuego"],
         ], ["Clase", "Fuego", "Letra-forma (NFPA 10 / IRAM 10005)", "Pictograma NFPA 10"], [8, 32, 32, 28]),
         "<p>En el sistema de pictogramas, la clase para la que el agente <b>no es apto</b> se muestra con fondo "
         "negro y barra diagonal roja; los matafuegos de agua y espuma deben mostrar la clase C tachada.</p>",
         "<h2>2. NFPA 704 no se usa en el matafuego</h2>",
         "<p>El rombo de NFPA 704 (azul salud, rojo inflamabilidad, amarillo inestabilidad, blanco riesgos "
         "especiales, escala 0 a 4) identifica los peligros de los <b>materiales almacenados</b> en un edificio o "
         "tanque para los bomberos. No es una señal del matafuego ni de su clase de fuego.</p>",
         "<h2>3. Colores de seguridad y carteles</h2>",
         tabla([
             ["Color del matafuego", "rojo (IRAM 3523 y afines)", "rojo habitual; NFPA no fija el color del cuerpo"],
             ["Cartel de ubicación", "IRAM 10005: rojo con pictograma blanco; ISO 7010 F001", "OSHA / ANSI Z535; "
              "ISO 7010 F001 aceptado"],
             ["Chapa baliza", "franjas rojas y blancas a 45° (IRAM 10005), FL_SEN_01", "no existe en NFPA 10"],
             ["Tamaño del cartel", "ISO 3864-1: h = L/Z", "visible desde el recorrido normal (NFPA 10)"],
         ], ["Tema", "IRAM / Argentina", "NFPA 10 / EE. UU."], [24, 38, 38]),
         "<h2>4. Instalación</h2>",
         tabla([
             ["Altura de la parte superior", "≤ 1,50 m (práctica argentina, Dec. 351/79; confirmar)",
              "≤ 1,53 m (5 ft) si pesa ≤ 18,14 kg; ≤ 1,07 m (3,5 ft) si pesa más (§6.1.3.8.1-2)"],
             ["Separación al piso", "-", "≥ 102 mm (4 in) (§6.1.3.8.3)"],
             ["Distancia de recorrido", "según riesgo y reglamentación local",
              "clase A: 22,9 m (75 ft); clase B: 9,15 o 15,25 m (30 o 50 ft) según potencial"],
             ["Visibilidad", "chapa baliza y cartel", "visible, accesible, sin obstrucciones; señalizado si no se ve"],
         ], ["Tema", "IRAM / Argentina", "NFPA 10"], [24, 38, 38]),
         "<h2>5. Inspección, mantenimiento y prueba hidráulica</h2>",
         tabla([
             ["Inspección", "trimestral (IRAM 3517-2)", "mensual"],
             ["Mantenimiento", "anual", "anual"],
             ["Examen interno polvo presurizado", "en cada recarga / PH", "cada 6 años"],
             ["PH polvo y halogenados", "cada 5 años", "cada 12 años"],
             ["PH CO<sub>2</sub>, agua, espuma, químico húmedo", "cada 5 años", "cada 5 años"],
             ["Solución AFFF premezclada", "en cada recarga", "reemplazo cada 3 años"],
         ], ["Actividad", "IRAM", "NFPA 10"], [40, 30, 30]),
         "<p class='nota'>Los números de sección de NFPA 10 corresponden a la edición 2022; verificar contra la "
         "edición adoptada por la autoridad competente. Los valores IRAM se indican como referencia (ver fuentes).</p>",
         FUENTES]
    return "".join(h)


DOCUMENTOS = [("DOC-01_Tratamiento_superficial_y_pintura", doc01),
              ("DOC-02_Ensayos_fabricacion_ABC", doc02),
              ("DOC-03_Ensayos_recarga_por_tipo", doc03),
              ("DOC-04_NFPA10_vs_IRAM", doc04)]


def pdf(html_body, ruta, titulo):
    """HTML → PDF A4 con márgenes de 20/15 mm y pie con número de página."""
    mm = 72 / 25.4
    story = pymupdf.Story(html=f"<body>{html_body}</body>", user_css=CSS)
    page = pymupdf.paper_rect("a4")
    area = pymupdf.Rect(20 * mm, 15 * mm, page.width - 15 * mm, page.height - 18 * mm)
    w = pymupdf.DocumentWriter(ruta)
    more = True
    while more:
        dev = w.begin_page(page)
        more, _ = story.place(area)
        story.draw(dev)
        w.end_page()
    w.close()
    d = pymupdf.open(ruta)
    for i, p in enumerate(d):
        p.insert_text((20 * mm, page.height - 9 * mm), f"FLAMA S.A. · {titulo} · página {i + 1} de {len(d)}",
                      fontsize=7)
    d.saveIncr() if d.can_save_incrementally() else None
    d.close()
