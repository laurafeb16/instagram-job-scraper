# -*- coding: utf-8 -*-
"""
Aplicación principal del dashboard.
"""
import streamlit as st
from multipage import MultiPage
from dashboard.pages import home, trends, forecast, recommender

# Configuración de la página
st.set_page_config(
    page_title="Instagram Job Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inicializar la aplicación multipage
app = MultiPage()

# Agregar páginas
app.add_page("Inicio", home.app)
app.add_page("Tendencias", trends.app)
app.add_page("Pronósticos", forecast.app)
app.add_page("Recomendador", recommender.app)

# Título principal
st.title("Instagram Job Analytics Dashboard")

# Ejecutar la aplicación
app.run()
