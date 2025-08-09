# -*- coding: utf-8 -*-
import logging
import os
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import requests
from io import BytesIO
import numpy as np # Added for potential future advanced image processing, not strictly used in current PIL example

class EnhancedImageProcessor:
    def __init__(self, tesseract_path=None):
        self.logger = logging.getLogger(__name__)
        
        # Configurar Tesseract
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        else:
            # Fallback a la ruta por defecto de Tesseract en Windows
            default_path_windows = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
            # Fallback a una ruta común en Linux/macOS
            default_path_unix = '/usr/bin/tesseract' # Adjust if tesseract is in /usr/local/bin etc.

            if os.path.exists(default_path_windows):
                pytesseract.pytesseract.tesseract_cmd = default_path_windows
            elif os.path.exists(default_path_unix):
                pytesseract.pytesseract.tesseract_cmd = default_path_unix
            else:
                self.logger.warning("Tesseract no encontrado en las rutas por defecto. Asegúrate de que esté en tu PATH o especifica 'tesseract_path'.")
       
        try:
            # Test Tesseract to ensure it's properly configured
            tesseract_version = pytesseract.get_tesseract_version()
            self.logger.info(f"Tesseract versión: {tesseract_version}")
        except pytesseract.TesseractNotFoundError:
            self.logger.error("Tesseract no está instalado o no está en el PATH. La extracción de texto fallará.")
        except Exception as e:
            self.logger.error(f"Error al verificar Tesseract: {str(e)}")
            
    def load_image_from_url(self, url):
        """Carga una imagen desde una URL"""
        try:
            response = requests.get(url, timeout=10) # Added timeout
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
            image = Image.open(BytesIO(response.content))
            self.logger.info(f"Imagen cargada exitosamente desde URL: {url}")
            return image.convert('RGB') # Ensure consistent mode
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error de red o HTTP al cargar imagen desde URL {url}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error inesperado al cargar imagen desde URL {url}: {e}")
            return None
            
    def load_image_from_path(self, path):
        """Carga una imagen desde una ruta local"""
        try:
            if not os.path.exists(path):
                self.logger.error(f"La ruta de la imagen no existe: {path}")
                return None
            image = Image.open(path)
            self.logger.info(f"Imagen cargada exitosamente desde ruta: {path}")
            return image.convert('RGB') # Ensure consistent mode
        except Exception as e:
            self.logger.error(f"Error al cargar imagen desde ruta {path}: {e}")
            return None
            
    def preprocess_image(self, image):
        """Preprocesa la imagen con técnicas avanzadas para mejorar el OCR."""
        if image is None:
            return None

        try:
            # 1. Convertir a escala de grises
            gray_image = image.convert('L')
            self.logger.debug("Paso 1: Convertido a escala de grises.")

            # 2. Aumentar tamaño (escalado heurístico basado en el formato)
            # Para el formato dado, un escalado mayor puede ser beneficioso.
            width, height = gray_image.size
            if width < 1000 or height < 1000: # Scale up if resolution is low
                enlarged = gray_image.resize((width * 4, height * 4), Image.LANCZOS)
                self.logger.debug("Paso 2: Imagen escalada 4x.")
            else:
                enlarged = gray_image.resize((width * 2, height * 2), Image.LANCZOS) # Less aggressive for already large images
                self.logger.debug("Paso 2: Imagen escalada 2x.")


            # 3. Mejorar contraste de forma adaptativa si es posible, o fija
            # Usamos autocontraste para distribuir el rango de píxeles
            contrast_enhanced = ImageOps.autocontrast(enlarged, cutoff=0.5)
            self.logger.debug("Paso 3: Contraste mejorado (autocontraste).")

            # 4. Aumentar nitidez
            sharpener = ImageEnhance.Sharpness(contrast_enhanced)
            sharpened_img = sharpener.enhance(3.0) # Ajustado a 3.0
            self.logger.debug("Paso 4: Nitidez aumentada.")

            # 5. Reducción de ruido con filtro mediano (más robusto para el ruido sal y pimienta)
            filtered_img = sharpened_img.filter(ImageFilter.MedianFilter(size=5)) # Aumentado a size=5
            self.logger.debug("Paso 5: Ruido reducido con MedianFilter.")

            # 6. Binarización adaptativa o con umbral mejorado
            # Para el tipo de imagen proporcionado, un umbral fijo puede funcionar bien si el fondo es claro y el texto oscuro.
            # Sin embargo, una binarización adaptativa es generalmente más robusta.
            # Aquí, probamos un umbral fijo después de los ajustes de contraste/brillo.
            # Considerar aplicar un segundo paso de contraste o brillo si el texto no es suficientemente oscuro.
            
            # Ajustar brillo para que el texto sea más oscuro antes de binarizar
            brightness = ImageEnhance.Brightness(filtered_img)
            brightened_img = brightness.enhance(0.8) # Reducir ligeramente el brillo general para oscurecer texto, o aumentar para fondos oscuros

            # Binarización: texto oscuro en fondo claro
            # Intentar un umbral un poco más alto, o una curva
            threshold = 150 # Este valor es experimental, ajustar según el resultado.
            binarized_img = brightened_img.point(lambda p: 0 if p < threshold else 255) # Invertido si el texto es claro y fondo oscuro.

            # Si el texto es oscuro sobre fondo claro (como la imagen de ejemplo), la lógica es:
            # píxeles > umbral son blancos (fondo), píxeles <= umbral son negros (texto).
            # binarized_img = brightened_img.point(lambda p: 255 if p > threshold else 0)


            # Si después de todos los pasos, el texto es tenue, podemos intentar otro paso de contraste
            final_processed_image = ImageEnhance.Contrast(binarized_img).enhance(1.5)
            
            # Guardar versión preprocesada para depuración
            debug_dir = "debug_images_processed"
            os.makedirs(debug_dir, exist_ok=True) # Ensure directory exists
            
            filename = os.path.join(debug_dir, f"last_processed_{os.urandom(4).hex()}.png") # Unique filename
            final_processed_image.save(filename)
            self.logger.info(f"Imagen preprocesada guardada en {filename}")
            
            return final_processed_image
        except Exception as e:
            self.logger.error(f"Error en el preprocesamiento: {e}", exc_info=True) # Added exc_info for traceback
            return image # Return original image on error
            
    def extract_text(self, image, lang='spa'):
        """Extrae texto de una imagen usando Tesseract OCR con múltiples configuraciones."""
        if image is None:
            return ""

        try:
            # Preprocesar la imagen
            processed_image = self.preprocess_image(image)
            if processed_image is None:
                self.logger.error("El preprocesamiento de la imagen falló, no se puede extraer texto.")
                return ""

            # Probar diferentes configuraciones de Tesseract y quedarse con la mejor
            # Priorizar --psm 6 y --psm 3 para documentos estructurados.
            # --oem 3 es el motor por defecto y el mejor para la mayoría de los casos.
            # Considerar --user-words y --user-patterns si hay vocabulario específico recurrente.
            configs = [
                f'--psm 3 --oem 3 -l {lang}',  # Fully automatic page segmentation, but no OSD
                f'--psm 6 --oem 3 -l {lang}',  # Assume a single uniform block of text
                f'--psm 1 --oem 3 -l {lang}',  # Automatic page segmentation with OSD
                f'--psm 4 --oem 3 -l {lang}',  # Assume a single column of text of variable sizes
            ]
            
            best_text = ""
            best_length = 0
            best_config = ""
            
            for config in configs:
                try:
                    text = pytesseract.image_to_string(processed_image, config=config)
                    
                    # Post-procesamiento del texto: limpiar espacios y nuevas líneas dobles
                    text = text.replace('\n\n', '\n').strip()
                    
                    if len(text) > best_length:
                        best_text = text
                        best_length = len(text)
                        best_config = config
                except Exception as e:
                    self.logger.warning(f"Error con config Tesseract '{config}': {e}")
                    continue # Try next config
            
            self.logger.info(f"Texto extraído con {best_length} caracteres. Mejor configuración: {best_config}")
            return best_text
        except pytesseract.TesseractNotFoundError:
            self.logger.error("Tesseract no está instalado o no está en el PATH. No se pudo extraer texto.")
            return ""
        except Exception as e:
            self.logger.error(f"Error general al extraer texto: {e}", exc_info=True)
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

