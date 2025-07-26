# -*- coding: utf-8 -*-
"""
Pagina de analisis de tendencias.
"""
from typing import Dict, List, Any
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import numpy as np

from dashboard.utils.helpers import (
    get_job_posts_df,
    get_area_stats,
    get_company_stats,
    get_skills_stats
)

def app() -> None:
    """Renderiza la pagina de analisis de tendencias."""
    st.header("Analisis de Tendencias")
    
    # Obtener datos
    job_df = get_job_posts_df()
    _, area_counts = get_area_stats()
    company_df = get_company_stats()
    skill_counts = get_skills_stats()
    
    if job_df.empty:
        st.warning("No hay datos suficientes para mostrar tendencias.")
        return
    
    # Crear pestanas
    tab1, tab2, tab3 = st.tabs(["Habilidades", "Empresas", "Areas"])
    
    with tab1:
        st.subheader("Habilidades mas demandadas")
        
        if skill_counts:
            # Crear dos columnas
            col1, col2 = st.columns([3, 2])
            
            with col1:
                # Grafico de barras de habilidades
                skills_df = pd.DataFrame({
                    'Habilidad': list(skill_counts.keys()),
                    'Frecuencia': list(skill_counts.values())
                })
                
                fig = px.bar(
                    skills_df.head(15),
                    x='Frecuencia',
                    y='Habilidad',
                    orientation='h',
                    title="Top 15 Habilidades",
                    color='Frecuencia',
                    color_continuous_scale=px.colors.sequential.Viridis
                )
                st.plotly_chart(fig)
            
            with col2:
                # Nube de palabras
                wordcloud = WordCloud(
                    width=800,
                    height=400,
                    background_color='white',
                    colormap='viridis',
                    max_words=100
                ).generate_from_frequencies(skill_counts)
                
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.imshow(wordcloud, interpolation='bilinear')
                ax.axis('off')
                st.pyplot(fig)
        else:
            st.info("No hay datos suficientes para mostrar estadisticas de habilidades.")
    
    with tab2:
        st.subheader("Empresas con mas ofertas")
        
        if not company_df.empty:
            # Grafico de empresas
            fig = px.bar(
                company_df.head(10),
                x='count',
                y='company',
                orientation='h',
                title="Top 10 Empresas",
                color='count',
                color_continuous_scale=px.colors.sequential.Plasma,
                labels={'count': 'Numero de Ofertas', 'company': 'Empresa'}
            )
            st.plotly_chart(fig)
            
            # Tabla de empresas
            st.dataframe(
                company_df.rename(columns={
                    'company': 'Empresa',
                    'count': 'Ofertas',
                    'percentage': '% del Total'
                })
            )
        else:
            st.info("No hay datos suficientes para mostrar estadisticas de empresas.")
    
    with tab3:
        st.subheader("Distribucion por Areas Tecnologicas")
        
        if area_counts:
            # Grafico de areas
            areas_df = pd.DataFrame({
                'Area': list(area_counts.keys()),
                'Ofertas': list(area_counts.values())
            })
            
            # Grafico de pastel interactivo
            fig = px.pie(
                areas_df,
                names='Area',
                values='Ofertas',
                title="Distribucion por Area",
                color_discrete_sequence=px.colors.qualitative.Bold
            )
            st.plotly_chart(fig)
            
            # Tendencia temporal (simplificada)
            if 'post_date' in job_df.columns and 'area' in job_df.columns:
                # Convertir a datetime si no lo es
                if not pd.api.types.is_datetime64_any_dtype(job_df['post_date']):
                    job_df['post_date'] = pd.to_datetime(job_df['post_date'])
                
                # Agrupar por mes y area
                job_df['month'] = job_df['post_date'].dt.to_period('M')
                trend_df = job_df.groupby(['month', 'area']).size().reset_index(name='count')
                
                # Convertir Period a string para plotly
                trend_df['month'] = trend_df['month'].astype(str)
                
                # Crear grafico de lineas
                fig = px.line(
                    trend_df,
                    x='month',
                    y='count',
                    color='area',
                    title="Evolucion Temporal por Area",
                    labels={'month': 'Mes', 'count': 'Ofertas', 'area': 'Area'}
                )
                st.plotly_chart(fig)
        else:
            st.info("No hay datos suficientes para mostrar estadisticas por area.")
