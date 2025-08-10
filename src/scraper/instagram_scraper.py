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
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import logging
import pickle
import re

class InstagramScraper:
    def __init__(self, username, password, target_account, headless=False):
        self.username = username
        self.password = password
        self.target_account = target_account
        self.base_url = "https://www.instagram.com/"
        self.posts = []
        
        # Control mejorado de navegación y duplicados
        self.processed_urls = set()  # URLs ya procesadas GLOBALMENTE
        self.session_posts = []      # Posts de la sesión actual
        self.failed_navigation_count = 0
        self.max_failed_navigations = 2
        self.browser_crashed = False
        
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
        
        # Configurar opciones de Chrome más robustas
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-popup-blocking")
        
        # Argumentos adicionales para estabilidad
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        chrome_options.add_argument("--no-first-run")
        chrome_options.add_argument("--disable-extensions")
        
        # User agent actualizado para 2025
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")
        
        # Usar ChromeDriver local
        chrome_driver_path = os.path.join(os.getcwd(), 'chromedriver.exe')
        self.logger.info(f"Buscando ChromeDriver en: {chrome_driver_path}")
        
        # Inicializar el driver con manejo de errores
        try:
            self.driver = webdriver.Chrome(
                service=Service(chrome_driver_path),
                options=chrome_options
            )
            self.driver.set_window_size(1366, 768)
            self.wait = WebDriverWait(self.driver, 15)
            self.browser_crashed = False
            
            # Ejecutar script anti-detección
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
        except Exception as e:
            self.logger.error(f"Error inicializando driver: {e}")
            self.browser_crashed = True
            raise

    def random_sleep(self, min_seconds=1, max_seconds=3):
        """Espera un tiempo aleatorio para simular comportamiento humano"""
        time.sleep(random.uniform(min_seconds, max_seconds))

    def _is_browser_alive(self):
        """Verifica si el navegador sigue activo"""
        try:
            if self.browser_crashed:
                return False
            self.driver.current_url
            return True
        except Exception:
            self.browser_crashed = True
            return False

    def _reinitialize_browser(self):
        """Reinicializa el navegador si se crashea"""
        try:
            self.logger.warning("🔄 Reinicializando navegador...")
            
            # Cerrar navegador anterior si existe
            try:
                if hasattr(self, 'driver'):
                    self.driver.quit()
            except:
                pass
            
            # Reinicializar
            chrome_options = Options()
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")
            
            chrome_driver_path = os.path.join(os.getcwd(), 'chromedriver.exe')
            self.driver = webdriver.Chrome(
                service=Service(chrome_driver_path),
                options=chrome_options
            )
            self.driver.set_window_size(1366, 768)
            self.wait = WebDriverWait(self.driver, 15)
            self.browser_crashed = False
            
            # Ejecutar script anti-detección
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Recargar cookies si existen
            self.load_cookies()
            
            self.logger.info("✅ Navegador reinicializado exitosamente")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error reinicializando navegador: {e}")
            self.browser_crashed = True
            return False

    def login(self):
        """Inicia sesión en Instagram o carga sesión guardada"""
        if not self._is_browser_alive():
            if not self._reinitialize_browser():
                return False
        
        self.logger.info("🔐 Iniciando proceso de login...")
        
        # Intentar cargar cookies primero
        cookies_loaded = self.load_cookies()
        if cookies_loaded:
            self.logger.info("✅ Login completado usando cookies guardadas")
            return True
        
        # Si no hay cookies o falló, hacer login normal
        try:
            self.logger.info("📝 Realizando login manual en Instagram")
            self.driver.get(self.base_url)
            self.random_sleep(3, 5)
            
            # Manejar posible pop-up de cookies
            self._close_popups()
            
            # Ingresar credenciales - selectores actualizados para 2025
            try:
                # Esperar a que aparezca el formulario de login
                username_input = self.wait.until(
                    EC.presence_of_element_located((By.XPATH, "//input[@name='username' or @aria-label='Teléfono, usuario o correo electrónico' or @aria-label='Phone number, username, or email']"))
                )
                password_input = self.wait.until(
                    EC.presence_of_element_located((By.XPATH, "//input[@name='password' or @aria-label='Contraseña' or @aria-label='Password']"))
                )
                
                # Escribir credenciales de manera más natural
                self._type_naturally(username_input, self.username)
                self.random_sleep(0.5, 1.5)
                self._type_naturally(password_input, self.password)
                self.random_sleep(0.5, 1.5)
                
                # Hacer clic en el botón de login - selectores actualizados
                login_button = self.driver.find_element(By.XPATH, "//button[@type='submit' or contains(., 'Iniciar sesión') or contains(., 'Log in') or div[contains(text(), 'Iniciar sesión')] or div[contains(text(), 'Log in')]]")
                login_button.click()
                
                # Esperar a que se complete el login
                self.random_sleep(5, 8)
                
                # Verificar si el login fue exitoso
                if self._verify_login_success():
                    # Manejar ventanas emergentes post-login
                    self._close_popups()
                    
                    # Guardar cookies después de login exitoso
                    self.save_cookies()
                    self.logger.info("✅ Login exitoso")
                    return True
                else:
                    self.logger.error("❌ Login falló - verificación no exitosa")
                    return False
                
            except Exception as e:
                self.logger.error(f"❌ Error al ingresar credenciales: {str(e)}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error durante el login: {str(e)}")
            return False

    def _verify_login_success(self):
        """Verifica si el login fue exitoso"""
        try:
            # Esperar un poco para que la página cargue
            self.random_sleep(2, 3)
            
            # Buscar indicadores de que estamos logueados
            success_indicators = [
                "//nav//a[@aria-label='Inicio' or @aria-label='Home']",
                "//nav//svg[@aria-label='Inicio' or @aria-label='Home']",
                "//a[contains(@href, '/direct/')]",  # Direct messages
                "//div[@role='menubar']",  # Barra de navegación
                "//img[@alt and contains(@src, 'fbcdn')]"  # Avatar de usuario
            ]
            
            for indicator in success_indicators:
                try:
                    elements = self.driver.find_elements(By.XPATH, indicator)
                    if elements:
                        self.logger.debug(f"✅ Login verificado con: {indicator}")
                        return True
                except:
                    continue
            
            # También verificar que NO estemos en la página de login
            current_url = self.driver.current_url
            if '/accounts/login' not in current_url and '/login' not in current_url:
                self.logger.debug("✅ Login verificado por URL")
                return True
            
            return False
            
        except Exception as e:
            self.logger.debug(f"Error verificando login: {str(e)}")
            return False

    def _type_naturally(self, element, text):
        """Escribe texto de manera más natural"""
        element.clear()
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))

    def navigate_to_target_account(self):
        """Navega a la cuenta objetivo"""
        if not self._is_browser_alive():
            if not self._reinitialize_browser():
                return False
        
        try:
            self.logger.info(f"🔍 Navegando a la cuenta: {self.target_account}")
            self.driver.get(f"{self.base_url}{self.target_account}/")
            self.random_sleep(3, 5)
            
            # Verificar si la cuenta existe
            if "Esta página no está disponible" in self.driver.page_source or "Page not found" in self.driver.page_source:
                self.logger.error(f"❌ La cuenta {self.target_account} no existe o no está disponible")
                return False
                
            return True
        except Exception as e:
            self.logger.error(f"❌ Error al navegar a la cuenta objetivo: {str(e)}")
            return False

    def scrape_posts(self, limit=10):
        """Método principal MEJORADO que evita duplicados y mantiene orden"""
        try:
            self.logger.info(f"🚀 Iniciando extracción de {limit} posts con selectores actualizados 2025")
            
            if not self._is_browser_alive():
                if not self._reinitialize_browser():
                    return []
            
            posts_data = []
            
            # ESTRATEGIA NUEVA: Obtener URLs únicas considerando posts ya procesados
            all_available_urls = self._get_chronological_post_urls(limit * 3)
            
            if not all_available_urls:
                self.logger.error("❌ No se pudieron obtener URLs de posts")
                return []
            
            # Filtrar URLs ya procesadas en sesiones anteriores
            new_urls = []
            for url in all_available_urls:
                clean_url = url.split('?')[0]  # Limpiar parámetros
                if clean_url not in self.processed_urls:
                    new_urls.append(url)
                    if len(new_urls) >= limit:
                        break
            
            if not new_urls:
                self.logger.warning("⚠️ Todas las URLs disponibles ya fueron procesadas")
                return []
            
            self.logger.info(f"📋 URLs únicas para procesar: {len(new_urls)}")
            self.logger.info(f"📊 URLs ya procesadas anteriormente: {len(self.processed_urls)}")
            
            # Procesar posts de uno en uno con mejor manejo de errores
            for i, post_url in enumerate(new_urls):
                try:
                    if not self._is_browser_alive():
                        self.logger.warning("🔄 Navegador cerrado, reinicializando...")
                        if not self._reinitialize_browser():
                            break
                    
                    post_id = self._extract_post_id(post_url)
                    self.logger.info(f"🔍 Procesando post {i+1}/{len(new_urls)}: {post_id}")
                    
                    # Marcar como procesado ANTES de intentar extraer
                    clean_url = post_url.split('?')[0]
                    self.processed_urls.add(clean_url)
                    
                    # Navegar al post con retry
                    success = False
                    for attempt in range(2):
                        try:
                            self.driver.get(post_url)
                            self.random_sleep(2, 4)
                            
                            if self._wait_for_post_load():
                                success = True
                                break
                            else:
                                self.logger.warning(f"⚠️ Intento {attempt + 1}: Post no cargó")
                        except Exception as e:
                            self.logger.warning(f"⚠️ Intento {attempt + 1} falló: {str(e)}")
                            if not self._is_browser_alive():
                                if not self._reinitialize_browser():
                                    break
                    
                    if not success:
                        self.logger.warning(f"⚠️ No se pudo cargar post: {post_url}")
                        continue
                    
                    # Cerrar popups
                    self._close_popups()
                    
                    # Extraer datos
                    post_data = self._extract_post_data_improved()
                    
                    if post_data and post_data.get('image_url'):
                        posts_data.append(post_data)
                        self.session_posts.append(post_data)
                        self.logger.info(f"✅ Post {i+1} extraído: {post_id}")
                    else:
                        self.logger.warning(f"⚠️ No se extrajeron datos válidos: {post_url}")
                    
                    # Pausa entre posts
                    if i < len(new_urls) - 1:
                        self.random_sleep(2, 4)
                
                except Exception as e:
                    self.logger.error(f"❌ Error procesando {post_url}: {str(e)}")
                    continue
            
            self.posts = posts_data
            self.logger.info(f"🎉 Extracción completada: {len(posts_data)} posts únicos extraídos")
            self.logger.info(f"📊 Total procesados en la sesión: {len(self.processed_urls)}")
            
            return posts_data
            
        except Exception as e:
            self.logger.error(f"❌ Error crítico: {str(e)}")
            self._save_debug_screenshot("critical_error")
            return []

    def _get_chronological_post_urls(self, target_count=30):
        """Obtiene URLs en orden cronológico (más nuevos primero) SIN duplicados - Actualizado 2025"""
        try:
            if not self._is_browser_alive():
                if not self._reinitialize_browser():
                    return []
            
            self.logger.info("📥 Obteniendo URLs en orden cronológico con selectores 2025...")
            
            # Navegar al perfil
            self.driver.get(f"{self.base_url}{self.target_account}/")
            self.random_sleep(3, 5)
            
            # Lista para mantener orden cronológico
            ordered_urls = []
            seen_urls = set()
            scroll_attempts = 0
            max_scrolls = 8
            no_new_content_count = 0
            
            while len(ordered_urls) < target_count and scroll_attempts < max_scrolls:
                # Selectores actualizados para Instagram 2025
                post_selectors = [
                    "a[href*='/p/']",  # Selector básico
                    "article a[href*='/p/']",  # Dentro de artículos
                    "div[role='tablist'] ~ div a[href*='/p/']",  # Posts en grid
                    "main a[href*='/p/']",  # Dentro del main
                ]
                
                current_count = len(ordered_urls)
                
                # Intentar todos los selectores
                for selector in post_selectors:
                    try:
                        post_links = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        
                        # Procesar enlaces en orden (Instagram los muestra cronológicamente)
                        for link in post_links:
                            try:
                                href = link.get_attribute('href')
                                if href and '/p/' in href:
                                    clean_href = href.split('?')[0]  # Limpiar parámetros
                                    if clean_href not in seen_urls:
                                        seen_urls.add(clean_href)
                                        ordered_urls.append(href)  # Mantener URL original con parámetros
                                        
                                        if len(ordered_urls) >= target_count:
                                            break
                            except:
                                continue
                        
                        if len(ordered_urls) >= target_count:
                            break
                            
                    except Exception as e:
                        self.logger.debug(f"Error con selector {selector}: {str(e)}")
                        continue
                
                new_found = len(ordered_urls) - current_count
                
                if new_found > 0:
                    self.logger.info(f"📋 Encontradas {new_found} URLs nuevas. Total: {len(ordered_urls)}")
                    no_new_content_count = 0
                else:
                    no_new_content_count += 1
                    self.logger.debug(f"Sin contenido nuevo en scroll {scroll_attempts + 1}")
                
                # Si no hay contenido nuevo por 3 scrolls consecutivos, parar
                if no_new_content_count >= 3:
                    self.logger.info("No se encuentra más contenido nuevo")
                    break
                
                # Scroll para cargar más posts
                if len(ordered_urls) < target_count:
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    self.random_sleep(2, 3)
                    scroll_attempts += 1
            
            self.logger.info(f"✅ URLs cronológicas obtenidas: {len(ordered_urls)}")
            
            # Log de URLs para debugging
            if ordered_urls:
                self.logger.debug("📋 Primeras 5 URLs:")
                for i, url in enumerate(ordered_urls[:5]):
                    post_id = self._extract_post_id(url)
                    self.logger.debug(f"  {i+1}. {post_id}")
            
            return ordered_urls
            
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo URLs cronológicas: {str(e)}")
            return []

    def _wait_for_post_load(self, timeout=15):
        """Espera a que el post se cargue completamente - Actualizado para Instagram 2025"""
        try:
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                # Verificar múltiples indicadores de carga
                
                # 1. Verificar que hay contenido principal
                main_content_found = False
                main_selectors = [
                    "main[role='main']",
                    "article",
                    "div[role='main']",
                    "section",
                ]
                
                for selector in main_selectors:
                    if self.driver.find_elements(By.CSS_SELECTOR, selector):
                        main_content_found = True
                        break
                
                # 2. Verificar que hay imágenes cargadas
                images_found = False
                image_selectors = [
                    "img[src*='fbcdn.net']",
                    "img[src*='instagram']",
                    "img[decoding='auto']",
                    "img[style*='object-fit']",
                ]
                
                for selector in image_selectors:
                    images = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if images:
                        # Verificar que al menos una imagen está realmente cargada
                        for img in images:
                            if img.get_attribute('complete') == 'true' or img.size['height'] > 50:
                                images_found = True
                                break
                        if images_found:
                            break
                
                # 3. Verificar que no estamos en una página de error
                error_indicators = [
                    "Esta página no está disponible",
                    "Page not found",
                    "Sorry, this page isn't available",
                    "Lo sentimos, esta página no está disponible"
                ]
                
                is_error = False
                page_text = self.driver.find_element(By.TAG_NAME, "body").text
                for error_text in error_indicators:
                    if error_text in page_text:
                        is_error = True
                        break
                
                if is_error:
                    self.logger.warning("⚠️ Página de error detectada")
                    return False
                
                # Si tenemos contenido principal E imágenes, considerarlo cargado
                if main_content_found and images_found:
                    self.logger.debug("✅ Post cargado exitosamente")
                    return True
                
                # Log de debugging cada 3 segundos
                if int(time.time() - start_time) % 3 == 0:
                    self.logger.debug(f"⏳ Esperando carga... Main: {main_content_found}, Images: {images_found}")
                
                time.sleep(0.5)
        
            self.logger.warning(f"⚠️ Timeout esperando carga del post")
            return False
            
        except Exception as e:
             self.logger.debug(f"Error esperando carga del post: {str(e)}")
             return False

    def _extract_post_data_improved(self):
        """Extractor de datos mejorado para Instagram 2025"""
        try:
            # Obtener URL actual
            post_url = self.driver.current_url
            
            # Debug de estructura (solo en modo debug)
            self._debug_current_page()
        
            # Extraer imagen principal
            img_url = self._extract_image_improved()
            if not img_url:
                self.logger.warning("⚠️ No se pudo extraer imagen")
                return None
            
            # Extraer descripción con método mejorado
            description = self._extract_description_improved()
            
            # Log detallado de la descripción extraída
            if description:
                self.logger.info(f"📝 Descripción extraída exitosamente: {len(description)} caracteres")
                self.logger.debug(f"Primeros 200 chars: {description[:200]}...")
            else:
                self.logger.warning("⚠️ No se extrajo descripción del post")
            
            # Extraer fecha
            post_date = self._extract_date_improved()
            
            # Verificar si es carrusel (pero NO navegar por él)
            is_carousel = self._detect_carousel_safely()
            
            # Construir datos del post
            post_data = {
                "url": post_url,
                "image_url": img_url,
                "description": description or "",
                "date": post_date or datetime.now().isoformat(),
                "scraped_at": datetime.now().isoformat(),
                "is_carousel": is_carousel,
                "carousel_images": [img_url] if is_carousel else [],
                "post_id": self._extract_post_id(post_url)
            }
            
            return post_data
            
        except Exception as e:
            self.logger.error(f"❌ Error extrayendo datos del post: {str(e)}")
            return None

    def _extract_image_improved(self):
        """Extractor de imagen mejorado para Instagram 2025"""
        try:
            # Lista de selectores actualizados para Instagram 2025
            selectors = [
                # Selectores más específicos primero
                "article img[src*='fbcdn.net']:not([src*='profile']):not([src*='avatar'])",
                "main img[src*='fbcdn.net']:not([src*='profile']):not([src*='avatar'])",
                "div[role='dialog'] img[src*='fbcdn.net']:not([src*='profile']):not([src*='avatar'])",
                
                # Selectores por estructura
                "img[style*='object-fit'][src*='fbcdn.net']",
                "img[decoding='auto'][src*='fbcdn.net']",
                "img[loading='lazy'][src*='fbcdn.net']",
                
                # Selectores más genéricos
                "img[sizes][src*='fbcdn.net']",
                "img[alt]:not([alt=''])[src*='fbcdn.net']",
            ]
            
            for i, selector in enumerate(selectors):
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    self.logger.debug(f"Selector {i+1}: '{selector}' → {len(elements)} elementos")
                    
                    for element in elements:
                        img_url = element.get_attribute("src")
                        if (img_url and 
                            img_url.startswith('http') and 
                            'fbcdn.net' in img_url and
                            not 'profile' in img_url.lower() and
                            not 'avatar' in img_url.lower() and
                            not 'icon' in img_url.lower()):
                            
                            # Verificar que la imagen tenga dimensiones válidas
                            try:
                                width = element.size.get('width', 0)
                                height = element.size.get('height', 0)
                                if width > 50 and height > 50:  # Imagen de tamaño válido
                                    self.logger.debug(f"✅ Imagen extraída con: {selector} ({width}x{height})")
                                    return img_url
                            except:
                                # Si no podemos obtener dimensiones, aceptar la imagen
                                self.logger.debug(f"✅ Imagen extraída con: {selector}")
                                return img_url
                except Exception as e:
                    self.logger.debug(f"Error con selector {i+1}: {str(e)}")
                    continue
            
            # Método alternativo: buscar cualquier imagen válida
            try:
                all_images = self.driver.find_elements(By.TAG_NAME, "img")
                for img in all_images:
                    src = img.get_attribute("src")
                    if (src and 
                        'fbcdn.net' in src and 
                        not 'profile' in src.lower() and
                        not 'avatar' in src.lower() and
                        not 'icon' in src.lower()):
                        
                        # Verificar dimensiones
                        try:
                            width = img.size.get('width', 0)
                            height = img.size.get('height', 0)
                            if width > 100 and height > 100:
                                self.logger.debug("✅ Imagen extraída con método alternativo")
                                return src
                        except:
                            pass
            except:
                pass
                
            self.logger.warning("⚠️ No se pudo extraer URL de imagen")
            return ""
            
        except Exception as e:
            self.logger.error(f"❌ Error extrayendo imagen: {str(e)}")
            return ""

    def _extract_description_improved(self):
        """🔧 EXTRACTOR DE DESCRIPCIÓN ULTRA MEJORADO - VERSIÓN 2025 ULTRA ROBUSTA"""
        try:
            self.logger.info("🔍 Iniciando extracción ULTRA ROBUSTA de descripción...")
            
            # === GUARDAR SCREENSHOT Y HTML PARA DEBUG ===
            self._save_debug_screenshot("description_extraction")
            self._save_debug_html("description_extraction")
            
            # === ESTRATEGIA #0: BUSCAR EN TITLE DE LA PÁGINA ===
            try:
                page_title = self.driver.title
                if page_title and len(page_title) > 30 and self._is_job_related_description(page_title):
                    self.logger.info(f"✅ DESCRIPCIÓN EXTRAÍDA del title ({len(page_title)} chars)")
                    return page_title
            except:
                pass
            
            # === ESTRATEGIA #1: META TAGS (MÁS CONFIABLE) ===
            self.logger.debug("🎯 Estrategia #1: Meta tags...")
            
            meta_selectors = [
                "meta[property='og:description']",
                "meta[name='description']", 
                "meta[property='description']",
                "meta[name='twitter:description']",
                "meta[property='og:title']"
            ]
            
            for selector in meta_selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    content = element.get_attribute('content')
                    
                    if content and len(content) > 30:
                        self.logger.debug(f"Meta encontrado: {selector} - {len(content)} chars")
                        cleaned_content = self._clean_meta_description(content)
                        
                        if cleaned_content and len(cleaned_content) > 20:
                            self.logger.info(f"✅ DESCRIPCIÓN de meta tag ({len(cleaned_content)} chars)")
                            return cleaned_content
                            
                except Exception as e:
                    self.logger.debug(f"Error con {selector}: {str(e)}")
                    continue
            
            # === ESTRATEGIA #2: SELECTORES UNIVERSALES BÁSICOS ===
            self.logger.debug("🎯 Estrategia #2: Selectores universales...")
            
            universal_selectors = [
                # Intentar el más básico primero
                "article",
                "main", 
                "[role='main']",
                "[role='article']",
                "section",
                "div[id*='content']",
                "div[class*='content']"
            ]
            
            for selector in universal_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        text = element.text.strip()
                        if text and len(text) > 100:
                            self.logger.debug(f"Texto de {selector}: {len(text)} chars")
                            
                            # Buscar descripción inteligente en el texto
                            smart_desc = self._extract_smart_description(text)
                            if smart_desc:
                                self.logger.info(f"✅ DESCRIPCIÓN de {selector} ({len(smart_desc)} chars)")
                                return smart_desc
                                
                except Exception as e:
                    self.logger.debug(f"Error con {selector}: {str(e)}")
                    continue
            
            # === ESTRATEGIA #3: TEXTO COMPLETO DE LA PÁGINA ===
            self.logger.debug("🎯 Estrategia #3: Texto completo...")
            
            try:
                full_page_text = self.driver.find_element(By.TAG_NAME, "body").text
                
                if full_page_text and len(full_page_text) > 100:
                    self.logger.debug(f"Texto completo: {len(full_page_text)} chars")
                    
                    # Guardar texto completo para análisis manual
                    debug_filename = f"debug_full_text_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                    with open(debug_filename, 'w', encoding='utf-8') as f:
                        f.write(f"URL: {self.driver.current_url}\n")
                        f.write(f"TEXTO COMPLETO ({len(full_page_text)} chars):\n")
                        f.write("="*80 + "\n")
                        f.write(full_page_text)
                    
                    self.logger.debug(f"📝 Texto completo guardado en: {debug_filename}")
                    
                    # Buscar patrones de trabajo en texto completo
                    job_patterns = [
                        r'((?:Práctica|práctica)[^.]*?(?:Empresa|empresa)[^.]*?(?:Contacto|contacto)[^.]{50,500})',
                        r'((?:Empresa|empresa):[^.]*?(?:Contacto|contacto):[^.]{50,500})',
                        r'((?:GRUPO|Grupo|Compañía)[^.]*?(?:ofreciendo|oferta|solicita|busca)[^.]{50,500})',
                        r'([^.]{100,}(?:práctica|trabajo|empleo|vacante|oferta)[^.]{100,})',
                    ]
                    
                    for pattern in job_patterns:
                        matches = re.findall(pattern, full_page_text, re.IGNORECASE | re.DOTALL)
                        for match in matches:
                            cleaned = re.sub(r'\s+', ' ', match).strip()
                            if len(cleaned) > 100 and self._is_job_related_description(cleaned):
                                self.logger.info(f"✅ DESCRIPCIÓN por patrón regex ({len(cleaned)} chars)")
                                return cleaned
                                
            except Exception as e:
                self.logger.debug(f"Error con texto completo: {str(e)}")
            
            # === ESTRATEGIA #4: XPATH ULTRA AGRESIVO ===
            self.logger.debug("🎯 Estrategia #4: XPath ultra agresivo...")
            
            aggressive_xpaths = [
                # Buscar cualquier texto que contenga palabras clave
                "//text()[contains(., 'práctica') or contains(., 'Práctica')]/..",
                "//text()[contains(., 'empresa') or contains(., 'Empresa')]/..",  
                "//text()[contains(., 'contacto') or contains(., 'Contacto')]/..",
                "//text()[contains(., 'oportunidad')]/..",
                "//text()[contains(., 'trabajo')]/..",
                
                # Buscar por longitud de texto
                "//*[string-length(text()) > 100]",
                "//*[string-length(text()) > 50]",
            ]
            
            for xpath in aggressive_xpaths:
                try:
                    elements = self.driver.find_elements(By.XPATH, xpath)
                    self.logger.debug(f"XPath '{xpath[:30]}...' → {len(elements)} elementos")
                    
                    for element in elements:
                        try:
                            text = element.text.strip()
                            if text and len(text) > 50 and self._is_job_related_description(text):
                                smart_desc = self._extract_smart_description(text)
                                if smart_desc:
                                    self.logger.info(f"✅ DESCRIPCIÓN con XPath agresivo ({len(smart_desc)} chars)")
                                    return smart_desc
                        except:
                            continue
                except:
                    continue
            
            # === ESTRATEGIA #5: ÚLTIMO RECURSO - CUALQUIER TEXTO LARGO ===
            self.logger.debug("🎯 Estrategia #5: Último recurso...")
            
            try:
                all_elements = self.driver.find_elements(By.XPATH, "//*")
                text_candidates = []
                
                for element in all_elements:
                    try:
                        text = element.text.strip()
                        if text and 50 <= len(text) <= 2000:
                            text_candidates.append(text)
                    except:
                        continue
                
                # Ordenar por longitud y buscar el mejor
                text_candidates.sort(key=len, reverse=True)
                
                for text in text_candidates[:10]:  # Solo los 10 más largos
                    if self._is_job_related_description(text):
                        smart_desc = self._extract_smart_description(text)
                        if smart_desc:
                            self.logger.info(f"✅ DESCRIPCIÓN último recurso ({len(smart_desc)} chars)")
                            return smart_desc
                        
            except Exception as e:
                self.logger.debug(f"Error en último recurso: {str(e)}")
            
            self.logger.warning("❌ TODAS las estrategias fallaron - NO se extrajo descripción")
            return ""
            
        except Exception as e:
            self.logger.error(f"❌ Error crítico en extracción: {str(e)}")
            return ""

    def _save_debug_html(self, filename_prefix):  # ✅ CORREGIR INDENTACIÓN AQUÍ
        """Guarda HTML de la página para debugging"""
        try:
            if self._is_browser_alive():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"debug_{filename_prefix}_{timestamp}.html"
                html_content = self.driver.page_source
            
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"<!-- POST URL: {self.driver.current_url} -->\n")
                    f.write(f"<!-- TIMESTAMP: {timestamp} -->\n")
                    f.write(html_content)
            
                self.logger.debug(f"📄 HTML guardado: {filename}")
        except Exception as e:
            self.logger.debug(f"Error guardando HTML: {str(e)}")

    def _is_valid_meta_description(self, content):
        """Verifica si el contenido de meta description es válido"""
        try:
            if not content or len(content) < 20:
                return False
            
            # Excluir descripciones genéricas de Instagram
            generic_patterns = [
                r'^\d+\s+(likes?|me gusta)',
                r'^\d+\s+(comments?|comentarios)',
                r'^.*\s+en Instagram:?\s*$',
                r'^Instagram.*foto.*vídeo',
                r'Mira.*en Instagram',
            ]
            
            for pattern in generic_patterns:
                if re.match(pattern, content, re.IGNORECASE):
                    return False
            
            # Verificar que contenga contenido relacionado con trabajo
            return self._is_job_related_description(content)
            
        except:
            return False

    def _clean_meta_description(self, content):
        """Limpia la descripción extraída de meta tags - CORREGIDO PARA NO TRUNCAR EMAILS"""
        try:
            self.logger.debug(f"🧹 Limpiando meta description: {len(content)} chars")
            self.logger.debug(f"Contenido original: {content[:200]}...")
            
            # Patrones MEJORADOS que NO cortan emails
            instagram_stats_patterns = [
                # NUEVO: Buscar el patrón completo y extraer solo la parte después de las comillas
                r'^\d+\s+(?:likes?|me gusta),\s*\d+\s+(?:comments?|comentarios)\s*-\s*\w+\s+el\s+[^:]+:\s*"([^"]+)".*$',
                r'^\d+\s+(?:me gusta|likes?),\s*\d+\s+(?:comentarios?|comments?)\s*-\s*\w+\s+el\s+[^:]+:\s*"([^"]+)".*$',
                
                # Patrones de seguridad (solo si no hay comillas)
                r'^\d+\s+(?:likes?|me gusta)\s*,\s*\d+\s+(?:comments?|comentarios)\s*-.*?:\s*',
                r'^\w+\s+•\s+\d+\s+(?:publicaciones?|posts?)\s+en Instagram:\s*',
            ]
            
            original_content = content
            cleaned_content = content
            
            # PRIMERO: Intentar extraer contenido entre comillas (método más seguro)
            quote_patterns = [
                r'^\d+[^"]*"([^"]{50,})"',  # Buscar contenido largo entre comillas
                r'"([^"]{100,})"',          # Cualquier contenido largo entre comillas
            ]
            
            for pattern in quote_patterns:
                match = re.search(pattern, content, re.DOTALL)
                if match:
                    extracted = match.group(1).strip()
                    if self._is_job_related_description(extracted):
                        self.logger.debug(f"✅ Extraído de comillas: {len(extracted)} chars")
                        return extracted
            
            # SEGUNDO: Si no hay comillas, usar patrones de limpieza conservadores
            for pattern in instagram_stats_patterns:
                # Si el patrón tiene grupo de captura, usarlo
                if '(' in pattern and ')' in pattern:
                    match = re.search(pattern, cleaned_content, flags=re.IGNORECASE | re.DOTALL)
                    if match:
                        extracted = match.group(1).strip()
                        if len(extracted) > 20:
                            self.logger.debug(f"✅ Extraído con patrón de captura: {len(extracted)} chars")
                            return extracted
                else:
                    # Patrón de limpieza simple
                    new_content = re.sub(pattern, '', cleaned_content, flags=re.IGNORECASE)
                    if new_content != cleaned_content:
                        cleaned_content = new_content
                        break
            
            # Limpiar caracteres finales y espacios
            cleaned_content = re.sub(r'"\s*\.\s*$', '', cleaned_content)
            cleaned_content = re.sub(r'"$', '', cleaned_content)
            cleaned_content = re.sub(r'\s*\.\s*$', '', cleaned_content)
            cleaned_content = re.sub(r'\s+', ' ', cleaned_content).strip()
            
            # VALIDACIÓN FINAL: Si la limpieza redujo demasiado el contenido, usar método alternativo
            if len(cleaned_content) < len(original_content) * 0.3:  # Si perdió más del 70%
                self.logger.debug("⚠️ Limpieza demasiado agresiva, intentando método alternativo...")
                
                # Buscar la parte más larga que contenga palabras de trabajo
                parts = original_content.split(':', 1)  # Dividir en el primer ':'
                if len(parts) > 1 and self._is_job_related_description(parts[1]):
                    alternative = parts[1].strip().strip('"').strip()
                    if len(alternative) > 50:
                        self.logger.debug(f"✅ Método alternativo exitoso: {len(alternative)} chars")
                        return alternative
            
            self.logger.debug(f"📝 Limpieza completada: {len(original_content)} → {len(cleaned_content)} chars")
            return cleaned_content if cleaned_content else original_content
            
        except Exception as e:
            self.logger.debug(f"Error limpiando meta description: {str(e)}")
            return content

    def _is_job_related_description(self, text):
        """Verifica si el texto es una descripción relacionada con trabajo - Mejorado para 2025"""
        try:
            if not text or len(text) < 20:
                return False
            
            # Palabras clave de trabajo/ofertas laborales (expandidas)
            job_keywords = [
                'práctica', 'trabajo', 'empleo', 'vacante', 'oferta', 'empresa',
                'contacto', 'solicita', 'busca', 'requiere', 'oportunidad',
                'posición', 'puesto', 'cargo', 'reclutamiento', 'talento',
                'profesional', 'candidato', 'aplicar', 'enviar', 'curriculum',
                'cv', 'hoja de vida', 'perfil', 'laboral', 'experiencia',
                'requisitos', 'competencias', 'habilidades', 'conocimientos'
            ]
            
            # Filtros mejorados para excluir UI de Instagram
            ui_filters = [
                'like', 'share', 'comment', 'view', 'follow', 'followers',
                'following', 'posts', 'stories', 'reels', 'igtv',
                'ago', 'hace', 'hours', 'horas', 'minutes', 'minutos',
                'days', 'días', 'weeks', 'semanas', 'months', 'meses',
                'ver más', 'show more', 'load more', 'cargar más',
                'home', 'explore', 'activity', 'profile'
            ]
            
            text_lower = text.lower()
            
            # Filtros adicionales para contenido no relevante
            if any(pattern in text_lower for pattern in ['@', '#hashtag', 'instagram.com']):
                if not any(keyword in text_lower for keyword in job_keywords):
                    return False
            
            # Si contiene principalmente filtros de UI, rechazar
            ui_count = sum(1 for ui_word in ui_filters if ui_word in text_lower)
            if ui_count > 3:  # Si tiene más de 3 palabras de UI
                return False
            
            # Si contiene palabras clave de trabajo, aceptar
            job_count = sum(1 for job_word in job_keywords if job_word in text_lower)
            if job_count >= 1:  # Al menos una palabra clave de trabajo
                return True
            
            # Si es texto largo sin palabras de UI, podría ser descripción
            if len(text) > 100 and ui_count == 0:
                return True
                
            return False
            
        except:
            return False

    def _extract_smart_description(self, full_text):
        """Extrae descripción de manera inteligente del texto completo - Mejorado 2025"""
        try:
            lines = full_text.split('\n')
            self.logger.debug(f"🔍 Analizando {len(lines)} líneas de texto...")
            
            # Buscar líneas que contengan información de trabajo
            job_lines = []
            found_job_content = False
            stop_words = ['like', 'comment', 'share', 'ago', 'hace', 'view', 'follow']
            
            for i, line in enumerate(lines):
                line = line.strip()
                if not line or len(line) < 10:
                    continue
                
                # Si es una línea de trabajo, empezar a recopilar
                if self._is_job_related_description(line):
                    found_job_content = True
                    job_lines.append(line)
                    self.logger.debug(f"  ✅ Línea de trabajo detectada: {line[:50]}...")
                elif found_job_content and len(line) > 20:
                    # Continuar recopilando si ya encontramos contenido de trabajo
                    # y la línea no es obviamente UI
                    if not any(stop_word in line.lower() for stop_word in stop_words):
                        job_lines.append(line)
                        self.logger.debug(f"  ➕ Línea adicional agregada: {line[:50]}...")
                    else:
                        # Si encontramos UI, parar la recopilación
                        self.logger.debug(f"  🛑 Línea de UI detectada, parando: {line[:50]}...")
                        break
                        
            if job_lines:
                description = '\n'.join(job_lines)
                self.logger.debug(f"📝 Descripción inteligente construida: {len(description)} chars")
                return description
                
            return ""
            
        except Exception as e:
            self.logger.debug(f"Error en extracción inteligente: {str(e)}")
            return ""

    def _extract_date_improved(self):
        """Extrae la fecha del post de manera mejorada para Instagram 2025"""
        try:
            # Buscar elementos de tiempo con selectores actualizados
            time_selectors = [
                "time",
                "time[datetime]",
                "[datetime]",
                "span[title]",  # Instagram a veces pone fechas en titles
            ]
            
            for selector in time_selectors:
                try:
                    time_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for time_elem in time_elements:
                        # Intentar datetime attribute
                        datetime_attr = time_elem.get_attribute("datetime")
                        if datetime_attr:
                            return datetime_attr
                        
                        # Intentar title attribute
                        title_attr = time_elem.get_attribute("title")
                        if title_attr:
                            return title_attr
                            
                        # Intentar el texto del elemento
                        text = time_elem.text.strip()
                        if text and any(word in text.lower() for word in ['ago', 'hace', 'hour', 'day', 'week']):
                            return datetime.now().isoformat()
                except:
                    continue
            
            # Método alternativo: buscar por texto de fecha en el DOM
            try:
                page_text = self.driver.find_element(By.TAG_NAME, "body").text
                date_patterns = [
                    r'(\d+)\s+(second|minute|hour|day|week|month|year)s?\s+ago',
                    r'hace\s+(\d+)\s+(segundo|minuto|hora|día|semana|mes|año)s?'
                ]
                
                for pattern in date_patterns:
                    match = re.search(pattern, page_text, re.IGNORECASE)
                    if match:
                        return datetime.now().isoformat()
            except:
                pass
            
        except Exception as e:
            self.logger.debug(f"Error extrayendo fecha: {str(e)}")
        
        return datetime.now().isoformat()

    def _detect_carousel_safely(self):
        """Detecta carruseles sin navegar por ellos - Actualizado 2025"""
        try:
            # Selectores actualizados para detectar carruseles en Instagram 2025
            carousel_indicators = [
                # Indicadores de múltiples imágenes
                "div[role='tablist']",
                "button[aria-label*='Next']",
                "button[aria-label*='Siguiente']",
                
                # Indicadores de posición (ej: "1 of 3")
                "span[aria-label*='1 of']:not([aria-label='1 of 1'])",
                "span[aria-label*='1 de']:not([aria-label='1 de 1'])",
                
                # Puntos indicadores
                "div[style*='transform'] button[aria-label*='of']",
                
                # Controles de navegación
                "button[aria-disabled='false'][aria-label*='Next']",
                "button[aria-disabled='false'][aria-label*='Siguiente']",
            ]
            
            for selector in carousel_indicators:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed():
                            # Verificar indicadores de posición
                            if 'of' in selector or 'de' in selector:
                                label = element.get_attribute('aria-label') or ''
                                if ('of' in label and not label.endswith('of 1')) or ('de' in label and not label.endswith('de 1')):
                                    self.logger.debug(f"Carrusel detectado: {label}")
                                    return True
                            else:
                                self.logger.debug(f"Carrusel detectado con: {selector}")
                                return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            self.logger.debug(f"Error detectando carrusel: {str(e)}")
            return False

    def _extract_post_id(self, url):
        """Extrae el ID del post de una URL de manera robusta"""
        try:
            if not url:
                return ""
                
            # Limpiar la URL
            clean_url = url.split('?')[0].split('#')[0]
            
            # Patrón para extraer ID
            pattern = r'/p/([A-Za-z0-9_-]+)'
            match = re.search(pattern, clean_url)
            
            if match:
                return match.group(1)
            
            # Si no se encuentra patrón, devolver parte de la URL
            if '/p/' in clean_url:
                parts = clean_url.split('/p/')
                if len(parts) > 1:
                    return parts[1].split('/')[0]
            
            return clean_url.split('/')[-1] or "unknown"
            
        except Exception as e:
            self.logger.debug(f"Error extrayendo ID: {str(e)}")
            return "unknown"

    def _close_popups(self):
        """Cierra popups de manera más eficiente - Actualizado 2025"""
        try:
            # Selectores actualizados para popups de Instagram 2025
            popup_selectors = [
                "button[aria-label='Cerrar' or aria-label='Close']",
                "div[role='dialog'] button:first-child",
                "svg[aria-label='Cerrar' or aria-label='Close']",
                "button[aria-label='Dismiss' or aria-label='Descartar']",
            ]
            
            text_selectors = [
                "Not Now", "Ahora no", "Accept", "Aceptar", "Allow", "Permitir",
                "Later", "Más tarde", "Skip", "Omitir", "Continue", "Continuar"
            ]
            
            popups_closed = 0
            
            # Intentar selectores CSS primero
            for selector in popup_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed():
                            element.click()
                            self.logger.debug(f"Popup cerrado: {selector}")
                            self.random_sleep(0.5, 1)
                            popups_closed += 1
                            break
                except:
                    continue
            
            # Intentar selectores con texto
            for text in text_selectors:
                try:
                    # Buscar tanto en buttons como en divs clickeables
                    xpath_patterns = [
                        f"//button[contains(text(), '{text}')]",
                        f"//div[@role='button'][contains(text(), '{text}')]",
                        f"//span[contains(text(), '{text}')]/parent::button",
                    ]
                    
                    for xpath in xpath_patterns:
                        elements = self.driver.find_elements(By.XPATH, xpath)
                        for element in elements:
                            if element.is_displayed():
                                element.click()
                                self.logger.debug(f"Popup cerrado: {text}")
                                self.random_sleep(0.5, 1)
                                popups_closed += 1
                                break
                        if popups_closed > 0:
                            break
                except:
                    continue
            
            return popups_closed > 0
            
        except Exception as e:
            self.logger.debug(f"Error cerrando popups: {str(e)}")
            return False

    def _debug_current_page(self):
        """Debugging para analizar la página actual - Optimizado"""
        try:
            current_url = self.driver.current_url
            self.logger.debug(f"🔍 URL actual: {current_url}")
        
            # Verificar elementos básicos rápidamente
            quick_checks = {
                "Articles": "article",
                "Images": "img[src*='fbcdn']",
                "Main content": "main",
            }
        
            for name, selector in quick_checks.items():
                try:
                    count = len(self.driver.find_elements(By.CSS_SELECTOR, selector))
                    self.logger.debug(f"  📋 {name}: {count}")
                except:
                    self.logger.debug(f"  ❌ {name}: Error")
            
        except Exception as e:
            self.logger.debug(f"Error en debug rápido: {str(e)}")

    def _save_debug_screenshot(self, filename_prefix):
        """Guarda captura de pantalla para debugging"""
        try:
            if self._is_browser_alive():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"debug_{filename_prefix}_{timestamp}.png"
                self.driver.save_screenshot(filename)
                self.logger.debug(f"📸 Captura guardada: {filename}")
        except Exception as e:
            self.logger.debug(f"Error guardando captura: {str(e)}")

    # === MÉTODOS DE COOKIES ===

    def save_cookies(self):
        """Guarda las cookies de la sesión"""
        try:
            if self._is_browser_alive():
                cookies = self.driver.get_cookies()
                with open('instagram_cookies.pkl', 'wb') as f:
                    pickle.dump(cookies, f)
                self.logger.info("🍪 Cookies guardadas correctamente")
                return True
        except Exception as e:
            self.logger.error(f"Error guardando cookies: {str(e)}")
            return False

    def load_cookies(self):
        """Carga cookies previamente guardadas - Optimizado para 2025"""
        try:
            if not os.path.exists('instagram_cookies.pkl'):
                self.logger.info("📋 No hay cookies guardadas")
                return False
            
            if not self._is_browser_alive():
                self.logger.warning("Navegador no disponible para cargar cookies")
                return False
            
            self.logger.info("🍪 Cargando cookies guardadas...")
            
            with open('instagram_cookies.pkl', 'rb') as f:
                cookies = pickle.load(f)
            
            # Navegar a Instagram primero
            self.driver.get(self.base_url)
            self.random_sleep(2, 3)
            
            # Añadir cookies
            cookies_loaded = 0
            for cookie in cookies:
                try:
                    self.driver.add_cookie(cookie)
                    cookies_loaded += 1
                except:
                    continue
            
            self.logger.info(f"✅ {cookies_loaded} cookies aplicadas")
            
            # Recargar la página
            self.driver.refresh()
            self.random_sleep(3, 5)
            
            # Verificar si la sesión está activa
            if self._verify_login_success():
                self.logger.info("🎉 Sesión cargada exitosamente desde cookies")
                return True
            else:
                self.logger.info("❌ Cookies inválidas")
                try:
                    os.remove('instagram_cookies.pkl')
                except:
                    pass
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error cargando cookies: {str(e)}")
            return False

    # === MÉTODOS FINALES ===

    def close(self):
        """Cierra el navegador de manera segura"""
        try:
            if hasattr(self, 'driver') and not self.browser_crashed:
                self.driver.quit()
                self.logger.info("🔒 Navegador cerrado correctamente")
        except Exception as e:
            self.logger.error(f"Error cerrando navegador: {str(e)}")

    def get_stats(self):
        """Devuelve estadísticas de la extracción"""
        return {
            "posts_extracted": len(self.posts),
            "posts_in_session": len(self.session_posts),
            "total_processed": len(self.processed_urls),
            "failed_navigations": self.failed_navigation_count,
            "browser_crashed": self.browser_crashed
        }

    # === MÉTODOS DE COMPATIBILIDAD ===

    def _extract_post_data(self):
        return self._extract_post_data_improved()

    def _extract_image(self):
        return self._extract_image_improved()

    def _extract_description(self):
        return self._extract_description_improved()

    def _extract_date(self):
        return self._extract_date_improved()

    def _extract_carousel_images(self):
        is_carousel = self._detect_carousel_safely()
        if is_carousel:
            return True, [self._extract_image_improved()]
        return False, []

    def _is_carousel_post(self):
        return self._detect_carousel_safely()

    def scrape_posts_alternative(self, limit=10):
        return self.scrape_posts(limit)

    def download_images(self, output_dir="data/images"):
        """Método legacy de compatibilidad"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        self.logger.info(f"Descargando {len(self.posts)} imágenes en {output_dir}")
        # Implementar descarga si es necesario