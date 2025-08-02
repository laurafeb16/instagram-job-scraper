# -*- coding: utf-8 -*-
import os
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
        response = requests.get(url)
        img = Image.open(BytesIO(response.content))
        img.save(output_path)
        logger.info(f"Imagen guardada en {output_path}")
        return True
    except Exception as e:
        logger.error(f"Error al guardar imagen: {str(e)}")
        return False
