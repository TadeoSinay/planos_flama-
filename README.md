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

## Planos y documentos complementarios

Base normativa leída en su texto completo: **IRAM 3517-2:2020** (dotación, elección, instalación,
señalización, control, mantenimiento y recarga) y **IRAM de Emergencia 3504:2001** (extintores de gases
limpios). Cada lámina y documento cita el apartado. Los PDF de las normas tienen licencia de IRAM y
**no se incluyen en el repositorio**.

Se generan con `python generar.py --complementarios` (o con `python generar.py` sin argumentos).
`salida/FLAMA_complementarios.pdf` junta las 22 láminas y los 5 documentos.

| Carpeta | Código | Contenido |
|---|---|---|
| `salida/cilindros/` | `FL_REC_ABC_1kg` … `FL_REC_ABC_100kg` + `despiece/FL_DES_REC_*` + `FLAMA_cilindros.pdf` | **Cilindros (recipientes ABC sueltos)**, plano de 3 hojas: (1) fabricación: vista, corte A-A, vista D, detalles, cotas con tolerancias; (2) verificación normativa contra IRAM 3523 / 3550 (material, espesor y fórmula 3550 4.1.3, costuras, abertura, estanquidad, expansión, rotura, niebla salina, marcado) y plan de inspección y ensayos por lote; (3) identificación, tapón, protocolo de ensayo y embalaje. Despiece con globos ligado al BOM. DXF + PDF + STEP |
| `salida/sustituto/` | `FL_SUS_00` … `FL_SUS_<tipo>` + `FLAMA_sustitutos.pdf` | **Extintores sustitutos** (IRAM 3517-2:2020 9.4.5; Res. 349/07 art. 32; Res. AGC 32/15): por modelo, faja amarilla ≤ 40 mm en la pollera acotada y desarrollada con sus 3 leyendas, isometría y lista; tarjeta DPS «sustituto habilitado» (PBA) y AGC «Es sustituto» (CABA). FL_SUS_00: equivalencias (igual clase, capacidad ≥) y ciclo de préstamo |
| `salida/senaletica/` | `FL_SEN_01` | Chapa baliza vertical 350 × 870 (y 260 × 870): franjas de 100 mm a 45°, borde fotoluminiscente de 15 mm, tipos de fuego 140 × 140, datos del PRS y n° de puesto (7.2.5, fig. 3); puesto de incendio con alturas (6.2.14, 7.3) |
| | `FL_SEN_02` | Cartel tridimensional de señalización en altura, caras ≥ 280 × 220 a 2,0-2,5 m (7.3, fig. 5) |
| | `FL_SEN_03` | Tipos de fuego: símbolo (letra en contorno) + pictograma, colores IRAM-DEF D 1054 (7.2.2, fig. 1); clases por modelo |
| | `FL_SEN_04` | Etiqueta de control celeste 35 × 50 con frecuencia (8.3.3), "fuera de servicio" 110 × 150 (fig. 8), oblea (9.4.14), numeración (fig. 2), rótulo de manguera 20 × 30 (9.7.1.4) |
| | `FL_SEN_05` | **Sistema de pictogramas NFPA 10 (Anexo B)** por modelo (referencia internacional) |
| | `FL_SEN_06` | Extintor de reserva (faja verde) y sustituto (faja amarilla) (5.3, 9.4.5); placa IRAM 3534 |
| | `FL_SEN_07` | Chapas horizontales o de piso 800 / 500 (fig. 4), chapa de baldes 500 × 500 (fig. 6) y balde 5-7 L (6.2.19) |
| | `FL_SEN_08` | Marbete (anillo plano y cónico, D 33/36/40/50, color por año, fig. 9, tabla 4) y marbete por modelo; traba y precinto (9.4.13) |
| `salida/accesorios/` | `FL_ACC_01` … `03` | Soporte de pared, soporte vehicular y gabinete (7.4), modelados en 3D, 3 vistas ISO E + isometría, STEP |
| `salida/esquemas/` | `FL_ESQ_01` … `03` | Banco de prueba hidrostática (9.7) con presiones de los 17 modelos; línea de carga ABC (9.4.8, 9.4.9); flujo de recarga |
| `salida/documentos/` | `DOC-01` | Tratamiento superficial y pintura: granallado Sa 2½, fosfatizado, polvo poliéster rojo 03-1-050, controles y **saponificación** |
| | `DOC-02` | **Ensayos de fabricación ABC**: rutina, lote y tipo |
| | `DOC-03` | **Control, mantenimiento y recarga por tipo** según IRAM 3517-2:2020 (frecuencias, PH, tabla 3, gas impulsor, recinto de polvo, marbete, inutilización) |
| | `DOC-04` | **NFPA 10 frente a IRAM**: símbolos y colores, pictogramas, NFPA 704, alturas, distancias, intervalos |
| | `DOC-05` | **Ensayos de fabricación HCFC/HFC** según IRAM 3504 |

