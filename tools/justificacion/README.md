# Justificación de medidas planos — herramientas

Genera `salida/justificacion/Justificacion de medidas planos.docx` (13 páginas sin huecos, todo en el Word: no hay Excel).

| Paso | Archivo | Qué hace |
|---|---|---|
| 1 | `crudo.py` | Saca del modelo 3D cada dimensión de cada pieza de los 17 planos → `crudo.json` |
| 2 | `figs.py` | Marcas rojas numeradas sobre planos Fadesa, catálogo, fichas, normas, fotos y planilla MP → `figs/` + `figs.json` |
| 3 | `proc_figs.py` | Capturas marcadas de los procesos FLAMA de carros y de manuales (F38, F39) |
| 3b | `carro_figs.py` | Carro: plano Fadesa «Rodante 50kg 800mm R2» (manija doblada 30°), fotos del carro y de la lanza (F41 a F45) y figuras del proceso de carros v2 (accesorios, plantilla de posiciones, kit → F46 a F48), la hoja de especificaciones «Polvos carros» del usuario (F49) y el proceso final de carros (manija, carro armado, foto del fleje → F50 a F52) |
| 3c | `marcado_fig.py <proceso de manuales>.pdf` | Proceso de manuales vigente, apartado «Numerado de cúpula» (número estampado en la cúpula, en arco junto al cuello → F53); corrige la marca 1 de F39 (versión anterior del documento) |
| 4 | `compacto.py <sha>` | Une todo en `compacto.json`: fuente «F10·3» de cada valor, lista D01… de valores de diseño con la lógica que los justifica, pendientes |
| 5 | `recorte.py` | Recorta cada captura a la zona de sus marcas (para el Word) |
| 5b | `analisis.py` | Análisis de cada medida de diseño FLAMA: cálculo de estática y resistencia (virola, casquete elipsoidal, cuello, válvula, pasadores, eje de rueda, CO₂ con CoolProp, tensión de la cúpula en la franja del marcado), cláusula de norma, costo y conclusión; condiciones de compra → `analisis.json` |
| 6 | `word2.js` | Word con docx-js (`npm install docx`): capturas de a dos con sus marcas, condiciones de compra en la página 1 y, al final, la sección 8 «Análisis y justificación de las medidas de diseño» (sin referencias al código). Lee `escala.json` |
| 7 | `ajuste.py` | Compaginación sin huecos: arma el Word, lo pasa a PDF (LibreOffice) y, página por página, sube la fila de figuras que saltó achicando un poco las imágenes (nunca por debajo del 60 % de su tamaño base) o, si no entra, agranda las de la página (cada una hasta el ancho de su celda) hasta llenarla; deja la escala de cada figura en `escala.json`; después se corre `word2.js` otra vez para el Word final |

Cada valor sale de un documento (figura y marca) o es una medida de diseño FLAMA justificada en la sección 8.

`figs/` tiene las capturas ya marcadas. Para volver a marcar desde cero, `figs.py` necesita las fuentes originales
(planos Fadesa, catálogo Fadesa 3, normas IRAM, Res. 522/07, Anexo R, fotos del relevamiento, planilla MP) y
`proc_figs.py` los dos documentos de proceso; no están en el repo (las normas no se suben). Ajustar las rutas `SP` /
`OUT` del principio de cada script a la máquina.
