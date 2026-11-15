"""Regla de la palanca (justo debajo de 727 °C) con actualización en tiempo real.

Se calcula y dibuja en el navegador, igual que la micrografía, así que los
porcentajes y las fórmulas cambian al instante mientras se arrastra el
deslizador de carbono. Los porcentajes y las fórmulas están en una sección desplegable (botón
con flecha, como las tablas de las demás pestañas).
"""
import streamlit as st

from tema import TEMA_CSS
from analisis import C_ALFA, C_CEM, C_EUT

_HTML = """
<div class="rp">
  <div class="rp-cab">
    <h3 class="rp-tit">Regla de la palanca (justo debajo de 727 °C)</h3>
    <button class="rp-bt" type="button" title="Mostrar la regla de la palanca" aria-label="Mostrar la regla de la palanca" aria-expanded="false">
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 9l6 6 6-6"/></svg>
    </button>
  </div>
  <div class="rp-mas"><div class="rp-in">
    <div class="rp-met">
      <div><div class="et">Ferrita proeutectoide</div><div class="val v-f"></div></div>
      <div><div class="et">Perlita</div><div class="val v-p"></div></div>
      <div><div class="et">Cementita proeutectoide</div><div class="val v-c"></div></div>
    </div>
    <div class="rp-form f-perlita"></div>
    <div class="rp-form f-otra"></div>
  </div></div>
</div>
"""

_CSS = TEMA_CSS + """
.rp { font-family: var(--st-font, sans-serif); color: var(--st-text-color); }
/* Título con el botón a su derecha */
.rp-cab { display: flex; align-items: center; gap: 12px; margin: 0; }
.rp-met { padding-top: 14px; }
.rp-tit { margin: 0; font-size: 1.75rem; font-weight: 600; line-height: 1.2; letter-spacing: -.005em;
          font-family: var(--st-heading-font, var(--st-font, sans-serif)); color: var(--st-heading-color, var(--st-text-color)); }
.rp-met { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
.et { font-size: 14px; margin-bottom: 4px; }
.val { font-size: 36px; line-height: 1.2; font-variant-numeric: tabular-nums; }
/* Botón para desplegar (flecha abajo) y guardar (flecha a la izquierda) las fórmulas */
.rp-bt { flex: none; width: 28px; height: 28px; padding: 0; display: grid; place-items: center;
         border-radius: 50%; cursor: pointer; border: 1px solid var(--t-borde); background: var(--t-fondo);
         color: var(--t-texto); transition: background .2s, color .2s, border-color .2s, transform .15s, box-shadow .2s; }
.rp-bt:hover { background: var(--st-primary-color); color: #fff; border-color: transparent;
               transform: scale(1.1); box-shadow: 0 2px 8px rgba(0,0,0,.25); }
.rp-bt:active { transform: scale(.94); }
.rp-bt:focus-visible { outline: 2px solid var(--st-primary-color); outline-offset: 2px; }
.rp-bt svg { width: 16px; height: 16px; fill: none; stroke: currentColor; stroke-width: 2.4;
             stroke-linecap: round; stroke-linejoin: round; transition: transform .3s ease; }
.rp.abierta .rp-bt svg { transform: rotate(90deg); }
.rp-mas { display: grid; grid-template-rows: 0fr; transition: grid-template-rows .3s ease; }
.rp.abierta .rp-mas { grid-template-rows: 1fr; }
.rp-in { overflow: hidden; min-height: 0; }
.rp-form { display: flex; justify-content: center; align-items: center; flex-wrap: wrap; gap: 10px;
           margin: 18px 0 4px; font-family: 'Times New Roman', Times, serif; font-size: 21px; }
.fr { display: inline-flex; flex-direction: column; align-items: center; vertical-align: middle; }
.fr > span { padding: 0 6px; white-space: nowrap; }
.fr > span:first-child { border-bottom: 1px solid currentColor; padding-bottom: 2px; }
.fr > span:last-child { padding-top: 2px; }
.m { font-style: italic; }
.n { font-variant-numeric: tabular-nums; }
"""

