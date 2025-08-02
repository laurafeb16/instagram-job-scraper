# -*- coding: utf-8 -*-
import time
import os
import random
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging
import pickle

class InstagramScraper:
    def __init__(self, username, password, target_account, headless=False):
        self.username = username
        self.password = password
        self.target_account = target_account
        self.base_url = "https://www.instagram.com/"
        self.posts = []
        
        # Configurar logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler("instagram_scraper.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Configurar opciones de Chrome
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        
        # Usar ChromeDriver local
        chrome_driver_path = os.path.join(os.getcwd(), 'chromedriver.exe')
        self.logger.info(f"Buscando ChromeDriver en: {chrome_driver_path}")
        
        # Inicializar el driver
        self.driver = webdriver.Chrome(
            service=Service(chrome_driver_path),
            options=chrome_options
        )
        
        # Establecer la ventana a un tamaño común
        self.driver.set_window_size(1366, 768)
        
        # Configurar wait con más tiempo para esperar elementos
        self.wait = WebDriverWait(self.driver, 20)
        
    def random_sleep(self, min_seconds=1, max_seconds=3):
        """Espera un tiempo aleatorio para simular comportamiento humano"""
        time.sleep(random.uniform(min_seconds, max_seconds))
        
    def login(self):
        """Inicia sesión en Instagram o carga sesión guardada"""
        # Intentar cargar cookies primero
        if self.load_cookies():
            return True
        
        # Si no hay cookies o falló, hacer login normal
        try:
            self.logger.info("Iniciando sesión en Instagram")
            self.driver.get(self.base_url)
            self.random_sleep(3, 5)  # Esperar a que cargue la página
            
            # Manejar posible pop-up de cookies
            try:
                cookie_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Accept') or contains(text(), 'Aceptar') or contains(text(), 'Allow')]")
                if cookie_buttons:
                    cookie_buttons[0].click()
                    self.logger.info("Pop-up de cookies aceptado")
                    self.random_sleep(1, 2)
            except Exception as e:
                self.logger.info(f"No se pudo manejar el pop-up de cookies: {str(e)}")
            
            # Ingresar credenciales
            try:
                username_input = self.wait.until(
                    EC.presence_of_element_located((By.XPATH, "//input[@name='username']"))
                )
                self.random_sleep()
                
                password_input = self.wait.until(
                    EC.presence_of_element_located((By.XPATH, "//input[@name='password']"))
                )
                
                # Escribir usuario y contraseña de manera humana (caracter por caracter)
                for char in self.username:
                    username_input.send_keys(char)
                    self.random_sleep(0.1, 0.3)
                
                self.random_sleep()
                
                for char in self.password:
                    password_input.send_keys(char)
                    self.random_sleep(0.1, 0.3)
                
                self.random_sleep()
                
                # Hacer clic en el botón de login
                login_buttons = self.driver.find_elements(By.XPATH, "//button[@type='submit']")
                if login_buttons:
                    login_buttons[0].click()
                else:
                    self.logger.error("No se encontró el botón de login")
                    return False
                
                # Esperar a que se complete el login
                self.random_sleep(5, 8)
            except Exception as e:
                self.logger.error(f"Error al ingresar credenciales: {str(e)}")
                return False
            
            # Manejar posibles ventanas emergentes post-login
            try:
                # Verificar si hay ventanas emergentes de "Save Info" o "Not Now"
                not_now_buttons = self.driver.find_elements(By.XPATH, 
                    "//button[contains(text(), 'Not Now') or contains(text(), 'Ahora no') or contains(text(), 'Later')]")
                
                if not_now_buttons:
                    not_now_buttons[0].click()
                    self.logger.info("Ventana emergente 'Not Now' cerrada")
                    self.random_sleep(2, 3)
                
                # Verificar si hay notificaciones emergentes
                try:
                    notification_buttons = self.driver.find_elements(By.XPATH, 
                        "//button[contains(text(), 'Not Now') or contains(text(), 'Ahora no')]")
                    
                    if notification_buttons:
                        notification_buttons[0].click()
                        self.logger.info("Notificación 'Not Now' cerrada")
                        self.random_sleep(2, 3)
                except:
                    pass
                
            except Exception as e:
                self.logger.info(f"No se pudo manejar ventanas emergentes: {str(e)}")
            
            # Guardar cookies después de login exitoso
            self.save_cookies()
            self.logger.info("Login exitoso")
            return True
        except Exception as e:
            self.logger.error(f"Error durante el login: {str(e)}")
            return False
    
    def navigate_to_target_account(self):
        """Navega a la cuenta objetivo"""
        try:
            self.logger.info(f"Navegando a la cuenta: {self.target_account}")
            self.driver.get(f"{self.base_url}{self.target_account}/")
            self.random_sleep(3, 5)
            
            # Verificar si la cuenta existe
            if "Esta página no está disponible" in self.driver.page_source or "Page not found" in self.driver.page_source:
                self.logger.error(f"La cuenta {self.target_account} no existe o no está disponible")
                return False
                
            return True
        except Exception as e:
            self.logger.error(f"Error al navegar a la cuenta objetivo: {str(e)}")
            return False
    
    def scrape_posts(self, limit=5):
        """Extrae posts de la cuenta objetivo"""
        try:
            self.logger.info(f"Iniciando extracción de {limit} posts")
            
            posts_data = []
            post_count = 0
            
            # Encontrar y hacer clic en la primera publicación para abrirla
            self.random_sleep(2, 4)
            
            # Diferentes selectores para encontrar posts
            selectors = [
                "article a", 
                "article div[role='button']", 
                "div._aagw", 
                "div[role='button'] div > img",
                "article div > div > div > div > a"
            ]
            
            first_post = None
            for selector in selectors:
                try:
                    self.logger.info(f"Intentando selector: {selector}")
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        first_post = elements[0]
                        break
                except Exception as e:
                    self.logger.info(f"Selector {selector} falló: {str(e)}")
            
            if not first_post:
                self.logger.error("No se pudo encontrar ninguna publicación")
                # Guardar captura de pantalla para depuración
                self.driver.save_screenshot("error_no_posts.png")
                self.logger.info("Se guardó captura de pantalla en error_no_posts.png")
                return []
            
            self.logger.info("Haciendo clic en la primera publicación")
            first_post.click()
            self.random_sleep(3, 5)
            
            while post_count < limit:
                try:
                    # Extraer datos del post actual
                    self.logger.info(f"Extrayendo post {post_count + 1}/{limit}")
                    
                    # Obtener la URL del post
                    post_url = self.driver.current_url
                    
                    # Obtener la imagen (probar diferentes selectores)
                    img_element = None
                    img_selectors = [
                        "article img[sizes]", 
                        "article div[role='button'] img",
                        "div._aagv img",
                        "div[role='dialog'] div[role='button'] img",
                        "div._ab8w img",
                        "div[style*='transform'] img:not([draggable='false'])"
                    ]
                    
                    for selector in img_selectors:
                        try:
                            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            if elements:
                                img_element = elements[0]
                                break
                        except:
                            continue
                    
                    if not img_element:
                        self.logger.error("No se pudo encontrar la imagen")
                        img_url = ""
                    else:
                        img_url = img_element.get_attribute("src")
                        self.logger.info(f"Selector usado para imagen: {selector}")
                        
                    # Obtener la descripción (probar diferentes selectores)
                    description = ""
                    desc_selectors = [
                        "h1 + div",
                        "div._a9zs",
                        "ul div.x9f619 > div.x1lliihq",
                        "div[role='button'] + div"
                    ]
                    
                    for selector in desc_selectors:
                        try:
                            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            if elements and elements[0].text:
                                description = elements[0].text
                                break
                        except:
                            continue
                    
                    # Obtener la fecha
                    post_date = ""
                    try:
                        date_elements = self.driver.find_elements(By.CSS_SELECTOR, "time")
                        if date_elements:
                            post_date = date_elements[0].get_attribute("datetime")
                    except:
                        pass
                    
                    # Detectar si es un carrusel (múltiples imágenes)
                    is_carousel = False
                    carousel_indicators = self.driver.find_elements(By.CSS_SELECTOR, 
                        "div._acnb, div[class*='carousel'], ul._acay")
                    
                    if carousel_indicators:
                        is_carousel = True
                        self.logger.info("Detectado carrusel con múltiples imágenes")
                    
                    # Extraer todas las imágenes si es un carrusel
                    carousel_images = []
                    
                    if is_carousel:
                        # Guardar la primera imagen
                        if img_url:
                            carousel_images.append(img_url)
                        
                        # Hacer clic en el botón "Siguiente" de carrusel
                        carousel_next_buttons = self.driver.find_elements(By.CSS_SELECTOR, 
                            "button._afxu, button._aahr, svg[aria-label='Siguiente']")
                        
                        while carousel_next_buttons:
                            try:
                                carousel_next_buttons[0].click()
                                self.random_sleep(1, 2)
                                
                                # Obtener la nueva imagen
                                for selector in img_selectors:
                                    try:
                                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                                        if elements:
                                            carousel_img_url = elements[0].get_attribute("src")
                                            if carousel_img_url and carousel_img_url not in carousel_images:
                                                carousel_images.append(carousel_img_url)
                                            break
                                    except:
                                        continue
                                
                                # Buscar el siguiente botón de carrusel
                                carousel_next_buttons = self.driver.find_elements(By.CSS_SELECTOR, 
                                    "button._afxu, button._aahr, svg[aria-label='Siguiente']")
                                
                                # Si llegamos al final, salir del bucle
                                if not carousel_next_buttons or len(carousel_images) >= 10:  # Límite de seguridad
                                    break
                            except Exception as e:
                                self.logger.error(f"Error al navegar por el carrusel: {str(e)}")
                                break
            
                    # Guardar los datos
                    post_data = {
                        "url": post_url,
                        "image_url": img_url,
                        "description": description,
                        "date": post_date,
                        "scraped_at": datetime.now().isoformat(),
                        "is_carousel": is_carousel,
                        "carousel_images": carousel_images if is_carousel else []
                    }
                    
                    self.logger.info(f"Post extraído: {post_url}")
                    posts_data.append(post_data)
                    post_count += 1
                    
                    # Hacer clic en el botón "Siguiente" para ir al siguiente post
                    if post_count < limit:
                        next_clicked = False
                        next_selectors = [
                            "svg[aria-label='Next']",
                            "svg[aria-label='Siguiente']",
                            "div._aaqg button",
                            "div._aaqg > button",
                            "button.coreSpriteRightPaginationArrow"
                        ]
                        
                        for selector in next_selectors:
                            try:
                                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                                if elements:
                                    elements[0].click()
                                    next_clicked = True
                                    self.random_sleep(2, 4)
                                    break
                            except:
                                continue
                        
                        if not next_clicked:
                            self.logger.error("No se pudo hacer clic en 'Siguiente', terminando extracción")
                            break
                
                except Exception as e:
                    self.logger.error(f"Error al extraer post: {str(e)}")
                    # Intentar continuar con el siguiente post
                    try:
                        next_buttons = self.driver.find_elements(By.CSS_SELECTOR, "button[aria-label='Next']")
                        if next_buttons:
                            next_buttons[0].click()
                            self.random_sleep(2, 4)
                            continue
                    except:
                        break
            
            self.posts = posts_data
            self.logger.info(f"Extracción finalizada. Se obtuvieron {len(posts_data)} posts")
            return posts_data
            
        except Exception as e:
            self.logger.error(f"Error durante la extracción de posts: {str(e)}")
            # Guardar captura de pantalla para depuración
            try:
                self.driver.save_screenshot("error_extraction.png")
                self.logger.info("Se guardó captura de pantalla en error_extraction.png")
            except:
                pass
            return []
    
    def download_images(self, output_dir="data/images"):
        """Descarga las imágenes de los posts extraídos"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        self.logger.info(f"Descargando {len(self.posts)} imágenes en {output_dir}")
        
        for i, post in enumerate(self.posts):
            try:
                # Implementar la descarga de imágenes
                # Esto se completará en la siguiente fase
                pass
            except Exception as e:
                self.logger.error(f"Error al descargar imagen {i}: {str(e)}")
    
    def close(self):
        """Cierra el navegador"""
        self.driver.quit()
        self.logger.info("Navegador cerrado")
    
    def save_cookies(self):
        """Guarda las cookies de la sesión"""
        try:
            cookies = self.driver.get_cookies()
            with open('instagram_cookies.pkl', 'wb') as f:
                pickle.dump(cookies, f)
            self.logger.info("Cookies guardadas correctamente")
            return True
        except Exception as e:
            self.logger.error(f"Error al guardar cookies: {str(e)}")
            return False

    def load_cookies(self):
        """Carga cookies previamente guardadas"""
        try:
            if not os.path.exists('instagram_cookies.pkl'):
                self.logger.info("No hay cookies guardadas")
                return False
            
            with open('instagram_cookies.pkl', 'rb') as f:
                cookies = pickle.load(f)
            
            # Primero navegar a Instagram
            self.driver.get(self.base_url)
            self.random_sleep(2, 3)
            
            # Añadir las cookies
            for cookie in cookies:
                try:
                    self.driver.add_cookie(cookie)
                except:
                    pass
            
            # Recargar la página
            self.driver.refresh()
            self.random_sleep(3, 5)
            
            # Verificar si seguimos con la sesión iniciada
            try:
                # Buscar elementos que indicen sesión iniciada
                profile_elements = self.driver.find_elements(By.XPATH, 
                    "//div[contains(@class, 'xh8yej3')]//img[@alt]")
                if profile_elements:
                    self.logger.info("Sesión cargada exitosamente desde cookies")
                    return True
            except:
                pass
            
            self.logger.info("No se pudo restaurar la sesión desde cookies")
            return False
        except Exception as e:
            self.logger.error(f"Error al cargar cookies: {str(e)}")
            return False
    