// Word «Justificación del BOM»: fuente, cálculo y control de cada valor de salida/bom/FLAMA_BOM.xlsx (densidades, cargas,
// gas impulsor, masas, sustituto y recargas por servicio). Lee el JSON de datos_bom.py. Sólo negro y grises.
// Uso: node word_bom.js <datos.json> <salida.docx>
const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType, ShadingType, HeadingLevel, AlignmentType,
  Footer, PageNumber, LevelFormat, BorderStyle,
} = require("docx");

const D = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const OUT = process.argv[3];

const W = 10306;                       // ancho útil (DXA): A4 con márgenes de 1,4 cm
const FONT = "Arial";
const NEGRO = "000000", GRIS_O = "595959", GRIS_M = "BFBFBF", GRIS_C = "EDEDED";
const fino = { style: BorderStyle.SINGLE, size: 4, color: GRIS_M };
const bordes = { top: fino, bottom: fino, left: fino, right: fino };

// número con coma decimal
const n = (x, d = 2) => (x === null || x === undefined || x === "") ? "—" :
  Number(x).toLocaleString("es-AR", { minimumFractionDigits: 0, maximumFractionDigits: d });
const sg = (x, d = 1) => (x === null || x === undefined) ? "—" : Math.abs(x) < 0.5 * 10 ** -d ? "0 %" :
  (x > 0 ? "+" : "−") + n(Math.abs(x), d) + " %";
const corto = (c) => c.replace("FL_MAT_", "").replace("FL_REC_", "").replace(/_/g, " ");

const t = (text, o = {}) => new TextRun({ text: String(text), font: FONT, size: o.size || 18, bold: o.bold,
  italics: o.italics, color: o.color || NEGRO });
const p = (runs, o = {}) => new Paragraph({ children: Array.isArray(runs) ? runs : [t(runs, o)],
  spacing: { after: o.after ?? 80, before: o.before ?? 0 }, alignment: o.align, heading: o.heading, keepNext: o.keepNext,
  numbering: o.bullet ? { reference: "vinetas", level: 0 } : undefined });
const h1 = (x) => p(x, { heading: HeadingLevel.HEADING_1, keepNext: true, before: 200 });
const h2 = (x) => p(x, { heading: HeadingLevel.HEADING_2, keepNext: true, before: 120 });
const nota = (x, o = {}) => p(Array.isArray(x) ? x : [t(x, { size: 16 })], { after: o.after ?? 60, keepNext: o.keepNext });
const vin = (x) => p(Array.isArray(x) ? x : [t(x, { size: 17 })], { bullet: true, after: 30 });
const b = (x, size = 17) => t(x, { bold: true, size });
const s = (x, size = 17) => t(x, { size });

function celda(c, ancho, o = {}) {
  const paras = (Array.isArray(c) ? c : [c]).map((x) => x instanceof Paragraph ? x :
    new Paragraph({ alignment: o.align, spacing: { after: 0 },
      children: [t(x === null || x === undefined ? "—" : String(x), { size: o.size || 14, bold: o.bold, color: o.color })] }));
  return new TableCell({ children: paras, width: { size: ancho, type: WidthType.DXA }, borders: bordes,
    shading: o.fill ? { type: ShadingType.CLEAR, color: "auto", fill: o.fill } : undefined,
    margins: { top: 20, bottom: 20, left: 60, right: 60 } });
}

// cols: anchos en DXA (suman W); num: índices de columnas numéricas (a la derecha); grupo: filas con fondo gris claro
function tabla(cols, cab, filas, o = {}) {
  const k = W / cols.reduce((a, x) => a + x, 0);
  const cw = cols.map((x) => Math.round(x * k));
  const num = new Set(o.num || []);
  const head = new TableRow({ tableHeader: true, cantSplit: true,
    children: cab.map((h, i) => celda(h, cw[i], { bold: true, color: "FFFFFF", fill: NEGRO, align: AlignmentType.CENTER })) });
  const rows = filas.map((f, j) => new TableRow({ cantSplit: true, children: f.map((c, i) => celda(c, cw[i], {
    align: num.has(i) ? AlignmentType.RIGHT : undefined, fill: (o.grupo || []).includes(j) ? GRIS_C : undefined,
    bold: (o.grupo || []).includes(j) })) }));
  return [new Table({ width: { size: W, type: WidthType.DXA }, columnWidths: cw, rows: [head, ...rows] }),
    p("", { after: o.after ?? 100 })];
}

