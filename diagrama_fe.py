"""Diagrama Fe–Fe3C (zona del acero) con actualización en tiempo real.

Se dibuja en el navegador como SVG, igual que la micrografía y la regla de la
palanca: la línea del acero, las temperaturas críticas y el texto inferior se
mueven al instante mientras se arrastra el deslizador de carbono.
"""
import streamlit as st

from tema import TEMA_CSS
from analisis import C_EUT, C_GAMMA_MAX, T_A3_0, T_EUT, T_EUTECTICO

_HTML = """
<div class="fe">
  <svg class="fe-svg" viewBox="0 0 520 420" role="img" aria-label="Diagrama Fe–Fe3C"></svg>
  <div class="fe-cap"></div>
</div>
"""

_CSS = TEMA_CSS + """
.fe { font-family: var(--st-font, sans-serif); color: var(--st-text-color); }
.fe-svg { display: block; width: 100%; height: auto; margin: 0 auto; }
.fe-svg text { font-family: var(--st-font, sans-serif); }
.eje { font-size: 12px; fill: var(--t-suave); }
.tit { font-size: 13px; fill: var(--t-suave); }
.zona { font-size: 14px; fill: var(--t-suave); }
/* Colores de las líneas del diagrama (distintos de los colores de las condiciones) */
.fe { --c-a3: #E0A100; --c-acm: #D63384; --c-a1: #3B82F6; }
.l-a3 { stroke: var(--c-a3); }
.l-acm { stroke: var(--c-acm); }
.l-a1 { stroke: var(--c-a1); }
.a1 { font-size: 12px; fill: var(--c-a1); font-weight: 600; }
.et-a3 { font-size: 12px; font-weight: 600; fill: var(--c-a3); }
.et-acm { font-size: 12px; font-weight: 600; fill: var(--c-acm); }
.temp { font-size: 12.5px; font-weight: 600; paint-order: stroke; stroke: var(--t-fondo); stroke-width: 4px; }
.pt { stroke: var(--t-fondo); }
.fe-cap { font-size: 12px; opacity: .65; margin-top: 4px; line-height: 1.5; }
.fe-cap b { font-weight: 600; }
/* Diagrama interactivo: arrastrar (o hacer clic) mueve el acero */
.fe-svg { cursor: ew-resize; touch-action: pan-y; user-select: none; -webkit-user-select: none; }  /* en táctil: vertical = desplazar la página */
.fe-svg.arrastrando { cursor: grabbing; }
.pt { cursor: grab; }
"""

