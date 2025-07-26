# -*- coding: utf-8 -*-
"""
Aplicacion principal del dashboard para visualizacion de ofertas laborales.
"""
import streamlit as st
from typing import Dict, List, Any

from dashboard.multipage import MultiPage
from dashboard.pages import home, trends
from dashboard.utils.helpers import get_dashboard_metrics

# Inicializar aplicacion multipagina
app = MultiPage(
    app_title="Instagram Job Analytics",
    app_icon="💼"
)

# Agregar paginas
app.add_page("Inicio", home.app, "🏠")
app.add_page("Tendencias", trends.app, "📊")

# Ejecutar la aplicacion
def main() -> None:
    """Funcion principal que ejecuta el dashboard."""
    # Actualizar metricas en el sidebar
    metrics = get_dashboard_metrics()
    
    # Ejecutar el app
    app.run()

if __name__ == "__main__":
    main()
