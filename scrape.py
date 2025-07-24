#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script principal para ejecutar el scraper de ofertas de trabajo en Instagram.
"""
import sys
import argparse
import logging
from backend.main import run_scraper

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("instagram_scraper.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Función principal para ejecutar el scraper desde línea de comandos"""
    parser = argparse.ArgumentParser(description="Instagram Job Scraper")
    parser.add_argument("--username", "-u", required=True, 
                        help="Nombre de usuario de Instagram a analizar")
    parser.add_argument("--posts", "-p", type=int, default=10,
                        help="Número máximo de posts a analizar")
    parser.add_argument("--headless", action="store_true",
                        help="Ejecutar en modo headless (sin interfaz gráfica)")
    parser.add_argument("--save-browser", action="store_true",
                        help="Guardar la sesión del navegador")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Mostrar información detallada")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        result = run_scraper(
            username=args.username,
            max_posts=args.posts,
            headless=args.headless,
            save_browser=args.save_browser
        )
        
        if result:
            logger.info(f"Scraping completado. Se procesaron {result} posts.")
            return 0
        else:
            logger.error("Error en el proceso de scraping.")
            return 1
    except KeyboardInterrupt:
        logger.info("Proceso interrumpido por el usuario.")
        return 130
    except Exception as e:
        logger.exception(f"Error no controlado: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())