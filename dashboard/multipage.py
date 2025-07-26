# -*- coding: utf-8 -*-
"""
Utilidad para gestionar multiples paginas en una aplicacion Streamlit.
"""
from typing import Callable, Dict, List, Optional
import streamlit as st

class MultiPage:
    """Clase para gestionar multiples paginas en aplicaciones Streamlit."""
    
    def __init__(self, app_title: str, app_icon: str = "📊") -> None:
        """Inicializa el gestor de paginas.
        
        Args:
            app_title: Titulo de la aplicacion
            app_icon: Icono para la aplicacion
        """
        self.pages: List[Dict[str, object]] = []
        self.app_title = app_title
        self.app_icon = app_icon
        
        # Configurar pagina
        st.set_page_config(
            page_title=app_title,
            page_icon=app_icon,
            layout="wide",
            initial_sidebar_state="expanded"
        )
    
    def add_page(self, title: str, func: Callable, icon: Optional[str] = None) -> None:
        """Agrega una pagina a la aplicacion.
        
        Args:
            title: Titulo de la pagina
            func: Funcion que renderiza la pagina
            icon: Icono opcional para la pagina
        """
        self.pages.append({
            "title": title,
            "function": func,
            "icon": icon or "📄"
        })
    
    def run(self) -> None:
        """Ejecuta la aplicacion mostrando la pagina seleccionada."""
        # Titulo principal
        st.title(f"{self.app_icon} {self.app_title}")
        
        # Sidebar para navegacion
        st.sidebar.title("Navegacion")
        
        # Selector de pagina
        page = st.sidebar.radio(
            "Ir a",
            self.pages,
            format_func=lambda page: f"{page['icon']} {page['title']}"
        )
        
        # Mostrar la pagina seleccionada
        page["function"]()
        
        # Informacion en el sidebar
        st.sidebar.markdown("---")
        st.sidebar.info(
            "Este dashboard analiza ofertas de trabajo extraidas de perfiles "
            "de Instagram de facultades universitarias."
        )
        
        # Metricas en el sidebar
        st.sidebar.markdown("### Metricas Globales")
        # Estos valores se actualizaran con datos reales cuando conectemos la BD
        st.sidebar.metric("Total de Ofertas", "0")
        st.sidebar.metric("Perfiles Analizados", "0")
        st.sidebar.metric("Ultima Actualizacion", "Nunca")
