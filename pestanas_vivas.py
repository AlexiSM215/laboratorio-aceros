"""Pestañas Propiedades, Datos reales, Resistencia vs ductilidad y Diseño inverso en tiempo real.

Todo se calcula y dibuja en el navegador (gráficas SVG propias), así que se
actualiza al instante mientras se arrastran los deslizadores, sin esperar al
servidor. Las rectas y los datos son los mismos que calcula `analisis.py`.
"""
import numpy as np
import streamlit as st

import analisis as an
from tema import TEMA_CSS

# ----------------------------------------------------------------------------
# Utilidades compartidas (JS y CSS)
# ----------------------------------------------------------------------------
_CSS_COMUN = TEMA_CSS + """
:host, .raiz { font-family: var(--st-font, sans-serif); color: var(--st-text-color); }
.g { display: block; width: 100%; height: auto; overflow: visible; }
.g text { font-family: var(--st-font, sans-serif); }
.eje { font-size: 12px; fill: var(--t-suave); }
.tit { font-size: 13px; fill: var(--t-suave); }
.ley { display: flex; flex-wrap: wrap; gap: 4px 16px; font-size: 13px; margin: 6px 0 2px; }
.ley span { display: inline-flex; align-items: center; gap: 6px; }
.ley i { width: 12px; height: 12px; border-radius: 50%; display: inline-block; }
.ley .est { color: #d4a400; font-size: 16px; line-height: 12px; }
.tip { position: fixed; pointer-events: none; z-index: 1000; background: rgba(30,30,30,.92); color: #fff;
       font-size: 12.5px; line-height: 1.45; padding: 6px 9px; border-radius: 6px; white-space: nowrap;
       opacity: 0; transition: opacity .08s; }
.tip.on { opacity: 1; }
.g.arrastrable { cursor: ew-resize; touch-action: pan-y; user-select: none; -webkit-user-select: none; }  /* en táctil: vertical = desplazar la página */
.g.arrastrando { cursor: grabbing; }
/* Zona gruesa e invisible alrededor de la estrella: fácil de agarrar con el dedo y, al
   arrastrar desde ella, la página nunca se desplaza (no se interrumpe el arrastre) */
.agarre { fill: transparent; touch-action: none; cursor: grab; }
.g.arrastrable path[fill="gold"] { cursor: grab; }
.tb { width: 100%; border-collapse: collapse; font-size: 14px; margin: 6px 0 4px; }
.tb th { text-align: left; font-weight: 600; background: var(--t-cabecera); }
.tb th, .tb td { padding: 7px 10px; border-bottom: 1px solid var(--t-borde); }
.tb td.n, .tb th.n { text-align: right; font-variant-numeric: tabular-nums; }
.tb td i { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 7px; }
.cap { font-size: 14px; opacity: .65; line-height: 1.5; margin: 6px 0; }
.met { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 8px; }
.met .et { font-size: 14px; margin-bottom: 4px; }
.met .et abbr { text-decoration: none; cursor: help; opacity: .55; margin-left: 4px; font-size: 12px;
                border: 1px solid currentColor; border-radius: 50%; padding: 0 5px; }
.met .val { font-size: 34px; line-height: 1.2; font-variant-numeric: tabular-nums; white-space: nowrap; }
.caja { padding: 16px; border-radius: 8px; font-size: 16px; line-height: 1.6; margin: 8px 0; }
.caja.info { background: var(--st-blue-background-color, rgba(28,131,225,.1)); color: var(--st-blue-text-color, rgb(0,66,128)); }
.caja.ok { background: var(--st-green-background-color, rgba(33,195,84,.1)); color: var(--st-green-text-color, rgb(23,114,51)); }
.caja.mal { background: var(--st-red-background-color, rgba(255,43,43,.09)); color: var(--st-red-text-color, rgb(125,53,59)); }
.sub { margin: 14px 0 2px; font-size: 16px; }
@media (max-width: 640px) { .met { grid-template-columns: repeat(2, 1fr); } .met .val { font-size: 26px; } }
"""

