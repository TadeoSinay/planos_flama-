// Word «Justificación de medidas planos» (versión compacta): capturas marcadas de a dos y, al final, el análisis de
// las medidas de diseño FLAMA (técnica, norma, economía y conclusión de cada una, de analisis.py).
const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell, WidthType, ShadingType,
  HeadingLevel, AlignmentType, ExternalHyperlink, Footer, PageNumber, LevelFormat, BorderStyle, PageBreak, LineRuleType,
} = require("docx");

const SP = "/tmp/claude-0/-home-user-TP-optimizacion/15292aaf-e550-5dee-a83e-77fd9177a6ef/scratchpad";
const OUT = process.argv[2] || "/home/user/planos_flama-/salida/justificacion/Justificacion de medidas planos.docx";
const C = JSON.parse(fs.readFileSync(`${SP}/jw/compacto.json`, "utf8"));
const AN = JSON.parse(fs.readFileSync(`${SP}/jw/analisis.json`, "utf8"));
// Escala por fila de figuras (clave: figura de la izquierda), calculada por ajuste.py para que no queden huecos al pie.
const ESC = (() => { try { return JSON.parse(fs.readFileSync(`${SP}/jw/escala.json`, "utf8")); } catch (_) { return {}; } })();

const W = 10306; // ancho útil (DXA): A4 con márgenes de 1,5 cm
const FONT = "Arial";
const AZUL = "1F3864";
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

// partir: las filas pueden cortarse entre páginas; titulo: fila de título a todo el ancho que se repite con el encabezado.
function tabla(cols, filas, cab, fills = [], partir = false, titulo = null) {
  const head = new TableRow({ tableHeader: true, children: cab.map((h, i) => celda(h, cols[i], { bold: true, color: "FFFFFF", fill: AZUL })) });
  const tit = titulo ? [new TableRow({ tableHeader: true, cantSplit: true, children: [new TableCell({ columnSpan: cols.length,
    width: { size: W, type: WidthType.DXA }, borders: bordes, shading: { type: ShadingType.CLEAR, color: "auto", fill: "D9E2F3" },
    margins: { top: 40, bottom: 40, left: 70, right: 70 },
    children: [new Paragraph({ spacing: { after: 0 }, children: [t(titulo, { bold: true, size: 20, color: AZUL })] })] })] })] : [];
  return new Table({ width: { size: W, type: WidthType.DXA }, columnWidths: cols,
    rows: [...tit, head, ...filas.map((f, j) => new TableRow({ cantSplit: !partir, children: f.map((c, i) => celda(c, cols[i], { fill: fills[j] })) }))] });
}

