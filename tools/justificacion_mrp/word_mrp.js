// Word «Justificación_MRP»: fuente, cálculo y control de cada valor de salida/mrp/FLAMA_MRP.xlsx, con las capturas
// marcadas de los procesos, cotizaciones y planillas citadas. Lee el JSON de datos_mrp.py. Sólo negro y grises.
// Uso: node word_mrp.js <datos.json> <salida.docx>
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell, WidthType, ShadingType, HeadingLevel,
  AlignmentType, Footer, PageNumber, LevelFormat, BorderStyle, LineRuleType,
} = require("docx");

const D = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const OUT = process.argv[3];
const AQUI = __dirname;

const W = 10306;
const FONT = "Arial";
const NEGRO = "000000", GRIS_O = "595959", GRIS_M = "BFBFBF", GRIS_C = "EDEDED";
const fino = { style: BorderStyle.SINGLE, size: 4, color: GRIS_M };
const bordes = { top: fino, bottom: fino, left: fino, right: fino };
const nada = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
const sinBordes = { top: nada, bottom: nada, left: nada, right: nada, insideHorizontal: nada, insideVertical: nada };

const n = (x, d = 2) => (x === null || x === undefined || x === "") ? "—" :
  Number(x).toLocaleString("es-AR", { minimumFractionDigits: 0, maximumFractionDigits: d });
const sg = (x, d = 1) => (x === null || x === undefined) ? "—" : Math.abs(x) < 0.5 * 10 ** -d ? "0 %" :
  (x > 0 ? "+" : "−") + n(Math.abs(x), d) + " %";
const pc = (x, d = 1) => (x === null || x === undefined) ? "—" : n(100 * x, d) + " %";

const t = (text, o = {}) => new TextRun({ text: String(text), font: FONT, size: o.size || 18, bold: o.bold,
  italics: o.italics, color: o.color || NEGRO });
const p = (runs, o = {}) => new Paragraph({ children: Array.isArray(runs) ? runs : [t(runs, o)],
  spacing: { after: o.after ?? 80, before: o.before ?? 0 }, alignment: o.align, heading: o.heading, keepNext: o.keepNext,
  numbering: o.bullet ? { reference: "vinetas", level: 0 } : undefined });
const h1 = (x) => p(x, { heading: HeadingLevel.HEADING_1, keepNext: true, before: 200 });
const h2 = (x) => p(x, { heading: HeadingLevel.HEADING_2, keepNext: true, before: 120 });
const nota = (x, o = {}) => p(Array.isArray(x) ? x : [t(x, { size: 16 })], { after: o.after ?? 60, keepNext: o.keepNext });
const vin = (x) => p(Array.isArray(x) ? x : [t(x, { size: 17 })], { bullet: true, after: 30 });

function celda(c, ancho, o = {}) {
  const paras = (Array.isArray(c) ? c : [c]).map((x) => x instanceof Paragraph ? x :
    new Paragraph({ alignment: o.align, spacing: { after: 0 },
      children: [t(x === null || x === undefined ? "—" : String(x), { size: o.size || 14, bold: o.bold, color: o.color })] }));
  return new TableCell({ children: paras, width: { size: ancho, type: WidthType.DXA }, borders: bordes,
    shading: o.fill ? { type: ShadingType.CLEAR, color: "auto", fill: o.fill } : undefined,
    margins: { top: 20, bottom: 20, left: 60, right: 60 } });
}

function tabla(cols, cab, filas, o = {}) {
  const k = W / cols.reduce((a, x) => a + x, 0);
  const cw = cols.map((x) => Math.round(x * k));
  const num = new Set(o.num || []);
  const head = new TableRow({ tableHeader: true, cantSplit: true,
    children: cab.map((h, i) => celda(h, cw[i], { bold: true, color: "FFFFFF", fill: NEGRO, align: AlignmentType.CENTER })) });
  const rows = filas.map((f, j) => {
    if ((o.grupo || []).includes(j)) return new TableRow({ cantSplit: true, children: [new TableCell({ columnSpan: cols.length,
      width: { size: W, type: WidthType.DXA }, borders: bordes, shading: { type: ShadingType.CLEAR, color: "auto", fill: GRIS_C },
      margins: { top: 20, bottom: 20, left: 60, right: 60 },
      children: [new Paragraph({ spacing: { after: 0 }, children: [t(f[0], { bold: true, size: 14 })] })] })] });
    return new TableRow({ cantSplit: true, children: f.map((c, i) => celda(c, cw[i], {
      align: num.has(i) ? AlignmentType.RIGHT : undefined, bold: (o.negrita || []).includes(j) })) });
  });
  return [new Table({ width: { size: W, type: WidthType.DXA }, columnWidths: cw, rows: [head, ...rows] }),
    p("", { after: o.after ?? 100 })];
}