_JS_COMUN = """
const NS = 'http://www.w3.org/2000/svg';
function el(tag, attrs, padre, texto) {
  const e = document.createElementNS(NS, tag);
  for (const k in attrs) e.setAttribute(k, attrs[k]);
  if (texto !== undefined) e.textContent = texto;
  if (padre) padre.appendChild(e);
  return e;
}
function ticks(a, b, n) {
  const p0 = (b - a) / n, p = Math.pow(10, Math.floor(Math.log10(p0))), m = p0 / p;
  const s = (m < 1.5 ? 1 : m < 3 ? 2 : m < 7 ? 5 : 10) * p, out = [];
  for (let v = Math.ceil(a / s) * s; v <= b + 1e-9; v += s) out.push(+v.toFixed(10));
  return out;
}
function dominio(vals, pad, min0) {
  let a = Math.min(...vals), b = Math.max(...vals);
  const d = (b - a) || 1; a -= d * pad; b += d * pad;
  if (min0 !== undefined) a = Math.max(a, min0);
  return [a, b];
}
// Ejes, rejilla y escalas. Devuelve funciones px/py y una capa para dibujar.
function marco(svg, o) {
  svg.innerHTML = '';
  const { W, H, M } = o;
  const px = (x) => M.l + (x - o.x[0]) / (o.x[1] - o.x[0]) * (W - M.l - M.r);
  const cx = (X) => o.x[0] + (X - M.l) / (W - M.l - M.r) * (o.x[1] - o.x[0]);  // inversa de px
  const py = (y) => H - M.b - (y - o.y[0]) / (o.y[1] - o.y[0]) * (H - M.t - M.b);
  const f = el('g', {}, svg);
  for (const t of ticks(o.y[0], o.y[1], 6)) {
    el('line', { x1: M.l, x2: W - M.r, y1: py(t), y2: py(t), class: 'rej' }, f);
    el('text', { x: M.l - 8, y: py(t) + 4, 'text-anchor': 'end', class: 'eje' }, f, o.fy ? o.fy(t) : t);
  }
  if (o.xcat) {
    o.xcat.forEach((c, i) => el('text', { x: px(i), y: H - M.b + 20, 'text-anchor': 'middle', class: 'eje' }, f, c));
  } else {
    for (const t of ticks(o.x[0], o.x[1], 8)) {
      el('line', { x1: px(t), x2: px(t), y1: M.t, y2: H - M.b, class: 'rej2' }, f);
      el('text', { x: px(t), y: H - M.b + 18, 'text-anchor': 'middle', class: 'eje' }, f, o.fx ? o.fx(t) : t);
    }
  }
  el('line', { x1: M.l, x2: W - M.r, y1: H - M.b, y2: H - M.b, class: 'eje-l' }, f);
  if (o.tx) el('text', { x: (M.l + W - M.r) / 2, y: H - 8, 'text-anchor': 'middle', class: 'tit' }, f, o.tx);
  if (o.ty) el('text', { x: 15, y: (M.t + H - M.b) / 2, 'text-anchor': 'middle', class: 'tit',
                         transform: `rotate(-90 15 ${(M.t + H - M.b) / 2})` }, f, o.ty);
  const id = 'clip' + Math.random().toString(36).slice(2);
  const cp = el('clipPath', { id }, el('defs', {}, svg));
  el('rect', { x: M.l, y: M.t - 12, width: W - M.l - M.r, height: H - M.t - M.b + 12 }, cp);
  return { px, py, cx, capa: el('g', { 'clip-path': `url(#${id})` }, svg), arriba: el('g', {}, svg) };
}
function estrella(cx, cy, r) {
  let d = '';
  for (let i = 0; i < 10; i++) {
    const a = -Math.PI / 2 + i * Math.PI / 5, rr = i % 2 ? r * 0.45 : r;
    d += (i ? 'L' : 'M') + (cx + rr * Math.cos(a)).toFixed(1) + ' ' + (cy + rr * Math.sin(a)).toFixed(1);
  }
  return d + 'Z';
}
// Globo de información al pasar el ratón sobre elementos con data-tip
function activarTips(root, svg) {
  if (svg._tips) return;
  svg._tips = true;
  const tip = document.createElement('div');
  tip.className = 'tip';
  root.appendChild(tip);
  svg.addEventListener('pointermove', (e) => {
    const t = e.target.closest && e.target.closest('[data-tip]');
    if (!t || svg._activo) { tip.classList.remove('on'); return; }  // sin globo mientras se arrastra
    tip.innerHTML = t.getAttribute('data-tip');
    tip.style.left = (e.clientX + 14) + 'px'; tip.style.top = (e.clientY - 10) + 'px';
    tip.classList.add('on');
  });
  svg.addEventListener('pointerleave', () => tip.classList.remove('on'));
}
const f0 = (v) => Number(v).toFixed(0), f1 = (v) => Number(v).toFixed(1), f2 = (v) => Number(v).toFixed(2);
// Gráfica interactiva: arrastrar (o hacer clic) para mover el acero. `aCarbono(x)` convierte
// la x del puntero (en unidades del viewBox) en % C; el deslizador aplica el valor.
function arrastrarCarbono(svg, aCarbono) {
  if (svg._arrastre) return;
  svg._arrastre = true;
  svg.classList.add('arrastrable');
  const xSvg = (e) => {
    const r = svg.getBoundingClientRect(), vb = svg.viewBox.baseVal;
    return (e.clientX - r.left) * vb.width / r.width;
  };
  const pedir = (e, extra) => {
    const c = aCarbono(xSvg(e));
    if (c === null || !isFinite(c)) return;
    svg._ultimoC = c;  // último valor válido
    window.dispatchEvent(new CustomEvent('carbono-pedir', { detail: { valor: c, ...extra } }));
  };
  svg.addEventListener('pointerdown', (e) => {
    if (e.button !== 0) return;
    e.preventDefault();
    try { svg.setPointerCapture(e.pointerId); } catch (err) { /* puntero no capturable */ }
    svg._activo = true; svg.classList.add('arrastrando');
    pedir(e, { inicio: true });
  });
  // Movimientos agrupados: como máximo uno por cuadro de pantalla (más fluido)
  svg.addEventListener('pointermove', (e) => {
    if (!svg._activo) return;
    svg._ultimoEv = e;
    if (!svg._cuadro) svg._cuadro = requestAnimationFrame(() => { svg._cuadro = 0; if (svg._activo) pedir(svg._ultimoEv, {}); });
  });
  const soltar = (e) => {
    if (!svg._activo) return;
    svg._activo = false; svg.classList.remove('arrastrando');
    cancelAnimationFrame(svg._cuadro); svg._cuadro = 0;
    // Si el navegador cancela el arrastre (p. ej. el dedo se movió en vertical), su posición
    // puede llegar en 0: se conserva el último valor válido en vez de saltar al origen
    if (e.type === 'pointercancel' || (e.clientX === 0 && e.clientY === 0)) {
      if (svg._ultimoC !== undefined) window.dispatchEvent(new CustomEvent('carbono-pedir', { detail: { valor: svg._ultimoC, fin: true } }));
    } else pedir(e, { fin: true });
  };
  svg.addEventListener('pointerup', soltar);
  svg.addEventListener('pointercancel', soltar);
}
function predecir(m, c) {
  return { UTS: m.a_UTS + m.b_UTS * c, YS: m.a_YS + m.b_YS * c, DU: Math.max(m.a_DU + m.b_DU * c, 0),
           en_rango: m.C_min - 1e-9 <= c && c <= m.C_max + 1e-9 };
}
function leyenda(div, d, activa) {
  div.innerHTML = d.orden.map((k) =>
    `<span style="opacity:${!activa || k === activa ? 1 : .55}"><i style="background:${d.color[k]}"></i>${k}</span>`
  ).join('') + '<span><b class="est">★</b>Tu acero</span>';
}
// Patrón común: redibujar con el valor del deslizador de carbono sin esperar al servidor
function conectar(root, data, dibujar) {
  root._data = data;
  if (!root._oyente) {
    root._oyente = (e) => { root._cLocal = e.detail; dibujar(root, root._data, e.detail); };
    window.addEventListener('carbono-cambia', root._oyente);
  }
  const c = window.__arrastrandoCarbono && root._cLocal !== undefined ? root._cLocal : data.c;
  if (!window.__arrastrandoCarbono) root._cLocal = undefined;
  dibujar(root, data, c);
  return () => { window.removeEventListener('carbono-cambia', root._oyente); root._oyente = null; };
}
const W = 900, H = 430, M = { l: 62, r: 16, t: 22, b: 50 };
// Al desplegar la tabla: deslizar la página a la vez que se abre, hasta que la línea
// "Acero con … % C" quede arriba (así las filas nuevas caben sin perder el deslizador)
function deslizarAlResumen(dur) {
  const sc = document.querySelector('[data-testid="stMain"]');
  const marca = document.querySelector('.st-key-resumen_acero');
  if (!sc || !marca) return;
  deslizarA(Math.max(0, marca.getBoundingClientRect().top - sc.getBoundingClientRect().top + sc.scrollTop - 4), dur);
}
// Al desplegar una tabla se recuerda dónde estaba la página; al guardarla, se vuelve ahí
// con un deslizamiento suave a la vez que la tabla se cierra
function recordarPosicion(root) {
  const sc = document.querySelector('[data-testid="stMain"]');
  root._scrollAntes = sc ? sc.scrollTop : 0;
}
function volverAlGuardar(root, dur) {
  const sc = document.querySelector('[data-testid="stMain"]');
  if (!sc || root._scrollAntes === undefined) return;
  if (sc.scrollTop > root._scrollAntes + 1) deslizarA(root._scrollAntes, dur);
}
// Deslizamiento suave de la página hasta `destino` (px), a la vez que se abre una tabla
function deslizarA(destino, dur) {
  const sc = document.querySelector('[data-testid="stMain"]');
  if (!sc) return;
  // Espacio extra temporal al final para poder deslizar desde el primer instante
  const blk = sc.querySelector('[data-testid="stMainBlockContainer"]');
  if (blk) {
    blk.style.paddingBottom = 'calc(1.5rem + 200px)';
    setTimeout(() => { blk.style.paddingBottom = ''; }, dur + 250);
  }
  const ini = sc.scrollTop, t0 = performance.now(), curva = (k) => 1 - Math.pow(1 - k, 3);
  const paso = (t) => {
    const k = Math.min(1, (t - t0) / dur);
    sc.scrollTop = ini + (destino - ini) * curva(k);
    if (k < 1) requestAnimationFrame(paso);
  };
  requestAnimationFrame(paso);
}
"""

