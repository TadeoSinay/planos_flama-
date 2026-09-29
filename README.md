# planos_flama — Planos técnicos de la línea de extintores FLAMA S.A.

Planos de conjunto, cortes, detalles ampliados y modelos 3D de los 17 extintores
del catálogo FLAMA, con rótulo FLAMA S.A. y representación según las normas IRAM
de dibujo técnico y sus equivalentes ISO.

Todo se genera por código a partir de sólidos 3D reales (kernel OpenCascade):
las vistas salen de proyectar esos sólidos con eliminación de líneas ocultas.
Por eso las tres vistas, la isometría, el corte y los detalles son coherentes
entre sí y con el modelo 3D.

## Contenido por modelo (`salida/FL_MAT_<TIPO>_<tamaño>/`)

Nomenclatura: `FL_MAT_<TIPO>_<tamaño>`, por ejemplo `FL_MAT_ABC_10kg`, `FL_MAT_CO2_2kg`,
`FL_MAT_AFFF_50l`. El mismo código figura como N° de plano en el rótulo.

| Archivo | Contenido |
|---|---|
| `FL_MAT_…​.dxf` | **El plano**: las 3 láminas en un solo dibujo, una presentación por lámina: **Hoja1_Conjunto** (vistas anterior, superior y lateral izquierda en método ISO E, isometría, cotas, números de posición y lista de piezas), **Hoja2_Corte_Detalles** (A2: corte A-A del recipiente y detalles ampliados A–E) y **Hoja3_Especificaciones** (tabla técnica y normas) |
| `FL_MAT_…​.pdf` | El mismo plano en PDF de 3 páginas a tamaño real (A3/A2) |
| `FL_MAT_…​.dwg` | Se genera en tu PC con `autocad\1_convertir_DXF_a_DWG.bat` o con el MCP (`autocad_convert_flama_to_dwg`). DWG es un formato cerrado y en este entorno no hay conversor disponible |
| `FL_MAT_…​.step` | Ensamble 3D con sólidos exactos por pieza (AutoCAD: `IMPORT`) |
| `FL_MAT_…​_3D.dxf` | Modelo 3D con una malla por pieza (AutoCAD: `CONVTOSOLID`) |

`salida/FLAMA_planos_completos.pdf` junta los 17 planos (51 láminas) y `salida/validacion.json`
tiene la verificación dimensional.

Los scripts para AutoCAD 2027 están en `autocad/` (ver `autocad/LEAME_AutoCAD.txt`):
convierten los DXF a DWG y abren los modelos 3D con
`"C:\Program Files\Autodesk\AutoCAD 2027\acad.exe" /product ACAD /language "es-ES"`.
Los scripts usan comandos con prefijo `_` (nombres globales en inglés), así que
funcionan igual con AutoCAD en español o en inglés.

## Modelos

| Código / archivo | Denominación | Norma IRAM agente | Norma IRAM extintor | Fuente de datos |
|---|---|---|---|---|
| FL_MAT_ABC_1kg | Extintor ABC 1 kg | 3569 | 3523 | catálogo pág. 4 · recipiente 1 kg 3" R1 |
| FL_MAT_ABC_2.5kg | Extintor ABC 2,5 kg | 3569 | 3523 | catálogo pág. 4 · recipiente 2,5 kg R2 |
| FL_MAT_ABC_5kg | Extintor ABC 5 kg | 3569 | 3523 | catálogo pág. 4 · recipiente 5 kg R2 |
| FL_MAT_ABC_10kg | Extintor ABC 10 kg | 3569 | 3523 | catálogo pág. 4 · recipiente 10 kg R2 |
| FL_MAT_AGUA_10l | Extintor Agua 10 l | – | 3525 | catálogo pág. 8 |
| FL_MAT_AFFF_10l | Extintor AFFF 10 l | 3515 | 3527 | catálogo pág. 10 |
| FL_MAT_AFFF_50l | Extintor AFFF 50 l sobre ruedas | 3515 | 3541 | catálogo pág. 11 · recipiente 50 kg R2 |
| FL_MAT_BC_5kg | Extintor BC 5 kg | 3569 | 3523 | catálogo pág. 6 · recipiente 5 kg R2 |
| FL_MAT_SALESK_6l | Extintor Sales K 6 l | 3697 | 3694 | catálogo pág. 15 |
| FL_MAT_CO2_2kg | Extintor CO₂ 2 kg | 41170 | 3509 | catálogo pág. 16 |
| FL_MAT_CO2_5kg | Extintor CO₂ 5 kg | 41170 | 3509 | catálogo pág. 16 |
| FL_MAT_HCFC-HFC_5kg | Extintor HCFC/HFC 5 kg | 3526-1 / 3526-5 | 3504 | catálogo págs. 13–14 · recipiente 5 kg R2 |
| FL_MAT_CLASED_9l | Extintor Clase D 9 l | – | 3523 | catálogo pág. 17 · recipiente 10 kg R2 (**ver pendientes**) |
| FL_MAT_ABC_25kg | Extintor ABC 25 kg sobre ruedas | 3569 | 3550 | catálogo pág. 5 · recipiente 25 kg R3 |
| FL_MAT_ABC_50kg | Extintor ABC 50 kg sobre ruedas | 3569 | 3550 | catálogo pág. 5 · recipiente 50 kg R2 |
| FL_MAT_ABC_70kg | Extintor ABC 70 kg sobre ruedas | 3569 | 3550 | catálogo pág. 5 |
| FL_MAT_ABC_100kg | Extintor ABC 100 kg sobre ruedas | 3569 | 3550 | catálogo pág. 5 · rodante 100 kg R1 (Ø390) |