// ------------------------------------------------------------------ capturas
const CAP = Object.fromEntries(D.capturas.map((x) => [x.id, x]));
function bloqueFigura(f, ancho) {
  const maxH = ancho > 400 ? 860 : 360;
  let w = Math.min(ancho, f.w), h = Math.round(f.h * w / f.w);
  if (h > maxH) { h = maxH; w = Math.round(f.w * maxH / f.h); }
  const png = path.join(AQUI, f.png);
  const img = new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 30 },
    children: [new ImageRun({ type: "png", data: fs.readFileSync(png), transformation: { width: w, height: h },
      altText: { title: f.id, description: f.titulo, name: f.id } })] });
  const cab = new Paragraph({ spacing: { after: 20 }, keepNext: true,
    children: [t(`${f.id} · `, { bold: true, size: 16 }), t(f.titulo, { bold: true, size: 16 })] });
  const marcas = new Paragraph({ spacing: { after: 80 }, children: (f.marcas || []).flatMap((m, i) => [
    t(`${m.n} `, { bold: true, size: 13, color: "C00000" }), t(m.etiqueta + (i < f.marcas.length - 1 ? "  ·  " : ""), { size: 13 })]) });
  return [cab, img, marcas];
}
const sep = () => new Paragraph({ spacing: { after: 0, before: 0, line: 20, lineRule: LineRuleType.EXACT }, children: [] });
function figs(ids) {
  const lista = ids.map((i) => { if (!CAP[i]) throw new Error("falta la captura " + i); return CAP[i]; });
  const out = [];
  const CW = Math.floor(W / 2);
  let par = [];
  const vaciar = () => {
    if (!par.length) return;
    out.push(new Table({ width: { size: W, type: WidthType.DXA }, columnWidths: [CW, CW], borders: sinBordes,
      rows: [new TableRow({ cantSplit: true, children: [par[0], par[1]].map((f) => new TableCell({ width: { size: CW, type: WidthType.DXA },
        borders: sinBordes, margins: { top: 60, bottom: 60, left: 80, right: 80 },
        children: f ? bloqueFigura(f, 330) : [new Paragraph({ children: [] })] })) })] }), sep());
    par = [];
  };
  lista.forEach((f) => {
    if (!f.medio) {
      vaciar();
      out.push(new Table({ width: { size: W, type: WidthType.DXA }, columnWidths: [W], borders: sinBordes,
        rows: [new TableRow({ cantSplit: true, children: [new TableCell({ width: { size: W, type: WidthType.DXA }, borders: sinBordes,
          margins: { top: 60, bottom: 60, left: 80, right: 80 }, children: bloqueFigura(f, 680) })] })] }), sep());
    } else {
      par.push(f);
      if (par.length === 2) vaciar();
    }
  });
  vaciar();
  return out;
}

const PA = Object.fromEntries(D.par.map((x) => [x.id, x]));
const PY = Object.fromEntries(D.par_y.map((x) => [x.id, x]));
const LIN = ["MANUALES", "RODANTES", "RECARGAS", "REVENDIDOS"];
const POL = Object.fromEntries(D.politica.map((x) => [x["Código"], x]));
const CMP = Object.fromEntries(D.compras.map((x) => [x["Código"], x]));
const V = Object.fromEntries(D.validacion.map((x) => [x.dato, x]));
const tot = D.totales;
const hijos = [];

// ------------------------------------------------------------------ portada y resumen
hijos.push(new Paragraph({ spacing: { after: 60 }, children: [new TextRun({ text: "Justificación del MRP", font: FONT, size: 40, bold: true })] }));
hijos.push(p([t("FLAMA S.A. · fuente, cálculo y control de cada valor de FLAMA_MRP.xlsx · octubre de 2026", { size: 18, color: GRIS_O })], { after: 160 }));
[
  "El MRP calcula el requerimiento bruto anual 2026–2035 de cada insumo por línea (manuales, rodantes, recargas con los sustitutos y revendidos), lo consolida por ítem y dimensiona la política de stock para el año 10 (2035): consumo diario, lead time, stock de seguridad, punto de pedido, lote en múltiplos de la unidad de compra, stock máximo y lugar en el almacén.",
  "Está indexado como el BOM: cada dato entra una sola vez en una hoja fija (PARAMETROS, DEMANDA, ESTACIONALIDAD, BOM_COEF, FAB_COMPRA, PROCESO, COMPRAS) y las demás lo leen por ID o por referencia de celda. Cada fila dice de qué celda sale su coeficiente.",
  "Fuentes: Proyecciones (demanda), FLAMA_BOM.xlsx (qué lleva cada producto), procesos de manuales y de carros (rendimientos y consumos de cada puesto), cotizaciones (lead times y unidades de compra), Dimensionamiento Técnico (estacionalidad) y la planilla de MP del equipo para lo que ningún documento trae, siempre marcado como estimado.",
  "Capturas: P = documento de proceso, Q = cotización, X = planilla fuente, M = hoja del propio MRP. El dato que se toma está marcado en rojo.",
].forEach((x) => hijos.push(vin(x)));
hijos.push(h2("Resultado de la revisión"));
const vv = (k) => V[k];
hijos.push(...tabla([28, 72], ["Control", "Resultado"], [
  ["Fórmulas", "Unas 32.500 fórmulas, ninguna con error después del recálculo (LibreOffice)."],
  ["Demanda del año de diseño", `2035: ${n(tot.MANUALES[9], 0)} recipientes de manuales, ${n(tot.RODANTES[9], 0)} de carros, ${n(tot.RECARGAS[9], 0)} recargas (con el pool y el alta de sustitutos) y ${n(tot.REVENDIDOS[9], 0)} revendidos.`],
  ["Estacionalidad", `Factor de pico de manuales ${n(D.lineas.MANUALES.factor, 3)} contra ${n(1665 / 1184, 3)} del proceso (1.665 / 1.184 cilindros por día). Carros: ${n(D.lineas.RODANTES.factor, 2)} con el perfil del Dimensionamiento; el proceso de carros supone 1,43 (promedio = 70 % del pico).`],
  ["Contraste con los procesos", `Caños de 1 kg ${sg(vv("Caños Ø76,2 de 1 kg por día (pico)").dif)}, granalla ${sg(vv("Granalla de manuales, kg por día (pico)").dif)}, nitrógeno ${sg(vv("Nitrógeno de manuales, m³ por día (pico)").dif)}, gas MAG ${sg(vv("Gas MAG de manuales, m³ por día (pico)").dif)}, hojas de 4,75 mm por año ${sg(vv("Hojas LAC 4,75 de carros por año").dif)}. Las diferencias mayores tienen causa identificada (sección 8).`],
  ["Lead times", `${D.compras.length} ítems: ${D.origen_lt["Cotización"]} salen de una cotización, ${D.origen_lt["Proceso"]} de los procesos, ${D.origen_lt["Planilla de MP"]} de la planilla de MP (estimado del equipo) y ${D.origen_lt["Supuesto"]} son supuestos a confirmar.`],
  ["Almacenes", "La calle de chapa y el rack de casquetes y cuplas de carros alcanzan; al rack de insumos de montaje de carros le falta 1 posición (ruedas). El resto da los m² que tiene que prever el layout."],
  ["Correcciones", "Fleje del fondo de 1 kg (1,25 × 135), fleje de la cúpula de 10 kg (1,6 mm), alambre de carros (Ø1,0), polvo de carros (ABC 90), tubos por día del proceso de manuales (53, no 97)."],
]));

