# -*- coding: utf-8 -*-
"""
Aplicación principal del dashboard para visualización de ofertas laborales.
"""
import streamlit as st
from typing import Dict, List, Any

from dashboard.multipage import MultiPage
from dashboard.pages import home, trends
from dashboard.utils.helpers import get_dashboard_metrics

# Inicializar aplicación multipágina
app = MultiPage(
    app_title="Instagram Job Analytics",
    app_icon="💼"
)

# Agregar páginas
app.add_page("Inicio", home.app, "🏠")
app.add_page("Tendencias", trends.app, "📊")

# Ejecutar la aplicación
def main() -> None:
    """Función principal que ejecuta el dashboard."""
    # Actualizar métricas en el sidebar
    metrics = get_dashboard_metrics()
    
    # Ejecutar el app
    app.run()

if __name__ == "__main__":
    main()
