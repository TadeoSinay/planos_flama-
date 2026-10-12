// Word «Justificación del BOM»: fuente, cálculo, tolerancia y control de cada valor de salida/bom/FLAMA_BOM.xlsx, con
// las capturas marcadas de las normas y fichas citadas. Lee el JSON de datos_bom.py. Sólo negro y grises.
// Uso: node word_bom.js <datos.json> <salida.docx>
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell, WidthType, ShadingType, HeadingLevel,
  AlignmentType, Footer, PageNumber, LevelFormat, BorderStyle, LineRuleType,
} = require("docx");

const D = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const OUT = process.argv[3];
const AQUI = __dirname;

const W = 10306;                       // ancho útil (DXA): A4 con márgenes de 1,4 cm
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
const pc = (x, d = 0) => (x === null || x === undefined) ? "—" : n(100 * x, d) + " %";
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

function celda(c, ancho, o = {}) {
  const paras = (Array.isArray(c) ? c : [c]).map((x) => x instanceof Paragraph ? x :
    new Paragraph({ alignment: o.align, spacing: { after: 0 },
      children: [t(x === null || x === undefined ? "—" : String(x), { size: o.size || 14, bold: o.bold, color: o.color })] }));
  return new TableCell({ children: paras, width: { size: ancho, type: WidthType.DXA }, borders: bordes,
    shading: o.fill ? { type: ShadingType.CLEAR, color: "auto", fill: o.fill } : undefined,
    margins: { top: 20, bottom: 20, left: 60, right: 60 } });
}

// cols: anchos relativos; num: columnas numéricas (a la derecha); grupo: filas título en gris claro
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
      align: num.has(i) ? AlignmentType.RIGHT : undefined })) });
  });
  return [new Table({ width: { size: W, type: WidthType.DXA }, columnWidths: cw, rows: [head, ...rows] }),
    p("", { after: o.after ?? 100 })];
}

