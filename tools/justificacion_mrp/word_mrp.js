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
// muestra, al final de cada sección, las capturas citadas que todavía no se vieron
function capturas(ids) {
  const nuevas = [...new Set(ids)].filter((i) => !vistas.has(i) && CAP[i]);
  nuevas.forEach((i) => vistas.add(i));
  if (nuevas.length) hijos.push(...figs(nuevas));
}
const fg = (ids) => (ids || []).filter((i) => CAP[i] || i.startsWith("W")).join(", ");
const corto = (x) => String(x).replace("Recarga ", "").replace("Cilindro ABC ", "cil. ").replace(" vacío", "")
  .replace("Matafuego ", "").replace("ABC ", "").replace("Sustituto nuevo (kit)", "kit");
// consumo por unidad: agrupa los productos que tienen el mismo valor
function consumo(c, prods, um) {
  const g = new Map();
  Object.entries(c).forEach(([k, v]) => { const key = `${n(v, 4)} ${um}`; g.set(key, [...(g.get(key) || []), k]); });
  const sinKit = prods.filter((x) => !x.startsWith("Sustituto"));
  if (g.size === 1 && Object.keys(c).length === prods.length) return `${[...g.keys()][0]} en todos`;
  if (g.size === 1 && sinKit.length < prods.length && sinKit.every((x) => x in c)) return `${[...g.keys()][0]} en todas las recargas`;
  const resto = sinKit.filter((x) => !(x in c));
  const largo = (ks) => ks.length > 8 && sinKit.length < prods.length;
  return [...g.entries()].map(([v, ks]) => largo(ks) ? `${v} en las demás recargas` : `${v}: ${ks.map(corto).join(", ")}`).join(" · ") +
    ([...g.values()].some(largo) && resto.length ? ` · nada: ${resto.map(corto).join(", ")}` : "");
}

// ------------------------------------------------------------------ portada
hijos.push(new Paragraph({ spacing: { after: 60 }, children: [new TextRun({ text: "Justificación del MRP", font: FONT, size: 40, bold: true })] }));
hijos.push(p([t("FLAMA S.A. · de dónde sale cada valor de FLAMA_MRP.xlsx · octubre de 2026", { size: 18, color: GRIS_O })], { after: 160 }));
[
  "El MRP hace una sola cuenta: lo que hay que comprar de cada material = consumo por unidad de producto × unidades a producir. La suma de las cuatro líneas (manuales, rodantes, recargas de la planta industrial y revendidos) da lo que se compra por año, de 2026 a 2035, y con el mes pico de 2035 se arma la política de stock.",
  "No hay supuestos: cada valor sale de los procesos de manuales, carros y recargas, del BOM, de las Proyecciones, de los dos Dimensionamientos, de la planilla de MP, de una cotización o de una ficha técnica. Lo que no tiene un consumo documentado no entra al MRP y se compra por punto de pedido (sección 7).",
  "El Excel tiene sólo números y fórmulas. Cada fila lleva un código en la columna «Ref.»; en este documento está ese código con de dónde sale el valor y la figura donde se ve. Figuras: P = proceso de manuales o carros, R = proceso de recargas, D = Dimensionamiento Técnico FLAMA, X = otras planillas (Proyecciones, Dimensionamiento V2, planilla de MP), B = BOM, Q = cotización, M = el propio MRP. El dato que se toma está marcado en rojo.",
].forEach((x) => hijos.push(vin(x)));
hijos.push(...tabla([20, 58, 22], ["Hoja", "Qué tiene", "Ref."], [
  ["DEMANDA", "Unidades por año de cada producto. Las recargas son las de la planta industrial.", "D01 a D47"],
  ["ESTACIONALIDAD", "Perfiles y producción mensual de 2035, como el Dimensionamiento Técnico FLAMA; mes pico y factor de pico de cada línea.", "E01 a E08"],
  ["MANUALES, RODANTES, RECARGAS, REVENDIDOS", "Arriba la demanda de cada producto; abajo el consumo por unidad de cada material (una columna por producto); a la derecha lo que hay que comprar por año y en el mes pico.", "M, R, K y V"],
  ["CONSOLIDADO", "Una fila por material: la suma de las cuatro líneas.", "—"],
  ["POLITICA_STOCK", "Año 2035: demanda de diseño, stock de seguridad, punto de pedido, lote, stock máximo y posiciones por almacén.", "P00 a P115"],
  ["PROY_INDEXADO, PROY_RESERVAS", "Copias de las hojas de las Proyecciones: si se pegan valores nuevos, todo se recalcula.", "—"],
]));

