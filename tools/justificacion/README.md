# Justificación de medidas planos — herramientas

Genera `salida/justificacion/Justificacion de medidas planos.docx` (≈ 11 páginas) y `.xlsx` (matriz por familia).

| Paso | Archivo | Qué hace |
|---|---|---|
| 1 | `crudo.py` | Saca del modelo 3D cada dimensión de cada pieza de los 17 planos → `crudo.json` |
| 2 | `figs.py` | Marcas rojas numeradas sobre planos Fadesa, catálogo, fichas, normas, fotos y planilla MP → `figs/` + `figs.json` |
| 3 | `proc_figs.py` | Capturas marcadas de los procesos FLAMA de carros y de manuales (F38, F39) |
| 3b | `carro_figs.py` | Carro: plano Fadesa «Rodante 50kg 800mm R2» (manija doblada 30°, oreja) y foto del carro relevado (portaeje, chapa triangular) → F41, F42 |
| 4 | `compacto.py <sha>` | Une todo en `compacto.json`: fuente «F10·3» de cada valor, lista D01… de valores de diseño con link a la línea del commit `<sha>`, pendientes |
| 5 | `recorte.py` | Recorta cada captura a la zona de sus marcas (para el Word) |
| 6 | `xlsx_compacto.py` | Excel: hojas «Cómo leer», «Manuales ABC», «Rodantes ABC», «Revendidos» (pieza × modelo: valor + fuente, color por estado) y «Fuentes» |
| 7 | `word2.js` | Word con docx-js (`npm install docx`): capturas de a dos con sus marcas, pendientes y tabla de valores de diseño |

Colores (mismo criterio que el BOM): sin color = documento; amarillo = diseño FLAMA; naranja = a validar.

`figs/` tiene las capturas ya marcadas. Para volver a marcar desde cero, `figs.py` necesita las fuentes originales
(planos Fadesa, catálogo Fadesa 3, normas IRAM, Res. 522/07, Anexo R, fotos del relevamiento, planilla MP) y
`proc_figs.py` los dos documentos de proceso; no están en el repo (las normas no se suben). Ajustar las rutas `SP` /
`OUT` del principio de cada script a la máquina.