_JS = """
function fracciones(c, k) {
  let fp = c <= k.eut ? (c - k.alfa) / (k.eut - k.alfa) : (k.cem - c) / (k.cem - k.eut);
  fp = Math.min(1, Math.max(0, fp));
  return { f: c <= k.eut ? 1 - fp : 0, p: fp, c: c <= k.eut ? 0 : 1 - fp };
}
const frac = (a, b) => `<span class="fr"><span>${a}</span><span>${b}</span></span>`;
const sub = (s) => `<span><span class="m">f</span><sub>${s}</sub></span>`;

function dibujar(root, k, c) {
  const fr = fracciones(c, k);
  const pct = (v) => Math.round(v * 100) + '%';
  root.querySelector('.v-f').textContent = pct(fr.f);
  root.querySelector('.v-p').textContent = pct(fr.p);
  root.querySelector('.v-c').textContent = pct(fr.c);
  const cs = `<span class="n">${Number(c).toFixed(2)}</span>`;
  const f = (v) => Math.max(0, v).toFixed(3);
  const C = '<span class="m">C</span>';
  let perlita, otra;
  if (c <= k.eut) {
    // Hipoeutectoide: perlita y ferrita proeutectoide
    perlita = `${sub('perlita')} = ${frac(C + ' − 0.022', '0.76 − 0.022')} = `
            + `${frac(cs + ' − 0.022', '0.738')} = <span class="n">${f(fr.p)}</span>`;
    otra = `${sub('ferrita')} = ${frac('0.76 − ' + C, '0.76 − 0.022')} = `
         + `${frac('0.76 − ' + cs, '0.738')} = <span class="n">${f(fr.f)}</span>`;
  } else {
    // Hipereutectoide: perlita y cementita proeutectoide
    perlita = `${sub('perlita')} = ${frac('6.70 − ' + C, '6.70 − 0.76')} = `
            + `${frac('6.70 − ' + cs, '5.94')} = <span class="n">${f(fr.p)}</span>`;
    otra = `${sub('Fe₃C')} = ${frac(C + ' − 0.76', '6.70 − 0.76')} = `
         + `${frac(cs + ' − 0.76', '5.94')} = <span class="n">${f(fr.c)}</span>`;
  }
  root.querySelector('.f-perlita').innerHTML = perlita;
  root.querySelector('.f-otra').innerHTML = otra;
}

// Deslizamiento suave de la página (al desplegar, lo necesario para ver las fórmulas;
// al guardar, de vuelta a donde estaba)
function deslizar(destino, dur) {
  const sc = document.querySelector('[data-testid="stMain"]');
  if (!sc) return;
  const blk = sc.querySelector('[data-testid="stMainBlockContainer"]');
  if (blk) {  // espacio temporal para poder deslizar desde el primer instante
    blk.style.paddingBottom = 'calc(1.5rem + 220px)';
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

export default function (component) {
  const { data, parentElement } = component;
  const root = parentElement;
  root._k = data.k;
  const rp = root.querySelector('.rp'), bt = root.querySelector('.rp-bt');
  rp.classList.toggle('abierta', !!root._abierta);
  bt.onclick = () => {
    root._abierta = !root._abierta;
    rp.classList.toggle('abierta', root._abierta);
    const t = root._abierta ? 'Guardar la regla de la palanca' : 'Mostrar la regla de la palanca';
    bt.title = t; bt.setAttribute('aria-label', t); bt.setAttribute('aria-expanded', root._abierta);
    const sc = document.querySelector('[data-testid="stMain"]');
    if (!sc) return;
    if (root._abierta) {
      root._antes = sc.scrollTop;
      const fin = rp.getBoundingClientRect().bottom + root.querySelector('.rp-in').scrollHeight;
      const falta = fin - (window.innerHeight - 24);
      if (falta > 0) deslizar(sc.scrollTop + falta, 300);
    } else if (root._antes !== undefined && sc.scrollTop > root._antes + 1) {
      deslizar(root._antes, 300);
    }
  };
  if (!root._oyente) {
    root._oyente = (e) => { root._cLocal = e.detail; dibujar(root, root._k, e.detail); };
    window.addEventListener('carbono-cambia', root._oyente);
  }
  const c = window.__arrastrandoCarbono && root._cLocal !== undefined ? root._cLocal : data.c;
  if (!window.__arrastrandoCarbono) root._cLocal = undefined;
  dibujar(root, data.k, c);
  return () => {
    window.removeEventListener('carbono-cambia', root._oyente);
    root._oyente = null;
  };
}
"""

_componente = st.components.v2.component('regla_palanca', html=_HTML, css=_CSS, js=_JS)


def regla_palanca(c: float, key: str = 'regla_palanca'):
    """Muestra las fracciones de fase y, desplegando, las fórmulas de la regla de la palanca."""
    _componente(key=key, data={'c': float(c), 'k': {'eut': C_EUT, 'alfa': C_ALFA, 'cem': C_CEM}})
