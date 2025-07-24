# -*- coding: utf-8 -*-
import os
import sys
import instaloader
import pytesseract
from PIL import Image
import shutil
import glob
import argparse
import traceback
import time
import random
import threading
import json
import re
from datetime import datetime

class TimeoutError(Exception):
    pass

def timeout(seconds):
    def decorator(function):
        def wrapper(*args, **kwargs):
            result = [TimeoutError("Operación demorada demasiado tiempo")]
            def target():
                try:
                    result[0] = function(*args, **kwargs)
                except Exception as e:
                    result[0] = e
            thread = threading.Thread(target=target)
            thread.daemon = True
            thread.start()
            thread.join(seconds)
            if isinstance(result[0], Exception):
                raise result[0]
            return result[0]
        return wrapper
    return decorator

def ensure_dir(directory):
    """Asegura que exista un directorio, creándolo si es necesario."""
    if not os.path.exists(directory):
        os.makedirs(directory)

def save_post_metadata(username, post, image_path):
    """Guarda los metadatos del post en un archivo JSON."""
    shortcode = post.shortcode
    json_path = os.path.join("data/raw", f"{shortcode}.json")
    
    metadata = {
        "username": username,
        "shortcode": shortcode,
        "caption": post.caption,
        "timestamp": post.date_utc.isoformat(),
        "image_path": image_path,
        "url": f"https://www.instagram.com/p/{shortcode}/"
    }
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=4)
    
    return json_path

def is_job_post(caption):
    """Determina si un post es una oferta de trabajo o práctica profesional."""
    if not caption:
        return False
    
    # Patrones de búsqueda para ofertas laborales
    job_patterns = [
        r"[Vv]acante(?:\s+[^.]*?)?ofrecida\s+por\s+['\"]?([^'\".,]+)['\"]?",
        r"[Pp]ráctica\s+laboral(?:\s+[^.]*?)?ofrecida\s+por\s+['\"]?([^'\".,]+)['\"]?",
        r"[Pp]ráctica\s+profesional(?:\s+[^.]*?)?ofrecida\s+por\s+['\"]?([^'\".,]+)['\"]?",
        r"[Oo]ferta\s+de\s+(?:trabajo|empleo|vacante)(?:\s+[^.]*?)?(?:en|por|para)\s+['\"]?([^'\".,]+)['\"]?",
        r"[Ss]e\s+busca(?:\s+[^.]*?)para(?:\s+[^.]*?)en\s+['\"]?([^'\".,]+)['\"]?"
    ]
    
    for pattern in job_patterns:
        match = re.search(pattern, caption)
        if match:
            company = match.group(1).strip() if match.groups() else "Desconocida"
            return True, company
    
    return False, None

