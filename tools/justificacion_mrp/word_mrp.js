// Word «Justificación_MRP»: de dónde sale cada valor de salida/mrp/FLAMA_MRP.xlsx (una tabla por hoja, con el código
// Ref. de cada fila del Excel) y las capturas marcadas de los procesos, planillas, BOM y cotizaciones citados.
// Lee el JSON de datos_mrp.py. Sólo negro y grises. Uso: node word_mrp.js <datos.json> <salida.docx>
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

// ------------------------------------------------------------------ utilidades del cuerpo
const LIN = ["MANUALES", "RODANTES", "RECARGAS", "REVENDIDOS"];
const hijos = [];
const vistas = new Set();
// las capturas angostas van de a dos por fila
D.capturas.forEach((c) => { c.medio = c.id !== "G01" && (c.w < 1300 || c.h < 420); });
// muestra, al final de cada sección, las capturas citadas que todavía no se vieron
function capturas(ids) {
  const nuevas = [...new Set(ids)].filter((i) => !vistas.has(i) && CAP[i]);
  nuevas.forEach((i) => vistas.add(i));
  if (nuevas.length) hijos.push(...figs(nuevas));
}
const fg = (ids) => [...new Set(ids || [])].filter((i) => CAP[i] || i.startsWith("W")).join(", ");
const corto = (x) => String(x).split(" (")[0];
// M01, M02, M03, M07 → «M01–M03, M07»
function rango(refs) {
  const out = [];
  let a = null, b = null;
  const num = (r) => parseInt(r.replace(/^\D+/, ""), 10);
  refs.forEach((r) => {
    if (a && num(r) === num(b) + 1 && r[0] === a[0]) { b = r; return; }
    if (a) out.push(a === b ? a : `${a}–${b}`);
    a = b = r;
  });
  if (a) out.push(a === b ? a : `${a}–${b}`);
  return out.join(", ");
}
// agrupa las filas de una línea que se calculan igual (mismo texto y mismas figuras)
function grupos(filas) {
  const m = new Map();
  filas.forEach((f) => {
    const k = f.como + "|" + f.figs.join(",");
    if (!m.has(k)) m.set(k, { refs: [], mats: [], como: f.como, figs: f.figs });
    const g = m.get(k);
    g.refs.push(f.ref);
    const nm = corto(f.material) + (f.destino ? ` (${f.destino})` : "");
    if (!g.mats.includes(nm)) g.mats.push(nm);
  });
  return [...m.values()];
}

// ------------------------------------------------------------------ portada
hijos.push(new Paragraph({ spacing: { after: 60 }, children: [new TextRun({ text: "Justificación del MRP", font: FONT, size: 40, bold: true })] }));
hijos.push(p([t("FLAMA S.A. · de dónde sale cada valor de FLAMA_MRP.xlsx · octubre de 2026", { size: 18, color: GRIS_O })], { after: 140 }));
[
  "Una sola cuenta: lo que hay que comprar de cada material = consumo por unidad de producto × unidades a producir. Se suman las cuatro líneas (manuales, rodantes, recargas de la planta industrial y revendidos) y, con el mes pico de 2035, se arma la política de stock.",
  "Sin supuestos: cada valor sale de un proceso, el BOM, las Proyecciones, los Dimensionamientos, la planilla de MP, una cotización o una ficha técnica. Lo que no tiene consumo documentado se compra por punto de pedido (sección 6).",
  "En el Excel cada fila tiene un código «Ref.»; acá están agrupados con de dónde salen y la figura. P = proceso de manuales o carros, R = proceso de recargas, F = Dimensionamiento Técnico FLAMA, X = otras planillas, B = BOM, Q = cotización, M y G = el MRP. El dato está marcado en rojo.",
].forEach((x) => hijos.push(vin(x)));

