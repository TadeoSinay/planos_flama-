# Justificación del BOM — herramientas

Genera `salida/justificacion/Justificacion del BOM.docx`: la fuente, el cálculo y el control de cada valor de
`salida/bom/FLAMA_BOM.xlsx` (densidades, carga y tolerancia, gas impulsor, relación de llenado del CO₂, masas contra
referencia, sustituto y recargas por servicio). Sólo negro y grises.

| Paso | Archivo | Qué hace |
|---|---|---|
| 1 | `datos_bom.py <datos.json> [cache.pkl]` | Calcula cada valor con los mismos módulos del BOM y lo controla (tabla 3 de la IRAM 3517-2, IRAM 2533, gas real con CoolProp, masa contra plano o ficha) → JSON. `cache.pkl` es opcional: la estructura de los productos ya armada, para no reconstruir los modelos 3D (unos 8 minutos) |
| 2 | `textos.py` | Textos del Word armados con esos números (los importa `datos_bom.py`) |
| 3 | `word_bom.js <datos.json> <salida.docx>` | Word con docx-js (`npm install docx`) |

```
python tools/justificacion_bom/datos_bom.py /tmp/datos.json
NODE_PATH=<node_modules con docx> node tools/justificacion_bom/word_bom.js /tmp/datos.json "salida/justificacion/Justificacion del BOM.docx"
```

Las normas se citan por cláusula; no se transcriben ni se suben al repo.