# ----------------------------------------------------------------------------
# Propiedades
# ----------------------------------------------------------------------------
_HTML_PROP = """
<div class="raiz">
  <div class="met">
    <div><div class="et">Resistencia a la tracción (UTS)<abbr title="Recta UTS = a + b·C de la sección 3.1">?</abbr></div><div class="val v-uts"></div></div>
    <div><div class="et">Límite de fluencia (YS)</div><div class="val v-ys"></div></div>
    <div><div class="et">Ductilidad (elongación)</div><div class="val v-du"></div></div>
    <div><div class="et">Error típico de predicción<abbr title="Error medio al predecir un acero que no se usó en el ajuste (validación cruzada, sección 5.6)">?</abbr></div><div class="val v-err"></div></div>
  </div>
  <div class="cap modelo"></div>
  <div class="pf">
    <div class="pf-graf">
      <div class="ley"></div>
      <svg class="g" viewBox="0 0 900 430"></svg>
    </div>
    <div class="pf-tabla">
      <div class="seg">
        <button data-p="UTS">UTS</button><button data-p="YS">YS</button><button data-p="DU">Ductilidad</button>
      </div>
      <div class="pf-bloque">
      <div class="sub"><b>Mismo acero, distinto procesamiento</b><br>(predicción de cada recta con este %C)</div>
      <div class="rk">
        <button class="rk-bt" type="button"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 9l6 6 6-6"/></svg></button>
        <div class="rk-cuerpo">
          <table class="tb tb-top"></table>
          <div class="rk-mas"><div class="rk-in"><table class="tb tb-resto"></table></div></div>
        </div>
      </div>
      </div>
    </div>
  </div>
</div>
"""
_CSS_PROP = """
.seg { display: inline-flex; border: 1px solid var(--t-borde); border-radius: 8px; overflow: hidden; margin: 10px 0 4px; }
.seg button { font: inherit; font-size: 14px; padding: 6px 16px; border: 0; background: transparent; cursor: pointer;
              color: inherit; border-right: 1px solid var(--t-borde); }
.seg button:last-child { border-right: 0; }
.seg button.on { background: var(--st-primary-color); color: #fff; }
/* Gráfica a la izquierda y tabla a la derecha (en pantallas angostas, una debajo de otra) */
.raiz { container-type: inline-size; }
/* Nota de la recta en un solo renglón (con cualquier condición) */
.modelo { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.pf { display: flex; gap: 24px; align-items: flex-start; flex-wrap: nowrap; }
.pf-graf { flex: 1 1 300px; min-width: 240px; }
/* Ancho para que ningún texto de la tabla se parta en dos renglones */
.pf-tabla { flex: 0 0 520px; min-width: 0; }
/* Si no caben las dos columnas, la tabla va debajo de la gráfica, a todo el ancho */
@container (max-width: 790px) { .pf { flex-wrap: wrap; } .pf-tabla { flex: 1 1 100%; } }
.pf-tabla .sub { margin: 10px 0 6px; font-size: 14px; line-height: 1.4; text-align: center; }
.pf-tabla .seg { display: flex; width: fit-content; margin: 0 auto 4px; }  /* centrados respecto a la tabla */
.pf-bloque { display: flow-root; }  /* título + tabla; su margen superior lo fija ajustarTablaProp */
.pf-tabla .tb-top, .pf-tabla .tb-resto { font-size: 12px; }
.pf-tabla .tb-top th, .pf-tabla td { white-space: nowrap; line-height: 1.25; vertical-align: middle; }
/* Todos los valores centrados, igual que los títulos de columna */
.pf-tabla td, .pf-tabla td.n { text-align: center; }
.pf-tabla .tb-top th, .pf-tabla .tb-top td, .pf-tabla .tb-resto td { padding: 5px 6px; }
/* "Rango con datos": ancho fijo para "no (extrapolación)" en un renglón (la tabla no cambia de alto) */
.pf-tabla td.rg { white-space: nowrap; }
"""
_JS_PROP = """
const ETQ = { UTS: 'UTS (MPa)', YS: 'YS (MPa)', DU: 'Ductilidad (%)' };
// Tamaño de la gráfica: mismo criterio que "Compromiso resistencia–ductilidad": llega
// hasta el borde inferior de la pantalla (sin contar los avisos amarillos), con
// proporción máxima 2:1 y sin pasar del ancho de su columna
function medidasProp(root) {
  const svg = root.querySelector('.g');
  if (!svg.getClientRects().length) return null;  // pestaña oculta
  const sc = document.querySelector('[data-testid="stMain"]') || document.scrollingElement;
  const avisos = document.querySelector('.st-key-avisos');
  const altoAvisos = avisos ? avisos.getBoundingClientRect().height : 0;
  const arriba = svg.getBoundingClientRect().top - sc.getBoundingClientRect().top + sc.scrollTop - altoAvisos;
  const libre = sc.clientHeight - arriba - 24 - 6;
  const anchoMax = Math.floor(root.querySelector('.pf-graf').getBoundingClientRect().width);
  const h = Math.max(260, Math.floor(libre));
  const w = Math.min(anchoMax, h * 2);
  return { W: w, H: Math.min(h, Math.floor(w / 1.25)) };
}
function construirProp(root, d, prop) {
  const { W, H } = root._tamP, svg = root.querySelector('.g');
  svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
  const pts = [], m = d.modelos[d.cnd];
  for (const k of d.orden) pts.push(...d.puntos[k][prop]);
  for (const c of [0.05, 1.0]) pts.push(predecir(m, c)[prop]);
  const g = marco(svg, { W, H, M, x: [0, 1.05], y: dominio(pts, 0.06, prop === 'DU' ? 0 : undefined),
                                               tx: 'C (% en peso)', ty: ETQ[prop] });
  el('line', { x1: g.px(d.eut), x2: g.px(d.eut), y1: M.t, y2: H - M.b, class: 'guia', 'stroke-dasharray': '3 4' }, g.capa);
  el('text', { x: g.px(d.eut) + 5, y: M.t + 4, class: 'eje' }, g.arriba, 'eutectoide');
  const unidad = prop === 'DU' ? ' %' : ' MPa';
  for (const k of [...d.orden.filter((x) => x !== d.cnd), d.cnd]) {
    const act = k === d.cnd, p = d.puntos[k], mk = d.modelos[k];
    for (let i = 0; i < p.C.length; i++) {
      el('circle', { cx: g.px(p.C[i]), cy: g.py(p[prop][i]), r: act ? 5 : 4, fill: d.color[k], 'fill-opacity': act ? .85 : .25,
                     'data-tip': `${p.acero[i]} · ${k}<br>C = ${f2(p.C[i])} %<br>${ETQ[prop].split(' ')[0]} = ${prop === 'DU' ? f1(p[prop][i]) : f0(p[prop][i])}${unidad}` }, g.capa);
    }
    const y = (c) => mk['a_' + prop] + mk['b_' + prop] * c;
    el('line', { x1: g.px(mk.C_min), y1: g.py(y(mk.C_min)), x2: g.px(mk.C_max), y2: g.py(y(mk.C_max)),
                 stroke: d.color[k], 'stroke-width': act ? 4 : 1.5, 'stroke-linecap': 'round' }, g.capa);
  }
  g.est = el('path', { fill: 'gold', stroke: '#000', 'stroke-width': 1.5 }, g.arriba);
  g.agarre = el('circle', { r: 26, class: 'agarre' }, g.arriba);
  return g;
}
// Título + tabla en una posición fija (no se deslizan): colocados de modo que, al
// desplegar la tabla, su final coincida con el final de la gráfica (eje horizontal).
// Con la tabla debajo de la gráfica (pantallas angostas), sin margen.
function ajustarTablaProp(root) {
  const bloque = root.querySelector('.pf-bloque'), pg = root.querySelector('.pf-graf'), pt = root.querySelector('.pf-tabla');
  if (!bloque || !pg.getClientRects().length || !root._tamP) return;
  const lado = pt.getBoundingClientRect().left >= pg.getBoundingClientRect().right;
  let mt = 0;
  if (lado) {
    const finGrafica = root.querySelector('.g').getBoundingClientRect().top + root._tamP.H - M.b;
    const seg = root.querySelector('.pf-tabla .seg');
    // (el margen inferior de los botones y el superior del bloque se combinan, no se suman)
    const inicio = seg.getBoundingClientRect().bottom, minimo = parseFloat(getComputedStyle(seg).marginBottom);
    const inn = bloque.querySelector('.rk-in');
    const rk = bloque.querySelector('.rk');
    const altoAbierto = bloque.getBoundingClientRect().height - inn.getBoundingClientRect().height + inn.scrollHeight
                      - parseFloat(getComputedStyle(rk).marginBottom);
    mt = Math.max(minimo, Math.round(finGrafica - inicio - altoAbierto));
  }
  if (bloque.style.marginTop !== mt + 'px') bloque.style.marginTop = mt + 'px';
}
// Todas las filas de la tabla con la misma altura: la de la fila más alta
// (por ejemplo "Laminado en caliente" si su nombre ocupa dos renglones)
function igualarFilas(root) {
  const filas = [...root.querySelectorAll('.pf-tabla tr')].filter((t) => t.querySelector('td'));
  if (!filas.length || !filas[0].getClientRects().length) return;
  filas.forEach((t) => { t.style.height = ''; });
  const alto = Math.max(...filas.map((t) => t.getBoundingClientRect().height));
  filas.forEach((t) => { t.style.height = alto + 'px'; });
}
function dibujarProp(root, d, c) {
  root._tamP = medidasProp(root) || root._tamP || { W: 900, H: 430 };
  // Columna derecha (botones y tabla) a la altura donde empieza la gráfica de la izquierda
  const pg = root.querySelector('.pf-graf'), pt = root.querySelector('.pf-tabla');
  if (pg.getClientRects().length) {
    const lado = pt.getBoundingClientRect().left >= pg.getBoundingClientRect().right;  // una junto a otra
    // (+ M.t: margen interno superior del SVG, donde empieza el área de la gráfica)
    const mt = lado ? Math.round(root.querySelector('.g').getBoundingClientRect().top - pg.getBoundingClientRect().top + M.t) + 'px' : '0px';
    if (pt.style.marginTop !== mt) pt.style.marginTop = mt;
  }
  const prop = root._prop || 'UTS', clave = d.cnd + '|' + prop + '|' + root._tamP.W + 'x' + root._tamP.H;
  if (root._clave !== clave) { root._g = construirProp(root, d, prop); root._clave = clave; }
  const m = d.modelos[d.cnd], p = predecir(m, c), g = root._g;
  root.querySelector('.v-uts').textContent = f0(p.UTS) + ' MPa';
  root.querySelector('.v-ys').textContent = f0(p.YS) + ' MPa';
  root.querySelector('.v-du').textContent = f1(p.DU) + ' %';
  root.querySelector('.v-err').textContent = '± ' + f0(m.error_LOO) + ' MPa';
  const v = p[prop];
  g.est.setAttribute('d', estrella(g.px(c), g.py(v), 12));
  g.est.setAttribute('data-tip', `<b>Tu acero</b> · ${d.cnd}<br>C = ${f2(c)} %<br>${ETQ[prop].split(' ')[0]} = ${prop === 'DU' ? f1(v) + ' %' : f0(v) + ' MPa'}`);
  g.agarre.setAttribute('cx', g.px(c)); g.agarre.setAttribute('cy', g.py(v));
  g.agarre.setAttribute('data-tip', g.est.getAttribute('data-tip'));
  // Tabla "mismo acero, distinto procesamiento": cerrada muestra solo la condición elegida
  const cols = '<colgroup><col style="width:28.4%"><col style="width:13.5%"><col style="width:11.8%"><col style="width:17.9%"><col style="width:28.4%"></colgroup>';
  const fila = (k) => {
    const q = predecir(d.modelos[k], c);
    return `<tr${k === d.cnd ? ' class="sel"' : ''}><td><i style="background:${d.color[k]}"></i>${k}</td>`
      + `<td class="n">${f0(q.UTS)}</td><td class="n">${f0(q.YS)}</td><td class="n">${f1(q.DU)}</td>`
      + `<td class="rg">${q.en_rango ? 'sí' : 'no (extrapolación)'}</td></tr>`;
  };
  requestAnimationFrame(() => { igualarFilas(root); ajustarTablaProp(root); });
  root.querySelector('.tb-top').innerHTML = cols
    + '<tr><th>Condición</th><th class="n">UTS (MPa)</th><th class="n">YS (MPa)</th><th class="n">Ductilidad (%)</th><th>Rango con datos</th></tr>'
    + fila(d.cnd);
  root.querySelector('.tb-resto').innerHTML = cols + d.orden.filter((k) => k !== d.cnd).map(fila).join('');
}
export default function (component) {
  const { data, parentElement } = component;
  const root = parentElement;
  const modelo = root.querySelector('.modelo');
  modelo.textContent = data.texto_modelo; modelo.title = data.texto_modelo;  // completa al pasar el ratón
  leyenda(root.querySelector('.ley'), data, data.cnd);
  activarTips(root, root.querySelector('.g'));
  // Arrastrar en la gráfica mueve el carbono (eje x = % C)
  arrastrarCarbono(root.querySelector('.g'), (x) => root._g ? root._g.cx(x) : null);
  // Botón para desplegar/guardar la tabla; al desplegar se desliza la página
  const rk = root.querySelector('.rk'), bt = root.querySelector('.rk-bt');
  const rotular = () => {
    const t = root._rkAbierta ? 'Guardar la tabla' : `Mostrar las ${data.orden.length} condiciones`;
    bt.title = t; bt.setAttribute('aria-label', t); bt.setAttribute('aria-expanded', !!root._rkAbierta);
  };
  rk.classList.toggle('abierta', !!root._rkAbierta);
  rotular();
  bt.onclick = () => {
    root._rkAbierta = !root._rkAbierta;
    rk.classList.toggle('abierta', root._rkAbierta);
    rotular();
    if (!root._rkAbierta) volverAlGuardar(root, 300);
    // Deslizar solo lo necesario para que la tabla abierta quepa completa en la pantalla
    if (root._rkAbierta) {
      recordarPosicion(root);
      const falta = rk.getBoundingClientRect().bottom + root.querySelector('.rk-in').scrollHeight - (window.innerHeight - 16);
      const sc = document.querySelector('[data-testid="stMain"]');
      if (falta > 0 && sc) deslizarA(sc.scrollTop + falta, 300);
    }
  };
  const botones = root.querySelectorAll('.seg button');
  botones.forEach((b) => {
    b.classList.toggle('on', b.dataset.p === (root._prop || 'UTS'));
    b.onclick = () => {
      root._prop = b.dataset.p;
      botones.forEach((x) => x.classList.toggle('on', x === b));
      dibujarProp(root, root._data, root._cActual ?? root._data.c);
    };
  });
  // Recalcular el tamaño al mostrar la pestaña o cambiar el tamaño de la ventana
  if (!root._obsP) {
    const rehacer = () => requestAnimationFrame(() => dibujarProp(root, root._data, root._cActual ?? root._data.c));
    root._obsP = new ResizeObserver(rehacer);
    root._obsP.observe(root.querySelector('.pf-graf'));
    window.addEventListener('resize', rehacer);
  }
  return conectar(root, data, (r, d, c) => { r._cActual = c; dibujarProp(r, d, c); });
}
"""