# ========================================================================================
# FUNCIÓN DE COMPATIBILIDAD PARA MAIN.PY (NO MODIFICA EL CÓDIGO ORIGINAL ARRIBA)
# ========================================================================================

# Instancia global del procesador (singleton pattern)
_global_processor = None

def get_processor():
    """Obtiene una instancia del procesador OCR (singleton)"""
    global _global_processor
    if _global_processor is None:
        _global_processor = EnhancedImageProcessor()
    return _global_processor

def extract_text_from_image(image_path, lang='spa'):
    """
    Función de compatibilidad para main.py - CORREGIDA con guardado de debug
    """
    # === LOG TEMPORAL PARA DEBUGGING ===
    logger = logging.getLogger(__name__)
    logger.info(f"🧪 [DEBUG] extract_text_from_image MEJORADA ejecutándose para: {image_path}")
    
    try:
        processor = get_processor()
        extracted_text = processor.extract_text_from_path(image_path, lang)
        
        logger.info(f"🧪 [DEBUG] Texto extraído: {len(extracted_text)} caracteres")
        
        # === GUARDAR TEXTO EXTRAÍDO PARA DEBUG ===
        if extracted_text and len(extracted_text.strip()) > 10:
            try:
                debug_dir = "debug_texts"
                os.makedirs(debug_dir, exist_ok=True)
                logger.info(f"🧪 [DEBUG] Directorio debug_texts creado/verificado")
                
                base_name = os.path.splitext(os.path.basename(image_path))[0]
                debug_file = os.path.join(debug_dir, f"{base_name}.txt")
                logger.info(f"🧪 [DEBUG] Archivo debug: {debug_file}")
                
                # ALWAYS OVERWRITE - no verificar si existe
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(f"POST URL: [Extraído desde {image_path}]\n")
                    f.write(f"IMAGE URL: [Imagen local]\n") 
                    f.write(f"DESCRIPTION: [Texto extraído por OCR]\n")
                    f.write(f"EXTRACTED TEXT:\n")
                    f.write(extracted_text)
                
                logger.info(f"💾 Texto OCR guardado en: {debug_file}")     
            except Exception as save_error:
                logger.warning(f"Error guardando texto debug: {str(save_error)}")
        else:
            logger.info(f"🧪 [DEBUG] No se guardó texto - muy corto o vacío")
        
        return extracted_text
        
    except Exception as e:
        logger.error(f"Error en extract_text_from_image: {str(e)}")
        return ""

def extract_text_from_url(image_url, lang='spa'):
    """
    Función adicional para extraer texto desde URL
    
    Args:
        image_url (str): URL de la imagen
        lang (str): Idioma para OCR (por defecto 'spa' para español)
        
    Returns:
        str: Texto extraído de la imagen
    """
    try:
        processor = get_processor()
        return processor.extract_text_from_url(image_url, lang)
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Error en extract_text_from_url: {str(e)}")
        return ""

# Exportar funciones para compatibilidad
__all__ = [
    'EnhancedImageProcessor',
    'extract_text_from_image',
    'extract_text_from_url',
    'get_processor'
]