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
import random # Import the random module for uniform delays

def main():
    # Configurar Tesseract
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    
    # Configurar argumentos de línea de comandos
    parser = argparse.ArgumentParser(description="Instagram Faculty Page Analyzer")
    parser.add_argument('--username', default='ucm_fdi', 
                        help='Nombre de usuario de Instagram de la facultad')
    parser.add_argument('--session', 
                        help='Nombre de usuario de Instagram para la sesión guardada')
    args = parser.parse_args()
    
    # Configurar Instaloader
    L = instaloader.Instaloader(download_pictures=True, 
                                download_videos=False, 
                                download_video_thumbnails=False,
                                compress_json=False,
                                download_geotags=False,
                                request_timeout=60)
    
    # Cargar sesión guardada si se proporciona
    if args.session:
        try:
            print(f"Cargando sesión para el usuario: {args.session}")
            L.load_session_from_file(args.session)
            print("Sesión cargada correctamente")
        except Exception as e:
            print(f"Error al cargar la sesión: {e}")
            print("Recomendación: Guarda una sesión primero con 'instaloader --login=TU_USUARIO'")
            return 1
    
    # Crear directorio temporal para descargas
    temp_dir = "temp_instagram_data"
    os.makedirs(temp_dir, exist_ok=True)
    
    try:
        # Verificar si Tesseract está instalado
        try:
            print(f"Versión de Tesseract: {pytesseract.get_tesseract_version()}")
        except pytesseract.TesseractNotFoundError:
            print("Error: Tesseract OCR no está instalado o no está en el PATH.")
            return 1
            
        print(f"Intentando acceder al perfil: {args.username}")
        # Obtener perfil
        try:
            profile = instaloader.Profile.from_username(L.context, args.username)
            print(f"Perfil encontrado: {profile.username} ({profile.full_name})")
            # Delay after getting the profile: 3-7 seconds
            time.sleep(random.uniform(3, 7)) 
        except instaloader.exceptions.ProfileNotExistsException:
            print(f"Error: El perfil '{args.username}' no existe.")
            return 1
        except Exception as e:
            print(f"Error al acceder al perfil: {e}")
            traceback.print_exc()
            return 1
            
        # Obtener los 3 posts más recientes
        print("Obteniendo posts recientes...")
        try:
            posts = list(profile.get_posts())[:3]
            print(f"Se encontraron {len(posts)} posts recientes")
            if not posts:
                print(f"No se encontraron posts para el perfil '{args.username}'.")
                return 1
            # Delay after fetching the list of posts: 3-7 seconds
            time.sleep(random.uniform(3, 7)) 
        except Exception as e:
            print(f"Error al obtener posts: {e}")
            traceback.print_exc()
            return 1
            
        # Imprimir leyendas y descargar imágenes
        print("=== CAPTIONS ===")
        for i, post in enumerate(posts):
            try:
                print(f"Caption {i+1}: {post.caption}")
                # Descargar post si es el primero (para OCR)
                if i == 0:
                    print(f"Descargando post {i+1}...")
                    # Longer delay after downloading a post: 8-15 seconds
                    L.download_post(post, target=temp_dir)
                    time.sleep(random.uniform(8, 15)) 
            except Exception as e:
                print(f"Error al procesar post {i+1}: {e}")
                traceback.print_exc()
                continue
            
        # Encontrar el primer archivo de imagen en el directorio temporal
        image_files = glob.glob(os.path.join(temp_dir, "*.jpg"))
        print(f"Archivos de imagen encontrados: {len(image_files)}")
        if not image_files:
            print("No se encontraron imágenes en el post descargado.")
            return 1
            
        # Aplicar OCR a la primera imagen
        image_path = image_files[0]
        print(f"\nAplicando OCR a: {image_path}")
        print("=== OCR TEXT FROM FIRST IMAGE ===")
        
        try:
            # Verificar que el archivo existe y es accesible
            if not os.path.exists(image_path):
                print(f"Error: El archivo {image_path} no existe")
                return 1
                
            img = Image.open(image_path)
            print(f"Imagen cargada: {img.format}, {img.size}px")
            text = pytesseract.image_to_string(img, lang='spa')
            print(text)
            # Small delay after OCR processing: 1-3 seconds
            time.sleep(random.uniform(1, 3)) 
        except pytesseract.TesseractError as e:
            print(f"Error de Tesseract: {e}")
            print("Asegúrate de que los datos del idioma español estén instalados.")
            return 1
        except Exception as e:
            print(f"Error al procesar la imagen: {e}")
            traceback.print_exc()
            return 1
            
        return 0
        
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")
        traceback.print_exc()
        return 1
        
    finally:
        # Limpiar
        if os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                print(f"Directorio temporal {temp_dir} eliminado")
            except Exception as e:
                print(f"Error al eliminar directorio temporal: {e}")

if __name__ == "__main__":
    sys.exit(main())