# ----------------------------------------------------------------------------
# Resistencia vs ductilidad
# ----------------------------------------------------------------------------
_HTML_COMP = """
<div class="raiz comp">
  <div class="ley"></div>
  <svg class="g" viewBox="0 0 600 300"></svg>
</div>
"""
# Gráfica centrada; su tamaño se calcula en el navegador para ocupar todo el alto libre
# de la pantalla (dejando visible la nota de abajo). El viewBox coincide con el tamaño
# real, así el texto de los ejes no cambia de tamaño.
_CSS_COMP = """
.comp { max-width: 600px; margin: 0 auto; }
.comp .ley { justify-content: center; }
"""
_JS_COMP = """
// Tamaño de la gráfica: todo el alto libre hasta el borde inferior de la pantalla,
// dejando sitio para la nota que va debajo (proporción máxima 2:1, sin pasar del ancho)
function medidas(root) {
  const svg = root.querySelector('.g');
  if (!svg.getClientRects().length) return null;  // pestaña oculta
  const sc = document.querySelector('[data-testid="stMain"]') || document.scrollingElement;
  const host = root.getRootNode().host;
  const cont = host && host.closest('[data-testid="stElementContainer"]');
  const nota = cont && cont.nextElementSibling;
  const altoNota = nota ? nota.getBoundingClientRect().height : 48;
  // Los avisos amarillos (extrapolación) no cuentan: al aparecer no deben encoger la gráfica
  const avisos = document.querySelector('.st-key-avisos');
  const altoAvisos = avisos ? avisos.getBoundingClientRect().height : 0;
  const arriba = svg.getBoundingClientRect().top - sc.getBoundingClientRect().top + sc.scrollTop - altoAvisos;
  const libre = sc.clientHeight - arriba - 16 - altoNota - 24 - 6;
  const anchoMax = Math.floor(root.querySelector('.comp').parentElement.getBoundingClientRect().width);
  const h = Math.max(240, Math.floor(libre));
  const w = Math.min(anchoMax, h * 2);
  return { W: w, H: Math.min(h, Math.floor(w / 1.25)) };
}
function construirComp(root, d) {
  const xs = [], ys = [];
  for (const k of d.orden) { xs.push(...d.puntos[k].UTS); ys.push(...d.puntos[k].DU); }
  const m = d.modelos[d.cnd];
  for (const c of [0.05, 1.0]) { const p = predecir(m, c); xs.push(p.UTS); ys.push(p.DU); }
  const { W, H } = root._tam, svg = root.querySelector('.g');
  svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
  root.querySelector('.comp').style.maxWidth = W + 'px';
  const g = marco(svg, { W, H, M, x: dominio(xs, 0.05), y: dominio(ys, 0.06, 0),
                                               tx: 'UTS (MPa)', ty: 'Ductilidad (%)' });
  for (const k of d.orden) {
    const p = d.puntos[k];
    for (let i = 0; i < p.C.length; i++) {
      el('circle', { cx: g.px(p.UTS[i]), cy: g.py(p.DU[i]), r: 4, fill: d.color[k], 'fill-opacity': .35,
                     'data-tip': `${p.acero[i]} · ${k}<br>UTS ${f0(p.UTS[i])} MPa<br>Ductilidad ${f0(p.DU[i])} %` }, g.capa);
    }
  }
  for (const k of [...d.orden.filter((x) => x !== d.cnd), d.cnd]) {
    const mk = d.modelos[k], a = predecir(mk, mk.C_min), b = predecir(mk, mk.C_max);
    el('line', { x1: g.px(a.UTS), y1: g.py(mk.a_DU + mk.b_DU * mk.C_min), x2: g.px(b.UTS), y2: g.py(mk.a_DU + mk.b_DU * mk.C_max),
                 stroke: d.color[k], 'stroke-width': k === d.cnd ? 4 : 2, 'stroke-linecap': 'round' }, g.capa);
  }
  g.est = el('path', { fill: 'gold', stroke: '#000', 'stroke-width': 1.5 }, g.arriba);
  g.agarre = el('circle', { r: 26, class: 'agarre' }, g.arriba);
  return g;
}
function dibujarComp(root, d, c) {
  root._tam = medidas(root) || root._tam || { W: 600, H: 300 };
  const clave = d.cnd + '|' + root._tam.W + 'x' + root._tam.H;
  if (root._clave !== clave) { root._g = construirComp(root, d); root._clave = clave; }
  const p = predecir(d.modelos[d.cnd], c), g = root._g;
  g.est.setAttribute('d', estrella(g.px(p.UTS), g.py(p.DU), 12));
  g.est.setAttribute('data-tip', `<b>Tu acero</b> · ${d.cnd}<br>C = ${f2(c)} %<br>UTS ${f0(p.UTS)} MPa · Ductilidad ${f1(p.DU)} %`);
  g.agarre.setAttribute('cx', g.px(p.UTS)); g.agarre.setAttribute('cy', g.py(p.DU));
  g.agarre.setAttribute('data-tip', g.est.getAttribute('data-tip'));
}
export default function (component) {
  const { data, parentElement } = component;
  const root = parentElement;
  leyenda(root.querySelector('.ley'), data, data.cnd);
  activarTips(root, root.querySelector('.g'));
  // Arrastrar en la gráfica mueve el carbono: la UTS del puntero se convierte en % C
  // con la recta de la condición elegida (la estrella se desliza sobre esa recta)
  arrastrarCarbono(root.querySelector('.g'), (x) => {
    if (!root._g) return null;
    const m = root._data.modelos[root._data.cnd];
    return (root._g.cx(x) - m.a_UTS) / m.b_UTS;
  });
  // Recalcular el tamaño al mostrar la pestaña o cambiar el tamaño de la ventana
  if (!root._obs) {
    const rehacer = () => requestAnimationFrame(() => dibujarComp(root, root._data, root._cActual ?? root._data.c));
    root._obs = new ResizeObserver(rehacer);
    root._obs.observe(root.querySelector('.comp').parentElement);
    window.addEventListener('resize', rehacer);
  }
  const fin = conectar(root, data, (r, d, c) => { r._cActual = c; dibujarComp(r, d, c); });
  return fin;
}
"""