Origen de cada valor en los documentos: **C** catálogo FLAMA, **N** norma leída, **N\*** norma hermana
aplicada por analogía (IRAM 3504 para criterios de rotura y expansión de los ABC), **R** valor de referencia
a confirmar con la norma de fabricación.

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

| Norma | Título | Qué se aplica en las láminas |
|---|---|---|
| IRAM 4501 | Dibujo técnico. Métodos de proyección | Método ISO E: superior (B) debajo de la anterior (A), lateral izquierda (C) a su derecha; símbolo junto a la escala en el rótulo |
| IRAM 4502 | Dibujo técnico. Líneas | Grupo 0,7: A continua gruesa 0,7 (visibles), E trazos **media** 0,35 (ocultas), B continua fina 0,18 (cotas, rayados, referencias, fondos de rosca), F trazo largo y corto fina 0,18 (ejes y centros), G fina con extremos gruesos (plano de corte). Relación 4:2:1 |
| IRAM 4503 | Dibujo técnico. Letras | Letra tipo B vertical; alturas 1,8 · 2,5 · 3,5 · 5 · 7 |
| IRAM 4504 | Formatos, elementos gráficos y plegado de láminas | A3 / A2; recuadro a **25 mm** del borde izquierdo y 10 mm de los demás; marcas de centrado y zonas |
| IRAM 4505 | Dibujo tecnológico. Escalas | Sólo 1:1, 1:2, 1:5, 1:10, 1:20 y 2:1, 5:1; se elige la mayor que entra en A3 o A2 |
| IRAM 4507 | Dibujo técnico. Representación de secciones y cortes | CORTE A-A por el plano de simetría, con letras y flechas |
| IRAM 4508 | Rótulo, lista de materiales y despiezo | Rótulo **175 × 51 mm**; lista de materiales del mismo ancho sobre el rótulo: posición, cantidad, denominación, código, material, **peso**, observaciones |
| IRAM 4509 | Dibujo técnico. Rayados indicadores de secciones y cortes | 45° con línea fina, orientación alternada en piezas contiguas, secciones delgadas ennegrecidas |
| IRAM 4513 | Dibujo técnico. Acotación | Flecha de triángulo lleno **1:4**; separación ≥ altura de cifra; cotas fuera del contorno; coma decimal |
| IRAM 4520 | Dibujo tecnológico. Representación de roscas y partes roscadas | Rosca interior en corte: cresta gruesa, fondo fino |
| IRAM 4540 | Dibujo técnico. Representación de vistas en perspectiva | Isometría con ejes a 120°, sin ocultas |
| ISO 2553 / 4063 | Soldaduras | Filete todo alrededor; proceso **131 MIG** (acero al carbono) o **141 TIG** (inoxidable) |
| ISO 2768-1 | Tolerancias generales | Clase m |

Los datos de las normas IRAM de dibujo (márgenes, rótulo, líneas, flechas, rayados)
se tomaron de resúmenes publicados de cada norma. El texto completo es material
protegido de IRAM y hay que consultarlo en la edición vigente.

## Qué distingue a cada tipo (no sólo las dimensiones)

| Tipo | Recipiente | Válvula | Descarga |
|---|---|---|---|
| ABC / BC / HCFC-HFC | chapa acero SAE 1010, costura MIG, fondo cóncavo con pollera | latón forjado, manómetro IRAM 3533 | manguera + tobera con portatobera (1 kg: tobera directa, sin manguera) |
| Clase D | idem 10 kg | idem | manguera + **lanza aplicadora de flujo suave** con empuñadura |
| Agua | **acero inoxidable AISI 304, costura TIG** | idem | manguera + **tobera de chorro pleno** |
| AFFF | inoxidable, TIG | idem | manguera + **lanza espumígena** con 4 tomas de aire |
| Sales K | inoxidable, TIG | idem | manguera + **lanza aplicadora larga** con boquilla de niebla |
| CO₂ | **cilindro sin costura 34CrMo4, cuello integral**, pie de apoyo | **sin manómetro, con disco de seguridad** | 2 kg: brazo giratorio + difusor; 5 kg: manga de alta presión + difusor con empuñadura y soporte |
| Rodantes ABC | recipiente con dos cabezales, bastidor de caño, ruedas de caucho macizo | idem con manómetro | manguera enrollada + válvula esférica + tobera campana |
| Rodante AFFF 50 l | idem | idem | válvula esférica + **lanza espumígena** |

## Verificaciones automáticas (`verificar.py`)

- Altura y ancho de cada modelo igual al catálogo (±0,05 mm). La profundidad incluye el suncho.
- **Masa**: la suma de la lista de materiales (volumen × densidad) + carga nominal se compara con el peso cargado del catálogo. Da entre −8 % y +12 % en los 17 modelos; el ABC 10 kg da −2 % y su recipiente 5,24 kg, contra 5,48 kg del plano de referencia.
- IRAM 4504 recuadro 25/10, IRAM 4508 rótulo 175 × 51, IRAM 4502 grupo de líneas, IRAM 4513 flecha 1:4, escalas normalizadas, 3 presentaciones, rótulos completos y ningún "A definir".

## Materiales