def main():
    # Configurar Tesseract
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    
    # Configurar argumentos de línea de comandos
    parser = argparse.ArgumentParser(description="Instagram Faculty Page Analyzer")
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
    args = parser.parse_args()
    
    # Crear estructura de directorios
    ensure_dir("data/raw")
    
    # Configurar Instaloader con parámetros más "humanos"
    L = instaloader.Instaloader(
        download_pictures=True, 
        download_videos=False, 
        download_video_thumbnails=False,
        compress_json=False,
        download_geotags=False,
        request_timeout=60,
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        max_connection_attempts=3
    )
    
    # Cargar sesión guardada si se proporciona (con reintentos)
    if args.session:
        for attempt in range(args.max_retries):
            try:
                print(f"Cargando sesión para el usuario: {args.session} (intento {attempt+1})")
                L.load_session_from_file(args.session)
                print("Sesión cargada correctamente")
                # Pausa para simular comportamiento humano
                time.sleep(random.uniform(2, 5))
                break
            except Exception as e:
                print(f"Error al cargar la sesión (intento {attempt+1}): {e}")
                if attempt < args.max_retries - 1:
                    wait_time = (2 ** attempt) + random.uniform(1, 3)  # Retroceso exponencial
                    print(f"Reintentando en {wait_time:.2f} segundos...")
                    time.sleep(wait_time)
                else:
                    print("No se pudo cargar la sesión después de varios intentos.")
                    print("Recomendación: Guarda una sesión primero con 'instaloader --login=TU_USUARIO'")
                    return 1
    
    # Crear directorio temporal para descargas
    temp_dir = "temp_instagram_data"
    ensure_dir(temp_dir)
    
    try:
        # Verificar si Tesseract está instalado
        try:
            print(f"Versión de Tesseract: {pytesseract.get_tesseract_version()}")
        except pytesseract.TesseractNotFoundError:
            print("Error: Tesseract OCR no está instalado o no está en el PATH.")
            return 1
        
        # Obtener perfil (con reintentos)
        profile = None
        for attempt in range(args.max_retries):
            try:
                print(f"Intentando acceder al perfil: {args.username} (intento {attempt+1})")
                profile = instaloader.Profile.from_username(L.context, args.username)
                print(f"Perfil encontrado: {profile.username} ({profile.full_name})")
                # Pausa aleatoria para simular comportamiento humano
                time.sleep(random.uniform(3, 7))
                break
            except instaloader.exceptions.ProfileNotExistsException:
                print(f"Error: El perfil '{args.username}' no existe.")
                return 1
            except Exception as e:
                print(f"Error al acceder al perfil (intento {attempt+1}): {e}")
                if attempt < args.max_retries - 1:
                    wait_time = (2 ** attempt) + random.uniform(1, 3)  # Retroceso exponencial
                    print(f"Reintentando en {wait_time:.2f} segundos...")
                    time.sleep(wait_time)
                else:
                    print("No se pudo acceder al perfil después de varios intentos.")
                    traceback.print_exc()
                    return 1
        
        if not profile:
            print("No se pudo obtener el perfil. Abortando.")
            return 1
        
        # Obtener posts individualmente y buscar ofertas de trabajo
        print(f"Buscando posts de ofertas de trabajo (revisando hasta {args.post_limit} posts)...")
        job_posts = []
        posts_checked = 0
        
        # Función para obtener un post con timeout
        @timeout(30)
        def get_next_post(iterator):
            return next(iterator)
        
        # Obtener un iterador de posts
        post_iterator = profile.get_posts()
        
        while posts_checked < args.post_limit:
            try:
                print(f"Revisando post {posts_checked+1}/{args.post_limit}...")
                post = get_next_post(post_iterator)
                posts_checked += 1
                
                # Verificar si es un post de oferta laboral
                is_job, company = is_job_post(post.caption)
                
                if is_job:
                    print(f"✅ Encontrada oferta de trabajo en '{company}' (shortcode: {post.shortcode})")
                    job_posts.append(post)
                    print(f"   Fecha: {post.date}")
                    print(f"   Caption: {post.caption[:100]}...")
                else:
                    print(f"❌ No es oferta laboral (shortcode: {post.shortcode})")
                
                # Pausa entre obtenciones de posts para parecer más humano
                time.sleep(random.uniform(3, 7))
            except TimeoutError:
                print(f"Timeout al obtener el post. La operación tomó demasiado tiempo.")
                break
            except StopIteration:
                print("No hay más posts disponibles.")
                break
            except Exception as e:
                print(f"Error al obtener post: {e}")
                traceback.print_exc()
                # Pausa más larga en caso de error
                time.sleep(random.uniform(10, 15))
                continue
        
        print(f"\nSe encontraron {len(job_posts)} posts de ofertas laborales entre {posts_checked} posts revisados")
        
        if not job_posts:
            print(f"No se encontraron ofertas laborales en el perfil '{args.username}'.")
            print("Prueba con otro perfil o aumenta el límite de posts a revisar con --post-limit")
            return 1
        
        # Descargar y guardar las ofertas laborales encontradas
        print("\n=== OFERTAS LABORALES ENCONTRADAS ===")
        downloaded_images = []
        
        for i, post in enumerate(job_posts):
            try:
                print(f"\nOferta {i+1}/{len(job_posts)}: {post.shortcode}")
                print(f"Caption: {post.caption}")
                print(f"Descargando post...")
                
                # Función para descargar un post con timeout
                @timeout(120)
                def download_post(loader, post, target):
                    loader.download_post(post, target=target)
                
                try:
                    download_post(L, post, temp_dir)
                    
                    # Buscar la imagen descargada
                    post_images = glob.glob(os.path.join(temp_dir, f"{post.date_utc.strftime('%Y-%m-%d_%H-%M-%S')}_UTC*.jpg"))
                    
                    if post_images:
                        # Guardar la imagen con el shortcode como nombre
                        dest_path = os.path.join("data/raw", f"{post.shortcode}.jpg")
                        shutil.copy2(post_images[0], dest_path)
                        
                        # Guardar metadatos en JSON
                        json_path = save_post_metadata(args.username, post, dest_path)
                        
                        print(f"✅ Imagen guardada en: {dest_path}")
                        print(f"✅ Metadatos guardados en: {json_path}")
                        
                        downloaded_images.append((post, dest_path))
                    else:
                        print("❌ No se encontraron imágenes en el post.")
                    
                except TimeoutError:
                    print("❌ Timeout al descargar el post. La operación tomó demasiado tiempo.")
                    continue
                except Exception as e:
                    print(f"❌ Error al descargar el post: {e}")
                    traceback.print_exc()
                    continue
                
                # Pausa después de descargar
                time.sleep(random.uniform(5, 10))
            except Exception as e:
                print(f"Error al procesar post: {e}")
                traceback.print_exc()
                continue
        
        # Aplicar OCR a la primera imagen descargada (si existe)
        if downloaded_images:
            post, image_path = downloaded_images[0]
            print(f"\nAplicando OCR a: {image_path}")
            print("=== OCR TEXT FROM FIRST IMAGE ===")
            
            try:
                img = Image.open(image_path)
                print(f"Imagen cargada: {img.format}, {img.size}px")
                text = pytesseract.image_to_string(img, lang='spa')
                print(text)
                
                print(f"\nSe descargaron y procesaron {len(downloaded_images)} ofertas laborales")
                print(f"Archivos guardados en el directorio 'data/raw/'")
                return 0
            except pytesseract.TesseractError as e:
                print(f"Error de Tesseract: {e}")
                print("Asegúrate de que los datos del idioma español estén instalados.")
                return 1
            except Exception as e:
                print(f"Error al procesar la imagen: {e}")
                traceback.print_exc()
                return 1
        else:
            print("No se pudieron descargar imágenes. No se puede realizar OCR.")
            return 1
    
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")
        traceback.print_exc()
        return 1
    
    finally:
        # Limpiar directorio temporal
        if not args.keep_files and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                print(f"Directorio temporal {temp_dir} eliminado")
            except Exception as e:
                print(f"Error al eliminar directorio temporal: {e}")

if __name__ == "__main__":
    sys.exit(main())