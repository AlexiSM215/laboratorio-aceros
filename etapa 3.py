"""Laboratorio de aceros al carbono — app interactiva (Streamlit).

Basta con ejecutar este archivo de cualquier forma (F5 en IDLE o VS Code,
`python "etapa 3.py"`, doble clic en "Laboratorio de aceros.app"): si no se
está corriendo dentro de Streamlit, el propio archivo prepara el entorno
.venv (la primera vez) y lanza `streamlit run` abriendo el navegador.
"""


def _lanzar_con_streamlit():
    """Relanza este archivo con `streamlit run` usando el Python de .venv."""
    try:
        from streamlit import runtime
        if runtime.exists():
            return  # ya estamos dentro de Streamlit → seguir con la app
    except ImportError:
        pass

    import os
    import subprocess
    import sys
    import threading
    import time
    import webbrowser
    from pathlib import Path

    carpeta = Path(__file__).resolve().parent
    venv = carpeta / '.venv'
    py = venv / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')

    if not py.exists():
        print('Creando el entorno .venv e instalando librerías (solo la primera vez)...')
        subprocess.run([sys.executable, '-m', 'venv', str(venv)], check=True)
        subprocess.run([str(py), '-m', 'pip', 'install', '-r',
                        str(carpeta / 'requirements.txt')], check=True)

    puerto = 8501
    url = f'http://localhost:{puerto}'
    print(f'Iniciando el laboratorio en {url} ...')
    print('Para detenerlo: Ctrl+C (o cierra esta ventana).')
    proceso = subprocess.Popen(
        [str(py), '-m', 'streamlit', 'run', str(Path(__file__).resolve()),
         '--server.headless', 'true', '--server.port', str(puerto),
         '--browser.gatherUsageStats', 'false'],
        cwd=str(carpeta))
    threading.Thread(target=lambda: (time.sleep(3), webbrowser.open(url)),
                     daemon=True).start()
    try:
        proceso.wait()
    except KeyboardInterrupt:
        proceso.terminate()
        proceso.wait()
    raise SystemExit


_lanzar_con_streamlit()

from html import escape

import streamlit as st

import analisis as an
from avisos import avisos
from diagrama_fe import diagrama_fe
from micrografia import micrografia
from regla_palanca import regla_palanca
import pestanas_vivas as pv

st.set_page_config(page_title='Laboratorio de aceros al carbono', layout='wide')

