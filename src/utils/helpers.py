# -*- coding: utf-8 -*-
import os
import shutil
from PIL import Image
import requests
from io import BytesIO
import logging

logger = logging.getLogger(__name__)

def save_image_from_url(url, output_path):
    """Guarda una imagen desde una URL a un archivo local"""
    try:
        # Crear directorio si no existe
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Descargar y guardar imagen
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        img = Image.open(BytesIO(response.content))
        img.save(output_path)
        logger.debug(f"Imagen guardada en {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Error al guardar imagen desde {url}: {str(e)}")
        return None

def clean_environment():
    """Limpia el entorno de ejecución eliminando archivos temporales"""
    try:
        logger.info("🧹 Limpiando entorno de ejecución...")
        
        # Directorios a limpiar
        dirs_to_clean = [
            'debug_images',
            'temp_images', 
            'data/images',
            'logs'
        ]
        
        # Archivos temporales a eliminar
        temp_files = [
            'debug_*.png',
            'temp_*.jpg',
            'temp_*.png'
        ]
        
        cleaned_count = 0
        
        # Limpiar directorios
        for dir_path in dirs_to_clean:
            if os.path.exists(dir_path):
                try:
                    # Solo limpiar contenido, no eliminar el directorio
                    for filename in os.listdir(dir_path):
                        file_path = os.path.join(dir_path, filename)
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                            cleaned_count += 1
                        elif os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                            cleaned_count += 1
                    logger.debug(f"✅ Limpiado directorio: {dir_path}")
                except Exception as e:
                    logger.warning(f"⚠️ No se pudo limpiar {dir_path}: {str(e)}")
        
        # Limpiar archivos temporales en el directorio raíz
        for pattern in temp_files:
            if '*' in pattern:
                # Manejar patrones con wildcards
                import glob
                for file_path in glob.glob(pattern):
                    try:
                        os.remove(file_path)
                        cleaned_count += 1
                        logger.debug(f"✅ Eliminado: {file_path}")
                    except Exception as e:
                        logger.warning(f"⚠️ No se pudo eliminar {file_path}: {str(e)}")
            else:
                # Archivos específicos
                if os.path.exists(pattern):
                    try:
                        os.remove(pattern)
                        cleaned_count += 1
                        logger.debug(f"✅ Eliminado: {pattern}")
                    except Exception as e:
                        logger.warning(f"⚠️ No se pudo eliminar {pattern}: {str(e)}")
        
        # Recrear directorios necesarios
        essential_dirs = ['debug_images', 'logs', 'data']
        for dir_path in essential_dirs:
            os.makedirs(dir_path, exist_ok=True)
        
        logger.info(f"✅ Entorno limpiado exitosamente ({cleaned_count} elementos eliminados)")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error limpiando entorno: {str(e)}")
        return False

def ensure_directories():
    """Asegura que existan los directorios necesarios"""
    try:
        required_dirs = [
            'data',
            'data/images', 
            'debug_images',
            'logs',
            'temp'
        ]
        
        for dir_path in required_dirs:
            os.makedirs(dir_path, exist_ok=True)
            
        logger.debug("✅ Directorios verificados/creados")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creando directorios: {str(e)}")
        return False

def get_file_size_mb(file_path):
    """Obtiene el tamaño de un archivo en MB"""
    try:
        if os.path.exists(file_path):
            size_bytes = os.path.getsize(file_path)
            size_mb = size_bytes / (1024 * 1024)
            return round(size_mb, 2)
        return 0
    except Exception:
        return 0

def clean_filename(filename):
    """Limpia un nombre de archivo removiendo caracteres no válidos"""
    try:
        import re
        # Remover caracteres no válidos para nombres de archivo
        cleaned = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Limitar longitud
        if len(cleaned) > 200:
            cleaned = cleaned[:200]
        return cleaned
    except Exception:
        return "unnamed_file"

def validate_image_url(url):
    """Valida si una URL apunta a una imagen válida"""
    try:
        if not url or not isinstance(url, str):
            return False
            
        # Verificar que sea una URL válida
        if not url.startswith(('http://', 'https://')):
            return False
            
        # Verificar que contenga patrones de imagen
        image_patterns = [
            'fbcdn.net',
            '.jpg', '.jpeg', '.png', '.gif', '.webp',
            'instagram.com'
        ]
        
        return any(pattern in url.lower() for pattern in image_patterns)
        
    except Exception:
        return False

def format_file_size(size_bytes):
    """Formatea el tamaño de archivo en una cadena legible"""
    try:
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024**2:
            return f"{size_bytes/1024:.1f} KB"
        elif size_bytes < 1024**3:
            return f"{size_bytes/(1024**2):.1f} MB"
        else:
            return f"{size_bytes/(1024**3):.1f} GB"
    except Exception:
        return "0 B"

def safe_create_directory(path):
    """Crea un directorio de manera segura"""
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Error creando directorio {path}: {str(e)}")
        return False

def get_project_root():
    """Obtiene la ruta raíz del proyecto"""
    try:
        # Buscar hacia arriba hasta encontrar requirements.txt o .git
        current = os.path.abspath(os.path.dirname(__file__))
        
        while current != os.path.dirname(current):  # Hasta llegar a la raíz del sistema
            if (os.path.exists(os.path.join(current, 'requirements.txt')) or 
                os.path.exists(os.path.join(current, '.git')) or
                os.path.exists(os.path.join(current, 'src'))):
                return current
            current = os.path.dirname(current)
        
        # Si no se encuentra, usar directorio actual
        return os.getcwd()
        
    except Exception:
        return os.getcwd()

def log_system_info():
    """Registra información del sistema para debugging"""
    try:
        import platform
        import psutil
        
        logger.info("=== INFORMACIÓN DEL SISTEMA ===")
        logger.info(f"SO: {platform.system()} {platform.release()}")
        logger.info(f"Python: {platform.python_version()}")
        logger.info(f"Directorio de trabajo: {os.getcwd()}")
        logger.info(f"Raíz del proyecto: {get_project_root()}")
        
        # Información de memoria si psutil está disponible
        try:
            memory = psutil.virtual_memory()
            logger.info(f"Memoria RAM: {format_file_size(memory.total)} (disponible: {format_file_size(memory.available)})")
        except:
            pass
            
        logger.info("=" * 35)
        
    except Exception as e:
        logger.debug(f"No se pudo obtener información del sistema: {str(e)}")

# Función de inicialización
def initialize_environment():
    """Inicializa el entorno completo"""
    try:
        logger.info("🚀 Inicializando entorno...")
        
        # Asegurar directorios
        ensure_directories()
        
        # Log de información del sistema
        log_system_info()
        
        logger.info("✅ Entorno inicializado correctamente")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error inicializando entorno: {str(e)}")
        return False

# Exportar funciones principales
__all__ = [
    'save_image_from_url',
    'clean_environment', 
    'ensure_directories',
    'get_file_size_mb',
    'clean_filename',
    'validate_image_url',
    'format_file_size',
    'safe_create_directory',
    'get_project_root',
    'log_system_info',
    'initialize_environment'
]