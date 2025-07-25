# -*- coding: utf-8 -*-
"""
M�dulo para configuraci�n y recolecci�n de m�tricas de observabilidad.
"""
from typing import Callable, Any, TypeVar, Dict
import time
import functools

from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry

# Crear registro para m�tricas
registry = CollectorRegistry()

# M�tricas de Instagram
POSTS_SCRAPED = Counter(
    'instagram_posts_scraped_total', 
    'Total number of Instagram posts scraped',
    registry=registry
)

JOBS_EXTRACTED = Counter(
    'jobs_extracted_total', 
    'Total number of job posts extracted',
    registry=registry
)

FAILED_SCRAPES = Counter(
    'instagram_scrape_failures_total', 
    'Total number of failed scraping attempts',
    registry=registry
)

# M�tricas de duraci�n
HTTP_REQUEST_DURATION = Histogram(
    'http_requests_duration_seconds', 
    'Duration of HTTP requests in seconds',
    ['method', 'endpoint'],
    registry=registry
)

OCR_PROCESSING_DURATION = Histogram(
    'ocr_processing_duration_seconds', 
    'Duration of OCR processing in seconds',
    registry=registry
)

JOB_EXTRACTION_DURATION = Histogram(
    'job_extraction_duration_seconds', 
    'Duration of job information extraction in seconds',
    registry=registry
)

# M�tricas de estado
ACTIVE_SCRAPING_JOBS = Gauge(
    'active_scraping_jobs', 
    'Number of active scraping jobs',
    registry=registry
)

EXTRACTION_SUCCESS_RATE = Gauge(
    'job_extraction_success_rate_percent', 
    'Success rate of job extraction from posts',
    registry=registry
)

# Tipo gen�rico para funciones
F = TypeVar('F', bound=Callable[..., Any])

def track_time(histogram: Histogram) -> Callable[[F], F]:
    """Decorador para medir el tiempo de ejecuci�n de una funci�n.
    
    Args:
        histogram: Histograma Prometheus donde registrar la duraci�n
        
    Returns:
        Funci�n decorada que registra su tiempo de ejecuci�n
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapped_func(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            try:
                return func(*args, **kwargs)
            finally:
                duration = time.time() - start_time
                histogram.observe(duration)
        return wrapped_func  # type: ignore
    return decorator

def track_http_request(method: str, endpoint: str) -> Callable[[F], F]:
    """Decorador para medir el tiempo de ejecuci�n de peticiones HTTP.
    
    Args:
        method: M�todo HTTP (GET, POST, etc.)
        endpoint: Endpoint o URL destino
        
    Returns:
        Funci�n decorada que registra su tiempo de ejecuci�n
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapped_func(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            try:
                return func(*args, **kwargs)
            finally:
                duration = time.time() - start_time
                HTTP_REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)
        return wrapped_func  # type: ignore
    return decorator

def update_extraction_success_rate(success_count: int, total_count: int) -> None:
    """Actualiza la tasa de �xito de extracci�n de trabajos.
    
    Args:
        success_count: N�mero de extracciones exitosas
        total_count: N�mero total de intentos
    """
    if total_count > 0:
        success_rate = (success_count / total_count) * 100
        EXTRACTION_SUCCESS_RATE.set(success_rate)