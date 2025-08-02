# -*- coding: utf-8 -*-
import logging
import os
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import requests
from io import BytesIO

class EnhancedImageProcessor:
    def __init__(self, tesseract_path=None):
        # Configuración básica igual...
        self.logger = logging.getLogger(__name__)
        
        # Configurar Tesseract
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        else:
            default_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
            if os.path.exists(default_path):
                pytesseract.pytesseract.tesseract_cmd = default_path
        
        try:
            pytesseract.get_tesseract_version()
            self.logger.info(f"Tesseract versión: {pytesseract.get_tesseract_version()}")
        except Exception as e:
            self.logger.error(f"Error al verificar Tesseract: {str(e)}")
    
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
        """Preprocesa la imagen con técnicas avanzadas usando solo PIL"""
        try:
            # Convertir a escala de grises
            gray_image = image.convert('L')
            
            # Aumentar tamaño (3x en lugar de 2x)
            width, height = gray_image.size
            enlarged = gray_image.resize((width*3, height*3), Image.LANCZOS)
            
            # Mejorar contraste
            enhancer = ImageEnhance.Contrast(enlarged)
            enhanced_img = enhancer.enhance(3.5)  # Aumentar más el contraste
            
            # Aumentar nitidez para mejorar detección de bordes
            sharpener = ImageEnhance.Sharpness(enhanced_img)
            sharpened_img = sharpener.enhance(2.5)  # Aumentar nitidez
            
            # Filtro para reducir ruido
            filtered_img = sharpened_img.filter(ImageFilter.MedianFilter(size=3))
            
            # Ajustar brillo
            brightness = ImageEnhance.Brightness(filtered_img)
            brightened_img = brightness.enhance(1.3)  # Aumentar brillo
            
            # Binarización - convertir a blanco y negro
            threshold_img = brightened_img.point(lambda p: 255 if p > 140 else 0)
            
            # Guardar versión preprocesada para depuración
            debug_dir = "debug_images_processed"
            if not os.path.exists(debug_dir):
                os.makedirs(debug_dir)
                
            filename = f"{debug_dir}/last_processed.png"
            threshold_img.save(filename)
            self.logger.info(f"Imagen preprocesada guardada en {filename}")
            
            return threshold_img
        except Exception as e:
            self.logger.error(f"Error en el preprocesamiento: {str(e)}")
            return image
    
    def extract_text(self, image, lang='spa'):
        """Extrae texto de una imagen usando Tesseract OCR con múltiples configuraciones"""
        try:
            # Preprocesar la imagen
            processed_image = self.preprocess_image(image)
            
            # Probar diferentes configuraciones de Tesseract y quedarse con la mejor
            configs = [
                '--psm 1 --oem 3 -l spa',  # Página automática con orientación
                '--psm 3 --oem 3 -l spa',  # Página completa
                '--psm 4 --oem 3 -l spa',  # Bloque de texto orientado
                '--psm 6 --oem 3 -l spa',  # Bloque uniforme de texto
            ]
            
            best_text = ""
            best_length = 0
            best_config = ""
            
            for config in configs:
                # Extraer texto con la configuración actual
                text = pytesseract.image_to_string(processed_image, config=config)
                
                # Post-procesamiento del texto
                text = text.replace('\n\n', '\n').strip()
                
                # Verificar si este resultado es mejor que el anterior
                if len(text) > best_length:
                    best_text = text
                    best_length = len(text)
                    best_config = config
            
            self.logger.info(f"Texto extraído con {best_length} caracteres")
            self.logger.info(f"Mejor configuración: {best_config}")
            return best_text
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