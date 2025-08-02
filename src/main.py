# -*- coding: utf-8 -*-
import os
import sys
import logging
from dotenv import load_dotenv
from datetime import datetime

# Añadir el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.scraper.instagram_scraper import InstagramScraper
from src.image_processing.ocr import EnhancedImageProcessor
from src.database.models import init_db, JobPost, JobData, CarouselImage
from src.text_analysis.job_analyzer import is_job_post, extract_job_data
from src.utils.helpers import save_image_from_url

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("main.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

def main():
    # Obtener credenciales desde variables de entorno
    username = os.getenv("INSTAGRAM_USERNAME")
    password = os.getenv("INSTAGRAM_PASSWORD")
    target_account = os.getenv("TARGET_ACCOUNT")
    
    if not all([username, password, target_account]):
        logger.error("Faltan credenciales. Configura las variables de entorno.")
        return
    
    # Iniciar el scraper
    logger.info("Iniciando scraper de Instagram")
    scraper = InstagramScraper(username, password, target_account, headless=False)
    
    try:
        # Login
        if not scraper.login():
            logger.error("Fallo en el login. Abortando.")
            return
        
        # Navegar a la cuenta objetivo
        if not scraper.navigate_to_target_account():
            logger.error("Fallo al navegar a la cuenta objetivo. Abortando.")
            return
        
        # Extraer posts (límite de 5 para prueba)
        posts = scraper.scrape_posts(limit=5)
        
        if not posts:
            logger.error("No se pudieron extraer posts. Abortando.")
            return
        
        logger.info(f"Se extrajeron {len(posts)} posts")
        
        # Inicializar procesador de imágenes
        image_processor = EnhancedImageProcessor()
        
        # Inicializar base de datos
        db_session = init_db()
        
        # Procesar cada post
        for post_count, post in enumerate(posts, start=1):
            logger.info(f"Procesando post: {post['url']}")
            
            logger.info(f"URL de la imagen a procesar: {post['image_url']}")
            
            # Guardar la imagen localmente para inspección
            save_image_from_url(
                post['image_url'], 
                f"debug_images/post_{post_count}.png"
            )
            
            # Extraer texto de la imagen
            image_text = image_processor.extract_text_from_url(post['image_url'])
            logger.info(f"Texto extraído de la imagen: {image_text[:100]}...")
            
            # Guardar el texto en un archivo para inspección
            debug_texts_dir = "debug_texts"
            if not os.path.exists(debug_texts_dir):
                os.makedirs(debug_texts_dir)
            with open(f"{debug_texts_dir}/post_{post_count}.txt", "w", encoding="utf-8") as f:
                f.write(image_text)
            
            # Determinar si es una oferta de trabajo
            is_job, job_type, score, is_expired = is_job_post(image_text, post['description'])
            logger.info(f"¿Es oferta laboral? {is_job} (Puntuación: {score}, Tipo: {job_type or 'No identificado'}, {'Finalizada' if is_expired else 'Activa'})")
            
            # Convertir fechas de formato string a objetos datetime
            post_date = datetime.fromisoformat(post['date'].replace('Z', '+00:00'))
            scraped_at = datetime.fromisoformat(post['scraped_at'])
            
            # Crear registro en la base de datos
            job_post = JobPost(
                post_url=post['url'],
                image_url=post['image_url'],
                description=post['description'],
                post_date=post_date,
                scraped_at=scraped_at,
                is_carousel=post.get('is_carousel', False)  # Añadir campo de carrusel
            )
            db_session.add(job_post)
            db_session.commit()
            
            # Guardar imágenes del carrusel si existen
            if post.get('is_carousel', False) and post.get('carousel_images'):
                for idx, img_url in enumerate(post['carousel_images']):
                    carousel_img = CarouselImage(
                        post_id=job_post.id,
                        image_url=img_url,
                        image_order=idx
                    )
                    db_session.add(carousel_img)
                db_session.commit()
            
            # Solo procesar más a fondo si es una oferta laboral
            if is_job:
                # Extraer información estructurada
                job_info = extract_job_data(image_text, post['description'])
                
                # Guardar datos estructurados
                job_data = JobData(
                    post_id=job_post.id,
                    company_name=job_info['company_name'] or "Por determinar",
                    job_type=job_type or "Por determinar",
                    contact_info=f"{job_info['contact_name'] or ''} | {job_info['contact_position'] or ''} | {job_info['contact_email'] or ''} | {job_info['contact_phone'] or ''}".strip(),
                    position_title=job_info['position_title'] or "Por determinar",
                    requirements=str(job_info['requirements']) if job_info['requirements'] else image_text,
                    # Opcional: agregar en description si está finalizada
                    benefits="OFERTA FINALIZADA" if is_expired else str(job_info['benefits']),
                    is_active=not is_expired
                )
            else:
                # Es un post que no es oferta laboral
                job_data = JobData(
                    post_id=job_post.id,
                    company_name="N/A",
                    job_type="N/A",
                    contact_info="N/A",
                    position_title="N/A",
                    requirements=image_text
                )
            
            db_session.add(job_data)
            db_session.commit()
        
        logger.info("Datos guardados en la base de datos")
        
    except Exception as e:
        logger.error(f"Error en el proceso principal: {str(e)}")
    finally:
        # Cerrar el navegador
        scraper.close()
        logger.info("Proceso finalizado")

if __name__ == "__main__":
    main()
