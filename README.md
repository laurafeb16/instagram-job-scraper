<p align="center">
  <img src="icon.svg" width="80" alt="Logo">
</p>
<h1 align="center">Instagram Job Scraper</h1>

Sistema especializado para extraer, procesar y analizar ofertas de trabajo y prácticas profesionales publicadas en perfiles de Instagram de facultades universitarias.

## Problema

Las facultades universitarias publican frecuentemente ofertas laborales y prácticas en sus perfiles de Instagram, pero:
- No existe una forma centralizada de acceder a estas ofertas
- La información está embebida en imágenes, dificultando la búsqueda y análisis
- No hay herramientas para identificar tendencias en demanda de habilidades

## Diseño y Arquitectura

El sistema implementa un flujo de procesamiento en etapas:
sequenceDiagram participant U as Usuario participant S as Scraper participant O as OCR participant E as Extractor participant DB as Base de Datos participant D as Dashboard
U->>S: Inicia extracción (perfil, posts_max)
S->>S: Navega y extrae posts
loop Para cada post
    S->>O: Procesa imagen con OCR
    O->>E: Detecta si es oferta laboral
    alt Es oferta
        E->>E: Extrae información estructurada
        E->>DB: Almacena datos
    end
end
U->>D: Consulta Dashboard
D->>DB: Obtiene análisis y tendencias
D->>U: Muestra visualizaciones

### Componentes Principales

- **Scraper**: Navega perfiles de Instagram usando Selenium para emular comportamiento humano
- **OCR Processor**: Procesa imágenes usando OpenCV y Tesseract para extraer texto
- **Job Extractor**: Identifica ofertas y extrae información estructurada mediante patrones
- **Dashboard**: Visualiza datos y análisis usando Streamlit

## Compensaciones (Trade-offs)

- **Robustez vs. Velocidad**: Implementamos pausas aleatorias y navegación simulando humanos para evitar bloqueos, sacrificando velocidad
- **Precisión vs. Generalidad**: OCR funciona mejor en imágenes con texto claro, pero hay compromiso con compatibilidad para diseños complejos
- **Almacenamiento vs. Tiempo**: Guardamos tanto imágenes como texto para permitir reanalizar sin volver a descargar

## Instrucciones

### Requisitos Previos

1. Instalar Tesseract OCR con soporte para español:
   - Ubuntu: `sudo apt-get install tesseract-ocr tesseract-ocr-spa`
   - macOS: `brew install tesseract tesseract-lang`
   - Windows: Descargar desde [GitHub UB-Mannheim](https://github.com/UB-Mannheim/tesseract/wiki)

2. Instalar dependencias: `pip install -r requirements.txt`

3. Configurar variables de entorno: `cp .env.example .env`


## Instalación

1. Clonar el repositorio: `git clone https://github.com/tu-usuario/instagram-job-scraper.git cd instagram-job-scraper`
2. Crear y activar entorno virtual (recomendado): `python -m venv env source env/bin/activate  # Linux/macOS env\Scripts\activate     # Windows`
3. Instalar dependencias: pip install -r requirements.txt
4. Configurar variables de entorno (opcional):
   - Copia `.env.example` a `.env`
   - Edita `.env` con tus configuraciones

## Ejecución

### Modo básico: 
`python scrape.py --username=USUARIO_FACULTAD --posts=20`

### Opciones disponibles:
`python scrape.py --username=ucm_fdi --posts=10 --headless --save-browser --verbose`

Parámetros:
- `--username`: Perfil de Instagram a analizar (obligatorio)
- `--posts`: Número máximo de posts a analizar (por defecto: 10)
- `--headless`: Ejecutar en modo headless (sin interfaz gráfica)
- `--save-browser`: No cerrar el navegador al terminar
- `--verbose`: Mostrar información detallada durante la ejecución

### Tests

Ejecuta todos los tests: `pytest`
Con cobertura: `pytest --cov=backend`
Tests específicos: `pytest tests/unit/test_job_extractor.py`

## Observabilidad

El sistema proporciona métricas en formato Prometheus:

- `jobs_scraped_total`: Total de ofertas extraídas
- `http_requests_duration_seconds`: Duración de peticiones HTTP
- `ocr_processing_duration_seconds`: Tiempo de procesamiento OCR

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
