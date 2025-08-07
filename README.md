Instagram Job Scraper

> **Proyecto Capstone** - Analizador automatizado de ofertas laborales en Instagram

## Descripción

Sistema inteligente que automatiza la detección y análisis de ofertas laborales publicadas en Instagram, específicamente para la Facultad de Ingeniería de Sistemas Computacionales (FISC) de la UTP.

## Características

- **Web Scraping** con Selenium
- **OCR** para extracción de texto desde imágenes
- **Análisis NLP** para clasificación automática
- **Base de datos** SQLAlchemy
- **Dashboard web** con Flask
- **Exportación** a Excel y CSV

## Instalación

### Prerrequisitos
- Python 3.8+
- Chrome + ChromeDriver
- Tesseract OCR

### Configuración
Clonar repositorio
git clone <repo-url> cd instagram-job-scraper

Instalar dependencias
pip install -r requirements.txt

Configurar variables de entorno
cp .env.example .env

Editar .env con tus credenciales

### Instalar Tesseract

**Windows:**
Descargar desde: https://github.com/UB-Mannheim/tesseract/wiki
**Linux:**
sudo apt install tesseract-ocr tesseract-ocr-spa
**macOS:**
rew install tesseract tesseract-lang

### Configurar .env
INSTAGRAM_USERNAME=tu_usuario 
INSTAGRAM_PASSWORD=tu_contraseña 
TARGET_ACCOUNT=utpfisc

## Uso

### Comandos básicos

Procesamiento estándar (25 posts)
python src/main.py

Número específico
python src/main.py 50

Modo headless
python src/main.py 20 --headless

Procesamiento masivo
python src/main.py --max

Dashboard web
python src/web/app.py

Abrir: http://localhost:5000

### Opciones avanzadas

Modo debug
python src/main.py 10 --debug

Solo limpiar BD
python src/main.py --clean-only

Procesar en lotes
python src/main.py 100 --batch 25

## Resultados
=== RESUMEN === Posts procesados: 25 Ofertas encontradas: 18 Tasa de éxito: 72%
Por tipo:
•    Práctica Profesional: 8
•    Práctica Laboral: 6
•    Vacante: 4

## :tools: Solución de Problemas

| Problema | Solución |
|----------|----------|
| ChromeDriver not found | Colocar chromedriver.exe en raíz |
| Tesseract not found | Verificar instalación y PATH |
| Login failed | Revisar credenciales en .env |

## Roadmap

- [x] Scraping básico
- [x] Dashboard web
- [ ] Machine Learning

*Desarrollado para la Universidad Tecnológica de Panamá*
