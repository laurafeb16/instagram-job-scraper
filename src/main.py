# -*- coding: utf-8 -*-
import os
import sys
import logging
import json
import io
import argparse
from dotenv import load_dotenv
from datetime import datetime
import time
import random

# Configurar encoding UTF-8 para evitar problemas con emojis
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Añadir el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.scraper.instagram_scraper import InstagramScraper
from src.image_processing.ocr import EnhancedImageProcessor
from src.database.models import init_db, JobPost, JobData, CarouselImage, AnalysisMetrics, get_job_statistics
from src.text_analysis.job_analyzer import is_job_post, extract_job_data
from src.utils.helpers import save_image_from_url

# Configurar logging SIN EMOJIS para evitar errores
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("main.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

def parse_arguments():
    """Parsea argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(
        description='Analizador de Ofertas Laborales de Instagram',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python src/main.py                    # Procesamiento por defecto (25 posts)
  python src/main.py 20                 # Procesar 20 posts
  python src/main.py --posts 100        # Procesar 100 posts
  python src/main.py 50 --batch 10      # 50 posts en lotes de 10
  python src/main.py --max               # Procesamiento masivo (2500 posts)
  python src/main.py --headless         # Ejecutar en modo headless
  python src/main.py --clean-only       # Solo limpiar entorno y BD
        """)
    
    # Argumento principal: número de posts
    parser.add_argument(
        'posts', 
        nargs='?', 
        type=int, 
        default=25,
        help='Número de posts a procesar (por defecto: 25)'
    )
    
    # Argumentos opcionales
    parser.add_argument(
        '--posts', '-p',
        type=int,
        dest='posts_alt',
        help='Número de posts a procesar (alternativo)'
    )
    
    parser.add_argument(
        '--batch', '-b',
        type=int,
        default=10,
        help='Tamaño de lote para scraping (por defecto: 10)'
    )
    
    parser.add_argument(
        '--max', '--masivo',
        action='store_true',
        help='Modo masivo: procesar hasta 2500 posts'
    )
    
    parser.add_argument(
        '--headless',
        action='store_true',
        help='Ejecutar navegador en modo headless (sin interfaz)'
    )
    
    parser.add_argument(
        '--no-clean',
        action='store_true',
        help='No limpiar entorno ni base de datos antes de iniciar'
    )
    
    parser.add_argument(
        '--clean-only',
        action='store_true',
        help='Solo limpiar entorno y base de datos, luego salir'
    )
    
    parser.add_argument(
        '--account', '-a',
        type=str,
        help='Cuenta de Instagram objetivo (sobrescribe .env)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Activar logging de debug detallado'
    )
    
    args = parser.parse_args()
    
    # Lógica de prioridad para el número de posts
    if args.posts_alt:
        args.posts = args.posts_alt
    
    if args.max:
        args.posts = 2500
        args.batch = 25
    
    # Validaciones
    if args.posts <= 0:
        parser.error("El número de posts debe ser mayor que 0")
    
    if args.posts > 3000:
        logger.warning(f"ADVERTENCIA: Número muy alto de posts ({args.posts}). Recomendado: máximo 2500")
    
    if args.batch <= 0 or args.batch > 100:
        parser.error("El tamaño de lote debe estar entre 1 y 100")
    
    return args

