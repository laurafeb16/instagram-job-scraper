import os
import sys
import instaloader
import pytesseract
from PIL import Image
import shutil
import glob
import argparse

def main():
    # Configurar argumentos de línea de comandos
    parser = argparse.ArgumentParser(description="Instagram Faculty Page Analyzer")
    parser.add_argument('--username', default='ucm_fdi', 
                        help='Nombre de usuario de Instagram de la facultad')
    args = parser.parse_args()
    
    # Configurar Instaloader
    L = instaloader.Instaloader()
    
    # Crear directorio temporal para descargas
    temp_dir = "temp_instagram_data"
    os.makedirs(temp_dir, exist_ok=True)
    
    try:
        # Verificar si Tesseract está instalado
        try:
            pytesseract.get_tesseract_version()
        except pytesseract.TesseractNotFoundError:
            print("Error: Tesseract OCR no está instalado o no está en el PATH.")
            return 1
            
        # Obtener perfil
        try:
            profile = instaloader.Profile.from_username(L.context, args.username)
        except instaloader.exceptions.ProfileNotExistsException:
            print(f"Error: El perfil '{args.username}' no existe.")
            return 1
        
        # Obtener los 3 posts más recientes
        posts = list(profile.get_posts())[:3]
        if not posts:
            print(f"No se encontraron posts para el perfil '{args.username}'.")
            return 1
        
        # Imprimir leyendas y descargar imágenes
        print("=== CAPTIONS ===")
        for i, post in enumerate(posts):
            print(f"Caption {i+1}: {post.caption}")
            # Descargar post si es el primero (para OCR)
            if i == 0:
                L.download_post(post, target=temp_dir)
        
        # Encontrar el primer archivo de imagen en el directorio temporal
        image_files = glob.glob(os.path.join(temp_dir, "*.jpg"))
        if not image_files:
            print("No se encontraron imágenes en el post descargado.")
            return 1
        
        # Aplicar OCR a la primera imagen
        image_path = image_files[0]
        print("\n=== OCR TEXT FROM FIRST IMAGE ===")
        
        try:
            text = pytesseract.image_to_string(Image.open(image_path), lang='spa')
            print(text)
        except pytesseract.TesseractError:
            print("Error: Falló el OCR de Tesseract. Asegúrate de que los datos del idioma español estén instalados.")
            return 1
        
        return 0
    
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")
        return 1
    
    finally:
        # Limpiar
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

if __name__ == "__main__":
    sys.exit(main())