# La barra superior de Streamlit (Deploy y menú) tapaba el contenido al desplazarse:
# se oculta y se hace transparente; solo queda el botón para reabrir la barra lateral.
st.html("""
<style>
header[data-testid="stHeader"] { background: transparent; pointer-events: none; }
header[data-testid="stHeader"] button, header[data-testid="stHeader"] a { pointer-events: auto; }
[data-testid="stToolbarActions"], [data-testid="stAppDeployButton"], [data-testid="stMainMenu"] { display: none; }
[data-testid="stToolbar"] { background: transparent; }
[data-testid="stDecoration"] { display: none; }
/* Sin espacio en blanco arriba: ni en el área principal ni en la barra lateral */
[data-testid="stMainBlockContainer"] { padding-top: 0.75rem; padding-bottom: 1.5rem; }
/* El aviso no ocupa espacio: se dibuja como notificación sobre la esquina derecha de las pestañas */
.st-key-avisos { height: 0 !important; min-height: 0 !important; position: relative; z-index: 60; overflow: visible !important;
                 margin: -16px 0 !important; }  /* sin separación entre "Acero con…" y las pestañas */
.st-key-avisos * { overflow: visible !important; }
/* Sin anclaje automático del navegador: al cerrarse un aviso sube la información y el título no se mueve */
[data-testid="stMain"] { overflow-anchor: none; }
/* Igual en todos los equipos: barras de desplazamiento delgadas con espacio fijo (en Windows son
   anchas y cambian el ancho del contenido) y sin agrandado automático del texto en iPad */
html { -webkit-text-size-adjust: 100%; text-size-adjust: 100%; }
/* Menús de Acero y Procesamiento: solo se elige de la lista (sin cursor de texto) */
[data-testid="stSidebar"] [data-testid="stSelectbox"] input { caret-color: transparent; cursor: pointer; }
[data-testid="stSidebar"] [data-testid="stSelectbox"] [data-baseweb="select"] > div { cursor: pointer; }
[data-testid="stMain"] { scrollbar-gutter: stable; scrollbar-width: thin; }
[data-testid="stMain"]::-webkit-scrollbar, [data-testid="stSidebarContent"]::-webkit-scrollbar { width: 8px; height: 8px; }
[data-testid="stMain"]::-webkit-scrollbar-thumb, [data-testid="stSidebarContent"]::-webkit-scrollbar-thumb {
  background: rgba(128,128,128,.45); border-radius: 4px; }
[data-testid="stMain"]::-webkit-scrollbar-track, [data-testid="stSidebarContent"]::-webkit-scrollbar-track { background: transparent; }
/* Tablets en vertical y ventanas angostas: columnas una debajo de otra y pestañas más compactas */
@media (max-width: 1000px) {
  [data-testid="stMainBlockContainer"] [data-testid="stHorizontalBlock"] { flex-wrap: wrap; }
  [data-testid="stMainBlockContainer"] [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] { min-width: 100%; }
  [role="tablist"] { gap: 8px; }
  [role="tablist"] [role="tab"] { padding-left: 0; padding-right: 0; }
  [role="tablist"] [role="tab"] p { font-size: 12px; }
}
[data-testid="stMainBlockContainer"] h1 { padding-top: 0; }
[data-testid="stSidebarHeader"] { position: absolute; top: 10px; right: 6px; height: auto; min-height: 0;
                                  padding: 0; margin: 0; z-index: 5; }
[data-testid="stSidebarUserContent"] { padding-top: 0.75rem; }
[data-testid="stSidebarUserContent"] h2:first-of-type { padding-top: 0; }
</style>
""")


# ----------------------------------------------------------------------------
# Datos y modelos (se calculan una sola vez)
# ----------------------------------------------------------------------------
@st.cache_data
def preparar():
    datos = an.cargar_datos()
    return datos, an.ajustar_modelos(datos)


datos, modelos = preparar()