_JS = """
const W = 520, H = 420, M = { l: 58, r: 14, t: 14, b: 50 };
const XMIN = 0, XMAX = 1.4, YMIN = 600, YMAX = 1000;
const px = (c) => M.l + (c - XMIN) / (XMAX - XMIN) * (W - M.l - M.r);
const py = (t) => H - M.b - (t - YMIN) / (YMAX - YMIN) * (H - M.t - M.b);
const NS = 'http://www.w3.org/2000/svg';

function el(tag, attrs, padre, texto) {
  const e = document.createElementNS(NS, tag);
  for (const k in attrs) e.setAttribute(k, attrs[k]);
  if (texto !== undefined) e.textContent = texto;
  padre.appendChild(e);
  return e;
}

function temperaturas(c, k) {
  if (c <= k.eut) return { a1: k.teut, a3: k.ta3 - (k.ta3 - k.teut) * c / k.eut, nom: 'A3' };
  return { a1: k.teut, a3: k.teut + (k.teutect - k.teut) * (c - k.eut) / (k.gmax - k.eut), nom: 'Acm' };
}

function construir(svg, k) {
  svg.innerHTML = '';
  const fondo = el('g', {}, svg);
  // Rejilla y ejes
  for (let t = YMIN; t <= YMAX; t += 50) {
    el('line', { x1: M.l, x2: W - M.r, y1: py(t), y2: py(t), class: 'rej' }, fondo);
    el('text', { x: M.l - 8, y: py(t) + 4, 'text-anchor': 'end', class: 'eje' }, fondo, t);
  }
  for (const c of [0, 0.25, 0.5, 0.75, 1, 1.25]) {
    el('line', { x1: px(c), x2: px(c), y1: M.t, y2: H - M.b, class: 'rej2' }, fondo);
    el('text', { x: px(c), y: H - M.b + 18, 'text-anchor': 'middle', class: 'eje' }, fondo, String(c));
  }
  el('text', { x: (M.l + W - M.r) / 2, y: H - 10, 'text-anchor': 'middle', class: 'tit' }, fondo, 'C (% en peso)');
  el('text', { x: 16, y: (M.t + H - M.b) / 2, 'text-anchor': 'middle', class: 'tit',
               transform: `rotate(-90 16 ${(M.t + H - M.b) / 2})` }, fondo, 'T (°C)');
  // Línea eutectoide vertical
  el('line', { x1: px(k.eut), x2: px(k.eut), y1: M.t, y2: H - M.b, class: 'guia', 'stroke-dasharray': '3 4' }, fondo);
  // A3 (continua) y Acm (discontinua), recortadas al área del gráfico
  const clip = el('clipPath', { id: 'fe-clip' }, el('defs', {}, svg));
  el('rect', { x: M.l, y: M.t, width: W - M.l - M.r, height: H - M.t - M.b }, clip);
  const curvas = el('g', { 'clip-path': 'url(#fe-clip)' }, svg);
  el('line', { x1: px(0), y1: py(k.ta3), x2: px(k.eut), y2: py(k.teut), class: 'l-a3', 'stroke-width': 2.5 }, curvas);
  const tAcm = temperaturas(XMAX, k).a3;
  el('line', { x1: px(k.eut), y1: py(k.teut), x2: px(XMAX), y2: py(tAcm), class: 'l-acm',
               'stroke-width': 2.5, 'stroke-dasharray': '7 5' }, curvas);
  // A1
  el('line', { x1: M.l, x2: W - M.r, y1: py(k.teut), y2: py(k.teut), class: 'l-a1', 'stroke-width': 2 }, svg);
  el('text', { x: W - M.r - 4, y: py(k.teut) + 16, 'text-anchor': 'end', class: 'a1' }, svg, 'A1 = 727 °C');
  // Zonas
  const zonas = [];
  for (const [c, t, s] of [[0.55, 950, 'γ (austenita)'], [0.15, 790, 'α + γ'], [1.15, 790, 'γ + Fe₃C'],
                           [0.30, 650, 'α + perlita'], [1.10, 650, 'perlita + Fe₃C']]) {
    zonas.push(el('text', { x: px(c), y: py(t), 'text-anchor': 'middle', class: 'zona' }, svg, s));
  }
  // Nombres de las líneas A3 y Acm, en su color
  zonas.push(el('text', { x: px(0.04), y: py(temperaturas(0.04, k).a3) - 9, class: 'et-a3' }, svg, 'A3'));
  zonas.push(el('text', { x: px(1.22), y: py(temperaturas(1.32, k).a3), 'text-anchor': 'end', class: 'et-acm' }, svg, 'Acm'));
  // Elementos que se mueven con el carbono
  const mov = el('g', {}, svg);
  const g = {
    linea: el('line', { y1: M.t, y2: H - M.b, 'stroke-width': 3 }, mov),
    p1: el('circle', { r: 6, class: 'pt', stroke: '#fff', 'stroke-width': 1.5 }, mov),
    p3: el('circle', { r: 6, class: 'pt', stroke: '#fff', 'stroke-width': 1.5 }, mov),
    t1: el('text', { class: 'temp' }, mov),
    t3: el('text', { class: 'temp' }, mov),
  };
  g.tt1 = el('title', {}, g.p1); g.tt3 = el('title', {}, g.p3);
  g.zonas = zonas;
  return g;
}

function dibujar(root, cfg, c) {
  const g = root._g, k = cfg.k, T = temperaturas(c, k);
  const x = px(c);
  g.linea.setAttribute('x1', x); g.linea.setAttribute('x2', x); g.linea.setAttribute('stroke', cfg.color);
  for (const [p, tt, t] of [[g.p1, g.tt1, T.a1], [g.p3, g.tt3, T.a3]]) {
    p.setAttribute('cx', x); p.setAttribute('cy', py(t)); p.setAttribute('fill', cfg.color);
    tt.textContent = Math.round(t) + ' °C';
  }
  // Etiquetas junto a los puntos (al lado contrario si el acero está muy a la derecha)
  const der = c < 1.0, dx = der ? 10 : -10, anc = der ? 'start' : 'end';
  for (const [t, y, s] of [[g.t1, py(T.a1) + 17, 'A1 ' + Math.round(T.a1) + ' °C'],
                           [g.t3, py(T.a3) - 9, T.nom + ' ' + Math.round(T.a3) + ' °C']]) {
    t.setAttribute('x', x + dx); t.setAttribute('y', y); t.setAttribute('text-anchor', anc);
    t.setAttribute('fill', cfg.color); t.textContent = s;
  }
  // Atenuar el nombre de una zona si una etiqueta de temperatura le pasa por encima
  const cajas = [g.t1.getBBox(), g.t3.getBBox()];
  const choca = (a, b) => a.x < b.x + b.width + 4 && b.x < a.x + a.width + 4 && a.y < b.y + b.height && b.y < a.y + a.height;
  for (const z of g.zonas) {
    const bz = z.getBBox();
    z.style.opacity = cajas.some((b) => choca(b, bz)) ? 0 : 1;
  }
  root.querySelector('.fe-cap').innerHTML =
    `Temperaturas críticas: <b>A1 = ${Math.round(T.a1)} °C</b>, <b>${T.nom} ≈ ${Math.round(T.a3)} °C</b> `
    + '(líneas rectas, aproximación esquemática).';
}

// Espacio que se reserva debajo de las figuras para el título de "Regla de la palanca"
const RESERVA_PALANCA = 34 + 16;
// Tamaño del diagrama: el natural (ancho de la columna), salvo que no quepa en la pantalla
// junto con su nota y el título de la regla de la palanca; entonces se achica
function ajustarTamano(root) {
  const svg = root.querySelector('.fe-svg'), cap = root.querySelector('.fe-cap');
  if (!svg.getClientRects().length) return;  // pestaña oculta
  const sc = document.querySelector('[data-testid="stMain"]') || document.scrollingElement;
  const arriba = svg.getBoundingClientRect().top - sc.getBoundingClientRect().top + sc.scrollTop;
  // Solo cuenta lo que va debajo del propio diagrama (su nota): así puede ser más grande
  const debajo = cap.getBoundingClientRect().height + 4;
  const maxAlto = sc.clientHeight - arriba - debajo - RESERVA_PALANCA - 24 - 6;
  const v = Math.max(260, Math.floor(maxAlto * W / H)) + 'px';
  if (svg.style.maxWidth !== v) svg.style.maxWidth = v;
}
export default function (component) {
  const { data, parentElement } = component;
  const root = parentElement;
  if (!root._g) root._g = construir(root.querySelector('.fe-svg'), data.k);
  ajustarTamano(root);
  // Recalcular cuando la página termina de acomodarse y al cambiar el tamaño de la ventana
  requestAnimationFrame(() => ajustarTamano(root));
  setTimeout(() => ajustarTamano(root), 400);
  if (!root._resize) { root._resize = () => ajustarTamano(root); window.addEventListener('resize', root._resize); }
  root._cfg = data;
  // Arrastrar en el diagrama mueve el carbono (el deslizador aplica el valor)
  const svg = root.querySelector('.fe-svg');
  if (!svg._arrastre) {
    svg._arrastre = true;
    const pedir = (e, extra) => {
      const r = svg.getBoundingClientRect();
      const x = (e.clientX - r.left) * W / r.width;
      const c = XMIN + (x - M.l) / (W - M.l - M.r) * (XMAX - XMIN);
      window.dispatchEvent(new CustomEvent('carbono-pedir', { detail: { valor: c, ...extra } }));
    };
    svg.addEventListener('pointerdown', (e) => {
      if (e.button !== 0) return;
      e.preventDefault(); svg.setPointerCapture(e.pointerId);
      svg._activo = true; svg.classList.add('arrastrando'); pedir(e, { inicio: true });
    });
    // Movimientos agrupados: como máximo uno por cuadro de pantalla (más fluido)
    svg.addEventListener('pointermove', (e) => {
      if (!svg._activo) return;
      svg._ultimoEv = e;
      if (!svg._cuadro) svg._cuadro = requestAnimationFrame(() => { svg._cuadro = 0; if (svg._activo) pedir(svg._ultimoEv, {}); });
    });
    const soltar = (e) => { if (!svg._activo) return; svg._activo = false; svg.classList.remove('arrastrando'); pedir(e, { fin: true }); };
    svg.addEventListener('pointerup', soltar);
    svg.addEventListener('pointercancel', soltar);
  }
  if (!root._oyente) {
    root._oyente = (e) => { root._cLocal = e.detail; dibujar(root, root._cfg, e.detail); };
    window.addEventListener('carbono-cambia', root._oyente);
  }
  const c = window.__arrastrandoCarbono && root._cLocal !== undefined ? root._cLocal : data.c;
  if (!window.__arrastrandoCarbono) root._cLocal = undefined;
  dibujar(root, data, c);
  return () => {
    window.removeEventListener('carbono-cambia', root._oyente);
    root._oyente = null;
  };
}
"""

_componente = st.components.v2.component('diagrama_fe', html=_HTML, css=_CSS, js=_JS)


def diagrama_fe(c: float, color: str, key: str = 'diagrama_fe'):
    """Diagrama Fe–Fe3C esquemático con la línea del acero de `c` % C (color de la condición)."""
    _componente(key=key, data={
        'c': float(c), 'color': color,
        'k': {'eut': C_EUT, 'teut': T_EUT, 'ta3': T_A3_0, 'teutect': T_EUTECTICO, 'gmax': C_GAMMA_MAX},
    })
