// Word «Justificación de medidas planos» (versión compacta): capturas marcadas de a dos y tabla de valores de diseño.
const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell, WidthType, ShadingType,
  HeadingLevel, AlignmentType, ExternalHyperlink, Footer, PageNumber, LevelFormat, BorderStyle, PageBreak,
} = require("docx");

const SP = "/tmp/claude-0/-home-user-TP-optimizacion/15292aaf-e550-5dee-a83e-77fd9177a6ef/scratchpad";
const OUT = process.argv[2] || "/home/user/planos_flama-/salida/justificacion/Justificacion de medidas planos.docx";
const C = JSON.parse(fs.readFileSync(`${SP}/jw/compacto.json`, "utf8"));

const W = 10306; // ancho útil (DXA): A4 con márgenes de 1,5 cm
const FONT = "Arial";
const AZUL = "1F3864";
const EST = { V: undefined, E: "FFF2CC", A: "F8CBAD" };
const fino = { style: BorderStyle.SINGLE, size: 4, color: "BFBFBF" };
const bordes = { top: fino, bottom: fino, left: fino, right: fino };
const nada = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
const sinBordes = { top: nada, bottom: nada, left: nada, right: nada, insideHorizontal: nada, insideVertical: nada };

const t = (text, o = {}) => new TextRun({ text, font: FONT, size: o.size || 18, bold: o.bold, italics: o.italics, color: o.color });
const p = (runs, o = {}) => new Paragraph({ children: Array.isArray(runs) ? runs : [t(runs, o)], spacing: { after: o.after ?? 80, before: o.before ?? 0 },
  alignment: o.align, heading: o.heading, keepNext: o.keepNext, numbering: o.bullet ? { reference: "vinetas", level: 0 } : undefined });
const link = (texto, url, size = 16) => new ExternalHyperlink({ link: url, children: [new TextRun({ text: texto, font: FONT, size, style: "Hyperlink" })] });

function celda(contenido, ancho, o = {}) {
  const paras = (Array.isArray(contenido) ? contenido : [contenido]).map((c) =>
    c instanceof Paragraph ? c : new Paragraph({ children: [t(String(c), { size: o.size || 14, bold: o.bold, color: o.color })], spacing: { after: 0 } }));
  return new TableCell({ children: paras, width: { size: ancho, type: WidthType.DXA }, borders: o.sin ? undefined : bordes,
    shading: o.fill ? { type: ShadingType.CLEAR, color: "auto", fill: o.fill } : undefined,
    margins: { top: 25, bottom: 25, left: 70, right: 70 } });
}

function tabla(cols, filas, cab, fills = []) {
  const head = new TableRow({ tableHeader: true, children: cab.map((h, i) => celda(h, cols[i], { bold: true, color: "FFFFFF", fill: AZUL })) });
  return new Table({ width: { size: W, type: WidthType.DXA }, columnWidths: cols,
    rows: [head, ...filas.map((f, j) => new TableRow({ cantSplit: true, children: f.map((c, i) => celda(c, cols[i], { fill: fills[j] })) }))] });
}

