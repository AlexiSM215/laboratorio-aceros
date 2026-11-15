"""Datos y modelos del laboratorio.

Reproduce la selección y los ajustes de la Etapa 2 del proyecto
("Proyecto con python, etapa 2.ipynb"): aceros AISI 10xx en cuatro
condiciones sin temple, rectas UTS/YS/ductilidad contra %C, regla de la
palanca y validación cruzada dejando un acero fuera.
"""
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

# El archivo de datos puede estar junto al código (versión web) o en la carpeta superior
_AQUI = Path(__file__).resolve().parent
RUTA_CSV = next((r for r in (_AQUI / "Dataset_limpio_corregido.csv", _AQUI.parent / "Dataset_limpio_corregido.csv")
                 if r.exists()), _AQUI / "Dataset_limpio_corregido.csv")

EL = ['Al', 'Cu', 'Mn', 'N', 'Ni', 'Ti', 'S', 'Fe', 'Zr', 'P', 'Si', 'V',
      'Mo', 'Co', 'C', 'Nb', 'B', 'Cr']
UTS = '(Ultimate) Tensile strength (MPa)'
YS = 'Yield strength (MPa)'
DU = 'Ductility (%)'
CL = 'Cluster Number (0 to 11)'

ORDEN = ['Recocido', 'Laminado en caliente', 'Normalizado', 'Estirado en frío']
COLOR = dict(zip(ORDEN, ['#2E86AB', '#E07A5F', '#3D9970', '#8E6CC0']))

DESCRIPCION = {
    'Recocido': 'Enfriamiento lento en horno → ferrita + perlita gruesa.',
    'Laminado en caliente': 'Enfriamiento al aire tras laminar → perlita intermedia.',
    'Normalizado': 'Austenizado y enfriado al aire → perlita fina y grano refinado.',
    'Estirado en frío': 'Laminado + deformación en frío → granos alargados y endurecidos por deformación.',
}

# Diagrama Fe–Fe3C (Callister y Rethwisch, 2018, cap. 9)
C_EUT, C_ALFA, C_CEM = 0.76, 0.022, 6.70
T_EUT, T_A3_0, C_GAMMA_MAX, T_EUTECTICO = 727, 912, 2.14, 1148


def clasificar(p: str):
    """Mismas reglas de palabras clave que la sección 2.4 de la Etapa 2."""
    if any(k in p for k in ['quench', 'temper', 'carburiz', 'heat treated']):
        return None
    if 'normaliz' in p:
        return 'Normalizado'
    if p.startswith('annealed'):
        return 'Recocido'
    if 'hot rolled' in p or p.startswith('as rolled'):
        return 'Laminado en caliente'
    if ('cold drawn' in p or p.startswith('as drawn')) and not any(
            k in p for k in ['stress relieved', 'anneal', 'spheroid']):
        return 'Estirado en frío'
    return None


def cargar_datos(ruta: Path = RUTA_CSV) -> pd.DataFrame:
    """Devuelve los 163 registros AISI 10xx usados en la Etapa 2."""
    df = pd.read_csv(ruta)
    clave = ['Name'] + EL + [UTS, YS, DU]
    contradictorio = (df.duplicated(subset=clave, keep=False)
                      & (df.groupby(clave)[CL].transform('nunique') > 1))
    carbono = df[df['Name'].str.match(r'aisi 10\d\d steel') & ~contradictorio].copy()
    carbono['Condición'] = carbono['Processing condition'].map(clasificar)
    datos = carbono[carbono['Condición'].notna()].copy()
    datos['Condición'] = pd.Categorical(datos['Condición'], categories=ORDEN, ordered=True)
    datos['Acero'] = datos['Name'].str.replace(' steel', '').str.upper()
    datos['f_perlita'] = fracciones(datos['C'].values)['perlita']
    return datos


def fracciones(c):
    """Regla de la palanca a temperatura justo debajo de 727 °C."""
    c = np.asarray(c, dtype=float)
    hipo = c <= C_EUT
    f_p = np.where(hipo, (c - C_ALFA) / (C_EUT - C_ALFA), (C_CEM - c) / (C_CEM - C_EUT))
    f_p = np.clip(f_p, 0, 1)
    f_a = np.where(hipo, 1 - f_p, 0.0)
    f_c = np.where(hipo, 0.0, 1 - f_p)
    return {'ferrita': f_a, 'perlita': f_p, 'cementita': f_c}


