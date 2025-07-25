# -*- coding: utf-8 -*-
"""
Módulo para extraer información de perfiles de Instagram usando Selenium.
"""
import os
import time
import random
import glob
import shutil
import json
import threading
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple, Union, Callable, TypeVar

import requests
import instaloader
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from backend.logging_config import get_logger, with_correlation_id

# Configurar logger
logger = get_logger(__name__)

class TimeoutError(Exception):
    """Excepción levantada cuando una operación excede el tiempo límite."""
    pass

T = TypeVar('T')

def timeout(seconds: int) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorador para establecer un tiempo límite en la ejecución de una función.
    
    Args:
        seconds: Tiempo límite en segundos
        
    Returns:
        Decorador configurado
    """
    def decorator(function: Callable[..., T]) -> Callable[..., T]:
        def wrapper(*args: Any, **kwargs: Any) -> T:
            result: List[Union[T, Exception]] = [TimeoutError("Operación demorada demasiado tiempo")]
            def target() -> None:
                try:
                    result[0] = function(*args, **kwargs)
                except Exception as e:
                    result[0] = e
            thread = threading.Thread(target=target)
            thread.daemon = True
            thread.start()
            thread.join(seconds)
            if isinstance(result[0], Exception):
                raise result[0]
            return result[0]
        return wrapper
    return decorator

def ensure_dir(directory: str) -> None:
    """Asegura que exista un directorio, creándolo si es necesario.
    
    Args:
        directory: Ruta del directorio a verificar/crear
    """
    if not os.path.exists(directory):
        os.makedirs(directory)

class InstagramScraper:
    """Clase para extraer información de perfiles de Instagram."""
    
    def __init__(self, data_dir: str = "data/raw", temp_dir: str = "temp_instagram_data", 
                 headless: bool = False) -> None:
        """Inicializa el scraper.
        
        Args:
            data_dir: Directorio donde guardar los datos extraídos
            temp_dir: Directorio temporal para descargas
            headless: Si se ejecuta en modo headless (sin interfaz gráfica)
        """
        self.data_dir = data_dir
        self.temp_dir = temp_dir
        self.headless = headless
        
        # Crear directorios necesarios
        ensure_dir(self.data_dir)
        ensure_dir(self.temp_dir)
        
        # Configurar el driver
        self.setup_driver()
        
        self.authenticated = False
        
        logger.info("Instagram scraper iniciado", 
                   data_dir=data_dir, 
                   temp_dir=temp_dir, 
                   headless=headless)
    
    def setup_driver(self) -> None:
        """Configura el navegador Chrome para el scraping."""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless")
        
        # Configuraciones para evitar detección de automatización
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        
        # Configuraciones de rendimiento y estabilidad
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # User agent humano
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")
        
        # Configurar servicio y driver
        self.driver = webdriver.Chrome(options=chrome_options)
        
        # Configurar tiempos de espera
        self.driver.implicitly_wait(10)
        
        logger.debug("Navegador Chrome configurado")
    
    def wait_random(self, min_time: float = 2, max_time: float = 5) -> None:
        """Espera un tiempo aleatorio para simular comportamiento humano.
        
        Args:
            min_time: Tiempo mínimo de espera en segundos
            max_time: Tiempo máximo de espera en segundos
        """
        base_time = random.uniform(min_time, max_time)
        variation = random.uniform(0.5, 1.5)
        sleep_time = base_time * variation
        
        logger.debug(f"Esperando {sleep_time:.2f} segundos")
        time.sleep(sleep_time)
    
    @with_correlation_id
    def scrape_profile(self, username: str, max_posts: int = 10, 
                      logger: Any = None) -> List[Dict[str, Any]]:
        """Extrae posts de un perfil de Instagram.
        
        Args:
            username: Nombre de usuario del perfil a analizar
            max_posts: Número máximo de posts a analizar
            logger: Logger para seguimiento
            
        Returns:
            Lista de posts extraídos
        """
        posts: List[Dict[str, Any]] = []
        url = f"https://www.instagram.com/{username}/"
        
        try:
            logger.info("Accediendo al perfil", username=username)
            self.driver.get(url)
            self.wait_random(3, 6)
            
            # Rechazar cookies si aparece el diálogo
            try:
                cookie_button = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Decline') or contains(text(), 'Rechazar')]"))
                )
                cookie_button.click()
                logger.debug("Diálogo de cookies cerrado")
                self.wait_random(1, 3)
            except TimeoutException:
                logger.debug("No se encontró diálogo de cookies")
            
            # Comprobar si el perfil existe
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "article a"))
                )
            except TimeoutException:
                logger.error("No se pudieron cargar los posts del perfil", username=username)
                return []
            
            # Recopilar enlaces a los posts
            post_links = set()
            scroll_attempts = 0
            max_scroll_attempts = 15  # Limitar intentos para evitar bucles infinitos
            
            while len(post_links) < max_posts and scroll_attempts < max_scroll_attempts:
                # Encontrar enlaces a posts
                elements = self.driver.find_elements(By.CSS_SELECTOR, 'article a[href*="/p/"]')
                
                for element in elements:
                    href = element.get_attribute('href')
                    if href and '/p/' in href:
                        post_links.add(href)
                
                if len(post_links) >= max_posts:
                    break
                
                # Simulación de comportamiento humano
                self.wait_random(0.5, 1)
                
                # Scroll con comportamiento aleatorio
                scroll_height = random.randint(500, 1000)
                self.driver.execute_script(f"window.scrollBy(0, {scroll_height});")
                
                # Movimiento aleatorio del mouse
                self.driver.execute_script(
                    f"window.scrollBy({random.randint(-20, 20)}, {random.randint(-20, 20)});"
                )
                
                self.wait_random(2, 4)
                scroll_attempts += 1
            
            logger.info(f"Encontrados {len(post_links)} enlaces a posts", count=len(post_links))
            
            # Extraer detalles de cada post
            for i, post_url in enumerate(list(post_links)[:max_posts]):
                try:
                    logger.info(f"Procesando post {i+1}/{min(len(post_links), max_posts)}", 
                               post_url=post_url, 
                               progress=f"{i+1}/{min(len(post_links), max_posts)}")
                    
                    post_data = self.scrape_post(post_url)
                    
                    if post_data:
                        posts.append(post_data)
                        
                    # Pausa entre posts
                    self.wait_random(3, 7)
                except Exception as e:
                    logger.error("Error al procesar post", 
                                post_url=post_url, 
                                error=str(e))
                    continue
            
        except Exception as e:
            logger.error("Error al analizar perfil", 
                        username=username, 
                        error=str(e))
        
        return posts
    
    @timeout(30)
    def get_next_post(self, iterator: Any) -> Any:
        """Obtiene el siguiente post de un iterador con timeout.
        
        Args:
            iterator: Iterador de posts de Instagram
            
        Returns:
            Objeto de post de Instagram
        """
        return next(iterator)
    
    def scrape_post(self, post_url: str) -> Optional[Dict[str, Any]]:
        """Extrae información de un post individual de Instagram.
        
        Args:
            post_url: URL del post a analizar
            
        Returns:
            Datos extraídos del post o None si hubo un error
        """
        try:
            self.driver.get(post_url)
            self.wait_random(3, 6)
            
            # Extraer shortcode del URL
            shortcode = post_url.split('/p/')[-1].rstrip('/').split('/')[0]
            
            # Obtener fecha de publicación
            try:
                time_element = self.driver.find_element(By.TAG_NAME, "time")
                timestamp = time_element.get_attribute("datetime")
            except NoSuchElementException:
                timestamp = datetime.now().isoformat()
            
            # Obtener URL de la imagen
            try:
                img_element = self.driver.find_element(By.CSS_SELECTOR, 'article img[src]')
                image_url = img_element.get_attribute('src')
            except NoSuchElementException:
                logger.warning(f"No se encontró imagen en el post {shortcode}")
                image_url = None
            
            # Obtener texto del caption
            try:
                # Estrategia 1: Buscar en spans largos
                caption_elements = self.driver.find_elements(By.CSS_SELECTOR, 'article span')
                caption = ""
                
                for elem in caption_elements:
                    text = elem.get_attribute('textContent')
                    if text and len(text) > 50:  # Probablemente es el caption
                        caption = text
                        break
                
                # Estrategia 2: Buscar en divs con más contenido
                if not caption:
                    div_elements = self.driver.find_elements(By.CSS_SELECTOR, 'article div')
                    for elem in div_elements:
                        text = elem.get_attribute('textContent')
                        if text and len(text) > 100:  # Es más probable que sea el caption
                            caption = text
                            break
            except:
                caption = ""
            
            # Guardar información básica
            post_data: Dict[str, Any] = {
                'shortcode': shortcode,
                'post_url': post_url,
                'image_url': image_url,
                'caption': caption,
                'timestamp': timestamp,
                'scrape_date': datetime.now().isoformat()
            }
            
            # Descargar la imagen si existe URL
            if image_url:
                image_path = os.path.join(self.data_dir, f"{shortcode}.jpg")
                
                # Descarga directa con requests
                try:
                    response = requests.get(image_url, stream=True)
                    if response.status_code == 200:
                        with open(image_path, 'wb') as f:
                            for chunk in response.iter_content(1024):
                                f.write(chunk)
                        logger.debug(f"Imagen guardada en {image_path}")
                        post_data['local_image_path'] = image_path
                except Exception as e:
                    logger.error(f"Error al descargar imagen", 
                                image_url=image_url, 
                                error=str(e))
            
            # Guardar metadatos en JSON
            json_path = os.path.join(self.data_dir, f"{shortcode}.json")
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(post_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Datos del post {shortcode} guardados correctamente", 
                       shortcode=shortcode, 
                       json_path=json_path)
            return post_data
            
        except Exception as e:
            logger.error("Error al procesar post", 
                        post_url=post_url, 
                        error=str(e))
            return None
    
    def close(self) -> None:
        """Cierra el navegador y libera recursos."""
        if hasattr(self, 'driver'):
            self.driver.quit()
            logger.debug("Navegador Chrome cerrado correctamente")