// ------------------------------------------------------------------ 1. cómo se lee
hijos.push(h1("1. Cómo se lee: el ABC 5 kg como ejemplo"));
const M = D.lineas.MANUALES;
const k5 = M.productos.indexOf("ABC 5 kg");
const d5 = M.demanda35[k5];
const ej = ["MP-03", "MP-07", "MP-08", "MP-33", "MP-43", "MP-28"].map((c) => M.filas.find((f) => f.codigo === c));
hijos.push(nota(`En 2035 se fabrican ${n(d5, 0)} matafuegos ABC 5 kg (D07). Lo que hay que comprar para ellos es el consumo por unidad × ${n(d5, 0)}:`, { keepNext: true }));
hijos.push(...tabla([10, 34, 16, 18, 22], ["Ref.", "Material", "Por matafuego", `× ${n(d5, 0)} =`, "De dónde sale"],
  ej.map((f) => [f.ref, f.material, `${n(f.cons["ABC 5 kg"], 4)} ${f.um}`, `${n(f.cons["ABC 5 kg"] * d5, 0)} ${f.um}`,
    f.como.split(";")[0].split(". ")[0].replace(/\.+$/, "") + "."]), { num: [2, 3] }));
hijos.push(nota("La hoja MANUALES hace esa cuenta para los 8 productos de la línea y para los 10 años con SUMAPRODUCTO: la fila del material por la fila de demanda del año. La columna «Mes pico 2035» usa la producción del mes pico (ESTACIONALIDAD) y alimenta la política de stock."));
capturas(["M03"]);

// ------------------------------------------------------------------ 2. demanda
hijos.push(h1("2. Demanda"));
hijos.push(nota("Todo sale de las Proyecciones (Indexado Dim Técnico y Reservas y Sustitutos). Las recargas son sólo las de la planta industrial: las 4 zonas que atiende (CABA Sur y PBA Sur 1.º, 2.º y 3.er cordón), el 34,2 % del mercado, como en el Dimensionamiento Técnico FLAMA. El proceso de recargas lo confirma: 13 recargas de BC por mes en la planta industrial, y el MRP da 14. Un sustituto nuevo ABC es un matafuego que fabrica FLAMA, así que se suma a manuales o rodantes; los de otros tipos se compran y se suman a revendidos. En recargas queda la recarga anual del pool y el kit de identificación del sustituto."));
hijos.push(...tabla([7, 30, 10, 10, 10, 33], ["Ref.", "Dato", "2026", "2030", "2035", "De dónde sale (figura)"],
  D.demanda.map((x) => {
    const pct = x.v35 !== null && x.v35 < 1;
    const f = (v) => pct ? pc(v, 1) : n(v, 0);
    return [x.ref, x.producto, f(x.v26), f(x.v30), f(x.v35), `${x.como} (${fg(x.figs)})`];
  }), { num: [2, 3, 4] }));
capturas(["X01", "X02", "X03", "X04", "D01", "X13"]);

