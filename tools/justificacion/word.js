// Word «Justificación de medidas planos»: capturas marcadas de cada fuente.
const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell, WidthType, ShadingType,
  HeadingLevel, AlignmentType, PageBreak, ExternalHyperlink, Footer, PageNumber, LevelFormat, BorderStyle,
  TableOfContents,
} = require("docx");

const SP = "/tmp/claude-0/-home-user-TP-optimizacion/15292aaf-e550-5dee-a83e-77fd9177a6ef/scratchpad";
const OUT = "/home/user/planos_flama-/salida/justificacion/Justificacion de medidas planos.docx";
const D = JSON.parse(fs.readFileSync(`${SP}/jw/word.json`, "utf8"));

const W = 9866; // ancho útil (DXA) en A4 con márgenes de 1,8 cm
const FONT = "Arial";
const AZUL = "1F3864";
const borde = { style: BorderStyle.SINGLE, size: 4, color: "BFBFBF" };
const bordes = { top: borde, bottom: borde, left: borde, right: borde };

const t = (text, o = {}) => new TextRun({ text, font: FONT, size: o.size || 20, bold: o.bold, italics: o.italics, color: o.color });
const p = (runs, o = {}) => new Paragraph({ children: Array.isArray(runs) ? runs : [t(runs, o)], spacing: { after: o.after ?? 100 },
  alignment: o.align, heading: o.heading, keepNext: o.keepNext, numbering: o.bullet ? { reference: "vinetas", level: 0 } : undefined });
const link = (texto, url) => new ExternalHyperlink({ link: url, children: [new TextRun({ text: texto, font: FONT, size: 20, style: "Hyperlink" })] });

function celda(contenido, ancho, o = {}) {
  const paras = (Array.isArray(contenido) ? contenido : [contenido]).map((c) =>
    c instanceof Paragraph ? c : new Paragraph({ children: [t(String(c), { size: o.size || 18, bold: o.bold, color: o.color })], spacing: { after: 40 } }));
  return new TableCell({ children: paras, width: { size: ancho, type: WidthType.DXA }, borders: bordes,
    shading: o.fill ? { type: ShadingType.CLEAR, color: "auto", fill: o.fill } : undefined,
    margins: { top: 50, bottom: 50, left: 90, right: 90 } });
}

function tabla(cols, filas, cab) {
  const head = new TableRow({ tableHeader: true, children: cab.map((h, i) => celda(h, cols[i], { bold: true, color: "FFFFFF", fill: AZUL })) });
  return new Table({ width: { size: W, type: WidthType.DXA }, columnWidths: cols,
    rows: [head, ...filas.map((f) => new TableRow({ children: f.map((c, i) => celda(c, cols[i])) }))] });
}

function imagen(f) {
  const maxW = 640, maxH = 800;
  let w = maxW, h = Math.round(f.h * maxW / f.w);
  if (h > maxH) { h = maxH; w = Math.round(f.w * maxH / f.h); }
  return new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 60 },
    children: [new ImageRun({ type: f.img.endsWith(".jpg") ? "jpg" : "png", data: fs.readFileSync(f.img), transformation: { width: w, height: h },
      altText: { title: f.id, description: f.titulo, name: f.id } })] });
}

const hijos = [];
// ------------------------------------------------------------------ portada
hijos.push(new Paragraph({ spacing: { before: 2400, after: 200 }, alignment: AlignmentType.CENTER,
  children: [new TextRun({ text: "Justificación de medidas planos", font: FONT, size: 48, bold: true, color: AZUL })] }));
hijos.push(p([t("FLAMA S.A. — origen de cada dimensión de los planos FL_MAT y FL_REC", { size: 26 })], { align: AlignmentType.CENTER, after: 600 }));
hijos.push(p([t("Octubre de 2026", { size: 22 })], { align: AlignmentType.CENTER, after: 200 }));
hijos.push(p([t("Complemento: «Justificacion de medidas planos.xlsx» (valores crudos pieza a pieza)", { size: 20, italics: true })],
  { align: AlignmentType.CENTER, after: 200 }));
hijos.push(new Paragraph({ children: [new PageBreak()] }));

// ------------------------------------------------------------------ cómo leer
hijos.push(p("Cómo leer este documento", { heading: HeadingLevel.HEADING_1 }));
[
  "Cada figura es una captura del documento del que se sacó una medida de los planos: planos Fadesa, catálogo Fadesa 3, fichas técnicas, normas IRAM y resoluciones, fotos del relevamiento de mercado, la planilla MP de FLAMA o, cuando no hay documento externo, la línea del generador de planos donde está escrito el valor de diseño.",
  "Los rectángulos rojos numerados marcan exactamente el dato tomado. La tabla debajo de cada figura dice qué valor se leyó en cada marca y en qué piezas de qué planos se usa.",
  "El Excel «Justificacion de medidas planos.xlsx» tiene los valores crudos: una fila por dimensión de cada pieza de los 17 planos, con las columnas «Fig. Word» y «Marca» que apuntan a este documento, la cuenta cuando el valor se calculó y el link a la línea exacta del código.",
  "Colores del Excel (mismo criterio que el BOM): sin color = tomado de un documento o calculado sólo con datos documentados; amarillo = valor de diseño FLAMA o estimado, sin documento; naranja = a validar.",
].forEach((x) => hijos.push(p(x, { bullet: true })));

