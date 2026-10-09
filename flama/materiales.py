"""Denominación, material y densidad de cada pieza; peso calculado.

El peso de la lista de materiales se calcula con el volumen del sólido 3D por la
densidad del material. Para piezas modeladas macizas pero que en la realidad son
huecas (manguera, caño de la manija del carro, cuerpo de la válvula esférica) se aplica el
factor de llenado indicado.

Los materiales que figuran en el catálogo de referencia se respetan (recipiente
de chapa de acero / acero inoxidable, válvula de latón forjado, manga de caucho
sintético, manómetro con sello IRAM 3533). El resto son los materiales de uso
corriente en la industria para cada componente; se consignan como especificación
de diseño FLAMA.
"""

# densidades (kg/dm³)
ACERO, INOX, LATON, ALUMINIO = 7.85, 7.93, 8.45, 2.70
CAUCHO, PP, PE, PVC = 1.20, 0.90, 0.95, 1.40

# clave: (denominación, material, densidad, factor de llenado, observaciones)
PIEZAS = {
    "cuerpo": ("Cuerpo (virola)", "Chapa acero SAE 1010", ACERO, 1.0, "costura longitudinal"),
    "cupula": ("Cúpula", "Chapa acero SAE 1010", ACERO, 1.0, "embutida"),
    "fondo": ("Fondo", "Chapa acero SAE 1010", ACERO, 1.0, "embutido"),
    "cuello": ("Cuello roscado", "Acero SAE 1010", ACERO, 1.0, None),
    "placas_refuerzo": ("Placas de refuerzo (2)", "Chapa LAC 4,75 curvada a Ø380", ACERO, 1.0,
                        "sobre la costura long."),
    "soldaduras": None,
    "cano_pesca": ("Caño de pesca (sifón)", "Tubo PVC rígido", PVC, 1.0, None),
    "filtro_pesca": ("Filtro del tubo de pesca", "Polipropileno perforado", PP, 0.6, "área ≥ 10 × boquilla"),
    "espiga": ("Espiga roscada", "Latón forjado", LATON, 1.0, None),
    "tuerca": ("Collarín de válvula", "Latón forjado", LATON, 1.0, None),
    "cuerpo_valvula": ("Cuerpo de válvula", "Latón forjado", LATON, 1.0, None),
    "vastago": ("Vástago", "Latón", LATON, 1.0, "con junta tórica"),
    "resorte": ("Resorte de válvula", "Alambre acero inox. AISI 302", INOX, 0.35, "cierre del vástago"),
    "eje": ("Eje de palanca", "Acero inox. AISI 304", INOX, 1.0, None),
    "manija_superior": ("Manija de accionamiento", "Chapa acero SAE 1010 pintada", ACERO, 1.0, None),
    "manija_inferior": ("Manija de transporte", "Chapa acero SAE 1010 pintada", ACERO, 1.0, None),
    "pasador": ("Pasador de seguridad", "Alambre acero inox. AISI 304", INOX, 1.0, "con precinto"),
    "manometro": ("Manómetro", "Comercial", None, 1.0, "sello IRAM 3533"),
    "disco_seguridad": ("Disco de seguridad", "Latón / disco de cobre", LATON, 1.0, "rotura 18 a 21 MPa"),
    "racor": ("Racor de manguera", "Latón", LATON, 1.0, None),
    "manguera": ("Manguera", "Caucho sintético", CAUCHO, 0.64, None),
    "tobera": ("Tobera", "Polipropileno", PP, 1.0, None),
    "lanza": ("Lanza", "Polipropileno", PP, 1.0, None),
    "empunadura": ("Empuñadura", "Polipropileno", PP, 1.0, None),
    "brazo_difusor": ("Brazo giratorio", "Tubo acero SAE 1010", ACERO, 0.45, None),
    "difusor": ("Difusor (bocina)", "Polietileno AD", PE, 1.0, "aislante térmico y eléctrico"),
    "suncho": ("Suncho portatobera", "Fleje acero SAE 1010 pintado", ACERO, 1.0, None),
    "pie": ("Pie de apoyo", "Polietileno AD", PE, 1.0, None),
    "rueda_der": ("Neumático macizo", "Caucho", CAUCHO, 1.0, None),
    "rueda_izq": None,
    "llanta_der": ("Llanta con cubo", "Chapa acero SAE 1010", ACERO, 1.0, None),
    "llanta_izq": None,
    "eje_ruedas": ("Eje de ruedas", "Barra acero SAE 1045 Ø25", ACERO, 1.0, "comprado"),
    "arandelas_tope": ("Arandelas de tope (4)", "Acero SAE 1010 Ø40 × Ø26 × 4", ACERO, 1.0, "compradas"),
    "soportes_eje": ("Soportes del eje (2)", "Chapa LAC del cuerpo (orilla)", ACERO, 1.0, "soldados al recipiente"),
    "manija_carro": ("Manija del carro", "Caño acero SAE 1010 Ø25,4×1,6", ACERO, 0.24, "soldada al recipiente"),
    "ganchos_manguera": ("Ganchos portamanguera (2)", "Chapa LAC del cuerpo (orilla) plegada", ACERO, 1.0,
                         "soldados al recipiente"),
    "tercera_pata": ("Tercera pata", "Chapa LAC del cuerpo (orilla) plegada", ACERO, 1.0, "soldada al fondo"),
    "manguera_enrollada": ("Manguera (tramo enrollado)", "Caucho sintético", CAUCHO, 0.64, None),
    "valvula_esferica": ("Válvula esférica", "Latón cromado", LATON, 0.45, None),
    "tobera_campana": ("Tobera campana", "Polipropileno", PP, 1.0, None),
    "etiqueta": ("Etiqueta / placa de características", "Vinilo autoadhesivo laminado", PVC, 1.0, "IRAM 3534"),
    "sello_iram": ("Estampilla IRAM de conformidad", "Provista por IRAM (Anexo R)", PVC, 1.0, "numerada"),
    "oblea_pba": ("Oblea de fabricación (PBA)", "Papel de seguridad autodestructible", PVC, 1.0, "Res. 522/07"),
    "junta_cuello": ("Junta tórica de asiento", "NBR 70 Shore A", CAUCHO, 1.0, "cambio c/recarga"),
    "precinto": ("Precinto de fábrica", "Polipropileno color", PP, 1.0, "id. FLAMA y lote"),
    "faja_garantia": ("Faja de garantía válvula-cuello", "Vinilo destructible rayado rojo/blanco", PVC, 1.0,
                      "nuevo sin abrir"),
    "tarjeta_caba": ("Tarjeta de identificación AGC (CABA)", "Etiqueta autoadhesiva emitida por la AGC", PVC, 1.0,
                     "sólo destino CABA"),
    "etiqueta_serie": ("Etiqueta de n° de serie GS1", "Poliéster autoadhesivo impreso térmico", PVC, 1.0, "QR GTIN + serie"),
}


