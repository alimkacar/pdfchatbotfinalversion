import os
from pathlib import Path

class Config:
    
    
    
    SECRET_KEY = os.environ.get('SECRET_KEY', 'pdf-rag-secret-key-2025')
    DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    
    MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'pdf'}
    
    
    BASE_DIR = Path(__file__).parent
    UPLOAD_FOLDER = BASE_DIR / 'data' / 'uploads'
    PROCESSED_FOLDER = BASE_DIR / 'data' / 'processed'
    
    # Metin işleme
    CHUNK_SIZE = 500
    CHUNK_OVERLAP = 100
    
    # Arama
    MAX_SEARCH_RESULTS = 5
    MIN_SIMILARITY = 0.01
    
    @classmethod
    def init_folders(cls):
        """Gerekli klasörleri oluşturur"""
        cls.UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
        cls.PROCESSED_FOLDER.mkdir(parents=True, exist_ok=True)
