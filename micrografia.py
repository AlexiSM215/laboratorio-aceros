"""Micrografía esquemática (sin escala) de un acero al carbono enfriado lentamente.

Se dibuja directamente en el navegador (canvas), así que se actualiza al
instante mientras se arrastra el deslizador de carbono, sin parpadeos.

Granos generados con un teselado de Voronoi. Cada grano es ferrita (claro)
o perlita (láminas alternas de ferrita y cementita). La fracción de área de
perlita sigue la regla de la palanca. En los hipereutectoides aparece una
red de cementita proeutectoide en los bordes de grano. El espaciado de las
láminas y el tamaño de grano dependen del procesamiento.
"""
import streamlit as st

from tema import TEMA_CSS
from analisis import C_ALFA, C_CEM, C_EUT

# Espaciado interlaminar relativo (px): perlita gruesa en el recocido, fina en el normalizado
LAMINA = {'Recocido': 9.0, 'Laminado en caliente': 6.5, 'Normalizado': 4.5, 'Estirado en frío': 6.0}
# Número de granos (el normalizado refina el grano)
GRANOS = {'Recocido': 45, 'Laminado en caliente': 70, 'Normalizado': 110, 'Estirado en frío': 70}

_HTML = """
<div class="mg">
  <div class="mg-marco">
    <canvas class="mg-canvas" width="420" height="420"></canvas>
    <div class="mg-c"></div>
  </div>
  <div class="mg-ley">
    <span><i class="sw sw-f"></i>Ferrita <b class="p-f"></b></span>
    <span><i class="sw sw-p"></i>Perlita <b class="p-p"></b></span>
    <span><i class="sw sw-c"></i>Cementita proeutectoide <b class="p-c"></b></span>
  </div>
</div>
"""

_CSS = TEMA_CSS + """
.mg { font-family: var(--st-font, sans-serif); color: var(--st-text-color); }
.mg-marco { position: relative; border-radius: 10px; overflow: hidden;
            box-shadow: 0 0 0 1px rgba(0,0,0,.12), 0 2px 10px rgba(0,0,0,.10); background: #e9e3d4; }
.mg-canvas { display: block; width: 100%; height: auto; aspect-ratio: 1 / 1; }
.mg-c { position: absolute; top: 10px; left: 10px; padding: 3px 9px; border-radius: 6px;
        background: rgba(20,20,20,.62); color: #fff; font-size: 13px; font-weight: 600; }
.mg-ley { display: flex; flex-wrap: wrap; justify-content: center; gap: 6px 16px; margin-top: 10px; font-size: 13px; }
.mg-ley span { display: inline-flex; align-items: center; gap: 6px; }
.mg-ley b { font-variant-numeric: tabular-nums; }
.sw { width: 14px; height: 14px; border-radius: 3px; display: inline-block; border: 1px solid rgba(0,0,0,.25); }
.sw-f { background: rgb(236,230,214); }
.sw-p { background: repeating-linear-gradient(45deg, rgb(70,58,52) 0 2px, rgb(194,189,175) 2px 4px); }
.sw-c { background: rgb(250,248,240); }
"""

