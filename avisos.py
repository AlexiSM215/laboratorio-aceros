"""Avisos de extrapolación como notificación junto a las pestañas.

En lugar de una franja que empuja el contenido, aparece un círculo amarillo con
"!" en la esquina derecha de la fila de pestañas (como una notificación). Al
pasar el ratón por encima se muestra el texto del aviso. Se calcula en el
navegador a partir del deslizador de carbono, así que aparece y desaparece al
instante.
"""
import streamlit as st

from analisis import C_EUT
from tema import TEMA_CSS

_HTML = """
<div class="av">
  <div class="nt nt-rec">
    <button class="av-bt bt-rec" type="button" aria-label="Recomendación">!</button>
    <div class="av-globo globo-rec" role="tooltip"></div>
  </div>
  <div class="nt nt-info">
    <button class="av-bt bt-info" type="button" aria-label="Nota">!</button>
    <div class="av-globo globo-info" role="tooltip"></div>
  </div>
  <div class="nt nt-aviso">
    <button class="av-bt" type="button" aria-label="Aviso">!</button>
    <div class="av-globo" role="tooltip">
      <div class="av-msg av-rango"></div>
      <div class="av-msg av-recocido">
        En el recocido la relación UTS–%C deja de ser lineal por encima del eutectoide (sección 5.4):
        la recta sobreestima la resistencia de los hipereutectoides (~180 MPa).
      </div>
    </div>
  </div>
</div>
"""

_CSS = TEMA_CSS + """
.av { position: absolute; right: 0; top: 7px; display: flex; align-items: center; gap: 8px;
      font-family: var(--st-font, sans-serif); z-index: 50; }
/* Cada notificación ocupa espacio solo cuando está activa (así la otra queda pegada a la derecha) */
.nt { position: relative; width: 0; margin-left: -8px; transition: width .3s ease, margin .3s ease; }
.nt.activo { width: 26px; margin-left: 0; }
/* Botón: círculo amarillo con "!" */
.av-bt { width: 26px; height: 26px; padding: 0; border: 0; border-radius: 50%; cursor: default;
         background: #F5B800; color: #3a2a00; font: 800 16px/26px var(--st-font, sans-serif);
         box-shadow: 0 1px 4px rgba(0,0,0,.25); transform: scale(0); opacity: 0;
         transition: transform .35s cubic-bezier(.34,1.56,.64,1), opacity .2s; }
.nt.activo .av-bt { transform: scale(1); opacity: 1; }
/* Pulso al aparecer, como una notificación recibida */
.nt.activo.nuevo .av-bt { animation: pulso 1.1s ease-out 2; }
@keyframes pulso { 0% { box-shadow: 0 0 0 0 rgba(245,184,0,.65); } 100% { box-shadow: 0 0 0 12px rgba(245,184,0,0); } }
/* Notificación azul (nota informativa) */
.bt-info { background: #2F7FE0; color: #fff; }
.nt.activo.nuevo .bt-info { animation: pulso-azul 1.1s ease-out 2; }
@keyframes pulso-azul { 0% { box-shadow: 0 0 0 0 rgba(47,127,224,.6); } 100% { box-shadow: 0 0 0 12px rgba(47,127,224,0); } }
/* Notificación verde: recomendación de Diseño inverso (roja si ninguna condición sirve) */
.bt-rec { background: #1F9D57; color: #fff; }
.nt.activo.nuevo .bt-rec { animation: pulso-verde 1.1s ease-out 2; }
@keyframes pulso-verde { 0% { box-shadow: 0 0 0 0 rgba(31,157,87,.6); } 100% { box-shadow: 0 0 0 12px rgba(31,157,87,0); } }
.nt-rec.mal .bt-rec { background: #E5484D; }
.av-globo.globo-rec { color: var(--st-green-text-color, rgb(23,114,51));
              background: linear-gradient(var(--st-green-background-color, rgba(33,195,84,.1)),
                                          var(--st-green-background-color, rgba(33,195,84,.1))), var(--t-fondo);
              border-color: color-mix(in srgb, #1F9D57 45%, transparent); }
.nt-rec.mal .av-globo.globo-rec { color: var(--st-red-text-color, rgb(125,53,59));
              background: linear-gradient(var(--st-red-background-color, rgba(255,43,43,.09)),
                                          var(--st-red-background-color, rgba(255,43,43,.09))), var(--t-fondo);
              border-color: color-mix(in srgb, #E5484D 45%, transparent); }
.av-globo.globo-info { color: var(--st-blue-text-color, rgb(0,66,128));
              background: linear-gradient(var(--st-blue-background-color, rgba(28,131,225,.1)),
                                          var(--st-blue-background-color, rgba(28,131,225,.1))), var(--t-fondo);
              border-color: color-mix(in srgb, #2F7FE0 45%, transparent); }
/* Globo con el texto, al pasar el ratón */
.av-globo { position: absolute; right: 0; top: 34px; width: min(420px, 80vw); padding: 12px 14px;
            border-radius: 8px; font-size: 14px; line-height: 1.5;
            color: var(--st-yellow-text-color, rgb(146, 108, 5));
            background: linear-gradient(var(--st-yellow-background-color, rgba(255,189,69,.14)),
                                        var(--st-yellow-background-color, rgba(255,189,69,.14))), var(--t-fondo);
            border: 1px solid color-mix(in srgb, #F5B800 45%, transparent);
            box-shadow: 0 6px 20px rgba(0,0,0,.18);
            opacity: 0; transform: translateY(-4px); pointer-events: none;
            transition: opacity .15s ease, transform .15s ease; }
.av-globo::before { content: ''; position: absolute; top: -6px; right: 8px; width: 10px; height: 10px;
                    transform: rotate(45deg); background: inherit; border-left: inherit; border-top: inherit; }
.nt.activo:hover .av-globo, .nt.activo:focus-within .av-globo { opacity: 1; transform: none; }
.av-msg { display: none; }
.av-msg.on { display: block; }
.av-msg.on + .av-msg.on { margin-top: 8px; padding-top: 8px; border-top: 1px solid color-mix(in srgb, currentColor 25%, transparent); }
.av-msg b { font-weight: 700; }
"""

