# -*- coding: utf-8 -*-
import os
import pytesseract
from PIL import Image

class OCRProcessor:
    """Clase para procesar imágenes con OCR."""
    
    def __init__(self, tesseract_cmd=None):
        """Inicializa el procesador OCR.
        
        Args:
            tesseract_cmd (str, optional): Ruta al ejecutable de Tesseract.
        """
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        
        # Verificar que Tesseract esté disponible
        try:
            self.tesseract_version = pytesseract.get_tesseract_version()
            print(f"Tesseract OCR inicializado (versión {self.tesseract_version})")
        except pytesseract.TesseractNotFoundError:
            print("Error: Tesseract OCR no está instalado o no está en el PATH.")
            self.tesseract_version = None
    
    def extract_text(self, image_path, lang='spa'):
        """Extrae texto de una imagen usando OCR.
        
        Args:
            image_path (str): Ruta a la imagen
            lang (str, optional): Idioma para OCR. Por defecto 'spa' (español)
            
        Returns:
            str: Texto extraído de la imagen
            
        Raises:
            FileNotFoundError: Si no se encuentra la imagen
            pytesseract.TesseractError: Si hay un error con Tesseract
        """
        if not self.tesseract_version:
            raise RuntimeError("Tesseract OCR no está configurado correctamente")
            
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"No se encontró la imagen: {image_path}")
            
        img = Image.open(image_path)
        print(f"Procesando imagen: {img.format}, {img.size}px")
        
        text = pytesseract.image_to_string(img, lang=lang)
        return text