Las normas de producto se transcriben tal como figuran en las filas
"Norma IRAM agente extintor" y "Norma IRAM extintor" del catálogo de referencia.

## Normas de dibujo aplicadas

| Norma | Equivalente ISO | Qué se aplica |
|---|---|---|
| IRAM 4501 | ISO 5456-2 | Método ISO E (primer diedro): superior debajo de la anterior, lateral izquierda a su derecha; símbolo del método en el rótulo |
| IRAM 4502 | ISO 128-20/-24 | Grupo 0,5: visibles 0,5; cotas, rayados y referencias 0,25; ocultas en trazos 0,25; ejes en trazo largo y punto 0,25; recuadro 0,7 |
| IRAM 4503 | ISO 3098 | Letra tipo B vertical; alturas 2,5 – 3,5 – 5 – 7 |
| IRAM 4504 | ISO 5457 | Formatos A3/A2, recuadro, marcas de centrado, zonas de 50 mm |
| IRAM 4505 | ISO 5455 | Sólo escalas normalizadas (1:1, 1:2, 1:5, 1:10, 1:20; 2:1, 5:1) |
| IRAM 4507 | ISO 128-40/-44/-50 | Plano de corte con letras y flechas; rayado a 45°; secciones delgadas ennegrecidas |
| IRAM 4508 | ISO 7200 / 7573 | Rótulo abajo a la derecha; lista de piezas encima, leída de abajo hacia arriba |
| IRAM 4513 | ISO 129-1 | Cotas en mm, cifra sobre la línea de cota, flecha llena, coma decimal, prefijo Ø |
| IRAM 4520 | ISO 6410-1 | Rosca interior: cresta con línea gruesa, fondo con línea fina |
| IRAM 4540 | ISO 5456-3 | Isometría sin aristas ocultas |
| – | ISO 2553 / ISO 4063 | Símbolos de soldadura: filete, todo alrededor, proceso 131 (MIG) |
| – | ISO 2768-1 | Tolerancias generales clase m |
| – | ISO 6433 | Números de posición |

## Verificación dimensional

`generar.py` construye cada conjunto y ajusta el largo de la palanca, la altura
del cuerpo de la válvula y la posición del eje de ruedas para que la caja
envolvente coincida con **altura y ancho del catálogo (±0,05 mm)**. El resultado
queda en `salida/validacion.json`.

La **profundidad** acotada (vista lateral) es la medida real del modelo e incluye
el espesor del suncho portamanguera. Por eso supera en 1,5–3 mm la
"profundidad" del catálogo, que coincide con el Ø del recipiente.

## Pendientes a confirmar por FLAMA (no inventados)

1. **Clase D 9 l**: el catálogo de referencia sólo lista clase D de 5 kg y 10 kg
   (IRAM 3523). El plano usa el recipiente de 10 kg y deja la observación en la hoja 3.
2. **Materiales "A definir"**: la lista de piezas sólo nombra los materiales que
   indica el catálogo (chapa de acero / acero inoxidable, válvula de latón forjado,
   manga de caucho sintético). El resto se completa en el BOM.
3. **Recipientes sin plano de referencia** (Agua, AFFF 10 l, Sales K, CO₂, 70 kg):
   el Ø y la altura salen del catálogo; los espesores y la longitud del cuerpo son
   derivados (ver hoja 3 de cada modelo).
4. **Rosca de válvula de CO₂**: se indica rosca cónica 25E (ISO 11363-1); confirmar
   con el proveedor del cilindro.
5. **Títulos de normas IRAM**: se citan por número y título. El texto normativo no
   se reproduce porque es material protegido de IRAM. Verificar los títulos de
   IRAM 4507 y 4540 contra la edición vigente.
6. Rótulo: los campos "Revisó" y "Aprobó" quedan en blanco para la firma.

## Regenerar

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
python generar.py                 # todos
python generar.py FL_MAT_ABC_10kg      # uno
```

Estructura del código:
`flama/catalogo.py` (datos), `flama/modelo3d.py` (sólidos), `flama/vistas.py`
(proyección HLR y cortes), `flama/lamina.py` (formato, rótulo, capas, cotas,
soldadura), `flama/planos.py` (hojas 1–3), `flama/exportar.py` (DXF/PDF/STEP),
`flama/normas.py` (normativa).
