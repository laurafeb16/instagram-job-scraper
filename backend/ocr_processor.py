# -*- coding: utf-8 -*-
"""
Módulo para procesar imágenes con OCR usando OpenCV y Tesseract.
"""
import os
import requests
import pytesseract
import cv2
import numpy as np
from PIL import Image
import io
import logging
from typing import Optional, Dict, List, Tuple, Union, Any
from backend.metrics import track_time, OCR_PROCESSING_DURATION, track_http_request

logger = logging.getLogger(__name__)

class OCRProcessor:
    """Clase para procesar imágenes con OCR."""
    
    def __init__(self, tesseract_cmd: Optional[str] = None) -> None:
        """Inicializa el procesador OCR.
        
        Args:
            tesseract_cmd: Ruta al ejecutable de Tesseract
        """
        # Configurar ruta a Tesseract
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        
        # Configurar Tesseract para español e inglés
        self.config: str = '--oem 3 --psm 6 -l spa+eng'
        
        # Verificar instalación de Tesseract
        try:
            self.tesseract_version = pytesseract.get_tesseract_version()
            logger.info(f"Tesseract inicializado (version {self.tesseract_version})")
        except Exception as e:
            logger.error(f"Error al inicializar Tesseract: {e}")
            self.tesseract_version = None
    
    @track_http_request(method="GET", endpoint="image")
    def download_image(self, image_url: str) -> Optional[np.ndarray]:
        """Descarga una imagen desde URL y la devuelve como array de OpenCV.
        
        Args:
            image_url: URL de la imagen
            
        Returns:
            Imagen en formato OpenCV o None si hubo error
        """
        try:
            response = requests.get(image_url, stream=True)
            response.raise_for_status()
            
            # Convertir a PIL Image y luego a OpenCV
            image = Image.open(io.BytesIO(response.content))
            return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        except Exception as e:
            logger.error(f"Error al descargar imagen {image_url}: {e}")
            return None
    
    def load_image(self, image_path: str) -> Optional[np.ndarray]:
        """Carga una imagen desde archivo local.
        
        Args:
            image_path: Ruta a la imagen
            
        Returns:
            Imagen en formato OpenCV o None si hubo error
        """
        try:
            if not os.path.exists(image_path):
                logger.error(f"No se encontro la imagen: {image_path}")
                return None
                
            image = cv2.imread(image_path)
            if image is None:
                logger.error(f"No se pudo leer la imagen: {image_path}")
                return None
                
            return image
        except Exception as e:
            logger.error(f"Error al cargar imagen {image_path}: {e}")
            return None
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocesa la imagen para mejorar la precisión del OCR.
        
        Args:
            image: Imagen en formato OpenCV
            
        Returns:
            Imagen preprocesada
        """
        # Copiar imagen para evitar modificar la original
        processed = image.copy()
        
        # Verificar si la imagen es a color
        if len(processed.shape) == 3:
            # Convertir a escala de grises
            gray = cv2.cvtColor(processed, cv2.COLOR_BGR2GRAY)
        else:
            gray = processed
        
        # Aplicar Gaussian blur para reducir ruido
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Aplicar umbral adaptativo para manejar iluminación variable
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        # Operaciones morfológicas para limpiar
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        return cleaned
    
    @track_time(OCR_PROCESSING_DURATION)
    def extract_text(self, image_path_or_url: str) -> str:
        """Extrae texto de una imagen usando OCR.
        
        Args:
            image_path_or_url: Ruta local o URL de la imagen
            
        Returns:
            Texto extraído de la imagen
        """
        try:
            # Determinar si es URL o ruta local
            if image_path_or_url.startswith(('http://', 'https://')):
                image = self.download_image(image_path_or_url)
            else:
                image = self.load_image(image_path_or_url)
            
            if image is None:
                return ""
            
            # Preprocesar para mejor OCR
            processed = self.preprocess_image(image)
            
            # Extraer texto usando Tesseract
            text = pytesseract.image_to_string(
                processed, 
                config=self.config
            )
            
            # Limpiar texto
            text = self.clean_text(text)
            
            logger.info(f"Extraidos {len(text)} caracteres de la imagen")
            return text
            
        except Exception as e:
            logger.error(f"Error en procesamiento OCR: {e}")
            return ""
    
    def clean_text(self, text: str) -> str:
        """Limpia y normaliza el texto extraído.
        
        Args:
            text: Texto a limpiar
            
        Returns:
            Texto limpio
        """
        if not text:
            return ""
        
        # Eliminar espacios en blanco extra y normalizar
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        cleaned = '\n'.join(lines)
        
        # Reemplazar errores comunes de OCR
        replacements: Dict[str, str] = {
            '|': 'I',
            '@': 'a',
            '0': 'O',  # Solo en contextos específicos
            '1': 'l',  # Solo en contextos específicos
        }
        
        # Aplicar reemplazos cuidadosamente
        for old, new in replacements.items():
            if old in cleaned:
                cleaned = cleaned.replace(old, new)
        
        return cleaned