# ----------------------------------------------------------------------------
# Diseño inverso (con su propio deslizador de resistencia)
# ----------------------------------------------------------------------------
_HTML_DIS = """
<div class="raiz">
  <div class="rk">
    <button class="rk-bt" type="button"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 9l6 6 6-6"/></svg></button>
    <div class="rk-cuerpo">
      <table class="tb tb-top"></table>
      <div class="rk-mas"><div class="rk-in"><table class="tb tb-resto"></table></div></div>
    </div>
  </div>
  <div class="sub tit-g"></div>
  <svg class="g" viewBox="0 0 900 400"></svg>
  <div class="sl">
    <div class="sl-cab"><span>Resistencia a la tracción requerida (MPa)</span><b class="sl-val"></b></div>
    <input class="sl-in" type="range" min="400" max="1000" step="10">
    <div class="sl-lim"><span>400</span><span>1000</span></div>
  </div>
</div>
"""
_CSS_RK = """
/* Tabla desplegable (Propiedades y Diseño inverso): cerrada muestra solo una fila */
.tb-top, .tb-resto { font-size: 13px; }
.tb-top th, .tb-top td, .tb-resto td { padding: 5px 10px; }
.rk { position: relative; border: 1px solid var(--t-borde); border-radius: 8px; margin: 8px 0; }
.rk-cuerpo { padding: 8px 14px; }
/* Botón para desplegar (flecha abajo) y guardar (flecha a la izquierda) la tabla */
.rk-bt { position: absolute; top: 8px; right: 20px; z-index: 2; width: 28px; height: 28px; padding: 0;
         display: grid; place-items: center; border-radius: 50%; cursor: pointer;
         border: 1px solid var(--t-borde); background: var(--t-fondo); color: var(--t-texto);
         transition: background .2s, color .2s, border-color .2s, transform .15s, box-shadow .2s; }
.rk-bt:hover { background: var(--st-primary-color); color: #fff; border-color: transparent;
               transform: scale(1.1); box-shadow: 0 2px 8px rgba(0,0,0,.25); }
.rk-bt:active { transform: scale(.94); }
.rk-bt:focus-visible { outline: 2px solid var(--st-primary-color); outline-offset: 2px; }
.rk-bt svg { width: 16px; height: 16px; fill: none; stroke: currentColor; stroke-width: 2.4;
             stroke-linecap: round; stroke-linejoin: round; transition: transform .3s ease; }
.rk.abierta .rk-bt svg { transform: rotate(90deg); }
/* Nombres de columna centrados; la última deja sitio al botón */
.tb-top th, .tb-top th.n { text-align: center; }
.tb-top th:last-child { padding-right: 46px; }
.rk-mas { display: grid; grid-template-rows: 0fr; transition: grid-template-rows .3s ease; }
.rk.abierta .rk-mas { grid-template-rows: 1fr; }
.rk-in { overflow: hidden; min-height: 0; }
.tb-top, .tb-resto { margin: 0; }
.tb-top th { white-space: nowrap; }
.tb tr.primero td { background: var(--st-green-background-color, rgba(33,195,84,.09)); font-weight: 600; }
.tb tr.fuera td { opacity: .45; }
/* Nota en un solo renglón: las filas no cambian de alto (tabla de tamaño fijo) */
.tb td.nota { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.tb tr.sel td { font-weight: 600; }
"""