const C = Object.fromEntries(D.cargas.map((x) => [x.codigo, x]));
const MS = Object.fromEntries(D.masas.map((x) => [x.codigo, x]));
const RE = Object.fromEntries(D.recargas.map((x) => [x.codigo, x]));
const fab = D.masas.filter((x) => x.propio).map((x) => x.codigo);
const rev = D.masas.filter((x) => !x.propio).map((x) => x.codigo);
const NOTAS = D.notas;

const hijos = [];
// ------------------------------------------------------------------ página 1
hijos.push(new Paragraph({ spacing: { after: 60 }, children: [new TextRun({ text: "Justificación del BOM", font: FONT, size: 40, bold: true })] }));
hijos.push(p([t("FLAMA S.A. · fuente, cálculo y control de cada valor de FLAMA_BOM.xlsx · octubre de 2026", { size: 18, color: GRIS_O })], { after: 160 }));
NOTAS.intro.forEach((x) => hijos.push(vin(x)));
hijos.push(h2("Resultado de la revisión"));
hijos.push(...tabla([30, 70], ["Control", "Resultado"], NOTAS.resumen.map((x) => [x[0], x[1]])));

// ------------------------------------------------------------------ 1. cómo se lee
hijos.push(h1("1. Cómo se lee el BOM"));
hijos.push(nota("Cada renglón tiene la cantidad en su propia unidad (UM) y, cuando corresponde, la densidad, el volumen total y la masa. El volumen y la masa total son los de la cantidad del renglón; la masa unitaria es la de una unidad (1 u, 1 kg o 1 L). La masa de un producto o subconjunto es la suma de la masa total de los renglones que tiene debajo; las piezas compradas sin masa declarada (manómetro, tornillos, internos de válvula) no suman.", { keepNext: true }));
hijos.push(...tabla([18, 10, 24, 24, 24], ["Renglón", "UM", "Densidad (kg/L)", "Volumen total (L)", "Masa (kg)"], [
  ["Pieza del modelo 3D", "u", "La del material (sección 3)", "Volumen del sólido (masa ÷ densidad) × cantidad", "Volumen × densidad × factor de llenado"],
  ["Polvo y agente limpio", "kg", "Asentada del agente en el recipiente", "Lo que ocupa la carga: masa ÷ densidad", "Carga objetivo (kg)"],
  ["Líquidos (agua, AFFF, sales K)", "L", "Del líquido", "Los litros de carga", "Litros × densidad"],
  ["CO₂", "kg", "Relación de llenado: kg de CO₂ por litro de cilindro", "Capacidad del cilindro: carga ÷ relación de llenado", "Carga (kg)"],
  ["Gas impulsor", "kg", "Normal (0 °C, 101,325 kPa)", "Litros normales de la carga (lo que ocuparía el gas a 0 °C y 1 atm)", "Masa por cálculo de gas (sección 4)"],
  ["Comprado armado (válvula HZ)", "u", "—", "—", "Suma de sus piezas (renglones de abajo)"],
]));

// ------------------------------------------------------------------ 2. fuentes
hijos.push(h1("2. Fuentes"));
hijos.push(nota("Se citan las cláusulas; las normas no se transcriben. Donde la norma del equipo no estuvo a la vista se usa la ficha técnica del fabricante del agente o del equipo, y se indica.", { keepNext: true }));
hijos.push(...tabla([24, 76], ["Documento", "Qué se toma"], NOTAS.fuentes));

// ------------------------------------------------------------------ 3. densidades
hijos.push(h1("3. Densidades"));
hijos.push(h2("Materiales de las piezas"));
hijos.push(...tabla([30, 10, 20, 40], ["Material", "kg/L", "Referencia", "Piezas"],
  D.materiales.map((x) => [x.mat, n(x.rho, 2), x.rango, x.uso]), { num: [1] }));
hijos.push(nota([b("Piezas huecas modeladas macizas. ", 16), s("El sólido 3D es macizo; la masa se corrige con un factor de llenado = volumen real de material ÷ volumen del sólido (pared del tubo, espiras del resorte, perforaciones del filtro):", 16)], { keepNext: true }));
hijos.push(...tabla([34, 34, 10, 22], ["Pieza", "Material", "Factor", "Observación"],
  D.llenado.map((x) => [x.pieza, x.material, n(x.factor, 2), x.obs]), { num: [2] }));
