"""Validación documental de materias primas, consumibles y componentes comprados del BOM.

Regla: ningún dato del BOM se acepta sin respaldo. Cada ítem cita el documento que lo respalda (cotización recibida,
ficha técnica del proveedor, licencia IRAM, plano de referencia, investigación de mercado FLAMA o norma). Lo que
ningún documento respalda NO se estima: queda «A VALIDAR» con el método para validarlo y sin cantidad inventada.

Documentos en el material entregado por FLAMA (carpetas INVESTIGACION PROVEEDORES, NORMAS, PLANOS FADESA, DEMSA,
CERTIFICACIONES DRAGO, GEORGIA, MELISAM). Las normas se citan por apartado; no se transcriben.
"""

DOCS = {
    "Q-PACHECO": ("Cotización Pacheco Chapas PR-42021 y PR-42024 (09/09/2026)",
                  "LAF 1,25 / 1,6 / 2,0 en rollos (fleje 200-300) y recortes 385×270, 330×475, 495×563; LAC 3,2 "
                  "recortes 490×858 y 640×994; LAC 4,75 recortes 1212×680 y 1212×900. Formulario: «Requiere "
                  "certificado: NO»."),
    "Q-PRADECON": ("Presupuestos Pradecon 173170 y 173195 (28/09/2026) + mail de ventas",
                   "Bobina flejada LAF 0,90 / 1,25 / 1,60 / 2,00 (C20-C14) y LAC 3,20 y 4,75; bobinas de origen "
                   "Ternium; las normas del material remiten a la web de Pradecon (ficha no adjunta)."),
    "Q-PARROTTA": ("Presupuesto Hierros Parrotta 00413329 (28/09/2026)",
                   "Chapa doble decapada N° 20/18/16/14 (0,9/1,2/1,6/2,0) y LAC 1/8\" y 3/16\" en hojas."),
    "Q-POLIMETAL": ("Cotización Polimetal (10/09/2026, descartada)",
                    "Recortes a medida 270×385×1,2; 330×475×1,6; 495×563×2; 490×858×3,2; 640×994×3,2; "
                    "680/900×1212×4,8."),
    "Q-METALPRI": ("Mail Metalpri / Prilux (09/09/2026)", "Caño c-c LF Ø76,2 × 0,90 y × 1,25 mm, barra de 6 m."),
    "Q-MID": ("Cotización Comercial MID 27626 (08/09/2026)", "Caño NGO BIS STD 2½\" 76 × 2,6 mm."),
    "Q-N2": ("Air Liquide, ficha técnica Nitrógeno V2.3 (2026)", "Pureza ≥ 99,8 %; H₂O ≤ 40 ppm; O₂ ≤ 100 ppm."),
    "Q-ARCAL": ("Air Liquide, ficha técnica ARCAL Speed V1.5 (2025)",
                "Ar + 8 % CO₂ (± 0,8), EN ISO 14175 M20-ArC-8, para soldadura MAG de aceros al carbono."),
    "Q-GETWELD": ("Cotización Getweld equipos de soldadura (18/09/2026)",
                  "MIG con 90 % Ar + 10 % CO₂ sobre SAE 1010 de 1,2-2,0 mm; velocidad 0-1500 mm/min."),
    "Q-AGENTES": ("Lista de precios de agentes y válvulas (2026)",
                  "Polvo ABC 55 / 75 / 90 (Sancibrao), BC Polvexi, acetato de potasio Gastro K, AFFF 3 % y 6 %; "
                  "válvulas HZ: M-22 1 kg c/tubo de pesca plástico, M-30 c/resorte y tubo 7/8 (2,5-5-10 kg), "
                  "carro 25 kg c/traba, manija y resorte, carro 50-70-100 kg."),
    "Q-PRYMAX": ("Presupuesto Prymax S00469 (18/09/2026)",
                 "Servicio de pintura en polvo al horno, rojo, por unidad: cilindros de 1 / 2,5 / 5 / 10 kg."),
    "Q-CARROS": ("Cotización servicio de pintura de carros (mensaje)", "Carro 25 / 50 / 70 / 100 kg por unidad."),
    "Q-YUKON": ("Fichas Yukon M-000200 (PH) y M-000150 (presurización)",
                "PH hasta 30 MPa con lectura de deformación; presurización con N₂ seco."),
    "I-FLAMA": ("Investigación de mercado FLAMA (Investigación mercado - maquinarias y MP.xlsx; Materias Primas.xlsx)",
                "Chapa LAF/LAC SAE 1010 de Ternium; tubo Ø76 para 1 kg; tapas de rodantes y cuello roscado "
                "tercerizados (Eli-Met); carro de rodantes comprado armado; varilla de refuerzo en 70/100 kg; "
                "alambre ER70S-6 AWS A5.18; granalla S330/S390 ISO 11124-3 / SAE J444; N₂ ≥ 99,9 % rocío "
                "< -40 °C; manómetro IRAM 3533; pintura de rodantes tercerizada por quemado (sin granalla)."),
    "R-FADESA": ("Planos Fadesa / Cautio SRL (2015-2017)",
                 "Material indicado «Acero IRAM 3523» / «Acero IRAM 3550»; recipientes 2,5-10 kg (G731-G733), "
                 "25 kg (G690), 50 kg (G689); válvula HZ en manuales; espesores 1,25 / 1,6 / 2,0 / 3,2."),
    "L-DEMSA": ("DEMSA: catálogo y hojas técnicas / HDS ABC 40-90, BC, Kitchen, AFFF",
                "Polvo ABC con Sello IRAM 3569 y BVQI; MAP nominal ± 5 %; relleno sulfato de amonio; densidad "
                "aparente > 0,85."),
    "L-DRAGO": ("Licencia IRAM 3523 Drago/Norbco (anexo I)",
                "Potencial por polvo: 1 kg DEM-60 1A-5B; 2,5 kg DEM-60 3A-20B; 5 kg DEM-60 6A-40B, DEM-90 10A-40B; "
                "10 kg DEM-60 6A-60B, DEM-90 10A-60B (otros polvos: Pyrochem)."),
    "N-3569": ("IRAM 3569:1996 (polvos ABC)",
               "La norma no fija el % de fosfato: la composición la declara el fabricante del polvo, con tolerancia "
               "± 10 % relativa (componentes < 50 %) o ± 5 % (> 50 %), y debe ser la del polvo calificado en el "
               "ensayo de potencial; color grisáceo (3.2); humedad ≤ 0,25 g/100 g; higroscopicidad ≤ 3."),
    "N-3523": ("IRAM 3523:1983", "3.2.1 a) material; 3.2.4 costuras y procesos; 3.3 válvula; 3.10 N₂ seco; "
               "4.1 recipiente; 4.2 manga; 4.5 manómetro; 5.1 marcado; 5.3 pintura."),
    "N-3550": ("IRAM 3550:1981", "3.2.1 material; 3.2.2 costuras; 3.11 pintura; 3.12 tren de rodaje; 4.1.2 "
               "soldadura; 4.1.3 espesor; 4.5 niebla salina."),
    "N-349": ("Res. 349/07 PBA (mod. 717/07)", "Art. 18 equipamiento mínimo del fabricante (cabina de pintura, niebla "
              "salina, etc.); art. 26 vida útil 20 años (CO₂ 30); art. 28-29 grabados en recarga y PH; art. 32 sustituto "
              "habilitado; art. 38 etiqueta de la bolsa de polvo con % mínimo de MAP; anexo IV cuño DPS 15 × 7."),
    "N-AGC": ("Res. AGC 32/15 (CABA) anexos I y II", "Tarjeta de dos módulos (papel con QR + etiqueta AGC); datos "
              "obligatorios (incluye vida útil); «Es sustituto»."),
    "N-3517": ("IRAM 3517-2:2020", "5.3 dotación de reserva (del cliente); 9.4.5 extintores sustitutos (faja amarilla ≤ 40 mm); tabla 2 gas impulsor; 9.4.13 precinto."),
}