# ----------------------------------------------------------------------------
# Deslizador de carbono que se actualiza mientras se arrastra
# (st.slider solo envía el valor al soltar el ratón)
# ----------------------------------------------------------------------------
_SLIDER_HTML = """
<div class="cs">
  <div class="cs-cab"><span>Carbono (% en peso)</span><b class="cs-val"></b></div>
  <input class="cs-in" type="range">
  <div class="cs-lim"><span class="cs-min"></span><span class="cs-max"></span></div>
</div>
"""
_SLIDER_CSS = """
.cs { font-family: var(--st-font, sans-serif); color: var(--st-text-color); padding: 4px 0 8px; }
.cs-cab { display: flex; justify-content: space-between; font-size: 14px; margin-bottom: 6px; }
.cs-val { color: var(--st-primary-color); }
.cs-in { width: 100%; accent-color: var(--st-primary-color); cursor: pointer; margin: 0; }
.cs-lim { display: flex; justify-content: space-between; font-size: 12px; opacity: .6; }
"""
_SLIDER_JS = """
export default function (component) {
  const { data, setStateValue, parentElement } = component;
  const root = parentElement;
  const input = root.querySelector('.cs-in');
  const etiqueta = root.querySelector('.cs-val');
  const mostrar = (v) => { etiqueta.textContent = Number(v).toFixed(2); };

  input.min = data.min; input.max = data.max; input.step = data.step;
  root.querySelector('.cs-min').textContent = Number(data.min).toFixed(2);
  root.querySelector('.cs-max').textContent = Number(data.max).toFixed(2);

  // Solo se sobrescribe la posición si el usuario no está arrastrando
  if (!root._arrastrando) { input.value = data.value; mostrar(data.value); }

  const enviar = () => {
    const v = Number(input.value);
    if (v !== root._ultimo) { root._ultimo = v; setStateValue('value', v); }
  };
  input.onpointerdown = () => { root._arrastrando = true; window.__arrastrandoCarbono = true; };
  input.onpointerup = input.onpointercancel = () => {
    root._arrastrando = false; window.__arrastrandoCarbono = false; enviar();
  };
  input.oninput = () => {
    mostrar(input.value);
    // Aviso inmediato a la micrografía (se redibuja en el navegador sin esperar al servidor)
    window.dispatchEvent(new CustomEvent('carbono-cambia', { detail: Number(input.value) }));
    if (!root._temporizador) {
      root._temporizador = setTimeout(() => { root._temporizador = null; enviar(); }, 60);
    }
  };
  input.onchange = enviar;

  // Las gráficas también pueden mover el carbono (arrastrando su punto): piden el valor
  // con el evento 'carbono-pedir' y este deslizador lo aplica como si lo moviera el usuario
  root._enviar = enviar;
  root._datos = data;
  if (!root._oyentePedir) {
    root._oyentePedir = (e) => {
      const d = root._datos, inp = root.querySelector('.cs-in');
      const v = Math.min(d.max, Math.max(d.min, +(Math.round(e.detail.valor / d.step) * d.step).toFixed(2)));
      if (e.detail.inicio) { root._arrastrando = true; window.__arrastrandoCarbono = true; }
      if (Number(inp.value) !== v || e.detail.inicio) {
        inp.value = v;
        root.querySelector('.cs-val').textContent = v.toFixed(2);
        window.dispatchEvent(new CustomEvent('carbono-cambia', { detail: v }));
      }
      if (e.detail.fin) {
        root._arrastrando = false; window.__arrastrandoCarbono = false; root._enviar();
      } else if (!root._temporizador) {
        root._temporizador = setTimeout(() => { root._temporizador = null; root._enviar(); }, 60);
      }
    };
    window.addEventListener('carbono-pedir', root._oyentePedir);
  }
}
"""
_slider_carbono = st.components.v2.component(
    'slider_carbono', html=_SLIDER_HTML, css=_SLIDER_CSS, js=_SLIDER_JS)


def _al_mover_carbono():
    estado = st.session_state.get('slider_c') or {}
    v = estado.get('value')
    if v is not None:
        st.session_state['C'] = round(float(v), 2)

# ----------------------------------------------------------------------------
# Barra lateral: elegir acero y condición
# ----------------------------------------------------------------------------
PRESETS = {'1020': 0.20, '1045': 0.45, '1060': 0.60, '1080': 0.80, '1095': 0.95}

if 'C' not in st.session_state:
    st.session_state['C'] = 0.45

PERSONALIZADO = 'personalizado'


def _al_elegir_acero():
    elegido = st.session_state['acero']
    if elegido in PRESETS:
        st.session_state['C'] = PRESETS[elegido]


with st.sidebar:
    st.header('Acero')
    # El desplegable muestra el acero que corresponde al carbono actual, o
    # "Personalizado" si el carbono se ajustó a mano con el deslizador
    st.session_state['acero'] = next((k for k, v in PRESETS.items()
                                      if abs(v - st.session_state['C']) < 1e-9), PERSONALIZADO)
    st.selectbox('Acero', [*PRESETS, PERSONALIZADO], key='acero', on_change=_al_elegir_acero,
                 filter_mode=None,  # solo elegir de la lista: no se puede escribir
                 label_visibility='collapsed',
                 format_func=lambda k: (f'Personalizado ({st.session_state["C"]:.2f} % C)'
                                        if k == PERSONALIZADO else f'AISI {k}'))
    _slider_carbono(key='slider_c', data={'value': st.session_state['C'], 'min': 0.05, 'max': 1.00,
                                          'step': 0.01},
                    on_value_change=_al_mover_carbono)
    c = st.session_state['C']
    st.header('Procesamiento')
    cnd = st.selectbox('Condición', an.ORDEN, index=2, label_visibility='collapsed',
                       filter_mode=None)  # solo elegir de la lista: no se puede escribir
    st.caption(an.DESCRIPCION[cnd])
    st.divider()
    st.caption(f'Datos: {len(datos)} registros de {datos["Name"].nunique()} aceros AISI 10xx '
               '(Etapa 2 del proyecto, MatWeb).')

