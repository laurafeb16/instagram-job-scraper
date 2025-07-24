# -*- coding: utf-8 -*-
import argparse
import sys
from backend.scraper import InstagramScraper
from backend.job_extractor import is_job_post
from backend.ocr_processor import OCRProcessor

def main():
    # Configurar argumentos de línea de comandos
    parser = argparse.ArgumentParser(description="Instagram Job Scraper")
    parser.add_argument('--username', default='ucm_fdi', 
                        help='Nombre de usuario de Instagram de la facultad')
    parser.add_argument('--session', 
                        help='Nombre de usuario de Instagram para la sesión guardada')
    parser.add_argument('--max-retries', type=int, default=3,
                        help='Número máximo de reintentos para operaciones fallidas')
    parser.add_argument('--keep-files', action='store_true',
                        help='Mantener archivos descargados (no eliminar directorio temporal)')
    parser.add_argument('--post-limit', type=int, default=10,
                        help='Número máximo de posts a verificar (por defecto: 10)')
    parser.add_argument('--tesseract-path', 
                        default=r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                        help='Ruta al ejecutable de Tesseract OCR')
    args = parser.parse_args()
    
    # Inicializar scraper
    scraper = InstagramScraper()
    
    # Inicializar procesador OCR
    ocr = OCRProcessor(tesseract_cmd=args.tesseract_path)
    
    try:
        # Autenticar en Instagram si se proporcionó sesión
        if args.session:
            if not scraper.login(args.session, max_retries=args.max_retries):
                print("No se pudo autenticar. Continuando sin autenticación...")
        
        # Obtener perfil
        profile = scraper.get_profile(args.username, max_retries=args.max_retries)
        if not profile:
            print(f"No se pudo obtener el perfil {args.username}. Abortando.")
            return 1
        
        # Buscar posts de ofertas de trabajo
        job_posts = scraper.find_job_posts(
            profile, 
            post_limit=args.post_limit,
            job_checker_func=is_job_post
        )
        
        if not job_posts:
            print("No se encontraron ofertas de trabajo. Abortando.")
            return 1
        
        # Procesar y guardar posts
        results = scraper.process_job_posts(args.username, job_posts)
        
        # Mostrar resultado de OCR en el primer post
        if results:
            post, image_path, json_path = results[0]
            print(f"\nAplicando OCR a: {image_path}")
            print("=== OCR TEXT FROM FIRST IMAGE ===")
            
            try:
                text = ocr.extract_text(image_path)
                print(text)
            except Exception as e:
                print(f"Error al realizar OCR: {e}")
        
        print(f"\nSe descargaron y procesaron {len(results)} ofertas laborales")
        print(f"Archivos guardados en el directorio 'data/raw/'")
        return 0
    
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")
        return 1
    
    finally:
        # Limpiar archivos temporales si no se especificó mantenerlos
        if not args.keep_files:
            scraper.cleanup()

if __name__ == "__main__":
    sys.exit(main())