Ya no queda ningún "A definir". Se respetan los materiales que da el catálogo
(chapa de acero / inoxidable, válvula de latón forjado, manga de caucho sintético,
manómetro con sello IRAM 3533). Para el resto se especifican los materiales
habituales de cada componente: acero SAE 1010 en cuello, manijas y sunchos;
inoxidable AISI 304 en eje y pasador; PVC o polipropileno en el sifón;
polipropileno en toberas y lanzas; polietileno AD aislante en el difusor de CO₂;
caucho macizo y chapa en las ruedas. Ver `flama/materiales.py`.

## Pendientes a confirmar por FLAMA

1. **Clase D 9 l**: el catálogo de referencia sólo tiene clase D de 5 y 10 kg; se usa el recipiente de 10 kg.
2. **Rosca de la válvula de CO₂**: se indica cónica 25E (ISO 11363-1); confirmar con el proveedor del cilindro.
3. **Espesores derivados** (Agua, AFFF, Sales K: 0,8 mm inox; CO₂: 5,4 / 6,0 mm; 70 kg): elegidos para que la masa coincida con el catálogo; confirmar con cálculo a presión de ensayo.
4. Firmas "Revisó" y "Aprobó" del rótulo.
5. Normas de fabricación **IRAM 3523** (polvo manual) y **IRAM 3550** (polvo rodante): confirmar los valores
   N\* y R de DOC-02 (rotura, expansión, ensayos de tipo). **IRAM 3504**: se leyó la edición de emergencia 2001;
   confirmar la vigente. **IRAM 10005**: el archivo recibido es un resumen, no la norma.
6. Pictogramas de las figuras 1 y 5 de IRAM 3517-2 y de NFPA 10: los dibujos son esquemáticos; para imprimir,
   usar los originales de cada norma.

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
`flama/normas.py` (normativa), `flama/recipientes.py` (recipientes sueltos),
`flama/senaletica.py`, `flama/accesorios.py`, `flama/esquemas.py`, `flama/documentos.py`.

## BOM y planos de despiece

`python generar.py --bom` genera **`salida/bom/FLAMA_BOM.xlsx`** y `python generar.py --despiece` genera
**`salida/despiece/FL_DES_<modelo>.dxf/.pdf`** (más `FLAMA_despieces.pdf` con las 17 láminas). Ambos salen del
mismo modelo 3D que los planos FL_MAT / FL_REC, así que código, posición, material, medida y peso coinciden.

| Hoja del Excel | Contenido |
|---|---|
| `01_Indice` | Origen, alcance, niveles, subconjuntos, regla «Entra MRP», códigos, fuentes y **colores de estado** |
| `02_Decisiones` | Decisiones de diseño y abastecimiento con su fundamento (fabricación propia sólo ABC, MRP, polvo DEMSA / Polvex, MAG Arcal 21, varilla, carro propio, tapas, pintura, granallado, inoxidables) |
| `03_Resumen_Productos` | Los 17 productos: agente, carga, gas, pesos frente al catálogo, ítems que entran en MRP |
| `04_BOM_Matafuegos` / `05_BOM_Cilindros` / `06_BOM_Sustitutos` | Tablas planas filtrables (17 FL_MAT, 8 FL_REC, 17 FL_SUS) |
| `07_BOM_Recargas` | Kits RK-*-A/B/C por extintor y caso (IRAM 3517-2:2020), con MRP y proveedor |
| `08_Quimica_Agentes` / `09_Carga_N2` | Densidades (aparente y empacada) y volumen libre, gas impulsor y control de llenado por fórmula |
| `10_Proveedores` | Proveedores nacionales por ítem (principal y alternativa, domicilio, distancia a Avellaneda, precio de referencia, estado) y directorio |
| `11_Validacion_MP` | Respaldo documental y estado de cada materia prima y componente |
| `12_Explosion_MP` | Explosión por unidad de lo que entra en MRP (base del futuro archivo MRP_MATERIA_PRIMA) |
| `13_Fuentes` / `14_Comparacion_Mercado` / `15_Indice_Planos` | Documentos citados, peso contra fabricantes con sello IRAM, índice de planos |
| `BOM_FL_MAT_*` / `BOM_FL_REC_*` | Una hoja por plano: BOM multinivel plegable con fórmulas de peso |

Columnas del BOM: … Origen · **Entra MRP** · **Proveedor principal** · **Alternativa** · Operación · Norma · Fuente ·
Plano · Observaciones. Colores de fila: sin color = validado · **amarillo** = estimado con justificación (norma o
fuente técnica) · **naranja** = a validar (falta dato, cotización o confirmación) · **rojo** = no cumple o decisión
pendiente. Revendidos: el BOM queda completo como referencia y en MRP entra sólo la fila S0 «Equipo terminado
comprado». Proveedores en `flama/proveedores.py`.

Subconjuntos: S1 recipiente (en los ABC = plano FL_REC) · S2 válvula · S3 descarga · S4 carro · S5 carga ·
S6 identificación y precinto · S7 embalaje · S8 soporte · S0 equipo terminado comprado (revendidos).
