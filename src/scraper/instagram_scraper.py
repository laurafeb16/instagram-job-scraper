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
        
        # === LOG TEMPORAL PARA DEBUGGING ===
        self.logger.info("🧪 [DEBUG] Método login() ejecutándose - VERSIÓN CORREGIDA")
        
        # Intentar cargar cookies primero
        self.logger.info("🧪 [DEBUG] A punto de llamar load_cookies()")
        cookies_loaded = self.load_cookies()
        self.logger.info(f"🧪 [DEBUG] load_cookies() retornó: {cookies_loaded}")
        
        if cookies_loaded:
            self.logger.info("✅ Login completado usando cookies guardadas")
            return True
        
        # Si no hay cookies o falló, hacer login normal
        self.logger.info("🧪 [DEBUG] Procediendo con login manual")
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
                # === SELECTORES ACTUALIZADOS PARA INSTAGRAM 2025 ===
            
                # 1. Verificar elementos principales (más genéricos)
                main_elements = [
                    "main[role='main']",  # Contenedor principal
                    "section",            # Secciones de contenido
                    "div[style*='flex']", # Divs con flex (común en IG)
                    "[data-testid]",      # Cualquier elemento con testid
                ]
            
                found_main = False
                for selector in main_elements:
                    if self.driver.find_elements(By.CSS_SELECTOR, selector):
                        found_main = True
                        self.logger.debug(f"✅ Elemento principal encontrado: {selector}")
                        break
            
                # 2. Verificar que hay imágenes (más flexible)
                image_selectors = [
                    "img[src*='fbcdn.net']",
                    "img[src*='instagram']",
                    "img[decoding='auto']",
                    "img[loading='lazy']",
                    "img[style*='object-fit']",
                ]
            
                found_image = False
                for selector in image_selectors:
                    images = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if images:
                        found_image = True
                        self.logger.debug(f"✅ Imagen encontrada: {selector} ({len(images)} imágenes)")
                        break
            
                # 3. Si encontramos contenido principal E imágenes, considerarlo cargado
                if found_main and found_image:
                    self.logger.debug("✅ Post cargado exitosamente")
                    return True
            
                # Log de debugging
                self.logger.debug(f"⏳ Esperando carga... Main: {found_main}, Images: {found_image}")
                time.sleep(0.5)
        
            self.logger.warning(f"⚠️ Timeout esperando carga del post")
            return False
            
        except Exception as e:
             self.logger.debug(f"Error esperando carga del post: {str(e)}")
             return False

    def _extract_post_data_improved(self):
        """Extractor de datos mejorado y más robusto con debugging"""
        try:
            # Obtener URL actual
            post_url = self.driver.current_url
            
            # Debug de estructura (solo en modo debug)
            self._debug_current_page()  # ← AGREGAR ESTA LÍNEA
        
            # Debug de estructura (solo en modo debug)
            try:
                self._debug_page_structure()
            except:
                pass
            
            # Extraer imagen principal
            img_url = self._extract_image_improved()
            if not img_url:
                self.logger.warning("No se pudo extraer imagen")
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
        """Extractor de descripción ULTRA MEJORADO con debugging detallado"""
        try:
            self.logger.debug("🔍 Iniciando extracción ULTRA mejorada de descripción...")
            
            # === GUARDAR SCREENSHOT PARA DEBUG ===
            if self._is_browser_alive():
                try:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    debug_screenshot = f"debug_description_{timestamp}.png"
                    self.driver.save_screenshot(debug_screenshot)
                    self.logger.debug(f"📸 Screenshot guardado: {debug_screenshot}")
                except:
                    pass
            
            # === ESTRATEGIA NUEVA: SELECTORES ESPECÍFICOS PARA CAPTION ===
            caption_selectors = [
                # Selectores más específicos para captions de Instagram 2025
                "article h1",  # Nuevo selector para títulos principales
                "article div[data-testid='post-caption'] span",
                "div[role='dialog'] div[data-testid='post-caption'] span",
                "article div[data-testid='post-caption-content'] span",
                
                # Selectores por estructura DOM actual
                "article div[class*='_ap3a'] div[class*='_a9zs'] span[dir='auto']",
                "div[role='dialog'] div[class*='_ap3a'] div[class*='_a9zs'] span[dir='auto']",
                
                # Selectores alternativos para contenido de texto
                "article div[role='button'] + div span[dir='auto']",
                "article div[class*='x1lliihq'] span[dir='auto']",
                
                # Selectores más amplios
                "article span[class*='_aacl _aaco _aacu _aacx _aad7 _aade']",
                "div[role='dialog'] span[class*='_aacl _aaco _aacu _aacx _aad7 _aade']",
            ]
            
            self.logger.debug(f"🎯 Probando {len(caption_selectors)} selectores específicos para captions...")
            
            for i, selector in enumerate(caption_selectors):
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    self.logger.debug(f"Selector {i+1}: '{selector}' → {len(elements)} elementos")
                    
                    for j, element in enumerate(elements):
                        try:
                            text = element.text.strip()
                            if text:
                                self.logger.debug(f"  Elemento {j+1}: '{text[:100]}...' ({len(text)} chars)")
                                
                                # Verificación mejorada
                                if self._is_job_related_description(text):
                                    self.logger.info(f"✅ DESCRIPCIÓN EXTRAÍDA - Selector {i+1}: '{selector}' ({len(text)} chars)")
                                    self.logger.debug(f"💡 Contenido completo: {text}")
                                    return text
                                    
                        except Exception as e:
                            self.logger.debug(f"Error procesando elemento {j+1}: {str(e)}")
                            continue
                            
                except Exception as e:
                    self.logger.debug(f"Error con selector {i+1}: {str(e)}")
                    continue
            
            # === ESTRATEGIA TEXTO COMPLETO CON FILTRADO INTELIGENTE ===
            self.logger.debug("🧠 Estrategia: Análisis inteligente de texto completo...")
            
            try:
                # Obtener todo el texto visible del artículo
                article = self.driver.find_element(By.TAG_NAME, "article")
                if article:
                    full_text = article.text.strip()
                    self.logger.debug(f"📄 Texto completo del artículo: {len(full_text)} caracteres")
                    
                    # Guardar texto completo para debug
                    try:
                        with open(f"debug_full_text_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", 'w', encoding='utf-8') as f:
                            f.write(f"POST URL: {self.driver.current_url}\n")
                            f.write(f"FULL TEXT ({len(full_text)} chars):\n")
                            f.write(f"{'='*50}\n")
                            f.write(full_text)
                    except:
                        pass
                    
                    # Extraer descripción inteligentemente
                    extracted_description = self._extract_smart_description(full_text)
                    if extracted_description:
                        self.logger.info(f"✅ DESCRIPCIÓN EXTRAÍDA del texto completo ({len(extracted_description)} chars)")
                        return extracted_description
                        
            except Exception as e:
                self.logger.debug(f"Error en análisis de texto completo: {str(e)}")
            
            # === ESTRATEGIA DE ÚLTIMO RECURSO: XPATH AGRESIVO ===
            self.logger.debug("🚨 Estrategia de último recurso: XPath agresivo...")
            
            aggressive_xpaths = [
                "//article//span[string-length(text()) > 50]",
                "//div[@role='dialog']//span[string-length(text()) > 50]",
                "//article//div[contains(@class, 'caption')]//span",
                "//article//div[contains(@style, 'white-space')]//span",
                "//span[contains(text(), 'práctica') or contains(text(), 'trabajo') or contains(text(), 'empresa')]",
            ]
            
            for xpath in aggressive_xpaths:
                try:
                    elements = self.driver.find_elements(By.XPATH, xpath)
                    self.logger.debug(f"XPath '{xpath}' → {len(elements)} elementos")
                    
                    for element in elements:
                        try:
                            text = element.text.strip()
                            if self._is_job_related_description(text):
                                self.logger.info(f"✅ DESCRIPCIÓN EXTRAÍDA con XPath agresivo ({len(text)} chars)")
                                return text
                        except:
                            continue
                except:
                    continue
            
            self.logger.warning("⚠️ No se pudo extraer descripción con NINGÚN método")
            return ""
            
        except Exception as e:
            self.logger.error(f"❌ Error crítico extrayendo descripción: {str(e)}")
            return ""

    def _is_job_related_description(self, text):
        """Verifica si el texto es una descripción relacionada con trabajo"""
        try:
            if not text or len(text) < 20:
                return False
            
            # Palabras clave de trabajo/ofertas laborales
            job_keywords = [
                'práctica', 'trabajo', 'empleo', 'vacante', 'oferta', 'empresa',
                'contacto', 'solicita', 'busca', 'requiere', 'oportunidad',
                'posición', 'puesto', 'cargo', 'reclutamiento', 'talento',
                'profesional', 'candidato', 'aplicar', 'enviar', 'curriculum'
            ]
            
            # Filtros para excluir UI de Instagram
            ui_filters = [
                'subir contactos', 'personas no usuarias', 'like', 'share', 
                'comment', 'view', 'follow', 'more posts', 'stories', 'reels',
                'home', 'profile', 'explore', 'ago', 'hace', 'hours', 'horas',
                'minutes', 'minutos', 'days', 'días', 'ver más', 'show more'
            ]
            
            text_lower = text.lower()
            
            # Si contiene principalmente filtros de UI, rechazar
            ui_count = sum(1 for ui_word in ui_filters if ui_word in text_lower)
            if ui_count > 2:  # Si tiene más de 2 palabras de UI
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
        """Extrae descripción de manera inteligente del texto completo"""
        try:
            lines = full_text.split('\n')
            self.logger.debug(f"🔍 Analizando {len(lines)} líneas de texto...")
            
            # Buscar líneas que contengan información de trabajo
            job_lines = []
            found_job_content = False
            
            for i, line in enumerate(lines):
                line = line.strip()
                if not line or len(line) < 10:
                    continue
                
                self.logger.debug(f"Línea {i+1}: '{line[:50]}...'")
                
                # Si es una línea de trabajo, empezar a recopilar
                if self._is_job_related_description(line):
                    found_job_content = True
                    job_lines.append(line)
                    self.logger.debug(f"  ✅ Línea de trabajo detectada")
                elif found_job_content and len(line) > 20:
                    # Continuar recopilando si ya encontramos contenido de trabajo
                    # y la línea no es obviamente UI
                    if not any(ui in line.lower() for ui in ['like', 'comment', 'share', 'ago', 'hace']):
                        job_lines.append(line)
                        self.logger.debug(f"  ➕ Línea adicional agregada")
                    else:
                        # Si encontramos UI, parar la recopilación
                        self.logger.debug(f"  🛑 Línea de UI detectada, parando recopilación")
                        break
                        
            if job_lines:
                description = '\n'.join(job_lines)
                self.logger.debug(f"📝 Descripción inteligente construida: {len(description)} chars")
                return description
                
            return ""
            
        except Exception as e:
            self.logger.debug(f"Error en extracción inteligente: {str(e)}")
            return ""

    def _is_valid_description(self, text):
        """Verifica si un texto es una descripción válida de Instagram"""
        try:
            # Filtros para excluir elementos de UI
            ui_keywords = [
                'like', 'share', 'comment', 'view', 'follow', 'more posts',
                'mas publicaciones', 'posts from', 'ver más', 'show more',
                'ago', 'hours', 'minutes', 'days', 'weeks', 'months',
                'hace', 'horas', 'minutos', 'días', 'semanas', 'meses',
                'home', 'profile', 'stories', 'reels', 'explore'
            ]
            
            # Verificar que no sea solo elementos de UI
            if any(ui_word in text.lower() for ui_word in ui_keywords):
                # Si contiene UI keywords, verificar que también tenga contenido real
                job_keywords = [
                    'práctica', 'trabajo', 'empresa', 'contacto', 'empleo',
                    'vacante', 'oferta', 'solicita', 'busca', 'requiere'
                ]
                if not any(job_word in text.lower() for job_word in job_keywords):
                    return False
            
            # Verificar que tenga contenido sustancial
            if len(text.split()) < 5:  # Menos de 5 palabras
                return False
            
            # Verificar que no sea solo números o símbolos
            if not any(c.isalpha() for c in text):
                return False
                
            return True
            
        except:
            return False

    def _extract_job_description_from_text(self, full_text):
        """Extrae descripción de trabajo de un texto completo"""
        try:
            lines = full_text.split('\n')
            job_lines = []
            capturing = False
            
            job_indicators = [
                'práctica', 'trabajo', 'empleo', 'vacante', 'oferta',
                'empresa', 'contacto', 'solicita', 'busca', 'requiere',
                'oportunidad', 'posición', 'puesto'
            ]
            
            for line in lines:
                line = line.strip()
                
                # Saltar líneas vacías o muy cortas
                if not line or len(line) < 10:
                    continue
                
                # Saltar elementos de UI
                if any(ui in line.lower() for ui in ['like', 'comment', 'share', 'ago', 'hace']):
                    continue
                
                # Comenzar a capturar si encontramos indicadores de trabajo
                if any(indicator in line.lower() for indicator in job_indicators):
                    capturing = True
                    job_lines.append(line)
                    continue
                
                # Si ya estamos capturando, continuar hasta encontrar una línea irrelevante
                if capturing:
                    # Verificar si la línea sigue siendo relevante
                    if (len(line) > 20 and 
                        not any(ui in line.lower() for ui in ['home', 'profile', 'stories'])):
                        job_lines.append(line)
                    else:
                        # Si encontramos una línea irrelevante, dejar de capturar
                        break
            
            if job_lines:
                description = '\n'.join(job_lines)
                if len(description) > 50:  # Asegurar que tenga contenido sustancial
                    return description
                    
            return ""
            
        except:
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

    def _debug_current_page(self):
        """Debugging TEMPORAL para ver qué elementos existen en la página"""
        try:
            current_url = self.driver.current_url
            self.logger.info(f"🔍 DEBUGGING página: {current_url}")
        
            # Verificar elementos básicos
            basic_checks = {
                "HTML body": "body",
                "Main sections": "main, section",
                "All divs": "div",
                "All images": "img",
                "Elements with testid": "[data-testid]",
                "Articles": "article",
                "Roles": "[role]",
            }
        
            for name, selector in basic_checks.items():
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    self.logger.info(f"  📋 {name}: {len(elements)} elementos")
                
                    # Para imágenes, mostrar algunas URLs
                    if selector == "img" and elements:
                        for i, img in enumerate(elements[:3]):
                            src = img.get_attribute("src") or "No src"
                            self.logger.info(f"    Imagen {i+1}: {src[:100]}...")
                        
                except Exception as e:
                    self.logger.info(f"  ❌ {name}: Error - {str(e)}")
        
            # Verificar título de la página
            try:
                title = self.driver.title
                self.logger.info(f"  📄 Título: {title}")
            except:
                pass
            
            # Guardar HTML completo para análisis
            try:
                html_debug = f"debug_html_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                with open(html_debug, 'w', encoding='utf-8') as f:
                    f.write(self.driver.page_source)
                self.logger.info(f"  📁 HTML guardado en: {html_debug}")
            except Exception as e:
                self.logger.info(f"  ❌ No se pudo guardar HTML: {str(e)}")
            
        except Exception as e:
            self.logger.error(f"Error en debug de página: {str(e)}")

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
        """Carga cookies previamente guardadas - VERSIÓN CORREGIDA"""
        try:
            if not os.path.exists('instagram_cookies.pkl'):
                self.logger.info("📋 No hay cookies guardadas, se realizará login normal")
                return False
            
            if not self._is_browser_alive():
                self.logger.warning("Navegador no disponible para cargar cookies")
                return False
            
            self.logger.info("🍪 Intentando cargar cookies guardadas...")
            
            with open('instagram_cookies.pkl', 'rb') as f:
                cookies = pickle.load(f)
            
            self.logger.info(f"📦 {len(cookies)} cookies encontradas")
            
            # Navegar a Instagram primero
            self.driver.get(self.base_url)
            self.random_sleep(2, 3)
            
            # Añadir cookies
            cookies_loaded = 0
            for cookie in cookies:
                try:
                    self.driver.add_cookie(cookie)
                    cookies_loaded += 1
                except Exception as e:
                    self.logger.debug(f"Error agregando cookie: {str(e)}")
                    continue
            
            self.logger.info(f"✅ {cookies_loaded} cookies aplicadas correctamente")
            
            # Recargar la página
            self.driver.refresh()
            self.random_sleep(3, 5)
            
            # Verificar si la sesión está activa con múltiples métodos
            session_active = False
            
            # Método 1: Buscar elementos de usuario logueado
            try:
                home_indicators = [
                    "svg[aria-label='Home']",
                    "svg[aria-label='Inicio']", 
                    "a[href='/']//svg",
                    "div[class*='x1n2onr6']//img[@alt]",  # Avatar de usuario
                    "nav a[href='/direct/']",  # Direct messages
                ]
                
                for indicator in home_indicators:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, indicator)
                    if elements and elements[0].is_displayed():
                        session_active = True
                        self.logger.info(f"✅ Sesión activa detectada con: {indicator}")
                        break
                        
            except Exception as e:
                self.logger.debug(f"Error verificando sesión: {str(e)}")
            
            # Método 2: Verificar que NO estemos en login
            if not session_active:
                try:
                    login_elements = self.driver.find_elements(By.XPATH, "//input[@name='username']")
                    if not login_elements:  # Si NO hay campos de login, probablemente estemos logueados
                        session_active = True
                        self.logger.info("✅ Sesión activa: no se encontraron campos de login")
                except:
                    pass
            
            # Método 3: Verificar URL actual
            if not session_active:
                current_url = self.driver.current_url
                if '/accounts/login' not in current_url and '/login' not in current_url:
                    session_active = True
                    self.logger.info(f"✅ Sesión activa: URL actual {current_url}")
            
            if session_active:
                self.logger.info("🎉 Sesión cargada exitosamente desde cookies")
                return True
            else:
                self.logger.info("❌ No se pudo restaurar la sesión desde cookies")
                # Eliminar cookies inválidas
                try:
                    os.remove('instagram_cookies.pkl')
                    self.logger.info("🗑️ Cookies inválidas eliminadas")
                except:
                    pass
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error cargando cookies: {str(e)}")
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

    def _debug_page_structure(self):
        """Método de debugging para analizar la estructura de la página"""
        try:
            if not self._is_browser_alive():
                return
                
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            debug_file = f"debug_page_structure_{timestamp}.txt"
            
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(f"POST URL: {self.driver.current_url}\n")
                f.write(f"TIMESTAMP: {timestamp}\n")
                f.write("="*80 + "\n\n")
                
                # Analizar artículos
                articles = self.driver.find_elements(By.TAG_NAME, "article")
                f.write(f"ARTÍCULOS ENCONTRADOS: {len(articles)}\n\n")
                
                for i, article in enumerate(articles):
                    f.write(f"ARTÍCULO {i+1}:\n")
                    f.write(f"Texto completo ({len(article.text)} chars):\n")
                    f.write(article.text[:500] + "...\n\n")
                    
                # Analizar elementos con data-testid
                testid_elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid*='caption']")
                f.write(f"ELEMENTOS CON data-testid 'caption': {len(testid_elements)}\n\n")
                
                for i, elem in enumerate(testid_elements):
                    f.write(f"ELEMENTO {i+1}: {elem.text[:200]}...\n\n")
                
                # Analizar spans con contenido
                spans = self.driver.find_elements(By.CSS_SELECTOR, "article span, div[role='dialog'] span")
                long_spans = [span for span in spans if len(span.text.strip()) > 30]
                f.write(f"SPANS CON CONTENIDO LARGO: {len(long_spans)}\n\n")
                
                for i, span in enumerate(long_spans[:10]):  # Solo los primeros 10
                    f.write(f"SPAN {i+1}: {span.text[:100]}...\n\n")
                    
            self.logger.info(f"📊 Debug de estructura guardado en: {debug_file}")
            
        except Exception as e:
            self.logger.error(f"Error en debug de estructura: {str(e)}")