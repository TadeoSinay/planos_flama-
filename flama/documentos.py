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

FUENTES = ("<p class='nota'><b>Fuente:</b> C = catálogo FLAMA · N = norma citada (texto leído) · N* = norma hermana aplicada por analogía · "
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
             ["6", "Pintura en polvo", "<b>Poliéster</b> (TGIC-free, apto exterior) <b>rojo 03-1-050 de IRAM-DEF D 1054</b> "
              "(IRAM 3504 6.3; 3517-2:2020 7.2.2), acabado brillante (3517-2 9.10). Espesor seco <b>60 a 100 µm</b>.", "N / R"],
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
             ["Brillo y color", "ISO 2813 / ISO 7724", "rojo 03-1-050 (IRAM-DEF D 1054), brillante; ΔE ≤ 1,5 contra patrón", "cada lote", "N / R"],
             ["Niebla salina", "IRAM 121 / ISO 9227 (NSS)", "IRAM 3504 5.1.5: 96 h sin corrosión galvánica y recubrimiento adherido; 240 h sin corrosión del recipiente. FLAMA: <b>500 h</b>, ampollamiento 0(S0) ISO 4628-2; "
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
              "(3,5 MPa manuales; 4,0 MPa rodantes) mantenida <b>1 min</b> (IRAM 3517-2:2020 9.7.5.2): sin "
              "caída de presión, pérdidas ni deformación permanente visible; bomba ≥ 150 % de Pe y jaula", "100 %", "C / N"],
             ["R4", "Secado interior", "después de la PH, hasta que no se vea agua ni humedad condensada "
              "(IRAM 3517-2:2020 9.8.2, con cámara de inspección)", "100 %", "N"],
             ["R5", "Pintura", "espesor y adherencia según DOC-01", "por lote", "R"],
             ["R6", "Carga de agente", "pesada de polvo ABC gris IRAM 3569 con balanza calibrada; tolerancia "
              "<b>1 y 2,5 kg: 0/+100 g; 5 y 10 kg: 0/+300 g; rodantes: +3 %</b> (IRAM 3517-2:2020 tabla 3); recinto HR ≤ 70 % (9.4.8)",
              "100 %", "N"],
             ["R7", "Presurización", "N<sub>2</sub> seco a la presión de servicio (1,4 MPa a 20 °C); verificación con "
              "manómetro patrón; aguja del manómetro IRAM 3533 en zona verde", "100 %", "C / N"],
             ["R8", "<b>Estanqueidad</b>", "ensayo de verificación de pérdidas de propelente y agente (IRAM 3517-2:2020 9.4.10): "
              "inmersión o detector; control de presión a las 24 h (criterio FLAMA)", "100 %", "N / R"],
             ["R9", "Pesada final y marcado", "masa total dentro de la tolerancia; etiqueta, n° de serie, sello IRAM, "
              "fecha; precinto y seguro colocados", "100 %", "N / C"],
         ], ["N°", "Ensayo", "Método y criterio", "Frecuencia", "Fuente"], [5, 20, 55, 10, 10]),
         "<h3>3.2 Ensayos por lote (muestreo)</h3>",
         tabla([
             ["L1", "Rotura (destructivo)", "presurizar hasta 2 × la presión de PH sin fisuras ni pérdidas; luego hasta la rotura, sin "
              "desprendimiento de material; si rompe en una soldadura, ≥ 8 × Ps (criterio de IRAM 3504 5.1.4, norma "
              "hermana; confirmar en IRAM 3523/3550)", "1 por lote (IRAM 3504 7.1.4)", "N* / R"],
             ["L2", "Expansión volumétrica", "a la presión de PH con la válvula colocada: deformación permanente ≤ 10 % de la total (IRAM 3504 "
              "5.1.3, norma hermana); secado a 105 °C ± 2 °C", "10 % del lote (IRAM 3504 7.1.3)", "N* / R"],
             ["L3", "Descarga", "manuales: ≥ 8 s y ≥ 85 % descargado; rodantes: 25 kg ≥ 10 s, 50/70 kg ≥ 15 s, "
              "100 kg ≥ 30 s, ≥ 85 % (IRAM 3517-2:2020 tabla 3); alcance según catálogo", "1 por lote", "N / C"],
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


def _ph_recarga(m):
    """Presión de PH en la recarga según IRAM 3517-2:2020 9.7.3."""
    if m.familia == "co2":
        return "IRAM 2533"
    if m.familia == "rodante":
        return "4,0 (rodante)"
    return f"{2.5 * _ps(m):.1f}".replace(".", ",") + " (2,5 × Ps)"


def _intervalo_ph(m):
    return "2 años" if (m.familia == "inox" or "AFFF" in m.codigo) else "5 años"


def _vida(m):
    return "30" if m.familia == "co2" else "20"


def doc03():
    fil_ph = []
    for m in MODELOS:
        fil_ph.append([m.codigo.replace("FL_MAT_", ""), _e(m.spec["Presión de servicio (MPa)"]), _ph_recarga(m),
                       _e(m.spec["Presión de ensayo (MPa)"]), _intervalo_ph(m), _vida(m)])
    h = [cabecera("DOC-03", "Mantenimiento, recarga y prueba hidrostática", "Todos los modelos FLAMA"),
         "<h1>Control, mantenimiento y recarga por tipo de extintor</h1>",
         "<p>Base: <b>IRAM 3517-2:2020</b> (texto completo); se citan los apartados. Donde la edición 2005 "
         "difería se aclara. NFPA 10 como referencia internacional (punto 8).</p>",
         "<h2>1. Frecuencias</h2>",
         tabla([
             ["Control periódico", "4 veces por año a intervalos regulares (trimestral); <b>mensual</b> en riesgo "
              "grave, daño mecánico, temperaturas extremas, atmósferas corrosivas u ocupación de alto riesgo; no "
              "debe coincidir con el mantenimiento (salvo el mensual)", "8.2"],
             ["Mantenimiento", "como mínimo anual o cuando el control lo indique; vehículos: se recomienda "
              "semestral (el polvo se compacta)", "9.2.1"],
             ["Recarga", "después de usarlo, cuando lo indique un control o el mantenimiento", "9.2.2"],
             ["Agente agua, AFFF, agua pulverizada, sales de potasio", "reemplazo <b>anual</b>, previo lavado "
              "interior", "9.9.1.8 a 9.9.1.10, anexo E"],
             ["Gases limpios (HCFC/HFC)", "vaciado con recuperación y verificación cada 5 años como máximo; "
              "nunca a la atmósfera", "9.4.4"],
             ["Prueba hidrostática", "<b>5 años</b> máx.: polvo, CO<sub>2</sub>, gases limpios. <b>2 años</b> "
              "máx.: agua, AFFF, agua pulverizada, acetato de potasio. Su vencimiento no puede ser anterior al del "
              "próximo mantenimiento", "9.7.2, anexo E"],
             ["Mangueras con cierre controlado (rodantes) y de CO<sub>2</sub>", "PH <b>anual</b>", "9.7.1.4"],
             ["Vida útil máxima", "la de la norma de fabricación; anexo E: CO<sub>2</sub> 30 años (hasta 10 kg), "
              "demás tipos 20 años. Sin fecha de fabricación o adulterada: obsoleto", "9.11, anexo E"],
             ["Registro del PRS", "trazabilidad de insumos, procesos y propiedad durante <b>6 años</b>", "9.4.16"],
         ], ["Actividad", "Requisito", "Apartado"], [24, 62, 14]),
         "<h2>2. Prueba hidrostática (9.7)</h2>",
         "<ul><li><b>Presiones</b> (9.7.3): recipientes de baja presión: <b>2,5 × Ps</b>, excepto extintores "
         "<b>rodantes: 4 MPa</b>; cilindros de CO<sub>2</sub>: IRAM 2533 (y revisión según IRAM 2529-1). "
         "Mangueras con cierre controlado: 2 × Ps y nunca menos de 2,8 MPa; mangueras de CO<sub>2</sub>: "
         "12 MPa (tabla 5).</li>"
         "<li><b>Procedimiento</b> (9.7.5.2): quitar válvula y partes internas, eliminar el polvo, llenar con agua "
         "purgando el aire, dentro de jaula o detrás de defensa, subir a la presión de prueba y <b>mantener 1 min</b>. "
         "Satisfactorio si no hay caída de presión, rotura, pérdidas visibles ni deformaciones permanentes "
         "visibles. Mangueras: marcar los acoples, 1 min a presión, secar con aire a ≤ 65 °C (9.7.5.3).</li>"
         "<li><b>Equipo</b> (9.7.4, 4.4.1 a): bomba capaz de ≥ 150 % de la presión de ensayo con retención, "
         "conexión flexible y jaula; máquina según IRAM 2587 con medición de deformación permanente para alta "
         "presión, circuito cerrado de agua y pulmón de ≥ 5 L. Nunca presión neumática ni de gas (9.7.4.1).</li>"
         "<li><b>No se ensaya y se inutiliza</b> (9.7.1.3): reparaciones con soldadura o masilla, corrosión, "
         "extintor quemado, inoxidable con anticongelante de cloruro de calcio, obsoleto, o CO<sub>2</sub> que no "
         "cumpla IRAM 3509, 3565 y 2529-1.</li>"
         "<li><b>Registro</b> (9.7.7): en cilindros de CO<sub>2</sub> se acuña PH, mes y dos últimos dígitos del "
         "año y el logo del PRS. Mangueras: rótulo plástico ≥ 20 × 30 mm (FL_SEN_04).</li>"
         "<li><b>Secado</b> (9.8.2): todo lo que no sea a base de agua se seca y se inspecciona con cámara de "
         "video hasta no ver agua ni humedad condensada.</li></ul>",
         tabla(fil_ph, ["Modelo", "Ps (MPa)", "PH recarga (MPa)", "Pe fabricación (catálogo)", "PH cada",
                        "Vida útil (años)"], [20, 12, 22, 20, 12, 14]),
         "<h2>3. Condiciones de funcionamiento a garantizar (9.4.12, tabla 3)</h2>",
         tabla([
             ["3504 gases limpios", "1 y 2,5 kg: 0 / −2 % · 5 y 10 kg: 0 / −3 %", "mín. 8 s", "mín. 90 %"],
             ["3509 CO<sub>2</sub> manual", "0 / −5 %", "mín. 8 s", "mín. 80 %"],
             ["3523 polvo manual", "1 y 2,5 kg: 0 / +100 g · 5 y 10 kg: 0 / +300 g", "mín. 8 s", "mín. 85 %"],
             ["3525 agua manual", "± 3 %", "40 a 65 s", "mín. 95 %"],
             ["3527 AFFF manual", "± 3 %", "40 a 65 s", "mín. 85 %"],
             ["3541 AFFF rodante", "± 3 %", "50 L: 90 a 150 s", "mín. 95 %"],
             ["3550 polvo rodante", "± 3 %", "25 kg ≥ 10 s · 50 y 70 kg ≥ 15 s · 100 kg ≥ 30 s", "mín. 85 %"],
             ["3694 sales de potasio", "0 / +3 %", "mín. 30 s", "mín. 85 %"],
         ], ["Norma / tipo", "Tolerancia de carga", "Tiempo de descarga", "Descarga"], [22, 34, 30, 14]),
         "<h2>4. Recarga</h2>",
         "<ul><li><b>Gas impulsor</b> (9.4.9, tabla 2): polvo: nitrógeno seco; agua, AFFF y sales de potasio: "
         "nitrógeno seco o aire comprimido; gases limpios: nitrógeno seco o argón (HCFC Mezcla B: sólo argón).</li>"
         "<li><b>Agentes</b> (9.9, tabla 6): sólo los normalizados (AFFF IRAM 3515, polvos IRAM 3521/3566/3569, "
         "sales de potasio IRAM 3697, CO<sub>2</sub> IRAM 41170, gases IRAM 3526-0), con certificación. Prohibido "
         "cambiar de tipo de agente o convertir el extintor (9.9.1.3, 9.4.6). El polvo de un extintor accionado "
         "no se reutiliza (9.9.1.4).</li>"
         "<li><b>Prohibido mezclar polvo ABC con BC</b>: puede hacer estallar el extintor (9.9.1.6). Clase D: el "
         "polvo no debe humedecerse (9.9.1.7).</li>"
         "<li><b>Control del polvo</b> (9.9.3): ante dudas, ensayo de extinción IRAM 3672 (masa máxima: ABC "
         "estándar 1,7 g; ABC 90 amarillo 1,2 g; bicarbonato de potasio y urea 1,1 g; bicarbonato de potasio "
         "1,3 g; BC rosado 1,8 g) y ensayo de fusión IRAM 3569 para ABC. Cambio de polvo ABC de versión anterior "
         "de la IRAM 3569 cuando el último dígito del año de fabricación coincide con el del año del "
         "mantenimiento (9.9.4).</li>"
         "<li><b>CO<sub>2</sub></b> (9.9.1.11): fase vapor ≥ 99,5 %, agua ≤ 0,01 % en peso, aceite ≤ 10 ppm; "
         "dispositivo antirretroceso verificado (9.4.17); recuperación en circuito cerrado recomendada (9.4.18).</li>"
         "<li><b>Recinto de polvo</b> (9.4.8): todo el proceso desde la despresurización hasta el cierre y "
         "presurización (salvo PH y secado); HR ≤ 70 %, deshumidificación por condensación (<b>prohibido usar "
         "estufas</b>; el aire no debe estar más caliente que el polvo), extracción ≥ 8 renovaciones/h, sin "
         "salida de polvo; el ensayo de pérdidas con métodos que evaporen agua se hace fuera del recinto.</li>"
         "<li><b>Ensayo de pérdidas</b> después de todo mantenimiento o recarga (9.4.10). Reponer cada manguera "
         "en su propio extintor (9.4.11).</li>"
         "<li><b>Traba y precinto</b> (9.4.13): pasador de alambre Ø 2,5 a 3,5 mm; ojal que deje pasar un "
         "cilindro de Ø 30 mm; precinto con identificación del fabricante, del PRS y lote, que rompe entre 30 N "
         "y 90 N; no más de un enlazado (FL_SEN_08).</li>"
         "<li><b>Oblea</b> (9.4.14): próximo mantenimiento, n° de serie del recipiente, vencimiento de la PH y "
         "PRS. <b>Marbete</b> (9.6): entre válvula y cuello, color según el último dígito del año (tabla 4), "
         "D = 33, 36, 40 ó 50 mm (FL_SEN_08). Placa IRAM 3534 (9.4.15).</li>"
         "<li><b>Pintura</b> (9.10): si hay oxidación, metal a la vista, pérdida de brillo o color distinto; "
         "remover óxido y pintura mal adherida, desengrasar, color de la norma de fabricación, acabado "
         "brillante (DOC-01).</li>"
         "<li><b>Sales de potasio</b> (9.4.21): el recipiente debe ser de acero inoxidable según IRAM 3694; si "
         "no lo es, se inutiliza. Bases plásticas sin repuesto: inutilizar (9.4.7).</li></ul>",
         "<h2>5. Inutilización (9.12) y obsoletos (9.12.3)</h2>",
         "<p>Retirar el agente con disposición ambiental; recipiente y cilindro expulsor con <b>dos orificios de "
         "Ø ≥ 10 mm</b>; mangueras cortadas en dos; acta del anexo G al responsable. Obsoletos: soda-ácido, "
         "espuma química, tetracloruro de carbono o clorobromometano, no recargables de más de 5 años, a "
         "inversión, recipiente de cobre o latón, recipiente roblonado, operados con cilindro de gas.</p>",
         "<h2>6. Reserva y sustitutos</h2>",
         "<p>Reserva ≥ 10 % de la dotación mínima (mínimo un ABC 5 kg), faja verde ≤ 40 mm EXTINTOR DE RESERVA "
         "(5.3). Sustituto del PRS: faja amarilla ≤ 40 mm con leyendas y datos del PRS (9.4.5). Ver FL_SEN_06.</p>",
         "<h2>7. Diferencias con la edición 2005</h2>",
         "<p>2005: PH de rodantes a 2,5 × Ps (2020: 4 MPa); mangueras sólo con la PH del extintor (2020: anual); "
         "marbete sólo baquelita con colores por período y D 40/50 (2020: varios materiales, color por último "
         "dígito, D 33 a 50); etiqueta de control sin campo de frecuencia.</p>",
         "<h2>8. NFPA 10 (referencia)</h2>",
         "<p>Inspección mensual, mantenimiento anual, examen interno de polvo presurizado cada 6 años, PH cada 12 "
         "años (polvo, halogenados) y cada 5 años (CO<sub>2</sub>, agua, espuma, químico húmedo); solución AFFF "
         "premezclada cada 3 años. Ver DOC-04.</p>",
         FUENTES]
    return "".join(h)


# ------------------------------------------------------------------ DOC-05
def doc05():
    m = next(x for x in MODELOS if x.codigo == "FL_MAT_HCFC-HFC_5kg")
    ps = _ps(m)
    ph = max(2.5 * ps, 0.8)
    h = [cabecera("DOC-05", "Ensayos de fabricación - HCFC/HFC", "FL_MAT_HCFC-HFC_5kg (IRAM 3504)"),
         "<h1>Ensayos de fabricación del extintor de gases limpios</h1>",
         "<p>Base: <b>IRAM de Emergencia 3504:2001</b> (primera edición, vigencia de emergencia de un año; copia "
         "consultada con traducción parcial al portugués). <b>Confirmar con la edición vigente</b>. Los valores "
         "del catálogo FLAMA figuran como C.</p>",
         "<h2>1. Construcción</h2>",
         tabla([
             ["Recipiente", "acero al carbono ≥ 0,71 mm con recubrimiento anticorrosivo exterior (o aluminio "
              "6061/6063 ≥ 0,71 mm sin soldaduras, o inoxidable ≥ 0,63 mm)", "4.3.1"],
             ["Costuras", "acero: como máximo una longitudinal y dos transversales (sin contar cuello y "
              "accesorios), por proceso automático: arco sumergido, resistencia, atmósfera inerte o brazing", "4.3.2"],
             ["Fondo", "espesor en la zona de apoyo ≥ 1,5 × espesor real de la parte cilíndrica", "5.1.1"],
             ["Abertura", "roscada, diámetro interior ≥ 19 mm", "5.1.2"],
             ["Válvula", "descarga continua o intermitente; traba con precinto identificado; si se puede quitar "
              "bajo presión, despresurización con ≥ 3 filetes enroscados; rosca ≥ 4 filetes", "4.4"],
             ["Manguera", "≥ 350 mm (2,5 kg y mayores); PH a 2 × Ps sin pérdidas", "5.2"],
             ["Gas impulsor", "HCFC Mezcla B: argón; otros: argón o nitrógeno seco con punto de rocío ≤ −56,7 °C",
              "4.11"],
             ["Presión de servicio", f"&lt; 1,7 MPa (catálogo: {_e(m.spec['Presión de servicio (MPa)'])} MPa)",
              "5.6 / C"],
             ["Base", "extintores de 2,5 kg y mayores se mantienen parados en forma estable", "4.13"],
         ], ["Ítem", "Requisito", "Apartado"], [16, 72, 12]),
         "<h2>2. Ensayos</h2>",
         tabla([
             ["Estanqueidad y expansión (PH)", f"a la mayor de 1,5 × Pmáx de servicio, 2,5 × Ps o 0,8 MPa "
              f"(FLAMA: {ph:.1f} MPa; catálogo {_e(m.spec['Presión de ensayo (MPa)'])} MPa): sin pérdidas, fisuras "
              "ni roturas; deformación permanente ≤ 10 % de la total. Luego secado a 105 °C ± 2 °C".replace(".", ",", 1),
              "5.1.3 / 8.2", "10 % del lote"],
             ["Rotura", "a 2 × la presión de 5.1.3 sin fisuras ni pérdidas; hasta rotura sin desprendimiento de "
              "material; si rompe en una soldadura, a ≥ 8 × Ps", "5.1.4 / 8.3", "1 por lote"],
             ["Corrosión", "niebla salina (IRAM 121): 96 h sin corrosión galvánica y recubrimiento adherido; "
              "240 h: funciona y se recarga, recipiente sin corrosión", "5.1.5", "tipo"],
             ["Capacidad", "1 y 2,5 kg: 0 / −2 %; 5 y 10 kg: 0 / −3 % (balanza de 50 g)", "5.5 / 8.5", "rutina"],
             ["Funcionamiento continuo", "≥ 90 % de la carga en ≥ 8 s, acondicionado 16 h a 50 °C y a −20 °C",
              "5.8.1 / 8.8.2", "tipo"],
             ["Funcionamiento intermitente", "≥ 90 % descargado en pulsos de 2 s cada 10 s", "5.8.3 / 8.8.3", "tipo"],
             ["Caudal", "variación ≤ 10 % del valor medio de tres extintores", "5.8.4 / 8.8.4", "tipo"],
             ["Trato rudo", "3 caídas desde 0,9 m (hasta 2,5 kg) o 0,6 m (mayores): pérdida ≤ 10 % de Ps; traba "
              "liberable con ≤ 180 N; funciona y extingue", "5.9 / 8.9", "tipo"],
             ["Vibraciones", "10 a 60 Hz en tres ejes y 2 h en resonancia; luego funcionamiento y alcance",
              "5.7 / 8.7", "tipo"],
             ["Potencial extintor", "5 kg: 1 A y 5 B (tabla 2); 1 kg: 2 B; 2,5 kg: 1 A 3 B; 10 kg: 2 A 10 B",
              "5.12", "tipo"],
             ["Conductividad", "apto clase C: no conductor (IRAM 3544)", "5.13", "tipo"],
             ["Pérdidas", "inmersión, solución tensioactiva o detector de gases", "4.12 / 8.10", "100 %"],
             ["Plásticos", "envejecimiento 180 d a 100 °C y UV 720 h (ASTM G 153)", "anexo A", "tipo"],
         ], ["Ensayo", "Criterio", "Apartado", "Frecuencia"], [18, 58, 12, 12]),
         "<h2>3. Marcado</h2>",
         "<p>Fabricante, n° de recipiente y año grabados; placa IRAM 3534 con las leyendas de precaución por uso "
         "en espacios cerrados y de contenido bajo presión, y datos del gas y del impulsor según IRAM 3526. "
         "Color rojo 03-1-050 de IRAM-DEF D 1054 (salvo inoxidable) (6.1 a 6.3).</p>",
         "<h2>4. Inspección de lotes</h2>",
         "<p>10 % del lote a PH y expansión; si falla alguno, se ensaya el 100 %; lote rechazado si antes del 50 % "
         "falla más del 10 %. Rotura: un recipiente por lote. Extintor terminado: IRAM 15/18, nivel II, AQL 4 % "
         "(PH de manguera, funcionamiento, pérdidas) y 6,5 % (resto) (7.1 a 7.3).</p>",
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
             ["Cartel en altura", "tridimensional EXTINTOR + pictograma, caras ≥ 280 × 220, a 2,0-2,5 m (3517-2:2020 7.3, "
              "FL_SEN_02)", "OSHA / ANSI Z535; ISO 7010 F001 aceptado"],
             ["Chapa baliza", "350 (ó 260) × 870, franjas 100 mm a 45°, borde fotoluminiscente 15 mm, tipos de fuego, n° de puesto, datos del PRS (7.2, FL_SEN_01/07)", "no existe en NFPA 10"],
             ["Símbolos de clase", "contorno de color con letra + pictograma, colores IRAM-DEF D 1054 (7.2.2, FL_SEN_03)", "letra-forma rellena o pictogramas (Anexo B)"],
         ], ["Tema", "IRAM / Argentina", "NFPA 10 / EE. UU."], [24, 38, 38]),
         "<h2>4. Instalación</h2>",
         tabla([
             ["Altura de la parte superior", "≤ 1,5 m hasta 20 kg; ≤ 1,0 m si pesa más (3517-2:2020 6.2.14)",
              "≤ 1,53 m (5 ft) si pesa ≤ 18,14 kg; ≤ 1,07 m (3,5 ft) si pesa más (§6.1.3.8.1-2)"],
             ["Separación al piso", "≥ 0,10 m (6.2.14)", "≥ 102 mm (4 in) (§6.1.3.8.3)"],
             ["Distancia de recorrido", "≤ 20 m clase A, ≤ 15 m clase B, ≤ 3 m clase K; mínimo uno cada 200 m² (6.2.4, 6.2.5)",
              "clase A: 22,9 m (75 ft); clase B: 9,15 o 15,25 m (30 o 50 ft) según potencial"],
             ["Visibilidad", "chapa baliza y cartel", "visible, accesible, sin obstrucciones; señalizado si no se ve"],
         ], ["Tema", "IRAM / Argentina", "NFPA 10"], [24, 38, 38]),
         "<h2>5. Inspección, mantenimiento y prueba hidráulica</h2>",
         tabla([
             ["Control / inspección", "trimestral; mensual en alto riesgo (8.2)", "mensual"],
             ["Mantenimiento", "anual; vehículos: semestral recomendado (9.2.1)", "anual"],
             ["Examen interno polvo presurizado", "en cada mantenimiento con cámara (9.8.2)", "cada 6 años"],
             ["PH polvo y gases limpios", "5 años máx.; rodantes a 4 MPa (9.7)", "cada 12 años"],
             ["PH CO<sub>2</sub>", "cada 5 años", "cada 5 años"],
             ["PH agua, AFFF, acetato de potasio", "2 años máx. (anexo E)", "cada 5 años"],
             ["Agente agua / AFFF / sales K", "cambio anual (9.9.1.8-10)", "AFFF premezclado: cada 3 años"],
             ["Mangueras rodantes y CO<sub>2</sub>", "PH anual (9.7.1.4)", "PH con el cilindro"],
         ], ["Actividad", "IRAM", "NFPA 10"], [40, 30, 30]),
         "<p class='nota'>Los números de sección de NFPA 10 corresponden a la edición 2022; verificar contra la "
         "edición adoptada por la autoridad competente. Valores IRAM: IRAM 3517-2:2020 (apartados citados).</p>",
         FUENTES]
    return "".join(h)


DOCUMENTOS = [("DOC-01_Tratamiento_superficial_y_pintura", doc01),
              ("DOC-02_Ensayos_fabricacion_ABC", doc02),
              ("DOC-03_Ensayos_recarga_por_tipo", doc03),
              ("DOC-04_NFPA10_vs_IRAM", doc04),
              ("DOC-05_Ensayos_fabricacion_HCFC-HFC", doc05)]


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
