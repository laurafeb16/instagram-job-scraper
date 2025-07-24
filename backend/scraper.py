# -*- coding: utf-8 -*-
"""
Módulo para extraer información de perfiles de Instagram usando Selenium.
"""
import os
import time
import json
import random
import logging
import requests
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

logger = logging.getLogger(__name__)

class InstagramScraper:
    """Clase para extraer información de perfiles de Instagram."""
    
    def __init__(self, headless=False, data_dir="data/raw"):
        """Inicializa el scraper.
        
        Args:
            headless (bool): Si se ejecuta en modo headless (sin interfaz gráfica)
            data_dir (str): Directorio donde guardar los datos extraídos
        """
        self.data_dir = data_dir
        self.headless = headless
        self.setup_driver()
        
        # Crear directorio si no existe
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir, exist_ok=True)
    
    def setup_driver(self):
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
        
        # Usar ChromeDriver específico o el PATH
        chrome_driver_path = os.getenv("CHROME_DRIVER_PATH")
        if chrome_driver_path and os.path.exists(chrome_driver_path):
            service = Service(executable_path=chrome_driver_path)
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
        else:
            self.driver = webdriver.Chrome(options=chrome_options)
            
        # Configurar tiempos de espera
        self.driver.implicitly_wait(10)
    
    def wait_random(self, min_time=2, max_time=5):
        """Espera un tiempo aleatorio para simular comportamiento humano."""
        base_time = random.uniform(min_time, max_time)
        variation = random.uniform(0.5, 1.5)
        sleep_time = base_time * variation
        
        logger.debug(f"Esperando {sleep_time:.2f} segundos...")
        time.sleep(sleep_time)
    
    def scrape_profile(self, username: str, max_posts: int = 10) -> List[Dict]:
        """Extrae posts de un perfil de Instagram.
        
        Args:
            username (str): Nombre de usuario del perfil a analizar
            max_posts (int): Número máximo de posts a analizar
            
        Returns:
            List[Dict]: Lista de posts extraídos
        """
        posts = []
        url = f"https://www.instagram.com/{username}/"
        
        try:
            logger.info(f"Accediendo al perfil: {username}")
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
                logger.error(f"No se pudieron cargar los posts del perfil {username}")
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
            
            logger.info(f"Encontrados {len(post_links)} enlaces a posts")
            
            # Extraer detalles de cada post
            for i, post_url in enumerate(list(post_links)[:max_posts]):
                try:
                    logger.info(f"Procesando post {i+1}/{min(len(post_links), max_posts)}: {post_url}")
                    post_data = self.scrape_post(post_url)
                    
                    if post_data:
                        posts.append(post_data)
                        
                    # Pausa entre posts
                    self.wait_random(3, 7)
                except Exception as e:
                    logger.error(f"Error al procesar post {post_url}: {e}")
                    continue            
        except Exception as e:
            logger.error(f"Error al analizar perfil {username}: {e}")
        
        return posts
    
    def scrape_post(self, post_url: str) -> Optional[Dict]:
        """Extrae información de un post individual de Instagram.
        
        Args:
            post_url (str): URL del post a analizar
            
        Returns:
            Dict: Datos extraídos del post o None si hubo un error
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
            post_data = {
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
                    logger.error(f"Error al descargar imagen {image_url}: {e}")
            
            # Guardar metadatos en JSON
            json_path = os.path.join(self.data_dir, f"{shortcode}.json")
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(post_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Datos del post {shortcode} guardados correctamente")
            return post_data
            
        except Exception as e:
            logger.error(f"Error al procesar post: {e}")
            return None
    
    def close(self):
        """Cierra el navegador y libera recursos."""
        if hasattr(self, 'driver'):
            self.driver.quit()
            logger.debug("Navegador cerrado correctamente")