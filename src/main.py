# -*- coding: utf-8 -*-
import os
import sys
import logging
import argparse
from datetime import datetime, timedelta
from dateutil import parser as date_parser

# Añadir el directorio raíz al path CORREGIDO
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Imports corregidos para funcionar desde cualquier directorio
try:
    from scraper.instagram_scraper import InstagramScraper
    from text_analysis.job_analyzer import extract_job_data, is_job_post
    from database.models import init_db, JobPost, JobData, AnalysisMetrics, migrate_existing_data
    from utils.helpers import clean_environment, save_image_from_url
    from image_processing.ocr import extract_text_from_image
except ImportError:
    # Fallback para imports absolutos
    try:
        from src.scraper.instagram_scraper import InstagramScraper
        from src.text_analysis.job_analyzer import extract_job_data, is_job_post
        from src.database.models import init_db, JobPost, JobData, AnalysisMetrics, migrate_existing_data
        from src.utils.helpers import clean_environment, save_image_from_url
        from src.image_processing.ocr import extract_text_from_image
    except ImportError as e:
        print(f"❌ Error de importación: {e}")
        print("📁 Verifica que el directorio actual tenga la estructura correcta")
        sys.exit(1)

# Cargar variables de entorno
from dotenv import load_dotenv
load_dotenv()

# Configuración de logging mejorada
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/instagram_scraper.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

def safe_parse_datetime(date_value):
    """Convierte cualquier formato de fecha a datetime de Python de manera segura"""
    try:
        if date_value is None:
            return datetime.now()
        
        if isinstance(date_value, datetime):
            return date_value
        
        if isinstance(date_value, str):
            # Intentar parsear diferentes formatos
            try:
                return date_parser.parse(date_value)
            except:
                # Si falla, devolver fecha actual
                return datetime.now()
        
        # Si es otro tipo, intentar convertir a string y parsear
        try:
            return date_parser.parse(str(date_value))
        except:
            return datetime.now()
            
    except Exception:
        return datetime.now()

class InstagramScraperAdapter:
    """Adaptador para el InstagramScraper que maneja los nuevos métodos esperados"""
    
    def __init__(self, target_account='utpfisc', headless=False):
        # Obtener credenciales del .env
        username = os.getenv('INSTAGRAM_USERNAME')
        password = os.getenv('INSTAGRAM_PASSWORD')
        
        if not username or not password:
            logger.warning("⚠️ Credenciales de Instagram no encontradas en .env")
            logger.warning("⚠️ Asegúrate de configurar INSTAGRAM_USERNAME y INSTAGRAM_PASSWORD")
            # Usar valores por defecto para testing o lanzar error
            username = "test_user"
            password = "test_password"
        
        self.scraper = InstagramScraper(
            username=username,
            password=password, 
            target_account=target_account,
            headless=headless
        )
        
    def setup_driver(self):
        """Configurar el driver (ya se hace en __init__)"""
        return not self.scraper.browser_crashed
    
    def login(self):
        """Login con el método adaptado"""
        return self.scraper.login()
    
    def navigate_to_account(self, account):
        """Navegar a la cuenta objetivo"""
        return self.scraper.navigate_to_target_account()
    
    def extract_posts(self, max_posts, pause_range=(1, 3)):
        """Extraer posts con el método mejorado"""
        try:
            posts = self.scraper.scrape_posts(limit=max_posts)
            return posts or []
        except Exception as e:
            logger.error(f"Error extrayendo posts: {str(e)}")
            return []
    
    def close(self):
        """Cerrar el scraper"""
        return self.scraper.close()