// ------------------------------------------------------------------ 1. cómo se lee
hijos.push(h1("1. Cómo se lee: el ABC 5 kg"));
const M = D.lineas.MANUALES;
const k5 = M.productos.indexOf("ABC 5 kg");
const d5 = M.demanda35[k5];
const ej = ["MP-03", "MP-07", "MP-33", "MP-43"].map((c) => M.filas.find((f) => f.codigo === c));
hijos.push(...tabla([10, 40, 18, 18, 14], ["Ref.", "Material", "Por matafuego", `× ${n(d5, 0)} matafuegos =`, "Figura"],
  ej.map((f) => [f.ref, corto(f.material), `${n(f.cons["ABC 5 kg"], 4)} ${f.um}`, `${n(f.cons["ABC 5 kg"] * d5, 0)} ${f.um}`, fg(f.figs)]),
  { num: [2, 3] }));
hijos.push(nota("Cada hoja de línea hace esa cuenta para todos sus productos y los 10 años: arriba la demanda, abajo el consumo por unidad, a la derecha lo que hay que comprar."));
capturas(["M03"]);

// ------------------------------------------------------------------ 2. demanda
hijos.push(h1("2. Demanda (hoja DEMANDA)"));
const DG = (refs) => D.demanda.filter((x) => refs.includes(x.ref));
const dd = Object.fromEntries(D.demanda.map((x) => [x.ref, x]));
hijos.push(...tabla([14, 30, 56], ["Ref.", "Dato", "De dónde sale (figura)"], [
  ["D01", `Parte de las recargas que hace la planta industrial: ${pc(dd.D01.v35, 1)}. Multiplica las recargas y los sustitutos`, `${dd.D01.como} (${fg(dd.D01.figs)})`],
  ["D02", `% de unidades nuevas que van a CABA: ${pc(dd.D02.v35, 1)}. Reparte tarjetas y obleas entre AGC y DPS`, `${dd.D02.como} (${fg(dd.D02.figs)})`],
  ["D03", `% de recargas de la planta industrial en CABA: ${pc(dd.D03.v35, 1)}. Lo mismo en recargas`, `${dd.D03.como} (${fg(dd.D03.figs)})`],
  ["D04", `% de recargas de equipos usados: ${pc(dd.D04.v35, 2)}. Entra en el polvo de recarga`, `${dd.D04.como} (${fg(dd.D04.figs)})`],
  ["D05–D20", "Matafuegos y cilindros de manuales y rodantes", "Indexado, producción de matafuegos y de cilindros. El ABC 5 kg suma la venta de reserva; ABC 5, 10, 50 y 100 kg suman los sustitutos nuevos de la planta industrial: son matafuegos que fabrica FLAMA. (X01, X03)"],
  ["D21–D37", "Recargas de 17 tipos", "(Indexado + recarga anual del pool de sustitutos) × D01. (X01, X03)"],
  ["D38", "Sustitutos nuevos (kit)", "Alta anual de sustitutos × D01: cada uno lleva su kit de identificación. (X03)"],
  ["D39–D47", "Revendidos de 9 tipos", "Indexado, matafuegos terciarizados + sustitutos nuevos que no son ABC (se compran). (X01, X03)"],
]));
hijos.push(nota(`Control: el proceso de recargas dice 13 recargas de BC por mes en la planta industrial; el MRP da ${n(D.lineas.RECARGAS.demanda35[7] / 12, 0)}.`));
capturas(["X01", "X03", "X02", "X13", "X04"]);

