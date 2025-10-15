import re
from werkzeug.utils import secure_filename

# Exception Sınıfları
class PDFProcessingError(Exception):
    """PDF işleme hataları"""
    pass

class SearchError(Exception):
    """Arama hataları"""
    pass

class ValidationError(Exception):
    """Validasyon hataları"""
    pass

# Validasyon Sınıfı
class Validator:
    """Basit validasyon işlemleri"""
    
    @staticmethod
    def validate_file(file, allowed_extensions, max_size):
        
        if not file or file.filename == '':
            raise ValidationError("Dosya seçilmedi")
        
        
        ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        if ext not in allowed_extensions:
            raise ValidationError(f"Geçersiz dosya formatı. İzin verilen: {', '.join(allowed_extensions)}")
        
        return secure_filename(file.filename)
    
    @staticmethod
    def validate_search_query(query, min_len=1, max_len=500):
        
        if not query or not query.strip():
            raise ValidationError("Arama terimi gerekli")
        
        query = query.strip()
        if len(query) < min_len:
            raise ValidationError(f"Arama terimi en az {min_len} karakter olmalı")
        
        if len(query) > max_len:
            raise ValidationError(f"Arama terimi en fazla {max_len} karakter olmalı")
        
        
        dangerous_patterns = ['<script', 'javascript:', 'DROP TABLE', 'DELETE FROM']
        query_lower = query.lower()
        for pattern in dangerous_patterns:
            if pattern.lower() in query_lower:
                raise ValidationError("Geçersiz karakter içeriği")
        
        return query


class TextCleaner:
    
    
    @staticmethod
    def clean_pdf_text(text):
        
        if not text:
            return ""
        
        
        text = re.sub(r'--- Sayfa \d+ ---', '', text)
        
       
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    @staticmethod
    def split_into_sentences(text):
        
        if not text:
            return []
        
        
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    @staticmethod
    def create_chunks(text, chunk_size=500, overlap=100):
        
        if not text:
            return []
        
        sentences = TextCleaner.split_into_sentences(text)
        chunks = []
        current_chunk = ""
        current_length = 0
        
        for sentence in sentences:
            sentence_length = len(sentence)
            
            if current_length + sentence_length > chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
               
                overlap_text = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
                current_chunk = overlap_text + " " + sentence
                current_length = len(current_chunk)
            else:
                current_chunk += " " + sentence
                current_length += sentence_length
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks


import logging

def setup_logger(name, level=logging.INFO):
    
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(level)
    return logger
