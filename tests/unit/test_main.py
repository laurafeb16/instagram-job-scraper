# -*- coding: utf-8 -*-
import pytest
from unittest.mock import patch, MagicMock, mock_open
import os
from backend.main import process_posts, run_scraper

@patch('json.dump')
@patch('builtins.open', new_callable=mock_open)
def test_process_posts_basic(mock_file, mock_json_dump):
    # Crear mocks para OCRProcessor y JobExtractor
    mock_processor = MagicMock()
    mock_processor.extract_text.return_value = "Texto OCR de prueba"
    
    mock_extractor = MagicMock()
    mock_extractor.is_job_post.return_value = (True, "Empresa")
    mock_extractor.extract_job_info.return_value = {
        "company": "Empresa",
        "title": "Puesto",
        "skills": ["Python"]
    }
    
    # Crear post ficticio con ruta a imagen existente
    # Usamos __file__ para tener una ruta real que exista
    test_post = {
        "shortcode": "ABC123",
        "caption": "Test post",
        "local_image_path": __file__  # Usar este archivo como "imagen"
    }
    
    # Ejecutar función
    with patch('os.path.exists', return_value=True):
        result = process_posts([test_post], mock_processor, mock_extractor)
    
    # Verificar
    assert len(result) == 1
    assert result[0]["is_job_post"] == True
    assert mock_processor.extract_text.called
    assert mock_extractor.is_job_post.called

@patch('backend.main.InstagramScraper')
@patch('backend.main.OCRProcessor')
@patch('backend.main.JobExtractor')
@patch('os.makedirs')
@patch('json.dump')
@patch('builtins.open', new_callable=mock_open)
def test_run_scraper_basic(mock_file, mock_json_dump, mock_makedirs, 
                           mock_extractor_class, mock_ocr_class, mock_scraper_class):
    # Configurar mocks
    mock_scraper = MagicMock()
    mock_scraper_class.return_value = mock_scraper
    
    # Simular posts encontrados
    mock_scraper.scrape_profile.return_value = [
        {"shortcode": "ABC123", "caption": "Test post"}
    ]
    
    # Mockear process_posts
    with patch('backend.main.process_posts', return_value=[{"shortcode": "ABC123"}]):
        # Ejecutar
        result = run_scraper("test_user", max_posts=1)
        
        # Verificar
        assert result == 1
        assert mock_scraper.scrape_profile.called
        assert mock_scraper.close.called
# Prueba cuando no hay posts
@patch('backend.main.InstagramScraper')
def test_run_scraper_no_posts(mock_scraper_class):
    # Configurar mocks
    mock_scraper = MagicMock()
    mock_scraper_class.return_value = mock_scraper
    
    # Simular que no se encontraron posts
    mock_scraper.scrape_profile.return_value = []
    
    # Ejecutar
    result = run_scraper("test_user", max_posts=1)
    
    # Verificar
    assert result == 0
    assert mock_scraper.scrape_profile.called

# Prueba para manejo de excepciones
@patch('backend.main.InstagramScraper')
def test_run_scraper_exception(mock_scraper_class):
    # Configurar mocks
    mock_scraper = MagicMock()
    mock_scraper_class.return_value = mock_scraper
    
    # Simular una excepción
    mock_scraper.scrape_profile.side_effect = Exception("Error de prueba")
    
    # Ejecutar
    result = run_scraper("test_user", max_posts=1)
    
    # Verificar
    assert result == 0
    assert mock_scraper.scrape_profile.called
    assert mock_scraper.close.called