hijos.push(p("Origen de las dimensiones de los planos", { heading: HeadingLevel.HEADING_2 }));
const n = D.n;
hijos.push(tabla([5400, 2200, 2266], D.tipos.map(([tipo, c]) => [tipo, String(c), `${Math.round(100 * c / n)} %`]),
  ["Tipo de origen", "Dimensiones", "% del total"]));
hijos.push(p(`Total: ${n} dimensiones. Con documento (sin color): ${D.estados.V}; diseño FLAMA o estimado (amarillo): ${D.estados.E}; a validar (naranja): ${D.estados.A}.`,
  { after: 200 }));

// ------------------------------------------------------------------ índice de figuras
hijos.push(p("Índice de figuras", { heading: HeadingLevel.HEADING_2 }));
const filasIdx = [];
D.secciones.forEach((s) => s.figs.forEach((f) => filasIdx.push([f.id, f.titulo, f.tipo, String(f.marcas.length)])));
hijos.push(tabla([800, 6066, 2200, 800], filasIdx, ["Fig.", "Fuente", "Tipo", "Marcas"]));

// ------------------------------------------------------------------ secciones
D.secciones.forEach((s, i) => {
  hijos.push(new Paragraph({ children: [new PageBreak()] }));
  hijos.push(p(`${i + 1}. ${s.titulo}`, { heading: HeadingLevel.HEADING_1 }));
  hijos.push(p(s.intro, { after: 200 }));
  s.figs.forEach((f, j) => {
    if (j > 0) hijos.push(new Paragraph({ children: [new PageBreak()] }));
    hijos.push(p(`${f.id} · ${f.titulo}`, { heading: HeadingLevel.HEADING_2, keepNext: true }));
    hijos.push(p([t("Documento: ", { bold: true }), t(f.fuente)], { after: 40 }));
    hijos.push(p([t("Dónde: ", { bold: true }), t(f.ubic)], { after: f.link ? 40 : 120 }));
    if (f.link) hijos.push(p([t("Link: ", { bold: true }), link(f.link, f.link)], { after: 120 }));
    hijos.push(imagen(f));
    hijos.push(p([t(`Figura ${f.id}. En rojo, el dato tomado de la fuente.`, { size: 16, italics: true, color: "595959" })],
      { align: AlignmentType.CENTER, after: 160 }));
    const code = f.tipo.startsWith("Diseño");
    if (code) {
      hijos.push(tabla([900, 8966], f.marcas.map((m) => [String(m.n), m.etiqueta]), ["Marca", "Líneas resaltadas"]));
      hijos.push(p([t("Se usa en: ", { bold: true }), t(`${f.n_usos} dimensiones del Excel — ` + f.usos_global.join("; ") + ".")],
        { after: 120 }));
    } else {
      const filas = f.marcas.map((m) => [String(m.n), m.etiqueta,
        m.usos.length ? m.usos.map((u) => new Paragraph({ children: [t(u, { size: 16 })], spacing: { after: 20 } }))
          .concat(m.mas ? [new Paragraph({ children: [t(`… y ${m.mas} más (ver Excel, columna «Fig. Word» = ${f.id})`, { size: 16, italics: true })] })] : [])
          : "—"]);
      hijos.push(tabla([700, 3500, 5666], filas, ["Marca", "Dato tomado", "Se usa en (modelo — pieza: dimensión = valor del plano)"]));
    }
    if (f.nota) hijos.push(p([t("Nota: ", { bold: true, size: 18 }), t(f.nota, { italics: true, size: 18 })], { after: 120 }));
  });
});

// ------------------------------------------------------------------ pendientes
hijos.push(new Paragraph({ children: [new PageBreak()] }));
hijos.push(p("Medidas a validar (naranja en el Excel)", { heading: HeadingLevel.HEADING_1 }));
hijos.push(p("Son las que no tienen un documento que las fije: la geometría derivada del 70 kg y las medidas de identificación relevadas en fotos. Hay que confirmarlas con el proveedor (Gockel para los casquetes), con IRAM y la AGC, o con el prototipo.", { after: 120 }));
D.pendientes.forEach((x) => hijos.push(p(x, { bullet: true, after: 40 })));

const doc = new Document({
  creator: "FLAMA S.A.", title: "Justificación de medidas planos",
  styles: {
    default: { document: { run: { font: FONT, size: 20 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 30, bold: true, font: FONT, color: AZUL }, paragraph: { spacing: { before: 120, after: 160 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 24, bold: true, font: FONT, color: AZUL }, paragraph: { spacing: { before: 120, after: 100 }, outlineLevel: 1 } },
    ],
  },
  numbering: { config: [{ reference: "vinetas", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
    style: { paragraph: { indent: { left: 540, hanging: 270 } } } }] }] },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1020, bottom: 1020, left: 1020, right: 1020 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [
      new TextRun({ text: "Justificación de medidas planos — FLAMA S.A. — pág. ", font: FONT, size: 16, color: "808080" }),
      new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 16, color: "808080" }),
      new TextRun({ text: " de ", font: FONT, size: 16, color: "808080" }),
      new TextRun({ children: [PageNumber.TOTAL_PAGES], font: FONT, size: 16, color: "808080" })] })] }) },
    children: hijos,
  }],
});
Packer.toBuffer(doc).then((b) => { fs.writeFileSync(OUT, b); console.log("ok", OUT, b.length); });
