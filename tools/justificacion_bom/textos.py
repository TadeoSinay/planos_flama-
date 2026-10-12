"""Textos del Word «Justificación del BOM», armados con los números del Excel (para que no queden desfasados).
Las normas se citan por cláusula; no se transcriben."""


def f(x, d=2):
    """Número con coma decimal y sin ceros de más."""
    s = f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return s.rstrip("0").rstrip(",") if "," in s else s


def sg(x, d=1):
    """Porcentaje con signo: +4,5 % / −5,2 %."""
    return ("+" if x > 0 else "−" if x < 0 else "") + f(abs(x), d) + " %"


def notas(D):
    MO = D["modelos"]
    C = {x["codigo"]: x for x in D["cargas"]}
    M = {x["codigo"]: x for x in D["masas"]}
    R = {x["id"]: x for x in D["referencias"] if "id" in x}
    co2 = [MO[c] for c in MO if MO[c]["Ref. agente"] == "AG_CO2"]
    con_gas = [x for x in D["cargas"] if x["x"]["Ref. gas"]]
    dif_gas = max(abs(x.get("dif_real") or 0) for x in con_gas)
    ocup = sorted((x for x in MO.values() if x["Ocupa (%)"] is not None), key=lambda x: x["Ocupa (%)"])
    a1, a5 = MO["FL_MAT_ABC_1kg"], MO["FL_MAT_ABC_5kg"]
    k = MO["FL_MAT_SALESK_6l"]
    mk, m70, m1 = M["FL_MAT_SALESK_6l"], M["FL_MAT_ABC_70kg"], M["FL_MAT_ABC_1kg"]
    dentro5 = [x for x in D["masas"] if abs(x["dif"]) <= 5]
    en_banda = [x for x in D["masas"] if x["dentro"]]
    rk_carga = k["Carga objetivo"] * R["AG_K"]["valor"]
    tol_masas = [x["tol_p"] for x in D["masas"]]
    tol_mm = [x["tol_m"] for x in D["masas"]]
    n = {}

    n["intro"] = [
        "Este documento acompaña a FLAMA_BOM.xlsx: para cada número del BOM dice de dónde sale (norma, ficha del "
        "fabricante, plano o cálculo), cómo se controló y con qué tolerancia.",
        "El Excel está indexado. Todo dato de entrada está una sola vez en la hoja REFERENCIAS, con un ID y su fuente. "
        "La hoja MODELOS calcula la carga y el gas de cada extintor con fórmulas sobre esos datos. Las hojas del BOM "
        "toman de las dos por fórmula: si cambia un dato, cambia todo lo que depende de él.",
        "Cada valor obtenido tiene mínimo y máximo. Se ven con el «+» que está arriba de Volumen total y de Masa "
        "total; un segundo «+» abre el cálculo de la tolerancia.",
        "El BOM muestra sólo las partes de cada matafuego, cilindro y servicio. Los insumos de proceso (soldadura, "
        "granalla, pintura), el embalaje y la materia prima quedan en el libro de respaldo.",
        "Las normas se citan por cláusula y no se transcriben. Al final están las capturas marcadas de cada cláusula y "
        "de cada ficha usada. Donde la norma del equipo no estuvo a la vista (IRAM 3527, 3541, 3697, 3566 y 3533), el "
        "valor sale de la IRAM 3517-2, que los incluye en sus tablas, o de la ficha del fabricante, y se indica.",
    ]
    n["resumen"] = [
        ["Carga de cada extintor", f"Los {len(MO)} modelos llevan la carga objetivo dentro de la tolerancia de la "
         "tabla 3 de la IRAM 3517-2 (9.4.12). Si la tolerancia es sólo positiva, la carga va al centro de la banda."],
        ["Agente dentro del recipiente", f"Ocupa entre el {f(100 * ocup[0]['Ocupa (%)'], 0)} % y el "
         f"{f(100 * ocup[-1]['Ocupa (%)'], 0)} % del recipiente. El más justo es el "
         f"{ocup[-1]['Extintor'].replace('Extintor ', '')}, revendido y cargado por su fabricante."],
        ["Gas impulsor", "Cada tipo lleva el gas de la tabla 2 (9.4.9). La masa calculada como gas ideal difiere "
         f"menos de {f(dif_gas + 0.05, 1)} % de la del gas real."],
        ["CO₂", f"Relación de llenado de {' y '.join(f(x['Relación de llenado CO₂ (kg/L)'], 3) for x in co2)} kg/L, "
         f"por debajo de {f(R['RLL_CO2']['valor'])} kg/L (IRAM 2533:2004 7.9, tabla 1)."],
        ["Presión de servicio", "Los manuales de polvo quedan por debajo de 1,7 MPa (IRAM 3523 4.7) aun con la "
         "presión máxima de la zona verde."],
        ["Tolerancias", f"Banda de masa del extintor completo: de {sg(max(tol_mm))} a {sg(min(tol_mm))} hacia abajo "
         f"y de {sg(min(tol_masas))} a {sg(max(tol_masas))} hacia arriba. Sale de la tolerancia general de los planos "
         "(ISO 2768-m), del rango de densidad del material y de la banda de carga de la tabla 3."],
        ["Masa contra la referencia", f"{len(dentro5)} de {len(D['masas'])} modelos están a ±5 % de su referencia y "
         f"{len(en_banda)} la tienen dentro de su banda de tolerancia. Los demás se explican en la sección 7."],
        ["Recargas", "Los cuatro servicios de la IRAM 3517-2, con los intervalos del anexo E. La reposición de agente "
         "en el mantenimiento sale de la tabla 3."],
    ]
    n["carga_intro"] = (
        "La carga del BOM es la carga objetivo. Es la nominal cuando la tolerancia de la tabla 3 (9.4.12) es simétrica "
        "o sólo negativa. Cuando es sólo positiva (0 / +X) va al centro de la banda: así nunca queda por debajo de la "
        "nominal ni sale de la banda por la dispersión de la balanza. El mínimo y el máximo son los límites de la "
        "tabla 3. El volumen del agente se compara con el del recipiente (modelo 3D), con la densidad del BOM y con la "
        "mínima de la ficha.")
    n["carga"] = [
        "Polvo manual (IRAM 3523): 0 / +100 g hasta 2,5 kg y 0 / +300 g en 5 y 10 kg, igual a la tabla II de la "
        "IRAM 3523 (N15). Objetivo: +50 g y +150 g.",
        "Polvo sobre ruedas (IRAM 3550), agua y AFFF (IRAM 3525, 3527 y 3541): ±3 %, objetivo igual a la nominal. Las "
        "IRAM 3527 y 3541 no estuvieron a la vista; la tabla 3 de la IRAM 3517-2 las incluye con su tolerancia (N01).",
        f"Sales de potasio. La IRAM 3694 5.5 admite 6 L +0,3 / −0 en fabricación (+5 %, N17); la tabla 3 admite "
        f"0 / +3 % en servicio. El objetivo de {f(k['Carga objetivo'])} L (+1,5 %) cumple las dos.",
        "CO₂ (IRAM 3509): 0 / −5 %. Gases limpios (IRAM 3504): 0 / −3 %. Objetivo igual a la nominal.",
        "Clase D 9 l. La capacidad está en litros; con la densidad típica de 1,00 kg/L son 9 kg. La hoja del modelo lo "
        "encuadra en la IRAM 3523, así que lleva la banda de los manuales de polvo.",
        f"Polvo ABC. En el recipiente cuenta la densidad asentada (después del vibrado de la carga), no la aparente. "
        f"Con la aparente mínima de la ficha (0,85, F_ABC), el ABC 1 kg y el ABC 5 kg no entrarían sin vibrar: "
        f"ocuparían el {f(100 * a1['Ocupa con ρ aparente mín. (%)'], 0)} % y el "
        f"{f(100 * a5['Ocupa con ρ aparente mín. (%)'], 0)} % del recipiente. Con la asentada de 1,10 (NOM-104) ocupan "
        f"el {f(100 * a1['Ocupa (%)'], 0)} % y el {f(100 * a5['Ocupa (%)'], 0)} %. La IRAM 3569 no fija densidad: se "
        "exige una asentada de 1,10 o más en la orden de compra y se verifica con la descarga mínima del 85 % (N01).",
        f"BC 5 kg: ocupa el {f(100 * MO['FL_MAT_BC_5kg']['Ocupa (%)'], 0)} % con la densidad aparente típica. Con la "
        "asentada ocupa menos, pero ninguna ficha la da; con la mínima de la ficha no le quedaría volumen libre y el "
        "mínimo de gas da 0. Lo carga su fabricante; al recibirlo se pesa y se controla la presión.",
    ]
    n["gas_intro"] = (
        "Masa de gas: los moles que entran en el volumen libre a la presión de servicio absoluta y a 20 °C, "
        "m = (Ps + Patm) · V libre · M / (R · T). El volumen libre es el del recipiente menos el que ocupa el agente. "
        "Ps es la presión de servicio de la hoja de cada modelo: 1,4 MPa en polvo y 0,8 MPa en agua, AFFF, sales K y "
        "HCFC. Mínimo: presión de la zona verde −10 %, volumen libre con el agente más voluminoso y 22 °C. Máximo: "
        "+10 %, volumen libre con el agente más compacto y 18 °C (IRAM 3523 2.3: 20 ± 2 °C, N14).")
    n["gas"] = (
        f"Con la ecuación de estado real del gas, la masa difiere menos de {f(dif_gas + 0.05, 1)} % de la de gas "
        "ideal, así que el cálculo alcanza. Cada tipo lleva el gas que exige la tabla 2 (9.4.9, N02): nitrógeno seco en "
        "polvo, aire comprimido en agua y AFFF (la tabla admite nitrógeno o aire), nitrógeno en sales K y argón en el "
        "HCFC (la nota de la tabla 2 sólo admite argón para el HCFC Mezcla B). La tolerancia de ±10 % de la presión "
        "sale de la NOM-045-SCFI (México); la IRAM 3533, que fija la zona verde del manómetro, no estuvo a la vista "
        "(N15, N17).")
    n["co2"] = (
        f"La IRAM 2533 limita la masa de CO₂ a {f(R['RLL_CO2']['valor'])} kg por litro de cilindro para elementos "
        "contra incendio, hasta 65 °C (N16). Cumplen los dos: el de 2 kg queda al "
        f"{f(100 * co2[0]['Relación de llenado CO₂ (kg/L)'] / R['RLL_CO2']['valor'], 1)} % del límite y el de 5 kg al "
        f"{f(100 * co2[1]['Relación de llenado CO₂ (kg/L)'] / R['RLL_CO2']['valor'], 1)} %. La banda de la carga es "
        "0 / −5 % (tabla 3).")
    n["tol_intro"] = [
        "Piezas del modelo 3D. Los planos dan la tolerancia general ISO 2768-m (rótulo) para toda medida sin "
        "tolerancia propia. El volumen de una pieza cambia cuando todas sus caras se corren lo que permite esa "
        "tolerancia. Eso se mide con el espesor equivalente, 2 × volumen / superficie, que en una chapa es su "
        "espesor y en una pieza maciza es del orden de su medida menor. Tolerancia de volumen = tolerancia ISO 2768-m "
        "de ese espesor ÷ el espesor. En las piezas huecas modeladas macizas (manguera, resorte, caños) la superficie "
        "se cuenta por dentro y por fuera.",
        "Masa mínima y máxima de la pieza = volumen mínimo × densidad mínima y volumen máximo × densidad máxima del "
        "material (REFERENCIAS). Las chapas finas dominan: la de 1,25 mm con ±0,1 mm da ±8 %.",
        "Agentes: la banda de la tabla 3. Gas: la presión ±10 %, la temperatura de 20 ± 2 °C y el volumen libre "
        "con la banda de carga y el rango de densidad del agente.",
        "Las masas de un subconjunto o de un producto son la suma de las de sus piezas, y lo mismo sus mínimos y "
        "máximos: es el peor caso, porque supone que todas las piezas se van al mismo extremo.",
        "Por debajo de 0,5 mm la ISO 2768 no da tolerancia general (etiquetas y obleas): esas piezas sólo llevan el "
        "rango de densidad. Las piezas compradas sin masa declarada (manómetro, internos de válvula, tornillos) no "
        "suman.",
    ]
    n["masas_intro"] = (
        "Masa del extintor cargado = masa total del BOM sin el soporte, porque el peso cargado de catálogo y de los "
        "planos no lo incluye. La referencia es el plano Fadesa del mismo modelo; si no hay plano, la ficha del "
        "fabricante (capturas F07 a F13, F24 y F25). El catálogo Fadesa 3 va aparte porque repite pesos entre modelos. "
        "La última columna dice si la referencia cae dentro de la banda de tolerancia del BOM.")
    n["masas"] = [
        f"Dentro de la banda de tolerancia: {', '.join(x['nombre'].replace('Extintor ', '') for x in en_banda)}.",
        f"ABC 1 kg, {sg(m1['dif'])} contra el plano Fadesa (F07). El recipiente es de chapa de 1,25 mm y la carga "
        "objetivo suma 50 g. El plano Fadesa no desglosa la masa, así que la diferencia no se puede ubicar con más "
        "precisión. Se confirma pesando el primer lote.",
        f"Sales K, {sg(mk['dif'])} contra la ficha Melisam ({f(mk['ref'], 1)} kg, F25). El catálogo Fadesa "
        f"({f(mk['catalogo'], 2)} kg, F21) es imposible: la carga sola pesa {f(rk_carga, 2)} kg. La diferencia con "
        "Melisam está en el recipiente inoxidable Ø190 × 470 del plano Fadesa, cuyas medidas Melisam no publica.",
        f"ABC 70 kg, {sg(m70['dif'])} contra la ficha Georgia ({f(m70['ref'])} kg, F24). El catálogo "
        f"({f(m70['catalogo'])} kg) no es compatible con el recipiente Ø390 × 4,75 del proceso FLAMA de carros.",
        "AFFF 50 l, CO₂ 2 kg, CO₂ 5 kg y clase D son revendidos. El BOM los describe con el modelo 3D de su plano y su "
        "masa real es la del equipo que se compra. La diferencia no cambia ninguna compra, porque al MRP entra el "
        "equipo terminado.",
    ]
    n["sustituto_intro"] = (
        "Al final de cada producto, el bloque «Si va como sustituto, se agrega» lista lo que lleva ese mismo equipo "
        "cuando FLAMA lo presta mientras el del cliente está en servicio. El sustituto tiene que ser de igual "
        "clasificación y por lo menos igual capacidad (9.4.5, N07).")
    n["sustituto"] = [
        ["Faja amarilla en la pollera", "IRAM 3517-2 9.4.5 b)", "Alto máximo de 40 mm, con tres leyendas: que es "
         "sustituto, que reemplaza al equipo del puesto y los datos del prestador. Largo: perímetro + 20 mm de solape. "
         "Alto: 40 mm, o lo que deje libre la oblea PBA."],
        ["Tarjeta DPS «SUSTITUTO HABILITADO»", "Res. 349/07 art. 32", "Sólo en PBA."],
        ["Tarjeta AGC «Es sustituto»", "Res. AGC 32/15 anexo II", "Sólo en CABA, sin domicilio de instalación."],
        ["Remito de préstamo", "Práctica de mercado relevada", "Registra el número de extintor, el puesto, el equipo "
         "retirado y las fechas."],
    ]
    n["recargas_intro"] = (
        "La IRAM 3517-2 distingue cuatro servicios. En la hoja Recargas cada extintor tiene los cuatro, con lo que "
        "consume cada uno y su masa con mínimo y máximo. La prueba hidráulica se hace dentro de un mantenimiento: su "
        "bloque es lo que se agrega a ese mantenimiento, y su título lee el intervalo de REFERENCIAS.")
    n["servicios"] = [
        ["Control periódico", "Trimestral (mensual en los casos de 8.2)", "8.2 · 8.3.3.1 (N05)",
         "Etiqueta de control celeste de 35 × 50 (figura 7). No se abre el equipo."],
        ["Mantenimiento", "Anual (9.2.1)", "9.2.1 · anexo E · anexo F (N06, N03, N04, N13)",
         "Polvo y gases limpios: reposición de agente (de 0 a la cota de la tabla de abajo) y gas impulsor completo, "
         "porque se despresuriza para abrir. Agua, AFFF y sales K: carga nueva entera, porque el anexo E manda cambiarla "
         "cada año, y gas. CO₂: control de masa y reposición hasta la banda, sin retirar la válvula. En todos, la "
         "identificación de servicio."],
        ["Recarga", "Después de cada uso (9.2.2)", "9.2.2 · 9.9.1.4 (N06, N10)",
         "Carga objetivo entera de agente nuevo (el polvo de un equipo accionado no se reutiliza) y gas. CO₂: conjunto "
         "de seguridad nuevo en cada descarga (anexo E, N03). Identificación de servicio."],
        ["Prueba hidráulica", "Cada 5 años (polvo, CO₂, gases limpios) o 2 años (agua, AFFF, sales K)",
         "9.7 · anexo E (N03, N04)",
         "Polvo y gases: el agente recuperado en sistema cerrado (4.4.1 y) y z), N11) vuelve al equipo, y en el "
         "mantenimiento se repone la diferencia. Oblea de vencimiento de la prueba. CO₂: se vacía y se vuelve a cargar "
         "con el recuperado, con disco, marbete y junta nuevos, porque se retira la válvula."],
    ]
    n["identificacion"] = [
        ["Precinto con identificación del recargador", "IRAM 3517-2 9.4.13 (N08)", "Mantenimiento y recarga."],
        ["Marbete indicador (color del año, tabla 4)", "IRAM 3517-2 9.6 · anexo E (N09)",
         "Cada vez que se retira la válvula. En polvo, agua, AFFF, sales K y gases limpios, todos los años (anexo E); "
         "en CO₂, sólo en la prueba hidráulica (la recarga se hace por la válvula)."],
        ["Etiqueta de servicio (próximo mantenimiento, n° de serie, vencimiento de la prueba hidráulica, prestador)",
         "IRAM 3517-2 9.4.14 (N08)", "Mantenimiento y recarga."],
        ["Estampilla y oblea de recarga", "Res. OPDS 522/07", "Equipos de PBA."],
        ["Tarjeta de identificación DPS", "Res. 349/07 art. 21", "Equipos de PBA."],
        ["Tarjeta de identificación AGC", "Ord. 40.473 art. 6 · Res. AGC 32/15", "Equipos de CABA."],
        ["Junta tórica de asiento del cuello", "Buena práctica (se abre el equipo)",
         "Cada vez que se retira la válvula."],
        ["Oblea de vencimiento de la prueba hidráulica", "IRAM 3517-2 9.7 · Res. 349/07 art. 29",
         "Prueba hidráulica."],
    ]
    n["reposicion_intro"] = (
        "Ninguna norma da la merma de agente en el mantenimiento. El polvo y los gases limpios se recuperan en sistema "
        "cerrado (4.4.1 y) y z), N11). Los ensayos de control del polvo usan muestras de gramos (9.9.3, tabla 7, N12). "
        "El equipo vuelve a la carga correcta (anexo F, N13) dentro de la tabla 3. Lo más que puede faltar sin salir "
        "de la tabla 3 es la carga objetivo menos el límite inferior de la banda; si falta más, el anexo F lo trata como "
        "masa inadecuada y corresponde una recarga. Por eso la reposición va de 0 a esa diferencia (cota superior).")
    n["correcciones"] = [
        ["Relación de llenado máxima del CO₂", "0,667 kg/L", f"{f(R['RLL_CO2']['valor'])} kg/L",
         "Es el valor de la IRAM 2533:2004 7.9 tabla 1 (N16)."],
        ["Densidad del concentrado AFFF", "1,00 kg/L", f"{f(R['AG_AFFF_C']['valor'], 3)} kg/L",
         "Ficha DEMSA 203 MN (F_AFFF)."],
        ["Gas impulsor", "Con la carga nominal", "Con la carga objetivo",
         "Más polvo deja menos volumen libre: −9 % de gas en el ABC 5 kg."],
        ["Referencia del marbete", "9.4.14", "9.6 · anexo E", "La 9.4.14 es la etiqueta; el marbete es la 9.6."],
        ["Referencia de la etiqueta de servicio", "8.3.3", "9.4.14",
         "La 8.3.3 es la etiqueta celeste del control periódico."],
        ["Reposición de polvo y gases en el mantenimiento", "3 % fijo (sin fuente)",
         "De 0 a objetivo − límite inferior de la tabla 3", "Tabla 3 y anexo F (sección 9)."],
        ["Recargas", "Casos A/B/C", "Control, mantenimiento, recarga y prueba hidráulica",
         "Son los servicios de la IRAM 3517-2, con los intervalos del anexo E."],
        ["Peso de referencia del Sales K", "8,25 kg (catálogo)", f"{f(mk['ref'], 1)} kg (ficha Melisam)",
         "El valor del catálogo es menor que la carga sola."],
        ["Peso de referencia del ABC 70 kg", f"{f(m70['catalogo'])} kg (catálogo)", f"{f(m70['ref'])} kg (ficha Georgia)",
         "Recipiente Ø390 × 4,75."],
        ["BOM", "Valores fijos", "Fórmulas indexadas a REFERENCIAS y MODELOS, con mínimo y máximo",
         "Pedido de revisión: todo justificado y con tolerancia."],
    ]
    n["condiciones"] = [
        "Polvo ABC: densidad asentada de 1,10 kg/L o más en la orden de compra (la IRAM 3569 no la fija). Se controla "
        "con la descarga mínima del 85 % (tabla 3).",
        "Zona verde del manómetro: verificar los ±10 % adoptados (NOM-045-SCFI) con la IRAM 3533 o con la ficha del "
        "manómetro que se compre. Si cambia, se corrige una sola celda (PS_TOL en REFERENCIAS).",
        "Equipos revendidos (BC, clase D, CO₂, AFFF 50 l): al recibirlos se pesan y se controla la presión. Su masa "
        "real reemplaza la del BOM cuando llegue la ficha del modelo comprado.",
        "Primer lote del ABC 1 kg: pesar el recipiente para cerrar la diferencia con el plano Fadesa.",
        "IRAM 3527, 3541, 3697 y 3566: si se consiguen, verificar la tolerancia y el agente contra lo que dice este "
        "documento (hoy salen de la IRAM 3517-2 y de las fichas DEMSA).",
    ]
    return n
