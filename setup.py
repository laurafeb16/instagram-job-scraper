from setuptools import setup, find_packages

setup(
    name="instagram-job-scraper",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        # Scraping & OCR
        "selenium>=4.16.0",
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.2",
        "pytesseract>=0.3.10",
        "opencv-python>=4.8.1",
        "pillow>=10.0.0",
        "python-dotenv>=1.0.0",
        
        # Database
        "sqlalchemy>=2.0.0",
        "psycopg2-binary>=2.9.6",
        "alembic>=1.12.0",
        "sqlalchemy-utils>=0.41.0",
        
        # Logging y observabilidad
        "structlog>=23.1.0",
        "prometheus-client>=0.16.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.10.0",
            "black>=23.3.0",
            "flake8>=6.0.0",
            "mypy>=1.3.0",
        ],
        "dashboard": [
            "streamlit>=1.31.0",
            "plotly>=5.18.0",
            "pandas>=2.1.0",
            "matplotlib>=3.8.0",
            "wordcloud>=1.9.0",
        ],
    },
)