def especificacion(m, clave):
    """(denominación, material, densidad, factor, obs) ajustada a la familia."""
    d = PIEZAS.get(clave)
    if d is None:
        return None
    nom, mat, rho, fac, obs = d
    g = m.geo
    if clave in ("cuerpo", "cupula", "fondo"):
        esp = {"cuerpo": g["t"], "cupula": g["td"], "fondo": g["tf"]}[clave]
        e = f"{esp:.2f}".rstrip("0").rstrip(".").replace(".", ",")
        if m.familia == "inox":
            mat, rho = f"Chapa acero inox. AISI 304 e={e}", INOX
        elif m.familia == "co2":
            mat = f"Tubo acero 34CrMo4 sin costura e={e}"
        elif m.familia == "rodante":
            mat = f"Chapa LAC IRAM-IAS U 500-04 e={e}"    # IRAM 3550 3.2.1; cotizada Pacheco/Pradecon
        elif clave == "cuerpo" and m.capacidad == "1 kg":
            mat = f"Caño c-c LF Ø76,2 e={e} (SAE 1010)"    # cotizado Metalpri
        else:
            mat = f"Chapa LAF IRAM-IAS U 500-05 e={e}"    # IRAM 3523 3.2.1 a); cotizada Pacheco/Pradecon
        if clave == "cuerpo":
            proc = m.soldadura
            obs = None if m.familia == "co2" else f"costura long. {proc[1]}"
    if clave == "cuerpo" and m.familia == "co2":
        nom, obs = "Cilindro sin costura", "cuello integral"
    if clave == "cuello":
        obs = g["cuello"][2].split(" (")[0]
        if m.familia == "inox":
            mat, rho = "Acero inox. AISI 304", INOX
    if clave == "cano_pesca" and m.familia == "co2":
        mat, rho = "Tubo aluminio", ALUMINIO
    if clave == "cano_pesca" and m.familia == "inox":
        mat, rho = "Tubo polipropileno", PP
    if clave == "lanza":
        nom = {"lanza_espuma": "Lanza espumígena", "lanza_espuma_rodante": "Lanza espumígena",
               "lanza_k": "Lanza aplicadora clase K", "lanza_d": "Lanza aplicadora flujo suave"}[m.descarga]
        if m.descarga == "lanza_d":
            mat, rho = "Tubo aluminio", ALUMINIO
        if m.descarga == "lanza_k":
            mat, rho = "Acero inox. AISI 304", INOX
            fac = 1.0
    if clave == "tobera":
        nom = {"tobera_chorro": "Tobera de chorro pleno", "tobera_1kg": "Tobera"}.get(m.descarga, "Tobera con portatobera")
    if clave == "manguera" and m.familia == "co2":
        mat = "Manga alta presión c/malla acero"
    if clave == "junta_cuello" and m.codigo == "FL_MAT_HCFC-HFC_5kg":
        mat = "EPDM (compatible con HCFC/HFC)"
    if clave == "suncho" and m.familia == "co2":
        nom = "Suncho soporte de difusor"
    if clave == "rueda_der":
        # IRAM 3550 3.12.1: ruedas metálicas revestidas de caucho o con cubierta neumática
        if float(m.spec.get("Diámetro de rueda (mm)", 0)) >= 400:
            nom, obs = "Rueda con cubierta neumática", "llanta metálica"
        else:
            obs = "llanta metálica"
    if clave in ("manija_superior", "manija_inferior") and not m.geo["cuello"][2].startswith("RBSP"):
        fac = 0.3       # chapa estampada en U (≈ 1,2 mm) representada maciza con el perfil Fadesa
    if clave == "manija_superior" and m.familia == "rodante" and m.geo["cuello"][2].startswith("RBSP"):
        nom, mat = "Palanca de accionamiento", "Planchuela acero SAE 1010 10 × 16 pintada"
    return nom, mat, rho, fac, obs


def peso(solido, rho, fac=1.0):
    """kg a partir del volumen del sólido (mm³)."""
    if rho is None:
        return None
    return solido.Volume() * 1e-6 * rho * fac