_JS = """
// Muestra u oculta una notificación; el pulso solo cuando aparece (no en cada redibujo)
function activar(nt, activo) {
  if (activo && !nt.classList.contains('activo')) {
    nt.classList.remove('nuevo'); void nt.offsetWidth; nt.classList.add('nuevo');
  }
  nt.classList.toggle('activo', activo);
}
// Recomendación de Diseño inverso: solo visible en esa pestaña
function pestanaActiva() {
  const t = document.querySelector('[role="tab"][aria-selected="true"]');
  return t ? t.textContent.trim() : '';
}
function mostrarRecomendacion(root) {
  const nt = root.querySelector('.nt-rec'), r = window.__recomendacion;
  if (r) { root.querySelector('.globo-rec').innerHTML = r.html; nt.classList.toggle('mal', r.tipo === 'mal'); }
  activar(nt, !!r && pestanaActiva() === 'Diseño inverso');
}
function actualizar(root, cfg, c) {
  const fuera = c < cfg.cmin - 1e-9 || c > cfg.cmax + 1e-9;
  const recocido = cfg.recocido && c > cfg.eut;
  root.querySelector('.av-rango').classList.toggle('on', fuera);
  root.querySelector('.av-recocido').classList.toggle('on', recocido);
  activar(root.querySelector('.nt-aviso'), fuera || recocido);
  const n = (fuera ? 1 : 0) + (recocido ? 1 : 0);
  root.querySelector('.nt-aviso .av-bt').setAttribute('aria-label', n > 1 ? `${n} avisos` : 'Aviso');
}

export default function (component) {
  const { data, parentElement } = component;
  const root = parentElement;
  root.querySelector('.av-rango').innerHTML =
    `Para <b>${data.cnd}</b> solo hay datos entre ${data.cmin.toFixed(2)} y ${data.cmax.toFixed(2)} % C. `
    + 'Las propiedades mostradas son una <b>extrapolación</b> de la recta.';
  // Nota azul (no depende del carbono): por ejemplo, YS estimado en algunas condiciones
  root.querySelector('.globo-info').textContent = data.info || '';
  activar(root.querySelector('.nt-info'), !!data.info);
  root._cfg = data;
  if (!root._oyenteRec) {
    root._oyenteRec = () => mostrarRecomendacion(root);
    window.addEventListener('recomendacion', root._oyenteRec);
    // Al cambiar de pestaña, mostrar u ocultar la recomendación
    document.addEventListener('click', (e) => {
      if (e.target.closest && e.target.closest('[role="tab"]')) setTimeout(() => mostrarRecomendacion(root), 60);
    }, true);
  }
  mostrarRecomendacion(root);
  if (!root._oyente) {
    root._oyente = (e) => { root._cLocal = e.detail; actualizar(root, root._cfg, e.detail); };
    window.addEventListener('carbono-cambia', root._oyente);
  }
  const c = window.__arrastrandoCarbono && root._cLocal !== undefined ? root._cLocal : data.c;
  if (!window.__arrastrandoCarbono) root._cLocal = undefined;
  actualizar(root, data, c);
  return () => {
    window.removeEventListener('carbono-cambia', root._oyente);
    root._oyente = null;
  };
}
"""

_componente = st.components.v2.component('avisos', html=_HTML, css=_CSS, js=_JS)


def avisos(c: float, condicion: str, c_min: float, c_max: float, info: str = '', key: str = 'avisos'):
    """Avisos de extrapolación y de no linealidad en el recocido (amarillo) y una nota
    informativa opcional (azul), como notificaciones junto a las pestañas."""
    _componente(key=key, data={'c': float(c), 'cnd': condicion, 'cmin': float(c_min),
                               'cmax': float(c_max), 'eut': C_EUT, 'recocido': condicion == 'Recocido',
                               'info': info})