def analyze_and_save_post(post, post_count, image_processor, db_session):
    """
    Analiza un post individual y guarda la información en la base de datos
    
    Args:
        post: Diccionario con información del post
        post_count: Número del post (para archivos de debug)
        image_processor: Instancia del procesador de imágenes
        db_session: Sesión de base de datos
    
    Returns:
        Dict con resultados del análisis
    """
    
    logger.info(f"Procesando post {post_count}: {post['url']}")
    
    try:
        # Verificar si el post ya existe en la base de datos
        existing_post = db_session.query(JobPost).filter_by(post_url=post['url']).first()
        if existing_post:
            logger.warning(f"Post {post_count} ya existe en BD: {post['url']}")
            return {
                "post_id": existing_post.id,
                "is_job": existing_post.is_job_offer,
                "job_type": "DUPLICADO",
                "score": existing_post.classification_score,
                "company": "N/A",
                "contact_email": None
            }
        
        # Crear directorios de debug si no existen
        os.makedirs("debug_images", exist_ok=True)
        os.makedirs("debug_texts", exist_ok=True)
        os.makedirs("debug_analysis", exist_ok=True)
        
        # Guardar imagen para inspección
        local_image_path = f"debug_images/post_{post_count}.png"
        save_image_from_url(post['image_url'], local_image_path)
        
        # Extraer texto de la imagen principal
        image_text = image_processor.extract_text_from_url(post['image_url'])
        logger.info(f"Texto extraído ({len(image_text)} caracteres): {image_text[:200]}...")
        
        # Guardar texto extraído para inspección
        with open(f"debug_texts/post_{post_count}.txt", "w", encoding="utf-8") as f:
            f.write(f"POST URL: {post['url']}\n")
            f.write(f"IMAGE URL: {post['image_url']}\n")
            f.write(f"DESCRIPTION: {post['description']}\n")
            f.write(f"EXTRACTED TEXT:\n{image_text}\n")
        
        # Análisis de clasificación
        is_job, job_type, score, is_expired = is_job_post(image_text, post['description'])
        
        logger.info(f"Análisis de clasificación:")
        logger.info(f"  - Es oferta laboral: {is_job}")
        logger.info(f"  - Tipo: {job_type or 'No identificado'}")
        logger.info(f"  - Puntuación: {score}")
        logger.info(f"  - Estado: {'Finalizada' if is_expired else 'Activa'}")
        
        # Convertir fechas
        post_date = datetime.fromisoformat(post['date'].replace('Z', '+00:00'))
        scraped_at = datetime.fromisoformat(post['scraped_at'])
        
        # Crear registro principal del post
        job_post = JobPost(
            post_url=post['url'],
            image_url=post['image_url'],
            description=post['description'],
            post_date=post_date,
            scraped_at=scraped_at,
            local_image_path=local_image_path,
            is_carousel=post.get('is_carousel', False),
            classification_score=score,
            is_job_offer=is_job
        )
        
        db_session.add(job_post)
        db_session.commit()
        
        # Procesar imágenes del carrusel si existen
        carousel_texts = []
        if post.get('is_carousel', False) and post.get('carousel_images'):
            for idx, img_url in enumerate(post['carousel_images']):
                # Guardar imagen del carrusel
                carousel_local_path = f"debug_images/post_{post_count}_carousel_{idx}.png"
                save_image_from_url(img_url, carousel_local_path)
                
                # Extraer texto de cada imagen del carrusel
                carousel_text = image_processor.extract_text_from_url(img_url)
                carousel_texts.append(carousel_text)
                
                # Crear registro de imagen del carrusel
                carousel_img = CarouselImage(
                    post_id=job_post.id,
                    image_url=img_url,
                    local_image_path=carousel_local_path,
                    image_order=idx,
                    extracted_text=carousel_text
                )
                db_session.add(carousel_img)
            
            db_session.commit()
            logger.info(f"Procesadas {len(post['carousel_images'])} imágenes del carrusel")
        
        # Extraer información estructurada si es una oferta laboral
        job_info = {}
        if is_job:
            # Combinar texto de imagen principal y carrusel para análisis completo
            combined_image_text = image_text
            if carousel_texts:
                combined_image_text += "\n\n" + "\n\n".join(carousel_texts)
            
            job_info = extract_job_data(combined_image_text, post['description'])
            
            logger.info("Información extraída:")
            logger.info(f"  - Empresa: {job_info.get('company_name', 'No identificada')}")
            logger.info(f"  - Industria: {job_info.get('company_industry', 'No identificada')}")
            logger.info(f"  - Contacto: {job_info.get('contact_name', 'No identificado')}")
            logger.info(f"  - Email: {job_info.get('contact_email', 'No identificado')}")
            logger.info(f"  - Puesto: {job_info.get('position_title', 'No identificado')}")
            
            # Crear registro de datos estructurados
            job_data = JobData(
                post_id=job_post.id,
                company_name=job_info.get('company_name') or "Por determinar",
                company_industry=job_info.get('company_industry'),
                job_type=job_type or "Por determinar",
                position_title=job_info.get('position_title'),
                work_modality=job_info.get('work_modality'),
                duration=job_info.get('duration'),
                contact_name=job_info.get('contact_name'),
                contact_position=job_info.get('contact_position'),
                contact_email=job_info.get('contact_email'),
                contact_phone=job_info.get('contact_phone'),
                requirements=job_info.get('requirements', []),
                knowledge_required=job_info.get('knowledge_required', []),
                functions=job_info.get('functions', []),
                benefits=job_info.get('benefits', []),
                experience_required=job_info.get('experience_required'),
                education_required=job_info.get('education_required'),
                is_active=job_info.get('is_active', True) and not is_expired
            )
        else:
            # Post que no es oferta laboral
            job_data = JobData(
                post_id=job_post.id,
                company_name="N/A",
                job_type="No es oferta laboral",
                requirements=[image_text] if image_text.strip() else [],
                is_active=False
            )
        
        db_session.add(job_data)
        db_session.commit()
        
        # Crear métricas de análisis
        metrics = AnalysisMetrics(
            post_id=job_post.id,
            text_length=len(image_text),
            classification_confidence=min(100, max(0, score + 50)),
            has_contact_info=bool(job_info.get('contact_email') or job_info.get('contact_phone')),
            has_requirements=bool(job_info.get('requirements')),
            has_benefits=bool(job_info.get('benefits'))
        )
        
        db_session.add(metrics)
        db_session.commit()
        
        # Guardar análisis detallado para inspección
        analysis_data = {
            "post_info": {
                "url": post['url'],
                "date": post['date'],
                "description": post['description']
            },
            "classification": {
                "is_job": is_job,
                "job_type": job_type,
                "score": score,
                "is_expired": is_expired
            },
            "extracted_info": job_info,
            "text_extracted": {
                "main_image": image_text,
                "carousel_images": carousel_texts
            }
        }
        
        with open(f"debug_analysis/post_{post_count}_analysis.json", "w", encoding="utf-8") as f:
            json.dump(analysis_data, f, ensure_ascii=False, indent=2)
        
        return {
            "post_id": job_post.id,
            "is_job": is_job,
            "job_type": job_type,
            "score": score,
            "company": job_info.get('company_name'),
            "contact_email": job_info.get('contact_email')
        }
    except Exception as e:
        db_session.rollback()
        logger.error(f"ERROR procesando post {post_count}: {str(e)}")
        raise

