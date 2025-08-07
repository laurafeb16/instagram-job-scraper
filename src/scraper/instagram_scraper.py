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
            
            chrome_driver_path = os.path.join(os.getcwd(), 'chromedriver.exe')
            self.driver = webdriver.Chrome(
                service=Service(chrome_driver_path),
                options=chrome_options
            )
            self.driver.set_window_size(1366, 768)
            self.wait = WebDriverWait(self.driver, 15)
            self.browser_crashed = False
            
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
        
        # Intentar cargar cookies primero
        if self.load_cookies():
            return True
        
        # Si no hay cookies o falló, hacer login normal
        try:
            self.logger.info("Iniciando sesión en Instagram")
            self.driver.get(self.base_url)
            self.random_sleep(3, 5)
            
            # Manejar posible pop-up de cookies
            self._close_popups()
            
            # Ingresar credenciales
            try:
                username_input = self.wait.until(
                    EC.presence_of_element_located((By.XPATH, "//input[@name='username']"))
                )
                password_input = self.wait.until(
                    EC.presence_of_element_located((By.XPATH, "//input[@name='password']"))
                )
                
                # Escribir credenciales de manera más natural
                self._type_naturally(username_input, self.username)
                self.random_sleep(0.5, 1)
                self._type_naturally(password_input, self.password)
                self.random_sleep(0.5, 1)
                
                # Hacer clic en el botón de login
                login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
                login_button.click()
                
                # Esperar a que se complete el login
                self.random_sleep(5, 8)
                
                # Manejar ventanas emergentes post-login
                self._close_popups()
                
                # Guardar cookies después de login exitoso
                self.save_cookies()
                self.logger.info("Login exitoso")
                return True
                
            except Exception as e:
                self.logger.error(f"Error al ingresar credenciales: {str(e)}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error durante el login: {str(e)}")
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

    def scrape_posts(self, limit=10):
        """Método principal MEJORADO que evita duplicados y mantiene orden"""
        try:
            self.logger.info(f"🚀 Iniciando extracción de {limit} posts (MÉTODO ANTI-DUPLICADOS)")
            
            if not self._is_browser_alive():
                if not self._reinitialize_browser():
                    return []
            
            posts_data = []
            
            # ESTRATEGIA NUEVA: Obtener URLs únicas considerando posts ya procesados
            all_available_urls = self._get_chronological_post_urls(limit * 3)
            
            if not all_available_urls:
                self.logger.error("No se pudieron obtener URLs de posts")
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
        """Obtiene URLs en orden cronológico (más nuevos primero) SIN duplicados"""
        try:
            if not self._is_browser_alive():
                if not self._reinitialize_browser():
                    return []
            
            self.logger.info("📥 Obteniendo URLs en orden cronológico...")
            
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
                # Obtener todos los enlaces visibles MANTENIENDO EL ORDEN
                post_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/p/']")
                
                current_count = len(ordered_urls)
                
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

    def _wait_for_post_load(self, timeout=10):
        """Espera a que el post se cargue completamente"""
        try:
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                # Verificar elementos esenciales
                if (self.driver.find_elements(By.TAG_NAME, "article") or 
                    self.driver.find_elements(By.CSS_SELECTOR, "div[role='dialog']")):
                    
                    # Verificar que hay una imagen
                    if self.driver.find_elements(By.CSS_SELECTOR, "img[src*='fbcdn.net']"):
                        return True
                
                time.sleep(0.5)
            
            return False
            
        except Exception as e:
            self.logger.debug(f"Error esperando carga del post: {str(e)}")
            return False

    def _extract_post_data_improved(self):
        """Extractor de datos mejorado y más robusto"""
        try:
            # Obtener URL actual
            post_url = self.driver.current_url
            
            # Extraer imagen principal
            img_url = self._extract_image_improved()
            if not img_url:
                self.logger.warning("No se pudo extraer imagen")
                return None
            
            # Extraer descripción
            description = self._extract_description_improved()
            
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
            self.logger.error(f"Error extrayendo datos del post: {str(e)}")
            return None

    def _extract_image_improved(self):
        """Extractor de imagen mejorado con mejor manejo de errores"""
        try:
            # Lista de selectores actualizados y ordenados por prioridad
            selectors = [
                "article img[src*='fbcdn.net']",
                "div[role='dialog'] img[src*='fbcdn.net']",
                "img[style*='object-fit'][src*='fbcdn.net']",
                "img[decoding='auto'][src*='fbcdn.net']",
                "div._aagv img[src*='fbcdn.net']",
                "img[sizes][src*='fbcdn.net']",
                "img[alt]:not([alt=''])[src*='fbcdn.net']",
            ]
            
            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        img_url = element.get_attribute("src")
                        if (img_url and 
                            img_url.startswith('http') and 
                            'fbcdn.net' in img_url and
                            not 'profile' in img_url.lower() and
                            not 'avatar' in img_url.lower()):
                            
                            self.logger.debug(f"✅ Imagen extraída con: {selector}")
                            return img_url
                except Exception:
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
                        self.logger.debug("✅ Imagen extraída con método alternativo")
                        return src
            except:
                pass
                
            self.logger.warning("⚠️ No se pudo extraer URL de imagen")
            return ""
            
        except Exception as e:
            self.logger.error(f"❌ Error extrayendo imagen: {str(e)}")
            return ""

    def _extract_description_improved(self):
        """Extractor de descripción mejorado"""
        try:
            # Selectores actualizados para descripción
            selectors = [
                "article div[data-testid='post-caption'] span",
                "div[role='dialog'] div[class*='_a9zs'] span",
                "article div[class*='_a9zs'] span",
                "span._ap3a._aaco._aacu._aacx._aad7._aade",
                "div[class*='x1lliihq'] span",
                "article h1 + div",
                "ul li div span[dir='auto']"
            ]
            
            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        text = element.text.strip()
                        if text and len(text) > 5:
                            self.logger.debug(f"✅ Descripción extraída con: {selector}")
                            return text[:2000]
                except Exception:
                    continue
            
            # Método alternativo: buscar en todo el artículo
            try:
                article = self.driver.find_element(By.TAG_NAME, "article")
                if article:
                    text = article.text.strip()
                    if text and len(text) > 20:
                        lines = text.split('\n')
                        for line in lines:
                            if (len(line) > 20 and 
                                not line.isdigit() and 
                                'ago' not in line.lower() and
                                'like' not in line.lower()):
                                self.logger.debug("✅ Descripción extraída del artículo")
                                return line[:2000]
            except:
                pass
                
            self.logger.debug("ℹ️ No se encontró descripción")
            return ""
            
        except Exception as e:
            self.logger.error(f"❌ Error extrayendo descripción: {str(e)}")
            return ""

    def _extract_date_improved(self):
        """Extrae la fecha del post de manera mejorada"""
        try:
            # Buscar elementos de tiempo
            time_elements = self.driver.find_elements(By.CSS_SELECTOR, "time")
            for time_elem in time_elements:
                datetime_attr = time_elem.get_attribute("datetime")
                if datetime_attr:
                    return datetime_attr
            
            # Método alternativo: buscar por texto de fecha
            date_patterns = [
                r'(\d+)\s+(second|minute|hour|day|week|month|year)s?\s+ago',
                r'hace\s+(\d+)\s+(segundo|minuto|hora|día|semana|mes|año)s?'
            ]
            
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            for pattern in date_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    return datetime.now().isoformat()
            
        except Exception as e:
            self.logger.debug(f"Error extrayendo fecha: {str(e)}")
        
        return datetime.now().isoformat()

    def _detect_carousel_safely(self):
        """Detecta carruseles sin navegar por ellos"""
        try:
            carousel_indicators = [
                "div[role='tablist'] button",
                "span[aria-label*='1 of']:not([aria-label='1 of 1'])",
                "button[aria-label='Next'][aria-disabled='false']",
            ]
            
            for selector in carousel_indicators:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    for element in elements:
                        if element.is_displayed():
                            if 'of' in selector:
                                label = element.get_attribute('aria-label') or ''
                                if 'of' in label and not label.endswith('of 1'):
                                    self.logger.debug(f"Carrusel detectado: {label}")
                                    return True
                            else:
                                self.logger.debug(f"Carrusel detectado con: {selector}")
                                return True
            
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
        """Cierra popups de manera más eficiente"""
        try:
            popup_selectors = [
                "button[aria-label='Close']",
                "div[role='dialog'] button:first-child",
                "svg[aria-label='Close']",
            ]
            
            text_selectors = [
                "Not Now", "Ahora no", "Accept", "Aceptar", "Allow", "Later"
            ]
            
            # Intentar selectores CSS primero
            for selector in popup_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements and elements[0].is_displayed():
                        elements[0].click()
                        self.logger.debug(f"Popup cerrado: {selector}")
                        self.random_sleep(0.5, 1)
                        return True
                except:
                    continue
            
            # Intentar selectores con texto
            for text in text_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, f"//button[contains(text(), '{text}')]")
                    if elements and elements[0].is_displayed():
                        elements[0].click()
                        self.logger.debug(f"Popup cerrado: {text}")
                        self.random_sleep(0.5, 1)
                        return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            self.logger.debug(f"Error cerrando popups: {str(e)}")
            return False

    def _save_debug_screenshot(self, filename_prefix):
        """Guarda captura de pantalla para debugging"""
        try:
            if self._is_browser_alive():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"debug_{filename_prefix}_{timestamp}.png"
                self.driver.save_screenshot(filename)
                self.logger.info(f"📸 Captura guardada: {filename}")
        except Exception as e:
            self.logger.error(f"Error guardando captura: {str(e)}")

    # Métodos de compatibilidad
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
        """Carga cookies previamente guardadas"""
        try:
            if not os.path.exists('instagram_cookies.pkl'):
                self.logger.info("No hay cookies guardadas")
                return False
            
            if not self._is_browser_alive():
                return False
            
            with open('instagram_cookies.pkl', 'rb') as f:
                cookies = pickle.load(f)
            
            # Navegar a Instagram primero
            self.driver.get(self.base_url)
            self.random_sleep(2, 3)
            
            # Añadir cookies
            for cookie in cookies:
                try:
                    self.driver.add_cookie(cookie)
                except:
                    pass
            
            # Recargar la página
            self.driver.refresh()
            self.random_sleep(3, 5)
            
            # Verificar si la sesión está activa
            try:
                if (self.driver.find_elements(By.CSS_SELECTOR, "svg[aria-label='Home']") or
                    self.driver.find_elements(By.XPATH, "//div[contains(@class, 'xh8yej3')]//img[@alt]")):
                    self.logger.info("🍪 Sesión cargada exitosamente desde cookies")
                    return True
            except:
                pass
            
            self.logger.info("No se pudo restaurar la sesión desde cookies")
            return False
            
        except Exception as e:
            self.logger.error(f"Error cargando cookies: {str(e)}")
            return False

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

    # Métodos legacy para compatibilidad
    def download_images(self, output_dir="data/images"):
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        self.logger.info(f"Descargando {len(self.posts)} imágenes en {output_dir}")
        
        for i, post in enumerate(self.posts):
            try:
                pass  # Implementar descarga si es necesario
            except Exception as e:
                self.logger.error(f"Error al descargar imagen {i}: {str(e)}")
