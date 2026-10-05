"""Denominación, material y densidad de cada pieza; peso calculado.

El peso de la lista de materiales se calcula con el volumen del sólido 3D por la
densidad del material. Para piezas modeladas macizas pero que en la realidad son
huecas (manguera, caño del bastidor, cuerpo de la válvula esférica) se aplica el
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
    "soldaduras": None,
    "cano_pesca": ("Caño de pesca (sifón)", "Tubo PVC rígido", PVC, 1.0, None),
    "espiga": ("Espiga roscada", "Latón forjado", LATON, 1.0, None),
    "tuerca": ("Collarín de válvula", "Latón forjado", LATON, 1.0, None),
    "cuerpo_valvula": ("Cuerpo de válvula", "Latón forjado", LATON, 1.0, None),
    "vastago": ("Vástago", "Latón", LATON, 1.0, "con junta tórica"),
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
    "eje_ruedas": ("Eje de ruedas", "Acero SAE 1045", ACERO, 1.0, None),
    "bastidor": ("Bastidor", "Caño acero SAE 1010 Ø25,4×1,6", ACERO, 0.24, None),
    "sunchos_bastidor": ("Sunchos de fijación", "Planchuela acero SAE 1010", ACERO, 1.0, None),
    "apoyo": ("Apoyo delantero", "Chapa acero SAE 1010 plegada", ACERO, 0.20, None),
    "manguera_enrollada": ("Manguera (tramo enrollado)", "Caucho sintético", CAUCHO, 0.64, None),
    "soportes_manguera": ("Soporte de manguera", "Planchuela acero SAE 1010", ACERO, 1.0, None),
    "valvula_esferica": ("Válvula esférica", "Latón cromado", LATON, 0.45, None),
    "tobera_campana": ("Tobera campana", "Polipropileno", PP, 1.0, None),
    "etiqueta": ("Etiqueta de instrucciones", "Vinilo autoadhesivo laminado", PVC, 1.0, "rotulado"),
    "sello_iram": ("Sello IRAM de conformidad", "Oblea de seguridad autoadhesiva", PVC, 1.0, "marca IRAM"),
    "junta_cuello": ("Junta tórica de asiento", "NBR 70 Shore A", CAUCHO, 1.0, "cambio c/recarga"),
    "precinto": ("Precinto numerado", "Polipropileno", PP, 1.0, "30-50 N"),
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
        else:
            mat = f"Chapa acero SAE 1010 e={e}"
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
    return nom, mat, rho, fac, obs


def peso(solido, rho, fac=1.0):
    """kg a partir del volumen del sólido (mm³)."""
    if rho is None:
        return None
    return solido.Volume() * 1e-6 * rho * fac
