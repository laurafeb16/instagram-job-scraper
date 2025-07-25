# -*- coding: utf-8 -*-
"""
Utilidad para gestionar múltiples páginas en una aplicación Streamlit.
"""
from typing import Callable, Dict, List, Optional
import streamlit as st

class MultiPage:
    """Clase para gestionar múltiples páginas en aplicaciones Streamlit."""
    
    def __init__(self, app_title: str, app_icon: str = "📊") -> None:
        """Inicializa el gestor de páginas.
        
        Args:
            app_title: Título de la aplicación
            app_icon: Icono para la aplicación
        """
        self.pages: List[Dict[str, object]] = []
        self.app_title = app_title
        self.app_icon = app_icon
        
        # Configurar página
        st.set_page_config(
            page_title=app_title,
            page_icon=app_icon,
            layout="wide",
            initial_sidebar_state="expanded"
        )
    
    def add_page(self, title: str, func: Callable, icon: Optional[str] = None) -> None:
        """Agrega una página a la aplicación.
        
        Args:
            title: Título de la página
            func: Función que renderiza la página
            icon: Icono opcional para la página
        """
        self.pages.append({
            "title": title,
            "function": func,
            "icon": icon or "📄"
        })
    
    def run(self) -> None:
        """Ejecuta la aplicación mostrando la página seleccionada."""
        # Título principal
        st.title(f"{self.app_icon} {self.app_title}")
        
        # Sidebar para navegación
        st.sidebar.title("Navegación")
        
        # Selector de página
        page = st.sidebar.radio(
            "Ir a",
            self.pages,
            format_func=lambda page: f"{page['icon']} {page['title']}"
        )
        
        # Mostrar la página seleccionada
        page["function"]()
        
        # Información en el sidebar
        st.sidebar.markdown("---")
        st.sidebar.info(
            "Este dashboard analiza ofertas de trabajo extraídas de perfiles "
            "de Instagram de facultades universitarias."
        )
        
        # Métricas en el sidebar
        st.sidebar.markdown("### Métricas Globales")
        # Estos valores se actualizarán con datos reales cuando conectemos la BD
        st.sidebar.metric("Total de Ofertas", "0")
        st.sidebar.metric("Perfiles Analizados", "0")
        st.sidebar.metric("Última Actualización", "Nunca")
