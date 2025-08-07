# Instagram Job Scraper

**Proyecto Capstone** - Analizador automatizado de ofertas laborales en Instagram

## Descripción

Sistema inteligente que automatiza la detección y análisis de ofertas laborales publicadas en Instagram, específicamente diseñado para la Facultad de Ingeniería de Sistemas Computacionales (FISC) de la Universidad Tecnológica de Panamá.

## Características Principales

- **Web Scraping Automatizado**: Utiliza Selenium para navegación web inteligente
- **Reconocimiento Óptico de Caracteres (OCR)**: Extrae texto desde imágenes de ofertas laborales
- **Procesamiento de Lenguaje Natural (NLP)**: Clasificación automática de ofertas laborales
- **Base de Datos Robusta**: Gestión de datos con SQLAlchemy
- **Dashboard Interactivo**: Interfaz web desarrollada con Flask
- **Exportación de Datos**: Soporte para formatos Excel y CSV

## Instalación

### Prerrequisitos

- Python 3.8 o superior
- Google Chrome y ChromeDriver
- Tesseract OCR Engine

### Configuración Inicial

**1. Clonar el repositorio**

```bash
git clone <repo-url>
cd instagram-job-scraper
```

**2. Instalar dependencias**

```bash
pip install -r requirements.txt
```

**3. Configurar variables de entorno**

```bash
cp .env.example .env
```

Editar el archivo `.env` con tus credenciales de Instagram.

### Instalación de Tesseract OCR

**Windows:**
- Descargar desde: https://github.com/UB-Mannheim/tesseract/wiki
- Agregar al PATH del sistema

**Linux:**
```bash
sudo apt install tesseract-ocr tesseract-ocr-spa
```

**macOS:**
```bash
brew install tesseract tesseract-lang
```

### Configuración del archivo .env

```env
INSTAGRAM_USERNAME=tu_usuario
INSTAGRAM_PASSWORD=tu_contraseña
TARGET_ACCOUNT=utpfisc
```

## Uso del Sistema

### Comandos Básicos

**Procesamiento estándar (25 posts):**
```bash
python src/main.py
```

**Especificar número de posts:**
```bash
python src/main.py 50
```

**Modo headless (sin interfaz gráfica):**
```bash
python src/main.py 20 --headless
```

**Procesamiento masivo:**
```bash
python src/main.py --max
```

### Dashboard Web

**Iniciar servidor:**
```bash
python src/web/app.py
```

Acceder a: http://localhost:5000

### Opciones Avanzadas

**Modo debug:**
```bash
python src/main.py 10 --debug
```

**Solo limpiar base de datos:**
```bash
python src/main.py --clean-only
```

**Procesamiento en lotes:**
```bash
python src/main.py 100 --batch 25
```

## Resultados Típicos

```
=== RESUMEN ===
Posts procesados: 25
Ofertas encontradas: 18
Tasa de éxito: 72%

Distribución por tipo:
• Práctica Profesional: 8
• Práctica Laboral: 6
• Vacante: 4
```

## Solución de Problemas

| Problema | Causa Común | Solución |
|----------|-------------|----------|
| ChromeDriver not found | Driver no instalado | Colocar chromedriver.exe en directorio raíz |
| Tesseract not found | OCR no configurado | Verificar instalación y variable PATH |
| Instagram login failed | Credenciales incorrectas | Revisar usuario/contraseña en archivo .env |
| Memory issues | Procesamiento masivo | Usar parámetro --batch para procesar en lotes |

## Arquitectura del Proyecto

```
instagram-job-scraper/
├── src/
│   ├── main.py              # Punto de entrada principal
│   ├── scraper/             # Módulos de web scraping
│   ├── ocr/                 # Procesamiento OCR
│   ├── nlp/                 # Análisis de texto
│   ├── database/            # Gestión de base de datos
│   └── web/                 # Dashboard Flask
├── data/                    # Archivos de datos
├── exports/                 # Exportaciones CSV/Excel
└── logs/                    # Archivos de registro
```

## Estado de Desarrollo

- [x] Sistema de scraping básico
- [x] Implementación OCR
- [x] Dashboard web funcional
- [x] Exportación de datos
- [ ] Modelo de Machine Learning
