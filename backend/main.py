# -*- coding: utf-8 -*-
"""
Modulo principal que coordina el proceso de scraping, OCR y extraccion de ofertas.
"""
import os
import json
import logging
from typing import List, Dict, Optional, Union
from datetime import datetime

from backend.scraper import InstagramScraper
from backend.ocr_processor import OCRProcessor
from backend.job_extractor import JobExtractor, extract_job_data

logger = logging.getLogger(__name__)

def process_posts(posts: List[Dict], processor: OCRProcessor, extractor: JobExtractor) -> List[Dict]:
    """Procesa los posts descargados con OCR y extraccion de informacion.
    
    Args:
        posts (List[Dict]): Lista de posts descargados
        processor (OCRProcessor): Procesador OCR
        extractor (JobExtractor): Extractor de ofertas
        
    Returns:
        List[Dict]: Posts procesados con informacion de ofertas
    """
    processed_posts = []
    
    for post in posts:
        try:
            shortcode = post.get('shortcode')
            local_image_path = post.get('local_image_path')
            
            if not local_image_path or not os.path.exists(local_image_path):
                logger.warning(f"Imagen no encontrada para post {shortcode}")
                continue
            
            # Extraer texto con OCR
            logger.info(f"Procesando OCR para post {shortcode}")
            ocr_text = processor.extract_text(local_image_path)
            
            # Verificar si es oferta laboral
            is_job_post, company = extractor.is_job_post(post.get('caption', '') + "\n" + ocr_text)
            
            if is_job_post:
                logger.info(f"Detectada oferta laboral en post {shortcode}")
                
                # Extraer informacion estructurada
                job_info = extract_job_data(ocr_text, post.get('caption', ''))
                
                # Si no se detecto empresa en el extractor estructurado, usar la detectada en is_job_post
                if not job_info['company'] and company and company != "Desconocida":
                    job_info['company'] = company
                
                # Anadir informacion de la oferta al post
                post['is_job_post'] = True
                post['job_info'] = job_info
                post['ocr_text'] = ocr_text
                
                # Actualizar el archivo JSON
                json_path = os.path.join('data/raw', f"{shortcode}.json")
                if os.path.exists(json_path):
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(post, f, ensure_ascii=False, indent=2)
                
                processed_posts.append(post)
            else:
                logger.info(f"Post {shortcode} no es una oferta laboral")
                post['is_job_post'] = False
                
                # Actualizar el archivo JSON de igual forma
                json_path = os.path.join('data/raw', f"{shortcode}.json")
                if os.path.exists(json_path):
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(post, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"Error al procesar post {post.get('shortcode')}: {e}")
    
    return processed_posts

def run_scraper(username: str, max_posts: int = 10, headless: bool = False, save_browser: bool = False) -> int:
    """Ejecuta el proceso completo de scraping.
    
    Args:
        username (str): Nombre de usuario de Instagram a analizar
        max_posts (int): Numero maximo de posts a analizar
        headless (bool): Si se ejecuta en modo headless
        save_browser (bool): Si se guarda la sesion del navegador
        
    Returns:
        int: Numero de posts procesados
    """
    try:
        # Inicializar componentes
        scraper = InstagramScraper(headless=headless)
        processor = OCRProcessor()
        extractor = JobExtractor()
        
        # Extraer posts
        logger.info(f"Iniciando scraping de {max_posts} posts de @{username}")
        posts = scraper.scrape_profile(username, max_posts)
        
        if not posts:
            logger.warning(f"No se encontraron posts para @{username}")
            return 0
        
        logger.info(f"Se encontraron {len(posts)} posts")
        
        # Procesar posts para OCR y extraccion de ofertas
        job_posts = process_posts(posts, processor, extractor)
        
        logger.info(f"Se identificaron {len(job_posts)} ofertas de trabajo")
        
        # Generar informe
        report = {
            "username": username,
            "total_posts_scraped": len(posts),
            "job_posts_found": len(job_posts),
            "scrape_date": datetime.now().isoformat(),
            "job_posts": [
                {
                    "shortcode": post.get('shortcode'),
                    "company": post.get('job_info', {}).get('company'),
                    "title": post.get('job_info', {}).get('title'),
                    "url": post.get('post_url')
                }
                for post in job_posts
            ]
        }
        
        # Guardar informe
        os.makedirs('data', exist_ok=True)
        report_path = f"data/report_{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Informe guardado en {report_path}")
        
        return len(posts)
    
    except Exception as e:
        logger.exception(f"Error en el proceso de scraping: {e}")
        return 0
    
    finally:
        if not save_browser and 'scraper' in locals():
            scraper.close()
