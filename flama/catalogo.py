"""Catálogo técnico de la línea de extintores FLAMA S.A.

Los valores de "Especificaciones" (capacidad, peso cargado, altura, ancho,
profundidad, tiempo de descarga, alcance, rango de temperatura, presiones y
normas IRAM) se transcriben literalmente de las tablas del catálogo de
referencia (Fadesa, "Catálogo 3"), página indicada en `fuente`.

Los parámetros geométricos de recipientes (Ø, cúpulas, cuellos, espesores)
provienen de los planos de recipientes de referencia cuando existen
(`geo_fuente`); en los demás casos se derivan de la capacidad y de las
dimensiones totales del catálogo y quedan marcados como "derivado".
"""

from dataclasses import dataclass, field


@dataclass
class Modelo:
    codigo: str               # código FLAMA del plano
    nombre: str               # denominación del plano
    familia: str              # manual | co2 | inox | rodante
    agente: str
    capacidad: str            # capacidad nominal tal como figura en la lista FLAMA
    spec: dict                # tabla de especificaciones (texto literal)
    fuente: str               # página del catálogo de referencia
    geo: dict = field(default_factory=dict)
    geo_fuente: str = "derivado"
    observaciones: list = field(default_factory=list)

    @property
    def descarga(self):
        """Dispositivo de descarga propio del tipo (ver DESCARGA)."""
        return DESCARGA[self.codigo]

    @property
    def soldadura(self):
        """Proceso de soldadura del recipiente (ISO 4063): 141 TIG en inoxidable,
        135 MAG (Arcal 21, Ar + 8 % CO2) en acero al carbono; el cilindro de CO2 es sin costura."""
        return {"inox": ("141", "TIG")}.get(self.familia, ("135", "MAG"))

    # dimensiones totales (mm) que el modelo 3D debe respetar
    @property
    def H(self):
        return float(str(self.spec["Altura (mm)"]).split("/")[-1].replace(".", ""))

    @property
    def W(self):
        return float(str(self.spec["Ancho (mm)"]).replace(".", ""))

    @property
    def D(self):
        return float(str(self.spec["Profundidad (mm)"]).replace(".", ""))


def _spec(cap, peso, alto, ancho, prof, desc, alc, temp, ps, pe, n_ag, n_ext, **extra):
    d = {
        "Capacidad nominal": cap,
        "Peso cargado (kg)": peso,
        "Altura (mm)": alto,
        "Ancho (mm)": ancho,
        "Profundidad (mm)": prof,
        "Tiempo de descarga (s)": desc,
        "Alcance (m)": alc,
        "Rango temperatura (°C)": temp,
        "Presión de servicio (MPa)": ps,
        "Presión de ensayo (MPa)": pe,
    }
    d.update(extra)
    if n_ag:
        d["Norma IRAM agente extintor"] = n_ag
    d["Norma IRAM extintor"] = n_ext
    return d


# --- geometría de recipientes de referencia (planos de recipientes) --------
# R: radio exterior, hc: altura del cuerpo cilíndrico medida desde el piso hasta
# la unión con la cúpula (rodantes: largo del cuerpo entre cabezales), hd: altura de la cúpula, t: espesor de cuerpo,
# td: espesor de cúpula, tf: espesor de fondo, zf_borde / zf_centro: altura
# del fondo (borde y centro) sobre el piso, cuello: (Ø ext, altura, rosca).
G_1KG = dict(R=76.2 / 2, total=298.0, hc=0, hd=12.5, t=1.25, td=0.9, tf=1.25,
             tipo_fondo="cupula", hf=22, cuello=(29, 12.5, "M22x1,5", 26), vol_dm3=1.18)
G_2K5 = dict(R=124 / 2, total=313.5, hc=0, hd=39.5, t=1.25, td=1.25, tf=1.25,
             tipo_fondo="concavo", zf_borde=16.0, zf_centro=5.5,
             cuello=(37, 14, "M30x1,5", 35), vol_dm3=3.5)
G_5KG = dict(R=153 / 2, total=389.5, hc=0, hd=54.5, t=1.6, td=1.6, tf=1.6,
             tipo_fondo="concavo", zf_borde=21.5, zf_centro=5.5,
             cuello=(37, 15, "M30x1,5", 35), vol_dm3=6.0)
G_10KG = dict(R=181.5 / 2, total=562.5, hc=0, hd=62.5, t=2.0, td=1.6, tf=2.0,
              tipo_fondo="concavo", zf_borde=16.5, zf_centro=4.8,
              cuello=(36.8, 14, "M30x1,5", 35), vol_dm3=12.5)
