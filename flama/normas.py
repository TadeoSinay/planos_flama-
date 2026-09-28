"""Normativa citada en las láminas.

Las normas de PRODUCTO se citan textualmente tal como figuran en las tablas
"Especificaciones" del catálogo de referencia ("Norma IRAM agente extintor",
"Norma IRAM extintor").

Las normas de DIBUJO se citan por número y título. Las equivalencias ISO son
las que rigen la representación efectivamente aplicada en este generador.
"""

# Normas de dibujo técnico aplicadas (número, título, qué se aplica en la lámina)
DIBUJO = [
    ("IRAM 4501", "Dibujo técnico - Vistas", "ISO 5456-2",
     "Método de proyección ISO E (primer diedro): vista superior debajo de la anterior, "
     "lateral izquierda a la derecha de la anterior; símbolo del método en el rótulo."),
    ("IRAM 4502", "Dibujo técnico - Líneas", "ISO 128-20 / ISO 128-24",
     "Grupo de líneas 0,5: continua gruesa 0,5 mm (aristas visibles), continua fina 0,25 mm "
     "(cotas, rayados, fondo de rosca, referencias), trazos finos 0,25 mm (aristas ocultas), "
     "trazo largo y punto fino 0,25 mm (ejes), trazo y punto grueso en extremos del plano de corte."),
    ("IRAM 4503", "Dibujo técnico - Letras y números", "ISO 3098-1/-2",
     "Escritura tipo B vertical; alturas nominales 2,5 - 3,5 - 5 - 7 - 10 mm."),
    ("IRAM 4504", "Dibujo técnico - Formatos, elementos gráficos y plegado de láminas", "ISO 5457",
     "Formatos serie A, recuadro 0,7 mm, marcas de centrado y sistema de coordenadas de zonas."),
    ("IRAM 4505", "Dibujo técnico - Escalas", "ISO 5455",
     "Sólo escalas normalizadas: 1:1, 1:2, 1:5, 1:10, 1:20 y ampliaciones 2:1, 5:1."),
    ("IRAM 4507", "Dibujo técnico - Cortes y secciones", "ISO 128-40 / 128-44 / 128-50",
     "Plano de corte con letras y flechas; rayado a 45° con línea fina; secciones "
     "estrechas ennegrecidas."),
    ("IRAM 4508", "Dibujo técnico - Rótulo, lista de materiales y despiece", "ISO 7200 / ISO 7573",
     "Rótulo en el ángulo inferior derecho; lista de piezas sobre el rótulo, leída de abajo "
     "hacia arriba; números de posición (ISO 6433)."),
    ("IRAM 4513", "Dibujo técnico - Acotación", "ISO 129-1",
     "Cotas en mm sin unidad, cifra sobre la línea de cota, flechas cerradas llenas, "
     "separador decimal coma; prefijo Ø en diámetros."),
    ("IRAM 4520", "Dibujo técnico - Representación de roscas", "ISO 6410-1",
     "Cresta con línea gruesa, fondo con línea fina; rayado hasta la cresta."),
    ("IRAM 4540", "Dibujo técnico - Representación de perspectivas", "ISO 5456-3",
     "Proyección axonométrica isométrica, sin aristas ocultas."),
]

SOLDADURA = ("ISO 2553", "Representación simbólica de soldaduras",
             "Símbolo de filete, contorno en todo el perímetro; proceso 131 (MIG, ISO 4063).")
TOLERANCIAS = ("ISO 2768-1", "Tolerancias generales", "clase m (media) salvo indicación")

AVISO_NORMAS = ("Las normas se citan por número y título; el texto normativo completo "
                "debe consultarse en la edición vigente publicada por IRAM / ISO.")


def normas_producto(m):
    s = m.spec
    res = []
    if "Norma IRAM agente extintor" in s:
        res.append(("Norma IRAM agente extintor", s["Norma IRAM agente extintor"]))
    res.append(("Norma IRAM extintor", s["Norma IRAM extintor"]))
    return res