def clean_environment():
    """Limpia el entorno antes de ejecutar el script"""
    logger.info("Limpiando entorno para nueva ejecución...")
    
    # Directorios a limpiar
    dirs_to_clean = [
        "debug_images",
        "debug_images_processed", 
        "debug_texts",
        "debug_analysis"
    ]
    
    # Limpiar cada directorio
    for dir_path in dirs_to_clean:
        if os.path.exists(dir_path):
            logger.info(f"Limpiando directorio: {dir_path}")
            for file in os.listdir(dir_path):
                file_path = os.path.join(dir_path, file)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                except Exception as e:
                    logger.error(f"Error al borrar {file_path}: {e}")
        else:
            # Crear el directorio si no existe
            logger.info(f"Creando directorio: {dir_path}")
            os.makedirs(dir_path, exist_ok=True)
    
    logger.info("Limpieza completada")

def clean_database():
    """Limpia la base de datos para evitar conflictos de UNIQUE constraint"""
    logger.info("Limpiando base de datos...")
    db_session = init_db()
    try:
        # Eliminar todos los registros existentes
        db_session.query(AnalysisMetrics).delete()
        db_session.query(CarouselImage).delete()
        db_session.query(JobData).delete()
        db_session.query(JobPost).delete()
        db_session.commit()
        logger.info("Base de datos limpiada correctamente")
    except Exception as e:
        db_session.rollback()
        logger.error(f"Error al limpiar la base de datos: {e}")
    finally:
        db_session.close()

def remove_duplicates_from_list(posts_list):
    """Elimina posts duplicados basándose en la URL"""
    seen_urls = set()
    unique_posts = []
    duplicates_count = 0
    
    for post in posts_list:
        if post['url'] not in seen_urls:
            seen_urls.add(post['url'])
            unique_posts.append(post)
        else:
            duplicates_count += 1
    
    if duplicates_count > 0:
        logger.warning(f"Se eliminaron {duplicates_count} posts duplicados de la lista")
    
    return unique_posts