class JobScrapingPipeline:
    """Pipeline mejorado para extracción de ofertas laborales con nuevas funcionalidades"""
    
    def __init__(self, target_account='utpfisc', headless=False, clean_env=True):
        self.target_account = target_account
        self.headless = headless
        self.clean_env = clean_env
        
        # Inicializar base de datos
        self.db_session = init_db()
        
        # Migrar datos existentes si es necesario
        migrate_existing_data(self.db_session)
        
        # Inicializar scraper usando el adaptador
        self.scraper = InstagramScraperAdapter(target_account=target_account, headless=headless)
        
        # Contadores para estadísticas
        self.stats = {
            'posts_processed': 0,
            'job_offers_found': 0,
            'duplicates_skipped': 0,
            'errors': 0,
            'technologies_extracted': 0,
            'soft_skills_extracted': 0,
            'contacts_extracted': 0,
            'functions_extracted': 0,
            'benefits_extracted': 0
        }

    def setup_environment(self):
        """Configura el entorno de ejecución"""
        
        if self.clean_env:
            logger.info("Limpiando entorno para nueva ejecución...")
            clean_environment()
            
            # Limpiar base de datos
            logger.info("Limpiando base de datos...")
            try:
                self.db_session.query(AnalysisMetrics).delete()
                self.db_session.query(JobData).delete()
                self.db_session.query(JobPost).delete()
                self.db_session.commit()
                logger.info("Base de datos limpiada correctamente")
            except Exception as e:
                logger.error(f"Error limpiando base de datos: {str(e)}")
                self.db_session.rollback()

    def process_post_enhanced(self, post_data: dict) -> dict:
        """Procesa un post individual con las nuevas funcionalidades mejoradas - CORREGIDO"""
        
        # Inicializar variables por defecto para evitar errores
        job_data_dict = {}
        extracted_text = ""
        
        try:
            # Extraer texto de imagen si está disponible
            if post_data.get('image_path'):
                try:
                    extracted_text = extract_text_from_image(post_data['image_path'])
                    logger.debug(f"Texto extraído: {len(extracted_text)} caracteres")
                except Exception as e:
                    logger.warning(f"Error en OCR: {str(e)}")
            
            # Clasificar si es oferta laboral
            is_job, job_type, score, is_expired = is_job_post(
                extracted_text, 
                post_data.get('description', '')
            )
            
            logger.info(f"Análisis de clasificación:")
            logger.info(f"  - Es oferta laboral: {is_job}")
            logger.info(f"  - Tipo: {job_type}")
            logger.info(f"  - Puntuación: {score}")
            logger.info(f"  - Estado: {'Expirada' if is_expired else 'Activa'}")
            
            # CORRECCIÓN: Convertir fechas de manera segura
            post_date = safe_parse_datetime(post_data.get('date'))
            
            # Crear JobPost
            job_post = JobPost(
                post_url=post_data['url'],
                image_url=post_data.get('image_url', ''),
                description=post_data.get('description', ''),
                post_date=post_date,  # Fecha convertida de manera segura
                local_image_path=post_data.get('image_path'),
                is_job_offer=is_job,
                classification_score=score
            )
            
            self.db_session.add(job_post)
            self.db_session.flush()  # Para obtener el ID
            
            # Si es oferta laboral, extraer información detallada
            if is_job:
                try:
                    job_data_dict = extract_job_data(
                        extracted_text,
                        post_data.get('description', '')
                    )
                    
                    # Validar que job_data_dict sea un diccionario válido
                    if not isinstance(job_data_dict, dict):
                        job_data_dict = {}
                        logger.warning("extract_job_data no retornó un diccionario válido")
                    
                    # === LOGGING MEJORADO DE INFORMACIÓN EXTRAÍDA ===
                    logger.info("Información extraída:")
                    logger.info(f"  - Empresa: {job_data_dict.get('company_name', 'No identificada')}")
                    logger.info(f"  - Industria: {job_data_dict.get('company_industry', 'No especificada')}")
                    logger.info(f"  - Contacto: {job_data_dict.get('contact_name', 'No disponible')}")
                    logger.info(f"  - Email: {job_data_dict.get('contact_email', 'No disponible')}")
                    logger.info(f"  - Puesto: {job_data_dict.get('position_title', 'No especificado')}")
                    
                    # Logging de nuevos campos con validación segura
                    if job_data_dict.get('schedule'):
                        logger.info(f"  - Horario: {job_data_dict['schedule']}")
                    
                    programming_langs = job_data_dict.get('programming_languages', []) or []
                    if programming_langs and isinstance(programming_langs, list):
                        logger.info(f"  - Lenguajes: {', '.join(programming_langs[:3])}")
                    
                    soft_skills = job_data_dict.get('soft_skills', []) or []
                    if soft_skills and isinstance(soft_skills, list):
                        logger.info(f"  - Habilidades blandas: {', '.join(soft_skills[:3])}")
                    
                    # Crear JobData con nuevos campos - CORREGIDO
                    # Evitar conflicto de is_active
                    job_data_dict_copy = job_data_dict.copy()
                    job_data_dict_copy.pop('is_active', None)  # Remover si existe
                    
                    job_data = JobData(
                        post_id=job_post.id,
                        job_type=job_type,
                        is_active=not is_expired,
                        **job_data_dict_copy  # Sin conflicto de is_active
                    )
                    
                    self.db_session.add(job_data)
                    
                    # === CREAR MÉTRICAS MEJORADAS - CONTEO CORREGIDO ===
                    # Calcular tecnologías encontradas de forma COMPLETA
                    total_technologies = (
                        len(job_data_dict.get('programming_languages') or []) +
                        len(job_data_dict.get('databases') or []) +
                        len(job_data_dict.get('cloud_platforms') or []) +
                        len(job_data_dict.get('frameworks_tools') or []) +
                        len(job_data_dict.get('office_tools') or []) +         # ← AGREGADO
                        len(job_data_dict.get('specialized_software') or [])   # ← AGREGADO
                    )
                    
                    total_soft_skills = len(job_data_dict.get('soft_skills') or [])
                    total_functions = len(job_data_dict.get('functions') or [])
                    total_benefits = len(job_data_dict.get('benefits') or [])
                    
                    # Log detallado de conteo
                    logger.debug(f"🔢 Conteo de tecnologías:")
                    logger.debug(f"  - Lenguajes: {len(job_data_dict.get('programming_languages') or [])}")
                    logger.debug(f"  - Bases de datos: {len(job_data_dict.get('databases') or [])}")
                    logger.debug(f"  - Plataformas cloud: {len(job_data_dict.get('cloud_platforms') or [])}")
                    logger.debug(f"  - Frameworks/tools: {len(job_data_dict.get('frameworks_tools') or [])}")
                    logger.debug(f"  - Office tools: {len(job_data_dict.get('office_tools') or [])}")
                    logger.debug(f"  - Software especializado: {len(job_data_dict.get('specialized_software') or [])}")
                    logger.debug(f"  - TOTAL: {total_technologies}")
                    logger.debug(f"  - Habilidades blandas: {total_soft_skills}")
                    
                    metrics = AnalysisMetrics(
                        post_id=job_post.id,
                        ocr_confidence=85,  # Valor por defecto
                        text_length=len(extracted_text),
                        classification_confidence=min(100, max(0, score)),
                        has_contact_info=bool(job_data_dict.get('contact_name')),
                        has_requirements=bool(job_data_dict.get('requirements')),
                        has_benefits=bool(job_data_dict.get('benefits')),
                        has_technologies=bool(total_technologies > 0),
                        has_soft_skills=bool(total_soft_skills > 0),
                        has_schedule=bool(job_data_dict.get('schedule')),
                        total_technologies_found=total_technologies,
                        total_soft_skills_found=total_soft_skills,
                        extraction_completeness_score=self.calculate_completeness_score(job_data_dict)
                    )
                    
                    self.db_session.add(metrics)
                    
                    # Actualizar estadísticas CORREGIDAS
                    self.stats['job_offers_found'] += 1
                    self.stats['technologies_extracted'] += total_technologies
                    self.stats['soft_skills_extracted'] += total_soft_skills
                    self.stats['functions_extracted'] += total_functions
                    self.stats['benefits_extracted'] += total_benefits
                    if job_data_dict.get('contact_name'):
                        self.stats['contacts_extracted'] += 1
                    
                    logger.info(f"OFERTA #{self.stats['job_offers_found']}: {job_data_dict.get('company_name', 'Empresa no identificada')}")
                    logger.info(f"📊 Tecnologías en esta oferta: {total_technologies}")
                    logger.info(f"👥 Habilidades blandas en esta oferta: {total_soft_skills}")
                    
                except Exception as extraction_error:
                    logger.error(f"Error extrayendo datos de la oferta: {str(extraction_error)}")
                    # Continúa con el procesamiento pero sin datos extraídos
                    job_data_dict = {}
            
            self.db_session.commit()
            self.stats['posts_processed'] += 1
            
            return {
                'success': True,
                'is_job_offer': is_job,
                'job_type': job_type,
                'score': score,
                'company': job_data_dict.get('company_name') if job_data_dict else None,
                'extracted_text': extracted_text
            }
            
        except Exception as e:
            logger.error(f"Error procesando post: {str(e)}")
            self.db_session.rollback()
            self.stats['errors'] += 1
            return {
                'success': False, 
                'error': str(e), 
                'extracted_text': extracted_text,
                'is_job_offer': False
            }

    def calculate_completeness_score(self, job_data: dict) -> int:
        """Calcula un score de completitud basado en campos extraídos"""
        
        if not isinstance(job_data, dict):
            return 0
        
        score = 0
        max_score = 100
        
        # Campos básicos (40 puntos)
        if job_data.get('company_name'): score += 10
        if job_data.get('contact_email'): score += 10
        if job_data.get('contact_name'): score += 10
        if job_data.get('position_title'): score += 10
        
        # Campos detallados (30 puntos)
        if job_data.get('requirements'): score += 10
        if job_data.get('benefits'): score += 10
        if job_data.get('functions'): score += 10
        
        # Campos nuevos (30 puntos)
        if job_data.get('programming_languages'): score += 5
        if job_data.get('databases'): score += 5
        if job_data.get('soft_skills'): score += 5
        if job_data.get('schedule'): score += 5
        if job_data.get('work_modality'): score += 5
        if job_data.get('company_industry'): score += 5
        
        return min(max_score, score)

    def run_extraction(self, num_posts: int = 10, batch_size: int = None) -> dict:
        """Ejecuta el proceso de extracción con configuración automática mejorada"""
        
        logger.info("=== CONFIGURACIÓN ===")
        logger.info(f"Posts a procesar: {num_posts}")
        
        # Configuración automática inteligente
        if batch_size is None:
            if num_posts <= 5:
                batch_size = num_posts
                processing_batch = num_posts
                pause_range = (1, 2)
            elif num_posts <= 20:
                batch_size = 10
                processing_batch = 10
                pause_range = (1, 3)
            elif num_posts <= 50:
                batch_size = 15
                processing_batch = 15
                pause_range = (2, 4)
            else:
                batch_size = 20
                processing_batch = 20
                pause_range = (3, 5)
        else:
            processing_batch = batch_size
            pause_range = (1, 3)
        
        logger.info(f"Tamaño de lote: {batch_size}")
        logger.info(f"Lote scraping: {batch_size}")
        logger.info(f"Lote procesamiento: {processing_batch}")
        logger.info(f"Pausas: {pause_range[0]}-{pause_range[1]}s")
        
        # Limpiar entorno
        self.setup_environment()
        
        logger.info("=== INICIANDO ANÁLISIS DE OFERTAS LABORALES ===")
        logger.info(f"Cuenta objetivo: {self.target_account}")
        
        try:
            # Configurar scraper
            if not self.scraper.setup_driver():
                raise Exception("Error configurando el navegador")
            
            # Login
            logger.info("Iniciando proceso de login...")
            if not self.scraper.login():
                raise Exception("Error en el proceso de login")
            
            # Navegar a cuenta objetivo
            logger.info("Navegando a la cuenta objetivo...")
            if not self.scraper.navigate_to_account(self.target_account):
                raise Exception(f"Error navegando a la cuenta {self.target_account}")
            
            # === EXTRACCIÓN EN LOTES ===
            total_extracted = 0
            batch_number = 1
            
            while total_extracted < num_posts:
                remaining = num_posts - total_extracted
                current_batch_size = min(batch_size, remaining)
                
                logger.info(f"CONFIGURACIÓN AUTOMÁTICA:")
                logger.info(f"   Total posts: {num_posts}")
                logger.info(f"   Lote scraping: {current_batch_size}")
                logger.info(f"   Lote procesamiento: {processing_batch}")
                logger.info(f"   Pausas: {pause_range[0]}-{pause_range[1]}s")
                
                logger.info(f"Lote {batch_number}: extrayendo {current_batch_size} posts...")
                
                # Extraer posts del lote
                posts = self.scraper.extract_posts(
                    max_posts=current_batch_size,
                    pause_range=pause_range
                )
                
                if not posts:
                    logger.warning(f"No se obtuvieron posts en el lote {batch_number}")
                    break
                
                logger.info(f"Lote {batch_number}: {len(posts)} posts únicos extraídos")
                total_extracted += len(posts)
                
                # Procesar posts en lotes
                self.process_posts_in_batches(posts, processing_batch)
                
                batch_number += 1
                
                if total_extracted >= num_posts:
                    break
            
            logger.info(f"EXTRACCIÓN COMPLETADA: {total_extracted} posts únicos obtenidos")
            
            # === GENERAR RESUMEN FINAL ===
            return self.generate_final_summary()
            
        except Exception as e:
            logger.error(f"Error en extracción: {str(e)}")
            return {'success': False, 'error': str(e)}
        finally:
            try:
                self.scraper.close()
                logger.info("Recursos liberados correctamente")
            except:
                pass

    def process_posts_in_batches(self, posts: list, batch_size: int):
        """Procesa posts en lotes para mejor rendimiento"""
        
        total_batches = (len(posts) + batch_size - 1) // batch_size
        
        for i in range(0, len(posts), batch_size):
            batch = posts[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            
            logger.info(f"Procesando lote {batch_num}/{total_batches}")
            
            for j, post_data in enumerate(batch, 1):
                post_num = i + j
                logger.info(f"Procesando post {post_num}: {post_data['url']}")
                
                # Descargar imagen
                if post_data.get('image_url'):
                    image_path = save_image_from_url(
                        post_data['image_url'], 
                        f"debug_images/post_{post_num}.png"
                    )
                    post_data['image_path'] = image_path
                
                # Procesar post
                result = self.process_post_enhanced(post_data)
                
                # Mostrar progreso con manejo seguro de datos
                if result['success']:
                    if result.get('is_job_offer'):
                        company = result.get('company', 'No identificada')
                        extracted_text_len = len(result.get('extracted_text', ''))
                        logger.info(f"✅ Oferta encontrada: {company} ({extracted_text_len} caracteres)")
                        
                    progress = (post_num / len(posts)) * 100
                    logger.info(f"Progreso: {post_num}/{len(posts)} ({progress:.1f}%) - Ofertas: {self.stats['job_offers_found']}")
                else:
                    logger.warning(f"❌ Error procesando post: {result.get('error', 'Error desconocido')}")

    def generate_final_summary(self) -> dict:
        """Genera un resumen final mejorado con nuevas métricas"""
        
        logger.info("\n=== RESUMEN DE RESULTADOS ===")
        logger.info(f"Posts procesados: {self.stats['posts_processed']}")
        logger.info(f"Posts duplicados: {self.stats['duplicates_skipped']}")
        logger.info(f"Ofertas laborales encontradas: {self.stats['job_offers_found']}")
        logger.info(f"Errores encontrados: {self.stats['errors']}")
        
        # Calcular tasa de éxito con validación
        success_rate = 0
        if self.stats['posts_processed'] > 0:
            success_rate = (self.stats['job_offers_found'] / self.stats['posts_processed']) * 100
            logger.info(f"Tasa de éxito: {success_rate:.1f}%")
        else:
            logger.info("Tasa de éxito: 0% (no se procesaron posts)")
        
        # === ESTADÍSTICAS MEJORADAS ===
        
        try:
            # Obtener estadísticas de la base de datos
            total_posts = self.db_session.query(JobPost).count()
            active_offers = self.db_session.query(JobData).filter(JobData.is_active == True).count()
            
            logger.info(f"Total posts en BD: {total_posts}")
            logger.info(f"Ofertas activas: {active_offers}")
            
            # Por tipo de trabajo
            from sqlalchemy import func
            job_types = self.db_session.query(
                JobData.job_type, func.count(JobData.job_type)
            ).filter(
                JobData.job_type.isnot(None)
            ).group_by(JobData.job_type).all()
            
            if job_types:
                logger.info("Por tipo de trabajo:")
                for job_type, count in job_types:
                    logger.info(f"  - {job_type}: {count}")
            
            # Por industria
            industries = self.db_session.query(
                JobData.company_industry, func.count(JobData.company_industry)
            ).filter(
                JobData.company_industry.isnot(None)
            ).group_by(JobData.company_industry).all()
            
            if industries:
                logger.info("Por industria:")
                for industry, count in industries:
                    logger.info(f"  - {industry}: {count}")
            
            # === NUEVAS MÉTRICAS ===
            logger.info(f"\nMétricas de extracción mejoradas:")
            logger.info(f"  - Tecnologías extraídas: {self.stats['technologies_extracted']}")
            logger.info(f"  - Habilidades blandas extraídas: {self.stats['soft_skills_extracted']}")
            logger.info(f"  - Contactos extraídos: {self.stats['contacts_extracted']}")
            
            # Obtener ofertas de esta ejecución
            recent_offers = self.db_session.query(JobData).join(JobPost).filter(
                JobPost.scraped_at >= datetime.now() - timedelta(minutes=30),
                JobData.is_active == True
            ).all()
            
            logger.info(f"\nOfertas encontradas en esta ejecución:")
            for i, offer in enumerate(recent_offers, 1):
                company = offer.company_name or "Empresa no identificada"
                logger.info(f" {i}. {company}")
                logger.info(f"     Tipo: {offer.job_type}")
                
                # Manejo seguro de listas que pueden ser None
                if offer.programming_languages and isinstance(offer.programming_languages, list):
                    logger.info(f"     Tecnologías: {', '.join(offer.programming_languages[:3])}")
                    
                if offer.soft_skills and isinstance(offer.soft_skills, list):
                    logger.info(f"     Habilidades: {', '.join(offer.soft_skills[:3])}")
                logger.info("")
                
        except Exception as e:
            logger.error(f"Error generando estadísticas finales: {str(e)}")
        
        logger.info("=== PROCESAMIENTO COMPLETADO EXITOSAMENTE ===")
        
        return {
            'success': True,
            'posts_processed': self.stats['posts_processed'],
            'job_offers_found': self.stats['job_offers_found'],
            'success_rate': success_rate,
            'technologies_extracted': self.stats['technologies_extracted'],
            'soft_skills_extracted': self.stats['soft_skills_extracted'],
            'contacts_extracted': self.stats['contacts_extracted'],
            'functions_extracted': self.stats['functions_extracted'],
            'benefits_extracted': self.stats['benefits_extracted'],
            'errors': self.stats['errors']
        }

def main():
    """Función principal mejorada con nuevas opciones"""
    
    parser = argparse.ArgumentParser(description='Extractor de ofertas laborales de Instagram')
    parser.add_argument('num_posts', type=int, nargs='?', default=10, 
                       help='Número de posts a procesar (por defecto: 10)')
    parser.add_argument('--account', '-a', default='utpfisc', 
                       help='Cuenta de Instagram objetivo (por defecto: utpfisc)')
    parser.add_argument('--headless', action='store_true', 
                       help='Ejecutar navegador en modo headless')
    parser.add_argument('--no-clean', action='store_true', 
                       help='No limpiar entorno antes de ejecutar')
    parser.add_argument('--batch-size', '-b', type=int, 
                       help='Tamaño de lote personalizado')
    parser.add_argument('--debug', action='store_true', 
                       help='Activar modo debug con logs detallados')
    
    args = parser.parse_args()
    
    # Configurar logging para debug
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.info("Modo debug activado")
    
    # Verificar que el .env existe
    if not os.path.exists('.env'):
        logger.warning("⚠️ Archivo .env no encontrado")
        logger.info("📝 Crea un archivo .env con:")
        logger.info("   INSTAGRAM_USERNAME=tu_usuario")
        logger.info("   INSTAGRAM_PASSWORD=tu_contraseña")
    
    # Crear pipeline
    pipeline = JobScrapingPipeline(
        target_account=args.account,
        headless=args.headless,
        clean_env=not args.no_clean
    )
    
    try:
        # Ejecutar extracción
        result = pipeline.run_extraction(
            num_posts=args.num_posts,
            batch_size=args.batch_size
        )
        
        if result['success']:
            logger.info(f"✅ Proceso completado exitosamente")
            logger.info(f"📊 Ofertas encontradas: {result['job_offers_found']}")
            logger.info(f"🔧 Tecnologías extraídas: {result['technologies_extracted']}")
            logger.info(f"👥 Habilidades blandas: {result['soft_skills_extracted']}")
            logger.info(f"📞 Contactos extraídos: {result['contacts_extracted']}")
            logger.info(f"📋 Funciones extraídas: {result['functions_extracted']}")
            logger.info(f"🎁 Beneficios extraídos: {result['benefits_extracted']}")
            if result.get('errors', 0) > 0:
                logger.warning(f"⚠️  Errores encontrados: {result['errors']}")
        else:
            logger.error(f"❌ Error en el proceso: {result.get('error', 'Error desconocido')}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("🛑 Proceso interrumpido por el usuario")
        sys.exit(0)
    except Exception as e:
        logger.error(f"💥 Error crítico: {str(e)}")
        sys.exit(1)
    finally:
        # Cerrar sesión de base de datos
        try:
            pipeline.db_session.close()
        except:
            pass

if __name__ == "__main__":
    main()