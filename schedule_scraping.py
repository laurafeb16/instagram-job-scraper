# -*- coding: utf-8 -*-
"""
Script para programar la extracción periódica de datos de Instagram.
"""
import schedule
import time
import argparse
import logging
import os
import sys
from datetime import datetime
from typing import List, Optional

# Añadir directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import run_scraper
from backend.config import SCRAPE_INTERVAL_HOURS
from backend.logging_config import setup_logging, get_logger

# Configurar logging
setup_logging()
logger = get_logger(__name__)

def schedule_scraping(usernames: List[str], interval_hours: int = SCRAPE_INTERVAL_HOURS, 
                     max_posts: int = 20) -> None:
    """Programa la extracción periódica de datos de perfiles de Instagram.
    
    Args:
        usernames: Lista de usernames a scrapear
        interval_hours: Intervalo en horas entre ejecuciones
        max_posts: Número máximo de posts a extraer por perfil
    """
    def job() -> None:
        """Tarea a ejecutar según la programación."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"Iniciando scraping programado ({timestamp})")
        
        for username in usernames:
            try:
                logger.info(f"Procesando perfil: {username}")
                posts_count = run_scraper(username, max_posts=max_posts)
                logger.info(f"Se procesaron {posts_count} posts de {username}")
            except Exception as e:
                logger.error(f"Error al procesar {username}: {e}")
        
        logger.info(f"Scraping programado completado ({timestamp})")
    
    # Ejecutar inmediatamente la primera vez
    logger.info(f"Ejecutando scraping inicial para {len(usernames)} perfiles")
    job()
    
    # Programar ejecuciones periódicas
    schedule.every(interval_hours).hours.do(job)
    logger.info(f"Scraping programado cada {interval_hours} horas")
    
    # Mantener el script en ejecución
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Verificar cada minuto
    except KeyboardInterrupt:
        logger.info("Programa detenido manualmente")

def main() -> None:
    """Función principal."""
    parser = argparse.ArgumentParser(description="Programar scraping periódico de Instagram")
    parser.add_argument("--usernames", "-u", nargs="+", required=True,
                        help="Usernames de perfiles a scrapear")
    parser.add_argument("--interval", "-i", type=int, default=SCRAPE_INTERVAL_HOURS,
                        help=f"Intervalo en horas (default: {SCRAPE_INTERVAL_HOURS})")
    parser.add_argument("--max-posts", "-m", type=int, default=20,
                        help="Número máximo de posts a extraer por perfil")
    
    args = parser.parse_args()
    
    if not args.usernames:
        parser.error("Debe especificar al menos un username")
    
    schedule_scraping(args.usernames, args.interval, args.max_posts)

if __name__ == "__main__":
    main()