// ------------------------------------------------------------------ 1. estructura
hijos.push(h1("1. Cómo está armado el MRP"));
hijos.push(nota("Las hojas fijas se cargan una vez y todo lo demás son fórmulas. Si se pegan Proyecciones nuevas en PROY_INDEXADO y PROY_RESERVAS, o se cambia un parámetro, el MRP entero se recalcula.", { keepNext: true }));
hijos.push(...tabla([22, 78], ["Hoja", "Qué tiene"], [
  ["PARAMETROS", "Cada dato con ID, valor, unidad y fuente; abajo, los que cambian por año (% de recargas de equipos usados, % del destino CABA)."],
  ["PROY_INDEXADO / PROY_RESERVAS", "Copia (valores) de «Indexado Dim Técnico» y «Reservas y Sustitutos» de las Proyecciones."],
  ["DEMANDA", "Unidades por año de cada producto y línea, con la fila de las Proyecciones de donde sale."],
  ["ESTACIONALIDAD", "Perfil mensual de cada producto y perfil ponderado de cada línea en el año de diseño."],
  ["BOM_COEF", "Lo que se compra por unidad, fila por fila del BOM, y en recargas por servicio y mezcla del año."],
  ["FAB_COMPRA", "De qué materia prima sale cada pieza fabricada y cuánto rinde."],
  ["PROCESO", "Insumos de proceso y embalaje por unidad, puesto por puesto."],
  ["COMPRAS", "Catálogo: tipo, clase, almacén, proveedor, unidad de compra, lead time con su origen y fuente, días entre pedidos."],
  ["INSUMOS_DIRECTOS_* / INSUMOS_INDIRECTOS_*", "Por línea: para cada ítem una fila de total y una por producto (coeficiente × demanda × % de destino)."],
  ["CONSOLIDADO_INSUMOS", "Por ítem: tipo, clase, almacén, de qué línea y hoja sale, requerimiento por año y en unidades de compra."],
  ["POLITICA_STOCK", "Año de diseño: consumo diario, lead time, stock de seguridad, punto de pedido, lote, stock máximo, posiciones y m²."],
]));
hijos.push(h2("Decisiones acordadas"));
hijos.push(...tabla([20, 40, 40], ["Decisión", "Qué se hizo", "Por qué"], [
  ["Horizonte", "Requerimiento bruto anual 2026–2035; política de stock del año 10 (2035).", "La planta arranca sin stock ni pedidos en curso: un MRP mensual de diez años no cambia el bruto. El año 10 es el que dimensiona almacenes y lotes."],
  ["Dónde se fija el stock", "Por ítem y almacén, después del consolidado; el puesto sólo tiene su pulmón (carro diario).", "Al proveedor se le compra por ítem y el almacén es por ítem; el polvo y el gas los comparten varias líneas."],
  ["Directo o indirecto", "Directo: queda en el producto o sale con él (BOM, alambre, pintura, N₂, embalaje). Indirecto: se gasta en el puesto (gas MAG, discos, granalla, tapones).", "Criterio único para todas las líneas; es el que después separa costo del producto y gasto del centro de costo."],
  ["Sustitutos", "Van en RECARGAS: el equipo base y el kit de la IRAM 3517-2 9.4.5. Los ABC se fabrican en la línea, pero sus insumos se cargan a recargas.", "Así no se cuentan dos veces y recargas muestra todo lo que le cuesta su pool."],
  ["Costo", "El MRP queda en cantidades; COMPRAS y las hojas usan los mismos códigos para sumar después precios y centros de costo.", "El MRP calcula cantidades y fechas; el costo entra recién en el tamaño de lote económico, cuando haya precios."],
  ["Días entre pedidos (T)", "5 días hábiles para la materia prima crítica y los gases, 10 para lo nacional y los organismos, 20 para lo importado.", "Mientras no haya costo de pedir ni de mantener, el lote es el consumo de T días del pico."],
  ["Destino", "Obleas y tarjetas DPS sólo en la proporción de PBA; tarjeta AGC sólo en la de CABA.", "Cada jurisdicción exige su identificación (Res. 349/07 y 522/07 de PBA; Ord. 40.473 y Res. AGC 32/15 de CABA)."],
]));
hijos.push(...figs(["M01"]));

// ------------------------------------------------------------------ 2. demanda
hijos.push(h1("2. Demanda (hojas PROY_INDEXADO, PROY_RESERVAS y DEMANDA)"));
hijos.push(nota("Toda la demanda sale de las Proyecciones (versión 7). De «Indexado Dim Técnico»: matafuegos nuevos, cilindros vacíos, recargas de clientes (17 tipos), revendidos (9 tipos) y la distribución por zona. De «Reservas y Sustitutos»: la venta de reserva (se suma al ABC 5 kg, IRAM 3517-2 5.3), la recarga anual del pool de sustitutos y el alta anual de sustitutos (9.4.5).", { keepNext: true }));
hijos.push(...tabla([16, ...Array(10).fill(8.4)], ["Línea", ...D.totales.MANUALES.map((_, i) => String(2026 + i))],
  LIN.map((l) => [l, ...tot[l].map((x) => n(x, 0))]), { num: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10] }));
hijos.push(nota("Año de diseño, por producto:", { keepNext: true }));
hijos.push(...tabla([12, 40, 36, 12], ["Línea", "Producto", "De dónde sale", "2035"],
  D.demanda.map((x) => [x.linea, x.producto, x.origen, n(x.d2035, 0)]), { num: [3] }));
hijos.push(h2("Parámetros por año"));
hijos.push(...tabla([30, 14, 14, 14, 28], ["Parámetro", "2026", "2030", "2035", "Fuente"],
  D.par_y.map((x) => [x.dato, pc(x.valores[0], 2), pc(x.valores[4], 2), pc(x.valores[9], 2), x.fuente]), { num: [1, 2, 3] }));
hijos.push(nota("El % de usados sale 4,76 % los diez años en las cuatro hojas de proyección que lo traen. Esa fracción de las recargas lleva la recarga completa; el resto, el mantenimiento anual."));
hijos.push(...figs(["X01", "X02", "X03", "X04", "M02"]));