// ------------------------------------------------------------------ figura (celda de media página)
const CW = Math.floor(W / 2);
function bloqueFigura(f, s = 1) {
  const maxW = 330, maxH = { "Plano Fadesa": 315, "Catálogo Fadesa": 190, "Relevamiento de mercado": 235,
    "Norma / resolución": 230, "Ficha técnica de mercado": 250, "Planilla MP FLAMA": 150, "Proceso FLAMA": 290 }[f.tipo] || 300;
  let w = maxW, h = Math.round(f.ch * maxW / f.cw);
  if (h > maxH) { h = maxH; w = Math.round(f.cw * maxH / f.ch); }
  w = Math.round(w * s); h = Math.round(h * s);
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

// Una tabla por fila de figuras (separadas por un renglón de 1 pt): así el título de la sección queda unido sólo a la
// primera fila, también en LibreOffice, que une un párrafo «conservar con el siguiente» a la tabla entera.
const sep = () => new Paragraph({ spacing: { after: 0, before: 0, line: 20, lineRule: LineRuleType.EXACT }, children: [] });
function grilla(figs) {
  const out = [];
  for (let i = 0; i < figs.length; i += 2) {
    const par = [figs[i], figs[i + 1]], s = ESC[figs[i].id] || 1;
    out.push(new Table({ width: { size: W, type: WidthType.DXA }, columnWidths: [CW, CW], borders: sinBordes,
      rows: [new TableRow({ cantSplit: true, children: par.map((f) => new TableCell({ width: { size: CW, type: WidthType.DXA },
        borders: sinBordes, margins: { top: 60, bottom: 60, left: 80, right: 80 },
        children: f ? bloqueFigura(f, s) : [new Paragraph({ children: [] })] })) })] }), sep());
  }
  return out;
}

const porId = Object.fromEntries(C.figs.map((f) => [f.id, f]));
const rango = (a, b) => Array.from({ length: b - a + 1 }, (_, i) => porId[`F${String(a + i).padStart(2, "0")}`]).filter(Boolean);
const SECC = [
  ["1. Planos Fadesa de recipiente", "Cotas de los recipientes de 1 a 50 kg y detalles de unión (bordón, fondo encastrado, casquete con borde reducido).", rango(1, 6)],
  ["2. Planos Fadesa de extintor completo", "Válvula, manómetro, vástago, resorte, caño de pesca, racor, manguera, tobera y suncho medidos a escala; masa total.", rango(7, 13)],
  ["3. Catálogo Fadesa 3", "Peso, altura, ancho, profundidad, rueda, manga y presiones de cada modelo.", rango(14, 23)],
  ["4. Fichas de mercado y normas", "Masas de referencia sin plano Fadesa; cláusulas IRAM y resoluciones usadas (se citan, no se transcriben).", rango(24, 30).concat([porId.F40].filter(Boolean))],
  ["5. Relevamiento y planilla MP", "Identificación relevada en fotos (justificada en la sección 8) y celdas de la planilla de abastecimiento.", rango(31, 37)],
  ["6. Procesos FLAMA", "Documentos de proceso del usuario: medidas y uniones de carros, numerado, encastre y bordoneado de manuales.", rango(38, 39)],
  ["7. Carro: triángulos con V, caño del eje, manija, flejes, pata y lanza", "Proceso de carros v2 que mandaste (dónde va cada accesorio, plantilla de posiciones y piezas del kit: F46 a F48), plano Fadesa del rodante de 800 mm (manija doblada 30°, pata afinada y soldada), foto del carro relevado y las fotos que marcaste (soldadura de la barra lateral, altura del doblez y lanza con válvula esférica), la hoja de especificaciones «Polvos carros» (F49) y el proceso final de carros (manija, carro armado y fleje: F50 a F52).", rango(41, 52)],
];

const hijos = [];
// ------------------------------------------------------------------ página 1
hijos.push(new Paragraph({ spacing: { after: 60 }, children: [new TextRun({ text: "Justificación de medidas planos", font: FONT, size: 40, bold: true, color: AZUL })] }));
hijos.push(p([t("FLAMA S.A. · origen de cada dimensión de los planos FL_MAT, FL_REC y FL_DES · octubre de 2026", { size: 18, color: "595959" })], { after: 160 }));
[
  "Cada captura tiene marcas rojas numeradas sobre el dato tomado; debajo, qué dice cada marca. La fuente de un valor se cita «F10·3» (figura F10, marca 3).",
  "Lo que no sale de un documento es una decisión de diseño FLAMA: la sección 8 justifica cada una con el cálculo de estática y resistencia, la cláusula de norma que la alcanza y su costo frente a la alternativa. Lo que depende del proveedor queda como condición de compra (tabla de abajo).",
  "Los procesos FLAMA que mandaste (carros y manuales) fijan el 70 kg (Ø390 × 680), el 100 kg (900), las placas de refuerzo, el tren rodante soldado, el bordón, el encastre del fondo, la muesca del cuello y el número en la cúpula del 1 kg.",
  "El carro sigue el proceso de carros v2 (F46 a F48): dos triángulos de chapa 4,75 con una V de 90° hacia atrás donde se apoya el caño del eje (la chapa no lo envuelve; el caño no gira y el eje pasa por adentro al montaje final con arandelas y pasadores), manija de caño 1\" × 2,0 con las puntas aplastadas en lengüetas de 40 × 60 soldadas a los costados (sin orejas), flejes Ω para la manga y la pata delantera; las posiciones salen de la tabla del proceso. La válvula esférica con palanca de la lanza sale de tu foto (F45). Las medidas de conjunto de los carros de polvo (alto, ancho, profundidad, rueda y manga) son las de la hoja «Polvos carros» (F49): el ancho fija el largo del eje y la trocha, el alto ubica la curva de 30° de la manija y la profundidad la marca la palanca de la válvula. Los flejes tienen la base que da vueltas enteras con el largo de manga y patas hasta delante de la última vuelta; el de 100 kg lleva un tercero en el medio con las orejas hacia adentro, que cierra el paquete y deja la manga tensa.",
  "Fadesa es referencia de medidas, no de criterio: donde no cumple la norma manda la IRAM. Ej.: el tren de rodaje sigue la IRAM 3550 tabla III (rueda ≥ Ø300, banda ≥ 50 —Fadesa usa 49—, trocha ≥ 400 entre centros) y no el ancho del catálogo.",
].forEach((x) => hijos.push(p(x, { bullet: true, after: 40 })));
const n = C.n, e = C.estados;
const dis = e.E + (e.A || 0);
hijos.push(p([t(`${n} dimensiones: `, { bold: true }), t(`con documento ${e.V} (${Math.round(100 * e.V / n)} %) y diseño FLAMA ${dis} (${Math.round(100 * dis / n)} %), justificado en la sección 8 con cálculo, norma y costo.`)], { before: 80, after: 120 }));
const ITEMS = AN.grupos.flatMap((g) => g.items);
const COND = ITEMS.filter((x) => x.condicion);
hijos.push(p("Condiciones de compra que surgen del análisis", { heading: HeadingLevel.HEADING_2 }));
hijos.push(tabla([700, 3500, 6106], COND.map((x) => [x.id, x.titulo, x.condicion]), ["Ítem", "Medida", "Condición para comprar o certificar"]));

// ------------------------------------------------------------------ figuras
SECC.forEach(([tit, intro, figs]) => {
  hijos.push(p(tit, { heading: HeadingLevel.HEADING_1, keepNext: true, before: 160 }));
  hijos.push(p(intro, { size: 16, after: 60, keepNext: true }));
  hijos.push(...grilla(figs));
});

// ------------------------------------------------------------------ análisis de las medidas de diseño
hijos.push(p("8. Análisis y justificación de las medidas de diseño", { heading: HeadingLevel.HEADING_1, keepNext: true, before: 160 }));
hijos.push(p("Medidas que no salen de un documento. Cada una se justifica con el cálculo de estática y resistencia de materiales (o la lógica de uso), la cláusula de la norma que la alcanza (se cita, no se transcribe), el costo frente a la alternativa y la conclusión; si algo depende del proveedor, la condición de compra que lo cierra.", { size: 16, after: 40 }));
hijos.push(p([t("Bases de cálculo: ", { bold: true, size: 16 }), t("presiones de servicio / ensayo de la hoja de cada modelo (ABC manuales 1,4 / 3,5 MPa; rodantes 1,4 / 4,0; agua y espuma 0,8 / 2,0; CO₂ 15 / 25). Tensiones: virola σ = p·D / 2t; casquete elipsoidal con su factor de forma K; ejes y pasadores al corte doble; eje de rueda a flexión en voladizo. Materiales con su fluencia mínima: chapa del recipiente 265 MPa, SAE 1010 180, SAE 1045 trefilado 530, inoxidable 304 205 (σ0,2 de ASTM A240). CO₂ con su ecuación de estado (Span-Wagner). Precios: LAC USD 1,10/kg y lista HZ de válvulas.", { size: 16 })], { after: 80 }));
const pc = (runs, after = 20) => new Paragraph({ children: runs, spacing: { after } });
const ETQ = [["tecnica", "Técnica: "], ["norma", "Norma: "], ["economia", "Económica: "], ["conclusion", "Conclusión: "]];
AN.grupos.forEach((g, gi) => {
  if (gi) hijos.push(p("", { after: 100 }));
  hijos.push(tabla([2500, 7806], g.items.map((x) => [
    [pc([t(`${x.id} `, { bold: true, size: 14, color: AZUL }), t(x.titulo, { bold: true, size: 14 })]),
      pc([t(x.valor, { size: 14 })]), pc([t(x.modelos, { size: 13, color: "595959" })], 0)],
    [...ETQ.map(([k, e2], i) => pc([t(e2, { bold: true, size: 14 }), t(x[k], { size: 14 })], i === 3 && !x.condicion ? 0 : 20)),
      ...(x.condicion ? [pc([t("Condición de compra: ", { bold: true, size: 14, color: "C00000" }), t(x.condicion, { size: 14 })], 0)] : [])],
  ]), ["Medida y valor adoptado", "Justificación"], [], true, g.titulo));
});

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