// ------------------------------------------------------------------ 3. estacionalidad
hijos.push(h1("3. Estacionalidad"));
hijos.push(nota("Igual que el Dimensionamiento Técnico FLAMA: la producción de cada mes de 2035 es la demanda anual × el perfil de su tipo, y el mes pico es el de mayor producción de la línea. Los perfiles son los del Dimensionamiento; las recargas van parejas en los 12 meses (anual / 12), como en ese archivo. Los revendidos toman el perfil de su tamaño: manual comercial, y el AFFF 50 l el industrial sobre ruedas."));
hijos.push(...tabla([7, 27, ...Array(12).fill(5.5)], ["Ref.", "Perfil", "E", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"],
  D.perfiles.map((x) => [x.ref, x.nombre, ...x.meses.map((v) => pc(v, 1))]), { num: [...Array(12).keys()].map((i) => i + 2) }));
hijos.push(...tabla([7, 14, 10, 14, 14, 11, 30], ["Ref.", "Línea", "Mes pico", "Unidades del mes pico", "Promedio mensual", "Factor de pico", "Comentario"],
  LIN.map((l) => { const x = D.picos[l]; return [x.ref, l, x.mes, n(x.unidades, 0), n(x.promedio, 0), n(x.factor, 3),
    l === "MANUALES" ? "El proceso de manuales da 1.665 / 1.184 = 1,406" : l === "RODANTES" ? "El proceso de carros supone 1,43 (promedio = 70 % del pico)" :
    l === "RECARGAS" ? "Sin estacionalidad (Dimensionamiento FLAMA)" : ""]; }), { num: [3, 4, 5] }));
capturas(["D02", "D03", "D04"]);

// ------------------------------------------------------------------ 4. consumo por unidad
hijos.push(h1("4. Consumo por unidad"));
hijos.push(nota("Para cada línea: el consumo de cada material por unidad de producto (agrupado por valor: «0,0833: 5 kg, cil. 5 kg» quiere decir 0,0833 por matafuego de 5 kg y por cilindro de 5 kg), lo que hay que comprar en 2035 y de dónde sale. «Destino» CABA o PBA: el consumo se multiplica por el % de unidades que va a esa jurisdicción (D02 y D03)."));
const TIT = {
  MANUALES: "4.1 Manuales (ABC 1 a 10 kg y sus cilindros vacíos)",
  RODANTES: "4.2 Rodantes (ABC 25 a 100 kg y sus cilindros vacíos)",
  RECARGAS: "4.3 Recargas de la planta industrial (17 tipos y el kit del sustituto)",
  REVENDIDOS: "4.4 Revendidos",
};
const INTRO = {
  MANUALES: "Acero: cuerpos por hoja o por caño del proceso de manuales y kg de fleje por disco con el método de la planilla de MP. Soldadura, granalla, nitrógeno y embalaje: proceso de manuales; pintura: ficha del polvo. Válvula, manguera, manómetro, soportes e identificación: una por unidad según el BOM.",
  RODANTES: "Todo sale del proceso de carros: planes de corte (hoja mixta de 4,75 mm), casquetes y cuplas, cortes de caño y barra, gas y alambre puesto por puesto, discos y mechas. Las piezas de chapa del carro salen de las orillas del corte (sin compra). La pintura se terceriza (servicio por unidad).",
  RECARGAS: "Sin soldadura: un recipiente que se recarga no se suelda. Todo sale del proceso de recargas y de los parámetros de recargas del Dimensionamiento V2. Los repuestos (válvula, manómetro, manguera) no entran: se cambian si están dañados y su stock sale del registro de repuestos (R04).",
  REVENDIDOS: "Se compra el equipo terminado; FLAMA agrega la tarjeta AGC a los que van a CABA.",
};
LIN.forEach((l) => {
  const L_ = D.lineas[l];
  hijos.push(h2(TIT[l]));
  hijos.push(nota(INTRO[l]));
  hijos.push(...tabla([6, 9, 22, 26, 9, 28], ["Ref.", "Código", "Material", "Consumo por unidad", "2035", "De dónde sale (figura)"],
    L_.filas.map((f) => [f.ref, f.codigo, f.material + (f.destino ? ` (sólo ${f.destino})` : ""), consumo(f.cons, L_.productos, f.um),
      n(f.v35, 0), `${f.como} (${fg(f.figs)})`]), { num: [4] }));
  capturas([...(l === "RECARGAS" ? ["R01"] : []), ...L_.filas.flatMap((f) => f.figs)]);
});

// ------------------------------------------------------------------ 5. contraste
hijos.push(h1("5. Contraste con los procesos"));
hijos.push(nota("Consumo del MRP en el mes pico de 2035 (por día = mes pico / 20) contra el número que da cada proceso."));
hijos.push(...tabla([30, 11, 11, 10, 38], ["Dato", "MRP", "Proceso", "Dif.", "Fuente"],
  D.validacion.map((v) => [v.dato, n(v.mrp, 2), n(v.doc, 2), sg(v.dif), v.fuente]), { num: [1, 2, 3] }));
[
  "Caños, granalla, nitrógeno, recipientes por día, factor de pico y hojas de 4,75 mm coinciden (menos de 3 % de diferencia).",
  "Hojas de 1,6 mm y gas de manuales: el proceso usa la producción del pico por modelo (1.216 + 99 + 446 + 27 = 1.788 recipientes por día), que no cierra con su propio total de 1.665; el MRP usa el perfil de cada modelo del Dimensionamiento, que da 1.674 por día en total.",
  "Polvo de manuales: el MRP carga la carga objetivo del BOM (nominal + mitad de la tolerancia, 5,15 kg en el 5 kg); el proceso cuenta la nominal.",
  "Carros: el proceso supone 20 carros por día en el pico (promedio = 70 % del pico); con la demanda de las Proyecciones son 14, y el polvo baja en la misma proporción.",
].forEach((x) => hijos.push(vin(x)));
capturas(["P09"]);

// ------------------------------------------------------------------ 6. política
hijos.push(h1("6. Política de stock del año 2035"));
hijos.push(nota(`${D.p00.como} (${fg(D.p00.figs)})`));
hijos.push(nota("Lead time, días entre pedidos (T), stock de seguridad en días y lugar por posición son los de la planilla de MP («MP Abastecimiento»); cuando una cotización o un proceso da el mismo dato, se cita también. La unidad de compra sale del proceso o de la cotización cuando la traen. Los ítems que la planilla no tiene toman los valores de su misma familia (por ejemplo, las etiquetas y tarjetas los de MP-56 a MP-58)."));
const FAM = (x) => x.plan === x.codigo || x.codigo.startsWith(x.plan) ? x.plan : `${x.plan} (misma familia)`;
hijos.push(...tabla([6, 10, 18, 8, 13, 8, 8, 8, 8, 7, 6], ["Ref.", "Código", "Unidad de compra (fig.)", "LT (días)", "LT, T y SS de", "SS (días)", "T (días)", "Punto de pedido", "Stock máx.", "Lote (UC)", "Posic."],
  D.politica.map((x) => [x.ref, x.codigo, `${x.uc} (${x.fuc})`, `${x.lt}${x.flt ? " (" + x.flt + ")" : ""}`, FAM(x), x.ssd, x.t, n(x.pp, 0), n(x.smax, 0), x.lote, n(x.pos, 2)]),
  { num: [3, 5, 6, 7, 8, 9, 10] }));
hijos.push(h2("Posiciones por almacén"));
hijos.push(...tabla([46, 18, 18, 18], ["Almacén", "Posiciones requeridas", "Capacidad del proceso", "Resultado"],
  D.almacenes.map((a) => [a.almacen, a.pos, a.cap ?? "—", a.res || "Lo prevé el layout"]), { num: [1, 2] }));
hijos.push(nota("La calle de chapa y el rack de casquetes y cuplas de carros alcanzan. Al rack de insumos de montaje de carros le falta 1 posición (las ruedas vienen en pallets de 36 pares, planilla de MP): hay que sumar un módulo o pedir las ruedas en pallets más chicos."));
capturas(["X07", "X07B", "P06", "P07", "Q01", "Q02", "Q03", "Q04", "Q07", "M08"]);

// ------------------------------------------------------------------ 7. fuera del MRP
hijos.push(h1("7. Lo que no entra al MRP (se compra por punto de pedido)"));
hijos.push(...tabla([30, 70], ["Ítem", "Por qué no entra"], [
  ["Puntas de contacto y toberas MAG", "Ningún proceso da su consumo; la planilla de MP lo marca estimado (4 kg de alambre por punta)."],
  ["Disco flap de manuales", "El proceso de manuales nombra la amoladora con disco flap para corregir defectos, pero no da cuántos recipientes hace un disco."],
  ["Tapones de silicona del enmascarado", "Circulan entre la pintura y la carga (proceso de manuales): no se consumen por unidad."],
  ["Film stretch, esquineros y funda de carros", "El proceso de manuales nombra la envolvedora EDOS PS 5 pero no da el film por pallet (el folleto tampoco); el proceso de carros no describe el embalaje del carro."],
  ["Repuestos de recargas (válvula, manómetro, tubo sifón, manguera)", "Se cambian sólo si están dañados; el proceso de recargas dice que el stock de repuestos sale del registro que se lleva por orden de trabajo (R04)."],
  ["Fondo anticorrosivo, lijas, cinta, desengrasante y placa de servicio (recargas)", "Se usan sólo donde hace falta (metal a la vista, placa ilegible): no hay consumo por unidad."],
  ["Argón", "El proceso de recargas permite presurizar el agente limpio con nitrógeno o argón (R10): se usa nitrógeno, que ya se compra."],
  ["Agua de red", "Agua de los extintores de agua y de la prueba hidráulica (circuito cerrado): no es una compra de materia prima."],
]));

// ------------------------------------------------------------------ 8. observaciones
hijos.push(h1("8. Observaciones y pendientes"));
[
  "Dimensionamiento Técnico FLAMA: la fila «TOTAL CARROS» está dentro de las recargas y se suma dos veces (376.077 recargas en 2035 en lugar de 371.908). El MRP usa el Indexado, que no la tiene.",
  "Proceso de manuales: la recepción dice 97 tubos por día; con 1.216 tramos y 23 por caño son 53 (P01 y P03).",
  "Dimensionamiento V2: el 10 % de CO₂ y agente limpio que llegan descargados y el 15 % que se pinta están marcados por ustedes como «a validar» (X11).",
  "Fleje de 1,25 mm para el fondo del 1 kg: el disco es de 112 mm (planilla Materias Primas); la planilla de MP todavía tiene 0,9 × 106 mm. Hay que cotizarlo (135 mm de ancho).",
  "Revendidos: no hay cotización de los fabricantes; el lead time es el de los componentes armados de la planilla (20 días) hasta que se coticen.",
  "Casquetes: 60 días de lead time por ser importados; cotizar Gockel (nacional) para bajarlo.",
].forEach((x) => hijos.push(vin(x)));

// ------------------------------------------------------------------ 9. fuentes
hijos.push(h1("9. Fuentes"));
[
  "Procesos de FLAMA: fabricación de manuales, fabricación de carros y proceso de recargas (manual explicativo con videos).",
  "Proyecciones (versión 7): Indexado Dim Técnico, Reservas y Sustitutos y hojas de proyección por segmento.",
  "Dimensionamiento Técnico FLAMA (DATOS-BASE) y Dimensionamiento Técnico V2 (Parametros Recargas y Almacen PT).",
  "FLAMA_BOM.xlsx (MODELOS, Fabricados, Cilindros, Revendidos y Recargas).",
  "Planilla de MP «MP_Abastecimiento» (opción D) y planilla «Materias Primas» de la investigación de proveedores.",
  "Cotizaciones: Pradecon, Pacheco Chapas, Comercial MID, Air Liquide y Eli-Met (WhatsApp), lista de precios de agentes y válvulas, servicio de pintura de carros.",
  "W1 · Sinteplast, Esmalte Poliuretano Industrial, ficha técnica 356: 8,75 m² por litro con 40 µm secos. https://www.sinteplast.com.ar/admin/uploaded/fichas-tecnicas/producto-sinteplast-ficha-tecnica-356-20220223111619.pdf",
  "W2 · WEG, Politherm 66 W-ECO (poliéster), boletín técnico 10007312: densidad 1,51 g/cm³, rendimiento 9,46 m²/kg a 70 µm. https://static.weg.net/medias/downloadcenter/hc5/h8d/boletin-tecnico-10007312-politherm-66-w-eco-li-blanco-66450-br-es.pdf",
  "W3 · Products Finishing, citando al Powder Coating Institute: 95 a 98 % de aprovechamiento del polvo con recuperación. https://pfonline.com/articles/hte-powder-coatings-take-coverage-to-the-next-level",
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