// ------------------------------------------------------------------ capturas
function bloqueFigura(f, ancho) {
  const maxH = ancho > 400 ? 820 : 330;
  let w = Math.min(ancho, f.w), h = Math.round(f.h * w / f.w);
  if (h > maxH) { h = maxH; w = Math.round(f.w * maxH / f.h); }
  const png = path.join(AQUI, f.png);
  const img = new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 30 },
    children: [new ImageRun({ type: png.endsWith(".jpg") ? "jpg" : "png", data: fs.readFileSync(png),
      transformation: { width: w, height: h }, altText: { title: f.id, description: f.titulo, name: f.id } })] });
  const cab = new Paragraph({ spacing: { after: 20 }, keepNext: true,
    children: [t(`${f.id} · `, { bold: true, size: 16 }), t(f.titulo, { bold: true, size: 16 })] });
  const marcas = new Paragraph({ spacing: { after: 80 }, children: (f.marcas || []).flatMap((m, i) => [
    t(`${m.n} `, { bold: true, size: 13, color: "C00000" }), t(m.etiqueta + (i < f.marcas.length - 1 ? "  ·  " : ""), { size: 13 })]) });
  return [cab, img, marcas];
}
const sep = () => new Paragraph({ spacing: { after: 0, before: 0, line: 20, lineRule: LineRuleType.EXACT }, children: [] });
function grilla(figs) {
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
  figs.forEach((f) => {
    if (f.w >= 900 && !f.medio) {        // tablas anchas: a todo el ancho
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

const NOTAS = D.notas;
const MO = D.modelos;
const orden = D.cargas.map((x) => x.codigo);
const hijos = [];
// ------------------------------------------------------------------ página 1
hijos.push(new Paragraph({ spacing: { after: 60 }, children: [new TextRun({ text: "Justificación del BOM", font: FONT, size: 40, bold: true })] }));
hijos.push(p([t("FLAMA S.A. · fuente, cálculo, tolerancia y control de cada valor de FLAMA_BOM.xlsx · octubre de 2026", { size: 18, color: GRIS_O })], { after: 160 }));
NOTAS.intro.forEach((x) => hijos.push(vin(x)));
hijos.push(h2("Resultado de la revisión"));
hijos.push(...tabla([28, 72], ["Control", "Resultado"], NOTAS.resumen));

// ------------------------------------------------------------------ 1. cómo se lee
hijos.push(h1("1. Cómo se lee el BOM"));
hijos.push(nota("Hojas: REFERENCIAS (datos de entrada con su fuente), MODELOS (carga y gas de cada extintor), Fabricados, Revendidos, Cilindros y Recargas. En las hojas del BOM la columna Ref. es el ID de REFERENCIAS de donde salen la densidad y su rango; Material / agente se lee de ahí. Las filas que agrupan suman a sus hijos directos.", { keepNext: true }));
hijos.push(...tabla([18, 30, 52], ["Columna", "Qué es", "Cómo se calcula"], [
  ["Cant. / UM", "Cantidad en su unidad", "Piezas: del plano. Agentes y gas: carga objetivo y gas de MODELOS"],
  ["Densidad (kg/L)", "Del material, agente o gas", "Se busca por Ref. en REFERENCIAS; CO₂: relación de llenado (MODELOS)"],
  ["Volumen total (L)", "Volumen de la cantidad del renglón", "Cant. × Vol. unit. Gas: litros normales (0 °C, 1 atm)"],
  ["+ Vol. unit., mín., máx.", "Detalle del volumen", "Vol. unit.: sólido del modelo 3D (piezas) o 1 / densidad. Mín. y máx.: ± tolerancia de volumen o banda de carga"],
  ["Masa total (kg)", "Masa de la cantidad del renglón", "Cant. × Masa unit.; filas que agrupan: suma de los hijos"],
  ["+ Masa unit., mín., máx.", "Detalle de la masa", "Mín. = Vol. mín. × ρ mín.; Máx. = Vol. máx. × ρ máx. Agentes y gas: banda de MODELOS"],
  ["++ Cálculo de la tolerancia", "ρ mín. y máx., superficie, espesor eq., tolerancia ISO 2768-m, tolerancia de volumen", "Espesor eq. = 2 × volumen / superficie; tolerancia de volumen = tolerancia ISO del espesor eq. ÷ espesor eq."],
]));

// ------------------------------------------------------------------ 2. referencias
hijos.push(h1("2. Referencias (hoja REFERENCIAS)"));
hijos.push(nota("Cada dato de entrada de las cuentas, con su ID. Las capturas de las cláusulas y fichas citadas están en la sección 11 (N = norma, F = ficha).", { keepNext: true }));
const filasRef = [], grupoRef = [];
D.referencias.forEach((x) => {
  if (x.seccion) { grupoRef.push(filasRef.length); filasRef.push([x.seccion]); return; }
  filasRef.push([x.id, x.dato, n(x.valor, 6), n(x.min, 6), n(x.max, 6), x.unidad, x.fuente + (x.nota ? ` · ${x.nota}` : "")]);
});
hijos.push(...tabla([12, 26, 8, 8, 8, 7, 31], ["ID", "Dato", "Valor", "Mín.", "Máx.", "Unidad", "Fuente · nota"], filasRef,
  { num: [2, 3, 4], grupo: grupoRef }));
hijos.push(nota("Tolerancia general de los planos, ISO 2768-1 clase m (rótulo de cada plano):", { keepNext: true }));
hijos.push(...tabla([30, 30, 40], ["Más de (mm)", "Hasta (mm)", "± (mm)"], D.iso.map((x) => [n(x.desde, 1), n(x.hasta, 0), n(x.tol, 1)]), { num: [0, 1, 2] }));

// ------------------------------------------------------------------ 3. carga
hijos.push(h1("3. Carga de cada extintor (hoja MODELOS)"));
hijos.push(nota(NOTAS.carga_intro, { keepNext: true }));
hijos.push(...tabla([13, 6, 8, 9, 8, 8, 8, 7, 8, 8, 9, 8], ["Modelo", "IRAM", "Nominal", "Ref. tolerancia", "Objetivo", "Mín.", "Máx.",
  "ρ (kg/L)", "V agente (L)", "V recip. (L)", "Ocupa (máx.)", "Reposición"],
  orden.map((c) => { const x = MO[c]; return [corto(c), x["Norma IRAM"], `${n(x["Carga nominal"], 2)} ${x.UM}`, x["Ref. tolerancia"],
    n(x["Carga objetivo"], 3), n(x["Carga mín."], 3), n(x["Carga máx."], 3), n(x["ρ agente (kg/L)"], 3), n(x["V agente (L)"], 2),
    n(x["V recipiente (L)"], 2), x["Ocupa (%)"] === null ? "—" : `${pc(x["Ocupa (%)"])} (${pc(x["Ocupa máx. (%)"])})`,
    x["Reposición en mantenimiento (UM)"] === null ? "carga entera" : n(x["Reposición en mantenimiento (UM)"], 3)]; }),
  { num: [4, 5, 6, 7, 8, 9] }));
NOTAS.carga.forEach((x) => hijos.push(vin(x)));

// ------------------------------------------------------------------ 4. gas
hijos.push(h1("4. Gas impulsor"));
hijos.push(nota(NOTAS.gas_intro, { keepNext: true }));
hijos.push(...tabla([13, 8, 13, 14, 9, 9, 9, 9, 7, 9], ["Modelo", "Gas", "Ps (mín. – máx.)", "V libre (mín. – máx.)", "Gas (kg)",
  "Mín. (kg)", "Máx. (kg)", "Gas real (kg)", "Dif.", "L normales"],
  D.cargas.filter((c) => c.x["Ref. gas"]).map((c) => { const x = c.x; return [corto(c.codigo), x["Ref. gas"].replace("GAS_", ""),
    `${n(x["Ps (MPa)"], 2)} (${n(x["Ps mín. (MPa)"], 2)} – ${n(x["Ps máx. (MPa)"], 2)})`,
    `${n(x["V libre (L)"], 3)} (${n(x["V libre mín. (L)"], 3)} – ${n(x["V libre máx. (L)"], 3)})`,
    n(x["Gas (kg)"], 4), n(x["Gas mín. (kg)"], 4), n(x["Gas máx. (kg)"], 4), n(c.gas_real, 4), sg(c.dif_real, 2), n(x["Gas (L normales)"], 1)]; }),
  { num: [4, 5, 6, 7, 8, 9] }));
hijos.push(nota(NOTAS.gas));
hijos.push(...tabla([24, 16, 20, 20, 20], ["Gas", "M usada (g/mol)", "ρ normal usada (kg/L)", "ρ normal real (kg/L)", "Diferencia"],
  D.gases.map((x) => [x.dato, n(x.rho_n * 22414, 0), n(x.rho_n, 6), n(x.rho_real, 6), sg(x.dif, 2)]), { num: [1, 2, 3, 4] }));

// ------------------------------------------------------------------ 5. CO2
hijos.push(h1("5. CO₂: relación de llenado"));
hijos.push(...tabla([20, 14, 14, 18, 14, 10, 10], ["Modelo", "Carga (kg)", "Cilindro (L)", "Relación (kg/L)", "Máx. IRAM 2533", "Cumple", "Banda (kg)"],
  orden.filter((c) => MO[c]["Ref. agente"] === "AG_CO2").map((c) => { const x = MO[c]; return [corto(c), n(x["Carga objetivo"], 2),
    n(x["V recipiente (L)"], 2), n(x["Relación de llenado CO₂ (kg/L)"], 3), n(x["Máx. IRAM 2533 (kg/L)"], 2), x["CO₂ cumple"],
    `${n(x["Carga mín."], 2)} – ${n(x["Carga máx."], 2)}`]; }), { num: [1, 2, 3, 4] }));
hijos.push(nota(NOTAS.co2));

// ------------------------------------------------------------------ 6. tolerancias
hijos.push(h1("6. Tolerancias"));
NOTAS.tol_intro.forEach((x) => hijos.push(vin(x)));
hijos.push(h2("Ejemplos de cálculo (columnas plegadas del BOM)"));
hijos.push(...tabla([10, 15, 8, 8, 8, 7, 8, 8, 11, 9, 8], ["Código", "Pieza", "Ref.", "Vol. (L)", "Sup. (dm²)", "e eq. (mm)", "ISO (± mm)",
  "Tol. vol.", "ρ (mín. – máx.)", "Masa (kg)", "Mín. – máx."],
  D.ejemplos.map((x) => [x.codigo, x.pieza, x.ref.replace("MAT_", ""), n(x.vu, 4), n(x.sup, 2), n(x.e, 2), n(x.tiso, 1),
    "±" + n(x.tvol, 1) + " %", `${n(x.rho, 2)} (${n(x.rmin, 2)} – ${n(x.rmax, 2)})`, n(x.mt, 4), `${n(x.mmin, 4)} – ${n(x.mmax, 4)}`]),
  { num: [3, 4, 5, 6, 9] }));
hijos.push(h2("Piezas principales de los fabricados (masa y tolerancia)"));
const PZ = ["Cuerpo", "Cúpula", "Fondo", "Cuello roscado", "Válvula HZ armada", "Manguera"];
hijos.push(...tabla([14, 14, 14, 14, 14, 16, 14], ["Modelo", ...PZ.map((x) => x.replace(" roscado", "").replace(" armada", "") + " (kg)")],
  D.piezas.map((x) => [corto(x.codigo), ...PZ.map((k) => x[k] ? `${n(x[k].masa, 3)} ±${n(x[k].tol, 1)} %` : "—")]), { num: [1, 2, 3, 4, 5, 6] }));
hijos.push(h2("Cilindros de venta suelta"));
hijos.push(...tabla([40, 20, 20, 20], ["Cilindro", "Masa (kg)", "Mín. (kg)", "Máx. (kg)"],
  D.cilindros.map((x) => [x.nombre, n(x.masa, 3), n(x.min, 3), n(x.max, 3)]), { num: [1, 2, 3] }));

// ------------------------------------------------------------------ 7. masas
hijos.push(h1("7. Masa del extintor cargado contra la referencia"));
hijos.push(nota(NOTAS.masas_intro, { keepNext: true }));
hijos.push(...tabla([13, 9, 13, 8, 8, 27, 9, 7], ["Modelo", "BOM (kg)", "Banda (kg)", "Ref. (kg)", "Dif.", "Referencia", "Catálogo (kg)", "En banda"],
  D.masas.map((x) => [corto(x.codigo), n(x.bom, 2), `${n(x.bom_min, 2)} – ${n(x.bom_max, 2)}`, n(x.ref, 2), sg(x.dif), x.fuente,
    n(x.catalogo, 2), x.dentro ? "Sí" : "No"]), { num: [1, 3, 4, 6] }));
NOTAS.masas.forEach((x) => hijos.push(vin(x)));

// ------------------------------------------------------------------ 8. sustituto
hijos.push(h1("8. Si va como sustituto"));
hijos.push(nota(NOTAS.sustituto_intro, { keepNext: true }));
hijos.push(...tabla([30, 18, 52], ["Se agrega", "Norma", "Por qué"], NOTAS.sustituto));
hijos.push(nota("Todos se sustituyen con el mismo modelo: igual clasificación e igual capacidad. Faja de cada uno (alto × largo, mm):", { keepNext: true }));
hijos.push(...tabla([22, 22, 56], ["Modelo", "Faja amarilla (mm)", "Nota"], D.sustitutos.map((x) => [corto(x.codigo), x.faja, x.nota || ""])));

// ------------------------------------------------------------------ 9. recargas
hijos.push(h1("9. Recargas por servicio"));
hijos.push(nota(NOTAS.recargas_intro, { keepNext: true }));
hijos.push(...tabla([16, 18, 18, 48], ["Servicio", "Frecuencia", "Cláusula", "Qué se agrega en el BOM"], NOTAS.servicios));
hijos.push(h2("Identificación que se repone"));
hijos.push(...tabla([32, 24, 44], ["Ítem", "Norma", "Cuándo"], NOTAS.identificacion));
hijos.push(h2("Reposición de agente en el mantenimiento"));
hijos.push(nota(NOTAS.reposicion_intro, { keepNext: true }));
hijos.push(h2("Masa de agente y gas por servicio: valor (mín. – máx.), kg"));
const SV = (r, k) => { const s = r.servicios.find((x) => x[0].startsWith(k)); return s && s[1] ? `${n(s[1], 3)} (${n(s[2], 3)} – ${n(s[3], 3)})` : "—"; };
hijos.push(...tabla([16, 22, 22, 26, 14], ["Modelo", "Mantenimiento", "Recarga", "Prueba hidráulica", "Cada (años)"],
  D.recargas.map((r) => [corto(r.codigo), SV(r, "Mantenimiento"), SV(r, "Recarga"), SV(r, "Prueba hidráulica"),
    n(r.x["Prueba hidráulica cada (años)"], 0)])));

// ------------------------------------------------------------------ 10. correcciones
hijos.push(h1("10. Correcciones de esta revisión y condiciones"));
hijos.push(...tabla([24, 20, 26, 30], ["Valor", "Antes", "Ahora", "Por qué"], NOTAS.correcciones));
hijos.push(h2("Condiciones de compra y pendientes"));
NOTAS.condiciones.forEach((x) => hijos.push(vin(x)));

// ------------------------------------------------------------------ 11 y 12. capturas
hijos.push(h1("11. Capturas de normas y fichas"));
hijos.push(nota("Recortes de la cláusula o tabla citada, con el dato marcado en rojo (no se transcribe la norma). N = norma; F = ficha del fabricante.", { keepNext: true }));
hijos.push(...grilla(D.capturas));
hijos.push(h1("12. Capturas de las masas de referencia"));
hijos.push(nota("Las mismas capturas del Word «Justificación de medidas planos». Para la masa interesa la marca de masa o peso; las demás marcas se explican en ese documento.", { keepNext: true }));
hijos.push(...grilla(D.reusadas.map((f) => ({ ...f, medio: true, marcas: f.marcas.filter((m) => /masa|peso/i.test(m.etiqueta)) }))));

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
