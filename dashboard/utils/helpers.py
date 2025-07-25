# -*- coding: utf-8 -*-
"""
Funciones auxiliares para el dashboard.
"""
from typing import Dict, List, Any, Tuple, Optional
import pandas as pd
import streamlit as st
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from backend import models
from backend.database import SessionLocal
from backend.logging_config import get_logger

# Configurar logger
logger = get_logger(__name__)

@st.cache_data(ttl=600)
def get_job_posts_df() -> pd.DataFrame:
    """Obtiene un DataFrame con todas las ofertas laborales.
    
    Returns:
        DataFrame con ofertas laborales
    """
    try:
        db = SessionLocal()
        # Consultar ofertas con información de posts y perfiles
        query = (
            db.query(
                models.JobPost.id,
                models.JobPost.company,
                models.JobPost.title,
                models.JobPost.area,
                models.JobPost.skills,
                models.JobPost.benefits,
                models.JobPost.deadline,
                models.JobPost.is_open,
                models.JobPost.created_at,
                models.JobPost.updated_at,
                models.Post.shortcode,
                models.Post.caption,
                models.Post.timestamp.label('post_date'),
                models.InstagramProfile.username
            )
            .join(models.Post)
            .join(models.InstagramProfile)
            .order_by(desc(models.JobPost.created_at))
        )
        
        # Convertir a DataFrame
        df = pd.read_sql(query.statement, db.bind)
        
        # Cerrar sesión
        db.close()
        
        return df
    except Exception as e:
        logger.error(f"Error al obtener DataFrame de ofertas: {e}")
        # Devolver DataFrame vacío en caso de error
        return pd.DataFrame()

@st.cache_data(ttl=600)
def get_area_stats() -> Tuple[pd.DataFrame, Dict[str, int]]:
    """Obtiene estadísticas por área tecnológica.
    
    Returns:
        DataFrame con estadísticas por área y diccionario con conteos
    """
    try:
        db = SessionLocal()
        # Consultar conteo por área
        query = (
            db.query(
                models.JobPost.area,
                func.count(models.JobPost.id).label('count')
            )
            .group_by(models.JobPost.area)
        )
        
        # Convertir a DataFrame
        df = pd.read_sql(query.statement, db.bind)
        
        # Crear diccionario para acceso rápido
        area_counts = dict(zip(df['area'], df['count']))
        
        # Calcular porcentajes
        if not df.empty:
            total = df['count'].sum()
            df['percentage'] = df['count'] / total * 100
        
        # Cerrar sesión
        db.close()
        
        return df, area_counts
    except Exception as e:
        logger.error(f"Error al obtener estadísticas por área: {e}")
        # Devolver DataFrame vacío en caso de error
        return pd.DataFrame(), {}

@st.cache_data(ttl=600)
def get_company_stats() -> pd.DataFrame:
    """Obtiene estadísticas por empresa.
    
    Returns:
        DataFrame con estadísticas por empresa
    """
    try:
        db = SessionLocal()
        # Consultar conteo por empresa
        query = (
            db.query(
                models.JobPost.company,
                func.count(models.JobPost.id).label('count')
            )
            .filter(models.JobPost.company.isnot(None))
            .group_by(models.JobPost.company)
            .order_by(desc('count'))
            .limit(10)
        )
        
        # Convertir a DataFrame
        df = pd.read_sql(query.statement, db.bind)
        
        # Calcular porcentajes
        if not df.empty:
            total = db.query(func.count(models.JobPost.id)).scalar()
            df['percentage'] = df['count'] / total * 100
        
        # Cerrar sesión
        db.close()
        
        return df
    except Exception as e:
        logger.error(f"Error al obtener estadísticas por empresa: {e}")
        # Devolver DataFrame vacío en caso de error
        return pd.DataFrame()

@st.cache_data(ttl=600)
def get_skills_stats() -> Dict[str, int]:
    """Obtiene frecuencia de habilidades solicitadas.
    
    Returns:
        Diccionario con habilidades y su frecuencia
    """
    try:
        # Obtener DataFrame de ofertas
        df = get_job_posts_df()
        
        # Extraer y contar habilidades
        skill_counts: Dict[str, int] = {}
        
        if not df.empty and 'skills' in df.columns:
            for skills_list in df['skills']:
                if isinstance(skills_list, list):
                    for skill in skills_list:
                        skill_counts[skill] = skill_counts.get(skill, 0) + 1
        
        # Ordenar por frecuencia
        skill_counts = dict(sorted(
            skill_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:20])  # Limitar a 20 habilidades
        
        return skill_counts
    except Exception as e:
        logger.error(f"Error al obtener estadísticas de habilidades: {e}")
        return {}

@st.cache_data(ttl=600)
def get_dashboard_metrics() -> Dict[str, Any]:
    """Obtiene métricas globales para el dashboard.
    
    Returns:
        Diccionario con métricas globales
    """
    try:
        db = SessionLocal()
        
        # Total de ofertas
        total_jobs = db.query(func.count(models.JobPost.id)).scalar() or 0
        
        # Ofertas abiertas
        open_jobs = db.query(func.count(models.JobPost.id)).filter(
            models.JobPost.is_open == True
        ).scalar() or 0
        
        # Total de perfiles
        profiles_count = db.query(func.count(models.InstagramProfile.id)).scalar() or 0
        
        # Última actualización
        last_scrape = db.query(func.max(models.InstagramProfile.last_scraped)).scalar()
        
        # Cerrar sesión
        db.close()
        
        return {
            'total_jobs': total_jobs,
            'open_jobs': open_jobs,
            'profiles_count': profiles_count,
            'last_scrape': last_scrape
        }
    except Exception as e:
        logger.error(f"Error al obtener métricas globales: {e}")
        return {
            'total_jobs': 0,
            'open_jobs': 0,
            'profiles_count': 0,
            'last_scrape': None
        }

def get_post_url(shortcode: str) -> str:
    """Obtiene la URL completa de un post de Instagram.
    
    Args:
        shortcode: Código corto del post
        
    Returns:
        URL completa del post
    """
    return f"https://www.instagram.com/p/{shortcode}/"