tipo = 'hipoeutectoide' if c < an.C_EUT - 0.005 else ('eutectoide' if c <= an.C_EUT + 0.005 else 'hipereutectoide')

st.title('Laboratorio de aceros al carbono')
with st.container(key='resumen_acero'):  # punto de llegada del desplazamiento automático
    st.markdown(f'**Acero con {c:.2f} % C ({tipo}) · {cnd}**')

# Avisos de extrapolación: notificación (!) junto a las pestañas; el texto aparece al pasar el ratón
avisos(c, cnd, modelos.loc[cnd, 'C_min'], modelos.loc[cnd, 'C_max'],
       info=('En esta condición YS/UTS es casi constante: MatWeb probablemente reporta la fluencia como '
             'una fracción fija de la UTS (sección 5.5). Toma el YS como estimado.'
             if cnd in ('Laminado en caliente', 'Estirado en frío') else ''))

tabs = st.tabs(['Microestructura', 'Propiedades', 'Datos reales',
                'Resistencia vs ductilidad', 'Diseño inverso', 'Acerca de'])

# ----------------------------------------------------------------------------
# 1. Microestructura
# ----------------------------------------------------------------------------
with tabs[0]:
    izq, der = st.columns([1.15, 1])
    with izq:
        st.subheader('Diagrama Fe–Fe₃C (zona del acero)')
        diagrama_fe(c, an.COLOR[cnd])

    with der:
        st.subheader('Micrografía esquemática')
        micrografia(c, cnd)
        st.caption('<span style="font-size: 12px;">Esquema sin escala. La perlita son láminas alternas de '
                   'ferrita y cementita; su espaciado y el tamaño de grano cambian con el procesamiento (más '
                   'fino al normalizar, granos alargados al estirar en frío).</span>', unsafe_allow_html=True)

    regla_palanca(c)  # incluye el título y el botón para desplegar las fórmulas

# ----------------------------------------------------------------------------
# 2. Propiedades predichas
# ----------------------------------------------------------------------------
with tabs[1]:
    pv.propiedades(datos, modelos, cnd, c)

# ----------------------------------------------------------------------------
# 3. Datos reales
# ----------------------------------------------------------------------------
with tabs[2]:
    pv.datos_reales(datos, modelos, cnd, c)

    with st.expander(f'Ver los {int((datos["Condición"] == cnd).sum())} registros de {cnd}'):
        # Tabla compacta con altura limitada al espacio libre de la pantalla (así el
        # desplegable completo cabe sin desplazar la página); el resto de filas se ve
        # desplazándose dentro de la tabla, con el encabezado fijo
        ver = datos[datos['Condición'] == cnd].sort_values('C')
        # Colores según el tema activo (claro u oscuro, sigue al sistema)
        oscuro = getattr(st.context.theme, 'type', None) == 'dark'
        cab, borde = ('#2a2825', 'rgba(255,255,255,.09)') if oscuro else ('#f5f5f5', 'rgba(0,0,0,.07)')
        filas = ''.join(
            f'<tr><td>{escape(r["Acero"])}</td><td class="n">{r["C"]:.3f}</td><td class="n">{r["Mn"]:.2f}</td>'
            f'<td class="n">{r[an.UTS]:.0f}</td><td class="n">{r[an.YS]:.0f}</td><td class="n">{r[an.DU]:.1f}</td>'
            f'<td class="pc">{escape(str(r["Processing condition"]))}</td></tr>'
            for _, r in ver.iterrows())
        st.html(f'''<style>
.tabla-reg {{ width: 100%; border-collapse: collapse; table-layout: fixed; font-size: 12px; line-height: 1.6; }}
.caja-reg {{ max-height: max(120px, calc(100vh - 660px)); overflow-y: auto; border: 1px solid {borde};
             border-radius: 6px; }}
.tabla-reg th {{ text-align: left; font-weight: 600; background: {cab}; position: sticky; top: 0; z-index: 1; }}
.tabla-reg th, .tabla-reg td {{ padding: 3px 10px; border-bottom: 1px solid {borde}; vertical-align: top; }}
.tabla-reg .n {{ text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }}
.tabla-reg .pc {{ overflow-wrap: anywhere; opacity: .85; }}
/* El componente del desplazamiento automático no ocupa espacio (abajo queda el mismo margen que arriba) */
.st-key-desplazar_registros {{ display: none; }}
</style>
<div class="caja-reg"><table class="tabla-reg">
  <colgroup><col style="width:11%"><col style="width:7%"><col style="width:6%"><col style="width:7%">
            <col style="width:7%"><col style="width:10%"><col style="width:52%"></colgroup>
  <tr><th>Acero</th><th class="n">C</th><th class="n">Mn</th><th class="n">UTS</th><th class="n">YS</th>
      <th class="n">Ductilidad</th><th>Procesamiento (MatWeb)</th></tr>''' + filas + '</table></div>')
        pv.auto_desplazar('desplazar_registros', destino='[role="tablist"]', ajustar='.caja-reg')

