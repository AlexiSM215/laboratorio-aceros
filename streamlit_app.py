"""Punto de entrada para Streamlit Community Cloud (versión web del laboratorio).

Streamlit Cloud busca por defecto un archivo llamado streamlit_app.py; este solo
ejecuta la app principal, "etapa 3.py".
"""
import runpy
from pathlib import Path

runpy.run_path(str(Path(__file__).with_name('etapa 3.py')), run_name='__main__')
