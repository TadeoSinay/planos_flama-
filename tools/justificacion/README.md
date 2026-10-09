# Justificación de medidas planos — herramientas

Genera `salida/justificacion/Justificacion de medidas planos.docx` y `.xlsx`.

| Archivo | Qué hace |
|---|---|
| `crudo.py` | Saca del modelo 3D cada dimensión de cada pieza de los 17 planos → `crudo.json` (1101 filas) |
| `figs.py` | Dibuja las marcas rojas numeradas sobre cada fuente → `figs/` + `figs.json` (47 figuras) |
| `build_xlsx.py` | Excel (hojas Leyenda, Crudo, Fuentes, Resumen) |
| `prep_word.py` → `word.json` | Arma el contenido del Word (qué marca se usa en qué pieza) |
| `word.js` | Word con docx-js (`npm install docx`) |

`figs/` ya tiene las 47 capturas marcadas: para rearmar el Word alcanza con `word.json` + `figs/` + `word.js`
(ajustar las rutas `SP` / `OUT` del principio de cada script a la máquina).
Para volver a marcar desde cero, `figs.py` necesita las fuentes originales (planos Fadesa, catálogo Fadesa 3,
normas IRAM, Res. 522/07, Anexo R, fotos del relevamiento, planilla MP), que no están en el repo
(las normas no se suben).

Pendiente pedido por el usuario (09/10/2026): Word más compacto (sin perder marcas), Excel compacto
(matriz pieza/dimensión × modelo en lugar de 1101 filas).
