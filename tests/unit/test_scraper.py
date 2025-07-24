# -*- coding: utf-8 -*-
import pytest
from unittest.mock import patch, MagicMock, mock_open  # Añadir mock_open
from backend.scraper import InstagramScraper

def test_scraper_initialization():
    # Mockear la función setup_driver
    with patch.object(InstagramScraper, 'setup_driver'):
        scraper = InstagramScraper(headless=True)
        
        # Verificar valores de inicialización
        assert scraper.headless == True
        assert scraper.data_dir == "data/raw"

@patch('time.sleep')
def test_wait_random(mock_sleep):
    with patch.object(InstagramScraper, 'setup_driver'):
        scraper = InstagramScraper()
        scraper.wait_random(1, 2)
        assert mock_sleep.called

# Corregido: usar close en lugar de cleanup
@patch('selenium.webdriver.Chrome.quit')
def test_close(mock_quit):
    with patch.object(InstagramScraper, 'setup_driver'):
        scraper = InstagramScraper()
        # Crear un driver mock
        driver_mock = MagicMock()
        scraper.driver = driver_mock
        
        # Llamar al método close
        scraper.close()
        
        # Verificar que se llamó a quit en el driver
        assert driver_mock.quit.called

# Reemplazar el test fallido por uno que use scrape_post
@patch('selenium.webdriver.Chrome')
def test_scrape_post_basic(mock_chrome):
    # Configurar driver mock
    driver_mock = MagicMock()
    mock_chrome.return_value = driver_mock
    
    # Mockear time.sleep para evitar pausas
    with patch('time.sleep'):
        # Mockear os.path.exists
        with patch('os.path.exists', return_value=True):
            # Mockear json.dump
            with patch('json.dump'):
                # Mockear open
                with patch('builtins.open', mock_open()):
                    # Crear scraper y asignar driver
                    with patch.object(InstagramScraper, 'setup_driver'):
                        scraper = InstagramScraper()
                        scraper.driver = driver_mock
                        
                        # Configurar elementos necesarios
                        img_element = MagicMock()
                        img_element.get_attribute.return_value = "https://example.com/image.jpg"
                        time_element = MagicMock()
                        time_element.get_attribute.return_value = "2023-01-01T12:00:00"
                        caption_element = MagicMock()
                        caption_element.get_attribute.return_value = "Test caption"
                        
                        # Configurar find_element para devolver elementos
                        driver_mock.find_element.side_effect = [img_element, time_element]
                        driver_mock.find_elements.return_value = [caption_element]
                        
                        # Mockear requests.get para la imagen
                        with patch('requests.get') as mock_requests:
                            response_mock = MagicMock()
                            response_mock.status_code = 200
                            mock_requests.return_value = response_mock
                            
                            # Ejecutar método
                            result = scraper.scrape_post("https://instagram.com/p/ABC123/")
                            
                            # Verificar
                            assert result is not None
                            assert 'shortcode' in result
                            assert driver_mock.get.called

@patch('selenium.webdriver.Chrome')
def test_setup_driver(mock_chrome):
    # Ejecutar el método real (sin mockear)
    scraper = InstagramScraper()
    
    # Verificar que Chrome fue llamado
    assert mock_chrome.called
    
    # Verificar que el driver fue configurado
    assert hasattr(scraper, 'driver')

@patch('backend.scraper.WebDriverWait')
@patch('selenium.webdriver.Chrome')
def test_scrape_post(mock_chrome, mock_wait):
    # Configurar mocks
    driver_mock = MagicMock()
    mock_chrome.return_value = driver_mock
    
    # Configurar elementos a encontrar
    element_mock = MagicMock()
    element_mock.get_attribute.return_value = "https://example.com/image.jpg"
    driver_mock.find_element.return_value = element_mock
    
    # Mockear time_element
    time_element = MagicMock()
    time_element.get_attribute.return_value = "2023-01-01T12:00:00"
    
    # Configurar find_elements para devolver elementos con text content
    caption_element = MagicMock()
    caption_element.get_attribute.return_value = "Test caption"
    driver_mock.find_elements.return_value = [caption_element]
    
    # Mockear request.get para descarga de imagen
    with patch('requests.get') as mock_requests:
        response_mock = MagicMock()
        response_mock.status_code = 200
        response_mock.content = b"test image data"
        mock_requests.return_value = response_mock
        
        # Mockear open
        with patch('builtins.open', mock_open()) as mock_file:
            # Mockear json.dump
            with patch('json.dump') as mock_json_dump:
                # Preparar scraper
                scraper = InstagramScraper()
                scraper.driver = driver_mock
                
                # Mockear os.path.exists para crear el archivo json
                with patch('os.path.exists', return_value=True):
                    # Ejecutar
                    with patch('time.sleep'):  # Evitar esperas
                        result = scraper.scrape_post("https://instagram.com/p/ABC123/")
                    
                    # Verificar
                    assert result is not None
                    assert mock_file.called  # Se llamó a open para guardar imagen
                    assert mock_json_dump.called  # Se guardaron los metadatos
