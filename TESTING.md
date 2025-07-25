# Guía de Testing

Este documento describe los patrones y estrategias de prueba utilizados en el proyecto.

## Estructura de Tests

- `/tests/unit/`: Tests unitarios para componentes individuales
- `/tests/integration/`: Tests de integración entre componentes

## Componentes y Estrategias

### JobExtractor
- Se mockean las dependencias externas
- Se prueban patrones de extracción con textos predefinidos
- **Cobertura actual**: 93%

### OCRProcessor
- Se mockea pytesseract para evitar dependencia de OCR real
- Se simulan imágenes para probar preprocesamiento
- **Cobertura actual**: 68%

### InstagramScraper
- Se mockea Selenium para evitar acceso real a Instagram
- Se simulan respuestas para probar el procesamiento
- **Cobertura actual**: 55%

### Main
- Se mockean componentes individuales para probar flujo principal
- **Cobertura actual**: 85%

## Patrones de Prueba

### Mocking de HTTP
Utilizamos `responses` o `pytest-httpserver` para simular respuestas HTTP:

```python
@responses.activate
def test_download_image():
    responses.add(
        responses.GET, "https://example.com/image.jpg",
        body=open("tests/fixtures/test_image.jpg", "rb").read(),
        status=200,
        content_type="image/jpeg"
    )
    processor = OCRProcessor()
    image = processor.download_image("https://example.com/image.jpg")
    assert image is not None
```

### Fixtures Parametrizadas
Usamos fixtures parametrizadas para probar varios escenarios:
```python
@pytest.mark.parametrize("text,expected", [
    ("Vacante ofrecida por Microsoft", (True, "Microsoft")),
    ("Información general sobre admisiones", (False, None)),
])
def test_is_job_post(text, expected):
    extractor = JobExtractor()
    result = extractor.is_job_post(text)
    assert result == expected
```
## Ejecutar Tests

### Ejecutar todos los tests
`pytest`

### Ejecutar con cobertura
`pytest --cov=backend`

### Ejecutar solo tests unitarios
`pytest tests/unit/`

### Ejecutar test específico
`pytest tests/unit/test_job_extractor.py::test_is_job_post`

## Futuras Mejoras

- Implementar tests para base de datos usando bases de datos en memoria
- Crear tests para componentes ML con datos sintéticos
- Implementar tests E2E cuando el dashboard esté completo
