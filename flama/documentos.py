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
              "(3,5 MPa manuales; 4,0 MPa rodantes) mantenida <b>1 min</b> (criterio de IRAM 3517-2 4.3.3.6 h): sin "
              "caída de presión, pérdidas ni deformación permanente visible; bomba ≥ 150 % de Pe y jaula", "100 %", "C / N"],
             ["R4", "Secado interior", "después de la PH, hasta que no se vea agua ni humedad condensada "
              "(IRAM 3517-2 4.3.3.4)", "100 %", "N"],
             ["R5", "Pintura", "espesor y adherencia según DOC-01", "por lote", "R"],
             ["R6", "Carga de agente", "pesada de polvo ABC gris IRAM 3569 con balanza calibrada; tolerancia "
              "<b>1 y 2,5 kg: 0/+100 g; 5 y 10 kg: 0/+300 g; rodantes: +3 %</b> (IRAM 3517-2 anexo E); recinto HR ≤ 70 %",
              "100 %", "N"],
             ["R7", "Presurización", "N<sub>2</sub> seco a la presión de servicio (1,4 MPa a 20 °C); verificación con "
              "manómetro patrón; aguja del manómetro IRAM 3533 en zona verde", "100 %", "C / N"],
             ["R8", "<b>Estanqueidad</b>", "ensayo de verificación de pérdidas de propelente y agente (IRAM 3517-2 3.8): "
              "inmersión o detector; control de presión a las 24 h (criterio FLAMA)", "100 %", "N / R"],
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
             ["L3", "Descarga", "manuales: ≥ 8 s y ≥ 85 % descargado; rodantes: 25 kg ≥ 10 s, 50/70 kg ≥ 15 s, "
              "100 kg ≥ 30 s, ≥ 85 % (IRAM 3517-2 anexo E); alcance según catálogo", "1 por lote", "N / C"],
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
def _ps(m):
    return float(m.spec["Presión de servicio (MPa)"].replace(",", "."))