// ------------------------------------------------------------------ 3. estacionalidad
hijos.push(h1("3. Estacionalidad (hoja ESTACIONALIDAD)"));
hijos.push(nota("Como el Dimensionamiento Técnico FLAMA: producción de cada mes de 2035 = demanda del año × perfil. El mes pico es el de mayor producción de la línea. Recargas: anual / 12. Revendidos: el perfil de su tamaño."));
hijos.push(...tabla([7, 27, ...Array(12).fill(5.5)], ["Ref.", "Perfil", "E", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"],
  D.perfiles.map((x) => [x.ref, x.nombre, ...x.meses.map((v) => pc(v, 1))]), { num: [...Array(12).keys()].map((i) => i + 2) }));
hijos.push(...tabla([8, 14, 10, 15, 15, 12, 26], ["Ref.", "Línea", "Mes pico", "Producción del mes pico", "Promedio mensual", "Factor de pico", "Control"],
  LIN.map((l) => { const x = D.picos[l]; return [x.ref, l, x.mes, n(x.unidades, 0), n(x.promedio, 0), n(x.factor, 3),
    l === "MANUALES" ? "Proceso: 1.665 / 1.184 = 1,406" : l === "RECARGAS" ? "Sin estacionalidad (F03)" : ""]; }), { num: [3, 4, 5] }));
capturas(["F01", "F02", "F03"]);

// ------------------------------------------------------------------ 4. consumo por unidad
hijos.push(h1("4. Consumo por unidad (hojas MANUALES, RODANTES, RECARGAS y REVENDIDOS)"));
hijos.push(nota("Las filas que se calculan igual están juntas. «(CABA)» o «(PBA)»: se multiplica por el % que va a esa jurisdicción (D02, D03)."));
const TIT = { MANUALES: "4.1 Manuales", RODANTES: "4.2 Rodantes", RECARGAS: "4.3 Recargas de la planta industrial", REVENDIDOS: "4.4 Revendidos" };
const INTRO = {
  MANUALES: "El tubo pescante del 2,5, 5 y 10 kg (MP-46, PVC rígido como el caño de pesca del BOM) se compra aparte de la válvula, como lo pone la planilla de MP; el del 1 kg viene en la válvula M-22. Dos proveedores: Esinex (W19) y Securitá (W20).",
  RODANTES: "El tubo pescante de los carros (MP-47) se compra aparte de la válvula y es de acero SAE 1010, como lo pide la planilla de MP. Dos proveedores: Mozart (W21) y Georgia (W23); los dos lo usan de acero al carbono en sus matafuegos.",
  RECARGAS: "Sin soldadura: un recipiente que se recarga no se suelda. Los repuestos (válvula, manómetro, manguera) no entran: se cambian si están dañados y su stock sale del registro de repuestos (R04).",
};
LIN.forEach((l) => {
  const L_ = D.lineas[l];
  hijos.push(h2(TIT[l]));
  if (INTRO[l]) hijos.push(nota(INTRO[l]));
  const gs = grupos(L_.filas);
  hijos.push(...tabla([11, 29, 48, 12], ["Ref.", "Material", "Cómo se calcula", "Figura"],
    gs.map((g) => [rango(g.refs), g.mats.join(", "), g.como, fg(g.figs)])));
  capturas([...(l === "RECARGAS" ? ["R01"] : []), ...gs.flatMap((g) => g.figs)]);
});

// ------------------------------------------------------------------ 5. política
hijos.push(h1("5. Política de stock (hoja POLITICA_STOCK)"));
const pe = D.politica.find((x) => x.codigo === "MP-03");
hijos.push(nota(`Para cada material la hoja contesta cuándo pedir, cuánto pedir y cuánto lugar ocupa. Ejemplo: ${pe.codigo}, hoja de 1,6 mm del 5 kg.`, { keepNext: true }));
hijos.push(...tabla([24, 36, 40], ["Columna", "Qué es", `${pe.codigo} en 2035`], [
  ["Consumo por día", "La velocidad de consumo: promedio (año / 240) y en el mes pico (mes pico / 20)", `${n(pe.dprom, 1)} hojas por día; ${n(pe.dpico, 0)} en el mes pico`],
  ["Plazo de entrega (lead time)", "Cuántos días tarda el proveedor desde que se le pide. Es tiempo, no cantidad", `${pe.ltmin} a ${pe.ltmax} días (Pradecon)`],
  ["Consumo mientras llega el pedido", "Lo que se gasta esperando: consumo promedio × plazo medio", `${n(pe.dprom, 1)} × ${n((pe.ltmin + pe.ltmax) / 2, 1)} = ${n(pe.enlt, 0)} hojas`],
  ["Stock de seguridad", "Colchón para el mes pico y la demora máxima: consumo del pico × plazo máximo − consumo mientras llega", `${n(pe.dpico, 0)} × ${pe.ltmax} − ${n(pe.enlt, 0)} = ${n(pe.ss, 0)} hojas`],
  ["Punto de pedido", "El nivel de stock que dispara el pedido: consumo mientras llega + seguridad", `${n(pe.enlt, 0)} + ${n(pe.ss, 0)} = ${n(pe.pp, 0)} hojas`],
  ["Cantidad por pedido", "Consumo del mes pico durante los días entre pedidos (planilla de MP), en unidades de compra enteras", `${n(pe.dpico, 0)} × ${pe.t} días → ${pe.pedido} paquetes de ${pe.cont} = ${n(pe.pedido * pe.cont, 0)} hojas`],
  ["Stock máximo", "Lo que hay cuando llega el pedido: seguridad + pedido", `${n(pe.ss, 0)} + ${n(pe.pedido * pe.cont, 0)} = ${n(pe.smax, 0)} hojas`],
  ["Lugares en el almacén", "Pallets, estantes o cunas que ocupa el stock máximo", `${n(pe.smax, 0)} / ${n(pe.umpos, 0)} por lugar = ${n(pe.lugares, 1)}`],
]));
capturas(["G01"]);
hijos.push(nota("El stock baja a la velocidad de consumo; al tocar el punto de pedido se pide; mientras llega se consume lo que cubre el punto de pedido y, si todo va normal, el pedido llega cuando queda el stock de seguridad. El colchón sólo se usa si coinciden el mes pico y la demora máxima. Si un plazo no tiene rango (un solo valor) y el material no tiene mes pico (sólo recargas), el colchón da 0: aparece en cuanto el proveedor cotice el plazo con su rango."));
hijos.push(nota("Si el plazo es más largo que los días entre pedidos (casquetes importados, cuplas de Eli-Met), hay más de un pedido en camino: el punto de pedido se compara con el stock más lo pedido que todavía no llegó."));
hijos.push(h2("De dónde sale el plazo de entrega"));
const porFuente = new Map();
D.politica.forEach((x) => {
  const k = x.fuente.startsWith("Sin plazo") ? `${x.fuente}|${x.proveedor}` : x.fuente;
  if (!porFuente.has(k)) porFuente.set(k, { fuente: x.fuente, prov: x.proveedor, plazo: x.ltmin === x.ltmax ? `${x.ltmin}` : `${x.ltmin} a ${x.ltmax}`, fig: x.fig, cods: [] });
  porFuente.get(k).cods.push(x.codigo);
});
const conCot = [...porFuente.values()].filter((g) => !g.fuente.startsWith("Sin plazo"));
const sinCot = [...porFuente.values()].filter((g) => g.fuente.startsWith("Sin plazo"));
const rangoCods = (cods) => { const out = []; cods.forEach((c) => { const b = c.split("/")[0]; const prev = out.find((o) => o.b === b); if (prev && c.includes("/")) prev.n += 1; else out.push({ b, c, n: 1 }); }); return out.map((o) => (o.n > 1 ? `${o.b} (${o.n} medidas)` : o.c)).join(", "); };
hijos.push(nota("Primero las cotizaciones que traen plazo; después, el que publica en su web el proveedor o, si el elegido no lo publica, otro proveedor del mismo producto en el AMBA (W4 a W23, buscados el 12 y 13/10/2026). Días corridos → hábiles: × 5 / 7. El caño del 1 kg (MP-01) no usa la «entrega inmediata» de Comercial MID (Q04): cotizó Ø76 × 2,6 mm y el cuerpo es de 1,25 mm (planilla de MP).", { keepNext: true }));
hijos.push(...tabla([46, 10, 34, 10], ["Fuente del plazo", "Días hábiles", "Materiales", "Figura"],
  conCot.map((g) => [g.fuente, g.plazo, rangoCods(g.cods), g.fig])));
hijos.push(nota("Para el resto no hay plazo en ninguna cotización ni en la web del proveedor ni de otros del rubro en el AMBA (se buscaron en tres rondas: sitios, preguntas frecuentes, condiciones de envío y directorios de caños, ruedas, abrasivos, granalla, pintura en polvo industrial (Sinteplast, LAF, Interpon, Arnum-As), esmalte, agentes extintores, válvulas, manómetros, mangueras, tubos pescantes, conjuntos de seguridad, obleas, estampillas, tapones y matafuegos de reventa). Usan el plazo de la planilla de MP o del proceso de carros, sin rango, y hay que pedírselo a cada proveedor:", { keepNext: true }));
const provSin = new Map();
sinCot.forEach((g) => { const k = g.prov; if (!provSin.has(k)) provSin.set(k, { plazos: new Set(), cods: [] }); provSin.get(k).plazos.add(g.plazo); provSin.get(k).cods.push(...g.cods); });
const CONTACTO = {
  "Centrosider": "Alternativa: Hierros Torrent, 4555-6078 (vende el tubo de 1\" × 2 mm SAE 1010)",
  "Ruedar": "4442-4752 · ventas@ruedar.com.ar", "Escanort": "4795-0943",
  "Metalpri / Prilux": "Metalprisa / Prilux (CABA): cotizó el caño el 09/09/2026 sin plazo; publica stock permanente y entregas rápidas en CABA y GBA, sin días",
  "Alt. 1 Esinex (Billinghurst) / Alt. 2 Securitá": "Esinex: 1° Junta 5024, Billinghurst, 11 4563-9000 · esinex@esinex.com (W19) · Securitá: securitadistribuidora@gmail.com (W20)",
  "Alt. 1 Mozart (V. Alsina) / Alt. 2 Georgia (CABA)": "Mozart: Ucrania 1564, Valentín Alsina, 4218-3690 · info@mozartsrl.com.ar (W21) · Georgia: 4585-4400 · info@georgia.com.ar (W23)",
  "CyM Materiales": "11 3979-4111 · cymba@cym.com.ar",
  "Sinteplast": "11 6333-7400 (fabricante, planta de polvo en Tristán Suárez) · alternativa: Arnum-As (Haedo, distribuidor de polvo), 4659-4724", "DEMSA": "3489 495 000 · comercial@demsa.com.ar", "Polvex": "11 4405-3382",
  "Polvex / DEMSA": "11 4405-3382 · comercial@demsa.com.ar", "Polvex (HZ)": "11 4405-3382",
  "Yukon": "MatafuegosYa S.R.L. (Estomba 954), 4555-5100", "Georgia": "4585-4400 · info@georgia.com.ar",
  "DPS (PBA)": "Ministerio de Ambiente PBA (Res. 349/07)", "IRAM": "Perú 552, CABA · extintores.iram.org.ar",
  "A definir (inyectora)": "ACPLIND (Lerma 63, CABA), 4862-1323 · info@acplind.com",
  "Fabricante nacional": "Georgia 4585-4400 · Melisam 4766-6100 · Mozart (Lanús) 4218-3690",
};
hijos.push(...tabla([20, 9, 37, 34], ["Proveedor a consultar", "Plazo usado", "Materiales", "Contacto"],
  [...provSin.entries()].map(([k, v]) => [k, [...v.plazos].join(" / "), rangoCods(v.cods), CONTACTO[k] || ""])));
hijos.push(nota("La unidad de compra, su contenido, los días entre pedidos y cuánto entra en un lugar salen de la planilla de MP (X07, X07B); en los insumos de carros, de las unidades de entrega del proceso de carros (P07), y en los envases de recargas, de la lista de precios (Q07)."));
hijos.push(h2("Lugares por almacén"));
hijos.push(...tabla([50, 17, 17, 16], ["Almacén", "Lugares que ocupa el stock máximo", "Lugares que previó el proceso", "¿Alcanza?"],
  D.almacenes.map((a) => [a.almacen, a.pos, a.cap ?? "—", a.res || "Lo prevé el layout"]), { num: [1, 2] }));
capturas(["M07", "Q01", "Q03", "Q04", "X07", "X07B", "P06", "P07", "Q07", "M08"]);

// ------------------------------------------------------------------ 6. fuera del MRP
hijos.push(h1("6. Lo que no entra al MRP (se compra por punto de pedido)"));
hijos.push(...tabla([32, 68], ["Ítem", "Por qué"], [
  ["Puntas de contacto, disco flap de manuales", "Ningún proceso da su consumo (la planilla de MP lo marca estimado)."],
  ["Tapones de silicona del enmascarado", "Circulan entre pintura y carga: no se consumen por unidad."],
  ["Film, esquineros, funda de carros", "Los procesos no dan el consumo por pallet ni describen el embalaje del carro."],
  ["Repuestos de recargas", "Se cambian sólo si están dañados; el stock sale del registro de repuestos (R04)."],
  ["Fondo, lijas, cinta, desengrasante y placa de servicio (recargas)", "Se usan sólo donde hace falta."],
  ["Argón", "El agente limpio se presuriza con nitrógeno, que ya se compra (R10)."],
]));

// ------------------------------------------------------------------ 7. contraste
hijos.push(h1("7. Contraste con los procesos"));
hijos.push(...tabla([32, 11, 11, 10, 36], ["Dato (por día en el mes pico)", "MRP", "Proceso", "Dif.", "Fuente"],
  D.validacion.map((v) => [v.dato, n(v.mrp, 2), n(v.doc, 2), sg(v.dif), v.fuente]), { num: [1, 2, 3] }));
hijos.push(nota("Las diferencias grandes tienen causa: el proceso de manuales usa una producción del pico por modelo que suma 1.788 recipientes por día contra su propio total de 1.665; el polvo del MRP es la carga objetivo del BOM (nominal + mitad de la tolerancia); el proceso de carros supone 20 carros por día en el pico, y con la demanda de las Proyecciones son 14."));
capturas(["P09"]);

// ------------------------------------------------------------------ 8. pendientes
hijos.push(h1("8. Pendientes"));
[
  "Pedir el plazo de entrega, con su mínimo y máximo, a los proveedores sin plazo publicado (tabla de la sección 5), y confirmarlo a los que se tomó de otro proveedor del rubro (Vladimirsky, IndusPallets) o de una fuente antigua (Argensold, Maxiseguridad).",
  "Dimensionamiento Técnico FLAMA: la fila «TOTAL CARROS» se suma dos veces en las recargas (376.077 en lugar de 371.908). El MRP usa el Indexado.",
  "Proceso de manuales: la recepción dice 97 tubos por día; son 53 (1.216 tramos / 23).",
  "Dimensionamiento V2: el 10 % de CO₂ y agente limpio descargados y el 15 % que se pinta están marcados por ustedes «a validar» (X11).",
  "Confirmar con HZ que las válvulas M-30 y de carro se venden sin tubo pescante (la planilla de MP lo deja en dudas: «Materiales y útiles» dice que llegan armadas); si vienen con él, se sacan MP-46 y MP-47.",
  "BOM: el caño de pesca de los carros figura en PVC; la planilla de MP lo pide de acero SAE 1010 (MP-47).",
  "Cotizar el fleje de 1,25 × 135 mm del fondo del 1 kg (disco de 112 mm) y los revendidos.",
].forEach((x) => hijos.push(vin(x)));

// ------------------------------------------------------------------ 9. fuentes
hijos.push(h1("9. Fuentes"));
[
  "Procesos de manuales, de carros y de recargas; Proyecciones; Dimensionamiento Técnico FLAMA y V2; FLAMA_BOM.xlsx; planilla de MP y planilla Materias Primas; cotizaciones de Pradecon, Pacheco, Comercial MID, Air Liquide, Eli-Met, lista de precios de agentes y servicio de pintura de carros.",
  "W1 · Sinteplast, esmalte poliuretano industrial, ficha 356 (8,75 m²/L con 40 µm): https://www.sinteplast.com.ar/admin/uploaded/fichas-tecnicas/producto-sinteplast-ficha-tecnica-356-20220223111619.pdf",
  "W2 · WEG Politherm 66 (poliéster, 1,51 g/cm³, 9,46 m²/kg a 70 µm): https://static.weg.net/medias/downloadcenter/hc5/h8d/boletin-tecnico-10007312-politherm-66-w-eco-li-blanco-66450-br-es.pdf",
  "W3 · Products Finishing (Powder Coating Institute): 95 a 98 % de aprovechamiento con recuperación: https://pfonline.com/articles/hte-powder-coatings-take-coverage-to-the-next-level",
  "Plazos de entrega publicados (buscados el 12/10/2026):",
  "W4 · Metapol (CABA), acero SAE 1045: stock permanente en CABA de barras y planchuelas, entrega en 24 a 72 h en el AMBA: https://metapol.com.ar/productos/sae-1045.html",
  "W5 · Importa Fácil, importar de China a Argentina: 75 a 95 días desde la confirmación del pedido (navegación de 35 a 42 días + despacho y transporte interno): https://importa-facil.com.ar/cuanto-cuesta-importar-de-china-argentina",
  "W6 · Espacio Industria (Munro), distribuidor industrial: envío express con entrega en CABA y GBA en 24 h; vende discos de corte de 115 × 1 mm y mechas de acero rápido: https://espacio-industria.com/",
  "W7 · Rotolan (Lanús), etiquetas autoadhesivas en rollo: ancho de 20 a 210 mm, núcleo de 25, 40 o 76 mm, mínimo 500 u, entrega en 3 a 7 días hábiles: https://rotolan.com.ar/etiquetas-en-rollo.html. Entran las etiquetas del 1, 2,5 y 5 kg y las chicas; la del 10 kg (224 × 343 mm) y la de los carros (213 mm de alto) no.",
  "W8 · Papelera Damián (marca SonFuertes), entregas: reparto propio a localidades limítrofes de CABA en 3 a 5 días hábiles: https://papeleradamian.com/presta/content/delivery.html",
  "W9 · Sellerpack (Pompeya, CABA), fábrica de cajas desde 1934: producción de 10 a 15 días desde la aprobación de la prueba final; formatos con matriz existente, 3 a 5 días; troquel nuevo, +5 a 10 días: https://sellerpack.com.ar/industrias/construccion-industria/ y https://sellerpack.com.ar/cajas/exhibidor/",
  "W10 · Depallet, pallets de madera: entregas en un plazo estimado de 24 a 72 horas: https://depallet.com.ar/logistica/",
  "W11 · Würth Argentina, envíos: despacha al día hábil siguiente a la factura y entrega en hasta 5 días hábiles según el destino (unos 3 en CABA y AMBA); vende arandelas DIN 125, discos flap y O-rings métricos: https://www.wurth.com.ar/contenidos/preguntas-frecuentes/tiempos-de-entrega.html ; disco de corte de 355 × 3,5 × 25,4 mm: https://www.wurth.com.ar/es/tienda/corte-y-taladro/discos-de-corte/disco-de-corte-premium-355x3-5x25-4.html",
  "W12 · Soldanet, preguntas frecuentes: 4 a 5 días hábiles después de acreditado el pago; vende alambre MIG 70S6 de 15 kg: https://soldanet.com/preguntasfrecuentes",
  "W13 · Matafuegos Rodo: logística para entregar en 24/48 h y envío sin cargo en CABA y GBA (ABC, CO₂ 3,5 y 5 kg, K 6 l, HCFC 5 kg): https://www.matafuegosrodo.com/",
  "W14 · Argensold (Lomas del Mirador), O-rings: 10.000 productos en stock y entrega en 72 h a todo el país: https://www.facebook.com/people/Argensold-el-nombre-del-Oring/100091676384453/ ; 24 h según https://editores.com.ar/empresa/argensold",
  "W15 · Maxiseguridad (Munro): entrega a domicilio a las 48 h de pedido por la web: https://www.maxiseguridad.com.ar/detalle-noticias-maxiseguridad/169/Venta-y-Recarga-de-Matafuegos-en-Forma-Online",
  "W16 · RotulArte (CABA), impresión en vinilo autoadhesivo full color con laminado, hasta 155 cm de ancho: 24 a 48 h hábiles desde la aprobación del arte: https://rotularte.com.ar/impresion-vinilo-autoadhesivo/",
  "W17 · Todo Lanús, Formas Visuales (Lanús Oeste), imprenta digital y offset: entrega en 24 a 72 h: https://www.todolanus.com.ar/rubro/imprentas-talleres-graficos",
  "W18 · AGC, registro de fabricantes y recargadores: la empresa genera e imprime las tarjetas identificatorias en el sistema de la AGC con la boleta pagada: https://www.buenosaires.gob.ar/tramites/registro-de-fabricacion-reparacion-recarga-instalacion-y-control-de-extintores-matafuegos-y",
  "W19 · Esinex (Billinghurst), repuestos: tubos de pesca para matafuegos de 2,5, 5, 10 y 25 kg, con portacaño o filtro, para polvo, clase K y agua; no publica plazo: https://www.esinex.com.ar/product-page/tubo-de-pesca",
  "W20 · Securitá, distribuidora de seguridad industrial, repuestos: caños de pesca para matafuegos de 2,5, 5 y 10 kg; no publica plazo: http://www.securitá.com.ar/p/repuestos.html",
  "W21 · Matafuegos Mozart (Valentín Alsina, Lanús), fabricante de componentes, válvulas y matafuegos desde los años 70; su ABC lleva tubo de pesca de acero al carbono; no publica plazo: http://www.mozartsrl.com.ar/matafuegos-extintores-de-abc.htm",
  "W22 · Maxiseguridad (Munro), catálogo: agua 10 l, AFFF 10 l, rodante AFFF 50 l y CO₂ 2 kg: https://catalogo.maxiseguridad.com.ar/detalle-producto-maxiseguridad/8/Matafuego-a-base-de-Agua-10-Lts , https://control.maxiseguridad.com.ar/detalle-producto-maxiseguridad/90/Matafuego-a-base-de-espuma-AFFF-10-Lts , https://control.maxiseguridad.com.ar/detalle-producto-maxiseguridad/6/Matafuego-rodante-a-base-de-espuma-AFFF-50-Lts y https://control.maxiseguridad.com.ar/detalle-producto-maxiseguridad/611/Matafuego-a-base-de-CO2-2-Kg",
  "W23 · Matafuegos Georgia (La Paternal, CABA), venta mayorista; caño de pesca de acero al carbono en sus matafuegos de agua; no publica plazo: https://www.matafuegosgeorgia.com/prodcat/10-agua/",
].forEach((x) => hijos.push(vin(x)));

// ------------------------------------------------------------------ documento
const faltan = D.capturas.map((c) => c.id).filter((i) => !vistas.has(i));
if (faltan.length) console.log("capturas sin citar:", faltan.join(", "));
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
