# Relevamiento de rotulado: norma + mercado → especificación FLAMA

Fuentes. Las normas se citan por apartado y no se transcriben:
- IRAM 3534, 3523, 3550, 3504 y 3517-2.
- IRAM Anexo R.
- Res. OPDS 522/07 y Ord. 40.473.

El relevamiento son 24 fotos de equipos instalados y de la línea de etiquetado (2026):
- Fabricantes: Georgia, Melisam, Fadesa, Horizonte, De León y Maxiseguridad.
- Recargadores: Suyai y Firegram.

La especificación de cada modelo está en la **hoja 4** de su plano FL_MAT. Las piezas están en la BOM, subconjunto S6.

## 1. Etiqueta (placa de características)

| Tema | Norma | Mercado (fotos) | FLAMA adopta |
|---|---|---|---|
| Extensión | IRAM 3534 2.2.4.3: las instrucciones no superan un arco de 108° | La etiqueta envuelve ≈ 200–250°, con columnas laterales de datos y mantenimiento (Georgia, Melisam, Fadesa) | Panel central de 108° con instrucciones, más dos alas de 54° (72° si Ø < 100) |
| Encabezado | 2.2.1 2° marca; 3° a) tipo "MATAFUEGO…" | Marca grande y "EXTINTOR DE POLVO BAJO PRESIÓN" | "FLAMA" y la leyenda de tipo de la norma del producto ("MATAFUEGO A POLVO BAJO PRESIÓN") |
| Instrucciones | 2.2.1 1°: prominentes, con distancia; letra de 3–8 mm (< 9 kg) o 6,5–10 mm (≥ 9 kg) | 3 pasos numerados con ilustración: "ROMPA EL PRECINTO / QUITE EL SEGURO", "COLÓQUESE A 3 m" (1,5 m en 1 kg), "ACCIONE LA PALANCA Y DIRIJA EL CHORRO A LA BASE DEL FUEGO"; la AFFF rodante lleva 4 pasos | Los mismos pasos, adaptados por agente: CO₂, clase K, clase D, AFFF y rodantes |
| Clases | 2.2.2 símbolos ≥ 12 mm; 2.2.3 pictogramas ≥ 18 mm, tachados si no es apto | Fila "PARA FUEGOS CLASE" con el símbolo y el pictograma juntos | Igual |
| Uso eléctrico | — | "APTO PARA INSTALACIONES ELÉCTRICAS" / "NO APTO PARA USAR EN ELECTRICIDAD" | Leyenda en el panel central |
| Logos | 3523 5.2.4 p) Sello IRAM | IRAM, OPDS, GCBA, DPS y QR | Sello IRAM, OPDS, GCBA, DPS y QR a la ficha técnica |
| Datos (ala izq.) | 3534 3° b, c, d, h, i; 3523 5.2.4 (mes/año, n° de recipiente); 7.13 e) | Melisam muestra capacidad, potencial, año, marca del polvo, Ps y PH | Capacidad, agente y grado con marca, potencial + advertencia, Ps, PH, temperaturas, peso total, mes/año, n° de recipiente, "Industria Argentina" |
| Mantenimiento (ala der.) | 3534 3° e, f, g; 3523 5.2.4 j, n, o | Controles mensual, anual y PH cada 5 años; aviso de no mezclar polvos; "presurizar sólo con N₂ seco" | Igual, con el texto del agente por tipo |
| Pie | — | Fadesa: "Habilit. Ord. Mun. 40473 – C.H.A.S. – O.P.D.S. Registro" | FLAMA, domicilio, "Industria Argentina", Ord. 40.473 n°, OPDS n° y C.H.A.S. n° (1, 2,5 y 5 kg) |

## 2. Identificación debajo de la etiqueta y en la válvula

