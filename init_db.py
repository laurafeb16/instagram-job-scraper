#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para inicializar la base de datos y ejecutar migraciones.
"""
import os
import subprocess
import argparse
from typing import Optional, List

from sqlalchemy_utils import database_exists, create_database
from sqlalchemy import create_engine

from backend.config import DATABASE_URL
from backend.logging_config import setup_logging, get_logger

# Configurar logging
setup_logging()
logger = get_logger(__name__)

def run_alembic_command(command: str, message: Optional[str] = None) -> None:
    """Ejecuta un comando de Alembic.
    
    Args:
        command: Comando a ejecutar
        message: Mensaje opcional para la migración
    """
    cmd: List[str] = ["alembic", command]
    if command == "revision" and message:
        cmd.extend(["--autogenerate", "-m", message])
    
    logger.info(f"Ejecutando: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

def create_db_if_not_exists() -> None:
    """Crea la base de datos si no existe."""
    if not database_exists(DATABASE_URL):
        logger.info(f"Creando base de datos: {DATABASE_URL}")
        create_database(DATABASE_URL)
    else:
        logger.info(f"Base de datos ya existe: {DATABASE_URL}")

def main() -> None:
    """Función principal para inicializar la base de datos."""
    parser = argparse.ArgumentParser(description="Inicializar base de datos y migraciones")
    parser.add_argument("--message", "-m", default="Initial migration",
                        help="Mensaje para la migración inicial")
    parser.add_argument("--recreate", "-r", action="store_true",
                        help="Recrear la base de datos desde cero")
    args = parser.parse_args()
    
    # Verificar que estamos en el directorio raíz del proyecto
    if not os.path.exists("alembic.ini"):
        logger.error("Este script debe ejecutarse desde el directorio raíz del proyecto")
        return
    
    # Crear/verificar base de datos
    try:
        create_db_if_not_exists()
    except Exception as e:
        logger.error(f"Error al crear base de datos: {e}")
        return
    
    # Revisar si ya existen migraciones
    versions_dir = "backend/alembic/versions"
    has_migrations = os.path.exists(versions_dir) and len(os.listdir(versions_dir)) > 0
    
    # Crear migración inicial si no existe
    if not has_migrations:
        logger.info("Creando migración inicial")
        run_alembic_command("revision", args.message)
    else:
        logger.info("Ya existen migraciones")
    
    # Aplicar migraciones
    logger.info("Aplicando migraciones")
    if args.recreate:
        # Recrear desde cero
        run_alembic_command("downgrade", "base")
        run_alembic_command("upgrade", "head")
    else:
        # Solo actualizar
        run_alembic_command("upgrade", "head")
    
    logger.info("Base de datos inicializada correctamente")

if __name__ == "__main__":
    main()