_CSS_DIS = """
.sl { padding: 8px 0 2px; max-width: 520px; }
/* Más compacto para que todo quepa en una pantalla */
.caja.rec { font-size: 14px; line-height: 1.5; padding: 10px 14px; margin: 4px 0; }
.sub.tit-g { margin: 8px 0 0; font-size: 15px; }
.cap { margin: 2px 0; }
.tb { table-layout: fixed; }  /* columnas de ancho fijo */
.sl-cab { display: flex; justify-content: space-between; font-size: 14px; margin-bottom: 6px; }
.sl-val { color: var(--st-primary-color); font-variant-numeric: tabular-nums; }
.sl-in { width: 100%; accent-color: var(--st-primary-color); cursor: pointer; margin: 0; }
.sl-lim { display: flex; justify-content: space-between; font-size: 12px; opacity: .6; }
"""
_JS_DIS = """
function diseno(d, obj) {
  return d.orden.map((k) => {
    const m = d.modelos[k], c = (obj - m.a_UTS) / m.b_UTS;
    const dentro = m.C_min <= c && c <= m.C_max;
    const conf = dentro && !(k === 'Recocido' && c > d.eut);
    const nota = !dentro ? `Fuera del rango con datos (${f2(m.C_min)}–${f2(m.C_max)} % C)`
      : !conf ? 'Zona hipereutectoide: el recocido deja de ser lineal (sección 5.4)'
      : 'Dentro del rango con datos';
    return { k, c, du: conf ? m.a_DU + m.b_DU * c : null, conf, nota };
  });
}
// Alto de la gráfica de barras: todo el espacio libre hasta el borde inferior, dejando
// visibles la nota y el deslizador. No cuentan los avisos amarillos ni la parte
// desplegada de la tabla (así la gráfica no cambia de tamaño al abrirla).
function medidasDis(root) {
  const svg = root.querySelector('.g'), sl = root.querySelector('.sl');
  if (!svg.getClientRects().length) return null;  // pestaña oculta
  const sc = document.querySelector('[data-testid="stMain"]') || document.scrollingElement;
  const scTop = sc.getBoundingClientRect().top, rs = svg.getBoundingClientRect();
  // Posición de la gráfica con la tabla en su estado final (cerrada o desplegada),
  // aunque la tabla esté a media animación
  const inn = root.querySelector('.rk-in');
  const filas = root._rkAbierta ? inn.scrollHeight : 0;
  const svgAbs = rs.top - scTop + sc.scrollTop - inn.getBoundingClientRect().height + filas;
  let arriba = svgAbs;
  if (root._rkAbierta) {
    // Tabla desplegada: la página se desliza hasta las pestañas; la gráfica crece para
    // que desde las pestañas hasta el deslizador ocupe exactamente la pantalla
    const tabs = document.querySelector('[role="tablist"]');
    if (tabs) arriba -= tabs.getBoundingClientRect().top - scTop + sc.scrollTop - 4;
  }
  const debajo = sl.getBoundingClientRect().bottom - rs.bottom;
  const libre = sc.clientHeight - arriba - debajo - 24 - 6;
  const W = Math.floor(root.querySelector('.raiz').getBoundingClientRect().width);
  return { W, H: Math.max(120, Math.min(Math.floor(libre), Math.floor(W * 0.6))) };
}
// Deslizar la página hasta que la fila de pestañas quede arriba
function deslizarAPestanas(dur) {
  const sc = document.querySelector('[data-testid="stMain"]'), tabs = document.querySelector('[role="tablist"]');
  if (!sc || !tabs) return;
  deslizarA(Math.max(0, tabs.getBoundingClientRect().top - sc.getBoundingClientRect().top + sc.scrollTop - 4), dur);
}
function dibujarDis(root, d, obj) {
  root.querySelector('.sl-val').textContent = obj + ' MPa';
  const res = diseno(d, obj), val = res.filter((r) => r.conf);
  // La recomendación se muestra como notificación verde junto a las pestañas (avisos.py)
  let rec;
  if (val.length) {
    const mejor = val.reduce((a, b) => (b.du > a.du ? b : a));
    const real = d.aceros[mejor.k].reduce((a, b) => (Math.abs(b.C - mejor.c) < Math.abs(a.C - mejor.c) ? b : a));
    rec = { tipo: 'ok', html: `<b>Recomendación:</b> ${mejor.k} con <b>${f2(mejor.c)} % C</b> (el más cercano en los datos es `
      + `${real.acero}: ${f0(real.UTS)} MPa); conserva la mayor ductilidad: <b>${f1(mejor.du)} %</b>.` };
  } else {
    rec = { tipo: 'mal', html: 'Ninguna condición alcanza esa resistencia dentro del rango de carbono con datos. '
      + 'Para resistencias mayores hace falta temple y revenido o un acero aleado.' };
  }
  window.__recomendacion = rec;
  window.dispatchEvent(new CustomEvent('recomendacion'));
  // Clasificación: las condiciones confiables por ductilidad (mayor primero); las que
  // están fuera del rango o en zona no lineal, al final y en tono más claro
  const orden = [...res.filter((r) => r.conf).sort((x, y) => y.du - x.du), ...res.filter((r) => !r.conf)];
  const cols = '<colgroup><col style="width:7%"><col style="width:19%"><col style="width:13%"><col style="width:18%"><col style="width:43%"></colgroup>';
  const fila = (r, i) => `<tr class="${!r.conf ? 'fuera' : i === 0 ? 'primero' : ''}"><td class="n">${r.conf ? i + 1 : '—'}</td>`
    + `<td><i style="background:${d.color[r.k]}"></i>${r.k}</td><td class="n">${f2(r.c)}</td>`
    + `<td class="n">${r.du === null ? '—' : f1(r.du)}</td><td class="nota" title="${r.nota}">${r.nota}</td></tr>`;
  root.querySelector('.tb-top').innerHTML = cols
    + '<tr><th class="n">Puesto</th><th>Condición</th><th class="n">C necesario (%)</th><th class="n">Ductilidad esperada (%)</th><th>Nota</th></tr>'
    + fila(orden[0], 0);
  root.querySelector('.tb-resto').innerHTML = cols + orden.slice(1).map((r, j) => fila(r, j + 1)).join('');
  const rk = root.querySelector('.rk');
  rk.classList.toggle('abierta', !!root._rkAbierta);
  const bt = root.querySelector('.rk-bt');
  const rotular = () => {
    const t = root._rkAbierta ? 'Guardar la tabla' : `Mostrar las ${orden.length} condiciones`;
    bt.title = t; bt.setAttribute('aria-label', t); bt.setAttribute('aria-expanded', !!root._rkAbierta);
  };
  rotular();
  bt.onclick = () => {
    root._rkAbierta = !root._rkAbierta;
    rk.classList.toggle('abierta', root._rkAbierta);
    rotular();
    if (root._rkAbierta) {
      recordarPosicion(root);
      dibujarDis(root, root._dataDis, root._obj);  // gráfica más alta con la tabla desplegada
      deslizarAPestanas(300);
    } else {
      volverAlGuardar(root, 300);
      dibujarDis(root, root._dataDis, root._obj);  // vuelve a su alto normal
    }
  };
  root.querySelector('.tit-g').innerHTML = `<b>Carbono necesario para ${obj} MPa</b>`;
  // Barras (eje fijo para que no salte al mover el deslizador). El alto se ajusta a la
  // pantalla para que desde el título hasta el deslizador quepa sin desplazarse.
  const svg = root.querySelector('.g');
  root._tamDis = medidasDis(root) || root._tamDis || { W: 900, H: 400 };
  const { W: WD, H: HD } = root._tamDis, claveDis = WD + 'x' + HD;
  if (root._claveDis !== claveDis) { root._g = null; root._claveDis = claveDis; }
  const g = root._g || (root._g = (() => {
    svg.setAttribute('viewBox', `0 0 ${WD} ${HD}`);
    const g = marco(svg, { W: WD, H: HD, M: { l: 62, r: 16, t: 20, b: 32 }, x: [-0.5, d.orden.length - 0.5], y: d.ybar,
                           xcat: d.orden, ty: 'C necesario (%)', fy: (t) => f2(t) });
    g.barras = d.orden.map((k) => ({ r: el('rect', { fill: d.color[k], rx: 3 }, g.capa), t: el('text', { 'text-anchor': 'middle', class: 'tit' }, g.arriba) }));
    g.cero = el('line', { x1: 62, x2: WD - 16, class: 'guia' }, g.capa);
    return g;
  })());
  const ancho = (g.px(1) - g.px(0)) * 0.62, y0 = g.py(0);
  g.cero.setAttribute('y1', y0); g.cero.setAttribute('y2', y0);
  const tope = d.ybar[1] - 0.04;
  res.forEach((r, i) => {
    const corta = r.c > tope, y = g.py(Math.min(r.c, tope)), b = g.barras[i];
    b.r.setAttribute('x', g.px(i) - ancho / 2); b.r.setAttribute('width', ancho);
    b.r.setAttribute('y', Math.min(y, y0)); b.r.setAttribute('height', Math.max(1, Math.abs(y0 - y)));
    b.r.setAttribute('fill-opacity', r.conf ? 1 : .3);
    b.r.setAttribute('data-tip', `${r.k}<br>C necesario = ${f2(r.c)} %<br>${r.nota}`);
    b.t.setAttribute('x', g.px(i));
    b.t.setAttribute('y', corta ? y + 18 : (r.c >= 0 ? Math.min(y, y0) - 7 : Math.max(y, y0) + 16));
    b.t.style.fill = corta ? 'var(--t-texto)' : 'var(--t-suave)';
    b.t.textContent = (corta ? '↑ ' : '') + f2(r.c) + ' % C';
  });
}
export default function (component) {
  const { data, parentElement, setStateValue } = component;
  const root = parentElement;
  const input = root.querySelector('.sl-in');
  activarTips(root, root.querySelector('.g'));
  if (root._obj === undefined) root._obj = data.obj;
  input.value = root._obj;
  input.oninput = () => { root._obj = Number(input.value); dibujarDis(root, data, root._obj); };
  input.onchange = () => setStateValue('obj', Number(input.value));  // recordar el valor
  root._dataDis = data;
  // Recalcular el tamaño al mostrar la pestaña, abrir la tabla o cambiar la ventana
  if (!root._obsDis) {
    const rehacer = () => requestAnimationFrame(() => dibujarDis(root, root._dataDis, root._obj));
    root._obsDis = new ResizeObserver(rehacer);
    root._obsDis.observe(root.querySelector('.raiz'));
    window.addEventListener('resize', rehacer);
  }
  dibujarDis(root, data, root._obj);
}
"""

