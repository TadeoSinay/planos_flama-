"""Proveedores nacionales por ítem del BOM: principal y alternativa, con producto exacto, norma y respaldo.

Criterio (decisión FLAMA): sólo proveedores argentinos, cercanos o razonables para una planta en Avellaneda (PBA), que
vendan exactamente el ítem que pide el plano y cumplan la norma del producto. Los que ya cotizaron figuran con su
documento (ver validacion.DOCS) y el precio de referencia de la planilla de materias primas de FLAMA (MP-xx). El
resto quedó identificado con su producto exacto y se marca para cotizar.

Distancia: km por ruta desde Avellaneda centro, aproximados (aprox.).
Estado del ítem: COTIZADO = precio recibido y producto conforme · A COTIZAR = producto exacto identificado y conforme a
la norma (validado técnicamente), falta el precio · ESTIMADO = dato justificado por norma o fuente técnica, sin
confirmación del proveedor · A VALIDAR = el proveedor debe confirmar un punto técnico · NO CUMPLE / A DEFINIR = sin
proveedor nacional que tenga exactamente lo pedido, o en contradicción con la norma.
"""

# id: (razón social, rubro, domicilio, km aprox., contacto, certificación / norma, respaldo)
PROV = {
    "PACHECO": ("Pacheco Chapas", "Chapa y fleje LAF/LAC", "El Talar, Tigre (PBA)", 40, "-",
                "Origen Ternium; certificado de colada a pedido", "Q-PACHECO (PR-42021 / PR-42024)"),
    "PRADECON": ("Pradecon S.A.", "Chapa y bobina flejada LAF/LAC", "Garín, Escobar (PBA)", 55, "-",
                 "Bobinas de origen Ternium", "Q-PRADECON (173170 / 173195)"),
    "PARROTTA": ("Hierros Parrotta", "Chapa, hierros y redondos", "Av. Debenedetti 2851, Avellaneda", 3, "-",
                 "-", "Q-PARROTTA (00413329)"),
    "METALPRI": ("Metalpri / Prilux", "Caño con costura", "Nueva Pompeya, CABA", 8, "-", "-",
                 "Q-METALPRI (mail 09/09/2026)"),
    "MID": ("Comercial MID", "Caños", "Don Torcuato, Tigre (PBA)", 40, "-", "-", "Q-MID (27626)"),
    "CASEROS": ("Aceros Inoxidables Caseros", "Barras", "Caseros, Tres de Febrero (PBA)", 25, "-", "-",
                "Planilla MP-22 ($15.000/kg + IVA, barras de 6 m)"),
    "STOCCO": ("Stocco Hnos.", "Casquetes y tapas embutidas", "Calle 38 N° 4140, San Martín (PBA)", 25, "-",
               "Casquetes Ø340 a 6000 mm, e ≥ 3 mm", "Catálogo web (sin cotización)"),
    "CBACC": ("CB Accesorios", "Casquetes y accesorios para cañería (ASME)", "Nueva Pompeya, CABA", 8, "-",
              "Casquetes ASME B16.9 (medidas de cañería, no de recipiente)", "Catálogo web (sin cotización)"),
    "ELIMET": ("Eli-Met", "Mecanizado CNC bajo plano", "Albariño 2047, Mataderos, CABA", 15, "-", "-",
               "Planilla MP-20/21 (cupla M30 $5.261; cupla 2½\" $13.479 + IVA; 35-40 días)"),
    "CONARCO": ("Conarco (ESAB Argentina)", "Alambre macizo para MAG", "Venta por distribuidores de soldadura", None,
                "-", "AWS A5.18 ER70S-6", "Planilla MP-23/24 (sin cotizar)"),
    "AIRLIQ": ("Air Liquide Argentina - sucursal Piñeyro", "Gases industriales", "Tte. Cnel. Guiffra 799, Piñeyro, "
               "Avellaneda", 3, "0810-222-5272", "ARCAL 21 / ARCAL Speed EN ISO 14175 M20-ArC-8; N₂ ≥ 99,8 %",
               "Q-ARCAL · Q-N2 · planilla MP-25 ($8.800/m³ + acarreo) y MP-34 ($1.800/m³ + acarreo)"),
    "LINDE": ("Linde Argentina (ex Praxair)", "Gases industriales", "Red de sucursales GBA", None, "-",
              "Mezclas EN ISO 14175 M20; N₂ industrial", "Planilla MP-37 (sin cotizar)"),
    "CYM": ("CyM Materiales", "Granalla de acero", "GBA (cymba@cym.com.ar)", None, "cymba@cym.com.ar",
            "SAE J444 / ISO 11124-3", "Planilla MP-28 ($2.000/kg)"),
    "ROCA": ("Roca Ingeniería", "Granalla y equipos de granallado", "San Justo, La Matanza (PBA)", 20, "-",
             "SAE J444", "Web (sin cotización)"),
    "PRYMAX": ("Prymax", "Pintura en polvo al horno (servicio)", "Según presupuesto S00469", None, "-",
               "Pedir informe de niebla salina IRAM 121", "Q-PRYMAX (S00469)"),
    "PINTCARROS": ("Pintor de carros (cotización por mensaje)", "Pintura de rodantes (servicio)",
                   "Según cotización", None, "-", "Pedir informe de niebla salina IRAM 121 (3550 4.5: 240 h)",
                   "Q-CARROS"),
    "DEMSA": ("DEM S.A. (DEMSA)", "Agentes extintores", "Ruta 9 km 79, Campana (PBA)", 85, "-",
              "Sello IRAM 3569 (ABC) y BVQI", "L-DEMSA · L-DRAGO (potencial con DEM-60/90)"),
    "POLVEX": ("Polvex S.R.L. / Sancibrao", "Agentes y válvulas HZ (distribuidor)",
               "Boulogne Sur Mer 1813, Villa Maipú, San Martín (PBA)", 25, "11 4405-3382",
               "Polvo «según IRAM 3569» (sello no confirmado); válvulas HZ", "Q-AGENTES (lista de precios)"),
    "MOZART": ("Mozart S.R.L.", "Fabricante de extintores, válvulas y repuestos", "Ucrania 1564, Valentín Alsina, "
               "Lanús (PBA)", 9, "4218-3690", "Licencias IRAM de extintores y cilindros (2525/2526/2533, 3509, 3565)",
               "Web (sin cotización)"),
    "GEORGIA": ("Matafuegos Georgia - venta mayorista", "Fabricante de extintores y repuestos",
                "Gral. Manuel A. Rodríguez 2838, CABA", 15, "4585-4400 · ventas@matafuegosgeorgia.com",
                "Sello IRAM en sus extintores (fichas técnicas F1)", "Fichas técnicas (sin cotización de repuestos)"),
    "DRAGO": ("Drago (Luis Pasquinelli e Hijos S.A.)", "Fabricante de extintores", "Saladillo 1884, Castelar (PBA)",
              30, "-", "Licencias IRAM 3523, 3525, 3527, 3694, 3504, 3509", "L-DRAGO (licencias)"),
    "MELISAM": ("Melisam", "Fabricante de extintores", "Los Ceibos 428, San Isidro (PBA)", 30, "4766-6100",
                "Sello IRAM en sus extintores", "Fichas técnicas F2"),
    "PARPAL": ("Parpal S.R.L.", "Válvulas de latón forjado para extintores", "GBA", None, "-",
               "Válvulas M30 / M22", "Web (sin cotización)"),
    "RUEDAR": ("Ruedar", "Fábrica de ruedas industriales", "Paunero 557, Ciudad Madero, La Matanza (PBA)", 20, "-",
               "Goma maciza vulcanizada: Ø300 × 60 (M-1509, buje 20, 250 kg); Ø350 × 60 (buje 20/25/28, 150 kg)",
               "Catálogo web ruedar.com.ar (sin cotización)"),
    "ESCANORT": ("Escanort", "Ruedas y carros industriales", "GBA (escanort.com.ar)", None, "-",
                 "Ø400 × 100 neumática, rodamiento para eje 25, 200 kg (no maciza)",
                 "Catálogo web (sin cotización)"),
    "ASTUPRINT": ("Astuprint", "Etiquetas autoadhesivas industriales", "Tte. Cnel. Guiffra 970, Piñeyro, Avellaneda",
                  3, "-", "Vinilo / PP con laminado UV", "Web (sin cotización)"),
    "MULTILABEL": ("Multilabel", "Etiquetas autoadhesivas", "GBA", None, "-", "-", "Web (sin cotización)"),
    "SONFUERTES": ("SonFuertes (vía Papelera Damián)", "Precintos plásticos numerados y film", "GBA", None, "-",
                   "Numeración correlativa, color a pedido", "Web (sin cotización)"),
    "PRECINTER": ("Precinter", "Precintos de seguridad numerados", "GBA", None, "-", "-", "Web (sin cotización)"),
    "MAXIPACK": ("Maxipack", "Cajas de cartón corrugado a medida", "Aldecoa 953, Avellaneda", 3, "-",
                 "Corrugado simple / doble", "Web (sin cotización)"),
    "CARTOCAN": ("Cartocan", "Cajas de cartón corrugado", "La Rioja 1642, Avellaneda", 3, "-", "-",
                 "Web (sin cotización)"),
    "INDUSPALLETS": ("IndusPallets", "Pallets de madera", "Las Higueritas 548, Lanús Este (PBA)", 8, "-",
                     "1200 × 1000 (IRAM 10016)", "Web (sin cotización)"),
    "MVEMB": ("MV Embalajes", "Film stretch y embalaje", "CABA", 10, "-", "Film 23 µm × 500 mm pre-estirable",
              "Web (sin cotización)"),
    "EMBALPACK": ("Embalpack", "Film stretch y embalaje", "CABA", 10, "-", "-", "Web (sin cotización)"),
    "ARGENSOLD": ("Argensold", "O-rings y retenes", "GBA", None, "-", "NBR 70 Shore A", "Web (sin cotización)"),
    "WURTH": ("Würth Argentina", "Bulonería, tarugos y O-rings", "Sucursales GBA", None, "-", "-",
              "Web (sin cotización)"),
    "MAXISEG": ("Maxiseguridad", "Soportes y accesorios de extintores", "Munro, Vicente López (PBA)", 25, "-", "-",
                "Web (sin cotización)"),
    "CMREP": ("CM Representaciones", "Soportes y accesorios de extintores", "GBA", None, "-", "-",
              "Web (sin cotización)"),
    "GS1": ("GS1 Argentina", "Códigos GTIN 779", "CABA", 10, "-", "Estándar GS1", "Web"),
    "IRAM": ("IRAM - Instituto Argentino de Normalización", "Estampilla de conformidad", "Perú 552/556, CABA", 6, "-",
             "Anexo R (DC-PG-129)", "N-3523"),
    "DPS": ("Ministerio de Ambiente PBA (ex OPDS)", "Oblea y tarjetas DPS", "La Plata (PBA)", 55, "-",
            "Res. 522/07 · Res. 349/07", "N-349"),
    "AGC": ("Agencia Gubernamental de Control (CABA)", "Tarjeta AGC", "CABA", 6, "-", "Ord. 40.473 · Res. AGC 32/15",
            "N-AGC"),
}