hijos.push(h2("Agentes extintores"));
hijos.push(...tabla([20, 9, 9, 9, 11, 42], ["Agente", "ρ mín.", "ρ típica", "ρ máx.", "En el BOM", "Fuente"],
  D.agentes.map((x) => [x.nombre.split(" - ")[0], n(x.rho_min, 3), n(x.rho_tip, 3), n(x.rho_max, 3),
    x.empacada ? `${n(x.empacada, 2)} asentada` : (x.clave === "AFFF" ? `concentrado ${n(D.afff_conc, 3)}` : n(x.rho_tip, 3)), x.fuente]),
  { num: [1, 2, 3] }));
NOTAS.densidades.forEach((x) => hijos.push(vin(x)));
hijos.push(h2("Gases"));
hijos.push(...tabla([24, 16, 20, 20, 20], ["Gas", "M usada (g/mol)", "ρ normal usada (kg/L)", "ρ normal real (kg/L)", "Diferencia"],
  D.gases.map((x) => [x.gas, n(x.M, 0), n(x.rho_n, 6), n(x.rho_real, 6), sg(x.dif, 2)]), { num: [1, 2, 3, 4] }));
hijos.push(nota(NOTAS.gases));

// ------------------------------------------------------------------ 4. carga
hijos.push(h1("4. Carga de cada extintor"));
hijos.push(nota(NOTAS.carga_intro, { keepNext: true }));
const filasCarga = D.cargas.map((x) => [corto(x.codigo), x.norma, `${n(x.q, 2)} ${x.um}`, x.tol, `${n(x.obj, 3)}`,
  n(x.rho, 3), x.agente === "CO2" ? "—" : n(x.v_ag, 2), n(x.V, 2), x.agente === "CO2" ? "—" : n(x.ocup, 0) + " %",
  x.agente === "CO2" ? "—" : n(x.ocup_peor, 0) + " %"]);
hijos.push(...tabla([13, 6, 8, 10, 8, 8, 8, 8, 8, 9], ["Modelo", "IRAM", "Nominal", "Tolerancia (tabla 3)", "Objetivo",
  "ρ (kg/L)", "V agente (L)", "V recip. (L)", "Ocupa", "Ocupa con ρ mín."], filasCarga, { num: [4, 5, 6, 7, 8, 9] }));
NOTAS.carga.forEach((x) => hijos.push(vin(x)));
hijos.push(h2("Gas impulsor"));
hijos.push(nota(NOTAS.gas_intro, { keepNext: true }));
hijos.push(...tabla([14, 14, 8, 10, 11, 11, 11, 10], ["Modelo", "Gas (tabla 2)", "Ps (MPa)", "V libre (L)",
  "Masa gas ideal (kg)", "Masa gas real (kg)", "Diferencia", "Litros normales"],
  D.cargas.filter((x) => x.agente !== "CO2").map((x) => [corto(x.codigo), x.gas, n(x.ps, 1), n(x.libre, 3),
    n(x.m_gas, 4), n(x.m_gas_real, 4), sg(x.dif_real, 2), n(x.nl, 1)]), { num: [2, 3, 4, 5, 6, 7] }));
hijos.push(nota(NOTAS.gas));
hijos.push(h2("CO₂: relación de llenado"));
hijos.push(...tabla([20, 15, 15, 20, 15, 15], ["Modelo", "Carga (kg)", "Cilindro (L)", "Relación (kg/L)", "Máx. IRAM 2533", "Resultado"],
  D.cargas.filter((x) => x.agente === "CO2").map((x) => [corto(x.codigo), n(x.q, 1), n(x.V, 2), n(x.rll, 3),
    n(x.rll_max, 2), x.rll_ok ? "Cumple" : "No cumple"]), { num: [1, 2, 3, 4] }));
hijos.push(nota(NOTAS.co2));

// ------------------------------------------------------------------ 5. masas
hijos.push(h1("5. Masas"));
hijos.push(h2("Piezas principales de los fabricados"));
hijos.push(nota(NOTAS.piezas_intro, { keepNext: true }));
const PZ = ["Cuerpo", "Cúpula", "Fondo", "Cuello", "Válvula HZ", "Manguera", "Soporte de pared"];
hijos.push(...tabla([14, 12, 12, 12, 12, 13, 12, 13], ["Modelo", ...PZ.map((x) => x + " (kg)")],
  D.piezas.map((x) => [corto(x.codigo), ...PZ.map((k) => x[k] ? n(x[k].masa, 3) + (x[k].cant > 1 ? ` × ${x[k].cant}` : "") : "—")]),
  { num: [1, 2, 3, 4, 5, 6, 7] }));