# rodantes: dos cabezales, cuello soldado
G_25KG = dict(R=276.5 / 2, hc=493, hd=87, t=3.2, td=3.2, tf=3.2, tipo_fondo="cabezal",
              cuello=(37, 35, "M30x1,5", 35), vol_dm3=34.4)
G_50KG = dict(R=320 / 2, hc=640, hd=105, t=3.2, td=3.2, tf=3.2, tipo_fondo="cabezal",
              cuello=(88, 37, "RBSP 2 1/2\"-11 h", 80), vol_dm3=61.8)


def _g_rodante(D, hc, t=4.75):
    """70 y 100 kg (proceso FLAMA de carros, planta y planilla MP): Ø390, chapa LAC 4,75 (IRAM 3550 4.1.3.2: 4,5 mín.
    por encima de Ø320), cuerpo de 680 / 900 mm entre casquetes 15" (MP-17, compartido) y cupla 2½" BSP.
    Altura del casquete = 0,656·R, proporción del cabezal Fadesa de 50 kg (105 / 160). Dos placas de refuerzo
    200 × 100 × 4,75 por dentro sobre la costura longitudinal."""
    import math
    R = D / 2
    hd = round(0.656 * R, 1)
    ri, bi = R - t, hd - t
    vol = round((math.pi * ri * ri * hc + 2 * (2 / 3) * math.pi * ri * ri * bi) / 1e6, 1)
    return dict(R=R, hc=hc, hd=hd, t=t, td=t, tf=t, tipo_fondo="cabezal",
                cuello=(88, 37, "RBSP 2 1/2\"-11 h", 80), vol_dm3=vol, refuerzo=(200.0, 100.0, 4.75))


G_70KG = _g_rodante(390, 680)
G_100KG = _g_rodante(390, 900)


def _g_inox(H, R=95.0, hd=60.0, h_valv=100.0):
    """Recipiente de acero inoxidable; la altura del cuerpo se deriva de la
    altura total del catálogo (volumen interior resultante informado)."""
    import math
    t = 0.8  # chapa inoxidable habitual en extintores de 6 a 10 l
    hn = 14.0
    hc = H - h_valv - hn - hd
    ri = R - t
    vol = (math.pi * ri * ri * (hc - 14.0) + (2 / 3) * math.pi * ri * ri * (hd - t)) / 1e6
    return dict(R=R, hc=round(hc, 1), hd=hd, t=t, td=t, tf=t,
                tipo_fondo="concavo", zf_borde=14.0, zf_centro=4.0,
                cuello=(37, hn, "M30x1,5", 35), vol_dm3=round(vol, 2))


def _g_co2(D, H, h_valv=100.0):
    """Cilindro de acero sin costura para CO2 (fondo semiesférico con pie).
    La longitud del cuerpo se deriva de la altura total del catálogo."""
    import math
    R = D / 2
    t = 5.4 if D < 130 else 6.0  # pared para 25 MPa de ensayo; masa coherente con el peso cargado
    hombro = round(0.55 * R, 1)
    hn = 22.0
    z_pie = 8.0
    hc = H - h_valv - hn - hombro  # altura (desde el piso) de la unión cuerpo-hombro
    ri = R - t
    vol = (math.pi * ri * ri * (hc - z_pie - R) + (2 / 3) * math.pi * ri ** 3
           + (2 / 3) * math.pi * ri * ri * (hombro - t)) / 1e6
    return dict(R=R, hc=round(hc, 1), hd=hombro, t=t, td=t, tf=t, z_pie=z_pie,
                tipo_fondo="co2", cuello=(32, hn, "rosca cónica 25E (ISO 11363-1)", 25), vol_dm3=round(vol, 2))