// ------------------------------------------------------------------ 3. estacionalidad
hijos.push(h1("3. Estacionalidad y año de diseño"));
hijos.push(nota(`Días hábiles: ${n(PA.DH_MES.valor, 0)} por mes y ${n(PA.DH_AÑO.valor, 0)} por año (Dimensionamiento Técnico). Cierra con el proceso de manuales: 72.089 terminados de 2035 / 300 por día = 240 días. Cada producto tiene el perfil mensual del Dimensionamiento; el de la línea es el promedio ponderado por la demanda de 2035.`, { keepNext: true }));
hijos.push(...tabla([30, ...Array(12).fill(5.8)], ["Perfil", "E", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"],
  D.perfiles.map((x) => [x.nombre, ...x.meses.map((m) => pc(m, 1))]), { num: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12] }));
hijos.push(...tabla([20, 46, 14, 20], ["Línea", "Mes de mayor demanda", "Factor de pico", "Proceso"], LIN.map((l) => {
  const m = D.lineas[l].meses; const i = m.indexOf(Math.max(...m));
  return [l, `${["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"][i]} (${pc(m[i], 1)} del año)`,
    n(D.lineas[l].factor, 3), l === "MANUALES" ? "1,406 (1.665 / 1.184)" : l === "RODANTES" ? "1,43 (20 / 14)" : "—"];
}), { num: [2] }));
[
  "Manuales: el factor del MRP (1,405) es el del proceso (1,406), con el mismo dato de base.",
  "Carros: el proceso de carros toma «el promedio como el 70 % del pico» (P09), un supuesto propio. El Dimensionamiento fija la fabricación mensual de carros igual al perfil de ventas industrial (máximo 9 % en un mes): factor 1,08. El MRP usa el perfil, que es un dato. Si se prefiere el supuesto del proceso, se cambia el perfil en ESTACIONALIDAD y todo se recalcula.",
  "El consumo del mes pico de cada ítem suma el de cada línea con su propio perfil mes a mes (POLITICA_STOCK). Un ítem de un solo modelo toma el perfil de su línea: es apenas conservador (5 kg: 1,32 propio contra 1,405 de la línea).",
].forEach((x) => hijos.push(vin(x)));
hijos.push(...figs(["X05", "X06", "P09", "M03"]));

// ------------------------------------------------------------------ 4. coeficientes
hijos.push(h1("4. Coeficientes por unidad"));
hijos.push(h2("4.1 Del BOM a lo que se compra (BOM_COEF)"));
hijos.push(nota("Se recorre cada fila del FLAMA_BOM.xlsx y se decide qué se compra por ella. La columna Fila BOM dice de qué fila sale.", { keepNext: true }));
hijos.push(...tabla([30, 70], ["Fila del BOM", "Qué se compra"], [
  ["Cuerpo, cúpula, fondo y cuello", "Se fabrican o se compran semielaborados: el factor sale de FAB_COMPRA (4.2)."],
  ["Válvula HZ armada (K2) y sus piezas", "Una válvula armada (MP-42 en 1 kg, MP-43 de 2,5 a 10 kg, MP-44 en carros); el espárrago, el vástago, los resortes, la manija y el caño de pesca vienen con ella."],
  ["Dispositivo de descarga (S3) y sus piezas", "Una manguera armada por modelo (racor, manguera, tobera; en carros, válvula esférica y tobera campana)."],
  ["Polvo ABC 60 / ABC 90", `MP-33 (manuales) o MP-33B (rodantes) × (1 + merma ${pc(PA.MERMA_POLVO.valor, 0)}).`],
  ["Gas impulsor N₂ (kg)", `m³ normales = kg × (1 + pérdidas ${pc(PA.N2_PERD.valor, 0)}) / ${n(PA.RHO_N2.valor, 4)} kg/m³ (densidad del BOM).`],
  ["Identificación", "Un ítem por tipo. Oblea de fabricación y tarjetas DPS × % PBA; tarjeta AGC × % CABA."],
  ["Carro", "Manija y caño del eje: caño (largo / 6 m / 0,95); eje: barra trefilada (1 / piezas por barra); neumático: rueda completa (la llanta viene incluida); arandelas × 4, pasadores × 2; triángulos, pata, flejes y placas de refuerzo salen de las orillas del corte (sin compra)."],
  ["Agua, aire comprimido, agente recuperado", "No se compran: agua de red, aire del compresor de planta, agente que se recupera en la prueba hidráulica."],
]));
hijos.push(...tabla([60, 40], ["Tratamiento", "Filas"], Object.entries(D.tratamientos).sort((a, b) => b[1] - a[1]).map(([k, v]) => [k, n(v, 0)]), { num: [1] }));
hijos.push(...figs(["M04"]));

hijos.push(h2("4.2 Piezas fabricadas: de qué materia prima salen (FAB_COMPRA)"));
[
  "Cuerpos: piezas por hoja del plan de corte de cada proceso (27, 12 y 15 en manuales; 9 y 6 en las hojas de 3,2 mm de carros) y tramos de 255 mm por caño de 6 m en el 1 kg (23).",
  "Hoja de 4,75 mm (70 y 100 kg): la hoja RODANTES aplica el plan mixto del proceso: hojas mixtas = mín(cuerpos de 70 / 3; cuerpos de 100) y el resto en hojas de un solo modelo (4 de 70 o 3 de 100). Da 165 hojas en 2035, contra 0,7 por día × 240 = 168 del proceso.",
  "Discos de cúpula y fondo de manuales: kg de fleje por disco = ancho × (Ø del disco + puente) × espesor × 7,85 kg/dm³, con puente = espesor (el proceso programa el paso del alimentador como «diámetro del disco + puente»). Con el ancho y el disco del fleje cotizado reproduce las piezas por bobina de Pacheco (2,5 kg: 1.396 cúpulas por bobina de 492 kg).",
  "Carros: cúpula y fondo son casquetes comprados (MP-15 a 17) y el cuello es una cupla de Eli-Met (MP-20 y 21).",
].forEach((x) => hijos.push(vin(x)));
hijos.push(...tabla([9, 12, 24, 11, 8, 8, 8, 10, 10], ["Modelo", "Pieza", "Se hace en", "Ítem", "Ancho", "Ø disco", "e (mm)", "Rinde", "Ítem por pieza"],
  D.fab.map((x) => [x.modelo, x.pieza, x.hace, x.item, n(x.ancho, 0), n(x.d, 0), n(x.e, 2), n(x.rend, 0), n(x.factor, 5)]),
  { num: [4, 5, 6, 7, 8] }));
