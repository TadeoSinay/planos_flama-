# planos_flama — Planos técnicos de la línea de extintores FLAMA S.A.

Planos de conjunto, cortes, detalles ampliados y modelos 3D de los 17 extintores
del catálogo FLAMA, con rótulo FLAMA S.A. y representación según las normas IRAM
de dibujo técnico y sus equivalentes ISO.

Todo se genera por código a partir de sólidos 3D reales (kernel OpenCascade):
las vistas salen de proyectar esos sólidos con eliminación de líneas ocultas.
Por eso las tres vistas, la isometría, el corte y los detalles son coherentes
entre sí y con el modelo 3D.

## Contenido por modelo (`salida/<CÓDIGO>/`)

| Archivo | Contenido |
|---|---|
| `<CÓDIGO>_H1.dxf` | **Hoja 1 – Plano de conjunto**: vista anterior, superior y lateral izquierda (método ISO E), isometría, cotas generales, números de posición y lista de piezas |
| `<CÓDIGO>_H2.dxf` | **Hoja 2 – Corte A-A y detalles** (A2): corte del recipiente y detalles ampliados A–E (válvula/manómetro/manijas, cuello roscado, unión cúpula-cuerpo, fondo, tobera; en rodantes: válvula esférica y tobera) |
| `<CÓDIGO>_H3.dxf` | **Hoja 3 – Especificaciones y normas**: tabla técnica y normativa citada |
| `<CÓDIGO>.pdf` | Las 3 hojas en PDF, a tamaño real (A3/A2) |
| `<CÓDIGO>.step` | Ensamble 3D con sólidos exactos por pieza (AutoCAD: `IMPORT`) |
| `<CÓDIGO>_3D.dxf` | Modelo 3D con una malla por pieza (AutoCAD: `CONVTOSOLID`) |

`salida/FLAMA_planos_completos.pdf` junta los 51 planos y `salida/validacion.json`
tiene la verificación dimensional.

Los scripts para AutoCAD 2027 están en `autocad/` (ver `autocad/LEAME_AutoCAD.txt`):
convierten los DXF a DWG y abren los modelos 3D con
`"C:\Program Files\Autodesk\AutoCAD 2027\acad.exe" /product ACAD /language "en-US"`.

## Modelos

| Código | Denominación | Norma IRAM agente | Norma IRAM extintor | Fuente de datos |
|---|---|---|---|---|
| FL-ABC-001 | Extintor ABC 1 kg | 3569 | 3523 | catálogo pág. 4 · recipiente 1 kg 3" R1 |
| FL-ABC-002 | Extintor ABC 2,5 kg | 3569 | 3523 | catálogo pág. 4 · recipiente 2,5 kg R2 |
| FL-ABC-003 | Extintor ABC 5 kg | 3569 | 3523 | catálogo pág. 4 · recipiente 5 kg R2 |
| FL-ABC-004 | Extintor ABC 10 kg | 3569 | 3523 | catálogo pág. 4 · recipiente 10 kg R2 |
| FL-AGU-001 | Extintor Agua 10 l | – | 3525 | catálogo pág. 8 |
| FL-AFF-001 | Extintor AFFF 10 l | 3515 | 3527 | catálogo pág. 10 |
| FL-AFF-002 | Extintor AFFF 50 l sobre ruedas | 3515 | 3541 | catálogo pág. 11 · recipiente 50 kg R2 |
| FL-BC-001 | Extintor BC 5 kg | 3569 | 3523 | catálogo pág. 6 · recipiente 5 kg R2 |
| FL-K-001 | Extintor Sales K 6 l | 3697 | 3694 | catálogo pág. 15 |
| FL-CO2-001 | Extintor CO₂ 2 kg | 41170 | 3509 | catálogo pág. 16 |
| FL-CO2-002 | Extintor CO₂ 5 kg | 41170 | 3509 | catálogo pág. 16 |
| FL-HAL-001 | Extintor HCFC/HFC 5 kg | 3526-1 / 3526-5 | 3504 | catálogo págs. 13–14 · recipiente 5 kg R2 |
| FL-D-001 | Extintor Clase D 9 l | – | 3523 | catálogo pág. 17 · recipiente 10 kg R2 (**ver pendientes**) |
| FL-ABC-025 | Extintor ABC 25 kg sobre ruedas | 3569 | 3550 | catálogo pág. 5 · recipiente 25 kg R3 |
| FL-ABC-050 | Extintor ABC 50 kg sobre ruedas | 3569 | 3550 | catálogo pág. 5 · recipiente 50 kg R2 |
| FL-ABC-070 | Extintor ABC 70 kg sobre ruedas | 3569 | 3550 | catálogo pág. 5 |
| FL-ABC-100 | Extintor ABC 100 kg sobre ruedas | 3569 | 3550 | catálogo pág. 5 · rodante 100 kg R1 (Ø390) |

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
python generar.py FL-ABC-004      # uno
```

Estructura del código:
`flama/catalogo.py` (datos), `flama/modelo3d.py` (sólidos), `flama/vistas.py`
(proyección HLR y cortes), `flama/lamina.py` (formato, rótulo, capas, cotas,
soldadura), `flama/planos.py` (hojas 1–3), `flama/exportar.py` (DXF/PDF/STEP),
`flama/normas.py` (normativa).
