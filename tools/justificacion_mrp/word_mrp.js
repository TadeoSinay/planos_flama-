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
// las capturas angostas van de a dos por fila; las anchas (tablas de 12 meses) van a todo el ancho
D.capturas.forEach((c) => { c.medio = c.id !== "G01" && c.w < 1300; });
// muestra, al final de cada sección, las capturas citadas que todavía no se vieron
function capturas(ids) {
  const nuevas = [...new Set(ids)].filter((i) => !vistas.has(i) && CAP[i])
    .sort((a, b) => Number(CAP[a].medio) - Number(CAP[b].medio));
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
// «Tubo pescante, ABC 2,5 kg», «…, ABC 5 kg» → «Tubo pescante (2,5 kg, 5 kg y 10 kg)»; los materiales se separan con «;»
const VARIANTE = [/^(.+?),? (?:ABC|carro) ([\d,]+ (?:kg|l))$/, /^(.+?) (M\d+|2½")$/, /^(Matafuego) (.+)$/];
function juntar(mats) {
  const orden = [], porBase = new Map();
  mats.forEach((x) => {
    const r = VARIANTE.map((re) => x.match(re)).find(Boolean);
    const base = r ? r[1] : x;
    if (!porBase.has(base)) { porBase.set(base, []); orden.push(base); }
    porBase.get(base).push(r ? r[2] : null);
  });
  const y = (v) => (v.length > 1 ? `${v.slice(0, -1).join(", ")} y ${v[v.length - 1]}` : v[0]);
  return orden.map((b) => { const v = porBase.get(b);
    return v.length === 1 ? (v[0] === null ? b : mats.find((x) => x.startsWith(b))) : `${b} (${y(v.filter(Boolean))})`; }).join("; ");
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
hijos.push(nota("Como el Dimensionamiento Técnico FLAMA: producción de cada mes de 2035 = demanda del año × perfil. El mes pico es el de mayor producción de la línea. Recargas: anual / 12. Revendidos: el perfil de su tamaño. Para comprar, cada producto usa su propio mes pico: el AFFF 50 l sigue el perfil industrial (pico de marzo a agosto, 37 por mes) y en diciembre, pico de los revendidos, vende 33, menos que su promedio de 35; con el pico de la línea su stock de seguridad daba negativo."));
hijos.push(nota("Corregido en los dos Dimensionamientos (FLAMA y V2): el total de recargas sumaba también la fila «TOTAL CARROS», que es el subtotal de los cuatro carros, y los contaba dos veces. Ahora esa fila se muestra pero no entra en el total: 2035 = 371.909 recargas, igual que el Indexado (371.908), y 127.339 en la planta industrial (10.612 por mes, F03). El MRP no cambia: toma las recargas del Indexado."));
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
  MANUALES: "Tubo pescante del 2,5, 5 y 10 kg (MP-46): PVC rígido, como el caño de pesca del BOM. Va por fuera de la válvula y se compra aparte; el del 1 kg viene con la válvula M-22. Es lo que pide la norma: IRAM 3523 3.5 sólo exige un tubo interior que la carga no ataque, sin fijar el material, y 4.4 un diámetro interior de 8 mm como mínimo. El PVC no se corroe con el polvo ABC, el tubo es corto y liviano, y el ensayo de vibraciones (4.8) se hace con el matafuego armado. Proveedores: Esinex (W19) y Securitá (W20).",
  RODANTES: "Tubo pescante de los carros (MP-47): acero SAE 1010, como pide la planilla de MP; va por fuera de la válvula y se compra aparte. IRAM 3550 3.6 pide lo mismo que la 3523 (un tubo que la carga no ataque) y el acero cumple: el polvo va seco con nitrógeno seco (3.9) y la norma acepta el recipiente de acero al carbono con recubrimiento sólo por fuera (3.2.1). Lo que decide es el ensayo de rodadura (4.10, método 7.9): el carro cargado se remolca 1 km, se deja caer 20 cm y se lo hace chocar contra una pared, no se puede romper ninguna parte y después tiene que descargar como pide 4.11. Un tubo largo de PVC rígido, dentro de 25 a 100 kg de polvo, se puede fisurar o soltar de la rosca con esos golpes; el de acero no. Por eso el BOM y los planos de los carros quedaron en acero. Proveedores: Mozart (W21) y Georgia (W23), que lo usan de acero al carbono.",
  RECARGAS: "Sin soldadura: un recipiente que se recarga no se suelda. Los repuestos (válvula, manómetro, manguera) no entran: se cambian si están dañados y su stock sale del registro de repuestos (R04).",
};
LIN.forEach((l) => {
  const L_ = D.lineas[l];
  hijos.push(h2(TIT[l]));
  if (INTRO[l]) hijos.push(nota(INTRO[l]));
  const gs = grupos(L_.filas);
  hijos.push(...tabla([11, 29, 48, 12], ["Ref.", "Material", "Cómo se calcula", "Figura"],
    gs.map((g) => [rango(g.refs), juntar(g.mats), g.como, fg(g.figs)])));
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
hijos.push(nota("Primero las cotizaciones que traen plazo; después, el que publica en su web el proveedor o, si el elegido no lo publica, el de otro vendedor del mismo producto o rubro en el país, primero en PBA (W4 a W35, buscados del 12 al 13/10/2026). Ese plazo va marcado «≈» (aproximado): aproxima el del proveedor directo para justificar la política y se confirma al cotizarle. El link y el detalle de cada fuente están en el Excel (POLITICA_STOCK, columna «De dónde sale el plazo»). Días corridos → hábiles: × 5 / 7. El caño del 1 kg (MP-01) no usa la «entrega inmediata» de Comercial MID: cotizó Ø76 × 2,6 mm y el cuerpo es de 1,25 mm (planilla de MP).", { keepNext: true }));
const NOMBRE_W = { W4: "Metapol (CABA)", W5: "Importa Fácil (China)", W6: "Espacio Industria (Munro)", W7: "Rotolan (Lanús)",
  W8: "Papelera Damián", W9: "Sellerpack (Pompeya)", W10: "Depallet", W11: "Würth Argentina", W12: "Soldanet",
  W13: "Matafuegos Rodo", W14: "Würth Argentina", W15: "Matafuegos Aconcagua (J. C. Paz)", W16: "RotulArte (CABA)",
  W17: "Formas Visuales (Lanús)", W18: "Trámite AGC", W24: "Grupo Oxicas (Santa Fe)", W25: "Vernassa (CABA)",
  W26: "Matafuegos Aconcagua (J. C. Paz)", W27: "El Galpón (Corrientes)", W28: "AcerosYa (Sarandí)", W29: "Morshop",
  W30: "EGM Trader (Florida)", W31: "Enamels (Lanús)", W32: "Pinturerías Mafer", W33: "Trámite DPS (Res. 349/07)",
  W34: "IRAM (DC-PG-129)", W35: "Martin Morris (Coronel Suárez)" };
const mayus = (x) => x.charAt(0).toUpperCase() + x.slice(1);
const corta = (g) => (g.fuente.startsWith("Aproximado") ? "≈ " : "") +
  mayus(NOMBRE_W[g.fig] || g.fuente.replace(/^Aproximado:\s*/, "").split(/[:(]/)[0].trim());
const filasLT = new Map();
conCot.forEach((g) => {
  const k = `${corta(g)}|${g.plazo}`;
  if (!filasLT.has(k)) filasLT.set(k, { f: corta(g), plazo: g.plazo, figs: [], cods: [] });
  const r = filasLT.get(k);
  if (g.fig && !r.figs.includes(g.fig)) r.figs.push(g.fig);
  r.cods.push(...g.cods);
});
hijos.push(...tabla([36, 10, 54], ["Fuente (≈ aproximado al proveedor directo; W = link en el Excel)", "Días hábiles", "Materiales"],
  [...filasLT.values()].map((g) => { const w = g.figs.filter((x) => x.startsWith("W")).sort((a, b) => a.slice(1) - b.slice(1));
    return [w.length ? `${g.f} (${w.join(", ")})` : g.f, g.plazo, rangoCods(g.cods)]; })));
hijos.push(nota(sinCot.length ? "Para el resto no hay plazo en ninguna cotización ni en la web del proveedor ni de otros del rubro en el país: usan el plazo de la planilla de MP o del proceso de carros, sin rango, y hay que pedírselo a cada proveedor. Los marcados «≈» se confirman con el proveedor directo:" : "Todos los materiales tienen plazo con fuente (se buscaron en seis rondas, primero en PBA y después en otras provincias: sitios, preguntas frecuentes, condiciones de envío, términos y condiciones y directorios; los pliegos de compras públicas no sirven porque traen el plazo que exige el comprador). Los marcados «≈» salen de otro vendedor del mismo producto o rubro y se confirman con el proveedor directo al cotizarle:", { keepNext: true }));
const aConfirmar = new Map();
D.politica.filter((x) => x.fuente.startsWith("Aproximado") || x.fuente.startsWith("Sin plazo")).forEach((x) => {
  const k = x.proveedor;
  if (!aConfirmar.has(k)) aConfirmar.set(k, { plazos: new Set(), cods: [] });
  aConfirmar.get(k).plazos.add(x.ltmin === x.ltmax ? `${x.ltmin}` : `${x.ltmin} a ${x.ltmax}`);
  aConfirmar.get(k).cods.push(x.codigo);
});
const CONTACTO = {
  "Centrosider": "Alternativa: Hierros Torrent, 4555-6078 (vende el tubo de 1\" × 2 mm SAE 1010)",
  "Ruedar": "4442-4752 · ventas@ruedar.com.ar · alternativa: Ruedas Hofer (Haedo), rueda Ø300 × 50, eje 3/4\", 220 kg (cód. 10300), 4443-1439 · contacto@ruedashofer.com.ar", "Escanort": "4795-0943",
  "Metalpri / Prilux": "Metalprisa / Prilux (CABA): cotizó el caño el 09/09/2026 sin plazo; publica stock permanente y entregas rápidas en CABA y GBA, sin días",
  "Alt. 1 Esinex (Billinghurst) / Alt. 2 Securitá": "Esinex: 1° Junta 5024, Billinghurst, 11 4563-9000 · esinex@esinex.com (W19) · Securitá: securitadistribuidora@gmail.com (W20)",
  "Alt. 1 Mozart (V. Alsina) / Alt. 2 Georgia (CABA)": "Mozart: Ucrania 1564, Valentín Alsina, 4218-3690 · info@mozartsrl.com.ar (W21) · Georgia: 4585-4400 · info@georgia.com.ar (W23)",
  "CyM Materiales": "11 3979-4111 · cymba@cym.com.ar · alternativa: Granalladora Americana (Florida, PBA), fabricante, bolsa de 25 kg",
  "Sinteplast": "11 6333-7400 (fabricante, planta de polvo en Tristán Suárez) · alternativa: Arnum-As (Haedo, distribuidor de polvo), 4659-4724", "DEMSA": "3489 495 000 · comercial@demsa.com.ar", "Polvex": "11 4405-3382",
  "Polvex / DEMSA": "11 4405-3382 · comercial@demsa.com.ar", "Polvex (HZ)": "11 4405-3382 · alternativas que publican la válvula: Melisam (válvulas completas de 1 a 10 kg), ventas@extintoresmelisam.com.ar; Securitá (M-30 de 2,5 a 25 kg)",
  "Yukon": "MatafuegosYa S.R.L. (Estomba 954), 4555-5100 · alternativas: Melisam (manómetros); El Galpón (Corrientes), manómetro de 1,4 MPa y manguera de 5 kg, envía por Correo Argentino sin días publicados", "Georgia": "4585-4400 · info@georgia.com.ar",
  "DPS (PBA)": "Ministerio de Ambiente PBA (Res. 349/07)", "IRAM": "Perú 552, CABA · extintores.iram.org.ar",
  "ACPLIND (CABA)": "Lerma 63, CABA, 4862-1323 · info@acplind.com: 500.000 protectores de rosca hembra GAS, BSP y NPT en stock, en 300 medidas",
  "Pradecon": "Cotización 173195",
  "IndusPallets": "No publica plazo; alternativa: Depallet (W10), entrega en 24 a 72 h",
  "Argensold": "Av. J. M. de Rosas 698, Lomas del Mirador, 4699-3788 · ventas@argensold.com",
  "Maxiseguridad (Munro)": "Vélez Sarsfield 5263, Munro, 11 5365-8811 · comercial@maxiseguridad.com.ar", "Pacheco Chapas": "Cotizó el fleje sin plazo (Q02)",
  "Importado (China)": "Despachante de aduana / importador", "Vladimirsky": "Distribuidor de barras SAE 1045",
  "Fabricante nacional": "Georgia 4585-4400 · Melisam 4766-6100 · Mozart (Lanús) 4218-3690",
};
hijos.push(...tabla([20, 9, 37, 34], ["Proveedor directo a confirmar", "Plazo usado", "Materiales", "Contacto"],
  [...aConfirmar.entries()].map(([k, v]) => [k, [...v.plazos].join(" / "), rangoCods(v.cods), CONTACTO[k] || ""])));
hijos.push(nota("La unidad de compra, su contenido, los días entre pedidos y cuánto entra en un lugar salen de la planilla de MP (X07); en los insumos de carros, de las unidades de entrega del proceso de carros, y en los envases de recargas, de la lista de precios de agentes."));
hijos.push(h2("Lugares por almacén"));
hijos.push(...tabla([50, 17, 17, 16], ["Almacén", "Lugares que ocupa el stock máximo", "Lugares que previó el proceso", "¿Alcanza?"],
  D.almacenes.map((a) => [a.almacen, a.pos, a.cap ?? "—", a.res || "Lo prevé el layout"]), { num: [1, 2] }));

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
  "Confirmar con cada proveedor directo los plazos marcados «≈» («Aproximado» en el Excel: tomados de otro vendedor del mismo producto o rubro) ; confirmar con ACPLIND el de los tapones; las estampillas IRAM se piden con 30 días de anticipación.",
  "Proceso de manuales: la recepción dice 97 tubos por día; son 53 (1.216 tramos / 23).",
  "Dimensionamiento V2: el 10 % de CO₂ y agente limpio descargados y el 15 % que se pinta están marcados por ustedes «a validar» (X11).",
  "Proceso de recargas, Pintura: dice «esmalte poliuretano rojo brillante» y respirador para isocianatos; la planilla de MP pide esmalte sintético rojo RAL 3000 (X15), que es el que usa el MRP.",
  "Cotizar el fleje de 1,25 × 135 mm del fondo del 1 kg (disco de 112 mm) y los revendidos.",
].forEach((x) => hijos.push(vin(x)));

// ------------------------------------------------------------------ 9. fuentes
hijos.push(h1("9. Fuentes"));
[
  "Procesos de manuales, de carros y de recargas; Proyecciones; Dimensionamiento Técnico FLAMA y V2; FLAMA_BOM.xlsx; planilla de MP y planilla Materias Primas; cotizaciones de Pradecon, Pacheco, Comercial MID, Air Liquide, Eli-Met, lista de precios de agentes y servicio de pintura de carros.",
  "W1 · Sinteplast, Sintesmal, esmalte sintético industrial, ficha 741 (8,8 m²/L con 40 µm secos): https://www.sinteplast.com.ar/admin/uploaded/fichas-tecnicas/producto-sinteplast-ficha-tecnica-741-20220217112543.pdf",
  "W2 · WEG Politherm 66 (poliéster, 1,51 g/cm³, 9,46 m²/kg a 70 µm): https://static.weg.net/medias/downloadcenter/hc5/h8d/boletin-tecnico-10007312-politherm-66-w-eco-li-blanco-66450-br-es.pdf",
  "W3 · Products Finishing (Powder Coating Institute): 95 a 98 % de aprovechamiento con recuperación: https://pfonline.com/articles/hte-powder-coatings-take-coverage-to-the-next-level",
  "Fuentes de los plazos de entrega (W4 a W18 y W24 a W35, buscadas del 12 al 13/10/2026): el link de cada una está en el Excel, hoja POLITICA_STOCK, columna «De dónde sale el plazo», con el texto completo en el comentario de la celda. Otras fuentes web:",
  "W19 · Esinex (Billinghurst), repuestos: tubos de pesca para matafuegos de 2,5, 5, 10 y 25 kg, con portacaño o filtro, para polvo, clase K y agua; no publica plazo: https://www.esinex.com.ar/product-page/tubo-de-pesca",
  "W20 · Securitá, distribuidora de seguridad industrial, repuestos: caños de pesca para matafuegos de 2,5, 5 y 10 kg; no publica plazo: http://www.securitá.com.ar/p/repuestos.html",
  "W21 · Matafuegos Mozart (Valentín Alsina, Lanús), fabricante de componentes, válvulas y matafuegos desde los años 70; su ABC lleva tubo de pesca de acero al carbono; no publica plazo: http://www.mozartsrl.com.ar/matafuegos-extintores-de-abc.htm",
  "W22 · Maxiseguridad (Munro), catálogo: agua 10 l, AFFF 10 l, rodante AFFF 50 l y CO₂ 2 kg: https://catalogo.maxiseguridad.com.ar/detalle-producto-maxiseguridad/8/Matafuego-a-base-de-Agua-10-Lts , https://control.maxiseguridad.com.ar/detalle-producto-maxiseguridad/90/Matafuego-a-base-de-espuma-AFFF-10-Lts , https://control.maxiseguridad.com.ar/detalle-producto-maxiseguridad/6/Matafuego-rodante-a-base-de-espuma-AFFF-50-Lts y https://control.maxiseguridad.com.ar/detalle-producto-maxiseguridad/611/Matafuego-a-base-de-CO2-2-Kg ; BC 5 kg (Monnex): https://catalogo.maxiseguridad.com.ar/detalle-producto-maxiseguridad/63/Matafuego-Monnex-BC-5-Kg",
  "W23 · Matafuegos Georgia (La Paternal, CABA), venta mayorista; caño de pesca de acero al carbono en sus matafuegos de agua; no publica plazo: https://www.matafuegosgeorgia.com/prodcat/10-agua/",
].forEach((x) => hijos.push(p([t(x, { size: 14 })], { after: 20 })));

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