# ----------------------------------------------------------------------------
# Datos reales
# ----------------------------------------------------------------------------
_HTML_REAL = """
<div class="raiz">
  <h3 class="h3"></h3>
  <table class="tb"></table>
  <div class="cap">Mediana de los registros de cada acero (por ejemplo, el normalizado aparece en cuatro diámetros).</div>
  <p class="frase"></p>
</div>
"""
_CSS_REAL = """
.raiz { container-type: inline-size; }
/* Título en un solo renglón: la letra se reduce un poco si el ancho no alcanza */
.h3 { font-size: min(1.75rem, calc(100cqi / 37)); white-space: nowrap; font-weight: 600; line-height: 1.2;
      margin: 4px 0 14px; letter-spacing: -.005em; }
.frase { font-size: 16px; line-height: 1.6; margin: 10px 0 4px; }
.cap { font-size: 12.5px; }  /* nota de la mediana, un poco más pequeña */
/* Tabla de aceros más parecidos compacta, con los títulos de columna centrados */
.tb { font-size: 12px; margin: 2px 0; }
.tb th, .tb td { padding: 3px 10px; }
.tb th, .tb th.n { text-align: center; }
.tb tr.cerca td { background: var(--st-yellow-background-color, rgba(255, 215, 0, .16)); font-weight: 600; }
"""
_JS_REAL = """
function dibujarReal(root, d, c) {
  root.querySelector('.h3').textContent = `Aceros reales más parecidos (${d.cnd}, cerca de ${f2(c)} % C)`;
  const cerca = d.aceros[d.cnd].map((a, i) => ({ ...a, dist: Math.abs(a.C - c), i }))
    .sort((a, b) => a.dist - b.dist || a.i - b.i).slice(0, 5);
  root.querySelector('.tb').innerHTML =
    '<tr><th>Acero</th><th class="n">C</th><th class="n">Mn</th><th class="n">UTS</th><th class="n">YS</th>'
    + '<th class="n">Ductilidad</th><th class="n">registros</th></tr>'
    + cerca.map((a, j) => `<tr${j === 0 ? ' class="cerca"' : ''}><td>${a.acero}</td><td class="n">${a.C.toFixed(3)}</td>`
      + `<td class="n">${f2(a.Mn)}</td><td class="n">${f0(a.UTS)}</td><td class="n">${f0(a.YS)}</td>`
      + `<td class="n">${f1(a.DU)}</td><td class="n">${a.n}</td></tr>`).join('');
  const real = cerca[0], p = predecir(d.modelos[d.cnd], c), dif = p.UTS - real.UTS;
  root.querySelector('.frase').innerHTML = `El más cercano es <b>${real.acero}</b> con <b>${f0(real.UTS)} MPa</b>; `
    + `la recta predice ${f0(p.UTS)} MPa para ${f2(c)} % C (diferencia de ${dif >= 0 ? '+' : '−'}${f0(Math.abs(dif))} MPa).`;
}
export default function (component) {
  const { data, parentElement } = component;
  return conectar(parentElement, data, dibujarReal);
}
"""

_real = st.components.v2.component('datos_reales_vivo', html=_HTML_REAL, css=_CSS_COMUN + _CSS_REAL,
                                   js=_JS_COMUN + _JS_REAL)
_prop = st.components.v2.component('propiedades_vivo', html=_HTML_PROP, css=_CSS_COMUN + _CSS_PROP + _CSS_RK,
                                   js=_JS_COMUN + _JS_PROP)
_comp = st.components.v2.component('compromiso_vivo', html=_HTML_COMP, css=_CSS_COMUN + _CSS_COMP,
                                   js=_JS_COMUN + _JS_COMP)
_dis = st.components.v2.component('diseno_vivo', html=_HTML_DIS, css=_CSS_COMUN + _CSS_DIS + _CSS_RK,
                                  js=_JS_COMUN + _JS_DIS)