ESTADOS = ("VALIDADA", "VALIDADA CON CONDICIÓN", "A VALIDAR", "NO CUMPLE / A DEFINIR")

# (rubro, ítem, especificación adoptada en el BOM, requisito normativo, respaldo, estado, acción para cerrar)
VALIDACION = [
    ("Acero", "Chapa del cuerpo 2,5 / 5 / 10 kg", "LAF e = 1,25 / 1,6 / 2,0 (Ternium); calidad IRAM-IAS U 500-05",
     "IRAM 3523 3.2.1 a): acero al C U 500-04/-05/-506, e ≥ 0,71, recubrimiento exterior", "Q-PACHECO · Q-PRADECON · "
     "Q-PARROTTA · R-FADESA · I-FLAMA", "VALIDADA CON CONDICIÓN",
     "Formato y espesor: cotizados. La calidad U 500-05 no figura en ningún documento (Pacheco: «Requiere certificado: "
     "NO»). Pedir en la OC el certificado de calidad de la colada (Ternium)."),
    ("Acero", "Fleje para cúpula y fondo 1 a 10 kg", "LAF e = 0,9 / 1,25 / 1,6 / 2,0 en bobina flejada",
     "IRAM 3523 3.2.1 a)", "Q-PACHECO · Q-PRADECON", "VALIDADA CON CONDICIÓN",
     "Ídem chapa: exigir certificado de colada."),
    ("Acero", "Cuerpo 1 kg", "Caño c-c LF Ø76,2 × 1,25, barra 6 m", "IRAM 3523 3.2.1 a) y 3.2.4.2 (costura "
     "automática: resistencia eléctrica)", "Q-METALPRI · I-FLAMA", "VALIDADA CON CONDICIÓN",
     "Confirmar con Metalpri que la costura es por resistencia eléctrica (ERW) y pedir certificado de material."),
    ("Acero", "Chapa del cuerpo rodantes", "LAC e = 3,2 (25 y 50 kg) / 4,75 (70 y 100 kg); IRAM-IAS U 500-04",
     "IRAM 3550 3.2.1; 4.1.3.1 fórmula; 4.1.3.2 mínimos 2,9 / 4,5 mm", "Q-PACHECO · Q-PRADECON · R-FADESA",
     "VALIDADA CON CONDICIÓN", "4,75 cumple el mínimo de 4,5 (Ø > 320). 50 kg con 3,2 (igual que Fadesa G689) cumple "
     "la fórmula sólo con σf ≥ 265 MPa: exigirlo en el certificado o pasar a 4,0."),
    ("Semielaborado", "Tapas (cúpula y fondo) de rodantes", "Casquetes embutidos tercerizados, e = chapa del cuerpo",
     "IRAM 3550 3.2.1 / 4.1.3", "I-FLAMA", "A VALIDAR", "Sin cotización: pedir a embutidor con certificado."),
    ("Semielaborado", "Cuello roscado", "Pieza mecanizada comprada (Eli-Met): M22×1,5 / M30×1,5 / RBSP 2½\"",
     "IRAM 3523 4.1.2 (Ø int. ≥ 19); IRAM 3550 4.1.5 (≥ 25 / 70); roscas IRAM 5058 / 5063", "I-FLAMA · R-FADESA",
     "A VALIDAR", "Sin cotización: pedir a Eli-Met con material y calibre de rosca."),
    ("Semielaborado", "Varilla de refuerzo interior 70 / 100 kg", "Barra de acero longitudinal (según investigación)",
     "—", "I-FLAMA", "NO CUMPLE / A DEFINIR", "Medida sin cálculo: definir por cálculo estructural antes de "
     "incluirla con cantidad."),
    ("Consumible", "Alambre de soldadura", "ER70S-6 Ø0,9/1,2 (AWS A5.18)", "IRAM 3523 3.2.4.2 / 3550 4.1.2",
     "I-FLAMA · Q-GETWELD", "VALIDADA CON CONDICIÓN", "Cantidad = metal depositado del plano; el rendimiento real "
     "(salpicaduras) se mide en la prueba de soldadura del proveedor del equipo."),
    ("Consumible", "Gas de protección", "Mezcla M20: Ar + 8 % CO₂ (ARCAL Speed) — Getweld especifica 90/10",
     "IRAM 3523 3.2.4.2 c) y 3550 3.2.2.2 c): «atmósfera inerte»", "Q-ARCAL · Q-GETWELD",
     "NO CUMPLE / A DEFINIR", "La mezcla con CO₂ es activa (MAG), no inerte. Confirmar con el certificador (IRAM / "
     "BV) o usar Ar puro (MIG 131). Caudal no documentado: medir en la prueba de soldadura."),
    ("Consumible", "Granalla", "S330 / S390 (ISO 11124-3, SAE J444) — sólo manuales; rodantes por quemado",
     "DOC-01 (Sa 2½ ISO 8501-1)", "I-FLAMA", "VALIDADA CON CONDICIÓN",
     "Especificación respaldada; consumo por unidad sin dato: pedir a CyM (ECO 100) / Airblast (G-100)."),
    ("Servicio", "Pintura", "Servicio tercerizado de pintura en polvo al horno, rojo 03-1-050, por unidad",
     "IRAM 3523 5.3 / IRAM 3550 3.11; niebla salina IRAM 121 (3550 4.5: 240 h)", "Q-PRYMAX · Q-CARROS · N-349",
     "VALIDADA CON CONDICIÓN", "Res. 349/07 art. 18 d) lista cabina y equipo de pintura en el equipamiento del "
     "fabricante; la tercerización (Prymax / pintor de carros) queda sujeta a la aceptación del Ministerio de Ambiente "
     "PBA (autoridad de aplicación) en la inscripción. Exigir informe de niebla salina IRAM 121 del pintor."),
    ("Agente", "Polvo ABC", "Polvo con Sello IRAM 3569 del grado elegido; composición = la declarada por su fabricante",
     "IRAM 3569 (tabla de requisitos); IRAM 3523 7.13 e)", "N-3569 · L-DEMSA · L-DRAGO · Q-AGENTES",
     "VALIDADA CON CONDICIÓN", "Con DEM-60 / DEM-90 hay potencial de referencia (licencia Drago). La lista cotizada es "
     "Sancibrao ABC 55 / 75 / 90: con ese polvo el potencial sale del ensayo de tipo de FLAMA (IRAM 3542 / 3543). "
     "La bolsa debe declarar el % mínimo de fosfato monoamónico (Res. 349/07 art. 38 k)."),
    ("Gas", "Nitrógeno de presurización", "N₂ ≥ 99,8 %, H₂O ≤ 40 ppm", "IRAM 3523 3.10 (N₂ seco); IRAM 3517-2 tabla 2",
     "Q-N2 · I-FLAMA", "VALIDADA", "—"),
    ("Componente", "Válvula", "Válvula HZ armada (M-22 1 kg; M-30 2,5-10 kg; carro 25 kg; carro 50-100 kg)",
     "IRAM 3523 3.3 / IRAM 3550 3.4", "Q-AGENTES · R-FADESA", "VALIDADA CON CONDICIÓN",
     "Confirmar con el proveedor qué trae el kit (lista: resorte y tubo de pesca; vástago y junta se asumen "
     "incluidos)."),
    ("Componente", "Manómetro", "Manómetro con sello IRAM 3533", "IRAM 3523 4.5", "I-FLAMA", "A VALIDAR",
     "Sin cotización ni ficha: cotizar (Georgia / repuestos)."),
    ("Componente", "Manga y tobera", "Manga de caucho + tobera", "IRAM 3523 4.2 (≥ 350 mm; PH 2 × Ps)", "I-FLAMA",
     "A VALIDAR", "Sin cotización: cotizar con ensayo de PH de la manga."),
    ("Componente", "Carro de rodantes", "Carro armado comprado (bastidor, eje, ruedas, sunchos)",
     "IRAM 3550 3.12 (tren de rodaje)", "I-FLAMA", "A VALIDAR", "Sin cotización: cotizar (Ruedar / Biston)."),
    ("Identificación", "Etiqueta, oblea, estampilla, tarjeta, precinto, faja",
     "Según hoja 4 de cada plano FL_MAT", "IRAM 3534; Anexo R; Res. 522/07; Ord. 40.473; IRAM 3517-2 9.4.13",
     "N-3517 · fotos de mercado", "VALIDADA CON CONDICIÓN", "Formato respaldado; proveedor de etiquetas a cotizar."),
    ("Embalaje", "Caja, pallet y film", "Caja a medida del modelo; pallet 1200 × 1000; film stretch", "—",
     "Plano (medidas)", "A VALIDAR", "Consumo de film por pallet: medir en la envolvedora EDOS PS5."),
]


def estado_de(item):
    for r in VALIDACION:
        if r[1] == item:
            return r[5]
    return "A VALIDAR"