hijos.push(h2("Masa total del BOM contra la referencia"));
hijos.push(nota(NOTAS.masas_intro, { keepNext: true }));
hijos.push(...tabla([14, 9, 9, 9, 33, 9, 9], ["Modelo", "BOM (kg)", "Referencia (kg)", "Diferencia", "Referencia", "Catálogo (kg)", "Dif. catálogo"],
  [...fab, ...rev].map((c) => { const x = MS[c]; return [corto(c), n(x.bom, 2), n(x.ref, 2), sg(x.dif), x.fuente, n(x.catalogo, 2), sg(x.dif_cat)]; }),
  { num: [1, 2, 3, 5, 6], grupo: [] }));
NOTAS.masas.forEach((x) => hijos.push(vin(x)));
hijos.push(h2("Cilindros de venta suelta"));
hijos.push(...tabla([20, 14, 66], ["Cilindro", "Masa (kg)", "Composición (kg)"],
  D.cilindros.map((x) => [corto(x.codigo), n(x.masa, 3), x.partes.map((q) => `${q[0]} ${n(q[1], 3)}`).join(" · ")]), { num: [1] }));
hijos.push(nota(NOTAS.cilindros));

// ------------------------------------------------------------------ 6. sustituto
hijos.push(h1("6. Si va como sustituto"));
hijos.push(nota(NOTAS.sustituto_intro, { keepNext: true }));
hijos.push(...tabla([30, 16, 54], ["Se agrega", "Norma", "Por qué"], NOTAS.sustituto));
hijos.push(nota("Todos se sustituyen con el mismo modelo: igual clasificación e igual capacidad. Faja de cada uno (alto × largo, mm):", { keepNext: true }));
hijos.push(...tabla([22, 22, 56], ["Modelo", "Faja amarilla (mm)", "Nota"],
  D.sustitutos.map((x) => [corto(x.codigo), x.faja, x.nota || ""])));

// ------------------------------------------------------------------ 7. recargas
hijos.push(h1("7. Recargas por servicio"));
hijos.push(nota(NOTAS.recargas_intro, { keepNext: true }));
hijos.push(...tabla([18, 16, 16, 50], ["Servicio", "Frecuencia", "Cláusula", "Qué se agrega en el BOM"], NOTAS.servicios));
hijos.push(h2("Identificación que se repone"));
hijos.push(...tabla([30, 22, 48], ["Ítem", "Norma", "Cuándo"], NOTAS.identificacion));
hijos.push(h2("Reposición de agente en el mantenimiento"));
hijos.push(nota(NOTAS.reposicion_intro, { keepNext: true }));
hijos.push(...tabla([16, 7, 10, 11, 11, 11, 9, 9, 8, 8], ["Modelo", "IRAM", "Tolerancia", "Objetivo", "Límite inferior",
  "Reposición", "% nominal", "Gas (kg)", "PH (años)", "UM"],
  D.recargas.map((x) => [corto(x.codigo), x.norma, x.tol, n(x.obj, 3), x.rep === null ? "—" : n(x.lim_inf, 3),
    x.rep === null ? "carga entera" : n(x.rep, 3), x.rep === null ? "100 %" : n(x.rep_pct, 1) + " %", n(x.m_gas, 4), x.ph, x.um]),
  { num: [3, 4, 5, 6, 7, 8] }));
NOTAS.recargas.forEach((x) => hijos.push(vin(x)));

// ------------------------------------------------------------------ 8. correcciones
hijos.push(h1("8. Correcciones de esta revisión y condiciones"));
hijos.push(...tabla([26, 22, 22, 30], ["Valor", "Antes", "Ahora", "Por qué"], NOTAS.correcciones));
hijos.push(h2("Condiciones de compra y pendientes"));
NOTAS.condiciones.forEach((x) => hijos.push(vin(x)));

const doc = new Document({
  creator: "FLAMA S.A.", title: "Justificación del BOM",
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
      new TextRun({ text: "Justificación del BOM — FLAMA S.A. — pág. ", font: FONT, size: 14, color: "808080" }),
      new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 14, color: "808080" }),
      new TextRun({ text: " de ", font: FONT, size: 14, color: "808080" }),
      new TextRun({ children: [PageNumber.TOTAL_PAGES], font: FONT, size: 14, color: "808080" })] })] }) },
    children: hijos,
  }],
});
Packer.toBuffer(doc).then((buf) => { fs.writeFileSync(OUT, buf); console.log("ok", OUT, buf.length); });