@st.cache_data
def _base(_datos, _modelos, firma):
    """Datos y rectas en formato JSON para el navegador (se calcula una vez)."""
    puntos, aceros, mods = {}, {}, {}
    for k in an.ORDEN:
        d = _datos[_datos['Condición'] == k]
        puntos[k] = {'C': d['C'].round(4).tolist(), 'UTS': d[an.UTS].tolist(), 'YS': d[an.YS].tolist(),
                     'DU': d[an.DU].tolist(), 'acero': d['Acero'].tolist()}
        pa = an.aceros_cercanos(_datos, k, 0.0, n=10_000)
        aceros[k] = [{'acero': r.Acero, 'C': float(r.C), 'Mn': float(r.Mn), 'UTS': float(r.UTS), 'YS': float(r.YS),
                      'DU': float(r.Ductilidad), 'n': int(r.registros)} for r in pa.itertuples()]
        mods[k] = {c: float(v) for c, v in _modelos.loc[k].items() if isinstance(v, (int, float, np.number))}
    # Eje fijo del diseño inverso: cubre todo el rango del deslizador (400–1000 MPa)
    cs = [(u - mods[k]['a_UTS']) / mods[k]['b_UTS'] for k in an.ORDEN for u in (400, 1000)]
    # (tope en 1.3 % C: las barras que lo superan se cortan y se marcan con ↑)
    ybar = [min(0.0, min(cs) - 0.05), 1.3]
    return {'orden': an.ORDEN, 'color': an.COLOR, 'eut': an.C_EUT, 'puntos': puntos,
            'aceros': aceros, 'modelos': mods, 'ybar': ybar}


def _datos_base(datos, modelos):
    return _base(datos, modelos, (len(datos), tuple(modelos.index)))


def propiedades(datos, modelos, cnd: str, c: float):
    m = modelos.loc[cnd]
    texto = (f'Recta de {cnd}: UTS = {m["a_UTS"]:.0f} + {m["b_UTS"]:.0f}·C  (R² = {m["R2_UTS"]:.2f}, '
             f'{int(m["aceros"])} aceros). Por cada 0.1 % de C la UTS sube ≈{m["b_UTS"] / 10:.0f} MPa y la '
             f'ductilidad baja ≈{-m["b_DU"] / 10:.1f} puntos.')
    _prop(key='propiedades_vivo', data={**_datos_base(datos, modelos), 'cnd': cnd, 'c': float(c),
                                         'texto_modelo': texto})


def datos_reales(datos, modelos, cnd: str, c: float):
    _real(key='datos_reales_vivo', data={**_datos_base(datos, modelos), 'cnd': cnd, 'c': float(c)})


def compromiso(datos, modelos, cnd: str, c: float):
    _comp(key='compromiso_vivo', data={**_datos_base(datos, modelos), 'cnd': cnd, 'c': float(c)})


def diseno_inverso(datos, modelos):
    estado = st.session_state.get('diseno_vivo') or {}
    obj = int(estado.get('obj') or 650)
    _dis(key='diseno_vivo', data={**_datos_base(datos, modelos), 'obj': obj},
         default={'obj': 650}, on_obj_change=lambda: None)


# ----------------------------------------------------------------------------
# Desplazamiento automático al abrir un desplegable
# ----------------------------------------------------------------------------
_JS_AUTODESPL = """
// Contenedor que desplaza la página (en Streamlit es stMain)
function desplazable(e) {
  for (let x = e.parentElement; x; x = x.parentElement) {
    const o = getComputedStyle(x).overflowY;
    if (o === 'auto' || o === 'scroll') return x;
  }
  return document.scrollingElement;
}
// Posición de destino: la parte de arriba del elemento `destino` en el borde superior
function calcular(det, sc, d) {
  const marca = document.querySelector(d.destino);
  if (!marca || !det.getClientRects().length) return null;
  const r0 = sc.getBoundingClientRect().top;
  const abs = (el) => el.getBoundingClientRect().top - r0 + sc.scrollTop;
  const destino = Math.max(0, abs(marca) - d.margen);
  // Alto disponible para la tabla: que el desplegable termine justo al borde inferior
  const sum = det.querySelector('summary').getBoundingClientRect().height;
  const libre = sc.clientHeight - d.abajo - (abs(det) - destino) - sum - d.relleno;
  return { destino, alto: Math.max(d.minimo, Math.floor(libre)) };
}
function ajustar(det, sc, d) {
  const c = calcular(det, sc, d), caja = det.querySelector(d.ajustar);
  if (c && caja) caja.style.maxHeight = c.alto + 'px';
  return c;
}
// Deslizamiento suave (misma curva y duración que la apertura del desplegable)
function deslizar(sc, destino, dur) {
  const ini = sc.scrollTop, t0 = performance.now();
  const curva = (k) => 1 - Math.pow(1 - k, 3);
  const paso = (t) => {
    const k = Math.min(1, (t - t0) / dur);
    sc.scrollTop = ini + (destino - ini) * curva(k);
    // Si la página aún no es lo bastante alta (sigue abriéndose), insistir un poco más
    if (k < 1 || (Math.abs(sc.scrollTop - destino) > 1 && t - t0 < dur + 600)) requestAnimationFrame(paso);
  };
  requestAnimationFrame(paso);
}
export default function (component) {
  const { data, parentElement } = component;
  const exp = parentElement.closest('[data-testid="stExpander"]');
  const det = exp && exp.querySelector('details');
  if (!det) return;
  det._datos = data;
  const sc = desplazable(det);
  ajustar(det, sc, data);
  if (det._autoDespl) return;
  det._autoDespl = true;
  window.addEventListener('resize', () => ajustar(det, sc, det._datos));
  // Empezar a deslizar en el mismo clic que abre el desplegable
  det.querySelector('summary').addEventListener('click', () => {
    if (det.open) {  // se está cerrando: volver a donde estaba la página antes de abrir
      if (det._antes !== undefined && sc.scrollTop > det._antes + 1) {
        const blk = sc.querySelector('[data-testid="stMainBlockContainer"]');
        if (blk) {  // espacio temporal para que el navegador no la regrese de golpe al encoger
          blk.style.paddingBottom = `calc(1.5rem + ${Math.ceil(sc.scrollTop - det._antes) + 80}px)`;
          setTimeout(() => { blk.style.paddingBottom = ''; }, det._datos.duracion + 250);
        }
        deslizar(sc, det._antes, det._datos.duracion);
      }
      return;
    }
    det._antes = sc.scrollTop;
    const c = ajustar(det, sc, det._datos);
    if (!c) return;
    // Espacio extra temporal al final de la página para poder deslizar desde el primer
    // instante (si no, hay que esperar a que el desplegable crezca)
    const blk = sc.querySelector('[data-testid="stMainBlockContainer"]');
    if (blk) {
      blk.style.paddingBottom = `calc(1.5rem + ${c.alto + 80}px)`;
      setTimeout(() => { blk.style.paddingBottom = ''; }, det._datos.duracion + 250);
    }
    deslizar(sc, c.destino, det._datos.duracion);
  });
}
"""
_autodespl = st.components.v2.component('auto_desplazar', js=_JS_AUTODESPL, isolate_styles=False)


def auto_desplazar(key: str, destino: str, ajustar: str):
    """Colocar dentro de un st.expander: al abrirlo, la pantalla se desliza a la vez hasta
    que el elemento `destino` (selector CSS) queda arriba, y el elemento `ajustar` toma
    el alto justo para que el desplegable completo quepa en la pantalla."""
    _autodespl(key=key, height=0, data={'destino': destino, 'ajustar': ajustar, 'margen': 4,
                                        'abajo': 24, 'relleno': 36, 'minimo': 120, 'duracion': 420})