hijos.push(...figs(["P02", "P03", "P08", "P07", "Q02", "X10", "M06", "M08"]));

hijos.push(h2("4.3 Insumos de proceso y embalaje (PROCESO)"));
hijos.push(nota("Manuales, por recipiente (terminado o cilindro vacío):", { keepNext: true }));
hijos.push(...tabla([16, 21, 21, 21, 21], ["Modelo", "Gas MAG (m³)", "Alambre Ø0,9 (kg)", "Pintura (kg)", "Granalla (kg)"],
  Object.entries(D.man).map(([k, x]) => [k, n(x["MP-25"], 4), n(x["MP-23"], 4), n(x["MP-31"], 4), n(x["MP-28"], 3)]), { num: [1, 2, 3, 4] }));
[
  `Gas y alambre: coeficientes por modelo de la planilla de MP (largo de costura × caudal y avance). El gas se ajusta por ${n(PA.GAS_MAN_AJ.valor, 3)} para que, con la producción del pico del proceso de manuales (1.216 tramos de 1 kg; 99, 446 y 27 desarrollos de 2,5, 5 y 10 kg), dé los 48 m³ por día del proceso (P01): es el gas de arranque y cierre de cada costura, que la geometría no cuenta.`,
  `Pintura: kg = área exterior × densidad × espesor / 1000 / aprovechamiento, con el área de las dos caras del cuerpo, la cúpula y el fondo del BOM dividida por 2, densidad ${n(PA.PINT_RHO.valor, 2)} g/cm³ y ${n(PA.PINT_ESP.valor, 0)} µm (ficha WEG Politherm) y aprovechamiento ${pc(PA.PINT_APROV.valor, 0)} (cabina con recuperación de polvo, P04; Powder Coating Institute: 95 a 98 %). Es la fórmula de rendimiento teórico m²/kg = 1000 / (densidad × espesor) de Tiger Drylac.`,
  `Granalla: ${n(PA.GRANALLA.valor, 2)} kg por cilindro (proceso de manuales, P04). Tapones de silicona: 1 cada ${n(PA.TAPON_CICLOS.valor, 0)} usos, porque circulan; discos flap: 1 cada ${n(PA.DISCO_MAN.valor, 0)} recipientes; puntas: 1 cada ${n(PA.ALAMBRE_PUNTA.valor, 0)} kg de alambre (planilla de MP, estimados).`,
  "Embalaje (proceso de manuales, P05): una caja por recipiente (simple hasta 5 kg, doble en 10 kg), una etiqueta de caja, un pallet cada 400 / 167 / 90 / 40 recipientes con film y etiqueta de pallet, y un protocolo de ensayo por cilindro vacío.",
  "No entran desengrasante ni fosfatizante (MP-29 y 30 de la planilla): el proceso de manuales prepara la superficie con granallado, sin túnel químico.",
].forEach((x) => hijos.push(vin(x)));
hijos.push(nota("Carros, por unidad, suma de los cinco puestos de soldadura (puntos, longitudinal, cupla, circunferencial y accesorios):", { keepNext: true }));
hijos.push(...tabla([30, 35, 35], ["Modelo", "Gas Ar + 8 % CO₂ (m³)", "Alambre Ø1,0 (kg)"],
  Object.entries(D.carro).map(([k, x]) => [k, n(x["MP-25"], 4), n(x["MP-24"], 4)]), { num: [1, 2] }));
[
  "Cada puesto es una fila de PROCESO con su tabla del proceso de carros (P10 a P14). Los puestos 4 a 7 se aplican a terminados y cilindros; el 8 (accesorios) y el 8.1 sólo a carros terminados.",
  "Discos y mechas del 8.1 (P17): 3 cortes por juego / 200 por disco de sensitiva; 1 disco de corte cada 40 juegos de triángulos; 2 agujeros / 200 por mecha; 2 discos flap por mes en el pico. Placas de refuerzo del 70 y 100 kg (P18): 7 discos de corte y 1,75 flap por mes en el pico para 80 cuerpos. Antiproyecciones: 1 ml por cúpula de un aerosol de 400 ml.",
  "Pintura de carros: tercerizada (P15, «luego del pintado que es tercerizado»), un servicio por unidad (cotización por carro, Q09).",
  "Embalaje de carros: el proceso de carros todavía no tiene escritos los puestos 10 a 13. Se toma una funda de polietileno por carro (investigación de proveedores) y, para los cilindros vacíos, pallets de 24 / 9 / 6 / 6 con film, esquineros y etiqueta (planilla de MP). Queda como estimado.",
].forEach((x) => hijos.push(vin(x)));
hijos.push(...figs(["P01", "P04", "P05", "P10", "P11", "P12", "P13", "P14", "P15", "P16", "P17", "P18", "X08", "M07", "Q09"]));

hijos.push(h2("4.4 Recargas"));
hijos.push(nota(`Coeficiente del año = controles por año × control + (1 − % usados) × mantenimiento + % usados × recarga + prueba hidráulica / años + reposición. Controles: ${n(PA.CTRL_AÑO.valor, 0)} por año (IRAM 3517-2 8.2, trimestral). Prueba hidráulica cada 5 años (polvo, CO₂, agente limpio) o 2 (agua, AFFF, acetato), según el anexo E (está en el BOM). Recarga ABC 5 kg en 2035:`, { keepNext: true }));
hijos.push(...tabla([10, 34, 6, 8, 8, 8, 8, 6, 8, 10], ["Ítem", "Insumo", "UM", "Control", "Mant.", "Recarga", "PH", "Años", "Repos.", "Coef. 2035"],
  D.rec5.map((x) => [x.item, x.pieza, x.um, n(x.ctrl, 0), n(x.mant, 3), n(x.rec, 3), n(x.ph, 0), n(x.anios, 0), n(x.rep, 2), n(x.coef, 4)]),
  { num: [3, 4, 5, 6, 7, 8, 9] }));
