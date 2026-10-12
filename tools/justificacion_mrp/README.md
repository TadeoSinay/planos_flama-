# Justificación del MRP — herramientas

Genera `salida/justificacion/Justificación_MRP.docx`: de dónde sale cada valor de `salida/mrp/FLAMA_MRP.xlsx`, con
una tabla por hoja ordenada por el código «Ref.» de cada fila del Excel y las capturas marcadas de los procesos, el
BOM, las planillas fuente, las cotizaciones y el propio MRP. Sólo negro y grises.

| Paso | Archivo | Qué hace |
|---|---|---|
| 1 | `capturas_mrp.py <carpeta de fuentes> <FLAMA_MRP.xlsx>` | Recorta el párrafo o la tabla citada y marca el dato en rojo → `figs/*.png` y `capturas.json`. P = proceso de manuales o carros, R = proceso de recargas, D = Dimensionamiento Técnico FLAMA, X = otras planillas, B = BOM, Q = cotización, M = hoja del MRP. Con IDs al final, rehace sólo esas |
| 2 | `datos_mrp.py <FLAMA_MRP.xlsx> <datos.json>` | Lee los valores del MRP ya recalculado y la justificación de cada Ref. (`FLAMA_MRP_refs.json`) y arma el contraste con los procesos → JSON |
| 3 | `word_mrp.js <datos.json> <salida.docx>` | Word con docx-js (`npm install docx`) |

La carpeta de fuentes tiene: `carros.pdf`, `manuales.pdf`, `recargas.pdf` y `wpp.pdf` (los procesos de carros,
manuales y recargas y las cotizaciones de MP por WhatsApp, pasados a PDF con `soffice --headless --convert-to pdf`),
`Proyecciones.xlsx`, `Dimensionamiento_TecnicoV2.xlsx`, `Dimensionamiento_Tecnico_FLAMA.xlsx`, `MP_Abastecimiento.xlsx`
(planilla de MP, opción D), `Materias Primas.xlsx` y la carpeta `PRESUPUESTOS` de la investigación de proveedores. El
BOM se toma de `salida/bom/FLAMA_BOM.xlsx`.

```
python generar.py --mrp-insumos Proyecciones.xlsx
python tools/justificacion_mrp/capturas_mrp.py <fuentes> salida/mrp/FLAMA_MRP.xlsx
python tools/justificacion_mrp/datos_mrp.py salida/mrp/FLAMA_MRP.xlsx /tmp/datos_mrp.json
NODE_PATH=<node_modules con docx> node tools/justificacion_mrp/word_mrp.js /tmp/datos_mrp.json "salida/justificacion/Justificación_MRP.docx"
```
