# -*- coding: utf-8 -*-
import logging
import os
import pytesseract
from PIL import Image
import requests
from io import BytesIO
import numpy as np

class ImageProcessor:
    def __init__(self, tesseract_path=None):
        # Configurar logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler("image_processor.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Configurar Tesseract
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        else:
            # Ruta predeterminada en Windows
            default_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
            if os.path.exists(default_path):
                pytesseract.pytesseract.tesseract_cmd = default_path
        
        # Verificar que Tesseract esté instalado
        try:
            pytesseract.get_tesseract_version()
            self.logger.info(f"Tesseract versión: {pytesseract.get_tesseract_version()}")
        except Exception as e:
            self.logger.error(f"Error al verificar Tesseract: {str(e)}")
            self.logger.error("Asegúrate de que Tesseract OCR esté instalado correctamente")
    
    def load_image_from_url(self, url):
        """Carga una imagen desde una URL"""
        try:
            response = requests.get(url)
            image = Image.open(BytesIO(response.content))
            return image
        except Exception as e:
            self.logger.error(f"Error al cargar imagen desde URL: {str(e)}")
            return None
    
    def load_image_from_path(self, path):
        """Carga una imagen desde una ruta local"""
        try:
            return Image.open(path)
        except Exception as e:
            self.logger.error(f"Error al cargar imagen desde ruta: {str(e)}")
            return None
    
    def preprocess_image(self, image):
        """Preprocesa la imagen para mejorar el OCR"""
        try:
            # Convertir a escala de grises
            gray_image = image.convert('L')
            
            # Aplicar un poco de contraste
            # Esto es mucho más simple que con OpenCV pero debería ser suficiente
            return gray_image
        except Exception as e:
            self.logger.error(f"Error al preprocesar imagen: {str(e)}")
            return image
    
    def extract_text(self, image, lang='spa'):
        """Extrae texto de una imagen usando Tesseract OCR"""
        try:
            # Preprocesar la imagen
            processed_image = self.preprocess_image(image)
            
            # Extraer texto
            text = pytesseract.image_to_string(processed_image, lang=lang)
            
            return text
        except Exception as e:
            self.logger.error(f"Error al extraer texto: {str(e)}")
            return ""
    
    def extract_text_from_url(self, url, lang='spa'):
        """Extrae texto de una imagen desde una URL"""
        image = self.load_image_from_url(url)
        if image is not None:
            return self.extract_text(image, lang)
        return ""
    
    def extract_text_from_path(self, path, lang='spa'):
        """Extrae texto de una imagen desde una ruta local"""
        image = self.load_image_from_path(path)
        if image is not None:
            return self.extract_text(image, lang)
        return ""