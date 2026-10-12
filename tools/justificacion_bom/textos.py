"""Textos del Word «Justificación del BOM», armados con los números de datos_bom.py (para que no queden desfasados).
Las normas se citan por cláusula; no se transcriben."""


def f(x, d=2):
    """Número con coma decimal y sin ceros de más."""
    s = f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return s.rstrip("0").rstrip(",") if "," in s else s


def sg(x, d=1):
    """Porcentaje con signo: +4,5 % / −5,2 %."""
    return ("+" if x > 0 else "−" if x < 0 else "") + f(abs(x), d) + " %"


def notas(D):
    C = {x["codigo"]: x for x in D["cargas"]}
    M = {x["codigo"]: x for x in D["masas"]}
    R = {x["codigo"]: x for x in D["recargas"]}
    con_aire = [x for x in D["cargas"] if x["agente"] != "CO2"]
    ocup = sorted(con_aire, key=lambda x: x["ocup"])
    dif_gas = max(abs(x["dif_real"] or 0) for x in con_aire)
    co2 = [x for x in D["cargas"] if x["agente"] == "CO2"]
    dentro = [x for x in D["masas"] if abs(x["dif"]) <= 5]
    fuera = [x for x in D["masas"] if abs(x["dif"]) > 5]
    gases_dif = max(abs(x["dif"]) for x in D["gases"])
    a1, a5 = C["FL_MAT_ABC_1kg"], C["FL_MAT_ABC_5kg"]
    k = C["FL_MAT_SALESK_6l"]
    mk, m70, m1 = M["FL_MAT_SALESK_6l"], M["FL_MAT_ABC_70kg"], M["FL_MAT_ABC_1kg"]
    rk = next(p for p in D["subconj"] if p["codigo"] == "FL_MAT_SALESK_6l")["partes"]
    rec_k = dict(rk)["Recipiente"]
    rec70 = next(c for c in D["cilindros"] if c["codigo"].endswith("ABC_70kg"))["masa"]
    rec1 = next(c for c in D["cilindros"] if c["codigo"].endswith("ABC_1kg"))["masa"]
    n = {}

    n["intro"] = [
        "Este documento acompaña a FLAMA_BOM.xlsx: para cada número del BOM dice de dónde sale (norma, ficha del "
        "fabricante, plano o cálculo) y cómo se controló.",
        "El BOM muestra sólo las partes de cada matafuego, cilindro y servicio. Los insumos de proceso (soldadura, "
        "granalla, pintura), el embalaje y la materia prima quedan en el libro de respaldo.",
        "Las normas se citan por cláusula y no se transcriben. Donde la norma del equipo no estuvo a la vista "
        "(IRAM 3527, 3541, 3697 y 3566), el valor sale de la IRAM 3517-2, que los incluye en sus tablas, o de la ficha "
        "del fabricante, y se indica.",
        "Lo que se corrigió en esta revisión está en la sección 8.",
    ]
    n["resumen"] = [
        ["Carga de cada extintor", f"Los {len(D['cargas'])} modelos dentro de la tolerancia de la tabla 3 de la IRAM "
         "3517-2 (9.4.12). Si la tolerancia es sólo positiva, la carga va al centro de la banda."],
        ["Agente dentro del recipiente", f"Ocupa entre {f(ocup[0]['ocup'], 0)} % y {f(ocup[-1]['ocup'], 0)} % del "
         f"recipiente. El más justo es el {ocup[-1]['nombre'].replace('Extintor ', '')}, revendido y cargado por su "
         "fabricante."],
        ["Gas impulsor", f"El de la tabla 2 (9.4.9) para cada tipo. La masa calculada como gas ideal difiere menos de "
         f"{f(dif_gas + 0.05, 1)} % de la del gas real."],
        ["CO₂", f"Relación de llenado de {' y '.join(f(x['rll'], 3) for x in co2)} kg/L, por debajo de "
         f"{f(D['rll_iram2533'])} kg/L (IRAM 2533:2004 7.9, tabla 1)."],
        ["Masa del extintor cargado", f"{len(dentro)} de {len(D['masas'])} modelos a ±5 % de su referencia. Los otros "
         f"{len(fuera)} se explican en la sección 5."],
        ["Sustituto", "La faja amarilla tiene 40 mm o menos en todos los modelos (9.4.5 b)). Las tarjetas DPS y AGC "
         "llevan la leyenda de sustituto."],
        ["Recargas", "Los cuatro servicios de la IRAM 3517-2, con los intervalos del anexo E. La reposición de agente "
         "en el mantenimiento sale de la tabla 3."],
    ]
    n["fuentes"] = [
        ["IRAM 3517-2:2020", "4.4.1 l), y), z): trasvase de CO₂ y recuperación cerrada de polvo y de gases limpios. "
         "8.2 y 8.3.3.1: control trimestral y etiqueta celeste de 35 × 50 (figura 7). 9.2.1 y 9.2.2: mantenimiento "
         "anual y recarga después de cada uso. 9.4.5: sustitutos. 9.4.9 tabla 2: gas impulsor. 9.4.12 tabla 3: "
         "tolerancia de carga. 9.4.13: precintos. 9.4.14: etiqueta de servicio. 9.6: marbete. 9.7 y anexo E: "
         "ensayo hidrostático, disco de seguridad, marbete y estado de carga por tipo. 9.9.1.4: el polvo de un equipo "
         "accionado no se reutiliza. 9.9.3 tabla 7: ensayos de control del polvo. Anexo F: recargar hasta la masa "
         "correcta."],
        ["IRAM 3523", "Tabla II: tolerancia de carga de fabricación de los manuales de polvo (la misma de la tabla 3)."],
        ["IRAM 3694", "5.5: capacidad de 6 L, +0,3 L / −0 (página 9, la única disponible)."],
        ["IRAM 2533:2004", "7.9 tabla 1: relación de llenado máxima del CO₂, 0,68 kg/L."],
        ["IRAM 41170", "Calidad del CO₂ de carga."],
        ["IRAM 3569 · IRAM 3515", "Polvo ABC con sello (la norma no fija densidad) · espumígeno AFFF al 3 %."],
        ["NOM-104-STPS-2001 (México)", "Densidad empacada del polvo ABC de fosfato monoamónico ≥ 1,10 kg/L "
         "(aparente ≥ 0,82)."],
        ["Fichas DEMSA", "Polvo ABC y BC (Púrpura K): aparente > 0,85 · polvo D: > 0,85 · Kitchen (acetato de "
         "potasio): 1,300 g/mL a 20 °C · 203 MN (AFFF): 1,025 g/cm³ a 20 °C."],
        ["Halotron I (HDS)", "HCFC Mezcla B: 1,48 kg/L a 25 °C."],
        ["Res. 349/07 (PBA)", "Art. 21: tarjeta DPS. Art. 28 y 29: fecha de servicio y de ensayo hidrostático en el "
         "tubo de pesca. Art. 32: sustituto habilitado."],
        ["Res. OPDS 522/07 (PBA)", "Estampilla y oblea de recarga."],
        ["Ord. 40.473 art. 6 · Res. AGC 32/15 (CABA)", "Tarjeta de identificación; anexo II: leyenda «Es sustituto»."],
        ["Planos Fadesa R1 · fichas Georgia y Melisam · catálogo Fadesa 3", "Masas de referencia (sección 5)."],
        ["Propiedades de los gases", "Masas molares y volumen molar normal de 22,414 L/mol. Para el control del gas "
         "real, ecuaciones de estado de referencia: N₂ (Span 2000), aire (Lemmon 2000), argón (Tegeler 1999)."],
    ]
    n["densidades"] = [
        f"Polvos. En el recipiente cuenta la densidad asentada (después del vibrado de la carga), no la aparente. Con "
        f"la aparente mínima de la ficha (0,85), el ABC 1 kg y el ABC 5 kg no entrarían: ocuparían el "
        f"{f(a1['ocup_peor'], 0)} % y el {f(a5['ocup_peor'], 0)} % del recipiente. Con la asentada de 1,10 (NOM-104) "
        f"ocupan el {f(a1['ocup'], 0)} % y el {f(a5['ocup'], 0)} %. La IRAM 3569 no fija densidad: se exige una "
        "asentada de 1,10 o más en la orden de compra. Se verifica con la descarga mínima del 85 % de la tabla 3.",
        "BC y clase D son revendidos: se usa la densidad típica de la ficha (0,90 y 1,00). Los carga el fabricante del "
        "equipo.",
        f"AFFF. Premezcla con 3 % de concentrado de {f(D['afff_conc'], 3)} kg/L: 0,03 × {f(D['afff_conc'], 3)} + 0,97 × "
        "1,000 = 1,0008 kg/L. En el BOM van por separado el concentrado, que se compra, y el agua.",
        f"Sales de potasio: 1,300 kg/L (ficha DEMSA Kitchen). Los {f(k['obj'])} L de carga pesan "
        f"{f(k['masa_ag'], 2)} kg.",
        "HCFC: 1,48 kg/L. Los 5 kg ocupan 3,38 L de los 6,0 L del recipiente.",
        "CO₂. Dentro del cilindro es líquido y vapor a la presión de saturación, así que no tiene un volumen propio. "
        "En la columna de densidad va la relación de llenado (kg de CO₂ por litro de cilindro), que es lo que limita "
        "la norma (sección 4).",
    ]
    n["gases"] = (f"Las masas molares redondeadas (28, 29 y 40 g/mol) dan la densidad normal con menos de "
                  f"{f(gases_dif + 0.05, 1)} % de diferencia. No cambian ningún número del BOM.")
    n["carga_intro"] = (
        "La carga del BOM es la carga objetivo. Es la nominal cuando la tolerancia de la tabla 3 (9.4.12) es simétrica "
        "o sólo negativa. Cuando es sólo positiva (0 / +X) va al centro de la banda: así nunca queda por debajo de la "
        "nominal ni sale de la banda por la dispersión de la balanza. El volumen del agente se compara con el del "
        "recipiente (modelo 3D).")
    n["carga"] = [
        "Polvo manual (IRAM 3523): 0 / +100 g hasta 2,5 kg y 0 / +300 g en 5 y 10 kg. Objetivo: +50 g y +150 g.",
        "Polvo sobre ruedas (IRAM 3550) y agua o AFFF (IRAM 3525, 3527 y 3541): ±3 %, objetivo igual a la nominal. "
        "Las IRAM 3527 y 3541 no estuvieron a la vista; la tabla 3 de la IRAM 3517-2 las incluye con su tolerancia.",
        f"Sales de potasio. La IRAM 3694 5.5 admite 6 L +0,3 / −0 en fabricación (+5 %); la tabla 3 admite 0 / +3 % "
        f"en servicio. El objetivo de {f(k['obj'])} L (+1,5 %) cumple las dos.",
        "CO₂ (IRAM 3509): 0 / −5 %. Gases limpios (IRAM 3504): 0 / −3 %. Objetivo igual a la nominal.",
        "Clase D 9 l. La capacidad está en litros; con la densidad típica de 1,00 kg/L son 9 kg. La hoja del modelo lo "
        "encuadra en la IRAM 3523, así que lleva la banda de los manuales de polvo.",
        f"El BC 5 kg ocupa el {f(C['FL_MAT_BC_5kg']['ocup'], 0)} % del recipiente con la densidad aparente típica. Con "
        "la asentada ocupa menos, pero no hay ficha que la dé. Lo carga su fabricante; al recibirlo se pesa y se "
        "controla la presión.",
    ]
    n["gas_intro"] = (
        "Masa de gas: son los moles que entran en el volumen libre a la presión de servicio absoluta y 20 °C. "
        "n = (Ps + 0,101 MPa) · V libre / (R · T) y m = n · M. El volumen libre es el del recipiente menos el que "
        "ocupa el agente. Ps es la presión de servicio de la hoja de cada modelo: 1,4 MPa en polvo y 0,8 MPa en agua, "
        "AFFF, sales K y HCFC. El resultado se compara con la densidad real del gas a esa presión y temperatura.")
    n["gas"] = (
        f"La diferencia con el gas real es menor que {f(dif_gas + 0.05, 1)} %, así que el cálculo como gas ideal "
        "alcanza. Cada tipo lleva el gas que exige la tabla 2 (9.4.9). Polvo: nitrógeno seco. Agua y AFFF: aire "
        "comprimido (la tabla admite nitrógeno o aire). Sales K: nitrógeno. HCFC: argón (la nota de la tabla 2 sólo "
        "admite argón para el HCFC Mezcla B).")
    n["co2"] = (
        f"La IRAM 2533 limita la masa de CO₂ a {f(D['rll_iram2533'])} kg por litro de cilindro, para que a 65 °C el "
        "cilindro no quede lleno de líquido. Cumplen los dos modelos: el de 2 kg queda al "
        f"{f(100 * co2[0]['rll'] / D['rll_iram2533'], 1)} % del límite y el de 5 kg al "
        f"{f(100 * co2[1]['rll'] / D['rll_iram2533'], 1)} %.")
    n["piezas_intro"] = (
        "Masa de cada pieza = volumen del sólido del modelo 3D (el mismo de los planos) × densidad del material × factor "
        "de llenado. Las medidas de cada pieza se justifican en «Justificación de medidas planos». La válvula HZ se "
        "compra armada: su masa es la suma de las piezas que trae. Los 70 y 100 kg llevan además dos placas de refuerzo.")
    n["masas_intro"] = (
        "Masa del extintor cargado = masa total del BOM sin el soporte, porque el peso cargado de catálogo y de los "
        "planos no lo incluye. La referencia es el plano Fadesa del mismo modelo; si no hay plano, la ficha del "
        "fabricante. El catálogo Fadesa 3 va aparte porque repite pesos entre modelos.")
    sal = [x for x in dentro]
    n["masas"] = [
        f"A ±5 % de su referencia: {', '.join(x['nombre'].replace('Extintor ', '') for x in sal)}.",
        f"ABC 1 kg, {sg(m1['dif'])} contra el plano Fadesa. El recipiente de chapa de 1,25 mm pesa {f(rec1, 2)} kg y "
        "la carga objetivo suma 50 g. El plano Fadesa no desglosa la masa, así que la diferencia no se puede ubicar "
        "con más precisión. Se confirma pesando el primer lote.",
        f"Sales K, {sg(mk['dif'])} contra la ficha Melisam ({f(mk['ref'], 1)} kg). El catálogo Fadesa "
        f"({f(mk['catalogo'], 2)} kg) es imposible: la carga sola pesa {f(k['masa_ag'], 2)} kg y el recipiente "
        f"inoxidable Ø190 × 470 del plano Fadesa, {f(rec_k, 2)} kg. La diferencia con Melisam está en el recipiente, "
        "cuyas medidas Melisam no publica.",
        f"ABC 70 kg, {sg(m70['dif'])} contra la ficha Georgia ({f(m70['ref'])} kg). El catálogo "
        f"({f(m70['catalogo'])} kg) no es compatible con el recipiente Ø390 × 4,75 del proceso FLAMA de carros, que "
        f"solo pesa {f(rec70, 1)} kg.",
        "AFFF 50 l, CO₂ 2 kg, CO₂ 5 kg y clase D son revendidos. El BOM los describe con el modelo 3D de su plano y su "
        "masa real es la del equipo que se compra. La diferencia no cambia ninguna compra, porque al MRP entra el "
        "equipo terminado.",
        "Las piezas compradas sin masa declarada (manómetro, internos de válvula, tornillos) no suman.",
    ]
    n["cilindros"] = ("Masa del recipiente solo: cuerpo, cúpula, fondo, cuello y, en los 70 y 100 kg, placas de "
                      "refuerzo. Es la misma del recipiente del extintor de igual tamaño.")
    n["sustituto_intro"] = (
        "Al final de cada producto, el bloque «Si va como sustituto, se agrega» lista lo que lleva ese mismo equipo "
        "cuando FLAMA lo presta mientras el del cliente está en servicio. El sustituto tiene que ser de igual "
        "clasificación y por lo menos igual capacidad (9.4.5).")
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
        "consume cada uno. El ensayo hidrostático se hace dentro de un mantenimiento: su bloque es lo que se agrega a "
        "ese mantenimiento.")
    n["servicios"] = [
        ["Control periódico", "Trimestral (mensual en los casos de 8.2)", "8.2 · 8.3.3.1",
         "Etiqueta de control celeste de 35 × 50 (figura 7). No se abre el equipo."],
        ["Mantenimiento", "Anual (9.2.1)", "9.2.1 · anexo E · anexo F",
         "Polvo y gases limpios: reposición de agente (tabla de abajo) y gas impulsor completo, porque se despresuriza "
         "para abrir. Agua, AFFF y sales K: carga nueva entera, porque el anexo E manda cambiarla cada año, y gas. "
         "CO₂: control de masa y reposición hasta la banda, sin retirar la válvula. En todos, la identificación de "
         "servicio."],
        ["Recarga", "Después de cada uso (9.2.2)", "9.2.2 · 9.9.1.4",
         "Carga objetivo entera de agente nuevo (el polvo de un equipo accionado no se reutiliza) y gas. CO₂: conjunto "
         "de seguridad nuevo en cada descarga (anexo E). Identificación de servicio."],
        ["Ensayo hidrostático", "Cada 5 años (polvo, CO₂, gases limpios) o 2 años (agua, AFFF, sales K)", "9.7 · anexo E",
         "Polvo y gases: el agente recuperado en sistema cerrado (4.4.1 y) y z)) vuelve al equipo, y en el "
         "mantenimiento se repone la diferencia. Oblea de vencimiento del ensayo. CO₂: se vacía y se vuelve a cargar "
         "con el recuperado, con disco, marbete y junta nuevos, porque se retira la válvula."],
    ]
    n["identificacion"] = [
        ["Precinto con identificación del recargador", "IRAM 3517-2 9.4.13", "Mantenimiento y recarga."],
        ["Marbete indicador (color del año, tabla 4)", "IRAM 3517-2 9.6 · anexo E",
         "Cada vez que se retira la válvula. En polvo, agua, AFFF, sales K y gases limpios, todos los años (anexo E); "
         "en CO₂, sólo en el ensayo hidrostático (la recarga se hace por la válvula)."],
        ["Etiqueta de servicio (próximo mantenimiento, n° de serie, vencimiento PH, prestador)", "IRAM 3517-2 9.4.14",
         "Mantenimiento y recarga."],
        ["Estampilla y oblea de recarga", "Res. OPDS 522/07", "Equipos de PBA."],
        ["Tarjeta de identificación DPS", "Res. 349/07 art. 21", "Equipos de PBA."],
        ["Tarjeta de identificación AGC", "Ord. 40.473 art. 6 · Res. AGC 32/15", "Equipos de CABA."],
        ["Junta tórica de asiento del cuello", "Buena práctica (se abre el equipo)",
         "Cada vez que se retira la válvula."],
        ["Oblea de vencimiento de la prueba hidráulica", "IRAM 3517-2 9.7 · Res. 349/07 art. 29",
         "Ensayo hidrostático."],
    ]
    n["reposicion_intro"] = (
        "Ninguna norma da la merma de agente en el mantenimiento. El polvo y los gases limpios se recuperan en sistema "
        "cerrado (4.4.1 y) y z)). Los ensayos de control del polvo usan muestras de gramos (9.9.3, tabla 7). El equipo "
        "vuelve a la carga correcta (anexo F) dentro de la tabla 3. Lo más que puede faltar sin salir de la tabla 3 es "
        "la carga objetivo menos el límite inferior de la banda. Si falta más, el anexo F lo trata como masa "
        "inadecuada y corresponde una recarga. Esa diferencia se toma como reposición: es una cota superior.")
    r10, r25 = R["FL_MAT_ABC_10kg"], R["FL_MAT_ABC_25kg"]
    n["recargas"] = [
        f"Polvo manual: 50 g hasta 2,5 kg y 150 g en 5 y 10 kg (del 5 % en el de 1 kg al {f(r10['rep_pct'], 1)} % en "
        f"el de 10 kg). Polvo sobre ruedas: {f(r25['rep_pct'], 0)} %. CO₂: 5 %. HCFC: 3 %.",
        "La estimación anterior era un 3 % fijo, sin fuente. Con la tabla 3 queda igual en " +
        ", ".join(x["nombre"].replace("Extintor ", "") for x in D["recargas"] if x["rep"] is not None and
                  x["agente_polvo"] and abs(x["rep_pct"] - 3) < 0.05) + "; mayor en " +
        ", ".join(f"{x['nombre'].replace('Extintor ', '')} ({f(x['rep_pct'], 1)} %)" for x in D["recargas"]
                  if x["rep"] is not None and x["agente_polvo"] and x["rep_pct"] > 3.05) + "; menor en " +
        ", ".join(f"{x['nombre'].replace('Extintor ', '')} ({f(x['rep_pct'], 1)} %)" for x in D["recargas"]
                  if x["rep"] is not None and x["agente_polvo"] and x["rep_pct"] < 2.95) + ".",
        "El gas impulsor se repone entero en cada mantenimiento y recarga: para abrir el equipo hay que "
        "despresurizarlo. El de cada modelo es el de la sección 4.",
    ]
    n["correcciones"] = [
        ["Relación de llenado máxima del CO₂", "0,667 kg/L", f"{f(D['rll_iram2533'])} kg/L",
         "Es el valor de la IRAM 2533:2004 7.9 tabla 1. Los dos modelos cumplen."],
        ["Densidad del concentrado AFFF", "1,00 kg/L", f"{f(D['afff_conc'], 3)} kg/L",
         "Ficha DEMSA 203 MN. Cambia la masa del concentrado (+2,5 %)."],
        ["Referencia del marbete", "9.4.14", "9.6 · anexo E", "La 9.4.14 es la etiqueta; el marbete es la 9.6."],
        ["Referencia de la etiqueta de servicio", "8.3.3", "9.4.14",
         "La 8.3.3 es la etiqueta celeste del control periódico."],
        ["Reposición de polvo y gases en el mantenimiento", "3 % fijo (sin fuente)",
         "Objetivo − límite inferior de la tabla 3", "Sale de la tabla 3 y del anexo F (sección 7)."],
        ["Recargas", "Casos A/B/C", "Control, mantenimiento, recarga y ensayo hidrostático",
         "Son los servicios de la IRAM 3517-2, con los intervalos del anexo E."],
        ["Peso de referencia del Sales K", "8,25 kg (catálogo)", f"{f(mk['ref'], 1)} kg (ficha Melisam)",
         "El valor del catálogo es menor que la carga sola."],
        ["Peso de referencia del ABC 70 kg", f"{f(m70['catalogo'])} kg (catálogo)", f"{f(m70['ref'])} kg (ficha Georgia)",
         "Recipiente Ø390 × 4,75."],
    ]
    n["condiciones"] = [
        "Polvo ABC: densidad asentada de 1,10 kg/L o más en la orden de compra (la IRAM 3569 no la fija). Se controla "
        "con la descarga mínima del 85 % (tabla 3).",
        "Equipos revendidos (BC, clase D, CO₂, AFFF 50 l): al recibirlos se pesan y se controla la presión. Su masa "
        "real reemplaza la del BOM cuando llegue la ficha del modelo comprado.",
        "Primer lote del ABC 1 kg: pesar el recipiente para cerrar la diferencia con el plano Fadesa.",
        "IRAM 3527, 3541, 3697 y 3566: si se consiguen, verificar la tolerancia y el agente contra lo que dice este "
        "documento (hoy salen de la IRAM 3517-2 y de las fichas DEMSA).",
    ]
    return n
