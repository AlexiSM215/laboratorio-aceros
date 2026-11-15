"""Colores compartidos por los componentes, derivados del tema activo de Streamlit.

Streamlit sigue el modo claro/oscuro del sistema (por ejemplo, el modo noche de
macOS) y entrega sus colores a los componentes como variables CSS (--st-*).
Los colores neutros de las gráficas y tablas (rejilla, ejes, textos suaves,
bordes) se calculan a partir del color de texto y de fondo, así se ven bien en
los dos modos sin escribir colores fijos.
"""

TEMA_CSS = """
:host, .tema {
  --t-texto: var(--st-text-color, #31333f);
  --t-fondo: var(--st-background-color, #ffffff);
  --t-suave: color-mix(in srgb, var(--t-texto) 68%, transparent);
  --t-linea: color-mix(in srgb, var(--t-texto) 82%, transparent);
  --t-guia: color-mix(in srgb, var(--t-texto) 42%, transparent);
  --t-eje: color-mix(in srgb, var(--t-texto) 28%, transparent);
  --t-borde: color-mix(in srgb, var(--t-texto) 14%, transparent);
  --t-rejilla: color-mix(in srgb, var(--t-texto) 9%, transparent);
  --t-rejilla2: color-mix(in srgb, var(--t-texto) 5%, transparent);
  --t-cabecera: color-mix(in srgb, var(--t-texto) 5%, var(--t-fondo));
}
/* Clases para líneas SVG (las reglas CSS tienen prioridad sobre los atributos) */
.rej { stroke: var(--t-rejilla); }
.rej2 { stroke: var(--t-rejilla2); }
.eje-l { stroke: var(--t-eje); }
.guia { stroke: var(--t-guia); }
.linea { stroke: var(--t-linea); }
"""
