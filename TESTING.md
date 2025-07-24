# Guía de Testing

Este documento describe los patrones y estrategias de prueba utilizados en el proyecto.

## Estructura de Tests

- /tests/unit/: Tests unitarios para componentes individuales
- /tests/integration/: Tests de integración entre componentes

## Componentes y Estrategias

### JobExtractor
- Se mockean las dependencias externas
- Se prueban patrones de extracción con textos predefinidos
- Cobertura actual: 93%

### OCRProcessor
- Se mockea pytesseract para evitar dependencia de OCR real
- Se simulan imágenes para probar preprocesamiento
- Cobertura actual: 68%

### InstagramScraper
- Se mockea Selenium para evitar acceso real a Instagram
- Se simulan respuestas para probar el procesamiento
- Cobertura actual: 55%

### Main
- Se mockean componentes individuales para probar flujo principal
- Cobertura actual: 85%

## Ejecutar Tests
pytest

##Ejecutar con cobertura
pytest --cov=backend

##Ejecutar Tests Unitarios
pytest tests/unit


## Futuras Mejoras

- Implementar tests para base de datos usando bases de datos en memoria
- Crear tests para componentes ML con datos sintéticos
- Implementar tests E2E cuando el dashboard esté completo
