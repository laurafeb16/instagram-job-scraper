# -*- coding: utf-8 -*-
import os
import sys
import logging
from dotenv import load_dotenv

# Añadir el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.scraper.instagram_scraper import InstagramScraper
from src.image_processing.ocr import ImageProcessor
from src.database.models import init_db, JobPost, JobData

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
        image_processor = ImageProcessor()
        
        # Inicializar base de datos
        db_session = init_db()
        
        # Procesar cada post
        for post in posts:
            logger.info(f"Procesando post: {post['url']}")
            
            # Extraer texto de la imagen
            image_text = image_processor.extract_text_from_url(post['image_url'])
            logger.info(f"Texto extraído de la imagen: {image_text[:100]}...")
            
            # Crear registro en la base de datos
            job_post = JobPost(
                post_url=post['url'],
                image_url=post['image_url'],
                description=post['description'],
                post_date=post['date'],
                scraped_at=post['scraped_at']
            )
            db_session.add(job_post)
            db_session.commit()
            
            # Aquí implementaríamos el análisis de los textos para extraer información estructurada
            # Por ahora solo guardamos la data cruda
            job_data = JobData(
                post_id=job_post.id,
                company_name="Por determinar",  # Esto se extraería con NLP
                job_type="Por determinar",      # Esto se extraería con NLP
                contact_info="Por determinar",  # Esto se extraería con NLP
                position_title="Por determinar",# Esto se extraería con NLP
                requirements=image_text         # Texto crudo extraído de la imagen
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