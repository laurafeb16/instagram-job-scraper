# -*- coding: utf-8 -*-
import os
import instaloader
import time
import random
import glob
import shutil
import json
import threading
from datetime import datetime

class TimeoutError(Exception):
    """Excepción levantada cuando una operación excede el tiempo límite."""
    pass

def timeout(seconds):
    """Decorador para establecer un tiempo límite en la ejecución de una función."""
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

class InstagramScraper:
    """Clase para extraer información de perfiles de Instagram."""
    
    def __init__(self, data_dir="data/raw", temp_dir="temp_instagram_data"):
        """Inicializa el scraper.
        
        Args:
            data_dir (str): Directorio donde guardar los datos extraídos
            temp_dir (str): Directorio temporal para descargas
        """
        self.data_dir = data_dir
        self.temp_dir = temp_dir
        
        # Crear directorios necesarios
        ensure_dir(self.data_dir)
        ensure_dir(self.temp_dir)
        
        # Inicializar Instaloader con parámetros optimizados
        self.loader = instaloader.Instaloader(
            download_pictures=True, 
            download_videos=False, 
            download_video_thumbnails=False,
            compress_json=False,
            download_geotags=False,
            request_timeout=60,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            max_connection_attempts=3
        )
        
        self.authenticated = False
    
    def login(self, username, max_retries=3):
        """Carga una sesión guardada para autenticarse en Instagram.
        
        Args:
            username (str): Nombre de usuario de Instagram cuya sesión está guardada
            max_retries (int): Número máximo de intentos
            
        Returns:
            bool: True si la autenticación fue exitosa, False en caso contrario
        """
        for attempt in range(max_retries):
            try:
                print(f"Cargando sesión para el usuario: {username} (intento {attempt+1})")
                self.loader.load_session_from_file(username)
                print("Sesión cargada correctamente")
                self.authenticated = True
                # Pausa para simular comportamiento humano
                time.sleep(random.uniform(2, 5))
                return True
            except Exception as e:
                print(f"Error al cargar la sesión (intento {attempt+1}): {e}")
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + random.uniform(1, 3)  # Retroceso exponencial
                    print(f"Reintentando en {wait_time:.2f} segundos...")
                    time.sleep(wait_time)
                else:
                    print("No se pudo cargar la sesión después de varios intentos.")
                    return False
    
    def get_profile(self, username, max_retries=3):
        """Obtiene un perfil de Instagram.
        
        Args:
            username (str): Nombre de usuario del perfil a obtener
            max_retries (int): Número máximo de intentos
            
        Returns:
            Profile: Objeto de perfil de Instagram o None si no se pudo obtener
        """
        for attempt in range(max_retries):
            try:
                print(f"Intentando acceder al perfil: {username} (intento {attempt+1})")
                profile = instaloader.Profile.from_username(self.loader.context, username)
                print(f"Perfil encontrado: {profile.username} ({profile.full_name})")
                # Pausa aleatoria para simular comportamiento humano
                time.sleep(random.uniform(3, 7))
                return profile
            except instaloader.exceptions.ProfileNotExistsException:
                print(f"Error: El perfil '{username}' no existe.")
                return None
            except Exception as e:
                print(f"Error al acceder al perfil (intento {attempt+1}): {e}")
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + random.uniform(1, 3)  # Retroceso exponencial
                    print(f"Reintentando en {wait_time:.2f} segundos...")
                    time.sleep(wait_time)
                else:
                    print("No se pudo acceder al perfil después de varios intentos.")
                    return None
    
    @timeout(30)
    def get_next_post(self, iterator):
        """Obtiene el siguiente post de un iterador con timeout.
        
        Args:
            iterator: Iterador de posts de Instagram
            
        Returns:
            Post: Objeto de post de Instagram
        """
        return next(iterator)
    
    def find_job_posts(self, profile, post_limit=10, job_checker_func=None):
        """Busca posts de ofertas de trabajo en un perfil.
        
        Args:
            profile: Perfil de Instagram
            post_limit (int): Número máximo de posts a revisar
            job_checker_func (callable): Función para verificar si un post es oferta de trabajo
            
        Returns:
            list: Lista de posts de ofertas de trabajo encontrados
        """
        if not profile:
            return []
            
        if not job_checker_func:
            # Si no se proporciona función, asumir que todos los posts son válidos
            job_checker_func = lambda caption: (True, "Desconocida")
            
        job_posts = []
        posts_checked = 0
        
        print(f"Buscando posts de ofertas de trabajo (revisando hasta {post_limit} posts)...")
        
        # Obtener iterador de posts
        post_iterator = profile.get_posts()
        
        while posts_checked < post_limit:
            try:
                print(f"Revisando post {posts_checked+1}/{post_limit}...")
                post = self.get_next_post(post_iterator)
                posts_checked += 1
                
                # Verificar si es un post de oferta laboral
                is_job, company = job_checker_func(post.caption)
                
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
                # Pausa más larga en caso de error
                time.sleep(random.uniform(10, 15))
                continue
                
        print(f"\nSe encontraron {len(job_posts)} posts de ofertas laborales entre {posts_checked} posts revisados")
        return job_posts
    
    @timeout(120)
    def download_post(self, post):
        """Descarga un post de Instagram.
        
        Args:
            post: Post de Instagram a descargar
            
        Returns:
            str: Ruta a la imagen descargada o None si no se pudo descargar
        """
        self.loader.download_post(post, target=self.temp_dir)
        
        # Buscar la imagen descargada
        post_images = glob.glob(os.path.join(
            self.temp_dir, 
            f"{post.date_utc.strftime('%Y-%m-%d_%H-%M-%S')}_UTC*.jpg"
        ))
        
        if post_images:
            return post_images[0]
        return None
    
    def save_post_data(self, username, post, image_path):
        """Guarda los datos de un post en el directorio de datos.
        
        Args:
            username (str): Nombre de usuario del perfil
            post: Post de Instagram
            image_path (str): Ruta a la imagen descargada
            
        Returns:
            tuple: (imagen_guardada, metadatos_guardados) rutas a los archivos guardados
        """
        shortcode = post.shortcode
        dest_image_path = os.path.join(self.data_dir, f"{shortcode}.jpg")
        json_path = os.path.join(self.data_dir, f"{shortcode}.json")
        
        # Copiar imagen al directorio de datos
        shutil.copy2(image_path, dest_image_path)
        
        # Guardar metadatos
        metadata = {
            "username": username,
            "shortcode": shortcode,
            "caption": post.caption,
            "timestamp": post.date_utc.isoformat(),
            "image_path": dest_image_path,
            "url": f"https://www.instagram.com/p/{shortcode}/"
        }
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=4)
            
        return dest_image_path, json_path
    
    def process_job_posts(self, username, job_posts):
        """Procesa y guarda posts de ofertas de trabajo.
        
        Args:
            username (str): Nombre de usuario del perfil
            job_posts (list): Lista de posts de ofertas de trabajo
            
        Returns:
            list: Lista de tuplas (post, imagen_guardada, metadatos_guardados)
        """
        results = []
        
        print("\n=== PROCESANDO OFERTAS LABORALES ===")
        
        for i, post in enumerate(job_posts):
            try:
                print(f"\nOferta {i+1}/{len(job_posts)}: {post.shortcode}")
                print(f"Descargando post...")
                
                try:
                    image_path = self.download_post(post)
                    
                    if image_path:
                        # Guardar datos
                        dest_image, dest_json = self.save_post_data(username, post, image_path)
                        
                        print(f"✅ Imagen guardada en: {dest_image}")
                        print(f"✅ Metadatos guardados en: {dest_json}")
                        
                        results.append((post, dest_image, dest_json))
                    else:
                        print("❌ No se encontraron imágenes en el post.")
                    
                except TimeoutError:
                    print("❌ Timeout al descargar el post. La operación tomó demasiado tiempo.")
                    continue
                except Exception as e:
                    print(f"❌ Error al descargar el post: {e}")
                    continue
                
                # Pausa después de descargar
                time.sleep(random.uniform(5, 10))
            except Exception as e:
                print(f"Error al procesar post: {e}")
                continue
                
        return results
    
    def cleanup(self):
        """Limpia los archivos temporales."""
        if os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
                print(f"Directorio temporal {self.temp_dir} eliminado")
            except Exception as e:
                print(f"Error al eliminar directorio temporal: {e}")