// ------------------------------------------------------------------ figura (celda de media página)
const CW = Math.floor(W / 2);
function bloqueFigura(f) {
  const maxW = 330, maxH = { "Plano Fadesa": 315, "Catálogo Fadesa": 190, "Relevamiento de mercado": 235,
    "Norma / resolución": 230, "Ficha técnica de mercado": 250, "Planilla MP FLAMA": 150, "Proceso FLAMA": 290 }[f.tipo] || 300;
  let w = maxW, h = Math.round(f.ch * maxW / f.cw);
  if (h > maxH) { h = maxH; w = Math.round(f.cw * maxH / f.ch); }
  const img = new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 30 },
    children: [new ImageRun({ type: f.crop.endsWith(".jpg") ? "jpg" : "png", data: fs.readFileSync(f.crop),
      transformation: { width: w, height: h }, altText: { title: f.id, description: f.titulo, name: f.id } })] });
  const cab = new Paragraph({ spacing: { after: 20 }, keepNext: true, children: [t(`${f.id} · `, { bold: true, size: 16, color: AZUL }), t(f.titulo, { bold: true, size: 16 })] });
  const donde = new Paragraph({ spacing: { after: 20 }, children: [t(f.ubic + (f.link ? " · " : ""), { size: 13, color: "595959" }),
    ...(f.link ? [link("link", f.link, 13)] : [])] });
  const marcas = new Paragraph({ spacing: { after: f.nota ? 20 : 60 }, children: f.marcas.flatMap((m, i) => [
    t(`${m.n} `, { bold: true, size: 13, color: "C00000" }), t(m.etiqueta + (i < f.marcas.length - 1 ? "  ·  " : ""), { size: 13 })]) });
  const out = [cab, img, donde, marcas];
  if (f.nota) out.push(new Paragraph({ spacing: { after: 60 }, children: [t("Nota: " + f.nota, { size: 13, italics: true, color: "404040" })] }));
  return out;
}

function grilla(figs) {
  const filas = [];
  for (let i = 0; i < figs.length; i += 2) {
    const par = [figs[i], figs[i + 1]];
    filas.push(new TableRow({ cantSplit: true, children: par.map((f) => new TableCell({ width: { size: CW, type: WidthType.DXA },
      borders: sinBordes, margins: { top: 60, bottom: 60, left: 80, right: 80 },
      children: f ? bloqueFigura(f) : [new Paragraph({ children: [] })] })) }));
  }
  return new Table({ width: { size: W, type: WidthType.DXA }, columnWidths: [CW, CW], borders: sinBordes, rows: filas });
}

const porId = Object.fromEntries(C.figs.map((f) => [f.id, f]));
const rango = (a, b) => Array.from({ length: b - a + 1 }, (_, i) => porId[`F${String(a + i).padStart(2, "0")}`]).filter(Boolean);
const SECC = [
  ["1. Planos Fadesa de recipiente", "Cotas de los recipientes de 1 a 50 kg y detalles de unión (bordón, fondo encastrado, casquete con borde reducido).", rango(1, 6)],
  ["2. Planos Fadesa de extintor completo", "Válvula, manómetro, vástago, resorte, caño de pesca, racor, manguera, tobera y suncho medidos a escala; masa total.", rango(7, 13)],
  ["3. Catálogo Fadesa 3", "Peso, altura, ancho, profundidad, rueda, manga y presiones de cada modelo.", rango(14, 23)],
  ["4. Fichas de mercado y normas", "Masas de referencia sin plano Fadesa; cláusulas IRAM y resoluciones usadas (se citan, no se transcriben).", rango(24, 30).concat([porId.F40].filter(Boolean))],
  ["5. Relevamiento y planilla MP", "Identificación relevada en fotos (a validar) y celdas de la planilla de abastecimiento.", rango(31, 37)],
  ["6. Procesos FLAMA", "Documentos de proceso del usuario: medidas y uniones de carros, numerado, encastre y bordoneado de manuales.", rango(38, 39)],
];