def temperaturas_criticas(c: float):
    """A1 y A3/Acm (líneas rectas, aproximación esquemática del diagrama)."""
    if c <= C_EUT:
        return T_EUT, T_A3_0 - (T_A3_0 - T_EUT) * c / C_EUT, 'A3'
    return T_EUT, T_EUT + (T_EUTECTICO - T_EUT) * (c - C_EUT) / (C_GAMMA_MAX - C_EUT), 'Acm'


def ajustar_modelos(datos: pd.DataFrame) -> pd.DataFrame:
    """Rectas propiedad = a + b·C por condición (sección 3.1 y 3.2) + error LOO (5.6)."""
    filas = []
    for cnd in ORDEN:
        d = datos[datos['Condición'] == cnd]
        fila = {'Condición': cnd, 'registros': len(d), 'aceros': d['Name'].nunique(),
                'C_min': d['C'].min(), 'C_max': d['C'].max()}
        for col, nom in [(UTS, 'UTS'), (YS, 'YS'), (DU, 'DU')]:
            r = stats.linregress(d['C'], d[col])
            fila[f'a_{nom}'], fila[f'b_{nom}'], fila[f'R2_{nom}'] = r.intercept, r.slope, r.rvalue ** 2
        # Validación cruzada dejando un acero fuera (un valor por acero)
        pa = d.groupby('Name')[['C', UTS]].median()
        errores = []
        for acero in pa.index:
            ent = pa.drop(index=acero)
            r = stats.linregress(ent['C'], ent[UTS])
            errores.append(abs(pa.loc[acero, UTS] - (r.intercept + r.slope * pa.loc[acero, 'C'])))
        fila['error_LOO'] = float(np.mean(errores))
        filas.append(fila)
    return pd.DataFrame(filas).set_index('Condición')


def predecir(modelos: pd.DataFrame, cnd: str, c: float) -> dict:
    m = modelos.loc[cnd]
    return {
        'UTS': m['a_UTS'] + m['b_UTS'] * c,
        'YS': m['a_YS'] + m['b_YS'] * c,
        'DU': max(m['a_DU'] + m['b_DU'] * c, 0.0),
        'error': m['error_LOO'],
        'en_rango': m['C_min'] - 1e-9 <= c <= m['C_max'] + 1e-9,
    }


def diseno_inverso(modelos: pd.DataFrame, uts_obj: float) -> pd.DataFrame:
    """%C necesario para una UTS objetivo en cada condición (sección 6)."""
    filas = []
    for cnd in ORDEN:
        m = modelos.loc[cnd]
        c_req = (uts_obj - m['a_UTS']) / m['b_UTS']
        dentro = m['C_min'] <= c_req <= m['C_max']
        confiable = dentro and not (cnd == 'Recocido' and c_req > C_EUT)
        if not dentro:
            nota = f"Fuera del rango con datos ({m['C_min']:.2f}–{m['C_max']:.2f} % C)"
        elif not confiable:
            nota = 'Zona hipereutectoide: la relación del recocido deja de ser lineal (sección 5.4)'
        else:
            nota = 'Dentro del rango con datos'
        filas.append({'Condición': cnd, 'C necesario (%)': c_req,
                      'Ductilidad esperada (%)': m['a_DU'] + m['b_DU'] * c_req if confiable else np.nan,
                      'Confiable': confiable, 'Nota': nota})
    return pd.DataFrame(filas)


def aceros_cercanos(datos: pd.DataFrame, cnd: str, c: float, n: int = 5) -> pd.DataFrame:
    """Aceros reales (mediana por acero) más cercanos al %C elegido."""
    d = datos[datos['Condición'] == cnd]
    pa = (d.groupby('Acero')
            .agg(C=('C', 'median'), Mn=('Mn', 'median'), UTS=(UTS, 'median'),
                 YS=(YS, 'median'), Ductilidad=(DU, 'median'), registros=('Entry', 'size'))
            .reset_index())
    pa['distancia'] = (pa['C'] - c).abs()
    return pa.sort_values('distancia').head(n).drop(columns='distancia')
