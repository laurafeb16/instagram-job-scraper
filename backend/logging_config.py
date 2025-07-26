# -*- coding: utf-8 -*-
"""
Configuracion de logging estructurado para la aplicacion.
"""
import sys
import time
import uuid
from typing import Any, Dict, Optional, Callable

import structlog
from structlog.types import Processor, WrappedLogger

def generate_correlation_id() -> str:
    """Genera un ID de correlacion unico para seguimiento de operaciones.
    
    Returns:
        ID de correlacion en formato UUID4
    """
    return str(uuid.uuid4())

def add_timestamp(
    logger: WrappedLogger, name: str, event_dict: Dict[str, Any]
) -> Dict[str, Any]:
    """Anade timestamp en formato ISO a los eventos de log.
    
    Args:
        logger: Logger envuelto por structlog
        name: Nombre del logger
        event_dict: Diccionario del evento actual
        
    Returns:
        Diccionario del evento actualizado
    """
    event_dict["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%S.%fZ", time.gmtime())
    return event_dict

def setup_logging() -> None:
    """Configura el sistema de logging estructurado para la aplicacion."""
    processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        add_timestamp,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ]

    structlog.configure(
        processors=processors,
        logger_factory=structlog.PrintLoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(structlog.get_logger().level),
        context_class=dict,
        cache_logger_on_first_use=True,
    )

def get_logger(name: Optional[str] = None) -> structlog.BoundLogger:
    """Obtiene un logger configurado con el nombre especificado.
    
    Args:
        name: Nombre del modulo o componente
        
    Returns:
        Logger configurado
    """
    logger = structlog.get_logger(name)
    return logger.bind(component=name or "app")

def with_correlation_id(
    logger_func: Callable
) -> Callable:
    """Decorador para anadir un ID de correlacion a todas las llamadas de logging.
    
    Args:
        logger_func: Funcion de logging a decorar
        
    Returns:
        Funcion decorada
    """
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        correlation_id = kwargs.pop("correlation_id", generate_correlation_id())
        logger = kwargs.pop("logger", get_logger())
        
        bound_logger = logger.bind(correlation_id=correlation_id)
        return logger_func(*args, logger=bound_logger, **kwargs)
    
    return wrapper
