# -*- coding: utf-8 -*-
"""
Clase para manejar múltiples páginas en Streamlit.
"""
import streamlit as st

class MultiPage:
    """Clase para gestionar múltiples páginas en aplicaciones Streamlit."""
    
    def __init__(self):
        """Constructor que inicializa la lista de páginas."""
        self.pages = []
    
    def add_page(self, title, func):
        """Agrega una página a la aplicación.
        
        Args:
            title (str): Título de la página
            func (function): Función que renderiza la página
        """
        self.pages.append({
            "title": title,
            "function": func
        })
    
    def run(self):
        """Ejecuta la aplicación renderizando la página seleccionada."""
        # Sidebar para selección de página
        st.sidebar.title("Navegación")
        
        page = st.sidebar.radio(
            'Selecciona una página:',
            self.pages,
            format_func=lambda page: page["title"]
        )
        
        # Display the selected page
        page["function"]()
        
        # Agregar información adicional en el sidebar
        st.sidebar.markdown("---")
        st.sidebar.info(
            "Este dashboard analiza ofertas de trabajo extraídas de Instagram."
        )