def doc03():
    fil_ph = []
    for m in MODELOS:
        ps = _ps(m)
        if m.familia == "co2":
            pr = "IRAM 2529-1 (camisa de agua)"
        else:
            pr = f"{2.5 * ps:.1f}".replace(".", ",") + " (2,5 × Ps)"
        intervalo = "2 años" if m.familia == "inox" or "AFFF" in m.codigo else "5 años"
        fil_ph.append([m.codigo.replace("FL_MAT_", ""), _e(m.spec["Presión de servicio (MPa)"]), pr,
                       _e(m.spec["Presión de ensayo (MPa)"]), intervalo])
    h = [cabecera("DOC-03", "Mantenimiento, recarga y prueba hidráulica", "Todos los modelos FLAMA"),
         "<h1>Ensayos de control, mantenimiento y recarga por tipo</h1>",
         "<p>Base: <b>IRAM 3517-2:2005</b> (tercera edición, 2005-12-23), leída en su texto completo; se citan "
         "los apartados. Las novedades de la <b>revisión 2020</b> se toman de un resumen publicado por un "
         "prestador (fuente secundaria, columna S) hasta disponer del texto 2020. NFPA 10 como referencia.</p>",
         "<h2>1. Intervalos (IRAM 3517-2)</h2>",
         tabla([
             ["Control periódico", "cada 3 meses como mínimo, 4 controles cada 12 meses; verifica dotación y equipos "
              "(tabla B.1); formulario del anexo C por duplicado", "3.3.1 a 3.3.8", "N"],
             ["Etiqueta de control", "celeste, <b>35 mm de alto × 50 mm de largo</b>, con: EQUIPO CONTROLADO POR, "
              "FECHA (mes y año), EL PRÓXIMO CONTROL SE DEBE REALIZAR ANTES DE CUMPLIRSE LOS TRES MESES DE LA FECHA "
              "INDICADA; adherida al extintor, nunca al gabinete (FL_SEN_04)", "3.3.6", "N"],
             ["Mantenimiento", "por lo menos anualmente, o cuando lo indique el control; examen de partes mecánicas, "
              "agente y medio de expulsión", "3.4.2, 3.4.4", "N"],
             ["Equipos de reemplazo", "el extintor retirado se sustituye por uno de igual clasificación y potencial",
              "3.4.3", "N"],
             ["Recarga", "después del uso, cuando lo indique una inspección o el mantenimiento; sólo agentes "
              "IRAM del anexo D con certificación", "3.5.2, 3.5.3.7", "N"],
             ["Agua, AFFF (y sales K, 2020)", "cambiar el agente <b>cada año</b>, previo lavado interior",
              "tabla B.1; S", "N / S"],
             ["Prueba hidrostática", "<b>como máximo cada 5 años</b>: polvo, CO<sub>2</sub>, halogenados; "
              "<b>como máximo cada 2 años</b>: agua, AFFF (2020: también acetato de potasio). Su vencimiento no debe "
              "ser anterior al vencimiento de la carga", "tabla B.1, 4.3.1.6; S", "N / S"],
             ["Mangas", "PH cada vez que el extintor requiere PH o ante dudas (2005); anual para CO<sub>2</sub> y ABC "
              "con rótulo en la manga (2020)", "4.3.3.7; S", "N / S"],
             ["Marbete (disco)", "cambiar con cada mantenimiento y recarga (polvo, halogenados); CO<sub>2</sub>: con "
              "cada PH", "tabla B.1, 3.10", "N"],
         ], ["Actividad", "Requisito", "Apartado", "F."], [18, 60, 14, 8]),
         "<h2>2. Prueba hidrostática (4.3)</h2>",
         "<ul><li><b>Presión</b>: extintores bajo presión que operan a menos de 2,8 MPa: <b>2,5 veces la presión de "
         "servicio</b> (4.3.2.2). CO<sub>2</sub> y cilindros: IRAM 2529-1 (4.3.2.1, 4.3.3.5). Mangas de CO<sub>2</sub>: "
         "IRAM 3509/3565; las demás: a la presión de servicio (4.3.2.3).</li>"
         "<li><b>Equipo</b> (4.3.3.3): bomba manual o a motor capaz de <b>no menos del 150 %</b> de la presión de "
         "ensayo, válvulas de retención, conexión flexible y <b>jaula o barrera de protección</b> (FL_ESQ_01). "
         "Nunca presión neumática ni de gas.</li>"
         "<li><b>Procedimiento</b> (4.3.3.6): quitar válvula y partes internas, eliminar todo el polvo, llenar con "
         "agua purgando el aire, subir a la presión de prueba y <b>mantenerla 1 min</b>. Satisfactorio si no hay "
         "caída de presión, rotura, pérdidas visibles ni deformaciones permanentes visibles; si falla, se inutiliza.</li>"
         "<li><b>Mangas</b> (4.3.3.7): llenar de agua, llegar a la presión en 1 min como máximo, mantener 1 min; "
         "secar a no más de 65 °C; las que fallan se destruyen.</li>"
         "<li><b>No se ensaya y se inutiliza</b> (4.3.1.3): reparaciones por soldadura o masilla, picaduras "
         "pasantes, extintor quemado, inoxidable cargado con anticongelante de cloruro de calcio.</li>"
         "<li><b>Secado</b> (4.3.3.4): todo extintor que no sea de agua se seca hasta que no se vea agua ni "
         "humedad condensada.</li></ul>",
         tabla(fil_ph, ["Modelo", "Ps (MPa)", "PH recarga (MPa) 3517-2", "Pe fabricación (MPa, catálogo)",
                        "Intervalo PH"], [22, 12, 28, 22, 16]),
         "<p class='nota'>Donde la presión de fabricación del catálogo (rodantes 4,0 MPa) supera 2,5 × Ps, en la "
         "recarga rige 2,5 × Ps según 3517-2; FLAMA puede ensayar a la presión de fabricación si su norma de "
         "producto lo exige (confirmar con IRAM 3550 / 3541).</p>",
         "<h2>3. Condiciones de funcionamiento a garantizar (anexo E)</h2>",
         tabla([
             ["3523 polvo manual", "1 y 2,5 kg: 0 / +100 g · 5 y 10 kg: 0 / +300 g", "mín. 8 s", "mín. 85 %"],
             ["3550 polvo rodante", "+3 %", "25 kg mín. 10 s · 50 y 70 kg mín. 15 s · 100 kg mín. 30 s", "mín. 85 %"],
             ["3509 CO<sub>2</sub> manual", "0 / −5 %", "mín. 8 s", "mín. 80 %"],
             ["3525 agua manual", "+3 %", "40 a 65 s", "mín. 95 %"],
             ["3527 AFFF manual", "+3 %", "40 a 65 s", "mín. 85 %"],
             ["3541 AFFF rodante", "+3 %", "50 L: 90 a 150 s", "mín. 95 %"],
         ], ["Norma / tipo", "Tolerancia de carga", "Tiempo de descarga", "Descarga"], [22, 30, 32, 16]),
         "<h2>4. Recarga: requisitos de taller</h2>",
         "<ul><li>Recinto de polvo: humedad relativa <b>≤ 70 %</b> y extracción con <b>≥ 8 renovaciones por hora</b> "
         "(3.7).</li>"
         "<li>Polvo ABC: en la recarga anual debe ser <b>ABC estándar color gris</b> IRAM 3569 o superior (3.5.3.7); "
         "masa máxima de extinción IRAM 3672: gris 1,7 g · ABC 90 amarillo 1,2 g · BC rosado 1,8 g.</li>"
         "<li><b>Prohibido mezclar polvo ABC con BC</b>: la reacción puede hacer estallar el extintor (3.5.3.4). "
         "Polvo clase D: no debe humedecerse (3.5.3.6). No se convierte un extintor de un tipo a otro (3.5.4).</li>"
         "<li>Ensayo de pérdidas después de toda recarga (3.8). Reponer precintos con identificación y pasador de "
         "seguridad (3.11).</li>"
         "<li>Oblea o etiqueta firmemente adherida con: mes y año del próximo mantenimiento y recarga, mes y año de "
         "vencimiento de la PH, n° de serie y responsable inscripto (3.6.1); registro de trazabilidad (3.6.2).</li>"
         "<li><b>Disco marbete</b> de baquelita coloreada en su masa, entre válvula y recipiente, D interior 40 ó "
         "50 mm, 4 entallas radiales a 90° que rompan antes de 20 mm de deformación; color anual según tabla 1 "
         "(3.10, FL_SEN_04).</li>"
         "<li>Pintura: repintar si hay oxidación, metal a la vista, pérdida de brillo o color distinto (4.4; DOC-01).</li>"
         "<li><b>Inutilización</b> (4.5): retirar el agente, practicar <b>dos orificios de Ø ≥ 10 mm</b> en recipiente y "
         "cilindro expulsor, pintar <b>NO APTO</b> en amarillo y entregar nota con los motivos.</li></ul>",
         "<h2>5. Revisión 2020 (fuente secundaria S)</h2>",
         "<ul><li>Extintor de <b>reserva</b>: 10 % de la dotación, 40 mm inferiores pintados de verde con la leyenda "
         "EXTINTOR DE RESERVA. Extintor <b>sustituto</b>: 40 mm inferiores amarillos, leyenda EXTINTOR SUSTITUTO "
         "(FL_SEN_06).</li>"
         "<li>Vida útil: ABC 20 años como máximo; CO<sub>2</sub> de menos de 10 kg, 30 años.</li>"
         "<li>Matafuego de vehículo: mantenimiento sugerido cada 6 meses (el polvo se compacta).</li></ul>",
         "<h2>6. NFPA 10 (referencia)</h2>",
         "<p>Inspección mensual, mantenimiento anual, examen interno de polvo presurizado cada 6 años, PH cada 12 años "
         "(polvo, halogenados) y cada 5 años (CO<sub>2</sub>, agua, espuma, químico húmedo); solución AFFF premezclada "
         "cada 3 años. Ver DOC-04.</p>",
         FUENTES.replace("R = valor", "S = resumen publicado de IRAM 3517 (2020), a confirmar con el texto 2020 · R = valor")]
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
             ["Altura de la parte superior", "≤ 1,50 m para extintores de hasta 20 kg (IRAM 3517 rev. 2020, S)",
              "≤ 1,53 m (5 ft) si pesa ≤ 18,14 kg; ≤ 1,07 m (3,5 ft) si pesa más (§6.1.3.8.1-2)"],
             ["Separación al piso", "≥ 10 cm (IRAM 3517 rev. 2020, S)", "≥ 102 mm (4 in) (§6.1.3.8.3)"],
             ["Distancia de recorrido", "≤ 15 m de recorrido horizontal por piso (IRAM 3517-2 anexo A)",
              "clase A: 22,9 m (75 ft); clase B: 9,15 o 15,25 m (30 o 50 ft) según potencial"],
             ["Visibilidad", "chapa baliza y cartel", "visible, accesible, sin obstrucciones; señalizado si no se ve"],
         ], ["Tema", "IRAM / Argentina", "NFPA 10"], [24, 38, 38]),
         "<h2>5. Inspección, mantenimiento y prueba hidráulica</h2>",
         tabla([
             ["Inspección", "trimestral (IRAM 3517-2)", "mensual"],
             ["Mantenimiento", "anual", "anual"],
             ["Examen interno polvo presurizado", "en cada recarga / PH", "cada 6 años"],
             ["PH polvo y halogenados", "cada 5 años como máximo", "cada 12 años"],
             ["PH CO<sub>2</sub>", "cada 5 años", "cada 5 años"],
             ["PH agua, AFFF, acetato de potasio", "cada 2 años como máximo", "cada 5 años"],
             ["Agente agua / AFFF / sales K", "cambio anual", "AFFF premezclado: cada 3 años"],
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