| Elemento | Norma | Mercado | FLAMA |
|---|---|---|---|
| Oblea PBA Ø46 | Res. 522/07 an. 1, 2 y 6: inmediatamente debajo de la placa | Lila con guilloche; anillo "único sello oficial obligatorio…", DPS, Ley 19.587; campo "próxima revisión de carga"; n° tipo "1H01036888" | Pieza `oblea_pba` y detalle R4 |
| Estampilla IRAM | Anexo R | Rosa con guilloche; n° vertical "A 25 1111053"; sello azul; QR; se aplica con etiquetadora. Georgia la pone entre la etiqueta y la oblea | Al costado de la oblea, para respetar la Res. 522/07 (detalle R5). Alternativa: etiqueta BV "MODELO APROBADO" (Horizonte) |
| Tarjeta CABA | Ord. 40.473 art. 6; Res. AGC 32/15 (dos módulos: papel con QR + etiqueta AGC) | Etiqueta autoadhesiva AGC "Tarjeta de Identificación de Extintor" con QR y campos de domicilio, fabricante, recargador, venc. mantenimiento, fecha de fabricación, venc. VU (fabricación + 20 años), n° de tarjeta, agente, capacidad y n° de extintor | Pieza `tarjeta_caba` ≈ 140 × 55 (detalle R8). Antes figuraba como tarjeta colgante: **corregido** |
| Etiqueta de serie | IRAM 3523 5.1 (trazabilidad) | Melisam: etiqueta blanca con QR GS1 "(01)779…" en el costado | Pieza `etiqueta_serie` 45 × 25 a 180° (detalle R7) |
| Faja de garantía | — (garantía comercial) | Georgia: cinta rayada roja y blanca, "ATENCIÓN – la rotura total de esta cinta interrumpe la garantía" | Pieza `faja_garantia` 30 × 40 sobre la unión válvula-cuello (detalle R6). Es el "precinto de apertura" que indica equipo nuevo |
| Precinto | IRAM 3517-2 9.4.13; 3523 3.3.2 | Precinto plástico de color con el nombre del fabricante o recargador (Suyai, Melisam) | Pieza `precinto`: color, "FLAMA" y lote |

## 3. Recargas (no van en el equipo nuevo, sí en la BOM de recargas)

Las fotos de Suyai y Firegram muestran estos elementos:
- Etiqueta de servicio del recargador: n° de extintor, serie, próxima recarga, próxima PH e IRAM 3517-2.
- Precinto de color con el nombre del recargador.

Las normas agregan dos más:
- Oblea PBA de recarga y estampilla-precinto de 1" × 200 mm (Res. 522/07).
- Tarjeta AGC (Ord. 40.473).

Todo esto se agregó a la hoja **Recargas** de la BOM.

## 4. Corrección de datos

- **Potencial del 1 kg con DEM-60:** la licencia IRAM 3523 de Drago (anexo I) dice **1A-5B**. 1A-3B corresponde al polvo Pyrochem. Se corrigió en `flama/agentes.py`, que antes decía 1A-3B:C.

## 5. Pendientes y supuestos

- Medidas reales de la estampilla IRAM (60 × 40), de la tarjeta AGC (140 × 55) y de la faja (30 × 40). Están estimadas a partir de las fotos; hay que confirmarlas con IRAM, con la AGC y con el proveedor.
- 1 kg: la tarjeta AGC no entra en el cuerpo. Se asume que el 1 kg de uso vehicular no la lleva; confirmarlo con la AGC.
- ~~Vida útil~~ RESUELTO: Res. 349/07 art. 26 (mod. 717/07) fija 20 años desde la fabricación (CO₂ 30) y obliga al fabricante a declararla; la tarjeta AGC la incluye. Se agregó a la etiqueta.
- C.H.A.S. (Res. 91/2001): pendiente de leer. Por ahora es un campo a completar en 1, 2,5 y 5 kg.
- Arte final de las ilustraciones de los pasos y de los pictogramas: lo hace el proveedor de etiquetas. El plano fija las posiciones y los tamaños mínimos.
- Números de registro de OPDS, Ord. 40.473 y C.H.A.S.: se completan cuando FLAMA esté inscripta.

## 6. Agregados posteriores (Res. 349/07 PBA y Res. AGC 32/15)

- Cuño DPS de 15 × 7 mm junto al n° del extintor, en pollera u ojiva (Res. 349/07 anexo IV): agregado al marcado grabado (hoja 4 y cilindros).
- Extintor sustituto (IRAM 3517-2:2020 9.4.5): faja amarilla de 40 mm como máximo en la pollera, con 3 leyendas; tarjeta DPS «sustituto habilitado» (Res. 349/07 art. 32); tarjeta AGC «Es sustituto». Planos FL_SUS_*.
- Identificación de recarga completa (IRAM 3517-2, Res. 522/07, Res. 349/07 art. 21 y 28-29, Res. AGC 32/15): lámina FL_SEN_09.
