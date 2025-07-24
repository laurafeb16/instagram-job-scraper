# -*- coding: utf-8 -*-
"""
Configuración centralizada para el proyecto.
"""
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Instagram
INSTAGRAM_USERNAME = os.getenv("INSTAGRAM_USERNAME")
INSTAGRAM_PASSWORD = os.getenv("INSTAGRAM_PASSWORD")

# Tesseract
TESSERACT_PATH = os.getenv("TESSERACT_PATH")

# Database
DATABASE_URL = os.getenv("DATABASE_URL")

# Scraping
MAX_POSTS_PER_RUN = int(os.getenv("MAX_POSTS_PER_RUN", "20"))
SCRAPE_INTERVAL_HOURS = int(os.getenv("SCRAPE_INTERVAL_HOURS", "12"))
USER_AGENT = os.getenv("USER_AGENT")

# Directorios
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
TEMP_DIR = os.path.join(BASE_DIR, "temp_instagram_data")

# Asegurar directorios
os.makedirs(DATA_DIR, exist_ok=True)