[
  `Reposiciones en el mantenimiento de los ABC: válvula ${pc(PA.REPO_VALV.valor, 0)}, manómetro ${pc(PA.REPO_MANO.valor, 0)}, manguera ${pc(PA.REPO_MANG.valor, 0)} (planilla de MP, estimados: la IRAM 3517-2 manda reemplazar lo que no pasa la inspección, sin fijar una tasa). Retoque de pintura: ${pc(PA.P_RETOQUE.valor, 0)} de los equipos (Dimensionamiento, 9.10) × ${n(PA.RETOQUE_L.valor, 2)} L.`,
  "El agente recuperado en la prueba hidráulica, el agua de las premezclas y el aire comprimido no se compran.",
  "Pool de sustitutos: cada equipo del stock se recarga una vez por año con los mismos coeficientes que el tipo de cliente. Alta de sustitutos: el equipo base (el ABC fabricado con todos sus insumos o el equipo de reventa) más el kit de la 9.4.5 (faja amarilla, tarjetas DPS y AGC de sustituto, remito de préstamo).",
].forEach((x) => hijos.push(vin(x)));
hijos.push(...figs(["M05", "X09"]));
hijos.push(h2("4.5 Revendidos"));
hijos.push(nota("Se compra el equipo terminado e identificado por su fabricante y, si va a CABA, se le agrega la tarjeta AGC. No tienen insumos indirectos: la hoja de indirectos lo dice."));

// ------------------------------------------------------------------ 5. consolidado
hijos.push(h1("5. Consolidado de insumos"));
hijos.push(nota("Una fila de total por ítem y debajo una por cada hoja de origen (referencia a la fila de total del ítem en esa hoja), con tipo, clase, almacén, unidad de compra, proveedor y lead time buscados en COMPRAS. Principales ítems en el año de diseño:", { keepNext: true }));
const PRIN = ["MP-01", "MP-02", "MP-03", "MP-04", "MP-05", "MP-13", "MP-06", "MP-07", "MP-08", "MP-09", "MP-10", "MP-11", "MP-12", "MP-15", "MP-16", "MP-17", "MP-18", "MP-19", "MP-20", "MP-21", "MP-33", "MP-33B", "MP-34", "MP-25", "MP-23", "MP-24", "MP-28", "MP-31", "MP-42", "MP-43", "MP-45", "MP-37", "MP-41"];
const CO = Object.fromEntries(D.consolidado.map((x) => [x["Código"], x]));
hijos.push(...tabla([9, 36, 6, 10, 13, 12, 14], ["Código", "Ítem", "UM", "Tipo", "2035", "UC por año", "Unidad de compra"],
  PRIN.filter((c) => CO[c]).map((c) => { const x = CO[c]; return [c, x["Ítem / origen"], x.UM, x.Tipo, n(x["Año de diseño"], 0), n(x["UC en el año de diseño"], 0), x["Unidad de compra"]]; }),
  { num: [4, 5] }));
hijos.push(...figs(["M09"]));

// ------------------------------------------------------------------ 6. lead times
hijos.push(h1("6. Lead times y unidades de compra (hoja COMPRAS)"));
[
  "Orden de las fuentes: 1) cotización del proveedor; 2) documento de proceso de FLAMA (que ya los tomó de la planilla de MP o del proveedor); 3) planilla «MP Abastecimiento» del equipo, marcada como estimada; 4) supuesto, con su razón, a confirmar en la próxima cotización.",
  "De las cotizaciones: Pradecon «7/10 días» (chapa y fleje: se toman 10 días hábiles), Air Liquide «a día + 1» (gases), Eli-Met «35 a 40 días» corridos (28 hábiles), Comercial MID «entrega inmediata» (caño), Polimetal «10 días hábiles» (referencia). Pacheco no informa plazo (se toma el de Pradecon, que cotizó lo mismo) y Hierros Parrotta lo confirma con el pago.",
  "La planilla «Materias Primas» de la investigación tiene la columna de tiempo de entrega vacía (X10): por eso la mayoría sale del proceso o de la planilla de MP.",
  "Búsqueda web: para los casquetes importados se encontró el tránsito marítimo Shanghái – Buenos Aires de 38 a 40 días puerto a puerto (iContainers), que con la fabricación y el despacho cierra con los 60 días hábiles del proceso. Los sitios de los demás proveedores no publican plazos.",
  "Unidades de compra: las del proceso donde las hay (paquetes de 50 / 80 / 20 hojas, atados de 16 tubos, pallets de 400 / 300 / 150 casquetes, cajas de 100 / 40 cuplas, big bags de 1.000 kg) y las cotizadas (rollos de Pacheco de 492 a 738 kg, baterías de 115,5 m³). La planilla traía otras estimadas (atado de 61, pallets de 100 / 80 / 60, cajas de 200 / 50) y se reemplazaron.",
].forEach((x) => hijos.push(vin(x)));
hijos.push(...tabla([10, 36, 18, 6, 10, 20], ["Código", "Ítem", "Unidad de compra", "LT", "Origen", "Proveedor"],
  D.compras.map((x) => [x["Código"], x["Ítem"], x["Unidad de compra (UC)"], n(x["Lead time (días háb.)"], 0), x["Origen del lead time"], x["Proveedor principal"]]),
  { num: [3] }));
hijos.push(...figs(["P06", "Q01", "Q03", "Q04", "Q05", "Q06", "Q07", "Q08", "X07", "X07B"]));

