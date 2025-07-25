# -*- coding: utf-8 -*-
"""
Módulo principal que coordina el proceso de scraping, OCR y extracción de ofertas.
"""
import os
import json
from typing import List, Dict, Optional, Union, Any, Iterator
from datetime import datetime
from sqlalchemy.orm import Session

from backend.logging_config import get_logger, with_correlation_id
from backend.metrics import (
    POSTS_SCRAPED, JOBS_EXTRACTED, FAILED_SCRAPES, 
    update_extraction_success_rate, ACTIVE_SCRAPING_JOBS
)
from backend.scraper import InstagramScraper
from backend.ocr_processor import OCRProcessor
from backend.job_extractor import JobExtractor, extract_job_data
from backend.database import get_db
from backend import crud, models, schemas

# Configurar logger
logger = get_logger(__name__)

@with_correlation_id
def process_posts(
    posts: List[Dict[str, Any]], 
    processor: OCRProcessor, 
    extractor: JobExtractor,
    db: Optional[Session] = None,
    logger: Any = None
) -> List[Dict[str, Any]]:
    """Procesa los posts descargados con OCR y extracción de información.
    
    Args:
        posts: Lista de posts descargados
        processor: Procesador OCR
        extractor: Extractor de ofertas
        db: Sesión de base de datos opcional
        logger: Logger configurado
        
    Returns:
        Posts procesados con información de ofertas
    """
    processed_posts = []
    job_count = 0
    total_count = len(posts)
    
    # Obtener conexión a BD si no se proporcionó
    close_db = False
    if db is None and 'profile_id' in posts[0]:  # Si queremos persistir en BD
        db_gen = get_db()
        db = next(db_gen)
        close_db = True
    
    for post in posts:
        try:
            shortcode = post.get('shortcode')
            local_image_path = post.get('local_image_path')
            profile_id = post.get('profile_id')  # Puede ser None si no usamos BD
            
            logger.info("Procesando post", shortcode=shortcode)
            
            if not local_image_path or not os.path.exists(local_image_path):
                logger.warning("Imagen no encontrada", shortcode=shortcode, path=local_image_path)
                continue
            
            # Extraer texto con OCR
            ocr_text = processor.extract_text(local_image_path)
            post['ocr_text'] = ocr_text
            
            # Verificar si es oferta laboral
            is_job_post, company = extractor.is_job_post(
                post.get('caption', '') + "\n" + ocr_text
            )
            
            if is_job_post:
                logger.info("Detectada oferta laboral", 
                           shortcode=shortcode, 
                           company=company)
                job_count += 1
                
                # Extraer información estructurada
                job_info = extract_job_data(ocr_text, post.get('caption', ''))
                
                # Si no se detectó empresa en el extractor estructurado, usar la detectada en is_job_post
                if not job_info['company'] and company and company != "Desconocida":
                    job_info['company'] = company
                
                # Añadir información de la oferta al post
                post['is_job_post'] = True
                post['job_info'] = job_info
                
                # Persistir en base de datos si tenemos conexión y profile_id
                if db is not None and profile_id is not None:
                    # Verificar si el post ya existe
                    db_post = crud.post.get_by_shortcode(db, shortcode)
                    
                    if not db_post:
                        # Crear post
                        post_in = schemas.PostCreate(
                            profile_id=profile_id,
                            shortcode=shortcode,
                            caption=post.get('caption'),
                            timestamp=post.get('timestamp'),
                            image_path=local_image_path,
                            ocr_text=ocr_text,
                            is_job_post=True
                        )
                        db_post = crud.post.create(db, obj_in=post_in.dict())
                        logger.debug("Post creado en BD", post_id=db_post.id)
                    else:
                        # Actualizar post existente
                        post_update = schemas.PostUpdate(
                            ocr_text=ocr_text,
                            is_job_post=True
                        )
                        db_post = crud.post.update(db, db_obj=db_post, obj_in=post_update.dict(exclude_unset=True))
                        logger.debug("Post actualizado en BD", post_id=db_post.id)
                    
                    # Crear o actualizar oferta laboral
                    if db_post.job:
                        # Actualizar oferta existente
                        job_update = schemas.JobPostUpdate(
                            company=job_info['company'],
                            title=job_info['title'],
                            area=job_info['area'],
                            skills=job_info['skills'],
                            benefits=job_info['benefits'],
                            deadline=job_info['deadline'],
                            is_open=job_info['is_open']
                        )
                        crud.job_post.update(db, db_obj=db_post.job, obj_in=job_update.dict(exclude_unset=True))
                        logger.debug("Oferta laboral actualizada", job_id=db_post.job.id)
                    else:
                        # Crear nueva oferta
                        job_in = schemas.JobPostCreate(
                            post_id=db_post.id,
                            company=job_info['company'],
                            title=job_info['title'],
                            area=job_info['area'],
                            skills=job_info['skills'],
                            benefits=job_info['benefits'],
                            deadline=job_info['deadline'],
                            is_open=job_info['is_open']
                        )
                        db_job = crud.job_post.create(db, obj_in=job_in.dict())
                        logger.debug("Oferta laboral creada", job_id=db_job.id)
                
                # Actualizar archivo JSON
                json_path = os.path.join('data/raw', f"{shortcode}.json")
                if os.path.exists(json_path):
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(post, f, ensure_ascii=False, indent=2)
                
                processed_posts.append(post)
            else:
                logger.info("Post no es oferta laboral", shortcode=shortcode)
                post['is_job_post'] = False
                
                # Persistir en base de datos si tenemos conexión y profile_id
                if db is not None and profile_id is not None:
                    # Verificar si el post ya existe
                    db_post = crud.post.get_by_shortcode(db, shortcode)
                    
                    if not db_post:
                        # Crear post normal
                        post_in = schemas.PostCreate(
                            profile_id=profile_id,
                            shortcode=shortcode,
                            caption=post.get('caption'),
                            timestamp=post.get('timestamp'),
                            image_path=local_image_path,
                            ocr_text=ocr_text,
                            is_job_post=False
                        )
                        db_post = crud.post.create(db, obj_in=post_in.dict())
                        logger.debug("Post regular creado en BD", post_id=db_post.id)
                
                # Actualizar el archivo JSON de igual forma
                json_path = os.path.join('data/raw', f"{shortcode}.json")
                if os.path.exists(json_path):
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(post, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error("Error al procesar post", 
                        shortcode=post.get('shortcode'), 
                        error=str(e),
                        exc_info=True)
    
    # Cerrar conexión si la abrimos aquí
    if close_db and db is not None:
        db.close()
    
    # Actualizar métricas
    if total_count > 0:
        update_extraction_success_rate(job_count, total_count)
    
    return processed_posts

@with_correlation_id
def run_scraper(
    username: str, 
    max_posts: int = 10, 
    headless: bool = False, 
    save_browser: bool = False,
    logger: Any = None
) -> int:
    """Ejecuta el proceso completo de scraping.
    
    Args:
        username: Nombre de usuario de Instagram a analizar
        max_posts: Número máximo de posts a analizar
        headless: Si se ejecuta en modo headless
        save_browser: Si se guarda la sesión del navegador
        logger: Logger configurado
        
    Returns:
        Número de posts procesados
    """
    ACTIVE_SCRAPING_JOBS.inc()
    
    try:
        # Inicializar componentes
        scraper = InstagramScraper(headless=headless)
        processor = OCRProcessor()
        extractor = JobExtractor()
        
        # Obtener o crear perfil en BD
        db = next(get_db())
        profile = crud.profile.get_or_create(db, username)
        
        # Extraer posts
        logger.info("Iniciando scraping", username=username, max_posts=max_posts)
        posts = scraper.scrape_profile(username, max_posts)
        
        if not posts:
            logger.warning("No se encontraron posts", username=username)
            ACTIVE_SCRAPING_JOBS.dec()
            return 0
        
        logger.info(f"Posts encontrados", count=len(posts))
        POSTS_SCRAPED.inc(len(posts))
        
        # Añadir profile_id a los posts para persistencia
        for post in posts:
            post['profile_id'] = profile.id
        
        # Procesar posts para OCR y extracción de ofertas
        job_posts = process_posts(posts, processor, extractor, db)
        
        logger.info("Ofertas encontradas", count=len(job_posts))
        
        # Actualizar última fecha de scraping
        crud.profile.update_last_scraped(db, profile.id)
        
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
            
        logger.info("Informe guardado", path=report_path)
        
        return len(posts)
    
    except Exception as e:
        logger.exception("Error en el proceso de scraping", error=str(e))
        FAILED_SCRAPES.inc()
        return 0
    
    finally:
        ACTIVE_SCRAPING_JOBS.dec()
        if not save_browser and 'scraper' in locals():
            scraper.close()
