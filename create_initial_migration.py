#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para crear la migraci�n inicial de la base de datos.
"""
import os
import subprocess
import argparse
from typing import Optional

def run_alembic_command(command: str, message: Optional[str] = None) -> None:
    """Ejecuta un comando de Alembic.
    
    Args:
        command: Comando a ejecutar
        message: Mensaje opcional para la migraci�n
    """
    cmd = ["alembic", command]
    if command == "revision" and message:
        cmd.extend(["--autogenerate", "-m", message])
    
    print(f"Ejecutando: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

def main() -> None:
    """Funci�n principal para crear migraciones."""
    parser = argparse.ArgumentParser(description="Crear migraciones de base de datos")
    parser.add_argument("--message", "-m", default="Initial migration",
                        help="Mensaje para la migraci�n")
    args = parser.parse_args()
    
    # Verificar que estamos en el directorio ra�z del proyecto
    if not os.path.exists("alembic.ini"):
        print("Error: Este script debe ejecutarse desde el directorio ra�z del proyecto")
        return
    
    # Iniciar la migraci�n
    run_alembic_command("revision", args.message)
    print("Migraci�n creada exitosamente.")
    
    # Opcional: aplicar la migraci�n
    respuesta = input("�Desea aplicar la migraci�n ahora? (s/n): ")
    if respuesta.lower() == 's':
        run_alembic_command("upgrade", "head")
        print("Migraci�n aplicada exitosamente.")

if __name__ == "__main__":
    main()