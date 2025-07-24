# -*- coding: utf-8 -*-
import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from backend.ocr_processor import OCRProcessor

def test_ocr_basic():
    # Crear un OCRProcessor con métodos mockeados
    processor = OCRProcessor()
    
    # Mockear los métodos de carga y procesamiento
    processor.load_image = MagicMock(return_value=np.zeros((100, 100), dtype=np.uint8))
    processor.preprocess_image = MagicMock(return_value=np.zeros((100, 100), dtype=np.uint8))
    
    # Mockear pytesseract.image_to_string directamente
    with patch('pytesseract.image_to_string', return_value="Vacante: Desarrollador Python"):
        # Ejecutar el método que queremos probar
        text = processor.extract_text("dummy_path.jpg")
        
        # Verificar resultados
        assert "Vacante" in text
        assert "Desarrollador Python" in text

def test_clean_text():
    processor = OCRProcessor()
    
    # Texto con problemas comunes de OCR
    dirty_text = "He||o Wor|d\n\nThis is a 0CR test\n\n  Extra spaces  "
    
    cleaned = processor.clean_text(dirty_text)
    
    # Verificar limpieza de acuerdo a la implementación actual
    assert "HeIIo WorId" in cleaned  # Reemplaza | con I (mayúscula)
    assert "OCR test" in cleaned     # Reemplaza 0 con O
    assert "  Extra spaces  " not in cleaned  # No debe tener espacios extra
# Prueba para cuando la imagen no existe
def test_extract_text_no_image():
    processor = OCRProcessor()
    
    # Simular que load_image devuelve None
    processor.load_image = MagicMock(return_value=None)
    
    # Ejecutar
    text = processor.extract_text("ruta_inexistente.jpg")
    
    # Verificar
    assert text == ""
    assert processor.load_image.called

# Prueba para manejo de errores
@patch('pytesseract.image_to_string', side_effect=Exception("Error de OCR"))
def test_extract_text_error(mock_ocr):
    processor = OCRProcessor()
    
    # Simular que load_image devuelve una imagen válida
    processor.load_image = MagicMock(return_value=np.zeros((100, 100), dtype=np.uint8))
    processor.preprocess_image = MagicMock(return_value=np.zeros((100, 100), dtype=np.uint8))
    
    # Ejecutar
    text = processor.extract_text("ruta_con_error.jpg")
    
    # Verificar
    assert text == ""
    assert processor.load_image.called
    assert mock_ocr.called
# Prueba para URL de imagen
@patch('requests.get')
def test_download_image(mock_requests):
    # Simular respuesta
    response_mock = MagicMock()
    response_mock.content = b"fake image data"
    mock_requests.return_value = response_mock
    
    # Mockear Image.open
    with patch('PIL.Image.open') as mock_image_open:
        # Configurar mock de Image
        mock_img = MagicMock()
        mock_image_open.return_value = mock_img
        
        # Mockear numpy y cv2
        with patch('numpy.array') as mock_array:
            with patch('cv2.cvtColor') as mock_cv2:
                # Configurar retorno
                mock_array.return_value = "numpy array"
                mock_cv2.return_value = "cv2 processed"
                
                # Ejecutar
                processor = OCRProcessor()
                result = processor.download_image("https://example.com/image.jpg")
                
                # Verificar
                assert result == "cv2 processed"
                assert mock_requests.called
                assert mock_image_open.called
                
# Prueba para download_image con error
@patch('requests.get', side_effect=Exception("Error al descargar"))
def test_download_image_error(mock_requests):
    processor = OCRProcessor()
    result = processor.download_image("https://example.com/error.jpg")
    
    assert result is None
    assert mock_requests.called
