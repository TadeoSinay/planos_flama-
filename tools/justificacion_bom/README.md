# Justificación del BOM — herramientas

Genera `salida/justificacion/Justificacion del BOM.docx`: la fuente, el cálculo, la tolerancia y el control de cada
valor de `salida/bom/FLAMA_BOM.xlsx` (referencias, carga y tolerancia, gas impulsor, relación de llenado del CO₂,
tolerancias de piezas, masas contra referencia, sustituto y recargas por servicio), con las capturas marcadas de las
normas y fichas citadas. Sólo negro y grises.

| Paso | Archivo | Qué hace |
|---|---|---|
| 1 | `capturas.py <carpeta de normas> <carpeta de fichas DEMSA>` | Recorta la cláusula o tabla citada de cada norma y ficha, marca el dato en rojo → `figs/N??.png`, `figs/F_*.png` y `capturas.json`. Deja afuera los márgenes con los datos de la licencia; las normas no se suben |
| 2 | `datos_bom.py <FLAMA_BOM.xlsx> <datos.json> [cache.pkl]` | Lee los valores del Excel ya recalculado (el que deja `generar.py --bom`), agrega los controles que no están en el Excel (gas real con CoolProp, masa contra plano o ficha) y las capturas reusadas del Word de planos → JSON. `cache.pkl`: estructura de productos ya armada, sólo para la faja del sustituto (si no, rearma los modelos 3D) |
| 3 | `textos.py` | Textos del Word armados con esos números (los importa `datos_bom.py`) |
| 4 | `word_bom.js <datos.json> <salida.docx>` | Word con docx-js (`npm install docx`) |

```
python generar.py --bom
python tools/justificacion_bom/datos_bom.py salida/bom/FLAMA_BOM.xlsx /tmp/datos.json
NODE_PATH=<node_modules con docx> node tools/justificacion_bom/word_bom.js /tmp/datos.json "salida/justificacion/Justificacion del BOM.docx"
```

Las normas se citan por cláusula; no se transcriben ni se suben al repo.