def main():
    """Función principal optimizada con argumentos de línea de comandos"""
    
    # Parsear argumentos
    args = parse_arguments()
    
    # Configurar logging según argumentos
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Modo debug activado")
    
    # Mostrar configuración
    logger.info("=== CONFIGURACIÓN ===")
    logger.info(f"Posts a procesar: {args.posts}")
    logger.info(f"Tamaño de lote: {args.batch}")
    logger.info(f"Modo headless: {'Sí' if args.headless else 'No'}")
    logger.info(f"Limpiar entorno: {'No' if args.no_clean else 'Sí'}")
    
    # Solo limpiar si se especifica
    if args.clean_only:
        logger.info("Modo solo limpieza activado")
        clean_environment()
        clean_database()
        logger.info("Limpieza completada. Saliendo...")
        return
    
    # Limpiar entorno anterior (a menos que se especifique lo contrario)
    if not args.no_clean:
        clean_environment()
        clean_database()
    
    # Obtener credenciales desde argumentos o variables de entorno
    username = os.getenv("INSTAGRAM_USERNAME")
    password = os.getenv("INSTAGRAM_PASSWORD")
    target_account = args.account or os.getenv("TARGET_ACCOUNT")
    
    if not all([username, password, target_account]):
        logger.error("ERROR: Faltan credenciales. Configura las variables de entorno:")
        logger.error("- INSTAGRAM_USERNAME")
        logger.error("- INSTAGRAM_PASSWORD") 
        logger.error("- TARGET_ACCOUNT (o usa --account)")
        return
    
    logger.info("=== INICIANDO ANÁLISIS DE OFERTAS LABORALES ===")
    logger.info(f"Cuenta objetivo: {target_account}")
    
    # Inicializar componentes
    scraper = InstagramScraper(username, password, target_account, headless=args.headless)
    image_processor = EnhancedImageProcessor()
    db_session = init_db()
    
    try:
        # Proceso de scraping
        logger.info("Iniciando proceso de login...")
        if not scraper.login():
            logger.error("ERROR: Fallo en el login. Verificar credenciales.")
            return
        
        logger.info("Navegando a la cuenta objetivo...")
        if not scraper.navigate_to_target_account():
            logger.error("ERROR: No se pudo acceder a la cuenta objetivo.")
            return
        
        # CONFIGURACIÓN DINÁMICA BASADA EN ARGUMENTOS
        MAX_POSTS = args.posts
        BATCH_SIZE = min(args.batch, MAX_POSTS)
        
        # Ajustar configuración según el volumen
        if MAX_POSTS <= 10:
            RETRY_ATTEMPTS = 2
            PAUSE_RANGE = (1, 3)
            PROCESSING_BATCH_SIZE = MAX_POSTS
        elif MAX_POSTS <= 50:
            RETRY_ATTEMPTS = 3
            PAUSE_RANGE = (2, 5)
            PROCESSING_BATCH_SIZE = 5
        elif MAX_POSTS <= 200:
            RETRY_ATTEMPTS = 3
            PAUSE_RANGE = (3, 6)
            PROCESSING_BATCH_SIZE = 10
        else:  # Volumen alto
            RETRY_ATTEMPTS = 3
            PAUSE_RANGE = (3, 8)
            PROCESSING_BATCH_SIZE = 10
        
        logger.info(f"CONFIGURACIÓN AUTOMÁTICA:")
        logger.info(f"   Total posts: {MAX_POSTS}")
        logger.info(f"   Lote scraping: {BATCH_SIZE}")
        logger.info(f"   Lote procesamiento: {PROCESSING_BATCH_SIZE}")
        logger.info(f"   Pausas: {PAUSE_RANGE[0]}-{PAUSE_RANGE[1]}s")
        
        all_posts = []
        current_batch = 0
        consecutive_failures = 0
        
        # EXTRACCIÓN CON MANEJO DE DUPLICADOS
        while len(all_posts) < MAX_POSTS and consecutive_failures < RETRY_ATTEMPTS:
            remaining_posts = MAX_POSTS - len(all_posts)
            batch_size = min(BATCH_SIZE, remaining_posts)
            
            logger.info(f"Lote {current_batch + 1}: extrayendo {batch_size} posts...")
            
            try:
                batch_posts = scraper.scrape_posts(limit=batch_size)
                
                if not batch_posts:
                    consecutive_failures += 1
                    logger.warning(f"Lote vacío ({consecutive_failures}/{RETRY_ATTEMPTS})")
                    if consecutive_failures >= RETRY_ATTEMPTS:
                        logger.info("No hay más posts disponibles, finalizando")
                        break
                else:
                    # Filtrar duplicados antes de agregar
                    new_urls = {post['url'] for post in batch_posts}
                    existing_urls = {post['url'] for post in all_posts}
                    
                    unique_batch_posts = [post for post in batch_posts if post['url'] not in existing_urls]
                    
                    all_posts.extend(unique_batch_posts)
                    consecutive_failures = 0
                    
                    logger.info(f"Lote {current_batch + 1}: {len(unique_batch_posts)} posts únicos extraídos")
                    if len(unique_batch_posts) < len(batch_posts):
                        logger.info(f"   Se filtraron {len(batch_posts) - len(unique_batch_posts)} duplicados")
                
                current_batch += 1
                
                # Pausa inteligente
                if remaining_posts > batch_size and len(all_posts) < MAX_POSTS:
                    pause_time = random.uniform(*PAUSE_RANGE)
                    logger.info(f"Pausa de {pause_time:.1f}s...")
                    time.sleep(pause_time)
                
            except Exception as e:
                consecutive_failures += 1
                logger.error(f"ERROR en lote {current_batch + 1}: {str(e)}")
                if consecutive_failures >= RETRY_ATTEMPTS:
                    logger.error("Demasiados errores consecutivos, abortando")
                    break
                time.sleep(5)
        
        # Filtrado final de duplicados por seguridad
        all_posts = remove_duplicates_from_list(all_posts)
        
        logger.info(f"EXTRACCIÓN COMPLETADA: {len(all_posts)} posts únicos obtenidos")
        
        if not all_posts:
            logger.warning("No se obtuvieron posts para procesar")
            return
        
        # PROCESAMIENTO DINÁMICO
        results = []
        job_offers_found = 0
        duplicates_found = 0
        
        # Progreso más frecuente para volúmenes pequeños
        progress_interval = min(10, max(1, len(all_posts) // 10))
        
        for i in range(0, len(all_posts), PROCESSING_BATCH_SIZE):
            batch = all_posts[i:i + PROCESSING_BATCH_SIZE]
            
            batch_num = i // PROCESSING_BATCH_SIZE + 1
            total_batches = (len(all_posts) + PROCESSING_BATCH_SIZE - 1) // PROCESSING_BATCH_SIZE
            
            logger.info(f"Procesando lote {batch_num}/{total_batches}")
            
            for post_idx, post in enumerate(batch):
                post_count = i + post_idx + 1
                try:
                    result = analyze_and_save_post(post, post_count, image_processor, db_session)
                    results.append(result)
                    
                    if result['job_type'] == 'DUPLICADO':
                        duplicates_found += 1
                    elif result['is_job']:
                        job_offers_found += 1
                        logger.info(f"OFERTA #{job_offers_found}: {result.get('company', 'N/A')}")
                    
                    # Progreso dinámico
                    if post_count % progress_interval == 0 or post_count == len(all_posts):
                        progress = (post_count / len(all_posts)) * 100
                        logger.info(f"Progreso: {post_count}/{len(all_posts)} ({progress:.1f}%) - Ofertas: {job_offers_found}")
                        
                except Exception as e:
                    logger.error(f"ERROR procesando post {post_count}: {str(e)}")
                    continue
            
            # Pausa entre lotes de procesamiento
            if len(all_posts) > 50 and i + PROCESSING_BATCH_SIZE < len(all_posts):
                time.sleep(random.uniform(0.5, 2))
        
        # RESUMEN FINAL
        logger.info("\n=== RESUMEN DE RESULTADOS ===")
        logger.info(f"Posts procesados: {len(results)}")
        logger.info(f"Posts duplicados: {duplicates_found}")
        logger.info(f"Ofertas laborales encontradas: {job_offers_found}")
        
        if job_offers_found > 0:
            success_rate = (job_offers_found / (len(results) - duplicates_found)) * 100
            logger.info(f"Tasa de éxito: {success_rate:.1f}%")
        
        # Estadísticas detalladas
        stats = get_job_statistics(db_session)
        logger.info(f"Total posts en BD: {stats['total_posts']}")
        logger.info(f"Ofertas activas: {stats['active_offers']}")
        
        if stats.get('by_job_type'):
            logger.info("Por tipo de trabajo:")
            for job_type, count in stats['by_job_type'].items():
                if job_type and job_type != "No es oferta laboral":
                    logger.info(f"  - {job_type}: {count}")
        
        if stats.get('by_industry'):
            logger.info("Por industria:")
            for industry, count in stats['by_industry'].items():
                if industry:
                    logger.info(f"  - {industry}: {count}")
        
        # Mostrar ofertas encontradas
        if job_offers_found > 0:
            logger.info(f"\nOfertas encontradas en esta ejecución:")
            for i, result in enumerate([r for r in results if r['is_job']], 1):
                logger.info(f"{i:2d}. {result['company'] or 'Empresa no identificada'}")
                logger.info(f"     Tipo: {result['job_type']}")
                if result['contact_email']:
                    logger.info(f"     Contacto: {result['contact_email']}")
                logger.info("")
        
        logger.info("=== PROCESAMIENTO COMPLETADO EXITOSAMENTE ===")
        
    except KeyboardInterrupt:
        logger.info("\nProceso interrumpido por el usuario")
        logger.info(f"Posts procesados hasta el momento: {len(results) if 'results' in locals() else 0}")
    except Exception as e:
        logger.error(f"ERROR crítico: {str(e)}")
        raise
    finally:
        # Cerrar recursos
        scraper.close()
        db_session.close()
        logger.info("Recursos liberados correctamente")

if __name__ == "__main__":
    main()