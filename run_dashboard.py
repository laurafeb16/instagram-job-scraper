#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para ejecutar el dashboard de visualización.
"""
import os
import subprocess
import argparse

def main() -> None:
    """Función principal para ejecutar el dashboard."""
    parser = argparse.ArgumentParser(description="Ejecutar dashboard de visualización")
    parser.add_argument("--port", "-p", type=int, default=8501,
                        help="Puerto para el servidor (por defecto: 8501)")
    args = parser.parse_args()
    
    # Ejecutar streamlit
    cmd = ["streamlit", "run", "dashboard/app.py", "--server.port", str(args.port)]
    print(f"Ejecutando: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

if __name__ == "__main__":
    main()