// ------------------------------------------------------------------ 7. política
hijos.push(h1("7. Política de stock del año de diseño"));
hijos.push(...tabla([26, 38, 36], ["Columna", "Fórmula", "Por qué"], [
  ["Consumo diario promedio", "consumo de 2035 / 240", "Días hábiles del Dimensionamiento."],
  ["Consumo diario del pico", "mes pico / 20", "El mes pico sale de sumar cada línea con su perfil mes a mes."],
  ["Stock de seguridad", "(d pico − d prom) × LT", "Cubre que el pico caiga durante la demora. Sin datos de desvío de la demanda (planta nueva) no se puede usar z × σ; con este criterio el punto de pedido queda en el consumo del pico durante el lead time."],
  ["Punto de pedido", "d prom × LT + SS = d pico × LT", "Se pide cuando el stock baja a lo que se consume en el pico mientras llega el pedido."],
  ["Lote", "consumo de T días del pico, redondeado hacia arriba a la unidad de compra (mínimo 1)", "Lotes en paquetes, pallets, rollos o baterías enteros."],
  ["Stock máximo", "SS + lote", "Lo que tiene que entrar en el almacén; cobertura = stock máximo / d prom."],
  ["Posiciones y m²", "stock máximo (UC) / UC por posición, sumadas por almacén", "Contra la capacidad que el proceso ya fijó, o los m² que tiene que prever el layout."],
]));
const SEL = ["MP-01", "MP-03", "MP-07", "MP-13", "MP-11", "MP-12", "MP-15", "MP-16", "MP-17", "MP-18", "MP-20", "MP-33", "MP-33B", "MP-34", "MP-25", "MP-23", "MP-24", "MP-28", "MP-31", "MP-43", "MP-45", "MP-54/350", "MP-59/ABC1", "MP-37", "RV-CO2_2kg"];
hijos.push(...tabla([10, 6, 10, 9, 9, 5, 9, 9, 4, 10, 9, 10], ["Código", "UM", "Consumo 2035", "d prom", "d pico", "LT", "SS", "Pto. pedido", "T", "Lote (UC)", "Stock máx. (UC)", "Cobertura (días)"],
  SEL.filter((c) => POL[c]).map((c) => { const x = POL[c]; return [c, x.UM, n(x["Consumo del año de diseño"], 0), n(x["d prom (UM/día)"], 1), n(x["d pico (UM/día)"], 1),
    n(x["Lead time (días háb.)"], 0), n(x["Stock de seguridad (UM)"], 0), n(x["Punto de pedido (UM)"], 0), n(x["T (días háb.)"], 0),
    `${n(x["Lote (UC)"], 0)} × ${n(x["Contenido por UC"], 1)}`, n(x["Stock máximo (UC)"], 0), n(x["Cobertura del stock máx. (días)"], 0)]; }),
  { num: [2, 3, 4, 5, 6, 7, 8, 10, 11] }));
hijos.push(h2("Almacenes"));
hijos.push(...tabla([30, 11, 11, 24, 10, 14], ["Almacén", "Posiciones", "Capacidad", "Resultado", "m²", "Capacidad según"],
  D.almacenes.map((x) => [x.almacen, n(x.pos, 0), x.cap === null ? "—" : n(x.cap, 0), x.res, n(x.m2, 1), x.segun]), { num: [1, 2, 4] }));
[
  "Calle de chapa de carros (2 de 3 posiciones) y rack de casquetes y cuplas (8 de 12): alcanzan con lotes semanales de chapa y mensuales de casquetes.",
  "Rack de insumos de montaje de carros: hacen falta 9 posiciones y el proceso previó 8. Casi todo es ruedas (tres medidas en atados de 10 con pedido quincenal). Se resuelve con una posición más o pidiendo las ruedas cada semana.",
  "Los demás almacenes no tienen capacidad fijada en los procesos: el MRP da los m² de posiciones (sin pasillos) que el layout tiene que prever. Embalaje (cajas plegadas del 1 kg) y revendidos son los más grandes.",
].forEach((x) => hijos.push(vin(x)));
hijos.push(...figs(["M10", "M11"]));

// ------------------------------------------------------------------ 8. validación
hijos.push(h1("8. Contraste con los documentos de proceso"));
const EXPL = {
  "Hojas LAF 1,25 (2,5 kg) por día (pico)": "El proceso toma el pico de cada modelo por separado: sus desarrollos por día suman 1.788 recipientes contra 1.665 de la línea.",
  "Hojas LAF 1,6 (5 kg) por día (pico)": "Ídem: 446 desarrollos del 5 kg por día equivalen a 76.000 por año; las Proyecciones 2035 dan 65.200 (nuevos + reserva + cilindros).",
  "Hojas LAF 2,0 (10 kg) por día (pico)": "Ídem.",
  "Gas MAG de manuales, m³ por día (pico)": "Mismo efecto de volumen: con la producción del pico del proceso, el MRP da exactamente 48 m³ (por eso el ajuste).",
  "Polvo ABC 60 de manuales, kg por día (pico)": "El proceso da 1,7 t en el pico y 0,9 t en el promedio (relación 1,89, distinta de su propio factor 1,41). El MRP usa la carga objetivo del BOM + 1 % de merma.",
  "Polvo ABC 60 de manuales, kg por día (promedio)": "Ídem.",
  "Hojas LAC 3,2 de carros por día (pico)": "El proceso de carros supone 20 recipientes por día en el pico (promedio = 70 % del pico) y 14 de promedio (3.360 por año, 8 % más que los 3.100 de las Proyecciones 2035).",
  "Casquetes 12\" por día (pico)": "Ídem.",
  "Cuplas M30 por día (pico)": "Ídem.",
  "Polvo ABC 90 de carros, kg por día (pico)": "Además, el proceso carga los 20 recipientes del día; 1.287 de los 3.100 de 2035 son cilindros vacíos que no se cargan.",
  "Recipientes de carros por día (pico)": "Supuesto del 70 % del proceso contra el perfil del Dimensionamiento (sección 3).",
  "Recipientes de carros por día (promedio)": "El proceso usa 14 por día; las Proyecciones 2035 dan 3.100 / 240 = 12,9.",
  "Factor de pico de carros": "Sección 3.",
};
hijos.push(...tabla([28, 10, 10, 8, 44], ["Dato", "MRP", "Proceso", "Dif.", "Causa"],
  D.validacion.map((x) => [x.dato, n(x.mrp, 2), n(x.doc, 2), sg(x.dif), EXPL[x.dato] || "Coincide."]), { num: [1, 2, 3] }));

