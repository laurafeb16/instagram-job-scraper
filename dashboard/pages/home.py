# -*- coding: utf-8 -*-
"""
Pagina de inicio del dashboard.
"""
from typing import Callable, Dict, List, Any
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

from dashboard.utils.helpers import (
    get_dashboard_metrics,
    get_area_stats,
    get_job_posts_df,
    get_post_url
)

def app() -> None:
    """Renderiza la pagina de inicio del dashboard."""
    st.header("Resumen de Ofertas Laborales")
    
    # Obtener metricas
    metrics = get_dashboard_metrics()
    
    # Mostrar metricas en tarjetas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            label="Total de Ofertas", 
            value=metrics['total_jobs']
        )
    with col2:
        st.metric(
            label="Ofertas Abiertas", 
            value=metrics['open_jobs'],
            delta=f"{metrics['open_jobs']/metrics['total_jobs']*100:.1f}%" if metrics['total_jobs'] > 0 else None
        )
    with col3:
        st.metric(
            label="Ultima Actualizacion", 
            value=metrics['last_scrape'].strftime("%d/%m/%Y %H:%M") if metrics['last_scrape'] else "Nunca"
        )
    
    # Separador
    st.markdown("---")
    
    # Distribucion por area
    st.subheader("Distribucion por Area Tecnologica")
    area_df, _ = get_area_stats()
    
    if not area_df.empty:
        fig = px.pie(
            area_df, 
            names='area', 
            values='count',
            title="Distribucion de Ofertas por Area",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        st.plotly_chart(fig)
    else:
        st.info("No hay datos suficientes para mostrar la distribucion por area.")
    
    # Ofertas recientes
    st.subheader("Ofertas Recientes")
    job_df = get_job_posts_df()
    
    if not job_df.empty:
        # Seleccionar columnas relevantes
        display_df = job_df[['company', 'title', 'area', 'post_date', 'is_open', 'shortcode']].copy()
        
        # Formatear fecha
        display_df['post_date'] = pd.to_datetime(display_df['post_date']).dt.strftime('%d/%m/%Y')
        
        # Convertir estado a texto
        display_df['is_open'] = display_df['is_open'].map({True: "Abierta", False: "Cerrada"})
        
        # Anadir URL
        display_df['url'] = display_df['shortcode'].apply(get_post_url)
        
        # Renombrar columnas
        display_df = display_df.rename(columns={
            'company': 'Empresa',
            'title': 'Posicion',
            'area': 'Area',
            'post_date': 'Fecha',
            'is_open': 'Estado',
            'url': 'Enlace'
        })
        
        # Crear enlaces clicables
        def make_clickable(url: str, text: str = "Ver Post") -> str:
            return f'<a href="{url}" target="_blank">{text}</a>'
        
        display_df['Enlace'] = display_df.apply(
            lambda x: make_clickable(x['Enlace']), axis=1
        )
        
        # Mostrar tabla con las 10 ofertas mas recientes
        st.write(
            display_df.head(10).to_html(escape=False, index=False),
            unsafe_allow_html=True
        )
        
        # Enlace para ver todas las ofertas
        if len(job_df) > 10:
            st.write(f"Mostrando 10 de {len(job_df)} ofertas. ")
            st.button("Ver todas las ofertas", key="ver_todas")
    else:
        st.info("No hay ofertas laborales registradas.")
