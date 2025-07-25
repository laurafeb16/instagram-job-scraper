<p align="center">
  <img src="icon.svg" width="80" alt="Logo">
</p>
<h1 align="center">Instagram Job Scraper</h1>

Herramienta especializada para extraer ofertas de trabajo y prácticas profesionales de páginas de Instagram de facultades, utilizando técnicas avanzadas de scraping, OCR y procesamiento de lenguaje natural.

## Características

- Extracción eficiente de posts de Instagram mediante Selenium
- Procesamiento avanzado de imágenes con OpenCV para mejorar OCR
- Reconocimiento óptico de caracteres (OCR) bilingüe español/inglés
- Identificación automática de ofertas de trabajo
- Extracción estructurada de información: empresa, puesto, requisitos, etc.
- Clasificación de ofertas por área tecnológica

## Requisitos previos

1. Python 3.8 o superior
2. Tesseract OCR con soporte para español:
   - Ubuntu: `sudo apt-get install tesseract-ocr tesseract-ocr-spa`
   - macOS: `brew install tesseract tesseract-lang`
   - Windows: Descargar instalador desde [GitHub UB-Mannheim](https://github.com/UB-Mannheim/tesseract/wiki)
3. Chrome o Chromium instalado
4. ChromeDriver compatible con tu versión de Chrome

## Instalación

1. Clonar el repositorio: `git clone https://github.com/tu-usuario/instagram-job-scraper.git cd instagram-job-scraper`
2. Crear y activar entorno virtual (recomendado): `python -m venv env source env/bin/activate  # Linux/macOS env\Scripts\activate     # Windows`
3. Instalar dependencias: pip install -r requirements.txt
4. Configurar variables de entorno (opcional):
   - Copia `.env.example` a `.env`
   - Edita `.env` con tus configuraciones

## Uso

### Modo básico: 
python scrape.py --username=USUARIO_FACULTAD --posts=20

### Opciones disponibles:
python scrape.py --username=ucm_fdi --posts=10 --headless --save-browser --verbose

Parámetros:
- `--username`: Perfil de Instagram a analizar (obligatorio)
- `--posts`: Número máximo de posts a analizar (por defecto: 10)
- `--headless`: Ejecutar en modo headless (sin interfaz gráfica)
- `--save-browser`: No cerrar el navegador al terminar
- `--verbose`: Mostrar información detallada durante la ejecución

## Filtrado de ofertas

El sistema detecta automáticamente posts de ofertas de trabajo que contienen patrones como:
- "Vacante ofrecida por [compañía]"
- "Práctica laboral ofrecida por [compañía]"
- "Práctica profesional ofrecida por [compañía]"
- Otros patrones similares de ofertas de empleo

## Estructura de datos

El script guarda los posts que coinciden con ofertas laborales:
- Imágenes en `data/raw/{shortcode}.jpg`
- Metadatos en `data/raw/{shortcode}.json` con información detallada
- Informes de ejecución en `data/report_{usuario}_{fecha}.json`

## Notas sobre limitaciones

- Instagram implementa restricciones anti-scraping. Este proyecto usa técnicas para minimizar el riesgo de bloqueo, pero no garantiza inmunidad contra restricciones.
- Se recomienda usar la herramienta con moderación y respetar los términos de servicio de Instagram.
- Para uso intensivo, considere implementar rotación de IP o proxies.

## Notas sobre OCR

- El reconocimiento funciona mejor en imágenes con texto claro sobre fondo simple
- Pósters y diseños complejos pueden tener menor precisión de reconocimiento
- El preprocesamiento de imágenes mejora significativamente los resultados de OCR