const hijos = [];
// ------------------------------------------------------------------ página 1
hijos.push(new Paragraph({ spacing: { after: 60 }, children: [new TextRun({ text: "Justificación de medidas planos", font: FONT, size: 40, bold: true, color: AZUL })] }));
hijos.push(p([t("FLAMA S.A. · origen de cada dimensión de los planos FL_MAT, FL_REC y FL_DES · octubre de 2026", { size: 18, color: "595959" })], { after: 160 }));
[
  "Cada captura tiene marcas rojas numeradas sobre el dato tomado; debajo, qué dice cada marca. En el Excel «Justificacion de medidas planos.xlsx» la fuente de cada valor se escribe «F10·3» (figura F10, marca 3).",
  "Lo que no sale de un documento es un valor de diseño FLAMA: figura en la tabla final (D01…) con el link a la línea del generador y en amarillo en el Excel. Naranja = a validar.",
  "Los procesos FLAMA que mandaste (carros y manuales) fijan el 70 kg (Ø390 × 680), el 100 kg (900), las placas de refuerzo, el tren rodante soldado, el bordón, el encastre del fondo, la muesca del cuello y el número en la cúpula del 1 kg.",
  "Fadesa es referencia de medidas, no de criterio: donde no cumple la norma manda la IRAM. Ej.: el tren de rodaje sigue la IRAM 3550 tabla III (rueda ≥ Ø300, banda ≥ 50 —Fadesa usa 49—, trocha ≥ 400 entre centros) y no el ancho del catálogo.",
].forEach((x) => hijos.push(p(x, { bullet: true, after: 40 })));
const n = C.n, e = C.estados;
hijos.push(p([t(`${n} dimensiones: `, { bold: true }), t(`con documento ${e.V} (${Math.round(100 * e.V / n)} %), diseño FLAMA ${e.E} (${Math.round(100 * e.E / n)} %), a validar ${e.A || 0} (${Math.round(100 * (e.A || 0) / n)} %).`)], { before: 80, after: 120 }));
hijos.push(p("Lo que falta validar", { heading: HeadingLevel.HEADING_2 }));
hijos.push(tabla([3700, 2300, 4306], C.pendientes.map((x) => [x.que, x.modelos, x.criterio]), ["Pieza: dimensión", "Modelos", "Criterio usado / qué confirmar"],
  C.pendientes.map(() => EST.A)));

// ------------------------------------------------------------------ figuras
SECC.forEach(([tit, intro, figs]) => {
  hijos.push(p(tit, { heading: HeadingLevel.HEADING_1, keepNext: true, before: 160 }));
  hijos.push(p(intro, { size: 16, after: 60, keepNext: true }));
  hijos.push(grilla(figs));
});

// ------------------------------------------------------------------ valores de diseño
hijos.push(p("7. Valores de diseño FLAMA (sin documento)", { heading: HeadingLevel.HEADING_1, keepNext: true, before: 160 }));
hijos.push(p(`Línea exacta del generador de planos (commit ${C.sha.slice(0, 7)}). Amarillo = decisión de diseño a confirmar con el proveedor o el prototipo; naranja = a validar.`, { size: 16, after: 80 }));
hijos.push(tabla([560, 3700, 3600, 1246, 1200], C.disenos.map((d) => [d.id, d.que, d.criterio, d.modelos,
  new Paragraph({ children: [link(`${d.archivo}:${d.linea}`, d.link, 13)] })]), ["Id", "Qué define", "Criterio", "Modelos", "Código"],
  C.disenos.map((d) => EST[d.estado])));

const doc = new Document({
  creator: "FLAMA S.A.", title: "Justificación de medidas planos",
  styles: {
    default: { document: { run: { font: FONT, size: 18 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, font: FONT, color: AZUL }, paragraph: { spacing: { before: 160, after: 60 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 22, bold: true, font: FONT, color: AZUL }, paragraph: { spacing: { before: 100, after: 60 }, outlineLevel: 1 } },
    ],
  },
  numbering: { config: [{ reference: "vinetas", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
    style: { paragraph: { indent: { left: 400, hanging: 220 } } } }] }] },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 850, bottom: 850, left: 800, right: 800 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [
      new TextRun({ text: "Justificación de medidas planos — FLAMA S.A. — pág. ", font: FONT, size: 14, color: "808080" }),
      new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 14, color: "808080" }),
      new TextRun({ text: " de ", font: FONT, size: 14, color: "808080" }),
      new TextRun({ children: [PageNumber.TOTAL_PAGES], font: FONT, size: 14, color: "808080" })] })] }) },
    children: hijos,
  }],
});
Packer.toBuffer(doc).then((b) => { fs.writeFileSync(OUT, b); console.log("ok", OUT, b.length); });