# ítem: (descripción del ítem, producto exacto que se pide, principal, alternativa, estado, precio / cotización,
#        observación)
ITEMS = {
    # ---------------- acero y semielaborados
    "MP-HOJA-LAF": ("Chapa LAF del cuerpo 2,5 / 5 / 10 kg", "Recorte LAF IRAM-IAS U 500-05 e=1,25/1,6/2,0 a medida de "
                    "la hoja de corte", "PRADECON", "PACHECO", "COTIZADO",
                    "Planilla MP-02/03/04: USD 1,29 / 1,33 / 1,28 por kg (Pradecon)",
                    "Exigir certificado de colada en la OC"),
    "MP-HOJA-LAC": ("Chapa LAC del cuerpo rodantes", "Recorte LAC IRAM-IAS U 500-04 e=3,2 / 4,75, σf ≥ 265 MPa",
                    "PRADECON", "PACHECO", "COTIZADO", "Planilla MP-11/12: USD 1,10 / 1,09 por kg (Pradecon)",
                    "σf ≥ 265 MPa en el certificado (IRAM 3550 4.1.3.1)"),
    "MP-FLEJE": ("Fleje LAF de cúpula y fondo 1 a 10 kg", "Bobina flejada LAF e=0,9/1,25/1,6/2,0, ancho del plano",
                 "PACHECO", "PRADECON", "COTIZADO", "Planilla MP-05 a 10 y 13: USD 1,19-1,26 por kg",
                 "Pacheco flejes ≥ 1,25; Pradecon fleje 0,9 (1 kg)"),
    "MP-CANO": ("Caño del cuerpo 1 kg", "Caño c/costura ERW SAE 1010 Ø76,2 × 1,25, barra 6 m", "METALPRI", "MID",
                "COTIZADO", "Planilla MP-01 (Metalprisa)", "MID cotizó 2½\" × 2,6 (más pesado): alternativa con "
                "reserva; confirmar costura por resistencia (IRAM 3523 3.2.4.2 b)"),
    "MP-VARILLA": ("Varilla de refuerzo interior 70 / 100 kg", "Redondo liso SAE 1010 Ø8, barra 6 m (soldable con "
                   "ER70S-6)", "PARROTTA", "CASEROS", "ESTIMADO", "Planilla MP-22: $15.000/kg + IVA (Caseros)",
                   "Ø8 = propuesta de diseño (sin cálculo). Caseros cotizó como acero inoxidable: confirmar SAE 1010; "
                   "inoxidable no se suelda con ER70S-6"),
    "MP-CUELLO": ("Cuello roscado de manuales", "Asiento roscado SAE 1020 M22 (1 kg) / M30 × 1,5 (2,5-10 kg), "
                  "mecanizado bajo plano", "ELIMET", None, "A COTIZAR",
                  "Planilla MP-18/19: sin cotizar (Eli-Met cotizó la cupla M30 de carros)",
                  "Segundo tornero CNC a relevar"),
    "MP-CUPLA": ("Cupla soldable de rodantes", "Cupla SAE 1020 M30 × 1,5 (25/50 kg) / RBSP 2½\" (70/100 kg)",
                 "ELIMET", None, "COTIZADO", "Planilla MP-20/21: $5.261 / $13.479 c/u + IVA", "35-40 días"),
    "TAPA-ROD-G": ("Tapas (cúpula y fondo) 70 / 100 kg", "Casquete embutido toriesférico Ø350 / Ø390 × 4,75 LAC",
                   "STOCCO", "CBACC", "A COTIZAR", "Sin cotizar (planilla MP-17: tercerizado, importado)",
                   "Stocco embute desde Ø340 y e ≥ 3: cotizar con certificado de material. CB Accesorios vende "
                   "casquetes ASME de cañería: sólo si coincide el Ø"),
    "TAPA-ROD-C": ("Tapas (cúpula y fondo) 25 / 50 kg", "Casquete embutido Ø276 / Ø320 × 3,2 LAC", "STOCCO", "CBACC",
                   "NO CUMPLE / A DEFINIR", "Sin cotizar (planilla MP-15/16: importado)",
                   "Sin proveedor nacional en catálogo para Ø < 340: consultar a Stocco fuera de catálogo o "
                   "embutir en planta"),
    # ---------------- soldadura, superficie y pintura
    "C1": ("Alambre MAG", "ER70S-6 (AWS A5.18) Ø0,9 manuales / Ø1,2 rodantes, carrete 15 kg", "CONARCO", None,
           "A COTIZAR", "Planilla MP-23/24: sin cotizar", "Comprar al distribuidor de soldadura de zona sur"),
    "C2": ("Gas de protección MAG", "Arcal 21 / ARCAL Speed: Ar + 8 % CO₂ (EN ISO 14175 M20-ArC-8)", "AIRLIQ", "LINDE",
           "COTIZADO", "Planilla MP-25: $8.800/m³ + $1.000/m³ acarreo (batería 11 × 50 L)",
           "Decisión FLAMA: MAG 135; acreditar con el certificador (IRAM 3523 3.2.4.2 c)"),
    "C3": ("Granalla de acero", "S330 / S390 esférica alto C (SAE J444 / ISO 11124-3), bolsa 25 kg", "CYM", "ROCA",
           "COTIZADO", "Planilla MP-28: $2.000/kg", "-"),
    "C4M": ("Pintura de manuales (servicio)", "Pintura en polvo poliéster al horno, rojo 03-1-050, por cilindro",
            "PRYMAX", "PINTCARROS", "COTIZADO", "Q-PRYMAX (S00469, por unidad)",
            "Tercerización sujeta a aceptación del Ministerio (Res. 349/07 art. 18)"),
    "C4R": ("Pintura de rodantes (servicio)", "Preparación por quemado + pintura en polvo rojo 03-1-050, por carro",
            "PINTCARROS", "PRYMAX", "COTIZADO", "Q-CARROS (por carro)",
            "Tercerización sujeta a aceptación del Ministerio (Res. 349/07 art. 18)"),
    # ---------------- válvula y descarga
    "VALV-1": ("Válvula 1 kg", "Válvula HZ M-22 con tubo de pesca plástico", "POLVEX", "MOZART", "COTIZADO",
               "Planilla MP-42: $4.200 c/u", "Mozart fabrica válvulas con licencia IRAM: cotizar"),
    "VALV-M30": ("Válvula 2,5 a 10 kg", "Válvula HZ M-30 × 1,5 con resorte y tubo 7/8", "POLVEX", "MOZART",
                 "COTIZADO", "Planilla MP-43: $6.800 c/u", "Alternativa Parpal (latón forjado M30)"),
    "VALV-CARRO": ("Válvula de carro", "Válvula HZ de carro 25 kg (traba, manija, resorte) / 50-70-100 kg",
                   "POLVEX", "GEORGIA", "COTIZADO", "Planilla MP-44: $7.500 c/u", "-"),
    "MANOMETRO": ("Manómetro", "Manómetro con sello IRAM 3533, 1,4 MPa (rosca de la válvula)", "GEORGIA", "MOZART",
                  "A VALIDAR", "Planilla MP-45: sin cotizar", "Confirmar venta suelta con sello IRAM 3533"),
    "REP-VALV": ("Repuestos de válvula", "Manijas, eje, pasador, disco de seguridad de la válvula HZ", "POLVEX",
                 "MOZART", "A COTIZAR", "Q-AGENTES (válvula armada)", "Vienen con la válvula armada; sueltos sólo "
                 "para recarga"),
    "DESC-MAN": ("Manga y tobera de manuales", "Manguera EPDM/NBR trenzada ≥ 350 mm con racor + tobera (PH 2 × Ps)",
                 "GEORGIA", "MOZART", "A COTIZAR", "Planilla MP-48: sin cotizar", "Pedir ensayo de PH de la manga "
                 "(IRAM 3523 4.2)"),
    "DESC-ROD": ("Manga, lanza y válvula de rodantes", "Manguera armada 5 / 12 m + lanza o válvula esférica + tobera "
                 "campana", "GEORGIA", "MOZART", "A COTIZAR", "Planilla MP-49: sin cotizar", "-"),
    "ORING": ("Junta tórica", "O-ring NBR 70 Shore A, medida del cuello", "ARGENSOLD", "WURTH", "A COTIZAR",
              "Planilla MP-50: sin cotizar", "-"),
    # ---------------- carro (fabricación propia)
    "RUEDA-300": ("Rueda Ø300 (carro 25 kg)", "Rueda goma maciza Ø300 × 60, buje para eje Ø25", "RUEDAR", None,
                  "A VALIDAR", "Planilla MP-54: sin cotizar", "M-1509 de catálogo trae buje 20: pedir buje 25 o "
                  "rebajar puntas de eje"),
    "RUEDA-350": ("Rueda Ø350 (carros 50 / 70 kg)", "Rueda goma maciza Ø350 × 60, buje 25, 150 kg", "RUEDAR",
                  "ESCANORT", "A COTIZAR", "Planilla MP-54: sin cotizar", "150 kg por rueda > carga por rueda del "
                  "70 kg cargado (≈ 70 kg)"),
    "RUEDA-400": ("Rueda Ø400 (carro 100 kg)", "Rueda goma maciza Ø400, buje 25", "RUEDAR", "ESCANORT",
                  "NO CUMPLE / A DEFINIR", "Sin cotizar",
                  "No se halló Ø400 maciza nacional en catálogo; Escanort tiene Ø400 × 100 NEUMÁTICA (eje 25, 200 kg)"),
    "MP-EJE": ("Eje de ruedas", "Redondo SAE 1045 Ø25, barra 6 m", "PARROTTA", None, "A COTIZAR", "Sin cotizar",
               "Confirmar SAE 1045 con certificado"),
    "MP-CANO-CARRO": ("Caño del bastidor", "Caño SAE 1010 Ø25,4 × 1,6, barra 6 m", "METALPRI", "MID", "A COTIZAR",
                      "Sin cotizar (mismo proveedor que el caño del 1 kg)", "-"),
    "MP-PLANCHUELA": ("Planchuela de sunchos", "Planchuela SAE 1010 40 × 6, barra 6 m", "PARROTTA", None,
                      "A COTIZAR", "Sin cotizar", "-"),
    "MP-CHAPA-APOYO": ("Chapa del apoyo", "Chapa LAC e=3,2 (recorte de la hoja de rodantes)", "PRADECON", "PACHECO",
                       "COTIZADO", "Mismo material que la planilla MP-11", "-"),
    # ---------------- carga
    "POLVO-ABC": ("Polvo ABC", "Polvo ABC con Sello IRAM 3569, grado del modelo (DEM-60 / DEM-90), bolsa 25 kg",
                  "DEMSA", "POLVEX", "COTIZADO", "Lista Q-AGENTES (Sancibrao ABC 55/75/90)",
                  "DEMSA: sello IRAM 3569 y potencial de referencia (licencia Drago). Polvex: sello no confirmado; "
                  "con ese polvo el potencial sale del ensayo de tipo de FLAMA"),
    "N2": ("Nitrógeno seco", "N₂ ≥ 99,8 %, H₂O ≤ 40 ppm, batería 11 × 50 L 200 bar", "AIRLIQ", "LINDE", "COTIZADO",
           "Planilla MP-34: $1.800/m³ + $1.000/m³ acarreo", "-"),
    # ---------------- identificación
    "ETIQUETA": ("Etiqueta del extintor", "Vinilo autoadhesivo laminado UV, panel 108° + alas (hoja 4 del plano)",
                 "ASTUPRINT", "MULTILABEL", "A COTIZAR", "Planilla MP-56: sin cotizar", "-"),
    "ETIQ-SERIE": ("Etiqueta de serie GS1", "Poliéster autoadhesivo 45 × 25 con QR GS1 (GTIN 779)", "ASTUPRINT", "GS1",
                   "A COTIZAR", "Sin cotizar", "GS1 asigna los códigos; la imprenta imprime"),
    "FAJA": ("Faja de garantía", "Vinilo destructible rayado rojo-blanco 30 × 40", "ASTUPRINT", "MULTILABEL",
             "A COTIZAR", "Sin cotizar", "-"),
    "FAJA-SUS": ("Faja amarilla de sustituto", "Vinilo autoadhesivo amarillo, alto ≤ 40 mm, 3 leyendas",
                 "ASTUPRINT", "MULTILABEL", "A COTIZAR", "Sin cotizar", "IRAM 3517-2:2020 9.4.5"),
    "PRECINTO": ("Precinto de fábrica", "Precinto plástico numerado de color con «FLAMA»", "SONFUERTES", "PRECINTER",
                 "A COTIZAR", "Planilla MP-51: sin cotizar", "-"),
    "OBLEA-PBA": ("Oblea PBA", "Oblea oficial Ø46 (Res. 522/07)", "DPS", None, "COTIZADO", "Arancel oficial",
                  "Se adquiere al organismo"),
    "ESTAMPILLA": ("Estampilla IRAM", "Estampilla de conformidad (Anexo R)", "IRAM", None, "COTIZADO",
                   "Arancel de la licencia", "Se adquiere al organismo"),
    "TARJETA-AGC": ("Tarjeta AGC", "Tarjeta de dos módulos (papel con QR + etiqueta AGC)", "AGC", None, "COTIZADO",
                    "Arancel oficial", "Sólo destino CABA"),
    "TARJETA-DPS": ("Tarjeta DPS", "Tarjeta oficial DPS (Res. 349/07 art. 21 / 32)", "DPS", None, "COTIZADO",
                    "Arancel oficial", "Sólo PBA"),
    # ---------------- soporte y embalaje
    "SOPORTE": ("Soporte de pared / vehicular", "Soporte de chapa SAE 1010 pintado según FL_ACC_01 / 02",
                "MAXISEG", "CMREP", "A COTIZAR", "Planilla MP-52: sin cotizar", "-"),
    "TORNILLERIA": ("Tornillo y tarugo", "Tornillo M8 + tarugo nylon Ø10", "WURTH", None, "A COTIZAR", "Sin cotizar",
                    "-"),
    "CAJA": ("Caja de cartón corrugado", "Caja a medida del modelo (medida del plano), simple o doble", "MAXIPACK",
             "CARTOCAN", "A COTIZAR", "Planilla MP-59: $1.500 por caja 2,5-10 kg (evaluación económica)",
             "Ambos en Avellaneda"),
    "FUNDA": ("Funda y esquineros de rodantes", "Funda de PE + esquineros de cartón", "MVEMB", "EMBALPACK",
              "A COTIZAR", "Planilla MP-64: sin cotizar", "-"),
    "PALLET": ("Pallet", "Pallet de madera 1200 × 1000 (IRAM 10016)", "INDUSPALLETS", None, "A COTIZAR",
               "Planilla MP-60: sin cotizar", "-"),
    "FILM": ("Film stretch", "Film LLDPE 23 µm × 500 mm, pre-estirable 250 %", "MVEMB", "EMBALPACK", "A COTIZAR",
             "Planilla MP-63: sin cotizar", "-"),
    "ETIQ-PALLET": ("Etiqueta de pallet", "Papel térmico 100 × 150", "ASTUPRINT", "MULTILABEL", "A COTIZAR",
                    "Sin cotizar", "-"),
    "IMPRESOS": ("Impresos (instructivo, protocolo, remito)", "Impresión offset A5", "ASTUPRINT", None, "A COTIZAR",
                 "Sin cotizar", "-"),
    "TAPON": ("Tapón protector de rosca", "Tapón PE para M22 / M30 / RBSP 2½\"", None, None,
              "NO CUMPLE / A DEFINIR", "Planilla MP-62: inyectora local sin identificar",
              "Sin proveedor nacional identificado"),
    # ---------------- equipos revendidos (compra del equipo terminado)
    "EQ-CO2": ("Extintor de CO₂ terminado", "Extintor CO₂ con sello IRAM 3509 (cilindro IRAM 2533)", "MOZART",
               "GEORGIA", "A COTIZAR", "Sin cotizar", "Mozart: licencias de cilindros y extintores de CO₂"),
    "EQ-AGUA": ("Extintor de agua terminado", "Extintor de agua 10 L inoxidable con sello IRAM 3525", "GEORGIA",
                "DRAGO", "A COTIZAR", "Sin cotizar", "Drago: licencia IRAM 3525"),
    "EQ-AFFF": ("Extintor AFFF terminado", "Extintor AFFF con sello IRAM 3527 (manual) / 3541 (rodante)", "GEORGIA",
                "DRAGO", "A COTIZAR", "Sin cotizar", "Drago: licencia IRAM 3527 (10 L)"),
    "EQ-K": ("Extintor clase K terminado", "Extintor de acetato de potasio con sello IRAM 3694", "GEORGIA", "DRAGO",
             "A COTIZAR", "Sin cotizar", "Licencias 3694 de Drago y Georgia/Fadesa"),
    "EQ-HCFC": ("Extintor HCFC / HFC terminado", "Extintor de agente limpio con sello IRAM 3504", "GEORGIA", "MELISAM",
                "A COTIZAR", "Sin cotizar", "Drago también tiene licencia 3504"),
    "EQ-BC": ("Extintor BC terminado", "Extintor de polvo BC con sello IRAM 3523", "GEORGIA", "MELISAM", "A COTIZAR",
              "Sin cotizar", "-"),
    "EQ-D": ("Extintor clase D terminado", "Extintor de polvo clase D", "GEORGIA", "MELISAM", "A VALIDAR",
             "Sin cotizar", "Georgia: ficha de clase D 5 kg (otra capacidad: confirmar 9 L)"),
    # ---------------- recargas (agentes y gases de servicio)
    "REC-BC": ("Polvo BC para recarga", "Polvo BC bicarbonato de sodio con sello IRAM 3566, bolsa 25 kg", "POLVEX", "DEMSA",
               "COTIZADO", "Planilla MP-35: $2.505/kg (Polvex)", "Confirmar sello IRAM 3566 en la bolsa"),
    "REC-D": ("Polvo clase D para recarga", "Polvo NaCl para metales combustibles", "DEMSA", None, "A VALIDAR",
              "Planilla MP-36: sin cotizar", "DEMSA tiene hoja de seguridad de polvo D"),
    "REC-HCFC": ("Agente limpio para recarga", "HCFC-123 (Mezcla B) / HFC-236fa, IRAM 3526-1", None, None,
                 "NO CUMPLE / A DEFINIR", "Planilla MP-38: proveedor a definir", "Sin proveedor nacional identificado"),
    "REC-CO2": ("CO₂ para recarga", "CO₂ líquido grado industrial, cilindro con sifón 25-30 kg", "AIRLIQ", "LINDE",
                "A COTIZAR", "Planilla MP-37: pedido a Air Liquide, sin respuesta", "-"),
    "REC-AFFF": ("Concentrado AFFF para recarga", "AFFF 3 % (DEMSA 203 MN, IRAM 3515), bidón 20 L", "DEMSA", "POLVEX",
                 "COTIZADO", "Planilla MP-40: AFFF 3 % USD 7,32/L", "-"),
    "REC-K": ("Acetato de potasio para recarga", "Solución de acetato de potasio IRAM 3697 (Kitchen / Gastro K)",
              "POLVEX", "DEMSA", "COTIZADO", "Planilla MP-41: $4.468/L (bidón 10/20/30 L)", "-"),
    "ARGON": ("Argón de presurización", "Argón comprimido, cilindro 50 L 200 bar", "AIRLIQ", "LINDE", "A COTIZAR",
              "Planilla MP-39: sin cotizar", "-"),
    "MARBETE": ("Marbete de mantenimiento", "Anillo de color del año (IRAM 3517-2 9.4.14, fig. 9)", "ASTUPRINT",
                "MULTILABEL", "A COTIZAR", "Planilla MP-57: sin cotizar", "-"),
}

EQUIPO = {"co2": "EQ-CO2", "AGUA": "EQ-AGUA", "AFFF": "EQ-AFFF", "SALESK": "EQ-K", "HCFC-HFC": "EQ-HCFC",
          "BC": "EQ-BC", "CLASED": "EQ-D"}


def equipo(m):
    if m.familia == "co2":
        return "EQ-CO2"
    return EQUIPO[m.codigo.split("_")[2]]


def nombre(pid):
    return PROV[pid][0] if pid else "-"


def asignar(item):
    """(proveedor principal, alternativa, estado del proveedor) del ítem; ('', '', '') si no tiene."""
    if not item or item not in ITEMS:
        return "", "", ""
    it = ITEMS[item]
    return nombre(it[2]), nombre(it[3]), it[4]


def km(pid):
    k = PROV[pid][3]
    return f"≈ {k} km (aprox.)" if k else "a confirmar"
