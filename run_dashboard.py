#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para ejecutar el dashboard de visualizacion.
"""
import os
import sys
import subprocess
import argparse
from typing import List, Optional

def check_dependencies() -> bool:
    """Verifica si las dependencias necesarias estan instaladas.
    
    Returns:
        True si todas las dependencias estan instaladas, False en caso contrario
    """
    try:
        import streamlit
        import plotly
        import pandas
        import matplotlib
        import sqlalchemy
        return True
    except ImportError:
        return False

def install_dependencies() -> bool:
    """Instala las dependencias necesarias para el dashboard.
    
    Returns:
        True si la instalacion fue exitosa, False en caso contrario
    """
    req_file = "requirements-dashboard.txt"
    
    if not os.path.exists(req_file):
        print(f"Archivo {req_file} no encontrado. Creando archivo con dependencias basicas...")
        with open(req_file, "w") as f:
            f.write("streamlit>=1.31.0\n")
            f.write("plotly>=5.18.0\n")
            f.write("pandas>=2.1.0\n")
            f.write("matplotlib>=3.8.0\n")
            f.write("sqlalchemy>=2.0.0\n")
    
    print(f"Instalando dependencias desde {req_file}...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", req_file], check=True)
        return True
    except subprocess.CalledProcessError:
        print("Error al instalar dependencias. Intentando instalar dependencias minimas...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "streamlit", "pandas", "plotly"], check=True)
            return True
        except subprocess.CalledProcessError:
            return False

def main() -> None:
    """Funcion principal para ejecutar el dashboard."""
    parser = argparse.ArgumentParser(description="Ejecutar dashboard de visualizacion")
    parser.add_argument("--port", "-p", type=int, default=8501,
                        help="Puerto para el servidor (por defecto: 8501)")
    parser.add_argument("--no-deps-check", action="store_true",
                        help="Omitir verificacion de dependencias")
    args = parser.parse_args()
    
    # Verificar dependencias
    if not args.no_deps_check and not check_dependencies():
        print("Faltan dependencias necesarias para el dashboard.")
        if not install_dependencies():
            print("No se pudieron instalar las dependencias. Por favor, instale manualmente:")
            print("pip install streamlit pandas plotly matplotlib sqlalchemy")
            return
    
    # Ejecutar streamlit
    cmd: List[str] = ["streamlit", "run", "dashboard/app.py", "--server.port", str(args.port)]
    print(f"Ejecutando: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError:
        print("Error: No se encontro el ejecutable de streamlit.")
        print("Por favor, asegurese de que streamlit esta instalado correctamente.")
        print("pip install streamlit")
    except subprocess.CalledProcessError as e:
        print(f"Error al ejecutar el dashboard: {e}")

if __name__ == "__main__":
    main()