// ------------------------------------------------------------------ 9. correcciones y pendientes
hijos.push(h1("9. Correcciones y pendientes"));
hijos.push(...tabla([20, 22, 26, 32], ["Tema", "Antes", "Ahora", "Por qué"], [
  ["Fleje del fondo de 1 kg (MP-13)", "Planilla: 0,9 × 106 mm", "1,25 × 135 mm (a recotizar)", "El plano y el proceso piden 1,25 mm; el disco Ø112 no entra en 106 mm. Margen de 23 mm, como el fleje cotizado de 1,6 × 200 para el fondo Ø177."],
  ["Fleje de la cúpula de 10 kg (MP-09)", "Cotizado en 2,0 × 300 mm", "1,6 × 300 mm (a recotizar)", "El plano y el proceso piden 1,6 mm."],
  ["Alambre de carros (MP-24)", "Planilla e investigación: Ø1,2", "Ø1,0", "El proceso de carros suelda con 1,0 mm en todos los puestos."],
  ["Polvo de carros", "Proceso: «MP-33»", "MP-33B (ABC 90)", "El BOM define ABC 90 en rodantes (decisión FLAMA)."],
  ["Tubos de 1 kg por día", "Recepción de manuales: 97", "53", "1.216 tramos por día / 23 por caño (corte de tubo del mismo proceso)."],
  ["Unidades de entrega", "Planilla: atado de 61, pallets de 100 / 80 / 60 casquetes, cajas de 200 / 50 cuplas", "16 tubos; 400 / 300 / 150; 100 / 40", "Los procesos las definieron después, con el peso y la manipulación de cada bulto."],
  ["Desengrasante y fosfatizante", "Planilla MP-29 y 30", "No entran", "El proceso de manuales prepara con granallado, sin túnel químico."],
  ["Casquetes de carros", "Proceso: importados, 60 días", "60 días hasta que Gockel cotice", "La investigación de proveedores propone Gockel (Wilde, 5 km). Si cotiza, baja el lead time y el stock de seguridad."],
  ["Pintura de manuales", "Investigación: Prymax tercerizado", "Línea propia (proceso)", "El proceso de manuales tiene granalladora y línea Firesafer; Prymax queda como alternativa."],
  ["Pico de carros", "Proceso: promedio = 70 % del pico", "Perfil del Dimensionamiento (1,08)", "A revisar en el proceso de carros."],
]));
hijos.push(h2("Pendientes"));
[
  `Confirmar los ${D.origen_lt["Supuesto"]} lead times supuestos y los ${D.origen_lt["Planilla de MP"]} de la planilla de MP: pedir el plazo en el formulario de cada cotización.`,
  "Recotizar los flejes MP-13 y MP-09 con el espesor del plano.",
  "Escribir los puestos 10 a 13 del proceso de carros (secado, marcado, pintura tercerizada, carga) y su embalaje; hoy el embalaje de carros es estimado.",
  "Proveedor del tapón de PE de los cilindros sueltos y del agente limpio para recargas (sin proveedor nacional identificado).",
  "Rack de insumos de montaje de carros: una posición más.",
  "Costos: con los precios de COMPRAS se calcula el lote económico y los centros de costo, sin tocar el MRP.",
].forEach((x) => hijos.push(vin(x)));

// ------------------------------------------------------------------ 10. fuentes
hijos.push(h1("10. Fuentes"));
[
  "Proyecciones_7.xlsx (hojas Indexado Dim Técnico, Reservas y Sustitutos, PROYECCION SALUD / EDUCACION / INDUSTRIASALM / HOTELES).",
  "FLAMA_BOM.xlsx y su Word «Justificación del BOM» (coeficientes por producto y por servicio de recarga).",
  "Proceso de manuales (explicativo con videos) y proceso de carros (en limpio), FLAMA S.A., octubre de 2026.",
  "Dimensionamiento_TecnicoV2.xlsx (Parametros y Parametros Recargas).",
  "MP_Abastecimiento_Almacenamiento_FLAMA_OpcionD.xlsx (MP Abastecimiento, Coef Fabricacion, Coef Recargas).",
  "Cotizaciones: Pradecon 173170 / 173195 y mail del 28/09/2026; Pacheco Chapas PR-42021; Hierros Parrotta 00413329; Polimetal; Comercial MID 27626; Metalpri (mail); lista de precios de agentes y válvulas; Prymax S00469; servicio de pintura de carros (mensaje); cotizaciones de MP por WhatsApp (Air Liquide, Eli-Met, Aceros Inoxidables Caseros); planilla «Materias Primas».",
  "IRAM 3517-2:2020 (8.2, 9.4.5, 9.10, anexo E), citada por cláusula; las capturas de la norma están en el Word del BOM.",
  "Web: iContainers (tránsito marítimo Shanghái – Buenos Aires); Tiger Drylac (rendimiento teórico de pintura en polvo); ficha WEG Politherm 20 R; Powder Coating Institute citado por Products Finishing (aprovechamiento con recuperación).",
].forEach((x) => hijos.push(vin(x)));

const doc = new Document({
  creator: "FLAMA S.A.", title: "Justificación del MRP",
  styles: {
    default: { document: { run: { font: FONT, size: 18 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, font: FONT, color: NEGRO }, paragraph: { spacing: { before: 200, after: 80 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 21, bold: true, font: FONT, color: GRIS_O }, paragraph: { spacing: { before: 120, after: 60 }, outlineLevel: 1 } },
    ],
  },
  numbering: { config: [{ reference: "vinetas", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
    style: { paragraph: { indent: { left: 360, hanging: 200 } } } }] }] },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 800, bottom: 800, left: 800, right: 800 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [
      new TextRun({ text: "Justificación del MRP — FLAMA S.A. — pág. ", font: FONT, size: 14, color: "808080" }),
      new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 14, color: "808080" }),
      new TextRun({ text: " de ", font: FONT, size: 14, color: "808080" }),
      new TextRun({ children: [PageNumber.TOTAL_PAGES], font: FONT, size: 14, color: "808080" })] })] }) },
    children: hijos,
  }],
});
Packer.toBuffer(doc).then((buf) => { fs.writeFileSync(OUT, buf); console.log("ok", OUT, buf.length); });