# ----------------------------------------------------------------------------
# 4. Compromiso resistencia–ductilidad
# ----------------------------------------------------------------------------
with tabs[3]:
    st.subheader('Compromiso resistencia–ductilidad')
    st.markdown('<p style="font-size: 14px; margin: 0 0 10px;">Cada línea recorre el rango de carbono de su condición: '
                'al subir el %C la resistencia aumenta pero el acero se vuelve menos dúctil. '
                '<b>Arriba a la derecha es mejor.</b></p>', unsafe_allow_html=True)
    pv.compromiso(datos, modelos, cnd, c)
    st.caption('<span style="font-size: 12px;">Para la misma resistencia, el normalizado conserva más ductilidad '
               'que el laminado en caliente; el estirado en frío gana resistencia a costa de la ductilidad '
               '(endurecimiento por deformación).</span>', unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# 5. Diseño inverso
# ----------------------------------------------------------------------------
with tabs[4]:
    st.subheader('¿Qué acero necesito para una resistencia dada?')
    pv.diseno_inverso(datos, modelos)

# ----------------------------------------------------------------------------
# 6. Acerca de
# ----------------------------------------------------------------------------
with tabs[5]:
    st.subheader('Cómo funciona')
    st.markdown(f"""
Esta app convierte en herramienta interactiva la **Etapa 2 del proyecto**: *efecto del contenido de carbono en
la resistencia y la ductilidad de los aceros al carbono*.

- **Datos:** dataset limpio de la Etapa 1 (1780 registros) → aceros **AISI 10xx** (solo varían C y Mn) →
  4 condiciones sin temple → sin procesos contradictorios = **{len(datos)} registros de {datos['Name'].nunique()} aceros**.
- **Microestructura:** regla de la palanca del diagrama Fe–Fe₃C (eutectoide 0.76 % C; ferrita 0.022 % C;
  cementita 6.70 % C).
- **Propiedades:** rectas por mínimos cuadrados propiedad = a + b·C para cada condición.
- **Error de predicción:** validación cruzada dejando un acero fuera (un valor por acero).
""")
    st.subheader('Limitaciones')
    st.markdown("""
- Los datos de MatWeb son **valores típicos**, no ensayos individuales; algunos YS son estimados.
- La composición es **nominal** (centro del rango de la norma).
- Las rectas solo valen **dentro del rango de carbono con datos** de cada condición; en el recocido, solo hasta
  el eutectoide.
- La micrografía y el diagrama son **esquemáticos**: el tamaño de grano y el espaciado de la perlita no están a escala.
- Son asociaciones observacionales, no un modelo cinético; no aplica a aceros templados o aleados.
""")
