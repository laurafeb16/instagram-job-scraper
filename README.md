# Instagram Job Scraper

Herramienta especializada para extraer ofertas de trabajo y prácticas profesionales de páginas de Instagram de facultades.

## Requisitos previos

1. Instalar Tesseract OCR con soporte para español:
   - Ubuntu: `sudo apt-get install tesseract-ocr tesseract-ocr-spa`
   - macOS: `brew install tesseract tesseract-lang`
   - Windows: Descargar instalador desde https://github.com/UB-Mannheim/tesseract/wiki (asegúrate de incluir el paquete de idioma español)

2. Configurar sesión de Instagram:
   - Ejecuta `instaloader --login=TU_USUARIO_INSTAGRAM` para guardar la sesión

## Instalación

1. Clonar el repositorio: `git clone https://github.com/tu-usuario/instagram-job-scraper.git` `cd instagram-job-scraper`
2. Instalar dependencias: pip install -r requirements.txt

## Uso

Ejecutar búsqueda de ofertas: python -m backend.main --username=USUARIO_FACULTAD --session=TU_USUARIO_INSTAGRAM --post-limit=20

Opciones:
- `--username`: Perfil de Instagram a analizar (por defecto: ucm_fdi)
- `--session`: Usuario de Instagram cuya sesión está guardada
- `--post-limit=20`: Número máximo de posts a revisar (por defecto: 10)
- `--max-retries=5`: Número máximo de reintentos para operaciones fallidas
- `--keep-files`: No eliminar los archivos temporales después de la ejecución
- `--tesseract-path`: Ruta al ejecutable de Tesseract OCR

## Filtrado de ofertas

El script busca específicamente posts que contengan patrones como:
- "Vacante ofrecida por [compañía]"
- "Práctica laboral ofrecida por [compañía]"
- "Práctica profesional ofrecida por [compañía]"
- Otros patrones similares de ofertas de empleo

## Estructura de datos

El script guarda solo los posts que coinciden con ofertas laborales:
- Imágenes en `data/raw/{shortcode}.jpg`
- Metadatos en `data/raw/{shortcode}.json` con información como usuario, empresa, leyenda y timestamp

## Estructura del proyecto
instagram-job-scraper/ 
├── .gitignore 
├── README.md 
├── requirements.txt 
├── backend/ 
│   ├── init.py 
│   ├── main.py 
│   ├── scraper.py 
│   ├── ocr_processor.py 
│   └── job_extractor.py 
└── data/
└── raw/

## Notas sobre OCR

- El reconocimiento funciona mejor en imágenes con texto claro sobre fondo simple
- Pósters y diseños complejos pueden tener menor precisión de reconocimiento
- Imágenes de ofertas de trabajo formales suelen tener mejores resultados