"""Normativa citada en las láminas.

Las normas de PRODUCTO se citan textualmente tal como figuran en las tablas
"Especificaciones" del catálogo de referencia ("Norma IRAM agente extintor",
"Norma IRAM extintor").

Las normas de DIBUJO se citan por número y título. Las equivalencias ISO son
las que rigen la representación efectivamente aplicada en este generador.
"""

# Normas de dibujo técnico aplicadas (número, título, qué se aplica en la lámina)
DIBUJO = [
    ("IRAM 4501", "Dibujo técnico. Métodos de proyección", "ISO 5456-2",
     "Método ISO E: vista superior (B) debajo de la anterior (A), lateral izquierda (C) a su "
     "derecha; símbolo del método junto a la escala, dentro del rótulo."),
    ("IRAM 4502", "Dibujo técnico. Líneas", "ISO 128-20",
     "Grupo 0,7: A continua gruesa 0,7 (aristas visibles); E de trazos media 0,35 (ocultas); "
     "B continua fina 0,18 (cotas, rayados, referencias, fondo de rosca); F trazo largo y corto "
     "fina 0,18 (ejes); G fina con extremos gruesos (plano de corte). Relación 4:2:1."),
    ("IRAM 4503", "Dibujo técnico. Letras", "ISO 3098",
     "Letra tipo B vertical, trazo h/10; alturas de la serie 1,8 - 2,5 - 3,5 - 5 - 7 - 10."),
    ("IRAM 4504", "Formatos, elementos gráficos y plegado de láminas", "ISO 5457",
     "Formatos A3 y A2; recuadro a 25 mm del borde izquierdo y 10 mm de los demás; marcas de "
     "centrado; plegado a módulo A4."),
    ("IRAM 4505", "Dibujo tecnológico. Escalas", "ISO 5455",
     "Escalas normalizadas 1:1, 1:2, 1:5, 1:10, 1:20 y ampliaciones 2:1, 5:1."),
    ("IRAM 4507", "Dibujo técnico. Representación de secciones y cortes", "ISO 128-40/44",
     "Corte A-A por el plano de simetría, designado con letras y flechas de observación."),
    ("IRAM 4508", "Rótulo, lista de materiales y despiezo", "ISO 7200",
     "Rótulo de 175 × 51 mm en el ángulo inferior derecho; lista de materiales del mismo ancho "
     "apoyada sobre el rótulo (posición, cantidad, denominación, código, material, peso, observaciones)."),
    ("IRAM 4509", "Dibujo técnico. Rayados indicadores de secciones y cortes", "ISO 128-50",
     "Rayado a 45° con línea fina; orientación distinta en piezas contiguas; secciones delgadas ennegrecidas."),
    ("IRAM 4513", "Dibujo técnico. Acotación", "ISO 129-1",
     "Flecha: triángulo lleno con base : altura = 1 : 4; separación entre cotas y al dibujo no menor "
     "que la altura de la cifra; cotas fuera del contorno; coma decimal."),
    ("IRAM 4520", "Dibujo tecnológico. Representación de roscas y partes roscadas", "ISO 6410-1",
     "Rosca interior en corte: cresta con línea gruesa, fondo con línea fina; rayado hasta la cresta."),
    ("IRAM 4540", "Dibujo técnico. Representación de vistas en perspectiva", "ISO 5456-3",
     "Isometría: ejes a 120°, sin aristas ocultas."),
]

SOLDADURA = ("ISO 2553", "Representación simbólica de soldaduras",
             "Símbolo de filete, contorno en todo el perímetro; proceso 131 (MIG, ISO 4063).")
TOLERANCIAS = ("ISO 2768-1", "Tolerancias generales", "clase m (media) salvo indicación")

AVISO_NORMAS = ("Las normas se citan por número y título; el texto normativo completo "
                "debe consultarse en la edición vigente publicada por IRAM / ISO.")


def normas_producto(m):
    from .agentes import agente
    s = m.spec
    res = []
    n_ag = agente(m)["norma"]
    if n_ag.startswith("IRAM"):
        res.append(("Norma IRAM agente extintor", n_ag.replace("IRAM ", "")))
    res.append(("Norma IRAM extintor", s["Norma IRAM extintor"]))
    return res
