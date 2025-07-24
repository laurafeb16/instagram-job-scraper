# -*- coding: utf-8 -*-
"""
Página de inicio del dashboard.
"""
import streamlit as st
import pandas as pd
import plotly.express as px

def app():
    """Renderiza la página de inicio."""
    st.header("Resumen de Ofertas Laborales")
    
    # Mostrar una métrica simulada
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Total de Ofertas", value="0", delta="0")
    with col2:
        st.metric(label="Empresas Únicas", value="0", delta="0")
    with col3:
        st.metric(label="Habilidades Populares", value="N/A")
    
    # Mostrar un mensaje para comenzar
    st.info("📊 El dashboard mostrará estadísticas cuando haya datos disponibles.")
    
    # Espacio para un futuro gráfico
    st.subheader("Distribución de Ofertas por Área")
    st.write("Aquí se mostrará la distribución de ofertas por área tecnológica.")
    
    # Espacio para tabla de ofertas recientes
    st.subheader("Ofertas Recientes")
    st.write("Aquí se mostrarán las ofertas más recientes.")
