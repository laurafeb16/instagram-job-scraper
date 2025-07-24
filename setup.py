from setuptools import setup, find_packages

setup(
    name="instagram-job-scraper",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        # Scraping & OCR
        "selenium",
        "requests",
        "beautifulsoup4",
        "pytesseract",
        "opencv-python",
        "pillow",
        "python-dotenv",
        
        # Database
        "sqlalchemy",
        "psycopg2-binary",
        "alembic",
        
        # Dashboard
        "streamlit",
        "plotly",
        "pandas",
        
        # ML
        "scikit-learn",
        "nltk",
        "spacy",
    ],
    extras_require={
        "dev": [
            "pytest",
            "pytest-cov",
            "pytest-mock",
            "black",
            "flake8",
        ],
    },
)