_JS = """
const TAM = 420;
const FERRITA = [236, 230, 214], CEMENTITA = [250, 248, 240];
const OSCURO = [70, 58, 52], BORDE = [95, 85, 78];
const PERLITA_BASE = FERRITA.map((v) => v * 0.82);

function mulberry32(a) {
  return function () {
    a |= 0; a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// Geometría de granos (cara de calcular) -> se guarda por condición
const CACHE = (window.__mgCache = window.__mgCache || new Map());
function geometria(cfg) {
  const clave = cfg.condicion;
  if (CACHE.has(clave)) return CACHE.get(clave);
  const rnd = mulberry32(7);
  const estirado = cfg.condicion === 'Estirado en frío';
  const sy = estirado ? 0.35 : 1.0;
  const n = cfg.granos * (estirado ? 3 : 1);
  // Centros de grano con separación mínima: evita granos diminutos o superpuestos
  // que se verían como manchas sólidas oscuras o blancas
  const sx_ = new Float32Array(n), sy_ = new Float32Array(n);
  const H = TAM / sy, rmin2 = Math.pow(0.7 * Math.sqrt((TAM * H) / n), 2);
  for (let i = 0; i < n; i++) {
    let x, y, ok = false;
    for (let intento = 0; intento < 60 && !ok; intento++) {
      x = rnd() * TAM; y = rnd() * H; ok = true;
      for (let j = 0; j < i; j++) {
        const dx = x - sx_[j], dy = y - sy_[j];
        if (dx * dx + dy * dy < rmin2) { ok = false; break; }
      }
    }
    sx_[i] = x; sy_[i] = y;
  }

  const N = TAM * TAM;
  const etiqueta = new Uint16Array(N), borde = new Float32Array(N);
  for (let y = 0; y < TAM; y++) {
    const py = y / sy;
    for (let x = 0; x < TAM; x++) {
      let d1 = Infinity, d2 = Infinity, i1 = 0;
      for (let i = 0; i < n; i++) {
        const dx = x - sx_[i], dy = py - sy_[i];
        const d = dx * dx + dy * dy;
        if (d < d1) { d2 = d1; d1 = d; i1 = i; } else if (d < d2) { d2 = d; }
      }
      const k = y * TAM + x;
      etiqueta[k] = i1;
      borde[k] = (Math.sqrt(d2) - Math.sqrt(d1)) * sy;
    }
  }
  const areas = new Float64Array(n);
  for (let k = 0; k < N; k++) areas[etiqueta[k]]++;
  const orden = Array.from({ length: n }, (_, i) => i);
  for (let i = n - 1; i > 0; i--) { const j = Math.floor(rnd() * (i + 1)); [orden[i], orden[j]] = [orden[j], orden[i]]; }
  const acum = new Float64Array(n);
  let s = 0; for (let i = 0; i < n; i++) { s += areas[orden[i]]; acum[i] = s / N; }

  // Láminas de perlita con orientación aleatoria por grano (alineadas si está estirado)
  const ang = new Float32Array(n), fase = new Float32Array(n);
  for (let i = 0; i < n; i++) { ang[i] = rnd() * Math.PI * (estirado ? 0.25 : 1); fase[i] = rnd() * 2 * Math.PI; }
  const laminas = new Uint8Array(N);
  const w = (2 * Math.PI) / cfg.lamina;
  for (let y = 0; y < TAM; y++) for (let x = 0; x < TAM; x++) {
    const k = y * TAM + x, l = etiqueta[k];
    laminas[k] = Math.sin(w * (x * Math.cos(ang[l]) + y * Math.sin(ang[l])) + fase[l]) > 0.35 ? 1 : 0;
  }
  // Ligero ruido fijo (aspecto de imagen de microscopio)
  const ruido = new Float32Array(N);
  for (let k = 0; k < N; k++) ruido[k] = (rnd() + rnd() + rnd() - 1.5) * 7;

  const g = { n, etiqueta, borde, orden, acum, laminas, ruido };
  CACHE.set(clave, g);
  return g;
}

function fracciones(c, k) {
  let fp = c <= k.eut ? (c - k.alfa) / (k.eut - k.alfa) : (k.cem - c) / (k.cem - k.eut);
  fp = Math.min(1, Math.max(0, fp));
  return { f: c <= k.eut ? 1 - fp : 0, p: fp, c: c <= k.eut ? 0 : 1 - fp };
}

function dibujar(root, cfg, c) {
  const g = geometria(cfg);
  const fr = fracciones(c, cfg.k);
  const esP = new Uint8Array(g.n);
  // Hipereutectoide: todos los granos son perlita; la cementita va en los bordes
  if (fr.p >= 0.999 || fr.c > 0) esP.fill(1);
  else if (fr.p > 0) {
    let m = 0; while (m < g.n - 1 && g.acum[m] < fr.p - 1e-9) m++;
    for (let i = 0; i <= m; i++) esP[g.orden[i]] = 1;
  }
  const ancho = fr.c > 0 ? 1 + 60 * fr.c : 0;
  const canvas = root.querySelector('.mg-canvas');
  const ctx = canvas.getContext('2d');
  const img = root._img || (root._img = ctx.createImageData(TAM, TAM));
  const d = img.data;
  for (let k = 0, j = 0; k < TAM * TAM; k++, j += 4) {
    let col;
    const b = g.borde[k];
    if (b < 1.0) col = BORDE;
    else if (b < ancho) col = CEMENTITA;
    else if (esP[g.etiqueta[k]]) col = g.laminas[k] ? OSCURO : PERLITA_BASE;
    else col = FERRITA;
    const r = g.ruido[k];
    d[j] = col[0] + r; d[j + 1] = col[1] + r; d[j + 2] = col[2] + r; d[j + 3] = 255;
  }
  ctx.putImageData(img, 0, 0);
  const pct = (v) => Math.round(v * 100) + ' %';
  root.querySelector('.mg-c').textContent = Number(c).toFixed(2) + ' % C';
  root.querySelector('.p-f').textContent = pct(fr.f);
  root.querySelector('.p-p').textContent = pct(fr.p);
  root.querySelector('.p-c').textContent = pct(fr.c);
}

// La imagen mide lo mismo de alto que el diagrama Fe–Fe3C de la columna de al lado,
// para que las dos figuras terminen en el mismo pixel
function igualarAlDiagrama(root) {
  if (!root._fe || !root._fe.isConnected) {
    root._fe = null;
    for (const e of document.querySelectorAll('.st-key-diagrama_fe *')) {
      const s = e.shadowRoot && e.shadowRoot.querySelector('.fe-svg');
      if (s) { root._fe = s; break; }
    }
  }
  const fe = root._fe, mg = root.querySelector('.mg'), marco = root.querySelector('.mg-marco');
  if (!fe || !fe.getClientRects().length || !marco.getClientRects().length) return;
  // Lado del cuadro: desde donde empieza la imagen hasta donde termina el diagrama
  // (si el título del diagrama ocupa dos renglones, el diagrama empieza más abajo)
  const ancho = mg.parentElement ? mg.parentElement.getBoundingClientRect().width : Infinity;
  // Además, que la imagen, su leyenda y la nota de abajo quepan en la pantalla
  // (sin contar los avisos amarillos, que no deben encoger la imagen)
  const sc = document.querySelector('[data-testid="stMain"]') || document.scrollingElement;
  const host = root.getRootNode().host;
  const cont = host && host.closest('[data-testid="stElementContainer"]');
  const nota = cont && cont.nextElementSibling;
  const ley = root.querySelector('.mg-ley');
  const avisos = document.querySelector('.st-key-avisos');
  const debajo = (ley ? ley.getBoundingClientRect().height + 10 : 40)
               + (nota ? nota.getBoundingClientRect().height + 16 : 0) + 24 + 6;
  const arriba = marco.getBoundingClientRect().top - sc.getBoundingClientRect().top + sc.scrollTop
               - (avisos ? avisos.getBoundingClientRect().height : 0);
  const maxPantalla = sc.clientHeight - arriba - debajo - (34 + 16);  // + título de "Regla de la palanca"
  // Columnas una debajo de otra (pantallas angostas): la imagen queda bajo el diagrama, así
  // que no se alinea con él; toma un buen tamaño según el ancho disponible
  const apilada = marco.getBoundingClientRect().top >= fe.getBoundingClientRect().bottom - 1;
  const alto = apilada ? Math.round(Math.min(ancho, 480))
             : Math.round(Math.min(fe.getBoundingClientRect().bottom - marco.getBoundingClientRect().top,
                                   Math.max(200, maxPantalla)));
  if (alto <= 0) return;
  const lado = Math.round(Math.min(ancho, alto));
  // Solo la imagen se limita; la leyenda usa todo el ancho de la columna (un renglón)
  if (marco.style.maxWidth !== lado + 'px') { marco.style.maxWidth = lado + 'px'; marco.style.margin = '0 auto'; }
  // Si la columna es más angosta que el alto necesario, el cuadro se alarga hacia abajo
  // recortando un poco los lados de la imagen (sin deformarla)
  const canvas = root.querySelector('.mg-canvas');
  const h = alto + 'px';
  if (canvas.style.height !== h) { canvas.style.height = h; canvas.style.aspectRatio = 'auto'; canvas.style.objectFit = 'cover'; }
  if (!root._obsFe) {
    root._obsFe = new ResizeObserver(() => igualarAlDiagrama(root));
    root._obsFe.observe(fe);
  }
}
export default function (component) {
  const { data, parentElement } = component;
  const root = parentElement;
  root._cfg = data;
  igualarAlDiagrama(root);
  requestAnimationFrame(() => igualarAlDiagrama(root));
  if (!root._resize) { root._resize = () => igualarAlDiagrama(root); window.addEventListener('resize', root._resize); }
  // Redibujar al instante cuando el deslizador se mueve (sin esperar al servidor)
  if (!root._oyente) {
    root._oyente = (e) => { root._cLocal = e.detail; dibujar(root, root._cfg, e.detail); };
    window.addEventListener('carbono-cambia', root._oyente);
  }
  // Si el usuario está arrastrando, el valor local es el más reciente
  const c = window.__arrastrandoCarbono && root._cLocal !== undefined ? root._cLocal : data.c;
  if (!window.__arrastrandoCarbono) root._cLocal = undefined;
  dibujar(root, data, c);
  return () => {
    window.removeEventListener('carbono-cambia', root._oyente);
    root._oyente = null;
  };
}
"""

_componente = st.components.v2.component('micrografia', html=_HTML, css=_CSS, js=_JS)


def micrografia(c: float, condicion: str, key: str = 'micrografia'):
    """Muestra la micrografía esquemática del acero con `c` % C en la `condicion` dada."""
    _componente(key=key, data={
        'c': float(c), 'condicion': condicion,
        'granos': GRANOS.get(condicion, 70), 'lamina': LAMINA.get(condicion, 6.0),
        'k': {'eut': C_EUT, 'alfa': C_ALFA, 'cem': C_CEM},
    })