MODELOS = [
    Modelo("FL_MAT_ABC_1kg", "Extintor ABC 1 kg", "manual", "Polvo químico seco ABC", "1 kg",
           _spec("1 kg Ø3", "1,90", "340", "92", "76", "8/9", "2/3", "-20 a 50", "1,4", "3,5",
                 "3569", "3523", **{"Soporte vehicular": "Si", "Soporte pared": "No"}),
           "Catálogo pág. 4", G_1KG, "Plano recipiente 1 kg 3\" R1"),
    Modelo("FL_MAT_ABC_2.5kg", "Extintor ABC 2,5 kg", "manual", "Polvo químico seco ABC", "2,5 kg",
           _spec("2,5 kg", "4,60", "415", "220", "125", "9/12", "3/4", "-20 a 50", "1,4", "3,5",
                 "3569", "3523", **{"Soporte vehicular": "Opcional", "Soporte pared": "Si"}),
           "Catálogo pág. 4", G_2K5, "Plano recipiente 2,5 kg R2"),
    Modelo("FL_MAT_ABC_5kg", "Extintor ABC 5 kg", "manual", "Polvo químico seco ABC", "5 kg",
           _spec("5 kg", "8,50", "480", "225", "153", "10/13", "5/6", "-20 a 50", "1,4", "3,5",
                 "3569", "3523", **{"Soporte vehicular": "Opcional", "Soporte pared": "Si"}),
           "Catálogo pág. 4", G_5KG, "Plano recipiente 5 kg R2"),
    Modelo("FL_MAT_ABC_10kg", "Extintor ABC 10 kg", "manual", "Polvo químico seco ABC", "10 kg",
           _spec("10 kg", "16,50", "655", "230", "182", "18/22", "6/7", "-20 a 50", "1,4", "3,5",
                 "3569", "3523", **{"Soporte vehicular": "Opcional", "Soporte pared": "Si"}),
           "Catálogo pág. 4", G_10KG, "Plano recipiente 10 kg R2"),
    Modelo("FL_MAT_AGUA_10l", "Extintor Agua 10 l", "inox", "Agua", "10 l",
           _spec("10 dm³", "12,55", "620/650", "240", "190", "55", "9/11", "5 a 50", "0,8", "2,0",
                 None, "3525", **{"Soporte pared": "Si"}),
           "Catálogo pág. 8", _g_inox(650)),
    Modelo("FL_MAT_AFFF_10l", "Extintor AFFF 10 l", "inox", "Agua + espuma AFFF", "10 l",
           _spec("10 dm³", "12,60", "620/650", "240", "190", "55", "5/6", "-10 a 50", "0,8", "2,0",
                 "3515", "3527", **{"Soporte pared": "Si"}),
           "Catálogo pág. 10", _g_inox(650)),
    Modelo("FL_MAT_AFFF_50l", "Extintor AFFF 50 l sobre ruedas", "rodante", "Agua + espuma AFFF", "50 l",
           _spec("50 dm³", "100", "1.210", "466", "670", "130", "6/7", "-10 a 50", "0,8", "4,0",
                 "3515", "3541", **{"Diámetro de rueda (mm)": "350", "Longitud de manga (m)": "5"}),
           "Catálogo pág. 11", G_50KG, "Plano recipiente 50 kg R2"),
    Modelo("FL_MAT_BC_5kg", "Extintor BC 5 kg", "manual", "Polvo químico seco BC", "5 kg",
           _spec("5 kg", "8,50", "480", "225", "153", "10/13", "5/6", "-20 a 50", "1,4", "3,5",
                 "3569", "3523", **{"Soporte pared": "Si", "Soporte vehicular": "Opcional"}),
           "Catálogo pág. 6", G_5KG, "Plano recipiente 5 kg R2"),
    Modelo("FL_MAT_SALESK_6l", "Extintor Sales K 6 l", "inox", "Solución química pulverizada (clase K)", "6 l",
           _spec("6 dm³", "8,25", "470", "270", "190", "50", "3/4", "5 a 50", "0,8", "2,0",
                 "3697", "3694", **{"Soporte pared": "Si"}),
           "Catálogo pág. 15", _g_inox(470)),
    Modelo("FL_MAT_CO2_2kg", "Extintor CO₂ 2 kg", "co2", "Dióxido de carbono", "2 kg",
           _spec("2kg", "9", "520", "254", "114", "9", "1,5/3", "-20 a 50", "15", "25",
                 "41170", "3509", **{"Longitud de manga": "-", "Soporte pared": "Si"}),
           "Catálogo pág. 16", _g_co2(114, 520)),
    Modelo("FL_MAT_CO2_5kg", "Extintor CO₂ 5 kg", "co2", "Dióxido de carbono", "5 kg",
           _spec("5kg", "20", "790", "310", "140", "14", "1,5/3", "-20 a 50", "15", "25",
                 "41170", "3509", **{"Longitud de manga": "900", "Soporte pared": "Si"}),
           "Catálogo pág. 16", _g_co2(140, 790)),
    Modelo("FL_MAT_HCFC-HFC_5kg", "Extintor HCFC/HFC 5 kg", "manual", "HCFC 123 / HFC 236fa", "5 kg",
           _spec("5 kg", "8,50", "480", "225", "153", "10", "5", "-20 a 50", "0,8", "2,0",
                 "3526-1 (HCFC) / 3526-5 (HFC 236fa)", "3504",
                 **{"Soporte vehicular": "Opcional", "Soporte pared": "Si"}),
           "Catálogo págs. 13 y 14", G_5KG, "Plano recipiente 5 kg R2"),
    Modelo("FL_MAT_CLASED_9l", "Extintor Clase D 9 l", "manual", "Polvo químico seco D", "9 l",
           _spec("9 l", "16,50", "655", "230", "182", "18/22", "6/7", "-20 a 50", "1,4", "3,5",
                 None, "3523", **{"Soporte pared": "Si"}),
           "Catálogo pág. 17 (modelo 10 kg, único clase D de referencia)", G_10KG,
           "Plano recipiente 10 kg R2",
           ["La capacidad '9 l' proviene de la lista FLAMA; el catálogo de referencia sólo "
            "lista clase D de 5 kg y 10 kg. Se usa el recipiente de 10 kg: CONFIRMAR."]),
    Modelo("FL_MAT_ABC_25kg", "Extintor ABC 25 kg sobre ruedas", "rodante", "Polvo químico seco ABC", "25 kg",
           _spec("25 kg", "55", "1.140", "455", "600", "40", "5/6", "-20 a 50", "1,4", "4,0",
                 "3569", "3550", **{"Diámetro de rueda (mm)": "300", "Longitud de manga (m)": "5"}),
           "Catálogo pág. 5", G_25KG, "Plano recipiente 25 kg R3"),
    Modelo("FL_MAT_ABC_50kg", "Extintor ABC 50 kg sobre ruedas", "rodante", "Polvo químico seco ABC", "50 kg",
           _spec("50 kg", "100", "1.210", "466", "670", "45", "6/7", "-20 a 50", "1,4", "4,0",
                 "3569", "3550", **{"Diámetro de rueda (mm)": "350", "Longitud de manga (m)": "5"}),
           "Catálogo pág. 5", G_50KG, "Plano recipiente 50 kg R2"),
    Modelo("FL_MAT_ABC_70kg", "Extintor ABC 70 kg sobre ruedas", "rodante", "Polvo químico seco ABC", "70 kg",
           _spec("70 kg", "140", "1.350", "575", "736", "50", "7/8", "-20 a 50", "1,4", "4,0",
                 "3569", "3550", **{"Diámetro de rueda (mm)": "350", "Longitud de manga (m)": "5"}),
           "Catálogo pág. 5", G_70KG),
    Modelo("FL_MAT_ABC_100kg", "Extintor ABC 100 kg sobre ruedas", "rodante", "Polvo químico seco ABC", "100 kg",
           _spec("100 kg", "185", "1.400", "630", "840", "55", "8/9", "-20 a 50", "1,4", "4,0",
                 "3569", "3550", **{"Diámetro de rueda (mm)": "400", "Longitud de manga (m)": "12"}),
           "Catálogo pág. 5", G_100KG, "Plano extintor rodante 100 kg R1 (Ø390)"),
]


def por_codigo(c):
    return next(m for m in MODELOS if m.codigo == c)


# Dispositivo de descarga por modelo (según catálogo de referencia y práctica de cada agente)
DESCARGA = {
    "FL_MAT_ABC_1kg": "tobera_1kg", "FL_MAT_ABC_2.5kg": "tobera_polvo", "FL_MAT_ABC_5kg": "tobera_polvo",
    "FL_MAT_ABC_10kg": "tobera_polvo", "FL_MAT_BC_5kg": "tobera_polvo", "FL_MAT_HCFC-HFC_5kg": "tobera_polvo",
    "FL_MAT_AGUA_10l": "tobera_chorro", "FL_MAT_AFFF_10l": "lanza_espuma", "FL_MAT_SALESK_6l": "lanza_k",
    "FL_MAT_CLASED_9l": "lanza_d", "FL_MAT_CO2_2kg": "difusor_brazo", "FL_MAT_CO2_5kg": "difusor_manga",
    "FL_MAT_ABC_25kg": "campana", "FL_MAT_ABC_50kg": "campana", "FL_MAT_ABC_70kg": "campana",
    "FL_MAT_ABC_100kg": "campana", "FL_MAT_AFFF_50l": "lanza_espuma_rodante",
}
